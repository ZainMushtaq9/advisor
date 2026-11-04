# Phase 13 — Baseline methodology

Baselines first, complex models only on out-of-sample evidence —
per the brief. All baselines are pure Decimal functions in
`baselines.py`, tested on hand-calculated fixtures.

## Methods

- **naive_persistence** (random walk): next value = last value.
  Point needs 1 observation; interval needs 11 (1 origin + 10
  one-step residuals).
- **historical_mean**: mean of the whole series. Point needs 5 —
  fewer makes the "average" a single observation in disguise.
- **moving_average_5 / _20**: mean of the last 5 / 20 observations.
- **ar1**: OLS fit of value[t] on value[t-1]; iterated for
  multi-step horizons. Point needs 30 — a slope fitted on fewer
  points is noise presented as signal. Refuses on zero-variance
  regressors.
- **ets / arima / ml_tree**: registered candidates, NOT implemented.
  No statsmodels dependency is added for a pipeline that owns one
  price date. ML additionally requires out-of-sample evidence of
  incremental value over baselines (brief rule); none can exist on
  one observation.

## Intervals (no normality assumed)

Prediction intervals are empirical: point + the 10th/90th
percentile of in-sample one-step residuals (linear-interpolation
quantiles). Fewer than 10 residuals → the function refuses rather
than returning a guessed interval. This is the rule that forces
abstention in this run: naive persistence CAN name a point from
one observation (e.g. HUBC 197.24), but a point without a validated
interval is not a Phase 13 forecast, so it is recorded as
`point_only_abstained` in the assessment evidence and never stored
as a forecast row.

## What a stored forecast must carry (when one exists)

Method, horizon, origin date, inputs with as-of dates, point
estimate ONLY inside an interval/uncertainty statement, baseline
comparison, and calibration status. None exists yet; the assessment
rows record exactly which of these is missing and why.
