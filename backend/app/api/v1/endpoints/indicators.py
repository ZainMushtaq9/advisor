"""Phase 6 technical-indicator read-only endpoints (GET only).

Everything here is computed from rows that actually exist, or
explained as NOT_CALCULABLE with a reason. No value is ever
fabricated, and no endpoint writes anything.

Endpoints:
  GET /api/v1/indicators/coverage
      Live coverage summary: securities assessed, bars available,
      per-indicator calculable counts and NOT_CALCULABLE reasons.
  GET /api/v1/indicators/coverage/{ticker}
      Per-ticker verdicts for every registered indicator.
  GET /api/v1/indicators/values?ticker=&indicator_key=
      Stored technical_indicator_values rows only (empty today:
      nothing is calculable on one trading day). An empty result
      is a truthful empty state, not a missing feature.
  GET /api/v1/indicators/signals?ticker=
      Stored technical_signal_events rows only (empty: no rule is
      activated, and no rule fires on missing inputs). Signal
      events are observations, never buy/sell recommendations.

When no database is configured, endpoints answer 503 with a
truthful reason, never a fake empty market. An unknown ticker
returns 404; a known ticker with no observations returns 200
with all verdicts NOT_CALCULABLE.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.financial import (
    TechnicalIndicatorConfiguration,
    TechnicalIndicatorDefinition,
    TechnicalIndicatorValue,
    TechnicalSignalEvent,
)
from app.models.reference import Security
from app.services.technical_indicators import conventions, coverage
from app.services.technical_indicators.runner import load_series

router = APIRouter(tags=["indicators"])

MAX_LIMIT = 200

SCOPE_NOTE = (
    "Scope: Main Board / Normal Counter registry view only (470 "
    "securities); GEM and Non-Compliant securities are not captured. "
    "All committed prices are UNVERIFIED single-source observations "
    "for one trading day (2026-11-03). No KSE-100, full-market, or "
    "VERIFIED claim is made. Signal events, if any ever exist, are "
    "observations only, never buy/sell recommendations."
)


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


def _security_or_404(session: Session, ticker: str) -> Security:
    security = session.query(Security).filter_by(ticker=ticker).one_or_none()
    if security is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    return security


@router.get("/indicators/coverage")
def indicators_coverage(
    as_of: str | None = None,
    session: Session = Depends(get_session),  # noqa: B008
) -> dict:
    as_of_date: date | None = None
    if as_of is not None:
        try:
            as_of_date = date.fromisoformat(as_of)
        except ValueError:
            raise HTTPException(
                status_code=422, detail="as_of must be an ISO date (YYYY-MM-DD)"
            )
    series, _ids, conflicted = load_series(session)
    if as_of_date is None:
        all_dates = [b["date"] for bars in series.values() for b in bars]
        as_of_date = max(all_dates) if all_dates else None
    assessment = coverage.assess_market(series, as_of_date, conflicted_tickers=conflicted)
    return {
        "as_of": as_of_date.isoformat() if as_of_date else None,
        "securities_assessed": assessment["securities_assessed"],
        "indicators_registered": assessment["indicators_registered"],
        "securities_with_any_calculable": assessment["securities_with_any_calculable"],
        "per_indicator": assessment["per_indicator"],
        "scope_note": SCOPE_NOTE,
    }


@router.get("/indicators/coverage/{ticker}")
def indicators_coverage_ticker(
    ticker: str,
    as_of: str | None = None,
    session: Session = Depends(get_session),  # noqa: B008
) -> dict:
    _security_or_404(session, ticker)
    as_of_date: date | None = None
    if as_of is not None:
        try:
            as_of_date = date.fromisoformat(as_of)
        except ValueError:
            raise HTTPException(
                status_code=422, detail="as_of must be an ISO date (YYYY-MM-DD)"
            )
    series, _ids, conflicted = load_series(session)
    detail = coverage.assess_security(
        ticker,
        series.get(ticker, []),
        as_of_date,
        has_conflicted_inputs=ticker in conflicted,
    )
    detail["scope_note"] = SCOPE_NOTE
    return detail


@router.get("/indicators/values")
def indicators_values(
    ticker: str | None = None,
    indicator_key: str | None = None,
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),  # noqa: B008
) -> dict:
    skip, limit = _pagination(skip, limit)
    if indicator_key is not None and indicator_key not in conventions.BY_KEY:
        raise HTTPException(status_code=422, detail=f"Unknown indicator_key: {indicator_key}")
    query = (
        session.query(
            TechnicalIndicatorValue,
            Security.ticker,
            TechnicalIndicatorDefinition.indicator_key,
            TechnicalIndicatorConfiguration.id,
            TechnicalIndicatorConfiguration.config_version,
            TechnicalIndicatorConfiguration.parameters,
        )
        .join(Security, Security.id == TechnicalIndicatorValue.security_id)
        .join(
            TechnicalIndicatorConfiguration,
            TechnicalIndicatorConfiguration.id
            == TechnicalIndicatorValue.indicator_configuration_id,
        )
        .join(
            TechnicalIndicatorDefinition,
            TechnicalIndicatorDefinition.id
            == TechnicalIndicatorConfiguration.indicator_definition_id,
        )
        .order_by(
            TechnicalIndicatorValue.observation_date.desc(),
            Security.ticker,
            TechnicalIndicatorDefinition.indicator_key,
        )
    )
    if ticker is not None:
        _security_or_404(session, ticker)
        query = query.filter(Security.ticker == ticker)
    if indicator_key is not None:
        query = query.filter(TechnicalIndicatorDefinition.indicator_key == indicator_key)
    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "ticker": row_ticker,
                "indicator_key": key,
                "indicator_configuration_id": config_id,
                "config_version": config_version,
                "parameters": parameters,
                "observation_date": value.observation_date.isoformat(),
                "timeframe": value.timeframe,
                "value": str(value.value) if value.value is not None else None,
                "calculation_version": value.calculation_version,
                "last_input_observation_date": (
                    value.last_input_observation_date.isoformat()
                    if value.last_input_observation_date
                    else None
                ),
                "quality_status": value.quality_status,
                "source_key": value.source_key,
            }
            for value, row_ticker, key, config_id, config_version, parameters in rows
        ],
        "scope_note": SCOPE_NOTE,
    }


@router.get("/indicators/signals")
def indicators_signals(
    ticker: str | None = None,
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),  # noqa: B008
) -> dict:
    skip, limit = _pagination(skip, limit)
    query = (
        session.query(TechnicalSignalEvent, Security.ticker)
        .join(Security, Security.id == TechnicalSignalEvent.security_id)
        .order_by(
            TechnicalSignalEvent.event_date.desc(),
            Security.ticker,
        )
    )
    if ticker is not None:
        _security_or_404(session, ticker)
        query = query.filter(Security.ticker == ticker)
    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "ticker": row_ticker,
                "event_date": event.event_date.isoformat(),
                "indicator_key": event.indicator_key,
                "event_condition": event.event_condition,
                "observed_value": str(event.observed_value)
                if event.observed_value is not None
                else None,
                "parameter_configuration": event.parameter_configuration,
                "calculation_version": event.calculation_version,
            }
            for event, row_ticker in rows
        ],
        "note": (
            "Signal events are observations only, never buy/sell "
            "recommendations. No rule is currently activated, so no "
            "events exist; a rule activates only once its input "
            "indicators are calculable."
        ),
        "scope_note": SCOPE_NOTE,
    }
