# Phase 17 — Strategy registry (backtest-v1)

| Strategy | Rule reference | Universe | Rebalance |
|---|---|---|---|
| equal_weight_statements_3 | phase16:ew_statements_3_balanced | HUBC, NML, OGDC | buy_and_hold_from_construction |
| rule_screen_pass_balanced | phase15:decision-rules-v1 + phase16:rule_screen_pass_balanced | HUBC, OGDC | buy_and_hold_from_construction |
| rule_screen_pass_conservative | phase15:decision-rules-v1 + phase16:rule_screen_pass_conservative | HUBC, OGDC | buy_and_hold_from_construction |
| buy_and_hold_hubc | buy_and_hold_single_name | HUBC | buy_and_hold |
| buy_and_hold_ogdc | buy_and_hold_single_name | OGDC | buy_and_hold |

Registration is not a result: every registered strategy's
production run over 2026-11-03 → 2026-11-03 is NOT_RUNNABLE
(zero return intervals). A strategy version is immutable once
committed: a rule change registers a new version, never edits
backtest-v1 rows.

## Execution assumptions recorded on every run

- Signal time: close.
- Execution timing: next eligible close after the signal (first
  observed close strictly after the signal date; same-day fills
  are not assumed).
- Fees / taxes / slippage: UNVALIDATED (no validated source in
  the loaded data); values are NULL, never invented rates.
- Risk-free convention: not established. The SBP policy rate
  (12.00% p.a.) is a policy rate, not a Treasury-bill risk-free
  series, and is never used as one.
- Benchmark: none loaded (no KSE-100 series), so
  benchmark-relative return is not_applicable.
