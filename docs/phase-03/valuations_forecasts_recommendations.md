# Phase 3 — Valuations, Forecasts, Recommendations

## Valuations (versioned)

Method, inputs (statement ids + price ids, by id — never 'latest
at the time' prose), assumptions, sensitivity, value range
(value_low/value_high), model_version_id. A valuation whose
inputs cannot be named is not a Phase 3 valuation. No method is
privileged by the schema: dcf, multiples, dividend, asset_based
and residual_income are all method strings with their assumptions
stored alongside.

## Forecasts (versioned, probabilistic by design)

Point estimate + interval_low + interval_high + uncertainty
(NOT NULL) + bear/base/bull scenarios + probabilities where
calibrated + horizon (1d/1w/1m/3m/6m/12m) + model_version_id +
feature_snapshot_ref + assumptions. A forecast row without
uncertainty fields is invalid by schema, with one documented
exception only: a method that genuinely cannot produce intervals
must flag that, not silently present a point forecast.

forecast_evaluations (append-only): one row per forecast x
evaluation date x metric, referencing the exact forecast row and
the realised value's provenance. This is how forecast quality is
answered from data, not from memory.

## Recommendations (versioned, probabilistic, audited)

Signal (BUY/HOLD/SELL/WATCHLIST — a probabilistic proposal, never
a guarantee), confidence/probability, evidence links (forecasts,
valuations, ratios as JSON references), validity window, status
(active/superseded/expired). No guarantee language in any column
or value list. Recommendations are stored separately from the
signal events of Phase 6 and the decision engine of later phases;
Phase 3 provides the table, not the decision.

## What is NOT here

No price targets are computed in Phase 3, no forecast is run,
and no recommendation is issued. These tables hold zero rows at
the end of Phase 3. Their consumers are Phases 9+ and the
forecasting phases; Phase 3's job is that when they run, their
outputs land in versioned, auditable, uncertainty-carrying rows.
