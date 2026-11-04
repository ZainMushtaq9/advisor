# Phase 10 — Implementation specification

## 11-stage workflow (summary)

1. **Brainstorm:** macro context for a 3-company, 1-price-date system must
   be descriptive, not predictive; the value is dating, sourcing and
   vintage discipline, not indicator count.
2. **Research:** SBP MPS 2026-10-26 and PBS homepage read directly;
   press used only as H1 second sources and for press-keyed events.
3. **Validate:** every stored value cross-checked against the source
   text it came from (see run report audit table).
4. **Data inspection:** Phase 7 statement lines inspected for exposure
   evidence (finance costs, FX lines, borrowings, interest income).
5. **Architecture:** reuse Phase 3 tables where they exist
   (`economic_indicators`, `sector_metric_profiles`); add only the
   three tables Phase 10 needs (migration 20261104_0007).
6. **Implementation spec:** this document + the registry.
7. **Documentation:** six docs under `docs/phase-10/`.
8. **Testing strategy:** pure unit tests (no DB, no network) for
   point-in-time and revision rules; live CLI runs for idempotency;
   live API smoke tests; in-transaction revision proof on the live
   table (rolled back, zero rows left).
9. **Independent audit:** source-text audit table in the run report;
   one audit fix applied (see below).
10. **Correction:** `point_in_time` now ignores non-current rows itself
    instead of trusting the caller (test found it, function fixed).
11. **Checkpoint:** this report; Phase 10 verdict PARTIALLY COMPLETE.

## Tables

| Table | Grain / discipline |
|---|---|
| `economic_indicators` (Phase 3, reused) | `(indicator_code, observation_date, version_number)`; versioned trigger (only `is_current` flips); quality CHECK. |
| `company_macro_exposures` (new, 0007) | `(company_id, exposure_key, version_number)`; versioned trigger; quality CHECK; evidence mandatory. |
| `macro_regimes` (new, 0007) | `(observation_date, regime_label, method_version)`; immutable trigger; evidence JSON. |
| `macro_events` (new, 0007) | `(event_date, event_type, title)`; immutable trigger. |
| `sector_metric_profiles` (Phase 3, reused) | `(sector_id, metric_key)` with `metric_key = "macro:<indicator>"`. |

## Point-in-time rule

`availability_date = source_timestamp` (publication date) when the
publisher states one, else `collected_at` (the earliest date the value
is provably public). `point_in_time(indicator, as_of)` returns the
latest current observation with `availability_date <= as_of`, or an
explicit absence. Proven live: policy rate absent at 2026-10-25 and
known (12.00) at 2026-10-27; CPI MoM absent at 2026-11-01 and known
(1.10) at 2026-11-02.

## Revision rule

A revision inserts a new row (`version_number + 1`, `supersedes_id`
set) and flips the old row's `is_current` to false. Stored values are
never edited: the trigger raises
"table economic_indicators is versioned: only is_current may change;
figures require a new version row" on any other update. Proven live in
a rolled-back transaction (v1 1.10 preserved, v2 1.20 current, value
edit rejected, zero scratch rows left).

## Engine

- `backend/app/services/macro_analysis/__init__.py` — registries and
  collected data (indicators, observations, cross-checks, exposures,
  sector profiles, regime assessment, events, not-stored gaps).
- `formulas.py` — pure point-in-time + revision helpers.
- `runner.py` — idempotent seeding (dry-run default, `--commit`).
- `scripts/run_macro_analysis.py` — CLI (exit 0/1/2, JSON on stdout).
- `backend/app/api/v1/endpoints/macro.py` — GET-only endpoints
  (`/macro`, `/macro/point-in-time`, `/macro/regimes`,
  `/macro/exposures`, `/macro/events`, `/macro/sectors`).
- `backend/app/models/macro.py` — the three new tables.
- `backend/tests/test_macro_analysis_phase10.py` — 17 pure tests.

## What Phase 10 does NOT do

- No forecasting (Phase 13 owns it). SBP projections and the IMF
  forecast appear only in regime evidence marked FORECAST.
- No investment advice or buy/sell signals (Phase 15 owns proposals).
- No VERIFIED promotion of any Phase 7/8/9 row; macro outputs carry
  the lowest input quality and never exceed it.
- No FRED use (gate G-06).
- No new PSX market-data collection (Terms gate untouched).
