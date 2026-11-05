# Operations package (Phase 28)

Local/self-hosted production operations for PSX Intelligence AI. No Docker
(user decision 2026-11-04), no paid service, no daemon, no hosted scheduler.

## Stack (production)

| Piece | How it runs | Port |
|---|---|---|
| PostgreSQL 16 | System service (`pg_ctlcluster 16 main start`) | 5432, loopback only |
| Backend | uvicorn from `backend/.venv` | 8000, loopback only |
| Frontend | `next start` (production build) | 3000, loopback only |
| Jobs | Operator-invoked CLI only (`scripts/run_jobs.py run-due`) | — (no port, no daemon) |

The Phase 2 `deployment/` Dockerfiles and `docker-compose.yml` exist in the
repo but are **NOT used**: they predate the Docker ban and are documented
as superseded in `docs/phase-28/deployment_guide.md`. Nothing in `ops/`
invokes Docker (enforced by `test_deployment_phase28.py`). Likewise,
`scripts/dev.sh` (Redis/Celery dev stack) is dev-only; production does not
start Redis or Celery — Phase 25 jobs are DB-backed.

## Scripts

| Script | Purpose |
|---|---|
| `ops/start.sh` | Start postgres (if down) + backend + frontend (production build only). Jobs are NOT started — see the reminder it prints. |
| `ops/stop.sh` | Stop backend + frontend started by `start.sh`. PostgreSQL is deliberately left running (shared system service). |
| `ops/status.sh` | Read-only: health + job status + latest backup. |
| `ops/healthcheck.sh` | Production health: postgres, backend `/health`, frontend `/`, migration match (live revision == checkout head). |
| `ops/update.sh` | Safe update: refuse on dirty tree → backup → `git pull --ff-only` → `alembic upgrade head` → restart → health gate. Never restores over live by itself. |
| `ops/install.sh` | Instantiate systemd units (default: validate into a temp dir only). `--install` writes to `/etc/systemd/system` (root, explicit operator decision). |
| `ops/prune_backups.sh` | Retention pruning: dry-run default; `--confirm` deletes. Keeps newest 30 valid backups, never the newest, never invalid-manifest dirs. |
| `ops/env.production.example` | Production env template (placeholders only). |

## Systemd units (`ops/systemd/`)

`psx-backend.service`, `psx-frontend.service`. Instantiated by
`ops/install.sh` (`@INSTALL_PATH@`, `@SERVICE_USER@`). Validated with
`systemd-analyze verify` before any install. The backend unit reads secrets
from `database/.env` via `EnvironmentFile` — the secret is never in the unit.

## Backups (see `docs/phase-28/backup_retention_policy.md`)

- `database/backup.sh` — pg_dump (-Fc) + file-store tar + manifest with
  full key-table counts (Phase 28 extension) + optional GPG encryption
  (`BACKUP_GPG_RECIPIENT` set; unset = plaintext, the current default).
- `database/restore.sh` — restores into `psx_intelligence_restore_test`
  by default; refuses live unless `ALLOW_LIVE_RESTORE=1`. Decrypts `.gpg`
  backups first when plaintext is absent (private key required).
- `database/verify_restore.sh` — Phase 28 gate: manifest hash check +
  restored-vs-manifest row counts + alembic revision check. Fails loudly
  on any mismatch; never mutates the backup directory (decrypts to temp).

## Uptime limitations (explicit, not hidden)

Everything stops when the computer is off: postgres, backend, frontend.
Nothing runs while off (no daemon, no hosted scheduler), so no jobs, no
alerts, and no collection happen during downtime. On restart: start the
stack (`ops/start.sh`), then catch up with `scripts/run_jobs.py run-due`
(bounded: max 7 occurrences per pass). The session-gap SLO will honestly
show the missing days — that gap is a finding, never hidden. No permanent
public availability is claimed: there is no verified hosting, and the
services bind loopback only.
