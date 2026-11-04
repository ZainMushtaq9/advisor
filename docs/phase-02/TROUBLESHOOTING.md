# PSX Intelligence AI — Troubleshooting (Phase 2)

## Environment

| Symptom | Cause / fix |
|---|---|
| `psql` / `redis-cli` / `docker` not found | Not installed at Phase 1. PostgreSQL 16.15 and Redis 7.0.15 were installed via apt in Phase 2 (Team D/E). Docker Engine 29.1.3 (docker.io) is installed but registry pulls fail — see Docker below. Re-run `scripts/check_env.sh`, do not copy an old audit file. |
| PostgreSQL not accepting connections after reboot | `policy-rc.d` denies systemd start on this VM. Run `pg_ctlcluster 16 main start`, then `pg_isready`. |
| Redis not responding | Redis was started manually loopback-only (systemd denied). Start it manually; `redis-cli ping` must return PONG. Shut down with `redis-cli shutdown nosave` if it was started manually (stop_dev.sh only stops what dev.sh started). |
| Only ~0.8–1.1 GiB RAM available, no GPU | Host limits, not a code defect. Do not download Ollama models on this VM; core features must work with Ollama absent. |

## Backend

| Symptom | Cause / fix |
|---|---|
| `/api/v1/system/status` reports `database: unavailable` | Correct when DATABASE_URL is unset/blank — not a failure. Set it to the Team D URL from gitignored `database/.env` (never commit it) and restart; the coordinator verified `available, dialect: postgresql` this way on port 8001. |
| `DATABASE_URL=` blank reported as SET | Fixed by Team C (effective value decides SET vs MISSING; regression test exists). If you see the old behaviour, you are running pre-fix code. |
| 422 / 404 / 405 responses | Expected validation/routing behaviour; responses contain no tracebacks by design. Check the request shape against OpenAPI (`/docs`, `/openapi.json` lists exactly the four `/api/v1/*` paths). |
| Wildcard CORS / DEBUG=true rejected in production | By design (config validation). Fix the env values, do not weaken the validator. |

## Frontend

| Symptom | Cause / fix |
|---|---|
| Home badge reads "Backend not connected yet" | Correct until the backend serves `/health` on `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). Start the backend; do not hardcode a fake ok. |
| `vitest@latest` peer conflict | Known: Vitest 3.2.4 / jest-dom 6.9.1 are pinned instead (no `--force`/`--legacy-peer-deps`). Do not upgrade blindly. |
| Theme hydration lint warning | One justified `eslint-disable` for the browser-only localStorage read (default matches server render). Do not remove it without re-testing lint. |

## Database / storage

| Symptom | Cause / fix |
|---|---|
| `DATABASE_URL is not set` from health/probe scripts | Scripts require the env var. Run `set -a; source database/.env; set +a` first (password stays in the gitignored file, never in docs/logs). |
| Superuser psql commands fail auth as `psx_app` | Sourcing `database/.env` exports PGUSER. Use `-U postgres` with `env -u PGUSER -u PGPASSWORD -u PGDATABASE` for superuser commands. |
| Generated password breaks psql `-v` quoting | Use alphanumeric-only generated passwords (Team D fix). |
| Backup tar/restore exit code masked | Fixed by Team D (tar fails loudly under `set -e`; restore prints a warning and the row-count gate is authoritative). The 2 known harmless pg_restore default-privilege warnings are documented in DATABASE_SETUP.md. |
| Storage test fails on missing sidecar / Path vs str | Fixed by Team D (identical rewrite regenerates a missing sidecar; validator coerces Path to str). Re-run `python3 storage/test_storage_helper.py`. |

## Workers / Docker

| Symptom | Cause / fix |
|---|---|
| Worker crashes `ModuleNotFoundError: packaging` | kombu declares packaging only under its `redis` extra. `packaging==26.3` is pinned in `workers/requirements.txt`; recreate `workers/.venv`. |
| Worker tests fail `ModuleNotFoundError: workers` | Run from the REPO ROOT, not from `workers/`: `workers/.venv/bin/python -m pytest workers/tests/ -q`. Also install test deps from `workers/requirements-dev.txt` (pytest was initially missing from workers/.venv — coordinator fix). |
| `dev.sh` briefly shows frontend FAILED / worker NOT RUNNING | Readiness race, fixed with a 90 s poll. Re-run `scripts/healthcheck.sh` before concluding failure. |
| Docker pull/build TLS handshake timeout | Daemon-to-registry failure on this VM (DOCKER_SETUP.md D-05). Use the no-Docker path (`scripts/dev.sh`); do not claim Docker verified, do not use an untrusted-image workaround. Retry on a machine with working registry access. |
| `docker build` sends ~1 GB context | Fixed by coordinator: repo-root `.dockerignore` now excludes node_modules, .venv, .next, .git, storage data, *.db. First real build should show a few MB context. |
| Live preview URL returns a sign-in page | The supplied github.dev URL is NOT a runtime or preview (see LIVE_TEST_REPORT.md). Use the local VM; mark live preview UNVERIFIED unless actually inspected. |
