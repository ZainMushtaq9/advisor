#!/usr/bin/env bash
# PSX Intelligence AI — local stack WITHOUT Docker (Phase 2, Team E).
# Verified path on 2026-11-04: Docker Hub pulls are blocked on this VM, so
# this script, not Compose, is how the stack actually runs here.
# See docs/phase-02/LOCAL_DEVELOPMENT_GUIDE.md for the full procedure.
#
# Start order (defined sequence):
#   1. PostgreSQL — only if already running (Team D owns it); never
#      installed or started blindly by this script.
#   2. Redis — started if redis-server exists and nothing answers on 6379.
#   3. Backend — FastAPI/uvicorn from backend/.venv if present, else
#      system python -m uvicorn. DATABASE_URL unset => backend reports
#      db: unavailable (truthful, per Team C) and still serves /health.
#   4. Frontend — `npm run dev` from frontend/ if node_modules exists.
#   5. Worker — Celery worker from workers/.venv (created here if missing),
#      only if Redis answers; otherwise the dev fallback is reported and
#      the worker step is SKIPPED (never faked as running).
#
# Services run in the background; logs + pids go to /tmp/psx-dev/.
# Stop everything this script started:  scripts/stop_dev.sh
# Check everything:                     scripts/healthcheck.sh
# This script starts NO scheduler, NO agent loop, and spends NO money.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGDIR=/tmp/psx-dev
mkdir -p "$LOGDIR"

say() { printf '%s\n' "[dev] $*"; }
running_on() { # $1=port ; true if something answers on loopback
  (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null && return 0 || return 1
}

start_bg() { # $1=name $2=logfile $@=command...
  local name="$1" log="$2"; shift 2
  "$@" >"$log" 2>&1 &
  echo $! >"$LOGDIR/$name.pid"
  say "$name started (pid $(cat "$LOGDIR/$name.pid"), log $log)"
}

# 1. PostgreSQL (report only — Team D owns the cluster).
if command -v pg_isready >/dev/null 2>&1 && pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
  say "postgres: RUNNING on 5432 (owned by database team, left untouched)"
else
  say "postgres: NOT RUNNING / pg_isready absent — backend will report db: unavailable; this is expected without Team D's cluster"
fi

# 2. Redis.
if running_on 6379; then
  say "redis: already answering on 6379, not restarted"
elif command -v redis-server >/dev/null 2>&1; then
  redis-server --daemonize yes --port 6379 --save '' --appendonly no \
    --protected-mode yes --bind 127.0.0.1 >>"$LOGDIR/redis.log" 2>&1
  touch "$LOGDIR/redis.started-by-dev"
  sleep 1
  if running_on 6379; then say "redis: started on 6379"; else say "redis: FAILED to start — see $LOGDIR/redis.log"; fi
else
  say "redis: redis-server not installed — install it (docs/phase-02/REDIS_SETUP.md) or use the dev fallback"
fi
REDIS_UP=0; running_on 6379 && REDIS_UP=1
WORKER_STARTED=0

# 3. Backend (uvicorn, port 8000).
if running_on 8000; then
  say "backend: already answering on 8000, not restarted"
elif [ -x "$ROOT/backend/.venv/bin/uvicorn" ]; then
  (cd "$ROOT/backend" && start_bg backend "$LOGDIR/backend.log" "$ROOT/backend/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000)
elif command -v uvicorn >/dev/null 2>&1; then
  (cd "$ROOT/backend" && start_bg backend "$LOGDIR/backend.log" uvicorn app.main:app --host 127.0.0.1 --port 8000)
else
  say "backend: SKIPPED — no backend/.venv uvicorn and no system uvicorn found"
fi

# 4. Frontend (Next.js dev, port 3000).
if running_on 3000; then
  say "frontend: already answering on 3000, not restarted"
elif [ -d "$ROOT/frontend/node_modules" ]; then
  (cd "$ROOT/frontend" && start_bg frontend "$LOGDIR/frontend.log" npm run dev -- --port 3000)
else
  say "frontend: SKIPPED — frontend/node_modules missing (run npm install in frontend/ first)"
fi

# 5. Worker (Celery, only with Redis; else report the fallback).
if [ "$REDIS_UP" -eq 1 ]; then
  if [ ! -x "$ROOT/workers/.venv/bin/celery" ]; then
    say "worker: creating workers/.venv and installing workers/requirements.txt (one-time)"
    python3 -m venv "$ROOT/workers/.venv" && "$ROOT/workers/.venv/bin/pip" install -q -r "$ROOT/workers/requirements.txt"
  fi
  if [ -x "$ROOT/workers/.venv/bin/celery" ]; then
    if pgrep -f "celery -A workers.celery_app" >/dev/null 2>&1; then
      say "worker: already running, not restarted"
      WORKER_STARTED=1
    else
      (cd "$ROOT" && start_bg worker "$LOGDIR/worker.log" "$ROOT/workers/.venv/bin/celery" -A workers.celery_app worker --loglevel=info)
      WORKER_STARTED=1
    fi
  else
    say "worker: SKIPPED — celery install failed; dev fallback: python -m workers.dev_fallback run"
  fi
else
  say "worker: SKIPPED — no Redis. Dev-only fallback instead: python -m workers.dev_fallback enqueue add 2 3 && python -m workers.dev_fallback run"
fi

# Readiness wait: a fixed sleep is too short — the worker needs seconds
# to reach worker_ready (heartbeat) and Next.js dev needs seconds to
# compile its first page. Poll for up to 90 s instead of declaring the
# stack down after 2 s (that race produced false FAILED/NOT RUNNING
# lines on the first dev.sh run, 2026-11-04). A service whose pid died
# or that is still down after the wait is reported truthfully below.
for _ in $(seq 1 18); do
  backend_ok=0; frontend_ok=0; worker_ok=0
  curl -fsS --max-time 3 http://127.0.0.1:8000/health >/dev/null 2>&1 && backend_ok=1
  curl -fsS --max-time 3 http://127.0.0.1:3000/ >/dev/null 2>&1 && frontend_ok=1
  (cd "$ROOT" && "$ROOT/workers/.venv/bin/python" workers/healthcheck.py >/dev/null 2>&1) && worker_ok=1
  if [ "$backend_ok" -eq 1 ] && [ "$frontend_ok" -eq 1 ] && { [ "$worker_ok" -eq 1 ] || [ "$WORKER_STARTED" -eq 0 ]; }; then
    say "all expected services ready"
    break
  fi
  sleep 5
done
say "--- health summary ---"
"$ROOT/scripts/healthcheck.sh" || true
say "logs: $LOGDIR/*.log   stop: scripts/stop_dev.sh"
