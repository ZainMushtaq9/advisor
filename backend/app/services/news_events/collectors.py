"""Collectors (Phase 11).

Only one collector runs in this phase, and it touches no network: the
seed collector derives events from rows already in the database (Phase 7
financial documents, Phase 10 macro events). Every other source is
registry-only, and the PSX collector is a gated stub that refuses to run
until written PSX permission evidence exists.
"""

from __future__ import annotations

from app.services.news_events import (
    DOCUMENT_TYPE_TO_EVENT_TYPE,
    MACRO_EVENT_SOURCE,
    PUBLICATION_DATES,
    SEED_SUMMARIES,
    SOURCES,
)


class PolicyBlocked(Exception):
    """Raised when a collector is policy-gated. Never bypassed."""


def source_for_document(source_url: str | None) -> str:
    """Issuer IR by default; RNS-hosted filings map to rns_filing."""
    url = (source_url or "").lower()
    if "rns" in url or "londonstockexchange" in url:
        return "rns_filing"
    return "issuer_ir"


def build_seed_events(documents: list[dict], macro_events: list[dict]) -> list[dict]:
    """Build seed event dicts from already-stored DB rows.

    ``documents``: [{id, company_id, ticker, document_type, title,
    source_url, company_name}]. ``macro_events``: [{id, event_date
    (ISO str), event_type, title, quality_status}]. Unknown
    document/macro types are skipped and counted by the runner via the
    ``skipped`` list mechanism (returned as a second value).
    Publication dates and summaries resolve by TICKER (never by
    document id — ids shift across fresh imports).
    """
    events: list[dict] = []
    skipped: list[str] = []
    for doc in documents:
        event_type = DOCUMENT_TYPE_TO_EVENT_TYPE.get(doc["document_type"])
        if event_type is None:
            skipped.append(f"document {doc['id']}: unknown type {doc['document_type']}")
            continue
        ticker = doc.get("ticker")
        pub_date, pub_note = PUBLICATION_DATES.get(
            ticker, (None, f"no publication mapping for ticker {ticker}")
        )
        source_key = source_for_document(doc.get("source_url"))
        events.append(
            {
                "event_date": pub_date,
                "date_status": "known" if pub_date else "unknown",
                "event_type": event_type,
                "headline": doc["title"],
                "summary": SEED_SUMMARIES.get(ticker),
                "canonical_url": doc.get("source_url"),
                "publisher": doc.get("company_name") or "issuer",
                "source_key": source_key,
                "source_type": SOURCES[source_key][2],
                "primary_company_id": doc["company_id"],
                "document_id": doc["id"],
                "macro_event_id": None,
                "quality_status": "UNVERIFIED",
                "scope": "company",
                "transmission": "direct",
                "novelty": "first",
                "match_basis": "document_company_id",
                "match_confidence": 1.0,
                "match_evidence": (
                    f"seed link: Phase 7 document {doc['id']} belongs to "
                    f"company {doc['company_id']} (ticker {ticker}); {pub_note}"
                ),
            }
        )
    for macro in macro_events:
        source_key = MACRO_EVENT_SOURCE.get(macro["event_type"])
        if source_key is None:
            skipped.append(f"macro event {macro['id']}: unknown type {macro['event_type']}")
            continue
        events.append(
            {
                "event_date": macro["event_date"],
                "date_status": "known",
                "event_type": "macro_release",
                "headline": macro["title"],
                "summary": None,
                "canonical_url": None,
                "publisher": SOURCES[source_key][1],
                "source_key": source_key,
                "source_type": SOURCES[source_key][2],
                "primary_company_id": None,
                "document_id": None,
                "macro_event_id": macro["id"],
                "quality_status": macro.get("quality_status") or "UNVERIFIED",
                "scope": "macro",
                "transmission": "macro",
                "novelty": "first",
                "match_basis": "macro_calendar_link",
                "match_confidence": 1.0,
                "match_evidence": (
                    f"seed link: Phase 10 macro event {macro['id']} ({macro['event_type']})"
                ),
            }
        )
    return events, skipped


class GatedPsxCollector:
    """PSX announcements collector: refuses to run, by policy.

    Systematic retrieval of PSX announcements to build a collection is
    exactly what the PSX Terms of Use / Data Legal Notice prohibit
    without prior written permission, and no permission evidence exists.
    This stub exists so the gate is enforced in code (and tested), not
    just documented.
    """

    SOURCE_KEY = "psx_announcements"

    def run(self) -> list[dict]:
        raise PolicyBlocked(
            "PSX announcements collection is TERMS_GATED: systematic "
            "retrieval needs prior written PSX permission (Phase 5 Terms "
            "gate). No permission evidence exists. Unblocker: written PSX "
            "permission evidence, verified for its exact terms."
        )
