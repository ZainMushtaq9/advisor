# HBL Portfolio Coverage Expansion — Brief

**Status: PREPARATION ONLY — do NOT execute the expansion in this
task.** The user ordered expansion ONLY after a brief exists. This
brief is that prerequisite. No portfolio, ledger, comparison, or
exclusion row is created, changed, or deleted by this document, and
no acceptance verdict changes because of it.

## 1. Current state (measured, 2026-11-05)

- **Baseline portfolios (3, all `simulated_portfolios`, price_date
  2026-11-03, capital PKR 1,000,000, status CONSTRUCTED):**
  - `ew_statements_3_balanced` (equal_weight_baseline): eligible
    HUBC, NML, OGDC; cash 526.97.
  - `rule_screen_pass_balanced` (rule_based_screen_pass): eligible
    HUBC, OGDC; cash 418.86.
  - `rule_screen_pass_conservative` (rule_based_screen_pass):
    eligible HUBC, OGDC; cash 100,115.90 (cash_floor 0.10).
- **Ledger/comparison rows:** `paper_ledger_entries` 13,
  `portfolio_comparisons` 3. Portfolio reconciliation recomputation
  currently matches (ew_statements_3_balanced 999,473.03 + 526.97;
  rule_screen_pass_balanced 999,581.14 + 418.86 — see the acceptance
  run for exact values).
- **HBL exclusion rows are STALE and must be superseded, not
  edited in place.** `portfolio_exclusions` holds three HBL rows,
  all `SCREEN_NOT_RUNNABLE`:
  - "Baseline scope is the statement companies; HBL has no
    statements loaded (Phase 15 SCREEN_NOT_RUNNABLE) and is
    therefore out of baseline scope, not out of the universe. HBL's
    quote itself is ELIGIBLE."
  - Two rows: "Phase 15 screening is not SCREEN_PASS; gate reasons:
    {'gates': ['no_statements', 'too_few_dimensions']}."
  Both reasons predate the HBL batch. HBL now HAS statements (118
  total across the DB, +30 from HBL) and a 6/7 decision. The
  expansion must retire these reasons by versioning (new portfolio
  versions superseding old ones — `simulated_portfolios` already
  carries `version_number`, `supersedes_id`, `is_current`), never by
  overwriting the stored reasons.
- **Banking rule (binding, carried from the batch):** Phase 9 uses
  the bank residual-income model for HBL, never industrial models;
  where no banking adaptation exists the metric is `not_applicable`
  with the banking reason. Any HBL portfolio metric that needs a
  valuation or risk input must respect this rule or record
  `not_applicable` with the reason — it must not borrow an
  industrial-model value for HBL.

## 2. Eligibility evidence for HBL (measured)

- **Quote ELIGIBLE at 286.16** (price date 2026-11-03, the same
  price date as all baseline portfolios — no new price date is
  needed for the expansion).
- **Decision 2026-11-05:** SCREEN_PASS / HOLD_CANDIDATE / WITHHELD /
  LOW, 6/7 dimensions (the batch's HBL row; the older 2026-11-04
  HBL row at 2/7 is history and stays as history).
- **Fundamentals present:** HBL in fundamentals (144 total) and
  valuations (68 total; HBL trailing P/E 6.291996 = 286.16 / 45.48,
  EPS published 2026-03-03 ≤ price date 2026-11-03).
- **Forecasts:** HBL assessments 36, all abstained (no series meets
  any method's interval minimum) — so, as with the baseline, NO
  expected return is assumed from forecasts. The expansion inherits
  the baseline's "no validated expected-return source" stance.
- **What HBL does NOT yet have:** no portfolio membership, no ledger
  entries, no comparison rows. That absence is the gap this brief
  closes.

## 3. New portfolio definitions (proposed)

All new portfolios are NEW versions (`version_number` incremented,
`supersedes_id` pointing at the baseline row, `is_current` flipped
only after the acceptance criteria in §7 pass). The baseline rows
are never edited.

| Proposed portfolio | Method | Eligible tickers | Capital / price date | Notes |
|---|---|---|---|---|
| `ew_statements_4_balanced` | equal_weight_baseline | HUBC, NML, OGDC, HBL | PKR 1,000,000 / 2026-11-03 | Direct successor of `ew_statements_3_balanced`; same caps (max_single 0.50, max_sector 1.00, cash_floor 0.00). |
| `rule_screen_pass_balanced_v2` | rule_based_screen_pass | HUBC, OGDC, HBL | PKR 1,000,000 / 2026-11-03 | Successor of `rule_screen_pass_balanced`; HBL enters via its 2026-11-05 SCREEN_PASS decision. NML stays out (decision 4/7, not SCREEN_PASS). |
| `rule_screen_pass_conservative_v2` | rule_based_screen_pass | HUBC, OGDC, HBL | PKR 1,000,000 / 2026-11-03 | Successor of `rule_screen_pass_conservative`; same conservative constraints (cash_floor 0.10, max_sector 0.50). |

- **Deliberately NOT proposed:** a banking-sector-tilted portfolio
  (no sector-tilt brief exists, and a single-bank tilt would need
  its own risk justification); any portfolio using a different
  price date or capital (would break comparability with the
  baseline); any real-money or broker-linked variant (none exists
  in this project, and none is authorized).
- **Sector concentration watch:** HBL is COMMERCIAL BANKS while
  HUBC/NML/OGDC are energy/materials. The equal-weight v2 holds
  25% in one bank; the conservative v2's max_sector_weight 0.50
  must be evaluated against the banking sector weight explicitly
  in the construction report — if the cap binds, the binding
  constraint is recorded (same pattern as the baseline's
  `binding_constraints` notes), not silently relaxed.

## 4. Phase 17 ledger re-derivation plan

1. **Snapshot first.** Row exports + counts of `simulated_portfolios`,
   `paper_ledger_entries`, `portfolio_comparisons`,
   `portfolio_exclusions`, and the acceptance
   `portfolio_reconciliation` recomputation, before any write.
   (Same discipline as the D-05 snapshot in this task.)
2. **Construct the three new portfolio versions** with
   `scripts/run_portfolio_construction.py` (or its successor, if the
   implementing item extends it for versioning). Whole-share
   rounding applies exactly as in the baseline; cash is the
   residual, never a plug.
3. **Re-derive the ledger** with `scripts/run_backtesting.py`:
   new `paper_ledger_entries` for the three new portfolios only.
   The 13 baseline ledger rows are preserved untouched.
4. **Supersede the HBL exclusion reasons** by writing new exclusion
   rows (or by the portfolios' own eligibility lists — decide at
   implementation time, but record the decision): the old
   SCREEN_NOT_RUNNABLE rows stay as history with their original
   wording; the new state says HBL is included via the 2026-11-05
   SCREEN_PASS decision.
5. **Re-derive comparisons** (`portfolio_comparisons`): new rows
   comparing each v2 portfolio against its baseline predecessor
   (same capital, same price date, same method) — see §6.
6. **Re-run the acceptance portfolio_reconciliation recomputation**
   and confirm it matches under the new state, or report the exact
   mismatch. The recomputation's claimed value will need a
   measured update (same pattern as the D-05 census update in this
   task: measure first, then claim — never assert in advance).
7. **Reports:** the expansion does NOT regenerate Phase 22 reports
   unless the implementing item's brief says so; if it does, it
   follows the D-05 news-first order (news → decisions → reports)
   and creates new report versions, never overwrites.

## 5. Cash reconciliation method

- Identity per portfolio: `capital = sum(holdings at price_date) +
  cash`, with holdings valued at whole shares × the 2026-11-03
  price (HBL at 286.16). Cash is computed as the residual after
  whole-share rounding, exactly as the baseline does (baseline
  proofs: 999,473.03 + 526.97 = 1,000,000.00;
  999,581.14 + 418.86 = 1,000,000.00).
- Checks: cash ≥ cash_floor; max_single_weight and
  max_sector_weight caps evaluated on post-rounding weights;
  any binding constraint recorded in `binding_constraints`.
- Failure rule: if any new portfolio fails reconciliation (identity
  off by more than rounding, i.e. > PKR 0.01), the expansion stops
  and reports — no plug figure, no forced balance.

## 6. Comparison methodology

- **Pairs:** each v2 portfolio vs its baseline predecessor only
  (ew_4 vs ew_3; balanced_v2 vs balanced; conservative_v2 vs
  conservative). No cross-method comparisons (equal-weight vs
  rule-based answers a different question and is out of scope).
- **Held constant:** capital (PKR 1,000,000), price date
  (2026-11-03), method, caps, and the no-expected-return stance
  (forecasts abstain; no return is assumed for any portfolio).
- **Reported deltas:** holdings value, cash, cash weight, sector
  weights (with the banking sector shown separately), binding
  constraints, and the HBL weight actually achieved after rounding.
- **What is NOT compared:** returns (1 price date gives 0 return
  observations — same limitation as the baseline, stated not
  hidden); risk metrics that would need an industrial model for
  HBL (recorded `not_applicable` with the banking reason instead).

## 7. Tests (to be written by the implementing item)

- Construction: each v2 portfolio's eligible tickers, weights,
  caps, and cash reconcile to the §5 identity; HBL weight is
  present and within caps; NML absent from rule-based v2.
- Ledger: new ledger entries exist only for the v2 portfolios;
  baseline ledger rows unchanged (count + hashes, if available).
- Exclusions: old HBL SCREEN_NOT_RUNNABLE rows still present with
  original wording; new state shows HBL included (no overwrite).
- Reconciliation recomputation: matches under the new claimed
  value (measured, then claimed).
- Regression: full backend suite, acceptance run (portfolio
  recomputation explicitly verified), frontend suite if any
  portfolio surface changes.
- Guard test: a portfolio construction run with an ineligible
  ticker (e.g. a ticker without a SCREEN_PASS decision) refuses
  that ticker rather than including it.

## 8. Acceptance criteria

- The three v2 portfolios exist as new versions with the baseline
  rows preserved and `is_current` flipped only after §7 passes.
- Cash reconciles to the §5 identity for all three.
- The acceptance `portfolio_reconciliation` recomputation matches
  under its (measured, updated) claimed value.
- The HBL exclusion history is preserved verbatim; the new
  inclusion state is recorded separately.
- No report, decision, figure, or acceptance verdict changes except
  the ones this brief names (new portfolio/ledger/comparison rows
  + the measured reconciliation claim update).

## 9. Risks

- **Sector concentration:** a 25% single-bank weight in the
  equal-weight v2 is a real concentration change vs the baseline;
  the construction report must show it, not bury it.
- **Banking-model gaps:** any metric without a banking adaptation
  becomes `not_applicable` for HBL — if too many metrics drop out,
  the v2 portfolios' comparability weakens. The implementing item
  must list which metrics drop out before claiming comparability.
- **Single price date:** with one trading date, the expansion adds
  cross-sectional breadth (a fourth company) but no time-series
  depth. Returns, volatility, and drawdown remain NOT_CALCULABLE —
  the brief must not be read as promising them.
- **Stale-exclusion confusion:** readers of the old exclusion rows
  could conclude HBL is still excluded. The implementing item's
  report must state the supersession prominently.
- **Scope creep into trading:** all portfolios are hypothetical
  simulations (PKR 1,000,000 simulation capital, not real funds).
  Nothing in the expansion creates an order, broker, or custody
  concept, and no such concept may be added under this brief.
