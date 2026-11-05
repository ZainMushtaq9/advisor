"""Persistence runner for the News Intelligence Engine.

The processing pipeline (processing.py) never writes to the
database; this module decides persistence. Rules:

- Dedup by content_hash: an article already stored is skipped, never
  duplicated, and the skip is counted.
- PROCESSED / REVIEW results persist as a NewsArticle row plus its
  entity, summary, sentiment and impact rows. REVIEW rows are stored
  with status REVIEW, never silently promoted to PROCESSED.
- UNPROCESSED results persist as metadata-only article rows (title,
  link, dates) with status UNPROCESSED, so they can be reprocessed
  later; they carry no scores, because no scores were computed.
- REJECTED results are NOT persisted as articles: malformed model
  output is not content. Their errors are returned in the run report
  and recorded on the collection-run row, never hidden.
- New rows carry their inputs' quality_status, never higher. The
  default input status is UNVERIFIED; a caller that knows better
  passes it explicitly, and the runner never upgrades it.
- Collection from a BLOCKED source is refused before any fetch:
  collection_allowed() raises PolicyBlocked, and the refusal is
  recorded as a news_collection_runs row with status "refused".
  A refused run is a successful enforcement outcome, not a failure.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.news_intelligence import (
    NewsArticle,
    NewsArticleEntity,
    NewsCollectionRun,
    NewsImpactAssessment,
    NewsSentimentAssessment,
    NewsSummary,
)
from app.services.news_intelligence import collection as collection_mod
from app.services.news_intelligence import impact as impact_mod
from app.services.news_intelligence import processing as processing_mod
from app.services.news_intelligence.collection import PolicyBlocked  # noqa: F401 (re-exported: the gate exception)


def build_alias_index(session: Session) -> dict:
    """Build the Phase 11 resolver index from stored aliases.

    Returns {alias_normalized: [(company_id, alias_type, confidence,
    is_ambiguous)]}. Built from the database, never from hardcoded
    alias text, so it tracks the registry exactly.
    """
    from sqlalchemy import text as _text

    rows = session.execute(
        _text(
            "SELECT company_id, alias_normalized, alias_type, confidence, "
            "is_ambiguous FROM company_aliases"
        )
    ).all()
    index: dict[str, list] = {}
    for company_id, alias, alias_type, confidence, is_ambiguous in rows:
        index.setdefault(alias, []).append(
            (int(company_id), alias_type, float(confidence), bool(is_ambiguous))
        )
    return index


def build_ticker_maps(session: Session) -> tuple[set[str], dict[str, str], dict[int, str], dict[int, str]]:
    """Resolve registry identity BY TICKER for the runner.

    Returns (known_tickers, sector_by_ticker, ticker_by_company_id,
    name_by_company_id). Company ids are surrogate and shift across
    fresh imports; they are used here only as join keys inside one
    database snapshot, and the durable identity written to rows is
    always the ticker.
    """
    from sqlalchemy import text as _text

    rows = session.execute(
        _text(
            "SELECT c.id, c.legal_name, s.ticker, sec.name "
            "FROM companies c "
            "JOIN securities s ON s.company_id = c.id "
            "LEFT JOIN sectors sec ON sec.id = c.sector_id"
        )
    ).all()
    known: set[str] = set()
    sector_by_ticker: dict[str, str] = {}
    ticker_by_company_id: dict[int, str] = {}
    name_by_company_id: dict[int, str] = {}
    for company_id, company_name, ticker, sector_name in rows:
        if not ticker:
            continue
        ticker = str(ticker).upper()
        known.add(ticker)
        ticker_by_company_id[int(company_id)] = ticker
        name_by_company_id[int(company_id)] = company_name
        if sector_name:
            sector_by_ticker[ticker] = sector_name
    return known, sector_by_ticker, ticker_by_company_id, name_by_company_id


def record_collection_run(
    session: Session,
    source_key: str,
    status: str,
    items_seen: int = 0,
    items_stored: int = 0,
    policy_reason: str | None = None,
    error: str | None = None,
) -> NewsCollectionRun:
    """Append one collection-run record. Never overwrites history:
    a later run is a new row, so refusals stay auditable."""
    now = datetime.now(timezone.utc)
    row = NewsCollectionRun(
        source_key=source_key,
        run_started_at=now,
        run_finished_at=now,
        status=status,
        items_seen=items_seen,
        items_stored=items_stored,
        policy_reason=policy_reason,
        error=error,
    )
    session.add(row)
    return row


def refuse_collection(session: Session, source_key: str, collection_policy: str) -> dict:
    """Enforce the collection gate for one source and record it.

    Raises nothing: the PolicyBlocked reason is captured and stored
    as a refused run, and the report is returned. Callers that want
    the exception itself should call collection_allowed() directly.
    """
    try:
        collection_mod.collection_allowed(source_key, collection_policy, False)
        # A source that passes the gate is not refused; the caller
        # must run a real collection instead of calling this.
        return {"source_key": source_key, "refused": False, "reason": None}
    except PolicyBlocked as exc:
        record_collection_run(
            session, source_key, "refused", policy_reason=str(exc)
        )
        return {"source_key": source_key, "refused": True, "reason": str(exc)}


def persist_result(
    session: Session,
    result: dict,
    article_input: dict,
    input_quality_status: str = "UNVERIFIED",
) -> dict:
    """Persist one pipeline result. Returns {action, article_db_id}.

    Actions: "stored" (PROCESSED/REVIEW full rows), "stored_unprocessed"
    (metadata-only), "skipped_duplicate" (content_hash already present),
    "not_persisted" (REJECTED: malformed output is not content).
    """
    status = result.get("status")
    if status == "REJECTED":
        return {"action": "not_persisted", "article_db_id": None}
    title = article_input.get("title", "")
    canonical_url = article_input.get("canonical_url") or ""
    content_hash = collection_mod.article_content_hash(title, canonical_url)
    existing = (
        session.query(NewsArticle)
        .filter(NewsArticle.content_hash == content_hash)
        .first()
    )
    if existing is not None:
        return {"action": "skipped_duplicate", "article_db_id": existing.id}
    record = result.get("record") or {}
    fingerprint = collection_mod.article_fingerprint(title, canonical_url)
    published_at = collection_mod.normalize_published_at(
        article_input.get("published_at")
    )
    retrieved_at = collection_mod.normalize_published_at(
        article_input.get("retrieved_at")
    )
    article = NewsArticle(
        article_id=fingerprint,
        title=title[:500],
        source=article_input.get("source", "")[:200],
        canonical_url=canonical_url,
        published_at=published_at,
        retrieved_at=retrieved_at,
        language=record.get("language", article_input.get("language", "en")),
        summary=(record.get("summary", "") or "")[:280],
        content_hash=content_hash,
        processor=record.get("processor", result.get("processor", "RULE_BASED")),
        model_name=record.get("model_name"),
        model_version=record.get("model_version"),
        processing_timestamp=collection_mod.normalize_published_at(
            record.get("processing_timestamp")
        ),
        status=status,
        source_key=article_input.get("source_key"),
        source_timestamp=published_at,
        collected_at=retrieved_at,
        quality_status=input_quality_status,
    )
    session.add(article)
    session.flush()
    if status == "UNPROCESSED":
        return {"action": "stored_unprocessed", "article_db_id": article.id}
    # Entity rows: durable identity is the ticker; company_id is the
    # join key inside this snapshot only.
    ticker_by_company_id = article_input.get("_ticker_by_company_id") or {}
    for match in article_input.get("_resolver_matches", []):
        ticker = ticker_by_company_id.get(match["company_id"])
        if not ticker:
            continue
        session.add(
            NewsArticleEntity(
                article_id=article.id,
                company_id=match["company_id"],
                ticker=ticker,
                sector_name=article_input.get("_sector_by_ticker", {}).get(ticker),
                match_type=match["alias_type"],
                match_confidence=match["confidence"],
                match_evidence=match["evidence"],
                needs_review=bool(match["ambiguous"])
                or float(match["confidence"]) < 0.80,
            )
        )
    session.add(
        NewsSummary(
            article_id=article.id,
            summary=(record.get("summary", "") or "")[:280],
            source_link=canonical_url or None,
            is_llm=record.get("processor") == "LLM",
            model_name=record.get("model_name"),
        )
    )
    session.add(
        NewsSentimentAssessment(
            article_id=article.id,
            sentiment=record.get("sentiment", "neutral"),
            event_category=record.get("event_category", "other"),
            relevance_score=record.get("relevance_score", 0.0),
            impact_score=record.get("impact_score", 0.0),
            confidence_score=record.get("confidence_score", 0.0),
            potential_impact_horizon=record.get(
                "potential_impact_horizon", "unknown"
            ),
            extracted_facts=record.get("extracted_facts", []),
            supporting_evidence=record.get("supporting_evidence", []),
            uncertainty_notes=record.get("uncertainty_notes", []),
            risk_factors=record.get("risk_factors", []),
            processor=record.get("processor", "RULE_BASED"),
            model_name=record.get("model_name"),
            model_version=record.get("model_version"),
        )
    )
    impact = impact_mod.assess_impact(
        record,
        article_input.get("_credibility_class", "unverified"),
        sector_match=bool(record.get("sector_names")),
    )
    if impact.get("status") != "INSUFFICIENT_DATA":
        session.add(
            NewsImpactAssessment(
                article_id=article.id,
                importance_score=impact["importance_score"],
                credibility_score=impact["credibility_score"],
                credibility_class=article_input.get(
                    "_credibility_class", "unverified"
                ),
                company_relevance=impact["company_relevance"],
                sector_relevance=impact["sector_relevance"],
                market_relevance=impact["market_relevance"],
                horizon=impact["horizon"],
                supporting_facts=impact["supporting_facts"],
                counterarguments=impact["counterarguments"],
                uncertainty=(
                    "; ".join(impact["uncertainty"])
                    if isinstance(impact["uncertainty"], list)
                    else impact["uncertainty"]
                ),
                confidence=impact["confidence"],
                status="computed",
            )
        )
    return {"action": "stored", "article_db_id": article.id}


def run_processing(
    session: Session,
    items: list[dict],
    adapter=None,
    commit: bool = False,
    input_quality_status: str = "UNVERIFIED",
) -> dict:
    """Process a list of article dicts and persist the results.

    ``items``: article dicts in DeterministicFallback.process_record
    shape ({article_id, title, source, canonical_url, published_at,
    retrieved_at, language?, text, source_key?, _credibility_class?}).
    Dry-run (commit=False) processes everything and rolls back, so a
    dry run proves the pipeline without writing a row.
    """
    alias_index = build_alias_index(session)
    known, sector_by_ticker, ticker_by_company_id, name_by_company_id = (
        build_ticker_maps(session)
    )
    from app.services.news_events.resolver import resolve_text

    counts = {
        "PROCESSED": 0,
        "REVIEW": 0,
        "REJECTED": 0,
        "UNPROCESSED": 0,
        "skipped_duplicate": 0,
        "stored": 0,
        "stored_unprocessed": 0,
    }
    errors: list[dict] = []
    for item in items:
        item = dict(item)
        item["_ticker_by_company_id"] = ticker_by_company_id
        item["_sector_by_ticker"] = sector_by_ticker
        item["_resolver_matches"] = resolve_text(
            f"{item.get('title', '')} {item.get('text', '')}", alias_index
        )
        result = processing_mod.process_article(
            item,
            alias_index,
            known,
            sector_by_ticker,
            ticker_by_company_id,
            name_by_company_id,
            adapter=adapter,
        )
        persisted = persist_result(session, result, item, input_quality_status)
        action = persisted["action"]
        if action in ("stored",):
            counts["stored"] += 1
        elif action == "stored_unprocessed":
            counts["stored_unprocessed"] += 1
        elif action == "skipped_duplicate":
            counts["skipped_duplicate"] += 1
        counts[result["status"]] = counts.get(result["status"], 0) + 1
        if result.get("errors"):
            errors.append(
                {"article_id": item.get("article_id"), "errors": result["errors"]}
            )
    if commit:
        session.commit()
    else:
        session.rollback()
    return {
        "items": len(items),
        "counts": counts,
        "errors": errors,
        "committed": commit,
    }


def persist_reaction(
    session: Session,
    reaction: dict,
    article_id: int | None = None,
    event_id: int | None = None,
    event_date=None,
) -> dict:
    """Persist one market-reaction dict (computed by
    market_reaction.compute_reaction) as a NewsMarketReaction row.

    compute_reaction returns prices/returns as strings (Decimal
    values stringified for JSON); they are converted back to
    Decimal here for the NUMERIC columns. INSUFFICIENT_DATA rows
    are persisted too: the status IS the finding, and persisting
    it lets the API show the status explicitly instead of an empty
    list that hides the reason. Returns {action, reaction_db_id}.
    """
    from datetime import datetime as _datetime
    from decimal import Decimal as _Decimal

    from app.models.news_intelligence import NewsMarketReaction
    from app.services.news_intelligence.collection import PKT

    def _num(value):
        if value is None:
            return None
        try:
            return _Decimal(str(value))
        except Exception:
            return None

    stored_date = None
    if event_date is not None:
        if isinstance(event_date, _datetime):
            stored_date = event_date
        else:
            stored_date = _datetime(
                event_date.year, event_date.month, event_date.day, tzinfo=PKT
            )
    row = NewsMarketReaction(
        article_id=article_id,
        event_id=event_id,
        event_date=stored_date,
        pre_price=_num(reaction.get("pre_price")),
        event_day_price=_num(reaction.get("event_day_price")),
        post_price=_num(reaction.get("post_price")),
        returns=reaction.get("company_returns", {}),
        volume_change=_num(reaction.get("volume_change")),
        benchmark_return=reaction.get("benchmark_returns", {}),
        sector_return=reaction.get("sector_returns", {}),
        excess_return=reaction.get("excess_vs_benchmark", {}),
        status=reaction.get("status", "INSUFFICIENT_DATA"),
        note=reaction.get("note"),
    )
    session.add(row)
    session.flush()
    return {"action": "stored", "reaction_db_id": row.id}


def compute_event_reactions(session: Session, commit: bool = False) -> dict:
    """Compute market reactions for every stored Phase 11 event
    against stored market prices, and persist one row per event.

    With one price date in the data, most rows are INSUFFICIENT_DATA
    with the exact missing windows named — that is the honest
    result, not a failure to fix by inventing prices. Events with
    unknown dates (event_date NULL) get an INSUFFICIENT_DATA row
    naming the unknown date. Dry-run rolls back.
    """
    from datetime import date as _date

    from sqlalchemy import text as _text

    from app.services.news_intelligence import market_reaction as reaction_mod

    price_rows = session.execute(
        _text(
            "SELECT s.ticker, mp.trading_date, mp.close_price, mp.volume "
            "FROM market_prices mp JOIN securities s ON s.id = mp.security_id "
            "ORDER BY mp.trading_date"
        )
    ).all()
    by_ticker: dict[str, list[dict]] = {}
    for ticker, trading_date, close_price, volume in price_rows:
        by_ticker.setdefault(ticker, []).append(
            {
                "trading_date": trading_date,
                "close": close_price,
                "volume": volume,
            }
        )
    events = session.execute(
        _text(
            "SELECT e.id, e.event_date, nec.company_id, s.ticker "
            "FROM news_events e "
            "LEFT JOIN news_event_companies nec ON nec.event_id = e.id "
            "LEFT JOIN securities s ON s.company_id = nec.company_id "
            "ORDER BY e.id"
        )
    ).all()
    stored = 0
    details: list[dict] = []
    for event_id, event_date, _company_id, ticker in events:
        if event_date is None or ticker is None:
            reaction = {
                "status": "INSUFFICIENT_DATA",
                "company_returns": {},
                "benchmark_returns": {},
                "sector_returns": {},
                "excess_vs_benchmark": {},
                "missing": [
                    "event date unknown (NULL in Phase 11 record) or no "
                    "company link: no reaction computable, date never guessed"
                ],
                "note": (
                    "Event date unknown (NULL in Phase 11 record) or no "
                    "company link: no reaction computable, date never guessed."
                ),
            }
        else:
            reaction = reaction_mod.compute_reaction(
                event_date, by_ticker.get(ticker, [])
            )
        persist_reaction(
            session, reaction, event_id=event_id, event_date=event_date
        )
        stored += 1
        details.append(
            {
                "event_id": event_id,
                "ticker": ticker,
                "event_date": str(event_date) if event_date else None,
                "status": reaction["status"],
                "missing": reaction.get("missing", []),
            }
        )
    if commit:
        session.commit()
    else:
        session.rollback()
    return {"events": len(events), "stored": stored, "details": details,
            "committed": commit}


def build_digest(session: Session, limit: int = 20) -> dict:
    """Read-only digest over stored articles: newest PROCESSED /
    REVIEW rows first, with their latest sentiment and impact rows.
    No message is sent anywhere; the digest is a report dict the
    dashboard and the digest job show.
    """
    from sqlalchemy import text as _text

    rows = session.execute(
        _text(
            "SELECT a.id, a.title, a.source, a.canonical_url, "
            "a.published_at, a.status, s.sentiment, s.event_category, "
            "i.importance_score "
            "FROM news_articles a "
            "LEFT JOIN news_sentiment_assessments s ON s.article_id = a.id "
            "LEFT JOIN news_impact_assessments i ON i.article_id = a.id "
            "WHERE a.status IN ('PROCESSED', 'REVIEW') "
            "ORDER BY a.published_at DESC NULLS LAST, a.id DESC "
            "LIMIT :limit"
        ),
        {"limit": limit},
    ).all()
    return {
        "articles": [
            {
                "article_db_id": r[0],
                "title": r[1],
                "source": r[2],
                "canonical_url": r[3],
                "published_at": str(r[4]) if r[4] else None,
                "status": r[5],
                "sentiment": r[6],
                "event_category": r[7],
                "importance_score": r[8],
            }
            for r in rows
        ],
        "count": len(rows),
    }


def reconcile(session: Session) -> dict:
    """Read-only reconciliation: stored articles vs Phase 11 events
    vs evidence links. Counts are reported, never judged."""
    from sqlalchemy import text as _text

    def _count(table: str) -> int:
        row = session.execute(_text(f"SELECT COUNT(*) FROM {table}")).first()
        return int(row[0]) if row else 0

    return {
        "news_articles": _count("news_articles"),
        "news_events": _count("news_events"),
        "news_event_evidence": _count("news_event_evidence"),
        "news_collection_runs": _count("news_collection_runs"),
        "news_articles_processed": int(
            session.execute(
                _text(
                    "SELECT COUNT(*) FROM news_articles "
                    "WHERE status IN ('PROCESSED', 'REVIEW')"
                )
            ).first()[0]
        ),
    }
