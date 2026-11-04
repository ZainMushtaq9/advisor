# Phase 12 coverage report

## Coverage by deliverable

| Deliverable | Coverage | Status |
|---|---|---|
| Ownership and float dataset | 1/470 companies (HUBC); float: 0 companies | Partial — float absent by design (no published figure) |
| Corporate action registry | 2/470 companies with actions (HUBC, NML); 5 actions | Partial — dates unpublished in sources |
| Adjustment rules | 4 rules defined, 0 applied | Defined — application blocked on ex-dates |
| Market breadth/liquidity | 1 trading date; 444/470 priced; 37/37 sectors | Partial — single-day snapshot |
| Investor flows | 0 series, 0 rows | Empty by design — no verified series loaded |
| APIs | 6 GET-only routes, live-verified | Complete for this phase's data |

## Acceptance gate — item by item

- **Each ownership/action record has dates and a source.** PASS
  with the documented interpretation: every record carries a source
  (document + pages, or statement label + period) and every date
  field is either a value or an explicit NULL-with-reason in
  `date_evidence`. No date is invented.
- **Corporate action handling is tested against actual examples.**
  PASS: dividend adjustment tested on actual NML (123.61 − 5.00)
  and HUBC (197.24 − 10.00 / 5.00) values; bonus/split/TERP algebra
  tested on hand-calculated cases; raw preservation tested
  (is_adjusted False on all 444 rows).
- **Breadth completeness is visible.** PASS: every breadth metric
  carries numerator/denominator or an insufficient_inputs reason;
  the 26 missing tickers are named; sector coverage is per-sector.
- **No unsupported investor-flow claims are produced.** PASS: zero
  flow rows, zero flow claims; the API returns an empty list with
  the explanation and the unblocker.

## What would complete Phase 12

1. Per-company issuer-document verification pass (ownership for
   more companies, starting with HBL once its statements load).
2. PSX announcement data under written permission (action dates,
   universe-wide breadth inputs: previous_close, turnover).
3. More trading days (multi-day breadth, highs/lows, frequency).
4. A published free-float series (float-adjusted measures).
5. A terms-reviewed published flow series (SBP SCRA/FPI or NCCPL).
6. H1 verification (second agreeing source incl. official) for
   promotion of any row above UNVERIFIED.
