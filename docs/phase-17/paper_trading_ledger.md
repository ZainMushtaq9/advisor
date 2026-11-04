# Phase 17 — Paper trading ledger

## Lifecycle (simulator only, never execution)

proposed -> accepted -> filled / partially_filled / cancelled /
rejected. Acceptance requires the ticker in the universe and a
valid reference price. A fill requires a next eligible price
(first observed close strictly after the proposal date) and a
positive fill price. Without a later observed price an order
stays accepted and unfilled; it is never filled at an invented
price.

## Production ledger (computed, dated 2026-11-03, SIMULATION)

Re-derived from the three Phase 16 CONSTRUCTED simulated
portfolios (hypothetical capital PKR 1,000,000):

| Portfolio | Positions | Cash | Valuation |
|---|---|---|---|
| ew_statements_3_balanced | 3 | 526.97 | 1,000,000.00 |
| rule_screen_pass_balanced | 2 | 418.86 | 1,000,000.00 |
| rule_screen_pass_conservative | 2 | 100,115.90 | 1,000,000.00 |

Each position value is recomputed as units x price; cash is
capital minus the recomputed holdings total; valuation is
holdings + cash and reconciles to capital exactly. Total ledger
entries: 13 (7 positions + 3 cash + 3 valuations).

## Production orders: zero, by rule

- Phase 15 user-facing values are all WITHHELD, so no
  decision-driven order may be created.
- No price exists after 2026-11-03, so no order could fill.
- The lifecycle engine exists and is fixture-tested; it holds
  zero production rows rather than invented orders.

## Dividends, corporate actions, cash

No dividend or corporate-action ledger entry is created: the 5
stored dividend actions have NULL dates, so no ex-date exists
at which an adjustment or cash entry could be posted. Cash
movements from trades are absent because no production trade
exists. When an action gains an ex-date, a later run posts the
adjustment from the Phase 12 registry, never by backdating.
