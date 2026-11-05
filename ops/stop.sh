#!/usr/bin/env bash
# PSX Intelligence AI — production stop (Phase 28).
# Stops ONLY the backend and frontend started by ops/start.sh (pid files in
# ${PSX_RUN_DIR:-/tmp/psx-prod}/). PostgreSQL is a shared system service and
# is deliberately NEVER stopped here: stop it manually if you really mean it
# (pg_ctlcluster 16 main stop) — see docs/phase-28/operations_handover.md.
set -u
RUN_DIR="${PSX_RUN_DIR:-/tmp/psx-prod}"
for name in frontend backend; do
  if [ -f "$RUN_DIR/$name.pid" ]; then
    pid="$(cat "$RUN_DIR/$name.pid")"
    if kill "$pid" 2>/dev/null; then echo "stopped $name (pid $pid)"; else echo "$name (pid $pid) already gone"; fi
    rm -f "$RUN_DIR/$name.pid"
  else
    echo "$name: no pid file (not started by ops/start.sh, or already stopped)"
  fi
done
echo "postgres: left running on purpose (shared system service)"
