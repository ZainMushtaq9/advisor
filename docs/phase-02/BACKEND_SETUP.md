# PSX Intelligence AI — Backend Setup (Phase 2, Team C: Backend Foundation)

> Scope: foundation only. Real FastAPI app, versioned API, configuration,
> logging, validation, error handling, health endpoints, database
> connection interface, OpenAPI docs, restricted CORS, middleware and
> unit tests. **No Phase 3 schema, no financial functionality, no
> forecasting, no AI agents, no full-scale data collection.**
>
> Budget: PKR 0. Every dependency below is free/open-source; licences
> are recorded in `backend/LICENCES.md`. Local hardware, electricity
> and internet are external operating expenses, never called free.
>
> Ownership boundary: this team worked only inside `backend/` (plus
> this doc, which the task explicitly requested). `frontend/`,
> `database/`, `deployment/` and project-root files were not touched.
> The database team owns the actual PostgreSQL installation.

## 1. Verified environment

- Python **3.12.3** (present on this machine, verified 2026-11-04).
- PostgreSQL is **not installed/running here** — that is expected.
  With no `DATABASE_URL`, the API starts normally and
  `/api/v1/system/status` truthfully reports
  `database: {status: "unavailable", reason: "database_url_not_set"}`.
  It never hardcodes `ok` and never fakes a connection.
- Docker, `psql`, `redis-cli` were already reported absent in Phase 1;
  nothing in this setup requires them.

## 2. Install

From the project `backend/` directory:

```bash
cd ~/workspace/psx-intelligence-ai/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`.venv/` is gitignored. `requirements.txt` and `pyproject.toml` carry
the exact pins below (Phase 1 gate G-04).

### Pinned versions (installed and verified 2026-11-04)

| Package | Version | Licence |
|---|---|---|
| fastapi | 0.162.0 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| pydantic | 2.14.2 | MIT |
| pydantic-settings | 2.16.2 | MIT |
| SQLAlchemy | 2.1.8 | MIT |
| alembic | 1.20.1 | MIT |
| psycopg (+ psycopg-binary) | 3.3.7 | LGPL-3.0-only |
| httpx | 0.28.1 | BSD-3-Clause |
| pytest | 9.2.0 | MIT |
| ruff | 0.17.3 | MIT |

`psycopg` is the PostgreSQL driver variant pinned at setup (Phase 1
left the variant open). Full licence notes: `backend/LICENCES.md`.

## 3. Configure (environment variables)

Copy the template and edit it. Never commit a real `.env`:

```bash
cp .env.example .env
```

| Variable | Default | Meaning |
|---|---|---|
| `APP_NAME` | `psx-intelligence-ai` | Service name in responses |
| `ENVIRONMENT` | `development` | `development` / `production` / `test` |
| `DEBUG` | `false` | Rejected as `true` in production |
| `HOST` | `127.0.0.1` | Bind host |
| `PORT` | `8000` | Bind port |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `DATABASE_URL` | *(unset)* | SQLAlchemy URL, e.g. `postgresql+psycopg://<user>:<password>@<host>:<port>/<database>` (placeholders only). Leave unset until the database team provides PostgreSQL; the API reports the DB as unavailable instead of failing to start. A blank value counts as unset. SQLite (`sqlite:///./dev.db`) is a dev-only path per Phase 1, never production. |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated allowed origins. `*` is rejected in production; only `GET` methods are allowed by the CORS middleware. |

No credential is hardcoded anywhere in code; settings come only from
the environment / `.env` via Pydantic settings (`app/config.py`).

## 4. Run

```bash
cd ~/workspace/psx-intelligence-ai/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json
- Unversioned liveness alias: `GET /health` (Phase 1 monitor surface).

## 5. Endpoints (all report actual state)

| Endpoint | What it reports |
|---|---|
| `GET /api/v1/health` | Liveness only: `{"status":"ok","service":"psx-intelligence-ai","api_version":"v1"}`. Does not claim DB health. |
| `GET /api/v1/system/status` | Real Python/platform/package versions + a live DB probe (`available` / `unavailable`, dialect name only, exception class only — never the URL, host, user or password). |
| `GET /api/v1/system/version` | App version `0.1.0`, API version `v1`, Python version. |
| `GET /api/v1/config/status` | Each setting name with `SET` / `MISSING` and `source` (`environment` / `default` / `unset`) — **names only, never values**. A DATABASE_URL containing a secret is never echoed (covered by a test with a fake secret). |

### Real sample responses (2026-11-04, no DATABASE_URL set)

```json
// GET /api/v1/health
{"status": "ok", "service": "psx-intelligence-ai", "api_version": "v1"}

// GET /api/v1/system/status
{"service": "psx-intelligence-ai", "api_version": "v1", "environment": "development",
 "python_version": "3.12.3", "platform": "Linux-7.0.0-39-generic-x86_64-with-glibc2.39",
 "packages": {"fastapi": "0.162.0", "uvicorn": "0.54.0", "pydantic": "2.14.2",
              "sqlalchemy": "2.1.8", "alembic": "1.20.1"},
 "database": {"status": "unavailable", "reachable": false, "dialect": null,
              "reason": "database_url_not_set"}}

// GET /api/v1/system/version
{"service": "psx-intelligence-ai", "app_version": "0.1.0", "api_version": "v1",
 "python_version": "3.12.3"}

// GET /api/v1/config/status  (abridged; DATABASE_URL is the honest line)
{"settings": [{"name": "DATABASE_URL", "status": "MISSING", "source": "unset"}, "..."]}
```

With an unreachable PostgreSQL URL, `system/status` instead reports
`{"status": "unavailable", "reachable": false, "dialect": "postgresql+psycopg",
"reason": "connection_failed:OperationalError"}` — verified live
2026-11-04. With a reachable dev SQLite file it reports `available`.

### Error handling

- Unknown route → `404 {"error": "not_found", ...}`; wrong method → `405`;
  validation failure → `422 {"error": "validation_error", "detail": [...]}`;
  unexpected error → generic `500 {"error": "internal_error", ...}`.
  No response contains a stack trace, traceback, request body or secret.
- CORS preflight from a non-listed origin is rejected
  (`400 Disallowed CORS origin`, verified live).
- Logging is JSON-structured via the standard library only
  (`app/logging_config.py`); each request logs method, path, status,
  duration and a request id (`X-Request-ID` response header).

## 6. Tests and lint

```bash
cd ~/workspace/psx-intelligence-ai/backend
source .venv/bin/activate
python -m pytest -v        # 18 tests
ruff check app tests alembic
ruff format --check app tests alembic
```

Coverage (verified 2026-11-04, all passing): health, version, system
status (real versions; DB unavailable without URL; unavailable with an
unreachable URL; available with a reachable dev SQLite file),
config-status redaction (fake secret never echoed; blank URL counts as
MISSING), OpenAPI paths, 404/405/422 shapes without tracebacks, and
env validation (wildcard CORS and DEBUG rejected in production,
invalid environment rejected, blank DATABASE_URL treated as unset).

## 7. Migrations (foundation only)

Alembic is scaffolded with an intentionally **empty baseline migration**
(`alembic/versions/0001_baseline_empty.py`) — no Phase 3 tables, per
scope. `alembic/env.py` reads `DATABASE_URL` from the environment and
fails clearly when it is unset. Verified against a temporary SQLite file:

```bash
DATABASE_URL="sqlite:////tmp/psx_alembic_test.db" .venv/bin/alembic upgrade head
# -> Running upgrade -> 0001_baseline_empty, Baseline: no tables
DATABASE_URL="sqlite:////tmp/psx_alembic_test.db" .venv/bin/alembic current
# -> 0001_baseline_empty (head)
```

Real PostgreSQL migrations must be re-run against PostgreSQL by the
database team before any production claim (Phase 1 SQLite divergence
rule); a SQLite-only pass is not production proof.

## 8. File map

```text
backend/
  app/__init__.py            # __version__ = 0.1.0, api v1
  app/main.py                # create_app(), middleware, error handlers, /health alias
  app/config.py              # Pydantic settings, env/.env, CORS + prod validation
  app/logging_config.py      # stdlib JSON logging
  app/database.py            # engine/session factory, truthful check_database(), empty Base
  app/schemas.py             # foundation response models only
  app/api/v1/router.py       # /api/v1 prefix
  app/api/v1/endpoints/system.py  # the four endpoints
  alembic.ini, alembic/env.py, alembic/script.py.mako
  alembic/versions/0001_baseline_empty.py
  tests/conftest.py, tests/test_endpoints.py, tests/test_errors_and_config.py
  pyproject.toml, requirements.txt, LICENCES.md, .env.example, .gitignore
  .venv/                     # gitignored virtualenv
```

## 9. Blockers / open items

- **None blocking for this phase.** All tests, lint and live endpoint
  checks pass.
- **Expected, not a blocker:** PostgreSQL is not installed or running
  on this machine, so `database: unavailable` is the correct current
  state. The database team owns provisioning; once `DATABASE_URL`
  points at a real PostgreSQL instance, `/api/v1/system/status` will
  report `available` with no code change.
- **Minor warning (non-blocking):** pytest prints a
  `StarletteDeprecationWarning` that Starlette's TestClient using
  `httpx` is deprecated in favour of `httpx2`. Tests still pass; no
  action taken, since `httpx2` was not a task-listed dependency and
  adopting it would add an unverified package.
- **Not done, by instruction:** nothing was committed to git
  (no git repository exists at the project path, and the task forbade
  committing). A separate decision recorded in memory says to wait
  until Phase 2 finishes before pushing to a remote; no push was made.
