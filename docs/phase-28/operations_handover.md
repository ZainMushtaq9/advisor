# Phase 28 — Operations Handover

## Start / stop / status

```bash
ops/start.sh        # postgres (if down) + backend + frontend, then health summary
ops/stop.sh         # backend + frontend only; postgres deliberately left running
ops/status.sh       # read-only: health + job status + latest backup
ops/healthcheck.sh  # postgres, backend /health, frontend /, migration match
```

PostgreSQL is a shared system service: start it with
`pg_ctlcluster 16 main start`, stop it with `pg_ctlcluster 16 main stop`
(never via `ops/stop.sh` — stopping the cluster by accident would take
down every database on the host, not just this project).

## Update

```bash
ops/update.sh
```

Order (stops at the first failure): refuse on a dirty git tree → take a
verified backup → `git pull --ff-only` → `alembic upgrade head` →
restart → health gate. Rollback is the backup taken in step 1:
prove it in `psx_intelligence_restore_test` first
(`database/restore.sh <backup-dir>` + `database/verify_restore.sh
<backup-dir>`), and only then — with `ALLOW_LIVE_RESTORE=1` and explicit
operator confirmation — restore over live. `update.sh` never restores
over live by itself.

## Migrate (manual form)

```bash
cd database && .venv/bin/alembic upgrade head && cd ..
```

Always run from the deployment checkout (migration files live
per-branch; an older checkout lacks newer revisions and will report
"can't locate revision" for the live revision — that is a checkout
problem, not a database problem). A backup MUST exist and verify BEFORE
any migration touching existing tables (Phase 1 retention rule).

## Backup / restore

```bash
set -a; source database/.env; set +a
bash database/backup.sh                       # plaintext (default)
BACKUP_GPG_RECIPIENT=<key> bash database/backup.sh   # encrypted (opt-in)
bash database/restore.sh <backup-dir>         # into psx_intelligence_restore_test
bash database/verify_restore.sh <backup-dir>  # full gate: hashes + counts + revision
bash database/verify_restore.sh <backup-dir> psx_intelligence_restore_test
```

Full policy, retention, encryption-key steps, and RPO/RTO:
`backup_retention_policy.md`. Drill evidence: `restore_drill.md`.

## Jobs and catch-up

Jobs are operator-invoked, never automatic (Phase 25):

```bash
set -a; source database/.env; set +a
python scripts/run_jobs.py status    # read-only
python scripts/run_jobs.py run-due   # one pass, bounded (max 7 occurrences), then exits
```

The 3 collection jobs (`market_post_close`, `filing_check`,
`macro_release_check`) are PAUSED (Terms gate / DPS terms / no automated
fetch approved) and the runner refuses paused jobs — never unpause one
without the evidence that unblocks it (written PSX permission, DPS
filing-download terms, or an approved fetch, respectively).

## What stops when the computer is off — and how catch-up works

Everything stops: PostgreSQL, backend, frontend. Nothing runs while off:
no jobs, no alerts, no collection, no monitoring. No data is lost by
stopping — the database and file store persist on disk — but time-based
things do NOT catch up by themselves:

1. Start the stack: `ops/start.sh`.
2. Check health: `ops/healthcheck.sh` (migration match included).
3. Catch up jobs: `scripts/run_jobs.py run-due` (bounded: max 7
   occurrences per pass, 30-day lookback for new jobs; run it again if
   more occurrences are due).
4. Expect honest gap signals, and do NOT hide them: the session-gap SLO
   will show the missing trading days, market_prices source health will
   read stale, and drift vs the Phase 24 baseline will appear if
   documents/statements changed. A difference is a finding to explain
   (Phase 25/26/27 rule), never auto-fixed, never reworded away.
5. If the machine was replaced (not just restarted), follow the
   twice-proven VM-replacement recovery recipe in
   `docs/phase-27/incident_playbooks.md` (restore backup → migrate →
   deterministic phase re-runs in order, resolving identity by ticker).

## Incident

- Severity, escalation, rollback, and recovery playbooks:
  `docs/phase-27/incident_playbooks.md` (including the VM-replacement
  recipe and the Phase 26 push-disconnect runbook).
- Open exceptions live in the Phase 27 exception queue
  (`observability_exceptions`, 6 open at last run); incidents are
  recorded in `observability_incidents` (3 resolved at last run).
- Logs: structured JSON, one object per record, correlation IDs on
  every request (Phase 27); secrets are redacted by substring and
  database URLs redacted in full. No log text is stored in the DB.

## Upgrade

Application upgrade = `ops/update.sh` (above). Dependency upgrade =
change the pin, re-run the licence gate
(`test_deployment_phase28.py` fails on unreviewed dependencies until
the licence is checked and the allowlist updated), full backend suite,
frontend vitest + build, then the update procedure. Never upgrade
PostgreSQL, Node, or Python without a verified backup first and a
restore drill after.

## Shutdown (planned)

1. `ops/stop.sh` (backend + frontend).
2. Optional: `scripts/run_jobs.py run-due` BEFORE stopping, so no
   occurrence is left half-processed (jobs are single-pass; a stopped
   machine simply leaves occurrences due, which the next `run-due`
   picks up — nothing is half-written, because lease claims are atomic).
3. Take a backup if the state changed since the last one.
4. `pg_ctlcluster 16 main stop` only if the whole cluster is meant to stop.

## Shutdown (unplanned / crash)

On restart, the database recovers by itself (PostgreSQL crash recovery);
the file store needs no repair step. Then follow "What stops when the
computer is off" above. If the disk itself is gone, recovery is the
latest backup (restore drill proves the path) — which is why backups
must live somewhere other than only the machine they back up (see the
retention policy's off-machine note).
