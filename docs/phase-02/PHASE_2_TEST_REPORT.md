# PSX Intelligence AI — Phase 2 Test Report

Date: 2026-11-04. Coordinator re-runs on this VM unless a row says
"team-reported only". No test result is copied from a team report
without a coordinator re-run, except where explicitly marked.

## Coordinator re-verification results

| # | Test | Command / evidence | Result |
|---|---|---|---|
| T-01 | Backend pytest | `backend/.venv/bin/python -m pytest -q` | PASS — 18 passed, 1 Starlette deprecation warning (non-blocking, D-04 in defect register) |
| T-02 | Backend lint/format | `ruff check app tests alembic` | PASS — all checks passed |
| T-03 | Frontend typecheck | `npm run typecheck` (tsc --noEmit) | PASS — no errors |
| T-04 | Frontend lint | `npm run lint` (eslint) | PASS |
| T-05 | Frontend unit/component tests | `npm test` (Vitest) | PASS — 3 files, 11 tests |
| T-06 | Frontend build | `npm run build` | PASS — 8 static routes: /, /_not-found, /admin, /alerts, /companies, /dashboard, /portfolio, /research |
| T-07 | Frontend routes live (dev server :3000) | curl each route | PASS — / /dashboard /companies /research /portfolio /alerts /admin all HTTP 200 with "Foundation shell" banner; /no-such-route HTTP 404 |
| T-08 | Backend endpoints live (:8000) | curl /api/v1/health, /system/status, /system/version, /config/status | PASS — health ok, version 0.1.0, config names only (no values), DB truthfully unavailable without DATABASE_URL |
| T-09 | Backend ↔ PostgreSQL | Temp uvicorn on :8001 with DATABASE_URL from gitignored database/.env (value not recorded) | PASS — system/status: database available, dialect postgresql; config/status DATABASE_URL SET source environment |
| T-10 | DB health check | `database/.venv/bin/python database/scripts/health_check.py` with DATABASE_URL sourced | PASS — SELECT 1 = 1, server_version 16.15, tables alembic_version + phase2_probe only |
| T-11 | DB probe insert/retrieve | `database/.venv/bin/python database/scripts/probe_test.py` with DATABASE_URL sourced | PASS — inserted id 4, retrieved label/note exactly (labelled TEST — NOT PSX DATA), cleanup count 0, bad-connection cases correctly raise OperationalError |
| T-12 | DB migration up/down/re-up | Team D evidence + coordinator health check showing alembic_version present; migration file 20261104_0001 reviewed | PASS (team-reported up/down/re-up; coordinator verified head state, not a fresh down/up cycle — recorded honestly) |
| T-13 | Storage integrity | `python3 storage/test_storage_helper.py` | PASS — write hash match, read-back match, tamper fails, missing sidecar fails, unsafe paths rejected, overwrite refused |
| T-14 | Worker eager tests | `workers/.venv/bin/python -m pytest workers/tests/ -q` from REPO ROOT | PASS — 4 passed, 2 warnings (Celery setex deprecation). Note: pytest had to be installed into workers/.venv first (requirements-dev.txt added by coordinator); running from workers/ fails with ModuleNotFoundError: workers — run from repo root |
| T-15 | Celery live proof (real broker) | `bash scripts/run_celery_proof.sh` (multiple runs) | PASS — latest coordinator run: add task → 5, health_probe → status ok, PROOF OK; earlier Team E runs: add → 5 (three task IDs), health_probe → ok |
| T-16 | Worker healthcheck (fixed) | `workers/.venv/bin/python workers/healthcheck.py` + `scripts/healthcheck.sh` | PASS after coordinator fix — see defect D-22: heartbeat-only logic falsely reported NOT RUNNING (heartbeat is written only on worker_ready, TTL 120 s); fixed to accept inspect ping as authoritative liveness, heartbeat still reported separately |
| T-17 | Full-stack healthcheck script | `scripts/healthcheck.sh` | PASS for postgres/redis/backend/frontend (all OK); worker row now OK after D-22 fix (re-run recorded in audit report) |
| T-18 | Backup/restore | Coordinator re-run: `bash database/backup.sh` with DATABASE_URL sourced, then `bash database/restore.sh <latest>` to separate DB | PASS — backup 2026-11-04T1154-PKT, dump SHA-256 75b561597802f5917772c861b38e7f51e5d4eecefd97f1836a2543aca60d88a3, restore VERIFIED (phase2_probe rows restored 1 = manifest 1), with the 2 known harmless pg_restore default-privilege warnings documented by Team D. Team D's earlier backups (1140-PKT, 1142-PKT) were also restore-verified by Team D. Live-restore refusal without ALLOW_LIVE_RESTORE=1 was tested by Team D (exit 2) |
| T-19 | Docker compose validation | Team E: `docker compose config --quiet` | TEAM-REPORTED PASS (config valid) — but NO container built or run (see T-20) |
| T-20 | Docker build/run | Team E: docker build / pulls | FAIL (environment blocker, not code) — every registry pull fails with daemon TLS handshake timeout; docker images empty; no container run. Docker is therefore DEFINITION-ONLY. The verified path is the no-Docker local execution (scripts/dev.sh + healthcheck.sh) |
| T-21 | Playwright E2E | Coordinator attempt 2026-11-04: `npm install -D @playwright/test` → package 1.64.1 installed; `npx playwright install chromium` → FAILED: "Failed to download Chrome for Testing 156.0.8078.4 (playwright chromium v1248), Download failure, code=1". No system chromium found, no ~/.cache/ms-playwright cache. | NOT RUN — browser could not be downloaded on this VM (same class of environment/network failure as Docker registry TLS timeout, but a different endpoint/error). Frontend testing is therefore Vitest + build + dev-server curl checks, not browser E2E. Recorded as a follow-up (retry browser install on a machine with working CDN access, or point Playwright at a system chromium), not a pass. The @playwright/test package entry remains in frontend/package.json so the E2E intent is not lost |
| T-22 | Secret scan (manual) | Grep of .env.example files, team files, git status for secrets | PASS for committed scope — placeholders only (e.g. changeme-dev-only); real DB password only in gitignored database/.env (0600). Full git-history scan to be re-run at final commit (see audit report) |

## Failed / not-run tests (honest list)

1. Docker build/run — FAILED, environment blocker D-05 (Team E). Does not
   block Phase 2 acceptance, because acceptance item 17 allows "Docker
   works OR a verified alternative is documented" — the verified
   alternative is the no-Docker local stack.
2. Playwright E2E — NOT RUN (package installed, browser download
   failed, code=1). Does not block the "automated tests execute"
   acceptance item (backend, frontend unit, worker, storage, and DB
   tests all execute and pass), but it is a documented gap for a
   later phase to close by retrying the browser install elsewhere.
3. Migration fresh down/up cycle — coordinator verified head state
   only; Team D's up/down/re-up evidence is team-reported. The next
   phase must re-run a fresh down/up cycle before relying on migration
   history for production data.

## Tests that must NOT be read as production proof

- SQLite passes in backend tests are dev-only; PostgreSQL proof is the
  port-8001 run (T-09) and Team D's cluster evidence, not the SQLite
  test cases.
- Frontend route checks prove foundation shells render, not that any
  PSX data is displayed (there is none — by design).
- Probe/demo rows and files are labelled TEST / NOT PSX DATA and
  must never be presented as market data.
