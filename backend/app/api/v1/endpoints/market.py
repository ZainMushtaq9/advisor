"""Phase 5 market-data read-only endpoints (GET only).

CORS allows GET only (see app.main), and ingestion happens via the
CLI, never via a POST API — there is deliberately no write endpoint
here.

All endpoints return ONLY rows that actually exist in the database.
When market_prices is empty they return counts of 0 with the scope
note — never 404 for an empty market, never fabricated rows. A single
-resource lookup for an unknown ticker (GET /market/prices/{ticker}/
latest) returns 404, mirroring the registry endpoints; a known ticker
with no observations returns 200 with observation null. When no
database is configured, endpoints answer 503 with a truthful reason,
never a fake empty market.

Endpoints:
  GET /api/v1/market/prices?ticker=&from_date=&to_date=&quality_status=
  GET /api/v1/market/prices/{ticker}/latest
  GET /api/v1/market/status
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.base import QUALITY_STATUSES
from app.models.market import MarketPrice
from app.models.reference import Security
from app.services.market_data import quality
from app.services.market_data.ingestion import (
    BAR_TYPE,
    FRESHNESS_RULE_NOTE,
    SCOPE_NOTE,
)

router = APIRouter(tags=["market"])

MAX_LIMIT = 200


def get_session(request: Request) -> Generator[Session, None, None]:
    factory = get_session_factory(request.app.state.engine)
    if factory is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured (DATABASE_URL is not set).",
        )
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _pagination(skip: int, limit: int) -> tuple[int, int]:
    if skip < 0:
        raise HTTPException(status_code=422, detail="skip must be >= 0")
    if limit < 1 or limit > MAX_LIMIT:
        raise HTTPException(
            status_code=422, detail=f"limit must be between 1 and {MAX_LIMIT}"
        )
    return skip, limit


def _parse_date(value: str | None, name: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=422, detail=f"{name} must be an ISO date (YYYY-MM-DD)"
        )


def _number(value: object) -> float | None:
    return float(value) if value is not None else None


def _price_row(price: MarketPrice, ticker: str) -> dict:
    return {
        "ticker": ticker,
        "trading_date": price.trading_date.isoformat(),
        "bar_type": price.bar_type,
        "open": _number(price.open_price),
        "high": _number(price.high_price),
        "low": _number(price.low_price),
        "close": _number(price.close_price),
        "volume": price.volume,
        "turnover": _number(price.turnover),
        "previous_close": _number(price.previous_close),
        "is_adjusted": price.is_adjusted,
        "quality_status": price.quality_status,
        "freshness": quality.freshness_label(price.collected_at, price.trading_date),
        "source_key": price.source_key,
        "source_timestamp": (
            price.source_timestamp.isoformat() if price.source_timestamp else None
        ),
        "collected_at": price.collected_at.isoformat() if price.collected_at else None,
    }


def _security_by_ticker(session: Session, ticker: str) -> Security | None:
    return (
        session.query(Security)
        .filter(func.upper(Security.ticker) == ticker.strip().upper())
        .first()
    )


@router.get("/market/prices")
def list_prices(
    session: Session = Depends(get_session),  # noqa: B008
    ticker: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    quality_status: str | None = Query(default=None),
    skip: int = Query(default=0),
    limit: int = Query(default=50),
) -> dict:
    skip, limit = _pagination(skip, limit)
    start = _parse_date(from_date, "from_date")
    end = _parse_date(to_date, "to_date")
    if start is not None and end is not None and end < start:
        raise HTTPException(
            status_code=422, detail="to_date must not be before from_date"
        )
    if quality_status is not None and quality_status not in QUALITY_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"quality_status must be one of {list(QUALITY_STATUSES)}",
        )
    query = session.query(MarketPrice, Security.ticker).join(
        Security, Security.id == MarketPrice.security_id
    )
    if ticker:
        query = query.filter(func.upper(Security.ticker) == ticker.strip().upper())
    if start is not None:
        query = query.filter(MarketPrice.trading_date >= start)
    if end is not None:
        query = query.filter(MarketPrice.trading_date <= end)
    if quality_status is not None:
        query = query.filter(MarketPrice.quality_status == quality_status)
    total = query.count()
    rows = (
        query.order_by(MarketPrice.trading_date.desc(), MarketPrice.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "bar_type": BAR_TYPE,
        "scope_note": SCOPE_NOTE,
        "items": [_price_row(price, price_ticker) for price, price_ticker in rows],
    }


@router.get("/market/prices/{ticker}/latest")
def latest_price(ticker: str, session: Session = Depends(get_session)) -> dict:  # noqa: B008
    security = _security_by_ticker(session, ticker)
    if security is None:
        raise HTTPException(status_code=404, detail="Security not found.")
    row = (
        session.query(MarketPrice)
        .filter_by(security_id=security.id, bar_type=BAR_TYPE)
        .order_by(MarketPrice.trading_date.desc(), MarketPrice.id.desc())
        .first()
    )
    return {
        "ticker": security.ticker,
        "scope_note": SCOPE_NOTE,
        "observation": _price_row(row, security.ticker) if row is not None else None,
    }


@router.get("/market/status")
def market_status(session: Session = Depends(get_session)) -> dict:  # noqa: B008
    total = session.query(MarketPrice).filter_by(bar_type=BAR_TYPE).count()
    securities_with_observations = (
        session.query(func.count(func.distinct(MarketPrice.security_id)))
        .filter_by(bar_type=BAR_TYPE)
        .scalar()
    )
    date_range = (
        session.query(
            func.min(MarketPrice.trading_date), func.max(MarketPrice.trading_date)
        )
        .filter_by(bar_type=BAR_TYPE)
        .one()
    )
    counts = {status: 0 for status in QUALITY_STATUSES}
    for status, count in (
        session.query(MarketPrice.quality_status, func.count())
        .filter_by(bar_type=BAR_TYPE)
        .group_by(MarketPrice.quality_status)
        .all()
    ):
        counts[status] = count
    return {
        "market_prices_total": total,
        "securities_with_observations": securities_with_observations or 0,
        "earliest_trading_date": (
            date_range[0].isoformat() if date_range[0] is not None else None
        ),
        "latest_trading_date": (
            date_range[1].isoformat() if date_range[1] is not None else None
        ),
        "counts_by_quality_status": counts,
        "bar_type": BAR_TYPE,
        "scope_note": SCOPE_NOTE,
        "freshness_rule_note": FRESHNESS_RULE_NOTE,
        "is_adjusted_note": "All stored prices are official unadjusted values (is_adjusted=false).",
        "note": (
            "Counts are live database counts. Zero means no price "
            "observations have been ingested, not that the market is empty."
        ),
    }
