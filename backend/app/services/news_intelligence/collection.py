"""Permission-gated collection framework.

The gate is the product: a source is collected from ONLY when its
permission-register entry says COLLECTABLE (an official API, a
permitted RSS feed, or an authorized public endpoint) AND automated
fetching is approved for it. Every other source raises
``PolicyBlocked`` with the exact reason, and the runner records
the refusal instead of collecting. DPS/PSX is BLOCKED by the Terms
gate (see docs/news-intelligence/source_permission_register.md);
this module reuses the Phase 11 ``PolicyBlocked`` exception so
the gate is one mechanism, not two.

RSS/Atom parsing uses stdlib xml.etree only (no feedparser in the
venv, and no new dependency is added). HTML scraping is NOT
implemented here: HTML collection runs only when a source's
register entry explicitly permits it, and no current entry does
— adding an HTML collector needs its own permission review.

Timezone: Asia/Karachi throughout (zoneinfo). Trading weekdays
are Monday–Friday; no exchange-holiday calendar is claimed —
a missing trading day is tolerated as a data gap, never filled.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.services.news_events.collectors import PolicyBlocked

PKT = ZoneInfo("Asia/Karachi")

# Collection policies from the permission register. Only
# "COLLECTABLE" may be collected from, and only when the caller
# also passes automated_fetch_approved=True (a separate decision
# from the source being permitted).
COLLECTABLE_POLICY = "COLLECTABLE"

# Freshness display policy for news (engine policy, not a market
# rule): current <= 1 day, recent <= 7 days, stale beyond that.
# Stale is never relabelled current.
FRESHNESS_CURRENT_DAYS = 1
FRESHNESS_RECENT_DAYS = 7


def collection_allowed(
    source_key: str,
    collection_policy: str,
    automated_fetch_approved: bool,
) -> None:
    """Raise PolicyBlocked unless collection is permitted AND
    automated fetching is approved. The refusal message names the
    exact reason so a blocked run is evidence, not silence."""
    if collection_policy != COLLECTABLE_POLICY:
        raise PolicyBlocked(
            f"Source {source_key} is not collectable "
            f"(policy={collection_policy}). No collection attempted."
        )
    if not automated_fetch_approved:
        raise PolicyBlocked(
            f"Source {source_key} is permitted but automated fetching "
            "is not approved. Collection stays paused; manual sampled "
            "reads only."
        )


def backoff_delay_seconds(
    attempt: int,
    base_seconds: int = 60,
    cap_seconds: int = 3600,
) -> int:
    """Bounded exponential backoff (deterministic, no jitter, so
    tests can assert it exactly). attempt 0 -> base, then doubles
    up to the cap. Negative attempts are treated as 0."""
    attempt = max(0, int(attempt))
    return min(cap_seconds, base_seconds * (2 ** attempt))


def normalize_published_at(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp into an aware datetime.

    Naive values are treated as Asia/Karachi local time (the
    market's timezone) and labelled as such by the caller — never
    silently assumed to be UTC. Unparseable values return None
    (date unknown), never a guessed date.
    """
    if not value or not value.strip():
        return None
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=PKT)
    return parsed


def freshness_status(
    published_at: datetime | None,
    now: datetime | None = None,
) -> str:
    """current / recent / stale / unknown (never 'current' for a
    missing or future-dated publication)."""
    if published_at is None:
        return "unknown"
    now = now or datetime.now(timezone.utc)
    if published_at > now:
        return "unknown"
    age = now - published_at
    if age <= timedelta(days=FRESHNESS_CURRENT_DAYS):
        return "current"
    if age <= timedelta(days=FRESHNESS_RECENT_DAYS):
        return "recent"
    return "stale"


def is_trading_weekday(day: datetime | None) -> bool:
    """Monday–Friday. No holiday calendar is claimed: a weekday
    that is actually a holiday is a data gap, handled downstream
    as missing data, never filled."""
    if day is None:
        return False
    return day.weekday() < 5


def parse_rss_items(feed_xml: str) -> list[dict]:
    """Parse RSS 2.0 / Atom items into metadata dicts.

    Returns [{title, link, published, summary}] with summary
    capped at 280 chars (excerpt discipline). Full article bodies
    are never parsed or stored. Malformed XML raises ValueError
    (a source failure, recorded by the runner, not hidden).
    """
    try:
        root = ET.fromstring(feed_xml)
    except ET.ParseError as exc:
        raise ValueError(f"unparseable feed XML: {exc}") from exc

    def _text(element: ET.Element | None) -> str:
        if element is None or element.text is None:
            return ""
        return re.sub(r"\s+", " ", element.text).strip()

    items: list[dict] = []
    for item in root.iter("item"):
        title = _text(item.find("title"))
        link = _text(item.find("link"))
        published = _text(item.find("pubDate")) or _text(item.find("pubdate"))
        summary = _text(item.find("description"))[:280]
        if title and link:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "published": published,
                    "summary": summary,
                }
            )
    if not items:
        # Atom: entry/link[@rel='alternate'].
        for entry in root.iter():
            if not entry.tag.endswith("entry"):
                continue
            title = _text(entry.find("./{http://www.w3.org/2005/Atom}title"))
            link = ""
            for link_el in entry.findall("./{http://www.w3.org/2005/Atom}link"):
                if link_el.get("rel", "alternate") == "alternate":
                    link = link_el.get("href", "")
                    break
            published = _text(entry.find("./{http://www.w3.org/2005/Atom}published"))
            summary = _text(entry.find("./{http://www.w3.org/2005/Atom}summary"))[:280]
            if title and link:
                items.append(
                    {
                        "title": title,
                        "link": link,
                        "published": published,
                        "summary": summary,
                    }
                )
    return items


def article_content_hash(title: str, canonical_url: str | None) -> str:
    """SHA-256 of normalized title + '|' + URL (same grain as
    Phase 11 content_hash, so an article and its event dedup
    against each other)."""
    from app.services.news_events.dedup import content_hash

    return content_hash(title, canonical_url)


def article_fingerprint(title: str, canonical_url: str | None) -> str:
    """Stable article id grain: sha256 of the content hash (the
    article_id stored on processed records)."""
    return hashlib.sha256(
        article_content_hash(title, canonical_url).encode("utf-8")
    ).hexdigest()[:32]
