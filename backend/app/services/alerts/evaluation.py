"""Phase 21 alert evaluation: pure functions, no DB, no network.

Every function here works on plain dicts so the rules can be
unit-tested without a database. The runner loads stored rows
into these dict shapes and commits the results; nothing here
touches the database, the clock beyond the passed processing
time, or any external channel.

Suppression reasons (a suppressed candidate is counted, never
silently dropped):
- FUTURE_SCHEDULED: event date after the evaluation date.
- STALE: event date older than the rule's maximum event age,
  measured against the processing date.
- UNKNOWN_DATE: the source event carries no usable date.
- NO_EVENT_DATE: the source record exists but publishes no
  event date at all (dividend actions).
- NO_SERIES: the rule needs a series that does not exist
  (valuation history, calculable indicators, previous closes).
- FREQUENCY_LIMIT: the rule's daily limit is already reached.
Duplicates are counted separately as duplicates_skipped: the
same (rule, subject, event date) was already alerted.

Dedup key: ``rule_key|source_ref|event_date`` where the
source ref identifies the stored source row (e.g.
``risk_flags:12``). Keying on the source event — not just on
subject and date — is what keeps distinct events apart: one
company can carry several flags on the same as-of date, and
each is its own alert. The key never contains a price, a
score, or any invented value.
"""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.services.alerts import FLAG_SEVERITY_MAP, TIMEZONE

TZ = ZoneInfo(TIMEZONE)

# Lifecycle state machine. RESOLVED is terminal. Anything not
# listed here raises ValueError.
ALLOWED_TRANSITIONS = {
    ("NEW", "acknowledge"): "ACKNOWLEDGED",
    ("NEW", "mute"): "MUTED",
    ("NEW", "resolve"): "RESOLVED",
    ("ACKNOWLEDGED", "mute"): "MUTED",
    ("ACKNOWLEDGED", "resolve"): "RESOLVED",
    ("MUTED", "unmute"): "NEW",
    ("MUTED", "resolve"): "RESOLVED",
}


def dedup_key(rule_key: str, source_ref: str, event_date: date) -> str:
    """Build the deduplication key for one candidate alert."""
    return f"{rule_key}|{source_ref}|{event_date.isoformat()}"


def event_datetime(event_date: date) -> datetime:
    """Midnight Asia/Karachi on the event date (stored event dates
    are dates, not timestamps; the conversion is explicit and
    never pretends to be an intraday time)."""
    return datetime.combine(event_date, time(0, 0), tzinfo=TZ)


def classify_event(
    rule: dict, event_date: date | None, as_of: date, processing_date: date
) -> str | None:
    """Return a suppression reason, or None when the event may fire.

    Order matters: an unknown date is not stale, and a future
    event is not stale either.
    """
    if event_date is None:
        return "UNKNOWN_DATE"
    if event_date > as_of:
        return "FUTURE_SCHEDULED"
    if (processing_date - event_date).days > rule["max_event_age_days"]:
        return "STALE"
    return None


def in_quiet_window(
    processing_time: datetime,
    quiet_start: time | None,
    quiet_end: time | None,
) -> bool:
    """True when the processing time falls inside the quiet window.

    A window with no start or end never defers anything. A
    window that wraps midnight (e.g. 23:00-07:00) defers times
    at or after the start OR before the end.
    """
    if quiet_start is None or quiet_end is None:
        return False
    now = processing_time.astimezone(TZ).time()
    if quiet_start <= quiet_end:
        return quiet_start <= now < quiet_end
    return now >= quiet_start or now < quiet_end


def apply_frequency_limit(rule: dict, created_today: int, candidate_count: int) -> tuple[int, int]:
    """Split candidates into (allowed, suppressed) under the rule's
    daily limit. Rules without a limit allow everything."""
    limit = rule.get("daily_limit")
    if limit is None:
        return candidate_count, 0
    allowed = max(0, limit - created_today)
    if candidate_count <= allowed:
        return candidate_count, 0
    return allowed, candidate_count - allowed


def transition(status: str, action: str) -> str:
    """Apply one lifecycle action, or raise ValueError."""
    key = (status, action)
    if key not in ALLOWED_TRANSITIONS:
        raise ValueError(f"Cannot {action} an alert in status {status}")
    return ALLOWED_TRANSITIONS[key]


def map_flag_severity(flag_severity: str) -> str:
    """Map a stored risk-flag severity to an alert severity."""
    if flag_severity not in FLAG_SEVERITY_MAP:
        raise ValueError(f"Unknown flag severity: {flag_severity!r}")
    return FLAG_SEVERITY_MAP[flag_severity]


def evaluate_candidates(
    rule: dict,
    candidates: list[dict],
    as_of: date,
    processing_time: datetime,
) -> tuple[list[dict], dict[str, int]]:
    """Apply staleness/future/date gating to raw candidates.

    Each candidate carries: subject_type, ticker (nullable),
    company_id (nullable), sector (nullable), event_date
    (nullable), title, evidence (dict), source_ref (str, the
    stored source row reference, e.g. ``risk_flags:12``),
    quality_status (str), and optionally severity (which
    overrides the rule severity, used by risk flags).

    Returns (alerts, suppressed_counts). Alerts carry their
    dedup key, event/processing times, and as-of date; the
    runner adds rule_id and persistence. Suppressed candidates
    are counted by reason and never turned into alerts.
    """
    processing_date = processing_time.astimezone(TZ).date()
    alerts: list[dict] = []
    suppressed: dict[str, int] = {}
    for candidate in candidates:
        reason = classify_event(rule, candidate["event_date"], as_of, processing_date)
        if reason is not None:
            suppressed[reason] = suppressed.get(reason, 0) + 1
            continue
        event_date = candidate["event_date"]
        alerts.append(
            {
                "rule_key": rule["rule_key"],
                "subject_type": candidate["subject_type"],
                "ticker": candidate.get("ticker"),
                "company_id": candidate.get("company_id"),
                "sector": candidate.get("sector"),
                "event_time": event_datetime(event_date),
                "processing_time": processing_time,
                "as_of_date": as_of,
                "severity": candidate.get("severity") or rule["severity"],
                "origin": rule["origin"],
                "title": candidate["title"],
                "evidence": candidate["evidence"],
                "dedup_key": dedup_key(
                    rule["rule_key"],
                    candidate["source_ref"],
                    event_date,
                ),
                "quality_status": candidate.get("quality_status", "UNVERIFIED"),
            }
        )
    return alerts, suppressed


def valuation_change_candidates(rows: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Compute valuation-change candidates from stored valuation
    rows (pure; row dicts carry security_id, method,
    valuation_date, estimated_value, row_id, quality_status).

    Pairs are grouped by (security_id, method); only pairs with
    at least two rows are comparable, and the two latest rows
    by (valuation_date, row_id) are compared. A pair whose
    latest values are both present and different yields one
    candidate; equal values yield UNCHANGED; a missing value
    yields NO_VALUE. When no pair has two rows at all, the
    whole rule yields NO_SERIES (one suppression representing
    the missing series, not one per method).
    """
    by_pair: dict[tuple, list[dict]] = {}
    for row in rows:
        by_pair.setdefault((row["security_id"], row["method"]), []).append(row)
    comparable = {pair: pair_rows for pair, pair_rows in by_pair.items() if len(pair_rows) >= 2}
    if not comparable:
        return [], {"NO_SERIES": 1}
    candidates: list[dict] = []
    suppressed: dict[str, int] = {}
    for pair_rows in comparable.values():
        ordered = sorted(pair_rows, key=lambda r: (r["valuation_date"], r["row_id"]))
        old, new = ordered[-2], ordered[-1]
        if old["estimated_value"] is None or new["estimated_value"] is None:
            suppressed["NO_VALUE"] = suppressed.get("NO_VALUE", 0) + 1
            continue
        if old["estimated_value"] == new["estimated_value"]:
            suppressed["UNCHANGED"] = suppressed.get("UNCHANGED", 0) + 1
            continue
        candidates.append(
            {
                "security_id": new["security_id"],
                "method": new["method"],
                "event_date": new["valuation_date"],
                "old_value": old["estimated_value"],
                "new_value": new["estimated_value"],
                "old_row_id": old["row_id"],
                "new_row_id": new["row_id"],
                "quality_status": new["quality_status"],
            }
        )
    return candidates, suppressed


def paginate(items: list, limit: int, offset: int) -> list:
    """Validated slice helper shared by the API layer. Raises
    ValueError on out-of-range parameters (the endpoint maps it
    to HTTP 400)."""
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("offset must be >= 0")
    return items[offset : offset + limit]
