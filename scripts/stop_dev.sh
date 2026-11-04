#!/usr/bin/env bash
# Stop services started by scripts/dev.sh (pid files in /tmp/psx-dev/).
# Redis is shut down ONLY if dev.sh started it (flag file present) — a
# pre-existing Redis owned by someone else is never touched.
set -u
LOGDIR=/tmp/psx-dev
for name in frontend backend worker; do
  if [ -f "$LOGDIR/$name.pid" ]; then
    pid="$(cat "$LOGDIR/$name.pid")"
    if kill "$pid" 2>/dev/null; then echo "stopped $name (pid $pid)"; else echo "$name (pid $pid) already gone"; fi
    rm -f "$LOGDIR/$name.pid"
  fi
done
if [ -f "$LOGDIR/redis.started-by-dev" ]; then
  redis-cli shutdown nosave 2>/dev/null && echo "stopped redis (started by dev.sh)" || echo "redis shutdown failed or already stopped"
  rm -f "$LOGDIR/redis.started-by-dev"
else
  echo "redis left running (not started by dev.sh, or no redis-cli)"
fi
