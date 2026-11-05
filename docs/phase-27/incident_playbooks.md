# Phase 27 — Incident, Severity, Escalation, Rollback, Recovery Playbooks

## Severity scale

| Severity | Meaning | Examples in this project |
|---|---|---|
| sev1 | Data loss or a wrong value presented as fact | A stored price overwritten; a VERIFIED promotion without evidence |
| sev2 | A phase's output silently wrong | A seed that writes rows for the wrong company (surrogate-id trap) |
| sev3 | Service unavailable until recovered, no data loss | VM replacement (PostgreSQL gone); database down |
| sev4 | Transient failure, retry succeeds | Push network disconnect; a single failed job attempt |

No sev1 or sev2 has occurred. The recorded incidents are two
sev3 (VM replacements #5 and #6) and one sev4 (Phase 26 push
disconnect), all resolved with evidence in
`observability_incidents`.

## Escalation

1. The operator (this project's single maintainer) sees the
   failure in the observability dashboard or the CLI output.
2. If the failure is a data-integrity question (wrong value,
   wrong company, unexpected status change), STOP all runs and
   preserve the database as-is for audit. Do not re-run a seed
   over suspect rows.
3. If the failure is availability (database down, VM replaced),
   follow the recovery procedure below.
4. If the failure needs a user decision (written PSX permission,
   a live auth account, a merge to main, a deployment), it is
   reported to the user with its exact unblocker. No standing
   authorization covers those decisions.

## Rollback

- Code rollback: every phase works on its own branch from a
  verified tip; base tips are never moved and main is never
  merged without separate approval. Rolling back a phase means
  abandoning its branch, never rewriting history. No
  force-push, no history rewrite, ever.
- Data rollback: restore backup `2026-11-04T1230-PKT` (manifest
  SHA-256 verified) via `database/restore.sh` into the restore
  target first, verify, then re-run the deterministic phase
  commits in order (see recovery procedure). A rollback never
  edits stored business rows in place.
- Migration rollback: the Phase 27 migration has a downgrade
  (drops the 7 observability tables, reverse order). Business
  tables are untouched by it.

## Recovery procedure (proven twice: VM replacements #5 and #6)

1. Restart the cluster: `pg_ctlcluster 16 main start`
   (policy-rc.d denies auto-start).
2. Restore backup `2026-11-04T1230-PKT` into the live DB per
   `docs/phase-02/DATABASE_SETUP.md`; verify the manifest
   SHA-256 first.
3. Check out the LATEST branch first (migration files live
   per-branch), then migrate to the current head
   (`20261104_0023` after Phase 27).
4. Deterministically re-run, in order: registry import, the
   444-row price commit (with `--source-key
   dps_market_summary_2026-11-03` — a bare run rejects the 444
   as missing_field), Phase 6 coverage, Phase 7 extraction
   (run-1 + remainders, from the gitignored PDFs and committed
   page maps), then the Phase 8–22 `--commit` runners in order.
   Phases 23–24 made no business writes (24's migration only
   adds empty auth tables); Phase 25's job tables and Phase
   26's evaluation tables are recreated by their own runners.
5. Resolve ALL company identity by ticker, never by hardcoded
   company id (surrogate ids shift across fresh imports:
   original HUBC 289 / NML 394 / OGDC 403 / HBL 277; current
   HUBC 759 / NML 864 / OGDC 873 / HBL 747).
6. Known surrogate-id traps to check before trusting a re-run:
   macro sector ids (16/8/36/4 → 53/45/73/41 — needs permanent
   name-based resolution) and news publication-date keys (old
   document ids 13/14/15 vs live 7/8/9 — needs permanent
   ticker-based mapping). Both are open follow-ups, not fixed
   by temporary patches.
7. Do NOT re-fabricate superseded history: RAG benchmark
   results are 6 (r3 only) after replacement #6; r1/r2 rows
   were runs of superseded code and are not reproduced.
8. Verify health after recovery: business counts vs the
   Phase 24 baseline (drift SLO must be 0 differences, or each
   difference explained), HUBC close 197.2400, and the
   observability readiness endpoint `ready: true` — then
   preserve partial results safely: a failed run rolls back
   whole, never half-stored (every phase runner commits once
   or not at all).

## Failure-mode playbooks

- Process crash (uvicorn/CLI dies mid-run): the run is not
  stored (commit-once discipline); re-run the same run_id —
  idempotency makes the second attempt safe.
- Network outage (push disconnect): retry; verify with
  `git ls-remote` that remote SHA equals local tip before
  reporting success. Never report a push from the local tip
  alone.
- Source format change (a new DPS/issuer file layout): the
  ingest validator rejects unknown shapes (fail-fast) instead
  of storing them; the rejection is a finding, and the phase
  runner's dry-run shows it before any write.
- Corrupted download (garbage bytes): the market validator
  rejects unparseable rows with a reason code (tested); the
  file is quarantined, never stored. The HBL issuer-site
  challenge is a download block, not corruption: the
  live-browser route (normal visitor, no bypass) is the
  prescribed path, and it succeeded on 2026-11-05.
- Database disconnect: `check_database` reports
  `unavailable` with its reason; the readiness endpoint
  reports `ready: false` instead of crashing; `/health`
  stays 200 (liveness is not database health).
- Disk pressure: no probe writes large data; the largest
  growth events are bounded (one report load, one price date).
  If disk fills, stop all runners, free space from
  `frontend/test-results/` and other build artifacts first
  (never from `storage/` originals or backups), then re-run
  from the last verified backup.
