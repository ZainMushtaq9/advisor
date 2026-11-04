# Phase 5 — Test Report

Date: 2026-11-04 (Asia/Karachi). Branch: `phase-05-snapshot-import`.
Runner: `backend/.venv/bin/python -m pytest` (system python has
no pytest; the project venv is the runner — recorded here so
the count is reproducible).

## 1. Results (independently re-run by the coordinator)

| Suite | Result |
|---|---|
| New market tests (`test_market_data.py`, `test_market_api.py`) | **41 passed** |
| Pre-existing backend tests | **44 passed** |
| Full backend suite | **85 passed, 0 failed** |
| Backend Ruff (new/changed files, coordinator re-run) | clean |
| Frontend typecheck (after nav edit, coordinator re-run) | clean |
| Frontend lint (`lib/nav.ts`, `app/market/*`, coordinator re-run) | clean |
| Frontend `next build` with `/market` in routes (implementer run) | succeeds |

Correction to the implementer's report (audit A1): the
implementer reported "42 new / 43 pre-existing". The verified
split is **41 new / 44 pre-existing** (41 tests collected from
the two new files; 44 from the pre-existing files; 22 test
functions in the new files expand to 41 cases via
parametrization). The total — 85 passed — is unchanged and
was re-verified by the coordinator. No test was added or
removed to force the split.

## 2. What the 41 new tests cover

- Validation: every rejection code (missing_field,
  unknown_ticker, unparseable_date, unparseable_number,
  non_positive_price, negative_volume, negative_turnover,
  ohlc_inconsistency, future_trading_date vs Asia/Karachi
  today), blank turnover/previous_close/source_timestamp =
  absent (never zero).
- Quality: single source → UNVERIFIED; two agreeing →
  PARTIALLY_VERIFIED; official + agreeing → VERIFIED;
  disagreeing → both CONFLICTED (same run and cross-run
  side-by-side); stale 30/31-day boundary.
- Ingestion: idempotent re-ingest (second run skips all);
  catch-up ingests only missing dates; missing-session
  reporting with no zero rows; header validation before any
  DB work; unknown-ticker fail-fast before any write.
- API: empty-market states (counts 0 + scope note, never
  404/fabricated rows); unknown-ticker `/latest` → 404;
  unavailable state when DATABASE_URL is unset (503).
- All test prices are labelled TEST ONLY and live in tests
  only; no test writes to the production database.

## 3. CLI smoke test (throwaway SQLite, TEST ONLY)

Dry-run reported ingested=2 with the DB unchanged;
`--commit` ingested 2; re-commit skipped 2; unknown-ticker
`--commit` aborted exit 2 with no write; bad header aborted
before DB work; catch-up filtered 2 already-stored rows and
reported the remaining missing date. Production was not
touched: production `market_prices` verified 0 after all runs
(direct read, coordinator).

## 4. What was NOT tested (honest gaps)

- No live-market test: no live adapter exists and none was
  called; a live test would require the blocked route.
- No PostgreSQL end-to-end ingest run: the CLI smoke test
  used SQLite fixtures (see coverage limitation A5 on id
  generation). The shipped CLI is written for PostgreSQL
  (ids generate normally there); the first production ingest
  must be run `--dry-run` first and its report checked
  before any `--commit`.
- No load/performance test: with 0 production observations,
  a performance claim would be meaningless. Performance
  testing belongs to the first real backfill, not this phase.
