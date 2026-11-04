# PSX Intelligence AI — Local Development Guide (Phase 2, Team A)

**Audience:** a new developer joining with a clean machine. **Goal:** from
zero to a running skeleton by following this guide + `README.md` + `.env.example`.
No step here installs a paid item, downloads a model, ingests data, or touches
a credential. If a step below conflicts with a Phase 1 gate, the gate wins.

## 1. Prerequisites (check first, install only what you need)

```bash
bash scripts/check_env.sh
```

You need: Python 3.12, Node 24, npm, Git (all verified present on the audit
machine — see `ENVIRONMENT_AUDIT.md`). You do NOT need Docker, PostgreSQL,
Redis, Ollama, or Tesseract to run the skeleton (see §5 for what each one
unlocks). Install methods for the missing tools are in
`ENVIRONMENT_AUDIT.md` §5; installing PostgreSQL/Redis/Docker is owned by
other teams, not by this guide's reader acting as Team A.

## 2. Get the code (no remote, no push — read this first)

Team A initialised a LOCAL Git repository inside
`~/workspace/psx-intelligence-ai/` only, with branches `main`,
`development`, `feature/frontend-foundation`, `feature/backend-foundation`,
`feature/database-foundation`. **No remote is configured and no push has
been made.** Pushing waits for Phase 2 acceptance (user decision
2026-11-04): before any future push, re-verify remote state, `git status`,
and that no secret / `.env` / credential file is tracked. Never commit
another team's in-progress files.

## 3. Configure — copy the example, never commit your own file

```bash
cp .env.example .env
# Edit .env with YOUR OWN local values.
```

### Configuration contract (the backend team implements validation; this table is the contract)

"Required" means the application must fail loudly with a clear message if
the value is missing/invalid — it must never silently fall back to a
production value, a guessed URL, or a real credential. Validation code
itself belongs to the backend team; this guide documents the contract only.

| Variable | Section | Required? | Default / placeholder | Validation rule |
|---|---|---|---|---|
| `APP_ENV` | runtime | Yes | `dev` | Must be one of `dev`, `test`, `prod`. Anything else = startup error. |
| `DEBUG` | runtime | No | `true` in dev | Boolean. Must be `false` when `APP_ENV=prod` (startup error otherwise). |
| `NEXT_PUBLIC_API_URL` | frontend | Yes (frontend) | `http://localhost:8000` | Valid http(s) URL. The browser uses this to reach the backend; it must never point at a PSX portal or library. |
| `NEXT_PUBLIC_APP_NAME` | frontend | No | `PSX Intelligence AI` | Display string only. |
| `BACKEND_HOST` / `BACKEND_PORT` | backend | No | `127.0.0.1` / `8000` | Host + port the API binds to. Dev binds loopback only; binding `0.0.0.0` is a deployment decision, not a dev default. |
| `CORS_ORIGINS` | backend | Yes in prod | `http://localhost:3000` (dev) | Comma-separated origins. Prod must list only the real frontend origin; `*` with credentials is forbidden. |
| `DATABASE_URL` | database | No — optional (see reconciliation note below) | No default; blank counts as unset | Backend config (`backend/app/config.py`) is authoritative: when unset/blank, the backend still starts and `/api/v1/system/status` truthfully reports `database: unavailable`. To connect the real local PostgreSQL, set it to the Team D URL from `database/.env` (local, gitignored — never commit a real password). A SQLite URL may be used for dev-only tests; it is not production proof. |
| `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis | Only when workers run | `redis://localhost:6379/0` (broker), `/1` (results) | Valid Redis URL. If Redis is unreachable, workers fail loudly at startup; the API and tests must still run without workers. |
| `STORAGE_BASE_DIR` + `STORAGE_*_DIR` | storage | No | `./storage/...` subdirs | Directories under the repo (git-ignored). Must never point at a shared/public directory; raw data is never published. |
| `LOG_LEVEL` / `LOG_FORMAT` / `LOG_FILE` | logging | No | `INFO` / `json` / `./logs/app.log` | `LOG_LEVEL` in `DEBUG, INFO, WARNING, ERROR`. One JSON-structured format everywhere (stdlib logging). |
| `OLLAMA_HOST` | local AI | No | `http://localhost:11434` | Local host only. Must never be a cloud host. |
| `OLLAMA_MODEL` | local AI | No — INTENTIONALLY BLANK | (empty) | Leave blank until the ADR-007 evaluation gate chooses a model and its licence is checked. A blank value disables LLM features; it is not an error. |
| `FRONTEND_PORT` | dev | No | `3000` | Next.js dev server port. |
| `VENV_DIR` | dev | No | `.venv` | Python venv directory; never committed. |
| `TEST_DATABASE_URL` | test | Yes (tests) | `sqlite:///./test.db` | Throwaway SQLite file. Tests must NEVER use `dev.db` or any production database. |

### Variables that must NEVER exist

No variable for an external AI API key, a broker credential, an Ollama Cloud
key, a paid-service key, or a production password may be added to
`.env.example` or to code without a new, explicit, recorded decision — the
PKR 0 stack has no such key by design. If you find one, treat it as a defect
and report it.

## 4. Run the skeleton

### Backend (dev, no-Docker path)

```bash
python3 -m venv .venv
source .venv/bin/activate
# Backend requirements/lockfile are owned by the backend team and are NOT in
# this skeleton. When they land, install from them — do not invent versions:
pip install -r backend/requirements.txt   # only once that file exists
# Dev database: SQLite file from DATABASE_URL (dev.db). No server needed.
# Start (module path owned by backend team; do not guess it if it differs):
python -m uvicorn app.main:app --reload   # placeholder shape only — see backend README
```

### Frontend (scaffold present)

```bash
cd frontend
npm install   # frontend team's step; node_modules is git-ignored
npm run dev   # http://localhost:3000
npm run lint && npm run build   # before any frontend commit
```

### Workers (only once Redis exists)

```bash
celery -A app.worker worker --loglevel=info   # only once Redis is running;
# module path owned by backend team. Without Redis, workers stay off and the
# API/tests must still work — that is a design requirement, not a workaround.
```

### Tests (offline-first)

```bash
python -m pytest        # backend: fake clients, no network, no PSX call
npx playwright test     # frontend E2E: local dev only (once suites exist)
```

No test suite for this application exists yet in this skeleton; no passing
tests are claimed for it. The reference scaffold's offline tests are a
separate scaffold fact, not a claim about this application.

## 5. What works without each service

| Service absent | Consequence |
|---|---|
| Docker | Use the no-Docker path above. Container packaging comes later (Phase 2 definition). |
| PostgreSQL | Use SQLite dev DB (`DATABASE_URL=sqlite:///./dev.db`). Migrations must still pass on PostgreSQL before any release. |
| Redis | Workers off; API + tests still run. Collection/PDF/report jobs queue only when Redis exists. |
| Ollama / model | LLM features disabled, not broken. All core features work. |
| Tesseract | Text-layer PDF extraction works; scanned-page OCR waits for Tesseract. |

## 6. Storage layout and rules

`storage/` tiers (all git-ignored): `raw/` (immutable payloads + provenance),
`processed/` (validated/derived, traceable to raw ids), `financial_reports/`
(PDFs + extraction method logged), `parquet/` (regenerable exports),
`research_reports/` (reports citing output ids/versions),
`backups/` (local backups, never committed/shared). Raw is never overwritten
by processed values. Retention follows
`docs/phase-01/DATA_RETENTION_POLICY.md`.

## 7. Data gates (apply from day one)

- **Do not ingest** from SECP / SBP / PBS / Finance Division / World Bank /
  IMF / FRED machine interfaces (G-01, UNVERIFIED). FRED is additionally
  gated out of AI training, caching, and commercial output (G-06).
- **Do not harmonise** ~496 vs ~1029 vs 1000+ symbols or 38 vs 37 sectors
  (G-03). Keep both values with provenance.
- **Do not republish** PSX data: no live-feed republication, public dataset,
  or commercial embedding without a PSX agreement in writing.
- **Do not invent** prices, figures, endpoints, or coverage. Unverified =
  marked UNVERIFIED with the check still needed.

## 8. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `git status` shows another team's files as untracked | Expected. Leave them alone; do not stage them. |
| Backend won't start: `DATABASE_URL` error | Check `.env` exists (copied from `.env.example`) and points at a writable SQLite path in dev. |
| Worker won't start: Redis connection refused | Redis absent or not running — workers stay off by design; run API/tests without them. |
| Frontend can't reach API | Check `NEXT_PUBLIC_API_URL` matches the backend host/port, and the backend is actually running. |
| `check_env.sh` reports a MISSING tool | Read `ENVIRONMENT_AUDIT.md` §5 for the free method — or confirm you don't need that tool for skeleton work (§5 above). |
| A licence question at install | Read the shipped LICENSE file, update `LICENSE_REGISTER.md`, and apply the stop-and-replace rule if payment is required. |

## 9. Team E addendum — verified local stack procedure (2026-11-04)

> Appended by Team E (Redis / Docker / local execution). This section
> does not replace §§1–8; where it gives a concrete, run-verified command
> that differs from a §4 placeholder, the verified command governs for the
> running stack, and the difference is called out below for the
> coordinator to reconcile.

### 9.1 Corrections to §4 placeholders (verified, not guessed)

- **Worker module path:** §4's `celery -A app.worker worker` is a
  placeholder shape owned by no team yet. The worker that actually runs
  is Team E's: `celery -A workers.celery_app worker --loglevel=info`
  (from the repo root), or `scripts/run_worker.sh`. Do not use
  `app.worker` — no such module exists in this repo.
- **Backend start (verified):** from `backend/` with Team C's venv:
  `backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
  Health endpoints verified live: `/health` and `/api/v1/health`.
- **Redis DB numbers:** broker DB 0, results DB 1
  (`CELERY_BROKER_URL=redis://127.0.0.1:6379/0`,
  `CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1`; `REDIS_URL` accepted
  as a broker alias). This aligns Team E's app with the §3 contract
  table; earlier Team E drafts used /0 for both and were corrected and
  retested on 2026-11-04 (see `REDIS_SETUP.md` Run 3).
- **DATABASE_URL variance — RESOLVED by coordinator (2026-11-04, docs only, no backend code changed):** §3 previously listed `DATABASE_URL` as required with a SQLite dev default; Team C's actual `backend/app/config.py` treats it as optional (`None` → endpoints report unavailable). The backend code is authoritative. §3 has been corrected to optional/no-default, and `scripts/dev.sh` correctly does not invent a PostgreSQL credential. Coordinator verification 2026-11-04: backend started on port 8001 with the Team D PostgreSQL URL (from gitignored `database/.env`, value not recorded here) reported `database: available, dialect: postgresql`; without the URL it truthfully reports `unavailable`. See §9.3 for the dev.sh observed state (unavailable by design, not a failure).

### 9.2 The verified procedure (no Docker — Docker is definition-only)

```bash
scripts/dev.sh            # defined start order: postgres (report only),
                          # redis, backend, frontend, worker; readiness
                          # wait up to 90 s; then a health summary
scripts/healthcheck.sh    # one line per service; exit 0 = no service FAILED
scripts/run_celery_proof.sh  # live add + health_probe round-trip
scripts/stop_dev.sh       # stops what dev.sh started; Redis is shut down
                          # ONLY if dev.sh started it
```

Logs/pids: `/tmp/psx-dev/*.log`, `/tmp/psx-dev/*.pid`.
Worker health, standalone: `python -m workers.healthcheck`
(exit 0 = Redis OK + fresh heartbeat; 2 = Redis unreachable;
3 = no fresh heartbeat). Dev-only fallback when Redis is absent:
`python -m workers.dev_fallback enqueue add 2 3 &&
python -m workers.dev_fallback run` — not Celery, not a scheduler.
Full evidence: `REDIS_SETUP.md` (Redis/Celery) and `DOCKER_SETUP.md`
(Docker blocker D-05, Compose definition).

### 9.3 Verified run (2026-11-04, this VM, via `scripts/dev.sh`)

| Service | Result |
|---|---|
| PostgreSQL | OK via `pg_isready` on 5432 (database team's cluster, untouched) |
| Redis | OK — PONG, 7.0.15 |
| Backend | OK — `/health` and `/api/v1/health` return `status: ok` |
| Backend ↔ DB | **Unavailable, truthfully:** `/api/v1/system/status` reports `database_url_not_set`. The cluster was up, but no URL/credential was invented for it; connecting it needs Team D's URL. |
| Frontend | OK — `GET /` HTTP 200 (Next.js 16.4.5 dev server) |
| Worker | OK — `celery inspect ping` pong, fresh heartbeat |
| Celery proof | OK — latest retest: add `2653df34-dc98-4de4-a687-b48717ea5b7b` → 5; health_probe `e96b12cf-c892-4aae-b123-ec3b47e808c5` → `status: ok` |
| Regression tests | `python -m pytest workers/tests -q` from repo root: 4 passed |

Machine headroom during the run: 7.7 GiB RAM total, ~1.1 GiB available
with the full stack up.

### 9.4 Team E troubleshooting additions

| Symptom | Cause / fix (full detail in `REDIS_SETUP.md` §5, `DOCKER_SETUP.md` §6) |
|---|---|
| Worker crashes: `ModuleNotFoundError: packaging` | kombu declares packaging only under its `redis` extra (D-01). Fixed: `packaging==26.3` pinned in `workers/requirements.txt`; recreate `workers/.venv`. |
| `dev.sh` summary briefly shows frontend FAILED / worker NOT RUNNING | Readiness race, fixed with a 90 s poll (D-03). Re-run `healthcheck.sh` before concluding failure. |
| `healthcheck.py` inspect error in script form only | `sys.path` difference (D-02), fixed; both `python workers/healthcheck.py` and `python -m workers.healthcheck` now pong. |
| pytest collection errors | Run from the repo root (tests import `workers.*`). |
| Docker pull/build TLS timeout | Daemon-to-registry failure on this VM (D-05). Use the no-Docker path; do not claim Docker verified. |
| `docker build` sends ~1 GB context | Missing repo-root `.dockerignore` (D-04, outside Team E scope — coordinator to add). |
