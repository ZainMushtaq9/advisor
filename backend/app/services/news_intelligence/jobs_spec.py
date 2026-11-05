"""News job specifications for the Phase 25 job system.

These three definitions are the single source of truth for news
jobs: ``backend/app/services/jobs/registry.py`` extends its
JOB_DEFINITIONS with NEWS_JOB_DEFINITIONS, so ``scripts/run_jobs.py
register`` seeds them idempotently and preserves any
operator-changed status on re-registration.

Statuses are deliberate, not placeholders:

- news_collection_daily: PAUSED. No automated fetch is approved
  for any source (PSX Terms gate; SBP/PBS manual-read precedent;
  per-outlet news terms unreviewed). The handler enforces the gate
  and records refused runs; it never fetches.
- news_reconciliation_post_close: PAUSED for the same reason in
  Phase A — it runs only after the close against stored rows, and
  its first live run belongs to Phase B. (Its handler is read-only
  and safe; the pause is a scheduling decision, not a code gap.)
- news_digest: ACTIVE. Read-only digest over stored rows; it sends
  nothing anywhere. The digest is a run summary the dashboard shows.

No job here performs an external send, a purchase, or a trade.
"""

from __future__ import annotations

NEWS_JOB_DEFINITIONS: list[dict] = [
    {
        "job_key": "news_collection_daily",
        "title": "Daily news collection (permitted sources only)",
        "handler_key": "news_collection_daily",
        "schedule_kind": "daily",
        "schedule_spec": {"time": "17:00", "weekdays": [0, 1, 2, 3, 4]},
        "dependencies": [],
        "timeout_seconds": 1800,
        "max_attempts": 2,
        "backoff_base_seconds": 300,
        "priority": 5,
        "status": "paused",
        "pause_reason": (
            "No automated fetch approved for any news source: PSX "
            "announcements are TERMS_GATED (written permission pending, "
            "user-owned); SBP/PBS reads were manual official reads, not "
            "an approved automated fetch; per-outlet news terms are "
            "unreviewed. The handler enforces the gate and records "
            "refused runs; it never fetches."
        ),
    },
    {
        "job_key": "news_reconciliation_post_close",
        "title": "Post-close news/event reconciliation",
        "handler_key": "news_reconciliation_post_close",
        "schedule_kind": "daily",
        "schedule_spec": {"time": "17:30", "weekdays": [0, 1, 2, 3, 4]},
        "dependencies": ["news_collection_daily"],
        "timeout_seconds": 600,
        "max_attempts": 2,
        "backoff_base_seconds": 300,
        "priority": 6,
        "status": "paused",
        "pause_reason": (
            "Scheduling decision: reconciliation runs against stored "
            "rows only and its handler is read-only, but its first "
            "live run belongs to Phase B, after the Phase B live "
            "seed. The runner refuses paused jobs, so it cannot run "
            "before then."
        ),
    },
    {
        "job_key": "news_digest",
        "title": "Daily in-app news digest",
        "handler_key": "news_digest",
        "schedule_kind": "daily",
        "schedule_spec": {"time": "08:00"},
        "dependencies": [],
        "timeout_seconds": 300,
        "max_attempts": 2,
        "backoff_base_seconds": 60,
        "priority": 6,
        "status": "active",
        "pause_reason": None,
    },
]
