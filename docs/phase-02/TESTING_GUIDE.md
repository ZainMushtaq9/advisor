# PSX Intelligence AI — Testing Guide (Phase 2)

## Single documented test command (coordinator, 2026-11-04)

There is no single script yet that runs every suite in one invocation
without a running stack, so the verified sequence is documented here
and in scripts/dev.sh / scripts/healthcheck.sh. A future `scripts/test_all.sh`
is technical debt TD-08 (see docs/development/TECHNICAL_DEBT.md) — do not
claim it exists.

```bash
# Backend (from backend/, venv already created)
backend/.venv/bin/python -m pytest -q
backend/.venv/bin/ruff check app tests alembic

# Frontend (from frontend/)
npm run typecheck
npm run lint
npm test            # Vitest
npm run build

# Database + storage (DATABASE_URL from gitignored database/.env)
set -a; source database/.env; set +a
database/.venv/bin/python database/scripts/health_check.py
database/.venv/bin/python database/scripts/probe_test.py
python3 storage/test_storage_helper.py

# Workers (from REPO ROOT — tests import workers.*)
workers/.venv/bin/python -m pytest workers/tests/ -q
bash scripts/run_celery_proof.sh   # live broker proof, needs Redis + worker

# Full local stack (needs PostgreSQL, Redis, backend, frontend, worker)
scripts/dev.sh
scripts/healthcheck.sh
```

Note on worker tests: `workers/requirements.txt` contains runtime deps
only. Test runs need pytest, recorded in `workers/requirements-dev.txt`
(coordinator fix 2026-11-04: workers/.venv initially had no pytest, so
the tests could not be reproduced until it was installed). Run worker
tests from the repo root, not from `workers/`.

## What each suite proves (and does not prove)

| Suite | Proves | Does NOT prove |
|---|---|---|
| Backend pytest 18/18 | 4 endpoints, config redaction, error handling without traces, env validation, DB unavailable/unreachable/available cases, OpenAPI paths | Production PostgreSQL behaviour — SQLite passes in tests are dev-only; the coordinator separately verified PostgreSQL availability via a port-8001 run with the Team D URL |
| Frontend Vitest 11 tests | Env URL resolution, API client success/failure/unreachable, component empty states + shell notice | Browser E2E — Playwright was NOT installed in Phase 2 (Team B follow-up) |
| Frontend build | 8 static routes compile, TypeScript clean | Live preview — the github.dev URL is UNVERIFIED (sign-in page only); local dev-server curl checks are the only live route evidence |
| DB health/probe | SELECT 1, server version, probe insert/retrieve/cleanup, migration up/down/re-up, connection-failure handling | Any Phase 3 table — only `phase2_probe` exists |
| Storage helper tests | Hash match, tamper/missing-sidecar failure, unsafe-path rejection, overwrite refusal | Real PSX document handling — demo file only, labelled NOT PSX DATA |
| Worker eager tests 4/4 | Task logic + logging wiring in-process | Broker path — proved separately by `run_celery_proof.sh` live (add → 5, health_probe → ok) |
| Backup/restore | Dump + manifest hash verification, restore to a separate DB with row-count gate | Automated rotation — rotation is documented, manual until Phase 3, never below the 2-backup floor |

## Coordinator re-verification (2026-11-04, this VM)

Backend pytest 18 passed, ruff pass; frontend typecheck pass, lint pass,
Vitest 11 passed, build pass (8 static routes); DB health + probe pass
with DATABASE_URL sourced; storage tests all pass; worker eager tests
4 passed from repo root; Celery live proof OK (new task IDs recorded
in PHASE_2_TEST_REPORT.md); frontend dev-server routes 200 (see
PHASE_2_TEST_REPORT.md for the route table and the one pending
healthcheck run). No test result in this guide is copied from a team
report without a coordinator re-run, except where the test report
explicitly says so.
