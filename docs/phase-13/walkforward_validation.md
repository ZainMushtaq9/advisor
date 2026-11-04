# Phase 13 — Walk-forward validation

## Fold construction

Expanding window, chronological, never shuffled. Fold k trains on
`series[:origin]` with `origin >= min_train` and evaluates on the
next `horizon_steps` values; origins increase by `step`. A series
that yields no fold raises instead of returning an empty result
("no evidence" is never silently returned as a pass).

## Metrics (per method, per series)

- **MAE / RMSE** — from per-fold forecast vs realised pairs, all
  stored in the evaluation result so an auditor can recompute them.
- **Directional accuracy** — forecast direction vs realised
  direction, both measured against the origin value. Folds with a
  zero realised move are excluded from the denominator (reported as
  None when no fold has a non-zero move), never counted as misses.
- **Interval coverage (PICP)** — fraction of realised values inside
  their forecast intervals.
- **Calibration error** — |nominal − empirical| coverage gap for
  the evaluated interval level (80% in this implementation). With a
  single level this is one number, reported as such — never dressed
  up as a calibration curve.

## Leakage rules enforced

1. Train windows end strictly before the forecast origin; test
   values start strictly after it.
2. The historical-mean residual uses the expanding prior mean, not
   the full-sample mean (which would leak the evaluated value).
3. No future price, later disclosure, revision, corporate action
   or target-window overlap is used: the runner only reads rows
   dated on or before the origin.
4. Performance is reported by security, horizon and regime when
   evaluations exist. None exist yet: with no forecast, there is
   nothing to evaluate, and the pipeline reports that instead of
   inventing a backtest.

## Current evaluation status

Not evaluated (no forecasts, no folds possible on series of length
0–2 with the methods' minima). The validator is fully implemented
and tested on fixtures; it runs on production series the day a
series meets a method's minimum.
