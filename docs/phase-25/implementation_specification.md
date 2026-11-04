# Phase 25 — Implementation specification

Automation, scheduling, workflow recovery and job control.
Brief: playbook lines 1801–1857.

## Design decisions (and why)

1. **No resident daemon, no hosted workflow service, no paid
   scheduler.** The runner is a single-pass CLI (`run-due`):
   reclaim stale leases, materialise due occurrences, execute
   queued runs sequentially, exit. The operator (or a host
   cron) invokes it. The system never pretends something is
   watching the clock between runs — that is the honest
   offline model for a VM that is replaced without warning
   (replacements #4, #5, #6 all hit this project).
2. **No Celery/Redis for jobs.** Phase 2 proved Celery +
   Redis alive, but a broker + worker pair is exactly the
   always-on machinery a VM replacement kills, and it adds a
   second failure domain for zero benefit at this scale
   (tens of runs, not thousands). The database itself is
   the queue: it survives replacement via backup + restore,
   and claiming is one atomic UPDATE.
3. **Database-backed claiming with leases.** A run moves
   queued → running only via `UPDATE ... WHERE status =
   'queued'`; a second invoker gets rowcount 0 and skips
   it. Every claim carries owner + expiry (the job's
   timeout). A run past its lease is presumed crashed and
   reclaimed (attempt incremented) or dead-lettered when
   attempts are exhausted. A run inside a live lease is
   never touched.
4. **Sequential execution, one invocation at a time.** No
   two handlers run concurrently in one pass, so one run
   cannot exhaust resources for another. Throughput is
   irrelevant at this scale; determinism is everything.
5. **Idempotency keys are occurrence keys**
   (`job_key:YYYY-MM-DD`). Re-executing a succeeded run
   replays its stored summary without calling the handler.
   Manual runs are idempotent only with an operator-supplied
   `--run-tag`; without one each invocation is a distinct
   run (timestamp key). This is stated, not hidden.
6. **Checkpoints commit immediately.** `checkpoint()` calls
   `session.commit()` at once, so partial progress survives
   a crash even when the run then fails. A retried run
   resumes from its watermark instead of redoing finished
   steps (proven by the step-handler test). Checkpoint keys
   for multi-step handlers MUST be occurrence-scoped
   (`step:<date>`), not job-scoped, or state leaks across
   occurrences of the same job.
7. **Dependencies block, never fail, the dependent.**
   A dependent whose dependency is not yet succeeded waits
   (status `blocked`, re-evaluated every pass). A dependent
   whose dependency died stays blocked until an operator
   retries the dependency (retry-dead) — the watermark
   never advances past an unresolved occurrence, so
   catch-up never silently skips a missing upstream result.
8. **Bounded catch-up.** At most 7 unprocessed occurrences
   per job per pass, oldest first. A brand-new job looks
   back 30 days, not to epoch. The backlog drains over
   successive passes; the operator can always run one
   occurrence explicitly with `run-one --date`.
9. **Paused is enforcement, not a label.** The runner
   refuses paused jobs without creating a run. The three
   collection jobs are paused (Terms-gated / polling-not-
   approved) and their handlers are explicit stubs that
   dead-letter immediately if ever dispatched — so even a
   mistaken activation cannot silently collect or retry
   forever.
10. **PKT dates everywhere.** Schedules, occurrences and
    the digest watermark are Asia/Karachi dates. Pakistan
    has no DST (none since 2009), so wall-clock dates are
    unambiguous. The digest watermark was fixed mid-run
    from UTC to PKT: a 01:00 PKT digest under UTC dating
    mislabelled same-day alerts (see run_report.md).
11. **No verified PSX holiday calendar exists.** Trading
    weekdays are Monday–Friday only; no date is ever
    claimed to be a holiday. A weekday with no stored price
    rows is an observed gap, not a silent skip.

## Components

- `backend/app/models/jobs.py` — 4 tables (portable
  Integer PKs, Phase 24 SQLite lesson): `job_definitions`,
  `job_runs`, `job_checkpoints`, `job_dead_letters`.
- `database/migrations/versions/20261104_0021_phase_25_jobs.py`
  — 0020 → 0021.
- `backend/app/services/jobs/calendar.py` — pure schedule
  evaluator (daily/weekly/monthly/quarterly/annual/manual),
  nonexistent days skipped never moved, catch-up cap,
  idempotency keys.
- `backend/app/services/jobs/registry.py` — 8 seed
  definitions + EXPECTED_COUNTS drift baseline (verified
  end of Phase 24).
- `backend/app/services/jobs/handlers.py` — read-only
  handlers (health, digest, drift, QA audit) + manual
  retention purge (dry-run default, `--confirm` deletes
  only auth audit logs older than 12 months; job tables
  are never purged) + collection stubs (non-retryable).
- `backend/app/services/jobs/runner.py` — register,
  compute/materialise due, claim, reclaim, dependencies,
  execute, run-due, run-one, cancel, retry-dead, status.
- `backend/app/api/v1/endpoints/jobs.py` — GET-only:
  definitions, runs, run detail, checkpoints,
  dead-letters, status.
- `scripts/run_jobs.py` — CLI (register/list/due/run-due/
  run-one/cancel/retry-dead/status/purge). JSON on stdout,
  summary on stderr, exit 0/1/2 like the other CLIs.
- `frontend/app/admin/jobs/page.tsx` — operations
  dashboard (read-only; actions exist only in the CLI).
  Nav entry `Jobs` + Admin page row.
- `frontend/e2e/phase25/jobs.spec.ts` +
  `playwright.phase25.config.ts` — separate suite, same
  pattern as Phase 23 (own config, own spec dir).

## What Phase 25 deliberately does NOT do

- No broker, worker, daemon, or hosted scheduler.
- No polling loop of any kind (the runner runs once and
  exits; a host cron decides when to invoke it).
- No new market-data collection (all collection jobs
  paused; handlers are stubs).
- No execution/order/publication/send/promotion path
  (the no-execution scan test enforces this on new code).
- No live auth accounts (Phase 24 decision stands: auth
  tables stay empty until a parent/user decision).
- No frontend token support for enforced mode, no backup
  encryption, no dependency audit, no multi-instance rate
  limiting (Phase 24 gaps, still open — see run_report.md).
- No token-gating of the Phase 22 report approval CLI
  and no audit-retention purge job schedule: the purge
  exists as a manual-only job (Phase 24 candidate (b)
  adopted in manual form); token-gated approval (candidate
  (a)) does not belong to the scheduling brief and stays
  open for a later phase.
