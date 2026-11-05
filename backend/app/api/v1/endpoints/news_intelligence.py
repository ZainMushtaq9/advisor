"""News Intelligence Engine read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent
with a reason. No value is ever fabricated, and no endpoint writes
anything. An unknown ticker returns 404; a known ticker with no
articles returns 200 with an empty list and a no_inputs note.

Sentiment, importance, credibility and market reaction are served
as separate fields, never blended into a signal. No endpoint issues
a buy/sell recommendation: a recommendation question is answered
with uncertainty (Phase 19 rule), and Phase 15 WITHHELD values are
never reintroduced here.

Endpoints:
  GET /api/v1/news-intelligence/feed
      Article feed with filters (ticker, sector, source, sentiment,
      event category, publication date, importance, freshness).
  GET /api/v1/news-intelligence/companies/{ticker}/news
      Company news timeline (articles + Phase 11 events + reactions).
  GET /api/v1/news-intelligence/impact
      Impact dashboard (importance/credibility/relevance rows).
  GET /api/v1/news-intelligence/assistant?q=
      AI news assistant: answers ONLY from stored rows, with a
      source link on every factual claim.
  GET /api/v1/news-intelligence/sources
      Permission register: every source with its policy.
  GET /api/v1/news-intelligence/quality
      Source health + freshness dashboard.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.news_events import NewsEvent, NewsEventCompany, NewsSource
from app.models.news_intelligence import (
    NewsArticle,
    NewsArticleEntity,
    NewsCollectionRun,
    NewsImpactAssessment,
    NewsMarketReaction,
    NewsSentimentAssessment,
)
from app.models.reference import Company, Security
from app.services.news_intelligence import assistant as assistant_mod
from app.services.news_intelligence import rag_news as rag_news_mod

router = APIRouter(tags=["news-intelligence"])

SCOPE_NOTE = (
    "Scope: processed articles stored by the News Intelligence Engine "
    "(metadata + 280-char summaries + links only; no article bodies) "
    "plus the Phase 11 seed events. No live PSX announcement or "
    "news-site collection runs while the Terms gate is uncleared; "
    "collection jobs are PAUSED and refusals are recorded. Scores "
    "are review-worthiness and separated impact dimensions, never "
    "buy/sell signals; no percentage impact and no target price is "
    "ever served."
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
    security = (
        session.query(Security)
        .filter(Security.ticker == ticker.upper())
        .one_or_none()
    )
    if security is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker {ticker}")
    return session.query(Company).filter(Company.id == security.company_id).one()


def _article_docs(session: Session) -> list[dict]:
    """Stored articles in the rag_news document shape."""
    articles = session.query(NewsArticle).all()
    sentiments = {
        s.article_id: s
        for s in session.query(NewsSentimentAssessment).all()
    }
    entities: dict[int, list[str]] = {}
    sectors: dict[int, list[str]] = {}
    for e in session.query(NewsArticleEntity).all():
        entities.setdefault(e.article_id, []).append(e.ticker)
        if e.sector_name:
            sectors.setdefault(e.article_id, []).append(e.sector_name)
    docs = []
    for a in articles:
        s = sentiments.get(a.id)
        docs.append(
            {
                "id": a.id,
                "title": a.title,
                "summary": a.summary,
                "source": a.source,
                "canonical_url": a.canonical_url,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "tickers": entities.get(a.id, []),
                "sectors": sectors.get(a.id, []),
                "event_category": s.event_category if s else "other",
                "sentiment": s.sentiment if s else None,
                "status": a.status,
            }
        )
    return docs


def _article_dict(a: NewsArticle, s: NewsSentimentAssessment | None) -> dict:
    return {
        "id": a.id,
        "article_id": a.article_id,
        "title": a.title,
        "source": a.source,
        "canonical_url": a.canonical_url,
        "published_at": a.published_at.isoformat() if a.published_at else None,
        "retrieved_at": a.retrieved_at.isoformat() if a.retrieved_at else None,
        "language": a.language,
        "summary": a.summary,
        "processor": a.processor,
        "model_name": a.model_name,
        "status": a.status,
        "quality_status": a.quality_status,
        "sentiment": s.sentiment if s else None,
        "event_category": s.event_category if s else None,
        "relevance_score": s.relevance_score if s else None,
        "impact_score": s.impact_score if s else None,
        "confidence_score": s.confidence_score if s else None,
    }


@router.get("/news-intelligence/feed")
def news_intelligence_feed(
    ticker: str | None = None,
    sector: str | None = None,
    source: str | None = None,
    sentiment: str | None = None,
    event_category: str | None = None,
    published_after: str | None = None,
    min_importance: float | None = None,
    limit: int = Query(default=50, le=200),
    session: Session = Depends(get_session),
):
    """Filtered article feed. Filters apply before ordering; an
    empty result is an empty list, never an invented article."""
    query = session.query(NewsArticle)
    if source:
        query = query.filter(NewsArticle.source_key == source)
    if published_after:
        try:
            after = datetime.fromisoformat(published_after)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="published_after must be ISO-8601"
            ) from exc
        query = query.filter(NewsArticle.published_at >= after)
    articles = query.order_by(
        NewsArticle.published_at.desc().nulls_last(), NewsArticle.id.desc()
    ).all()
    sentiments = {
        s.article_id: s
        for s in session.query(NewsSentimentAssessment).all()
    }
    entities: dict[int, list[NewsArticleEntity]] = {}
    for e in session.query(NewsArticleEntity).all():
        entities.setdefault(e.article_id, []).append(e)
    impacts = {
        i.article_id: i
        for i in session.query(NewsImpactAssessment).all()
    }
    out = []
    for a in articles:
        s = sentiments.get(a.id)
        if sentiment and (not s or s.sentiment != sentiment):
            continue
        if event_category and (not s or s.event_category != event_category):
            continue
        rows = entities.get(a.id, [])
        tickers = [r.ticker for r in rows]
        sectors = [r.sector_name for r in rows if r.sector_name]
        if ticker and ticker.upper() not in tickers:
            continue
        if sector and sector not in sectors:
            continue
        impact = impacts.get(a.id)
        if min_importance is not None and (
            not impact or impact.importance_score < min_importance
        ):
            continue
        d = _article_dict(a, s)
        d["tickers"] = tickers
        d["sectors"] = sectors
        d["importance_score"] = impact.importance_score if impact else None
        d["credibility_score"] = impact.credibility_score if impact else None
        out.append(d)
        if len(out) >= limit:
            break
    return {"scope_note": SCOPE_NOTE, "articles": out}


@router.get("/news-intelligence/companies/{ticker}/news")
def company_news(ticker: str, session: Session = Depends(get_session)):
    """Company news page: articles, Phase 11 events, reactions."""
    company = _company_for_ticker(session, ticker)
    entity_rows = (
        session.query(NewsArticleEntity)
        .filter(NewsArticleEntity.company_id == company.id)
        .all()
    )
    article_ids = [r.article_id for r in entity_rows]
    articles = (
        session.query(NewsArticle)
        .filter(NewsArticle.id.in_(article_ids))
        .order_by(
            NewsArticle.published_at.desc().nulls_last(), NewsArticle.id.desc()
        )
        .all()
        if article_ids
        else []
    )
    sentiments = {
        s.article_id: s
        for s in session.query(NewsSentimentAssessment)
        .filter(NewsSentimentAssessment.article_id.in_(article_ids))
        .all()
    } if article_ids else {}
    reactions = (
        session.query(NewsMarketReaction)
        .filter(NewsMarketReaction.article_id.in_(article_ids))
        .all()
        if article_ids
        else []
    )
    event_links = (
        session.query(NewsEventCompany)
        .filter(NewsEventCompany.company_id == company.id)
        .all()
    )
    event_ids = [r.event_id for r in event_links]
    events = (
        session.query(NewsEvent)
        .filter(NewsEvent.id.in_(event_ids))
        .order_by(NewsEvent.event_date.desc().nulls_last(), NewsEvent.id.desc())
        .all()
        if event_ids
        else []
    )
    return {
        "ticker": ticker.upper(),
        "company_name": company.legal_name,
        "articles": [_article_dict(a, sentiments.get(a.id)) for a in articles],
        "phase11_events": [
            {
                "id": e.id,
                "event_date": e.event_date.isoformat() if e.event_date else None,
                "event_type": e.event_type,
                "headline": e.headline,
                "summary": e.summary,
                "canonical_url": e.canonical_url,
                "quality_status": e.quality_status,
            }
            for e in events
        ],
        "market_reactions": [
            {
                "article_id": r.article_id,
                "event_id": r.event_id,
                "status": r.status,
                "returns": r.returns,
                "note": r.note,
            }
            for r in reactions
        ],
        "note": (
            "Empty lists mean no stored rows for this company, not "
            "missing data filled in. Market reactions are correlation, "
            "not causality."
        ),
    }


@router.get("/news-intelligence/impact")
def news_impact(session: Session = Depends(get_session)):
    """Impact dashboard: separated dimensions per article."""
    impacts = (
        session.query(NewsImpactAssessment)
        .order_by(
            NewsImpactAssessment.importance_score.desc(),
            NewsImpactAssessment.id.desc(),
        )
        .limit(100)
        .all()
    )
    articles = {
        a.id: a
        for a in session.query(NewsArticle)
        .filter(NewsArticle.id.in_([i.article_id for i in impacts]))
        .all()
    } if impacts else {}
    return {
        "scope_note": SCOPE_NOTE,
        "impacts": [
            {
                "article_id": i.article_id,
                "title": articles[i.article_id].title
                if i.article_id in articles
                else None,
                "importance_score": i.importance_score,
                "credibility_score": i.credibility_score,
                "credibility_class": i.credibility_class,
                "company_relevance": i.company_relevance,
                "sector_relevance": i.sector_relevance,
                "market_relevance": i.market_relevance,
                "horizon": i.horizon,
                "confidence": i.confidence,
                "status": i.status,
                "counterarguments": i.counterarguments,
            }
            for i in impacts
        ],
    }


@router.get("/news-intelligence/assistant")
def news_assistant(
    q: str = Query(min_length=1),
    session: Session = Depends(get_session),
):
    """Answer one question from stored rows only, with citations.

    A recommendation question is answered with uncertainty, never
    with a signal. A question with no stored evidence is answered
    missing_data with NO citation (an invented citation would be
    worse than none)."""
    docs = _article_docs(session)
    ticker_by_company_name: dict[str, str] = {}
    for sec in session.query(Security).all():
        comp = session.query(Company).filter(Company.id == sec.company_id).one_or_none()
        if comp and comp.legal_name:
            ticker_by_company_name[comp.legal_name.strip().lower()] = sec.ticker
    sector_by_ticker: dict[str, str] = {}
    for e in session.query(NewsArticleEntity).all():
        if e.sector_name:
            sector_by_ticker[e.ticker] = e.sector_name
    answer = assistant_mod.answer_question(
        q, docs, ticker_by_company_name, sector_by_ticker
    )
    answer["retrieval"] = "FULL_TEXT_FALLBACK"
    answer["note"] = (
        "Answered from stored rows only. Vector retrieval is not "
        "implemented (no verified local embedding model); retrieval "
        "is deterministic full-text and labelled as such."
    )
    return answer


@router.get("/news-intelligence/sources")
def news_intelligence_sources(session: Session = Depends(get_session)):
    """Permission register: every source with its policy and terms
    note. A listed source is not an integrated source."""
    rows = session.query(NewsSource).order_by(NewsSource.source_key).all()
    return {
        "sources": [
            {
                "source_key": r.source_key,
                "name": r.name,
                "source_type": r.source_type,
                "collection_policy": r.collection_policy,
                "collection_status": r.collection_status,
                "terms_note": r.terms_note,
            }
            for r in rows
        ],
        "gate_note": (
            "PSX/DPS announcements are TERMS_GATED: systematic "
            "retrieval needs prior written permission (user-owned "
            "gate, not cleared). BLOCKED sources are never collected "
            "from; refusals are recorded in news_collection_runs."
        ),
    }


@router.get("/news-intelligence/quality")
def news_intelligence_quality(session: Session = Depends(get_session)):
    """Source health + freshness: collection-run history by source
    and status, plus stored-article counts by status."""
    runs = session.query(NewsCollectionRun).all()
    by_source: dict[str, dict] = {}
    for r in runs:
        bucket = by_source.setdefault(
            r.source_key, {"refused": 0, "collected": 0, "failed": 0, "paused": 0}
        )
        if r.status in bucket:
            bucket[r.status] += 1
    articles = session.query(NewsArticle).all()
    by_status: dict[str, int] = {}
    for a in articles:
        by_status[a.status] = by_status.get(a.status, 0) + 1
    return {
        "collection_runs_by_source": by_source,
        "articles_by_status": by_status,
        "freshness_note": (
            "Freshness is computed per article from published_at vs "
            "retrieved_at (Asia/Karachi): current <= 1 day, recent "
            "<= 7 days, stale beyond; missing or future-dated "
            "publication dates are 'unknown', never 'current'."
        ),
    }
