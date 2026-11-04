# Phase 25 — Job registry

Seed: `backend/app/services/jobs/registry.py`
(`JOB_DEFINITIONS`, 8 entries). Registered with
`scripts/run_jobs.py register` (idempotent).

## Definitions

| job_key | schedule (PKT) | status | handler | purpose |
|---|---|---|---|---|
| market_post_close | daily Mon–Fri 16:30 | PAUSED | collection stub | Daily post-close market collection |
| filing_check | quarterly (Jan/Apr/Jul/Oct) day 15, 09:00 | PAUSED | collection stub | Quarterly/annual filing availability check |
| macro_release_check | monthly day 3, 09:00 | PAUSED | collection stub | Monthly macro release check (PBS CPI / SBP MPS) |
| system_health | daily 07:00 | active | system_health | Row counts + migration head (read-only) |
| alert_digest | daily 08:00 | active | alert_digest | In-app digest totals (no send anywhere) |
| drift_check | weekly Monday 07:30 | active | drift_check | Stored-state drift vs EXPECTED_COUNTS |
| report_qa_audit | weekly Sunday 08:00 | active, depends on drift_check | report_qa_audit | Report set re-validation + no-publish assertion |
| retention_purge | manual only | active | retention_purge | Auth audit-log retention, 12 months |

## Pause reasons (exact, as stored)

- market_post_close: "Terms evidence pending: no new PSX
  collection without written PSX permission (Phase 5 Terms
  gate, user-owned). The runner refuses paused jobs, so
  this job cannot run."
- filing_check: "Automated issuer-page polling not
  approved; sampled manual checks only. DPS
  filing-download terms are not established (Phase 7
  blocker 2)."
- macro_release_check: "No automated fetch approved;
  Phase 10 macro reads were manual official reads
  (SBP/PBS pages). Automated polling of those pages is
  not authorised."

## Register semantics

- Insert missing definitions with their seed status.
- On re-registration, existing rows keep their OPERATOR
  status (an operator pause is never undone by re-seeding)
  but refresh title, handler, schedule, dependencies,
  timeout, retries, backoff and priority.
- Paused jobs are refused by `run-one` without creating
  a run, and skipped by `run-due` without creating rows
  (counted in the pass summary as skipped, not hidden).

## Run lifecycle

queued → running (atomic claim, lease = timeout) →
succeeded | failed (retryable, exponential backoff:
base × 2^(attempt−1)) → dead (dead-lettered) |
cancelled (queued/blocked only) | blocked (dependency
waiting/failed, re-evaluated every pass).
Terminal for watermark purposes: succeeded, dead,
cancelled. Failed and blocked do NOT advance
`last_processed_occurrence`.

## Retention

- Auth audit logs: 12 months, via the manual-only
  retention_purge job (dry-run default; `--confirm`
  deletes only rows older than 12 months).
- Job tables (`job_definitions`, `job_runs`,
  `job_checkpoints`, `job_dead_letters`) are NEVER
  purged by any job: they are the recovery evidence
  itself. Archival, if ever wanted, is an operator
  decision outside this phase.
