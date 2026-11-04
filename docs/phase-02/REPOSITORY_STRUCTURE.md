# PSX Intelligence AI — Repository Structure (Phase 2)

## Root layout (verified 2026-11-04)

```
psx-intelligence-ai/
  README.md, CONTRIBUTING.md, CHANGELOG.md, .gitignore, .env.example, .dockerignore
  frontend/        Next.js 16.4.5 + React 19.3.0 + TypeScript + Tailwind 4.3.4
    app/           App Router routes: /, /dashboard, /companies, /research,
                   /portfolio, /alerts, /admin (+ error, not-found, loading)
    components/    site-header/footer, theme, ui, data-table, chart-container,
                   foundation-shell, api-status, error-boundary
    features/ hooks/ lib/ services/ types/ styles/ tests/
  backend/         FastAPI 0.162.0 + Pydantic 2.14.2 + SQLAlchemy 2.1.8 + Alembic 1.20.1
    app/           main, config, database, logging_config, schemas,
                   api/v1/router + endpoints/system
    alembic/       env.py, script.py.mako, versions/0001_baseline_empty.py
    tests/         conftest, test_endpoints, test_errors_and_config
    pyproject.toml, requirements.txt, LICENCES.md, .env.example, .gitignore
  database/        PostgreSQL 16.15 infrastructure (Phase 2 only)
    migrations/    env.py, script.py.mako, versions/20261104_0001_phase2_probe.py
    schemas/       phase2-scope.md, pooling.md
    scripts/       health_check.py, probe_test.py
    backup.sh, restore.sh, alembic.ini, requirements.txt, .env.example (placeholders)
  storage/         Local file storage + integrity helper
    raw/{psx-dps,psxdata,pdf}, processed, financial_reports, parquet,
    research_reports, backups/, manifests/, quarantine/, tmp/
    storage_helper.py, test_storage_helper.py, size_report.sh
  workers/         Celery 5.6.3 + Redis 7.0.15 (self-hosted)
    celery_app.py, tasks.py, healthcheck.py, dev_fallback.py,
    requirements.txt, requirements-dev.txt (pytest, coordinator fix),
    tests/ (eager + dev-fallback tests, run from repo root)
    tasks/, schedulers/, monitoring/ — documented placeholders (READMEs)
  shared/schemas/  provenance.schema.json (draft Phase 1 §5 contract)
  scripts/         check_env.sh, dev.sh, healthcheck.sh, stop_dev.sh,
                   run_worker.sh, run_celery_proof.sh
  deployment/      docker-compose.yml, Dockerfile.backend/frontend/worker,
                   .env.example (placeholders) — DEFINITION ONLY, not verified
                   running (see DOCKER_SETUP.md blocker D-05)
  monitoring/      documented placeholder (README)
  tests/           documented placeholder (README); team tests live with
                   their components (backend/tests, frontend/tests,
                   workers/tests, storage/test_storage_helper.py)
  docs/
    phase-01/      Phase 1 specification set (67 files, accepted checkpoint)
    phase-02/      This Phase 2 set (see below)
    development/   Execution state, log, defect register, push log,
                   live test report, technical debt, account register
  .github/workflows/  ci.yml (env check + secrets-sanity only),
                      workers.yml (eager tests + live-broker job, not run in CI yet)
```

## Phase 2 docs in docs/phase-02/

ENVIRONMENT_AUDIT.md, COMPATIBILITY_REPORT.md, LICENSE_REGISTER.md,
FRONTEND_SETUP.md, BACKEND_SETUP.md, DATABASE_SETUP.md, STORAGE_SETUP.md,
REDIS_SETUP.md, DOCKER_SETUP.md, LOCAL_DEVELOPMENT_GUIDE.md,
REPOSITORY_STRUCTURE.md (this file), TESTING_GUIDE.md,
SECURITY_FOUNDATION.md, TROUBLESHOOTING.md, PHASE_2_TEST_REPORT.md,
PHASE_2_AUDIT_REPORT.md, PHASE_2_ACCEPTANCE_REPORT.md.

## Rules that apply to this tree

- No file in this tree contains a real secret, password, token, or
  credential. Real credentials live only in gitignored `.env` files
  (backend/.env is not present; database/.env mode 0600, gitignored).
- No Phase 3 schema exists here: the only database table created by a
  migration is `phase2_probe` (+ Alembic's `alembic_version`).
- No fabricated PSX data exists here: frontend routes are labelled
  foundation shells with empty states; probe/demo rows and files are
  labelled TEST / NOT PSX DATA.
- Virtualenvs (backend/.venv, database/.venv, workers/.venv),
  node_modules, .next, and storage data are gitignored and are NOT
  part of the pushed tree.
- `storage/backups/` contains two verified Phase 2 backups (see
  DATABASE_SETUP.md). Backups are local evidence, not production data.
