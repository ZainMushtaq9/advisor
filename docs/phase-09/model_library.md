# Phase 9 — Model library v1.0

All models are pure Decimal functions in
`backend/app/services/valuation/formulas.py`. No model ever returns
zero as a substitute and none ever raises on bad inputs — bad inputs
are a coverage outcome, not an exception. Hand-calculated tests live
in `backend/tests/test_valuation_phase09.py` (fixtures, not
production data, for the assumption-gated models).

## Relative valuation

| Model | Formula | Production state |
|---|---|---|
| pe_trailing | close_price / EPS | Computed for HUBC (5.1553x) and OGDC (17.8816x); NML blocked (negative EPS + unknown publication) |
| pb | close_price / book_value_per_share | NOT_CALCULABLE — no shares outstanding |
| ps | close_price / revenue_per_share | NOT_CALCULABLE — no shares outstanding |
| ev_ebitda | enterprise_value / EBITDA | NOT_CALCULABLE — no market cap, no EBITDA line |
| ev_ebit | enterprise_value / EBIT | NOT_CALCULABLE — no market cap |
| div_yield | DPS / close_price | NOT_CALCULABLE — no DPS series |
| market_cap | close_price x shares outstanding | NOT_CALCULABLE — no shares outstanding |
| enterprise_value | market_cap + ib_debt - cash | NOT_CALCULABLE — no market cap |
| cf_yield | OCF per share / close_price | NOT_CALCULABLE — no shares outstanding |
| peer_median_pe | median of comparable peers' trailing P/E (>= 3 peers) | NOT_CALCULABLE — no peers (sector-alone) |

Negative earnings, negative equity, and non-meaningful multiples:
a multiple on non-positive EPS returns None (NML). Negative equity
does not arise in this set (all three balance sheets are positive
equity). Diluted shares: the extracted EPS is used as printed
(HUBC eps_total, NML/OGDC eps_basic); no diluted-share adjustment
is attempted because no diluted share counts exist. Stale prices:
the single 2026-11-03 close is the valuation-date price by
definition; it is labelled single-date, not a series. Financial
companies: no industrial model is applied to a bank; HBL pending.

## Intrinsic models

| Model | Formula | Production state |
|---|---|---|
| dcf:fcff | PV of forecast FCFF + TV, TV = FCF_last x (1+g)/(r-g) | NOT_CALCULABLE — no WACC, growth, or forecasts |
| dcf:fcfe | PV of forecast FCFE + TV | NOT_CALCULABLE — no cost of equity, growth, or forecasts |
| dividend:ddm | Gordon: DPS x (1+g)/(r-g) | NOT_CALCULABLE — no DPS, growth, or required return |
| residual_income:bank | BV + PV of residual incomes | NOT_APPLICABLE (industrials); HBL pending |
| asset_based:equity_book_value_total | total_equity as printed | Computed for all 3 companies |
| asset_based:equity_book_value_owners | owners equity as printed | Computed for HUBC, NML; OGDC blocked (no split) |
| asset_based:sum_of_parts | sum of segment values | NOT_CALCULABLE — no segment statements |

Impossible-assumption guards (implemented and tested): terminal
growth at or above the discount rate returns None (DCF); required
return at or below growth returns None (DDM); non-positive discount
or required return returns None. Discount-rate correctness: no
discount rate is asserted in v1.0 — WACC, cost of equity, and
required returns must arrive source-backed (Phase 10 macro work),
never invented. Cash/debt adjustments for enterprise value use
interest-bearing debt and cash as defined in Phase 8 key maps, but
are unreachable without market cap.

## Scenarios and sensitivity

- Bear/base/bull scenarios exist only for models that compute. DCF
  scenarios are NOT_CALCULABLE with DCF itself.
- P/E price sensitivity (+/-10% price, EPS held) is mechanical, not
  a scenario forecast, and is stored in the row's value_low /
  value_high and sensitivity JSON.
- Book values are point values with no sensitivity range (low/high
  NULL) — inventing a range would be fabrication.
- No model output is averaged with another: incompatible models are
  reported side by side, never blended.

## Peer engine

`backend/app/services/valuation/peers.py`. Rules: same sector
(verbatim registry sector), same reporting frequency, period_end
within 90 days, not the company itself. Outlier rule: above 4 peers,
a multiple beyond 3x the peer median is excluded and reported;
below 4 peers no outlier step runs. Median requires >= 3 peers.
Production peer sets are empty for all three companies.

## Audit report (independent recomputation)

- HUBC P/E: 197.24 / 38.26 = 5.1552535... — matches the committed
  row (stored 5.155254 at Numeric(24,6) scale) and the unit test.
- OGDC P/E: 303.63 / 16.98 = 17.8816254... — matches the committed
  row (stored 17.881625) and the unit test.
- Book values match the Phase 7 normalized line items exactly
  (HUBC total 258,007,509,000; owners 235,381,655,000; NML total
  159,920,849,000; owners 146,538,114,000; OGDC total
  1,383,637,471,000 PKR).
- Row counts: 51 written (17 per company), 7 computed, 41
  insufficient_inputs, 3 not_applicable; second --commit wrote 0
  rows and skipped 51 (idempotency proven).
- All 51 rows are UNVERIFIED with source_key
  phase09-valuation-v1.0 and a computation_status in assumptions
  JSON; zero rows carry a higher status.
- Full backend suite: 162 passed (147 prior + 15 new).
- API smoke: HUBC/NML/OGDC 200 with correct computed sets, HBL 200
  pending, unknown ticker 404 (same custom handler as Phase 8).
