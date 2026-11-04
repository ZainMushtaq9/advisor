"""Quality assignment and freshness for daily OHLCV — Phase 5.

V1 freshness rule (the ONLY freshness rule in this version): an
observation whose collected_at is more than 30 days after its
trading_date is labelled STALE, in addition to its quality status.
Freshness is a separate label, not a replacement for quality_status:
quality_status stays one of UNVERIFIED / PARTIALLY_VERIFIED / VERIFIED /
CONFLICTED (see below), and the API and ingestion report carry a
``freshness`` field of STALE / CURRENT / UNKNOWN alongside it.
UNKNOWN means collected_at is absent, so the rule cannot be applied —
never a claim that the observation is fresh. No other freshness rule
exists in v1; nothing here infers freshness from a source, a delay
estimate, or a market calendar.

Quality rules (grain = one security x one trading_date x bar_type
"daily"; sources are distinguished by data_source_id, so conflicting
sources are stored side-by-side, never merged):
  - a single-source observation is UNVERIFIED, never VERIFIED;
  - two sources agreeing exactly on OHLCV for the same grain are
    PARTIALLY_VERIFIED;
  - if one of the agreeing sources is official AND another source
    agrees, the observation is VERIFIED. "Official" is the Phase 4
    constant OFFICIAL_SOURCES (psx_official, secp): the data_sources
    table has no boolean official flag, so source_key membership in
    that set is the official marker, exactly as in registry
    verification.py;
  - sources disagreeing on the same grain are each CONFLICTED: the
    disagreeing rows are stored side-by-side and no winner is picked.

Immutability caveat (Phase 3 triggers): market_prices rows cannot be
updated. Quality is therefore computed at insert time, against rows
already stored and against other rows in the same ingestion run. A row
ingested in a LATER run that disagrees with an already-stored row is
itself stored as CONFLICTED, but the earlier row keeps the status it
was stored with — it cannot be retroactively re-flagged. The conflict
remains visible because the grain then holds differing values with a
CONFLICTED row present. Within a single run, both disagreeing rows are
flagged CONFLICTED at insert time.

All stored prices are official unadjusted values: is_adjusted=False.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from app.models.registry import OFFICIAL_SOURCES

STALE_AFTER_DAYS = 30

FRESHNESS_STALE = "STALE"
FRESHNESS_CURRENT = "CURRENT"
FRESHNESS_UNKNOWN = "UNKNOWN"


def is_official_source(source_key: str | None) -> bool:
    return source_key in OFFICIAL_SOURCES


def freshness_label(
    collected_at: datetime | None, trading_date: date
) -> str:
    """Apply the v1 freshness rule only. Returns STALE / CURRENT /
    UNKNOWN (see module docstring)."""
    if collected_at is None:
        return FRESHNESS_UNKNOWN
    collected_date = collected_at.date()
    if (collected_date - trading_date).days > STALE_AFTER_DAYS:
        return FRESHNESS_STALE
    return FRESHNESS_CURRENT


def is_stale(collected_at: datetime | None, trading_date: date) -> bool:
    return freshness_label(collected_at, trading_date) == FRESHNESS_STALE


def assign_quality(
    candidate_source_key: str | None,
    candidate_ohlcv: tuple[Decimal, Decimal, Decimal, Decimal, int],
    other_observations: list[tuple[str | None, tuple[Decimal, Decimal, Decimal, Decimal, int]]],
) -> str:
    """Assign a quality status for one candidate observation.

    ``other_observations`` are the (source_key, OHLCV) pairs already
    known for the same grain from DIFFERENT sources (stored rows and/or
    other rows in the same run). An empty list means a single-source
    observation: UNVERIFIED, never VERIFIED from one source.
    """
    if not other_observations:
        return "UNVERIFIED"
    agreeing_sources = [
        source_key
        for source_key, ohlcv in other_observations
        if ohlcv == candidate_ohlcv
    ]
    if agreeing_sources:
        if is_official_source(candidate_source_key) or any(
            is_official_source(source_key) for source_key in agreeing_sources
        ):
            return "VERIFIED"
        return "PARTIALLY_VERIFIED"
    return "CONFLICTED"
