"""Phase 25 job registry: the seed definitions and the drift baseline.

Every definition states its real-world cadence and why. Jobs
that would collect new market data are registered PAUSED with
the exact reason: the runner refuses paused jobs, so pausing
is enforcement, not a label. Nothing in this registry polls
any source: the runner is invoked by an operator (or a host
cron), runs one pass, and exits. There is no resident daemon,
no hosted workflow service, and no paid scheduler anywhere.

Cadence rationale (see docs/phase-25/scheduling_cadence.md):

- PSX trades Monday-Friday; post-close work belongs after
  the close, so the market job is a 16:30 PKT weekday job.
  It stays PAUSED until written PSX permission evidence
  exists (Phase 5 Terms gate, user-owned).
- Issuer filings arrive quarterly/annually; the filing check
  is a quarterly job. It stays PAUSED: automated issuer-page
  polling is not approved, and DPS filing-download terms are
  not established — sampled manual checks only.
- SBP monetary policy is roughly six-weekly and PBS CPI is
  monthly; the macro check is a monthly job. It stays
  PAUSED: no automated fetch is approved; Phase 10 reads
  were manual official reads.
- The enabled jobs are all read-only recomputations over
  stored rows (health, drift, digest, QA audit) plus one
  manual-only retention job. They need no permission, no
  network, and no new data.

EXPECTED_COUNTS is the drift baseline: row counts verified
live at the end of Phase 24 (2026-11-05). The drift_check
handler compares the live database against these numbers and
reports every difference; it never writes a business row.
When a later phase legitimately changes a count (new
company load, HBL statements, a new phase's tables), that
phase updates this baseline explicitly with its evidence —
a drift report is then a finding, not an error to hide.
"""

from __future__ import annotations

# One entry per job. "status" is the SEED status only:
# register() preserves an operator-changed status on
# re-registration, so re-seeding never re-enables a job an
# operator paused (or vice versa).
JOB_DEFINITIONS: list[dict] = [
    {
        "job_key": "market_post_close",
        "title": "Daily post-close market collection",
        "handler_key": "collection_market_post_close",
        "schedule_kind": "daily",
        "schedule_spec": {"time": "16:30", "weekdays": [0, 1, 2, 3, 4]},
        "dependencies": [],
        "timeout_seconds": 1800,
        "max_attempts": 3,
        "backoff_base_seconds": 300,
        "priority": 1,
        "status": "paused",
        "pause_reason": (
            "Terms evidence pending: no new PSX collection without "
            "written PSX permission (Phase 5 Terms gate, user-owned). "
            "The runner refuses paused jobs, so this job cannot run."
        ),
    },
    {
        "job_key": "filing_check",
        "title": "Quarterly/annual filing availability check",
        "handler_key": "collection_filing_check",
        "schedule_kind": "quarterly",
        "schedule_spec": {"time": "09:00", "months": [1, 4, 7, 10], "day": 15},
        "dependencies": [],
        "timeout_seconds": 1800,
        "max_attempts": 2,
        "backoff_base_seconds": 300,
        "priority": 5,
        "status": "paused",
        "pause_reason": (
            "Automated issuer-page polling not approved; sampled "
            "manual checks only. DPS filing-download terms are not "
            "established (Phase 7 blocker 2)."
        ),
    },
    {
        "job_key": "macro_release_check",
        "title": "Monthly macro release check (PBS CPI / SBP MPS)",
        "handler_key": "collection_macro_release_check",
        "schedule_kind": "monthly",
        "schedule_spec": {"time": "09:00", "day": 3},
        "dependencies": [],
        "timeout_seconds": 1800,
        "max_attempts": 2,
        "backoff_base_seconds": 300,
        "priority": 5,
        "status": "paused",
        "pause_reason": (
            "No automated fetch approved; Phase 10 macro reads were "
            "manual official reads (SBP/PBS pages). Automated "
            "polling of those pages is not authorised."
        ),
    },
    {
        "job_key": "system_health",
        "title": "Daily system health check",
        "handler_key": "system_health",
        "schedule_kind": "daily",
        "schedule_spec": {"time": "07:00"},
        "dependencies": [],
        "timeout_seconds": 300,
        "max_attempts": 3,
        "backoff_base_seconds": 60,
        "priority": 1,
        "status": "active",
        "pause_reason": None,
    },
    {
        "job_key": "alert_digest",
        "title": "Daily in-app alert digest",
        "handler_key": "alert_digest",
        "schedule_kind": "daily",
        "schedule_spec": {"time": "08:00"},
        "dependencies": [],
        "timeout_seconds": 300,
        "max_attempts": 3,
        "backoff_base_seconds": 60,
        "priority": 2,
        "status": "active",
        "pause_reason": None,
    },
    {
        "job_key": "drift_check",
        "title": "Weekly stored-state drift check",
        "handler_key": "drift_check",
        "schedule_kind": "weekly",
        "schedule_spec": {"time": "07:30", "weekday": 0},
        "dependencies": [],
        "timeout_seconds": 600,
        "max_attempts": 3,
        "backoff_base_seconds": 60,
        "priority": 3,
        "status": "active",
        "pause_reason": None,
    },
    {
        "job_key": "report_qa_audit",
        "title": "Weekly report QA audit",
        "handler_key": "report_qa_audit",
        "schedule_kind": "weekly",
        "schedule_spec": {"time": "08:00", "weekday": 6},
        # Only meaningful if the stored state itself has not
        # drifted: if drift_check errored, this run waits
        # (status "blocked") instead of auditing bad numbers.
        "dependencies": ["drift_check"],
        "timeout_seconds": 600,
        "max_attempts": 3,
        "backoff_base_seconds": 60,
        "priority": 4,
        "status": "active",
        "pause_reason": None,
    },
    {
        "job_key": "retention_purge",
        "title": "Auth audit-log retention purge (12 months)",
        "handler_key": "retention_purge",
        "schedule_kind": "manual",
        "schedule_spec": {},
        "dependencies": [],
        "timeout_seconds": 600,
        "max_attempts": 1,
        "backoff_base_seconds": 60,
        "priority": 9,
        "status": "active",
        "pause_reason": None,
    },
]

# Row counts verified live at the end of Phase 24
# (2026-11-05, migration 20261104_0020). The drift_check
# handler compares the live database against these and
# reports every difference. Auth tables are 0 by decision
# (Phase 24: no live accounts); a nonzero auth count is a
# drift finding to investigate, not an error to auto-fix.
EXPECTED_COUNTS: dict[str, int] = {
    "companies": 470,
    "securities": 470,
    "registry_evidence": 1001,
    "market_prices": 444,
    "financial_documents": 3,
    "financial_statements": 88,
    "financial_statement_line_items": 1316,
    "auditor_opinions": 3,
    "technical_calculation_runs": 1,
    "technical_calculation_errors": 124,
    "technical_indicator_values": 0,
    "fundamental_metric_values": 108,
    "sector_metric_profiles": 120,
    "valuations": 51,
    "economic_indicators": 12,
    "news_events": 7,
    "ownership_holdings": 34,
    "forecast_assessments": 120,
    "risk_metric_values": 81,
    "decisions": 4,
    "simulated_portfolios": 3,
    "backtest_runs": 5,
    "orchestration_runs": 1,
    "rag_chunks": 943,
    "screen_results": 1418,
    "alerts": 89,
    "alert_deliveries": 89,
    "reports": 22,
    "report_figures": 541,
    "data_sources": 19,
    "auth_users": 0,
    "auth_tokens": 0,
    "auth_audit_logs": 0,
}
