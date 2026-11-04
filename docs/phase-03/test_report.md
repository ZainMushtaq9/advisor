# Phase 3 — Test Report

Date: 2026-11-04. All results below are from tests actually run
on this VM by the coordinator. Nothing is copied from a team
report without a re-run, except where a row says so. Test data is
labelled TEST ONLY and, for PostgreSQL tests, lives inside a
transaction that is rolled back at the end — no TEST row survives
in the production database (verified: production business tables
hold zero rows at phase end; the only pre-existing row-bearing
table is the Phase 2 probe, untouched).

## Suite totals (final run, after audit fixes)

- `database/tests/test_phase3_schema.py` — 10 passed
  (metadata + pure-logic; no database, by design — see below).
- `database/tests/test_phase3_postgres.py` — 16 passed
  (PostgreSQL behaviour in a rolled-back transaction, including
  6 audit-regression tests: H1 statement CHECK, H2 resolution
  trigger, H3 NULL-source rejection, M3 document-version trigger,
  M4 marker/immutable triggers, M6 announcement hash uniqueness).
- `backend/tests/` (Phase 2 suite, re-run) — 18 passed.
- `storage/test_phase3_engine.py` — 9 passed (including 3
  audit-L5 regressions: quarantine same-basename, manifest
  overwrite rejection, byte_size verification).
- **Total: 53 passed, 0 failed, 1 warning** (Starlette
  deprecation warning from Phase 2, non-blocking). Pre-fix total
  was 44 passed; the 9 new tests are the audit regressions above.
- Ruff (from `backend/`, where its pyproject lives): all checks
  passed on models, data_quality service, Phase 3 tests and
  storage engine. Note: running ruff from the repo root gives a
  different, misleading error count because its config is not
  discovered there — the backend/ run is the authoritative one.
- Live database at final run: alembic head `20261104_0004`,
  56 public tables, 23 triggers, 22 quality CHECK constraints
  (verified by query, not just by migration text).

## Why there is no SQLite schema test

An early Phase 3 draft ran model tests on SQLite in-memory.
SQLite cannot generate PostgreSQL Identity columns on BIGINT
primary keys (NOT NULL id failure on insert). Rather than
weaken the models to suit SQLite, the schema tests were moved to
PostgreSQL (the real target) and the SQLite file was rewritten
to metadata + pure-logic tests only. This failure and its fix
are recorded in the defect register.

## 28 test areas

| # | Area | Evidence |
|---|---|---|
| 1 | Schema completeness | 54 model tables asserted; 56 public tables in PG |
| 2 | Migration up | upgrade head -> 20261104_0003, exit 0 |
| 3 | Migration down | downgrade base -> exit 0 (after two fixed downgrade defects) |
| 4 | Fresh down/up cycle | Phase 2 cycle re-run (gate) + Phase 3 cycle, both exit 0 |
| 5 | FK integrity | Models + migration; insert paths exercised in PG tests |
| 6 | Unique grains | market_prices duplicate rejected (PG test) |
| 7 | Versioning | New version row + supersedes_id + is_current flip; figure edit rejected by trigger |
| 8 | Provenance | Columns present on all market/financial/news/analysis models; collection vs source time documented and separated |
| 9 | Quality CHECK constraints | BOGUS_STATUS rejected by PG CHECK (PG test) |
| 10 | Quality upgrade rule | Upgrade without evidence raises ValueError (unit test) |
| 11 | Immutability triggers | UPDATE and DELETE on market_prices rejected by trigger (PG test, DBAPIError) |
| 12 | Versioned trigger scope | Only is_current may change on 7 versioned tables (PG test) |
| 13 | Duplicate detection | Hash/URL key helper + unique grains + dividend 1:1 (unit + schema tests) |
| 14 | OHLC validation | Valid/invalid/missing/negative cases (unit test) |
| 15 | Balance-sheet identity | Pass/fail + tolerance + missing-input cases (unit test) |
| 16 | Cash-flow identity | Pass case + missing-input case (unit test) |
| 17 | Conflict side-by-side | Two sources, two rows, CONFLICTED, values_conflict true (PG test) |
| 18 | Missing != zero | NULL close/volume preserved, never 0 (PG test) |
| 19 | Forecast uncertainty | interval_low/high + uncertainty NOT NULL asserted on model metadata |
| 20 | Paper portfolios only | No broker/api_key/password/secret columns (metadata test) |
| 21 | Agent logs, no secrets | Same column test; references-only design documented |
| 22 | Macro revision preservation | economic_indicators grain includes version_number; zero rows by gate (G-01) |
| 23 | News/research hashes | document_hash/content_hash columns present; no PDF-bytes columns (metadata test) |
| 24 | Storage integrity | Phase 2 helper re-run via Phase 3 engine tests: manifest verify, tamper detection, quarantine, dry-run prune |
| 25 | Parquet guard | pyarrow absent -> RuntimeError, no fake file (storage test) |
| 26 | Backup/restore | Backups 2026-11-04T1217-PKT (head 0003) and 2026-11-04T1230-PKT (head 0004), both SHAs MATCHED on re-hash, restore VERIFIED to separate DB each time (row-count gate 0=0; 2 known harmless pg_restore warnings). Post-fix backup/restore was re-run by the coordinator after migration 0004; an independent re-run is covered in the completion report (verification agent). |
| 27 | Performance / scalability | Bulk insert 10,000 rows 0.49s; count query 0.014s; full suite 2.69s. No KSE-100/registry-scale claim (no such data exists) |
| 28 | Backend integration | Phase 2 endpoints re-verified live (:8002 health ok, version 0.1.0, Python 3.12.3); backend suite 18 passed |

## Not run / not claimed

- Docker build/run: UNVERIFIED (Phase 2 environment blocker,
  carried forward; definition-only).
- Playwright E2E: NOT RUN (browser download failure, Phase 2,
  carried forward).
- Frontend live routes: unchanged from Phase 2; Phase 2 route
  checks stand, not re-claimed as Phase 3 evidence.
- CI in CI: not run (no push before audit).
- Any PSX data test: none exists, because no PSX data was
  collected in Phase 3. Every 'row' in every test is TEST ONLY.
