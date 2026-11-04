"""Phase 25 schedule evaluation and trading-calendar rules (pure functions).

No database, no network, no clock reads inside the evaluator:
callers pass explicit dates, so every result is hand-checkable
and unit-testable.

Time zone: all schedule dates are Asia/Karachi wall-clock
dates. Pakistan has no daylight saving (none since 2009), so a
wall-clock date plus a "HH:MM" time is unambiguous; the time
itself is descriptive only — due-ness is decided per DATE,
because the runner is invoked by an operator (or a host cron),
not by a resident daemon. This is the honest offline model:
the system never pretends a daemon is watching the clock.

Schedule spec shapes (``schedule_kind`` + ``schedule_spec``):

- daily:    {"time": "16:30", "weekdays": [0, 1, 2, 3, 4]}
            (weekdays: Monday=0 .. Sunday=6; omitted = every day)
- weekly:   {"time": "07:30", "weekday": 0}
- monthly:  {"time": "09:00", "day": 3}
- quarterly:{"time": "09:00", "months": [1, 4, 7, 10], "day": 15}
- annual:   {"time": "09:00", "month": 6, "day": 30}
- manual:   {} — never due; operator runs only.

Deliberate rules, documented because they are choices:

- A day-of-month that does not exist in a given month (31 in
  February, 29 February in a non-leap year) is SKIPPED, never
  silently moved to another day. A moved date would mislabel
  the occurrence and break the idempotency key.
- Catch-up is bounded: at most ``MAX_CATCHUP`` unprocessed
  occurrences per job per invocation, oldest first. An
  unbounded catch-up after a long offline period would storm
  the database and the operator; the backlog drains over
  successive invocations, and the operator can always run a
  single occurrence explicitly with run-one.
- Trading weekdays are Monday-Friday. There is NO verified
  PSX holiday calendar stored anywhere in this project, so
  the scheduler never claims a date is a PSX holiday. A date
  counts as an observed trading session only when stored
  price rows exist for it (callers supply that check); a
  post-close job due on a weekday with no observed session
  is still created (collection is paused anyway) and the
  operator sees the gap instead of a silent skip.
"""

from __future__ import annotations

import calendar as _calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

PKT = ZoneInfo("Asia/Karachi")

# Maximum missed occurrences materialised per job per run-due
# invocation. Bounds catch-up after offline periods.
MAX_CATCHUP = 7


def today_pkt(now: datetime | None = None) -> date:
    """Current Asia/Karachi date (``now`` injectable for tests)."""
    if now is None:
        now = datetime.now(PKT)
    if now.tzinfo is None:
        now = now.replace(tzinfo=PKT)
    return now.astimezone(PKT).date()


def is_trading_weekday(day: date) -> bool:
    """Monday-Friday. NOT a holiday calendar: no verified PSX
    holiday list exists in this project, so no date is ever
    claimed to be a holiday here."""
    return day.weekday() < 5


def _matches(day: date, kind: str, spec: dict) -> bool:
    if kind == "daily":
        weekdays = spec.get("weekdays")
        if weekdays is not None and day.weekday() not in weekdays:
            return False
        return True
    if kind == "weekly":
        weekday = spec.get("weekday")
        if weekday is not None and day.weekday() != weekday:
            return False
        return True
    if kind == "monthly":
        return day.day == spec.get("day")
    if kind == "quarterly":
        months = spec.get("months", [1, 4, 7, 10])
        return day.month in months and day.day == spec.get("day")
    if kind == "annual":
        return day.month == spec.get("month") and day.day == spec.get("day")
    # "manual" and anything unknown: never due.
    return False


def occurrences(kind: str, spec: dict, start: date, end: date) -> list[date]:
    """Every due date in [start, end] for this schedule.

    Pure date walk; a nonexistent day-of-month simply never
    matches, so it is skipped rather than moved.
    """
    if kind == "manual" or end < start:
        return []
    found: list[date] = []
    day = start
    while day <= end:
        if _matches(day, kind, spec):
            found.append(day)
        day += timedelta(days=1)
    return found


def due_occurrences(
    kind: str,
    spec: dict,
    last_processed: date | None,
    today: date,
    limit: int = MAX_CATCHUP,
) -> list[date]:
    """Unprocessed due dates: (last_processed, today], oldest
    first, capped at ``limit``. ``last_processed=None`` means
    nothing has ever been processed: the window starts 30 days
    back so a brand-new job does not try to replay history —
    the operator backfills explicitly with run-one if needed.
    """
    if kind == "manual":
        return []
    start = (last_processed + timedelta(days=1)) if last_processed else (today - timedelta(days=30))
    return occurrences(kind, spec, start, today)[:limit]


def idempotency_key(job_key: str, occurrence: date | None) -> str:
    """Stable key for one occurrence. Manual runs use
    ``job_key:manual`` and are unique per invocation only via
    the run-one ``--run-tag`` suffix (see runner)."""
    if occurrence is None:
        return f"{job_key}:manual"
    return f"{job_key}:{occurrence.isoformat()}"


def month_length(year: int, month: int) -> int:
    """Days in a month (used by tests and by the cadence doc)."""
    return _calendar.monthrange(year, month)[1]
