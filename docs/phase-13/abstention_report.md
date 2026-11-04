# Phase 13 — Abstention report (production run, 2026-11-04)

## Verdict for live forecasting: ABSTAINED (all targets, all horizons)

120 assessment rows were written, 0 computed, 120
`insufficient_inputs`. This is the brief-compliant outcome, not a
missing run: the brief requires distributions/intervals "where
validated, not only point estimates" and requires abstention "where
confidence is poor". Confidence from 0–2 observations is nil.

## Per-target evidence (series lengths read from the database)

| Target | HUBC | NML | OGDC | Macro | Shortest interval shortfall |
|---|---|---|---|---|---|
| close_price | 1 | 1 | 1 | — | 10 (naive needs 11) |
| return | 0 | 0 | 0 | — | 11 |
| direction | 0 | 0 | 0 | — | 11 |
| volatility | 0 | 0 | 0 | — | 11 |
| volume | 1 | 1 | 1 | — | 10 |
| earnings | 2 | 2 | 2 | — | 9 |
| macro_policy_rate | — | — | — | 1 | 10 |
| macro_cpi_yoy | — | — | — | 1 | 10 |

Naive persistence could name a point for close_price, volume,
earnings and both macro targets (series >= 1), but its interval
needs 10 residuals it does not have. Those methods are recorded as
`point_only_abstained` in each assessment's evidence — visible,
auditable, and never served as forecasts.

## What was NOT done (and why it would have been wrong)

- No price series was invented, interpolated or borrowed from
  another source to make a model run.
- No point estimate was stored without an interval (the Phase 3
  `forecasts` table's NOT NULL interval columns enforce this at
  the schema level; Phase 13 respects it by writing 0 rows there).
- No backtest was fabricated: walk-forward evaluation needs folds,
  and no series yields one at the methods' minima.
- No guaranteed-return or directional claim is made anywhere.

## Exact unblockers (in order of impact)

1. **More trading days of price data** — the Phase 5 Terms gate.
   10 more trading days (11 closes) unlock naive intervals for
   close_price/volume; 30 closes unlock AR(1); 50+ unlock ARIMA
   candidacy. Each new trading day also adds one return/direction/
   volatility observation.
2. **More statement periods** — Phase 7 expansion. Each new income
   period adds one earnings observation per company.
3. **More macro vintages** — SBP/PBS monthly releases. Each new
   policy-rate or CPI observation extends those series by one.
4. **HBL statements** — the separate live-browser HBL download,
   then a Phase 7 load, then a Phase 13 re-run (adds HBL's 36
   assessments + snapshots without redesign).
5. **VERIFIED promotion** — H1 second agreeing source including an
   official source; everything stays UNVERIFIED until then.
