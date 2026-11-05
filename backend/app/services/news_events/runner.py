"""Phase 11 runner: registry + alias map + seed events, idempotent.

--dry-run computes everything and writes nothing; --commit writes and a
second --commit writes 0 new rows. Seed events come ONLY from rows
already in the database (Phase 7 documents, Phase 10 macro events).
No HTTP fetch happens anywhere in this module.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.financial import FinancialDocument
from app.models.governance import DataSource
from app.models.macro import MacroEvent
from app.models.news_events import (
    CompanyAlias,
    NewsEvent,
    NewsEventCompany,
    NewsSource,
)
from app.models.reference import Company, Security
from app.services.news_events import SOURCES
from app.services.news_events.aliases import build_alias_index
from app.services.news_events.collectors import build_seed_events
from app.services.news_events.dedup import content_hash, group_key
from app.services.news_events.resolver import resolve_text
from app.services.news_events.scoring import review_status, score_event

PKT = ZoneInfo("Asia/Karachi")


def _pkt_midnight(iso_date: str | None):
    if not iso_date:
        return None
    return datetime.fromisoformat(iso_date).replace(tzinfo=PKT)


def _get_or_create_data_source(session: Session, key: str, commit: bool):
    row = session.query(DataSource).filter_by(source_key=key).one_or_none()
    if row is None and commit:
        name, _pub, source_type, _pol, base_url, terms_note, _status = SOURCES[key]
        row = DataSource(
            source_key=key,
            display_name=name,
            source_type=source_type,
            base_reference=base_url or "",
            verification_status="UNVERIFIED",
            terms_summary=terms_note,
        )
        session.add(row)
        session.flush()
    return row


def run_news(session: Session, commit: bool) -> dict:
    today = datetime.now(PKT).date()

    # ---- sources ------------------------------------------------------
    sources_upserted = 0
    source_rows: dict[str, NewsSource | None] = {}
    for key, (
        name,
        publisher,
        source_type,
        policy,
        base_url,
        terms_note,
        status,
    ) in SOURCES.items():
        row = session.query(NewsSource).filter_by(source_key=key).one_or_none()
        if row is None:
            if commit:
                row = NewsSource(
                    source_key=key,
                    name=name,
                    publisher=publisher,
                    source_type=source_type,
                    collection_policy=policy,
                    base_url=base_url,
                    terms_note=terms_note,
                    excerpt_limit_chars=280,
                    collection_status=status,
                )
                session.add(row)
                session.flush()
            sources_upserted += 1
        else:
            if commit and (row.collection_policy != policy or row.collection_status != status):
                row.collection_policy = policy
                row.collection_status = status
                session.flush()
        source_rows[key] = row

    # ---- data source provenance rows ----------------------------------
    data_source_rows: dict[str, DataSource | None] = {}
    for key in SOURCES:
        data_source_rows[key] = _get_or_create_data_source(session, key, commit)

    # ---- alias map ----------------------------------------------------
    companies = session.query(Company.id, Company.legal_name).order_by(Company.id).all()
    tickers = {sec.company_id: sec.ticker for sec in session.query(Security).all()}
    company_rows = [(cid, legal, tickers.get(cid, "")) for cid, legal in companies]
    index = build_alias_index(company_rows)
    ambiguous_aliases = sum(1 for rows in index.values() if len({r[0] for r in rows}) > 1)

    aliases_inserted = 0
    aliases_skipped = 0
    for company_id, legal_name, ticker in company_rows:
        for alias, alias_type, conf in _aliases_for(company_id, index):
            existing = (
                session.query(CompanyAlias)
                .filter_by(company_id=company_id, alias_normalized=alias)
                .one_or_none()
            )
            if existing is not None:
                aliases_skipped += 1
                continue
            aliases_inserted += 1
            if commit:
                ambiguous = any(r[3] for r in index.get(alias, []) if r[0] == company_id)
                session.add(
                    CompanyAlias(
                        company_id=company_id,
                        alias_normalized=alias,
                        alias_type=alias_type,
                        confidence=conf,
                        is_ambiguous=ambiguous,
                    )
                )
    if commit:
        session.flush()

    # ---- seed events --------------------------------------------------
    documents = [
        {
            "id": d.id,
            "company_id": d.company_id,
            "ticker": tickers.get(d.company_id),
            "document_type": d.document_type,
            "title": d.title,
            "source_url": d.source_url,
            "company_name": dict((c.id, c.legal_name) for c in companies).get(d.company_id),
        }
        for d in session.query(FinancialDocument).order_by(FinancialDocument.id).all()
    ]
    macro_events = [
        {
            "id": m.id,
            "event_date": m.event_date.isoformat() if m.event_date else None,
            "event_type": m.event_type,
            "title": m.title,
            "quality_status": m.quality_status,
        }
        for m in session.query(MacroEvent).order_by(MacroEvent.id).all()
    ]
    seed_events, skipped_unknown = build_seed_events(documents, macro_events)

    existing_keys = {row[0] for row in session.query(NewsEvent.canonical_key).all()}
    existing_hashes = {
        row[0]
        for row in session.query(NewsEvent.content_hash)
        .filter(NewsEvent.content_hash.isnot(None))
        .all()
    }

    events_inserted = 0
    events_skipped_existing = 0
    events_skipped_duplicate = 0
    for event in seed_events:
        key = group_key(event)
        chash = content_hash(event["headline"], event["canonical_url"])
        if key in existing_keys:
            events_skipped_existing += 1
            continue
        if chash in existing_hashes:
            events_skipped_duplicate += 1
            continue
        existing_keys.add(key)
        existing_hashes.add(chash)
        score = score_event(
            event["source_type"],
            event["scope"],
            event["novelty"],
            event["transmission"],
        )
        from datetime import date as _date

        event_date = _date.fromisoformat(event["event_date"]) if event["event_date"] else None
        status = review_status(
            confidence=event["match_confidence"],
            ambiguous=False,
            date_status=event["date_status"],
            score=score,
            event_date=event_date,
            today=today,
        )
        events_inserted += 1
        if not commit:
            continue
        source_row = source_rows[event["source_key"]]
        resolver_matches = resolve_text(event["headline"], index)
        row = NewsEvent(
            event_date=event_date,
            date_status=event["date_status"],
            event_type=event["event_type"],
            headline=event["headline"][:500],
            summary=(event["summary"] or "")[:280] or None,
            canonical_url=event["canonical_url"],
            publisher=event["publisher"],
            source_id=source_row.id if source_row is not None else None,
            source_type=event["source_type"],
            content_hash=chash,
            canonical_key=key,
            primary_company_id=event["primary_company_id"],
            relevance_score=score,
            review_status=status,
            match_evidence={
                "basis": event["match_basis"],
                "confidence": event["match_confidence"],
                "evidence": event["match_evidence"],
                "resolver_matches": [
                    {
                        "company_id": m["company_id"],
                        "alias": m["alias"],
                        "confidence": m["confidence"],
                    }
                    for m in resolver_matches
                ],
            },
            macro_event_id=event["macro_event_id"],
            document_id=event["document_id"],
            data_source_id=(
                data_source_rows[event["source_key"]].id
                if data_source_rows[event["source_key"]] is not None
                else None
            ),
            source_key=event["source_key"],
            source_timestamp=_pkt_midnight(event["event_date"]),
            collected_at=datetime.now(PKT),
            quality_status=event["quality_status"],
        )
        session.add(row)
        session.flush()
        if event["primary_company_id"] is not None:
            session.add(
                NewsEventCompany(
                    event_id=row.id,
                    company_id=event["primary_company_id"],
                    match_type=event["match_basis"],
                    match_confidence=event["match_confidence"],
                    match_evidence=event["match_evidence"],
                )
            )
    if commit:
        session.flush()

    # ---- report -------------------------------------------------------
    covered = (
        session.query(NewsEvent.primary_company_id)
        .filter(NewsEvent.primary_company_id.isnot(None))
        .distinct()
        .count()
        if commit
        else len({e["primary_company_id"] for e in seed_events if e["primary_company_id"]})
    )
    review_counts: dict = {}
    if commit:
        for row in session.query(NewsEvent.review_status).all():
            review_counts[row[0]] = review_counts.get(row[0], 0) + 1
    else:
        review_counts = {"dry_run": len(seed_events)}

    gate = {
        "coverage_across_universe": {
            "pass": False,
            "reason": f"seed events cover {covered} of {len(companies)} companies; "
            "universe-wide coverage needs PSX announcements (TERMS_GATED) "
            "and per-outlet terms review",
        },
        "false_positives_ambiguous_tested": {
            "pass": True,
            "reason": "resolver tests: ticker substrings, generic words, "
            "abbreviation non-expansion, ambiguous-alias capping",
        },
        "official_vs_secondary_distinguished": {
            "pass": True,
            "reason": "source_type on every event; registry separates official, "
            "official_filing, regulator and secondary",
        },
        "no_copyrighted_corpus_redistributed": {
            "pass": True,
            "reason": "no article-body column; summaries capped at 280 chars; "
            "no full text collected or stored",
        },
    }

    return {
        "sources_upserted": sources_upserted,
        "aliases_inserted": aliases_inserted,
        "aliases_skipped_existing": aliases_skipped,
        "ambiguous_aliases": ambiguous_aliases,
        "events_inserted": events_inserted,
        "events_skipped_existing": events_skipped_existing,
        "events_skipped_duplicate": events_skipped_duplicate,
        "events_skipped_unknown_type": skipped_unknown,
        "companies_covered": covered,
        "universe_companies": len(companies),
        "review_counts": review_counts,
        "gate": gate,
        "verdict": "PARTIALLY COMPLETE",
    }


def _aliases_for(company_id: int, index: dict) -> list[tuple[str, str, float]]:
    """All (alias, type, effective confidence) rows for one company."""
    out: list[tuple[str, str, float]] = []
    for alias, rows in index.items():
        for cid, alias_type, conf, _amb in rows:
            if cid == company_id:
                out.append((alias, alias_type, conf))
    return out
