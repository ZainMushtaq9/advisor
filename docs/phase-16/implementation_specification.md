# Phase 16 — Implementation Specification

## Objective (playbook lines 1267–1328)

Construct diversified, constraint-aware hypothetical portfolios
using validated recommendations, returns, risk, liquidity, and
user-defined constraints. Dependencies: Phases 4, 5, 13, 14, 15.

## What was built

- **Models** (`backend/app/models/portfolio.py`, migration
  `20261104_0013`): `simulated_portfolios`,
  `simulated_portfolio_holdings`, `portfolio_exclusions`,
  `portfolio_sector_allocations`, `portfolio_comparisons`.
  Phase 3 `portfolios` / `portfolio_holdings` were intentionally
  NOT reused (precedent from Phases 11–15): they model user-owned
  portfolios with a user_id and no method, constraints,
  assumptions, sector, exclusion, or comparison semantics.
- **Service** (`backend/app/services/portfolio_construction/`):
  `__init__.py` (risk-profile registry, method registry,
  assumptions template, four-way eligibility function),
  `formulas.py` (pure Decimal math), `runner.py` (DB orchestration).
- **CLI**: `scripts/run_portfolio_construction.py` (--dry-run
  default / --commit, optional --profile filter).
- **API** (GET-only): `backend/app/api/v1/endpoints/portfolios.py`
  (list, detail with holdings/sectors/exclusions, comparisons,
  status).

## Construction rules

1. **Eligibility first.** A ticker needs a security row AND a
   positive close on 2026-11-03. Statuses: ELIGIBLE,
   NOT_IN_UNIVERSE, IN_UNIVERSE_NO_QUOTE, INVALID_QUOTE
   (null/zero/negative price). Rejected tickers never become
   positions; rule-based rejections are stored as exclusion rows.
2. **Whole shares only.** units = floor(target value / price);
   residual cash absorbs rounding; holdings + cash == capital
   exactly (Decimal). Target weights are stored next to actual
   (post-rounding) weights. Weights are stored at 6dp; the exact
   reconciliation is on values.
3. **Screening ≠ eligibility.** HBL has a valid quote (286.16)
   and is ELIGIBLE, but is rule-excluded (Phase 15
   SCREEN_NOT_RUNNABLE, no statements). NML has a valid quote
   but is rule-excluded (SCREEN_FAIL with gates). The rule-based
   portfolios use Phase 15 research conclusions and screening
   outcomes — NOT issued recommendations: every Phase 15
   user-facing value in this run is WITHHELD, and the portfolios
   say so in their assumptions.
4. **No look-ahead.** Only 2026-11-03 prices and Phase 15
   decisions dated 2026-11-04 (publications on or before that
   date) feed construction.
5. **Mean-variance gated, not faked.** It needs validated
   expected returns AND a covariance matrix. Phase 13 computed 0
   forecasts (120/120 abstained) and 1 price date gives 0 return
   observations, so the gate returns NOT_CALCULABLE with both
   reasons. The comparison row exists so the gating is auditable.
6. **Assumptions shown separately.** Expected returns, historical
   returns, and forecasts are three distinct absences in every
   portfolio's assumptions JSON, never merged into one invented
   return figure. Transaction costs are excluded (no defensible
   source), not invented.
7. **Simulation only.** Capital is hypothetical (PKR 1,000,000),
   horizon is not_specified (no horizon return claim is made),
   and no broker/order/execution concept exists anywhere — proven
   by a test scanning application source for execution identifiers
   (0 hits) and asserting the endpoint is GET-only.

## Portfolios constructed (all CONSTRUCTED, all UNVERIFIED)

| Name | Method | Profile | Holdings | Invested | Cash | Cash weight |
|---|---|---|---|---|---|---|
| ew_statements_3_balanced | equal_weight_baseline | balanced | HUBC, NML, OGDC | 999,473.03 | 526.97 | 0.0527% |
| rule_screen_pass_balanced | rule_based_screen_pass | balanced | HUBC, OGDC | 999,581.14 | 418.86 | 0.0419% |
| rule_screen_pass_conservative | rule_based_screen_pass | conservative | HUBC, OGDC | 899,884.10 | 100,115.90 | 10.0116% |

Exclusions: NML (SCREEN_FAIL) and HBL (SCREEN_NOT_RUNNABLE) from
both rule-based portfolios; HBL also recorded as out of baseline
scope for the EW portfolio (baseline scope is the statement
companies). Growth profile is defined-not-run: on the 2-name
rule-based set it collapses to balanced.

## Binding constraints

- Conservative cash floor: binding (invested capped at 90%;
  actual cash 10.0116%, excess purely whole-share rounding).
- Balanced max single-name weight (50%): effectively binding
  (targets exactly at the cap; actuals 49.98% after rounding).
- No cap was violated by any constructed portfolio (checked in
  code; a violation raises instead of storing).

## Residual risks (honest)

- 1 price date: no returns, no covariance, no multi-day breadth.
- All inputs UNVERIFIED; forecasts abstained; technical evidence
  absent; user-facing Phase 15 values WITHHELD.
- Coverage is 3–4 companies; HBL has no rule-based position
  pending its Phase 7 load.
- Sector concentration: each portfolio's largest sector weight
  equals its largest single-name weight (each name is its own
  sector here) — see sector_allocation_report.md.
