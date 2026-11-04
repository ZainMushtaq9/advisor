# Phase 12 adjustment rules

Four rule definitions, all `defined_not_applied` in this run (no
stored action has an ex-date, so no rule may be applied to any
series). Formulas are pure Decimal functions in
`backend/app/services/ownership_actions/adjustments.py`, tested
without a database.

| Rule | Formula | Requires |
|---|---|---|
| DIVIDEND_CASH | adjusted_close = raw_close − dividend_per_share, for prices on/after the ex-date | ex_date, dividend_per_share |
| BONUS_ISSUE | factor = (existing + bonus) / existing; adjusted_close = raw_close / factor; adjusted_volume = raw_volume × factor | bonus_ratio, ex_date |
| SPLIT | factor = new / old; adjusted_close = raw_close / factor; adjusted_volume = raw_volume × factor | split_ratio, ex_date |
| RIGHTS_ISSUE | TERP = (old × cum_price + new × subscription) / (old + new); factor = TERP / cum_price | subscription_price, rights_ratio, ex_date |

## Worked examples (rule demonstrations, NOT stored series)

These use actual stored values to prove the formulas; because no
ex-date exists, none of them is stored as an adjusted price, and no
adjusted series exists anywhere in the database.

- NML: raw close 123.61 (2026-11-03) − final DPS 5.00 = 118.61.
- HUBC: raw close 197.24 − final DPS 10.00 = 187.24; − interim
  DPS 5.00 = 192.24.
- Bonus algebra: 1-for-4 bonus → factor 1.25; price 100 → 80,
  volume 1,000 → 1,250 (pure formula test, no company).
- TERP algebra: 100 old shares at 50, 25 new at 40 → TERP 48
  (pure formula test, no company).

## Raw-preservation guarantee

`market_prices.is_adjusted` is False on all 444 rows after this run.
An adjustment produces a derived view only; it never updates a raw
row. The Phase 3 `corporate_actions.adjustment_factor` column is
where an applied factor will live once ex-dates exist; it is empty
today.
