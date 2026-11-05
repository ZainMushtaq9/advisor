#!/usr/bin/env bash
# PSX Intelligence AI — production start (Phase 28).
#
# Starts the local/self-hosted production stack WITHOUT Docker (user decision
# 2026-11-04: no Docker anywhere in this project) and WITHOUT any paid service:
#   1. PostgreSQL 16 cluster (system service; started only if it is down)
#   2. Backend  — FastAPI/uvicorn from backend/.venv (127.0.0.1:8000 default)
#   3. Frontend — Next.js production server `next start` (127.0.0.1:3000 default)
#
# Deliberately NOT started here:
#   - No scheduler, no daemon, no Celery worker, no Redis. Phase 25 replaced
#     those with a DB-backed, operator-invoked job framework: the operator
#     runs `scripts/run_jobs.py run-due` (or a host cron runs it). Jobs never
#     run by themselves, and nothing in this script fakes them as running.
#   - No dev server fallback for the frontend: production serves the
#     production build only. If frontend/.next is missing, this script
#     reports it and skips the frontend instead of silently running `next dev`.
#
# Ports: BACKEND_PORT (default 8000), FRONTEND_PORT (default 3000).
# CORS WARNING: the backend's default CORS origins allow only port 3000
# origins. If FRONTEND_PORT is not 3000, set CORS_ORIGINS in the backend
# environment to include the real frontend origin, or API calls from the
# browser will be blocked. Production refuses a wildcard CORS origin.
#
# Secrets: read ONLY from the environment (database/.env when present).
# This script never prints a secret, a password, or a DATABASE_URL.
# Logs + pids: ${PSX_RUN_DIR:-/tmp/psx-prod}/.
# Stop: ops/stop.sh. Status: ops/status.sh. Health: ops/healthcheck.sh.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${PSX_RUN_DIR:-/tmp/psx-prod}"
mkdir -p "$RUN_DIR"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"

say() { printf '[start] %s\n' "$*"; }
answering() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null && return 0 || return 1; }

# Environment (database/.env is gitignored, mode 0600). Sourcing it here only
# sets variables for the child processes; nothing secret is echoed.
if [ -z "${DATABASE_URL:-}" ] && [ -f "$ROOT/database/.env" ]; then
  set -a; # shellcheck disable=SC1091
  source "$ROOT/database/.env"; set +a
fi

# 1. PostgreSQL.
if command -v pg_isready >/dev/null 2>&1 && pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
  say "postgres: RUNNING on 5432"
else
  say "postgres: not answering — attempting pg_ctlcluster ${PG_CLUSTER:-16 main} start"
  if command -v pg_ctlcluster >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    pg_ctlcluster ${PG_CLUSTER:-16 main} start >>"$RUN_DIR/postgres.log" 2>&1 \
      && say "postgres: started" || say "postgres: FAILED to start — see $RUN_DIR/postgres.log (backend will report db: unavailable)"
  else
    say "postgres: pg_ctlcluster absent — start the cluster manually (see docs/phase-28/deployment_guide.md)"
  fi
fi

# 2. Backend.
if answering "$BACKEND_PORT"; then
  say "backend: already answering on $BACKEND_PORT, not restarted"
elif [ -x "$ROOT/backend/.venv/bin/uvicorn" ]; then
  (cd "$ROOT/backend" && "$ROOT/backend/.venv/bin/uvicorn" app.main:app \
    --host "$BACKEND_HOST" --port "$BACKEND_PORT" >"$RUN_DIR/backend.log" 2>&1 & echo $! >"$RUN_DIR/backend.pid")
  say "backend: started (pid $(cat "$RUN_DIR/backend.pid"), log $RUN_DIR/backend.log)"
elif command -v uvicorn >/dev/null 2>&1; then
  (cd "$ROOT/backend" && uvicorn app.main:app \
    --host "$BACKEND_HOST" --port "$BACKEND_PORT" >"$RUN_DIR/backend.log" 2>&1 & echo $! >"$RUN_DIR/backend.pid")
  say "backend: started with system uvicorn (pid $(cat "$RUN_DIR/backend.pid"))"
else
  say "backend: SKIPPED — no backend/.venv uvicorn and no system uvicorn found"
fi

# 3. Frontend (production build only).
if answering "$FRONTEND_PORT"; then
  say "frontend: already answering on $FRONTEND_PORT, not restarted"
elif [ -d "$ROOT/frontend/.next" ] && [ -x "$ROOT/frontend/node_modules/.bin/next" ]; then
  (cd "$ROOT/frontend" && "$ROOT/frontend/node_modules/.bin/next" start \
    --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT" >"$RUN_DIR/frontend.log" 2>&1 & echo $! >"$RUN_DIR/frontend.pid")
  say "frontend: started (pid $(cat "$RUN_DIR/frontend.pid"), log $RUN_DIR/frontend.log)"
elif [ -d "$ROOT/frontend/.next" ]; then
  say "frontend: SKIPPED — .next build exists but node_modules/.bin/next is missing (run npm install in frontend/ first)"
else
  say "frontend: SKIPPED — no production build (frontend/.next missing). Build first: cd frontend && npm run build"
fi

# Readiness wait (up to 30 s): a fixed sleep is too short for uvicorn/next.
for _ in $(seq 1 15); do
  b=0; f=0
  curl -fsS --max-time 3 "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1 && b=1
  curl -fsS --max-time 3 "http://127.0.0.1:$FRONTEND_PORT/" >/dev/null 2>&1 && f=1
  [ "$b" -eq 1 ] && [ "$f" -eq 1 ] && break
  sleep 2
done
say "--- health summary ---"
"$ROOT/ops/healthcheck.sh" || true
say "jobs: NOT auto-started by design — run: cd $ROOT && scripts/run_jobs.py run-due"
say "logs: $RUN_DIR/*.log   stop: ops/stop.sh"
