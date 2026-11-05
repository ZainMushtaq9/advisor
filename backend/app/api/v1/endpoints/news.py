"""Phase 11 news/event read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent with a
reason. No value is ever fabricated, and no endpoint writes anything.
An unknown ticker returns 404; a known ticker with no events returns
200 with an empty list and a no_inputs note. Event scores are
review-worthiness, never buy/sell signals; no sentiment is stored or
served.

Endpoints:
  GET /api/v1/news
      Event feed (latest first) + scope note.
  GET /api/v1/news/sources
      Source registry with collection policies.
  GET /api/v1/news/aliases?ticker=
      Alias rows for one company.
  GET /api/v1/news/quality
      Quality dashboard: counts by source type, review queue, coverage.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.news_events import (
    CompanyAlias,
    NewsEvent,
    NewsSource,
)
from app.models.reference import Company, Security

router = APIRouter(tags=["news"])

SCOPE_NOTE = (
    "Scope: seed events only, derived from Phase 7 documents (4 "
    "companies) and Phase 10 macro events (4). No live PSX announcement "
    "or news-site collection runs in Phase 11 (PSX TERMS_GATED; news "
    "terms unreviewed). Scores are review-worthiness, never buy/sell "
    "signals; no sentiment is stored."
)


def get_session(request: Request) -> Generator[Session, None, None]:
    factory = get_session_factory(request.app.state.engine)
    if factory is None:
        raise HTTPException(status_code=503, detail="No database configured.")
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _company_for_ticker(session: Session, ticker: str) -> Company:
    security = session.query(Security).filter(Security.ticker == ticker.upper()).one_or_none()
    if security is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker {ticker}")
    company = session.query(Company).filter(Company.id == security.company_id).one()
    return company


def _event_dict(row: NewsEvent) -> dict:
    return {
        "id": row.id,
        "event_date": row.event_date.isoformat() if row.event_date else None,
        "date_status": row.date_status,
        "event_type": row.event_type,
        "headline": row.headline,
        "summary": row.summary,
        "canonical_url": row.canonical_url,
        "publisher": row.publisher,
        "source_type": row.source_type,
        "primary_company_id": row.primary_company_id,
        "relevance_score": row.relevance_score,
        "review_status": row.review_status,
        "quality_status": row.quality_status,
    }


@router.get("/news")
def news_feed(session: Session = Depends(get_session)):
    rows = (
        session.query(NewsEvent)
        .order_by(NewsEvent.event_date.desc().nulls_last(), NewsEvent.id.desc())
        .limit(100)
        .all()
    )
    return {"scope_note": SCOPE_NOTE, "events": [_event_dict(r) for r in rows]}


@router.get("/news/sources")
def news_sources(session: Session = Depends(get_session)):
    rows = session.query(NewsSource).order_by(NewsSource.source_key).all()
    return {
        "sources": [
            {
                "source_key": r.source_key,
                "name": r.name,
                "source_type": r.source_type,
                "collection_policy": r.collection_policy,
                "collection_status": r.collection_status,
                "excerpt_limit_chars": r.excerpt_limit_chars,
            }
            for r in rows
        ]
    }


@router.get("/news/aliases")
def news_aliases(ticker: str, session: Session = Depends(get_session)):
    company = _company_for_ticker(session, ticker)
    rows = (
        session.query(CompanyAlias)
        .filter(CompanyAlias.company_id == company.id)
        .order_by(CompanyAlias.confidence.desc())
        .all()
    )
    return {
        "ticker": ticker.upper(),
        "company_id": company.id,
        "legal_name": company.legal_name,
        "aliases": [
            {
                "alias_normalized": r.alias_normalized,
                "alias_type": r.alias_type,
                "confidence": r.confidence,
                "is_ambiguous": r.is_ambiguous,
            }
            for r in rows
        ],
    }


@router.get("/news/quality")
def news_quality(session: Session = Depends(get_session)):
    by_source_type: dict[str, int] = {}
    for row in session.query(NewsEvent.source_type).all():
        by_source_type[row[0]] = by_source_type.get(row[0], 0) + 1
    review_counts: dict[str, int] = {}
    for row in session.query(NewsEvent.review_status).all():
        review_counts[row[0]] = review_counts.get(row[0], 0) + 1
    covered = (
        session.query(NewsEvent.primary_company_id)
        .filter(NewsEvent.primary_company_id.isnot(None))
        .distinct()
        .count()
    )
    universe = session.query(Company).count()
    return {
        "scope_note": SCOPE_NOTE,
        "events_by_source_type": by_source_type,
        "review_counts": review_counts,
        "companies_with_events": covered,
        "universe_companies": universe,
        "alias_rows": session.query(CompanyAlias).count(),
        "ambiguous_aliases": session.query(CompanyAlias)
        .filter(CompanyAlias.is_ambiguous.is_(True))
        .count(),
    }
