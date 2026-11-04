# Phase 17 — Transaction-cost sensitivity

## Cost model

Cost = traded value x (fees_bps + taxes_bps + slippage_bps) /
10000, computed only when all three bps inputs are present.
When any input is NULL the cost is NULL (never computed from
an invented rate).

## Production status: not_applicable

- Fees / taxes / slippage sources: none validated in the loaded
  data; assumption parameters are recorded as UNVALIDATED with
  NULL values on every run.
- Production trades: zero, so there is nothing to cost.
- Sensitivity demonstration: fixtures only (e.g. PKR 1,000,000
  traded at 10 + 15 + 5 bps = PKR 3,000). Fixture sensitivities
  are not production results and are never stored as such.

## What unlocks production cost sensitivity

1. A validated fee schedule source (broker/exchange published).
2. A validated tax rule source.
3. A slippage methodology with observed spreads or a stated
   assumption approved as an assumption (not as data).
4. Production trades (which need more price dates first).
