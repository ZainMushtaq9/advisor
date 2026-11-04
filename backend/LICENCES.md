# Dependency licences — backend, Phase 2 foundation

Checked 2026-11-04 from each installed package's own metadata
(`License-Expression` / `License` field, via `importlib.metadata`).
All items below are free/open-source; **none required payment, a
subscription, a sign-up or a credential**. If any future dependency
required payment, it must be stopped and replaced (Phase 1 gate G-02).

Note: local hardware, electricity and internet are external operating
expenses (Phase 1 disclosure) — they are not licence costs and are
never described as free.

## Direct dependencies (pinned in requirements.txt)

| Package | Version | Licence (as shipped) | Role |
|---|---|---|---|
| fastapi | 0.162.0 | MIT | Web framework |
| uvicorn | 0.54.0 | BSD-3-Clause | ASGI server |
| pydantic | 2.14.2 | MIT | Validation / schemas |
| pydantic-settings | 2.16.2 | MIT | Env / `.env` settings |
| SQLAlchemy | 2.1.8 | MIT | ORM / engine / sessions |
| alembic | 1.20.1 | MIT | Migrations |
| psycopg (+ psycopg-binary) | 3.3.7 | LGPL-3.0-only | PostgreSQL driver (used unmodified as a library; no code is linked into a redistributed derivative — if the project ever redistributes a combined work, re-check LGPL obligations then) |
| httpx | 0.28.1 | BSD-3-Clause | Test client transport |
| pytest | 9.2.0 | MIT | Test runner |
| ruff | 0.17.3 | MIT | Lint / format check |

## Notable transitive dependencies (same check method)

| Package | Version | Licence |
|---|---|---|
| starlette | 1.10.0 | BSD-3-Clause |
| anyio | 4.16.0 | MIT |
| Mako | 1.4.3 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| python-dotenv | 1.2.4 | BSD-3-Clause |

## Deliberately NOT included in Phase 2 foundation

pandas, NumPy, scikit-learn, statsmodels, Celery, Redis clients,
PyMuPDF, Ollama clients and PyTorch are Phase 1 stack items for later
phases/tasks — they are not installed here, so no licence or cost
claim is made for them in this phase. When a later phase adds one, its
shipped licence must be recorded here first, per Phase 1 gate G-02/G-04.
