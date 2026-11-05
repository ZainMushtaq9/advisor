#!/usr/bin/env bash
# PSX Intelligence AI — production status (Phase 28).
# Read-only report: process health (ops/healthcheck.sh), job status
# (Phase 25 CLI, read-only), and latest backup. Writes nothing, sends
# nothing, promotes nothing. Needs DATABASE_URL (database/.env) for the
# job and backup sections; those sections report "unknown" without it.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/ops/healthcheck.sh" || true
echo "--- jobs (operator-invoked, Phase 25) ---"
if [ -f "$ROOT/database/.env" ]; then
  (set -a; source "$ROOT/database/.env" 2>/dev/null; set +a
   cd "$ROOT" && backend/.venv/bin/python scripts/run_jobs.py status 2>&1 | head -20) \
   || echo "jobs: status command failed (see above)"
else
  echo "jobs: unknown (database/.env missing)"
fi
echo "--- latest backup ---"
LATEST="$(ls -dt "$ROOT/storage/backups"/202*-PKT 2>/dev/null | head -1)"
if [ -n "$LATEST" ]; then
  echo "latest: $LATEST"
  python3 -c "import json,sys; m=json.load(open(sys.argv[1])); print('timestamp:', m.get('backup_timestamp_pkt'), '| alembic:', m.get('alembic_revision'), '| encryption:', (m.get('encryption') or {}).get('enabled', False))" "$LATEST/manifest.json" 2>/dev/null \
    || echo "manifest: unreadable (operator review needed)"
else
  echo "latest: NONE — no backup exists yet; take one before any schema change (database/backup.sh)"
fi
