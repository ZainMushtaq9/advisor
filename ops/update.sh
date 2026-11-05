#!/usr/bin/env bash
# PSX Intelligence AI — production update (Phase 28).
# Safe order, and it stops at the first failure instead of pushing on:
#   1. Refuse if the git tree is dirty (never overwrite operator changes).
#   2. Take a verified backup FIRST (database/backup.sh; aborts on failure).
#   3. git pull --ff-only (fast-forward only — never a merge, never a rebase).
#   4. alembic upgrade head (from database/, with the branch's migrations).
#   5. Restart backend + frontend (ops/stop.sh + ops/start.sh).
#   6. Health gate (ops/healthcheck.sh must exit 0).
# Rollback is the backup taken in step 2: database/restore.sh into a test
# database first to prove it, then — only with ALLOW_LIVE_RESTORE=1 and
# operator confirmation — over live. This script never restores over live
# by itself. Usage: ops/update.sh  (run from the deployment checkout).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -n "$(git status --porcelain)" ]; then
  echo "update: REFUSED — git tree is dirty. Commit or stash operator changes first." >&2
  exit 2
fi
echo "update: step 1/6 — backup first"
if [ -z "${DATABASE_URL:-}" ] && [ -f "$ROOT/database/.env" ]; then
  set -a; # shellcheck disable=SC1091
  source "$ROOT/database/.env"; set +a
fi
bash "$ROOT/database/backup.sh" || { echo "update: ABORTED — backup failed, nothing changed." >&2; exit 2; }
echo "update: step 2/6 — git pull --ff-only"
git pull --ff-only || { echo "update: ABORTED — pull failed (not fast-forward?). Backup from step 1 is intact." >&2; exit 2; }
echo "update: step 3/6 — alembic upgrade head"
(cd "$ROOT/database" && .venv/bin/alembic upgrade head) || { echo "update: ABORTED — migration failed. Restore from the step-1 backup if needed." >&2; exit 2; }
echo "update: step 4/6 — restart services"
bash "$ROOT/ops/stop.sh" || true
bash "$ROOT/ops/start.sh" || { echo "update: WARNING — start reported problems; check ops/healthcheck.sh." >&2; }
echo "update: step 5/6 — health gate"
bash "$ROOT/ops/healthcheck.sh" || { echo "update: FAILED health gate — investigate before serving traffic." >&2; exit 1; }
echo "update: DONE — backup, pull, migrate, restart, health gate all passed."
