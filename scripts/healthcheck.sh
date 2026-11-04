#!/usr/bin/env bash
# PSX Intelligence AI — per-service health report (Phase 2, Team E).
# Prints one line per service: OK | NOT RUNNING | SKIPPED (with reason) |
# FAILED (a running service answering unhealthily).
# Exit code: 0 if no service is FAILED; 1 if any service is FAILED.
# SKIPPED/NOT RUNNING never fail the script — they are truthful reports
# that a service is absent, not claims that it is healthy.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILED=0

line() { printf '%-10s %s\n' "$1" "$2"; }

# PostgreSQL.
if command -v pg_isready >/dev/null 2>&1; then
  if pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then line postgres "OK (pg_isready, 5432)"
  else line postgres "NOT RUNNING (5432, database team cluster not up)"; fi
else
  line postgres "SKIPPED (pg_isready not installed)"
fi

# Redis.
if command -v redis-cli >/dev/null 2>&1; then
  if [ "$(redis-cli ping 2>/dev/null)" = "PONG" ]; then line redis "OK (PONG, $(redis-cli info server 2>/dev/null | grep '^redis_version:' | cut -d: -f2 | tr -d '\r'))"
  else line redis "NOT RUNNING (no PONG on 6379)"; fi
else
  line redis "SKIPPED (redis-cli not installed)"
fi

# Backend: /health (unversioned alias) and /api/v1/health.
if curl -fsS --max-time 5 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  line backend "OK (http://127.0.0.1:8000/health)"
elif (exec 3<>"/dev/tcp/127.0.0.1/8000") 2>/dev/null; then
  line backend "FAILED (port 8000 open but /health did not answer)"; FAILED=1
else
  line backend "NOT RUNNING (nothing on 8000)"
fi

# Frontend.
if curl -fsS --max-time 5 http://127.0.0.1:3000/ >/dev/null 2>&1; then
  line frontend "OK (http://127.0.0.1:3000/)"
elif (exec 3<>"/dev/tcp/127.0.0.1/3000") 2>/dev/null; then
  line frontend "FAILED (port 3000 open but / did not answer)"; FAILED=1
else
  line frontend "NOT RUNNING (nothing on 3000)"
fi

# Worker: Redis heartbeat + Celery inspect, via workers/healthcheck.py.
if [ -x "$ROOT/workers/.venv/bin/python" ]; then
  WPY="$ROOT/workers/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  WPY="python3"
else
  WPY=""
fi
if [ -n "$WPY" ]; then
  if (cd "$ROOT" && "$WPY" workers/healthcheck.py >/tmp/psx-dev/worker-health.txt 2>&1); then
    line worker "OK ($(grep '^worker_inspect:' /tmp/psx-dev/worker-health.txt | head -1))"
  else
    code=$?
    if [ "$code" -eq 2 ]; then line worker "NOT RUNNING (Redis unreachable — see /tmp/psx-dev/worker-health.txt)"
    elif [ "$code" -eq 3 ]; then line worker "NOT RUNNING (Redis OK, no fresh worker heartbeat)"
    else line worker "FAILED (healthcheck error — see /tmp/psx-dev/worker-health.txt)"; FAILED=1; fi
  fi
else
  line worker "SKIPPED (no python found)"
fi

exit "$FAILED"
