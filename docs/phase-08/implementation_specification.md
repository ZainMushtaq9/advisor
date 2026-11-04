# Phase 8 — Implementation specification

## Entry dependency

Phase 7 statements for 3 companies (3 documents, 88 statements,
1,316 line items, 3 auditor-opinion rows — all UNVERIFIED) plus the
Phase 4 registry for sectors. Phase 5 prices (444 rows, one day)
and Phase 6 indicators (0 calculable) do not feed Phase 8 except as
the documented reason market multiples are NOT_CALCULABLE.

Configured company-periods (see `conventions.py` PERIODS):

| Company | Period | Basis |
|---|---|---|
| HUBC (289) | FY2026 annual, audited, consolidated | Flow 2025-07-01→2026-06-30; BS 2026-06-30 vs 2025-06-30; 365 days |
| NML (394) | Nine months to 31 Mar 2025, unaudited, consolidated | Flow 2024-07-01→2025-03-31; BS 2025-03-31 vs 2024-06-30; 274 days |
| OGDC (403) | Six months to 31 Dec 2025, unaudited, consolidated | Flow 2025-07-01→2025-12-31; BS 2025-12-31 vs 2025-06-30; 184 days |

HBL (277, Habib Bank Limited) is PENDING: its CY2025 statements are
not loaded (PDF blocked at download; live-browser download runs
separately). Adding it later means one PERIODS entry + one KEY_MAP
entry; no redesign. Until then it has no ratios, no health row, no
warning row, and no sector profile.

## Components

| Component | Location |
|---|---|
| Metric registry v1.0, period config, key maps | `backend/app/services/fundamental_analysis/__init__.py` |
| Pure Decimal formulas (None = NOT_CALCULABLE) | `.../formulas.py` |
| Calculability assessment (36 metrics) | `.../coverage.py` |
| Health-v1 scoring | `.../health.py` |
| Review flags | `.../warnings.py` |
| DB load + idempotent writes | `.../runner.py` |
| CLI (dry-run default, --commit) | `scripts/run_fundamental_analysis.py` |
| GET-only API | `backend/app/api/v1/endpoints/fundamentals.py` |
| Tests (pure + endpoint 503) | `backend/tests/test_fundamental_analysis_phase08.py` |

## Storage (existing Phase 3 tables — no new migration)

- `fundamental_metric_definitions` — seeded idempotently by
  metric_key (formula_version 1.0).
- `fundamental_metric_values` — one row per (company, metric,
  period_end, 1.0); value NULL = NOT_CALCULABLE;
  computation_status computed / insufficient_inputs /
  not_applicable; input_statement_ids lists the exact statement
  versions used; quality_status UNVERIFIED.
- `financial_health_assessments` — one row per (company,
  period_end, category, health-v1); score NULL = insufficient data;
  evidence JSON carries sub-scores, bands, and the disclaimer.
- `fundamental_warning_events` — one row per (company, event_date,
  warning_type); evidence carries values + the review-only note.
- `sector_metric_profiles` — one row per (sector, metric_key) for
  the three computed sectors.

Idempotency: a second `--commit` writes 0 new rows (every write is
guarded by an existence check on its grain). Corrections require a
new calculation_version; no row is ever updated or deleted.

## Verification performed

- Backend suite: 147 passed (140 prior + 7 new), 0 failed.
- Ruff check + format clean on all new/changed files.
- Live dry-run reconciled against an independent precomputation:
  60 ratio values agree exactly; 7 days values agree within 0.001
  (the precomputation's intermediate 6-decimal quantisation, not an
  engine error — the engine carries full Decimal precision).
- Live API checks: ratios 200 (36 metrics), health 200, HBL
  pending 200, unknown ticker 404, sector-profiles 200 (empty until
  commit, with an explanatory note).

## What Phase 8 does not do

- No TTM synthesis, no annualisation, no zero-filling, no
  estimation, no VERIFIED promotion (all outputs UNVERIFIED).
- No market multiples (see the ratio dictionary for exact reasons).
- No ROIC (no validated NOPAT tax allocation).
- No buy/sell language anywhere: health scores are descriptive
  only, and no single aggregate grade is produced.
- No new PSX market-data collection, no DPS downloads, no PSX
  financials-portal use, no Docker, no merge to main.
