# Phase 13 — Implementation specification

## Brief source

Playbook extract `~/workspace/psx-playbook/psx_playbook.txt`, lines 1084–1142
(Phase 13, Forecasting and Predictive Analytics Engine).

## What was built

| Piece | Location |
|---|---|
| Target registry + method minima | `backend/app/services/forecasting/__init__.py` |
| Baselines (naive, mean, MA, AR(1), intervals) | `backend/app/services/forecasting/baselines.py` |
| Walk-forward validation + metrics | `backend/app/services/forecasting/validation.py` |
| Computability assessment | `backend/app/services/forecasting/coverage.py` |
| DB runner (registry, feature store, assessments) | `backend/app/services/forecasting/runner.py` |
| CLI | `scripts/run_forecasting.py` (`--dry-run` default / `--commit`) |
| GET-only API | `backend/app/api/v1/endpoints/forecasting.py` |
| Models + migration 0010 | `backend/app/models/forecasting.py`, `database/migrations/versions/20261104_0010_phase_13_forecasting.py` |
| Tests (pure, hand-calculated) | `backend/tests/test_forecasting_phase13.py` |

## Tables (new, migration 0010)

- `forecast_targets` — 48 rows: 8 targets x 6 horizons, with
  `method_requirements` JSON (per-method point/interval minima).
- `forecast_feature_snapshots` — 116 rows: per-company snapshots of
  stored Phase 8/9 values + price close/volume as of 2026-11-03,
  plus all 12 current Phase 10 macro observations as of 2026-11-04.
- `forecast_assessments` — 120 rows: one per (security, target,
  horizon), all `insufficient_inputs`, with per-method breakdown,
  baseline comparison (`none_available`) and calibration status
  (`not_calibrated_insufficient_history`) in evidence JSON.

## Deliberate non-reuse

The Phase 3 `forecasts` table requires NOT NULL `interval_low`,
`interval_high` and `uncertainty`. No interval is validatable from
one trading date, so Phase 13 writes ZERO rows there (and zero to
`forecast_evaluations`). This mirrors Phase 11 (news tables beside
Phase 3 `news`) and Phase 12 (`corporate_action_records` beside
Phase 3 `corporate_actions`). The table stays empty until a series
long enough to validate an interval exists.

## Scope decision

Analysis universe = HUBC, NML, OGDC (the statement companies), the
same scope as Phases 8–12. HBL has a price row but no statements:
its assessments are pending the Phase 7 load (recorded as a pending
note, not as rows). Assessing all 444 priced securities would add
15,984 identical abstention rows without information. Re-running the
script after a Phase 7 expansion adds companies without redesign.

## Leakage prevention

- The runner reads only rows dated on or before the origin
  (2026-11-03 prices; statement period ends; macro observation dates).
- Walk-forward folds are expanding-window and chronological; the
  series is never shuffled. `one_step_residuals` for the mean method
  uses the expanding prior mean, never the full-sample mean.
- No future price, later disclosure, revision, corporate action or
  target-window overlap can enter a forecast: there is no future
  data in the store at all (the single price date IS the origin).

## Status

PARTIALLY COMPLETE. Framework, feature store, assessments, API and
tests are complete and verified; live forecasting is abstained
because no target series meets any method's interval minimum.
See `abstention_report.md` for the per-target evidence.
