# Phase 25 — Recovery playbooks

## 1. VM replacement / PostgreSQL loss (replacements #4, #5, #6)

System state (apt PostgreSQL, Playwright browsers) does
NOT survive a VM replacement; home persists (repo,
credentials in `~/.config/gh`, venvs, `.env` files,
backups, worktrees). Symptoms: `pg_lsclusters` not found,
`psql` connection refused, uptime of minutes.

1. Confirm home is intact: worktree files, `database/.env`,
   `storage/backups/` present.
2. Reinstall PostgreSQL (apt). Expect apt-lock contention
   with the runtime's own OS-intent replay process right
   after a replacement: wait for it to finish rather than
   killing it — it may restore PostgreSQL itself.
3. Start the cluster: `pg_ctlcluster 16 main start`
   (policy-rc.d denies auto-start).
4. Recreate the contract (`docs/phase-02/DATABASE_SETUP.md`):
   database `psx_intelligence` OWNER postgres; role
   `psx_app` (LOGIN, NOSUPERUSER, NOCREATEDB,
   NOCREATEROLE); role password ONLY in `database/.env`
   (gitignored, mode 0600) — build the SQL from `.env`
   into a chmod-600 file owned by postgres, run it with
   `sudo -u postgres psql -f`, then delete it. Never
   print the password. Clear env for superuser commands:
   `env -u PGUSER -u PGPASSWORD -u PGDATABASE sudo -u
   postgres psql`.
5. Restore backup `2026-11-04T1230-PKT` into the live DB
   (`database/restore.sh` refuses live unless
   `ALLOW_LIVE_RESTORE=1`; it verifies the manifest
   SHA-256 first).
6. Migrate to head from the LATEST branch checkout
   (migration files live per-branch; an older checkout
   cannot resolve newer revisions).
7. Deterministically re-run, in order: registry import →
   444-row price commit → Phase 6 coverage commit →
   Phase 7 extraction commits (run-1 + remainders, from
   the gitignored PDFs and committed page maps) →
   Phase 8–22 `--commit` runs → Phase 25 `register` +
   `run-due` passes until 0 created. Phases 23–24 made
   no business DB writes, so they have no data commits
   to re-run (Phase 24's migration 0020 only adds empty
   auth tables).
8. Resolve ALL company identity BY TICKER, never by
   hardcoded company id: ids are surrogate and shift
   across fresh imports (original HUBC 289 / NML 394 /
   OGDC 403 / HBL 277; post-replacement HUBC 759 / NML
   864 / OGDC 873 / HBL 747). Phase 23 repaired Phase
   8/9/10 configs to ticker keys (a5077e0); check any
   re-run seed's id constants against the live DB first
   and patch temporarily in the worktree only.
9. Re-verify every recorded count (see run_report.md)
   before claiming recovery.

## 2. Interrupted run (process killed mid-handler)

- The run stays `running` with an expired lease.
- Next `run-due` reclaims it: attempt incremented,
  error `reclaimed_after_lease_expiry`, back to queued
  (or dead-lettered if attempts are exhausted).
- Partial checkpoints committed by the handler survive
  (checkpoint() commits immediately); the retried run
  resumes from them instead of redoing finished steps.
- Never touch a run inside a live lease: another
  invoker may own it.

## 3. Dead letter

- A run reaches `dead` only when attempts are exhausted
  or the error is non-retryable (collection stub,
  unknown handler). Its row lands in `job_dead_letters`.
- Operator: inspect the error (`status` / dashboard),
  fix the cause, then `retry-dead <id>`: a fresh queued
  run with a new key (`<key>:retry-N`) is created and
  the letter is marked resolved. The new run is NOT
  executed by retry-dead itself — run it via `run-due`
  or `run-one`.

## 4. Blocked run (dependency failed)

- A dependent stays `blocked` while its same-date
  dependency is not succeeded. It is re-evaluated every
  pass.
- If the dependency died, retry it (dead-letter path
  above). When it succeeds, the dependent unblocks on
  the next pass (or immediately via `run-one`).
- Cancelling a blocked run is terminal: its watermark
  advances, so catch-up moves past it deliberately.

## 5. Stuck-run diagnostics

- `run_jobs.py status` lists stuck runs (running past
  lease), paused definitions with reasons, unresolved
  dead letters, and all watermarks.
- The dashboard (`/admin/jobs`) shows the same status
  read-only.
- A stuck run with a LIVE lease is not stuck: it is
  owned by a concurrent invoker. Wait for its lease to
  expire before reclaiming.

## 6. Catch-up after an offline period

- `run-due` materialises at most 7 unprocessed
  occurrences per job per pass, oldest first. Run it
  repeatedly until a pass reports 0 created.
- The watermark never advances past failed/blocked
  occurrences: fix those first (playbooks 2–4), or
  cancel them explicitly if the operator decides the
  occurrence should be skipped.
- Never backfill by hand-editing watermarks: a false
  watermark hides a gap permanently. Use `run-one
  --date` for explicit single occurrences.
