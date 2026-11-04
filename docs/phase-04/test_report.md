# Phase 4 — Test Report

Date: 2026-11-04 (Asia/Karachi). All counts below are from runs
actually executed in this phase, not copied from earlier phases.

## Pytest suite (offline, no real PostgreSQL, no network)

Command: `backend/.venv/bin/python -m pytest tests/ -q`
Result after audit fixes: **44 passed, 0 failed, 1 warning** (the
Phase 2 Starlette deprecation warning, non-blocking). Before the
audit fix pass the count was 36 passed (18 Phase 4 + 18 Phase 2);
the fix pass added 8 Phase 4 tests and fixed 1 pre-existing
registry test (official-source rule, audit H1).

Breakdown (final):
- Phase 4 registry tests (`tests/test_registry.py`): **26 passed**
  - Normalization: 4 (ticker upper/strip, ticker empty rejection,
    name suffix handling, ISIN format validation).
  - Matching: 5 (ticker+name unique, ticker alone insufficient,
    ISIN wins, multiple candidates ambiguous, no-match for new).
  - Importer: 7 (create + idempotent, never verifies on success,
    second source -> PARTIALLY_VERIFIED, official source ->
    VERIFIED, ambiguous not merged, bad ticker/ISIN rejected,
    rename not merged on name alone).
  - Reconciliation: 2 (no snapshot -> no coverage claim;
    missing/extra/coverage 0.5 on a fixture snapshot).
- Phase 2 suite re-run (`test_endpoints.py`,
  `test_errors_and_config.py`): **18 passed** (unchanged).

Ruff: `ruff check` on all Phase 4 backend files + tests: **clean**
(10 findings found during the run were fixed: unused imports,
long lines, and the unused-variable case — see defect register).

## Live-PostgreSQL check (rolled back)

Script: `scripts/run_phase4_pg_check.py` (NOT a pytest test).
Result: **PHASE4_PG_CHECK_OK**.
- Import of 2 TEST ONLY records: companies_created=2,
  securities_created=2; re-import skipped_as_duplicate=2.
- Adversarial paths (added after audit recommendation 4, same
  rolled-back transaction): conflicting ISIN import ->
  conflicts=1, security CONFLICTED, stored ISIN unchanged;
  ambiguous record -> pending_review=1; ambiguous re-import ->
  quality-report count unchanged (de-duplicated).
- Reconcile with no snapshot: registry_tickers=2 (in
  transaction), coverage=None (no claim).
- Transaction ROLLED BACK: live database retains 0 business rows
  (verified by the API statistics call after rollback).
- API smoke test against the live (empty) database via
  TestClient: /companies, /securities, /sectors,
  /registry/statistics, /registry/quality, /registry/sources
  all 200; /companies/999999 and /securities/999999 both 404;
  /companies?limit=999 returned 422; statistics returned
  companies=0, securities=0.

## Live backend check (port 8003, uvicorn)

- /api/v1/registry/statistics -> 200, companies=0,
  securities=0, sectors=0, evidence_rows=0.
- /api/v1/companies -> 200, total=0, items=[].
- /api/v1/health -> 200.
- Server stopped after the check (port 8003 confirmed stopped;
  port 8000 was already running from earlier phase work and was
  left untouched).

## Frontend checks

- `npm run typecheck`: pass. `npm run lint`: pass.
  `npm run build`: pass (routes incl. /companies build).
- Frontend Vitest suite re-run in this phase: **3 test files,
  11 tests, all passed** (same count as Phase 2, re-run, not
  copied).

## Tests NOT run / NOT claimed

- Docker containers: not run (carried forward from Phase 2).
- Playwright E2E: not run (carried forward from Phase 2).
- CI in CI: not run (no push yet).
- Live DPS/PSX collection: attempted and FAILED (see
  source_research.md) — recorded as a blocker, not as a pass.
- A browser-rendered screenshot of /companies: not obtained
  (generic subagent, no live browser).
