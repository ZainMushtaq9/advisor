#!/usr/bin/env bash
# PSX Intelligence AI — production health report (Phase 28).
# Checks the production stack ONLY: PostgreSQL, backend, frontend, and the
# migration match (live alembic revision == branch head). Redis/Celery are
# deliberately NOT checked: they are Phase 2 proofs, not part of production
# (Phase 25 jobs are DB-backed and operator-invoked).
# One line per check: OK | NOT RUNNING | FAILED. Exit 0 only if nothing is
# FAILED; NOT RUNNING is a truthful report, not a failure of this script.
# Usage: ops/healthcheck.sh [backend-port] [frontend-port]
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${1:-${BACKEND_PORT:-8000}}"
FRONTEND_PORT="${2:-${FRONTEND_PORT:-3000}}"
FAILED=0
line() { printf '%-12s %s\n' "$1" "$2"; }

if command -v pg_isready >/dev/null 2>&1; then
  if pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then line postgres "OK (pg_isready, 5432)"
  else line postgres "NOT RUNNING (5432)"; fi
else
  line postgres "SKIPPED (pg_isready not installed)"
fi

if curl -fsS --max-time 5 "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
  line backend "OK (http://127.0.0.1:$BACKEND_PORT/health)"
elif (exec 3<>"/dev/tcp/127.0.0.1/$BACKEND_PORT") 2>/dev/null; then
  line backend "FAILED (port $BACKEND_PORT open but /health did not answer)"; FAILED=1
else
  line backend "NOT RUNNING (nothing on $BACKEND_PORT)"
fi

if curl -fsS --max-time 5 "http://127.0.0.1:$FRONTEND_PORT/" >/dev/null 2>&1; then
  line frontend "OK (http://127.0.0.1:$FRONTEND_PORT/)"
elif (exec 3<>"/dev/tcp/127.0.0.1/$FRONTEND_PORT") 2>/dev/null; then
  line frontend "FAILED (port $FRONTEND_PORT open but / did not answer)"; FAILED=1
else
  line frontend "NOT RUNNING (nothing on $FRONTEND_PORT)"
fi

# Migration match: live revision vs this checkout's head. Needs DATABASE_URL
# (database/.env) and the branch's migration files — run from this checkout.
if [ -f "$ROOT/database/.env" ]; then
  MIG_OUT="$(cd "$ROOT/database" && (set -a; source "$ROOT/database/.env" 2>/dev/null; set +a; .venv/bin/alembic current 2>/dev/null || echo 'ERROR'))"
  # `alembic heads` prints "20261104_0023 (head)": strip to the bare revision,
  # or every comparison false-fails (caught live 2026-11-05, fixed here).
  HEAD_REV="$(cd "$ROOT/database" && .venv/bin/alembic heads 2>/dev/null | head -1 | awk '{print $1}')"
  LIVE_REV="$(printf '%s' "$MIG_OUT" | grep -oE '20261104_[0-9]+' | head -1)"
  if [ -n "$LIVE_REV" ] && [ "$LIVE_REV" = "$HEAD_REV" ]; then
    line migrations "OK (live $LIVE_REV == head)"
  elif [ -n "$LIVE_REV" ]; then
    line migrations "FAILED (live $LIVE_REV != head $HEAD_REV — run ops/update.sh)"; FAILED=1
  else
    line migrations "NOT RUNNING (could not read live revision — is the database up?)"
  fi
else
  line migrations "SKIPPED (database/.env missing — no live database configured)"
fi

exit "$FAILED"
