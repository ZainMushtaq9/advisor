#!/usr/bin/env bash
# Run the Celery worker in the foreground (Phase 2, Team E).
# Requires Redis on 127.0.0.1:6379. Creates workers/.venv on first use.
#   scripts/run_worker.sh
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -x "$ROOT/workers/.venv/bin/celery" ]; then
  echo "[worker] creating workers/.venv ..."
  python3 -m venv "$ROOT/workers/.venv"
  "$ROOT/workers/.venv/bin/pip" install -q -r "$ROOT/workers/requirements.txt"
fi
if ! redis-cli ping 2>/dev/null | grep -q PONG; then
  echo "[worker] ERROR: Redis is not answering on 6379. Start it first (scripts/dev.sh) or use the dev fallback." >&2
  exit 1
fi
cd "$ROOT"
exec "$ROOT/workers/.venv/bin/celery" -A workers.celery_app worker --loglevel=info
