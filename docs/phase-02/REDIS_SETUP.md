# PSX Intelligence AI — Redis + Celery Setup (Phase 2, Team E)

> Status: **VERIFIED RUNNING on this VM, 2026-11-04** (Redis + Celery proof
> below). PKR 0 licence cost. No paid/managed service, no credential in any
> file, no market data, no agent scheduler.
>
> Phase 1 basis: `docs/phase-01/TECH_STACK_DECISIONS.md` §2.7 and
> `docs/phase-01/ADR/ADR-004-background-processing.md` — Celery + self-hosted
> Redis is the fixed stack. APScheduler is not used. Celery Beat is
> deliberately **not** configured: scheduling is a later-phase decision,
> not a Phase 2 Team E artefact.

## 1. What was installed, and how (exact evidence)

Environment at run time: Ubuntu 24.04.5 LTS, Python 3.12.3, root user,
4 CPUs, 7.7 GiB RAM. Disk measured on this VM is a 7.5 GiB overlay
(6.9 GiB free when Docker work started) — not the 147 GiB in the task
brief; that brief figure was not reproduced here and is not relied on.

| Component | Install command | Version verified | Licence verified (how) |
|---|---|---|---|
| Redis server | `apt-get update && apt-get install -y redis-server` (Ubuntu `noble-updates/universe`) | `Redis server v=7.0.15`, `redis-cli 7.0.15` | BSD-3-Clause — `/usr/share/doc/redis-server/copyright`, `Files: * / License: BSD-3-clause`. Redis 7.0 is **before** the 7.4 RSALv2/SSPLv1 change, so the Phase 1 tri-licence note for Redis 8 does not apply to this install; if Redis is ever upgraded to 7.4+/8, the licence option operated under must be recorded anew. |
| Celery | `pip install celery redis` (in a venv; pinned in `workers/requirements.txt`) | celery 5.6.3 (`celery --version`) | BSD-3-Clause — package METADATA `License: BSD-3-Clause` |
| redis-py | same pip install | redis 8.1.0 | MIT — package METADATA `License-Expression: MIT` |
| packaging | pinned explicitly (see defect D-01) | packaging 26.3 | (BSD/Apache-style, via kombu's extra pin; recorded here only as a version pin, not a licence claim) |

**systemd note (environment constraint, not a defect in this code):**
`apt` setup printed `invoke-rc.d: policy-rc.d denied execution of start`
for redis-server, so systemd did not start it. Redis was therefore started
manually, loopback-only:

```bash
redis-server --daemonize yes --port 6379 --save '' --appendonly no \
  --protected-mode yes --bind 127.0.0.1
redis-cli ping   # PONG
```

Persistence is intentionally off in this dev command (`--save ''`,
`--appendonly no`): Redis here is a broker + result backend, not a system
of record. The Compose file (production-shaped) uses `--appendonly yes`
with a persistent volume instead — see `DOCKER_SETUP.md`.

## 2. The Celery app (`workers/`)

| File | Role |
|---|---|
| `workers/celery_app.py` | App factory. Broker + result backend from `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`, defaults broker `redis://127.0.0.1:6379/0`, results `redis://127.0.0.1:6379/1` (DB numbers aligned to the Team A contract in `LOCAL_DEVELOPMENT_GUIDE.md` §3; `REDIS_URL` is accepted as a broker alias). JSON serializer only (never pickle). Bounded retries (max 3, back-off, 30 s default delay), results expire after 3600 s, UTC with Asia/Karachi display timezone. Writes a TTL'd worker heartbeat (`psx:worker:heartbeat`, 120 s) on `worker_ready`, deletes it on shutdown. **No Beat, no periodic tasks, no scheduler.** |
| `workers/tasks.py` | Probe tasks ONLY: `psx_intelligence_ai.add(a, b)` and `psx_intelligence_ai.health_probe()` (returns worker hostname + UTC timestamp, no data). Every task logs task id, name, inputs and result at INFO; failures and retries are logged separately. Real collection/PDF/report jobs are later-phase tasks with their own specs — they must not be added by extending these probes. |
| `workers/healthcheck.py` | Exit-code health check: 0 = Redis OK + fresh heartbeat; 2 = Redis unreachable; 3 = Redis OK but no fresh heartbeat. Also reports `celery inspect ping` (advisory). Run as `python -m workers.healthcheck` or `python workers/healthcheck.py`. |
| `workers/dev_fallback.py` | **Dev-only, not Celery, not a scheduler.** SQLite-backed in-process queue (`workers/dev_queue.db`, gitignored) running only the probe functions, one at a time, max 3 attempts. Use only when Redis is absent (Phase 1 Config A). Commands: `enqueue`, `run`, `status`. Never for production data or multi-worker work. |
| `workers/requirements.txt` | Pinned, installed versions: celery 5.6.3, redis 8.1.0, packaging 26.3 (D-01). |
| `workers/tests/` | `test_tasks_eager.py` (eager mode, no broker) + `test_dev_fallback.py` (stdlib SQLite). **Run from the repo root** (`python -m pytest workers/tests -q`): the tests import `workers.*`, so running pytest from another directory fails at collection — that is an invocation requirement, not a code failure (seen 2026-11-04, re-run from repo root: 4 passed). |

Run a worker (foreground):

```bash
scripts/run_worker.sh            # creates workers/.venv on first use
# or, full stack:
scripts/dev.sh
```

## 3. Proof — live task execution (verifiable)

Two independent live runs, both against the real Redis broker (not eager):

**Run 1 — ad-hoc proof venv, 2026-11-04 11:38 PKT (06:38 UTC).**
Worker `psx-worker@proof`, heartbeat `2026-11-04T06:37:59+00:00` (TTL 114 s
remaining when read).

- `add.delay(2, 3)` → task id `f385288e-d0e3-43aa-892c-3894569ff343`,
  state `SUCCESS`, result `5`.
- `health_probe.delay()` → task id `734cee42-b66b-4181-8b8f-0ca372ad99e7`,
  result `{'status': 'ok', 'worker': 'htch-runtime',
  'timestamp_utc': '2026-11-04T06:38:10.980218+00:00'}`.
- Worker log lines confirm start + success for both task ids.

**Run 2 — retest via `scripts/dev.sh` + `scripts/run_celery_proof.sh`,
2026-11-04 11:46 PKT (06:46 UTC), after defect D-01 was fixed and
`workers/.venv` was recreated from scratch.**
Worker `celery@htch-runtime`, heartbeat `2026-11-04T06:45:41+00:00`,
`celery inspect ping` → `{'celery@htch-runtime': {'ok': 'pong'}}`.

- `add.delay(2, 3)` → task id `426203f1-cf6c-492b-b34e-e3832345c71d`,
  result `5`, `SUCCESS`.
- `health_probe.delay()` → task id `17e7c05c-4886-43a4-ae90-f569372c7de4`,
  result `{'status': 'ok', 'worker': 'htch-runtime',
  'timestamp_utc': '2026-11-04T06:46:09.569741+00:00'}`, `SUCCESS`.
- `scripts/run_celery_proof.sh` printed `PROOF OK: both tasks returned SUCCESS`.
- Regression tests from repo root: `4 passed, 2 warnings`
  (warnings are a Celery-internal `setex` deprecation in its Redis backend,
  not a test failure).

**Run 3 — alignment retest, 2026-11-04 11:48 PKT (06:48 UTC).** After the
broker/results DB numbers were aligned to the Team A contract (broker /0,
results /1) and the worker was restarted from `scripts/dev.sh`,
`run_celery_proof.sh` again printed `PROOF OK`: add task
`2653df34-dc98-4de4-a687-b48717ea5b7b` → 5, health_probe
`e96b12cf-c892-4aae-b123-ec3b47e808c5` → `status: ok`, and the worker
health check again reported pong. Regression tests re-run: 4 passed.

The dev fallback was also exercised with stdlib Python only:
`enqueue add 2 3` → id 1 → `run` → `{"status": "done", "result": 5}`.

## 4. Environment variables (no secrets)

| Variable | Default | Meaning |
|---|---|---|
| `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` | Redis broker (Compose: `redis://redis:6379/0`) |
| `CELERY_RESULT_BACKEND` | `redis://127.0.0.1:6379/1` | Redis result backend (Compose: `redis://redis:6379/1`) |
| `REDIS_URL` | (unset) | Broker alias, used only if `CELERY_BROKER_URL` is unset |
| `PSX_DEV_QUEUE_PATH` | `workers/dev_queue.db` | Dev-fallback queue file only |

No password is set on dev Redis: it binds loopback only (direct path) or
sits on Compose's private `data_net` (container path). If a password is
ever added, it must come from `.env`, never from a committed file.

## 5. Defects found and fixed (for DEFECT_REGISTER.md)

| ID / severity | Defect (reproduced) | Root cause | Fix | Retest |
|---|---|---|---|---|
| D-01 / High (worker would not start from a fresh venv) | `ModuleNotFoundError: No module named 'packaging'` from `kombu/transport/redis.py` when the worker was started by `scripts/dev.sh` from a fresh `workers/.venv`. | kombu 5.7.0 imports `packaging.version` unconditionally but declares `packaging==26.3` only under its `redis` extra, which celery does not request — so `pip install celery redis` leaves it missing. The first proof venv had masked this because pytest (installed later there) had pulled packaging in. | Pinned `packaging==26.3` explicitly in `workers/requirements.txt` with this explanation in a comment. No feature disabled. | Deleted `workers/.venv`, re-ran `scripts/dev.sh`: worker started, heartbeat fresh, `run_celery_proof.sh` → PROOF OK (Run 2 ids above). |
| D-02 / Low (health check, script form only) | `python workers/healthcheck.py` reported `worker_inspect: error: ImportError` while `python -m workers.healthcheck` reported a pong. Exit code was still correct (0), but the inspect line was wrong in script form. | Script form puts `workers/` (not the repo root) on `sys.path`, so the package import failed and the relative-import fallback also failed (no package context). | Health check now inserts the repo root (parent of its own file) into `sys.path` before importing `workers.celery_app`. | Both invocation forms now report `{'celery@htch-runtime': {'ok': 'pong'}}` / `{'psx-worker@proof': {'ok': 'pong'}}`. |
| D-03 / Low (dev.sh reporting, not a service failure) | First `scripts/dev.sh` summary showed frontend FAILED and worker NOT RUNNING although both became healthy within ~30 s. | Fixed `sleep 2` before the summary was shorter than Next.js first-page compile and Celery `worker_ready`. The services were fine; the check raced them. | `dev.sh` now polls backend /health, frontend /, and the worker health check for up to 90 s (5 s interval) before printing the summary, skipping the worker wait only when no worker was started. | Second `dev.sh` run printed `all expected services ready` and all-OK summary. |

## 6. What this does NOT do

- No Celery Beat, no periodic schedule, no agent scheduler, no cron job.
- No market-data job, no PSX figure, no fabricated data anywhere.
- No managed Redis, no paid service, no credential in any committed file.
- The backend is **not** connected to PostgreSQL by this work: `dev.sh`
  never invents a `DATABASE_URL`. On 2026-11-04 the database team's
  cluster was up (`pg_isready` OK on 5432) but the backend was started
  with `DATABASE_URL` unset, so `/api/v1/system/status` truthfully
  reported `database: unavailable, reason: database_url_not_set`.
  Connecting it is Team D's URL/credential to supply, not Team E's to guess.
