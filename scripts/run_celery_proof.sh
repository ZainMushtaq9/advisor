#!/usr/bin/env bash
# Reproduce the Phase 2 Celery proof (Phase 2, Team E).
# Requires a running worker (scripts/run_worker.sh or scripts/dev.sh) and
# Redis on 127.0.0.1:6379. Prints both task ids and both results; exits
# non-zero if either task does not return SUCCESS.
#   scripts/run_celery_proof.sh
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/workers/.venv/bin/python"
[ -x "$PY" ] || PY="python3"
cd "$ROOT"
"$PY" -c "
from workers.tasks import add, health_probe
r1 = add.delay(2, 3)
print('ADD_TASK_ID', r1.id)
print('ADD_RESULT', r1.get(timeout=30))
assert r1.state == 'SUCCESS' and r1.result == 5
r2 = health_probe.delay()
print('PROBE_TASK_ID', r2.id)
print('PROBE_RESULT', r2.get(timeout=30))
assert r2.state == 'SUCCESS' and r2.result['status'] == 'ok'
print('PROOF OK: both tasks returned SUCCESS')
"
