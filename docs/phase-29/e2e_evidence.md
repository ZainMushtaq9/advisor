# Phase 29 — End-to-end evidence

Run: `phase29-acceptance-2026-11-05`, run date 2026-11-05, verdict
PARTIALLY COMPLETE. Fifteen scenarios, executed by
`scripts/run_acceptance.py` (dry-run default, `--commit` for the
recorded run) against the live database. No business row was written
or modified by this phase; the only writes are the acceptance tables
themselves (1 run, 15 scenarios, 15 recomputations, 14 defects).

## Outcomes

| Scenario | Outcome | Evidence (summary) |
|---|---|---|
| chain_hubc_full | PASS | 8 statements, 36 fundamentals, 17 valuations, decision present, 1 report, price 197.24 |
| chain_ogdc_full | PASS | 24 statements, 36 fundamentals, 17 valuations, decision present, 1 report, price 303.63 |
| chain_nml_full | PASS | 56 statements, 36 fundamentals, 17 valuations, decision present, 1 report, price 123.61 — with the loss, stale statement and valuation gaps honestly recorded |
| chain_hbl_partial | BLOCKED | 30 statements loaded, 0 fundamentals, 0 valuations, decision predates statements, 0 reports — Phases 8+ re-runs pending |
| missing_source | PASS | HBL analysis honestly pending; no fabrication, no invented row |
| delayed_data | PASS | market_prices stale flagged; session gap 2 weekdays recorded |
| ticker_rename | PASS | ENGRO/ICI/CNERGYICO absent; ENGROH/LCI/CNERGY present; no silent rename or merge |
| corporate_action | PASS | 5 dividends, all dates NULL, no adjusted series stored |
| restatement | NOT_EVALUABLE | financial_document_versions = 0 rows; versioning discipline documented but unexercised |
| suspended_security | NOT_EVALUABLE | No suspended flag exists in the registry scope |
| no_quote | PASS | AGLNCPS in universe, no price row; eligibility evidence recorded |
| model_failure | PASS | Forecasts abstained 120/120, decisions WITHHELD 4/4, backtests NOT_RUNNABLE 5/5, no fabricated outputs |
| process_restart | PASS | ops/start.sh exec fix + fresh-environment test + post-report re-test + twice-proven VM recovery recipe |
| provenance_warnings | PASS | 22 DRAFT reports, 0 published externally, QA gate, dashboard honesty layer |
| point_in_time | PASS | Decision date 2026-11-04 uses price date 2026-11-03; HUBC P/E uses EPS published 2026-09-21; no forecast or recommendation stored as fact (Phase 3 forecasts and recommendations tables are 0 rows) |

Counts: 12 PASS, 0 FAIL, 1 BLOCKED, 2 NOT_EVALUABLE.

## Notes

- The three full chains (HUBC, OGDC, NML) pass end to end: statement
  → fundamentals → valuation → decision → report, with the price
  date (2026-11-03) preceding the decision date (2026-11-04).
- The HBL chain is BLOCKED at statements by design: the HBL
  extraction loaded 30 statements and 800 line items, but no
  fundamentals, valuations, decision-with-evidence, or reports exist
  for HBL. That is the post-Phase-30 re-run batch (defect D-03), not
  a Phase 29 failure to fix by hand.
- NOT_EVALUABLE is not a pass and not a failure: restatement
  versioning and suspended-security handling have no production
  observation to evaluate against, and none was invented.
- The process_restart scenario FAILED in the first dry run because
  the audit scanner computed the repository root wrong (it stopped
  at `backend/`); the fix (`.parents[4]`) is recorded in the run
  report, and the scenario passes in the committed run.
