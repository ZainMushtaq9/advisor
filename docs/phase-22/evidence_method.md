# Phase 22 — Evidence Method

## Figure kinds

| Kind | Meaning | May be computed? |
|---|---|---|
| sourced_fact | A stored row reproduced (close, volume, date, count) | Yes |
| deterministic_calculation | A pure recomputation from stored rows (sum, ratio, count) | Yes |
| model_output | A Phase 8–21 model row reproduced (health, valuation, risk, decision) | Yes |
| analyst_inference | A judgement sentence grounded in stored rows (thesis text) | Never — an inference is not a computed value |
| assumption | A stated input (hypothetical capital) | Yes (the assumption itself, not a result) |

## Computation statuses

- `computed`: exactly one value form is present.
- `insufficient_inputs`: the inputs do not exist or do not
  meet the method's minimum; no value is carried, and the
  reason is in the figure's source note.
- `not_applicable`: the method does not apply to the subject
  by structure (e.g. bank residual-income for an industrial;
  OGDC interest coverage, which has no finance-cost line).

## Cut-off and no-look-ahead

- Report date = data cut-off = 2026-11-04. No stored row
  postdates the cut-off except SCHEDULED future events,
  which appear only as scheduled items with a `scheduled`
  warning, never as occurred.
- Price date 2026-11-03 is the single trading date with
  stored prices. No price after that date is used, because
  none is stored.
- Statement publication dates are respected: HUBC
  2026-09-21 and OGDC 2026-02-23 are on/before the decision
  date; NML's publication date is NULL and is reported as
  unknown, never guessed, and gates its Phase 15 conclusion.

## Stale and missing rules

- Stale threshold: 365 days (Phase 14's threshold). A
  latest period end more than 365 days before the cut-off
  yields a `stale` warning. NML (latest period end
  2025-03-31, 583 days) is stale; HUBC (127 days) and OGDC
  (308 days) are not.
- Missing data yields a `missing` warning plus an
  insufficient_inputs figure, never a zero or an estimate.
- Conflicting evidence is preserved side by side: Phase 15
  conflicts are listed in the counter-thesis, never averaged
  away; the OGDC cash-flow 1-thousand source defect is
  recorded in Phase 7 and never adjusted here.

## What is NOT_CALCULABLE, and why

| Output | Reason |
|---|---|
| Portfolio return | Zero return observations from one price date |
| Volatility, beta, correlation, downside deviation, VaR95/ES95, drawdown, gap risk | Series warm-ups unmet (30/251 observations); previous_close NULL on all 444 rows |
| Turnover liquidity | Turnover NULL on all rows |
| Sector volume HHI | Per-sector volume shares not stored by Phase 12 |
| Sensitivity coefficients | No FX amounts, floating/fixed debt split, or revenue elasticity stored |
| P/B, P/S, market cap, EV multiples, cash-flow yield | No share-count data (share capital in PKR cannot convert to shares without a par value) |
| Dividend yield, DDM | No DPS series |
| DCF (FCFF/FCFE) | No source-backed WACC, growth, or forecasts |
| Peer median P/E | Each company alone in its sector; cross-sector peers never forced |
| Sum-of-parts | No segment statements |
| ROIC | NOPAT needs validated tax allocation (HUBC operating profit includes post-tax associate earnings) |
| OGDC operating margin / ROCE | No operating-profit line |
| ROE owners (NML, OGDC) | No owners-attributable profit line |
| TTM ratios | No full-year NML/OGDC flows |
| Technical values (SMA, RSI, MACD, …) | 0 calculable Phase 6 values (needs 5+ closes) |
| Forecasts | Phase 13 abstained on all 120 assessments |
| User-facing decisions | All WITHHELD (confidence caps at LOW on UNVERIFIED inputs) |
| Backtest results | Phase 17 NOT_RUNNABLE (single observation) |
| Vector retrieval | Registered but not implemented (no verified local embedding model) |
| Universe-wide news coverage | Terms-gated (written PSX permission pending) |
| Investor flows | No verified published series loaded |
| Adjusted price series | No ex-dates for stored dividend actions |

## No-price-target rule

There is no `price_target` figure kind. `figure()` raises
on any key containing `price_target`, and QA rejects the
wording "target price" in any body. Valuation scenarios list
computed methods and unavailable methods with reasons; they
never state a target price, and no section recommends a
trade.
