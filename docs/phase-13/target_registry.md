# Phase 13 — Forecast target registry

8 targets x 6 horizons (1d, 1w, 1m, 3m, 6m, 12m) = 48 rows.
Horizon does not change computability: the minima are properties
of the series, not of how far ahead the forecast looks.

## Company targets (scope: company; origin 2026-11-03)

| Target | Series definition | Series length in this run |
|---|---|---|
| close_price | Daily `close_price` values, oldest first | 1 (one trading date) |
| return | Simple returns from consecutive closes | 0 (no consecutive pair) |
| direction | Up/down signs from consecutive closes | 0 |
| volatility | Realised volatility from consecutive closes | 0 |
| volume | Daily `volume` values | 1 |
| earnings | Distinct income-statement period ends (current + prior-year comparative, both stored by Phase 7) | 2 per company |

## Macro targets (scope: macro; origin 2026-11-04; security NULL)

| Target | Series definition | Series length in this run |
|---|---|---|
| macro_policy_rate | `sbp_policy_rate` observation dates (current rows) | 1 (2026-10-27) |
| macro_cpi_yoy | `cpi_yoy` observation dates (current rows) | 1 (2026-09-30) |

## Method minima (see baseline_methodology.md)

| Method | Point min | Interval min | Implemented |
|---|---|---|---|
| naive_persistence | 1 | 11 | yes |
| historical_mean | 5 | 15 | yes |
| moving_average_5 | 5 | 15 | yes |
| moving_average_20 | 20 | 30 | yes |
| ar1 | 30 | 40 | yes |
| ets | 30 | 40 | no — candidate only |
| arima | 50 | 60 | no — candidate only |
| ml_tree | 100 | 110 | no — gated on out-of-sample evidence |

Interval minimum = point minimum + 10 in-sample one-step residuals.
No target in this run meets any interval minimum, so no forecast
is computed for any target at any horizon.
