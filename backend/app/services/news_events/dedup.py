"""Event dedup and content hashing (Phase 11).

- content_hash = sha256(normalized headline + "|" + canonical URL or
  ""). Two rows with the same non-null content hash are the same
  content; the unique partial index enforces it in the database.
- canonical_key = (primary company or 'macro') | event type | date or
  'unknown' | headline core (normalized, suffix-stripped, first 80
  chars). Two items sharing a canonical key are the same underlying
  event; the second becomes a syndicated/coverage link, never a second
  event.
- Headline core uses the same suffix stripping as aliases so that
  "AGHA STEEL IND LTD" and "AGHA STEEL IND" headlines group together
  when company, type and date already agree.
"""

from __future__ import annotations

import hashlib

from app.services.news_events.aliases import normalize, strip_suffixes


def headline_core(headline: str) -> str:
    """Normalized, suffix-stripped headline truncated to 80 chars."""
    return strip_suffixes(normalize(headline))[:80]


def content_hash(headline: str, canonical_url: str | None) -> str:
    """SHA-256 of normalized headline + '|' + canonical URL (or '')."""
    payload = normalize(headline) + "|" + (canonical_url or "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_key(
    primary_company_id: int | None,
    event_type: str,
    event_date: str | None,
    headline: str,
) -> str:
    """Dedup grain for one underlying event."""
    company_part = str(primary_company_id) if primary_company_id else "macro"
    date_part = event_date or "unknown"
    return f"{company_part}|{event_type}|{date_part}|{headline_core(headline)}"


def group_key(event: dict) -> str:
    """Canonical key for an event dict (runner/seed shape)."""
    return canonical_key(
        event.get("primary_company_id"),
        event["event_type"],
        event.get("event_date"),
        event["headline"],
    )
