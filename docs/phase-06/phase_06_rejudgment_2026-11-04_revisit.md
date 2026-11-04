# Phase 6 revisit re-judgment — 2026-11-04

Branch: `phase-06-revisit`, branched from `phase-06-completion` tip
`e556806` (remote SHA verified equal before work; base tip NOT moved;
main untouched at `eb6025b`). No code, migration, or framework file
changed in this run. One new document (this file). Verdict:
**PARTIALLY COMPLETE (unchanged)**.

## 1. Entry state found — a real regression, restored, not assumed

The live DB (PostgreSQL 16, `psx_intelligence`, Alembic head
`20261104_0005`) held the recorded Phase 5 inputs — `market_prices`
444 rows, exactly one trading date 2026-11-03, `previous_close` NULL
on all 444, companies 470 — but ALL Phase 6 bookkeeping tables were
empty: `technical_calculation_runs` 0, `technical_calculation_errors`
0, `technical_indicator_definitions` 0,
`technical_indicator_configurations` 0, `technical_indicator_values` 0,
`technical_signal_events` 0.

Cause (established, not guessed): the Phase 6 completion run had
restored this bookkeeping after VM replacement #3, but VM replacement
#4 during the Phase 7 run restored the 1230-PKT backup and re-ran only
the registry import and the price commit. Phase 6 coverage was never
re-run after recovery #4, so its bookkeeping was lost. This revisit
restored it deterministically from the already-committed prices (no
new collection, no invented values).

## 2. Coverage restoration (existing DB rows only)

CLI `scripts/run_technical_indicators.py`, run key
`phase06-coverage-2026-11-03`, as-of 2026-11-03:

- Dry-run first: 470 assessed, 62 registered, 0 calculable, 0 written;
  DB counts unchanged afterward (runs 0, errors 0) — dry-run writes
  nothing, as designed.
- `--commit`: 470 assessed, 62 registered, 0 calculable, values
  written 0, error rows written 124.
- DB after commit, verified directly: runs 1, errors 124
  (`insufficient_warmup` 61, `missing_data` 63), definitions 62,
  configurations 62, values 0, signal events 0, 62 distinct error
  indicator keys. Reconciliation matches the completion run exactly:
  61 non-daily-return indicators × (1 insufficient_warmup row for the
  444 one-bar securities + 1 missing_data row for the 26 zero-bar
  securities) = 122, plus `daily_return`'s 2 missing_data rows = 124.
- Re-run guard verified: a further `--commit` reported
  `already_recorded: true`, wrote 0 values and 0 error rows; counts
  unchanged (1 run, 124 errors, 0 values).
- `daily_return` remains `missing_data` for all 470: `previous_close`
  is blank on every price row, so more trading days alone do NOT
  unblock it under the current convention; it needs a present
  `previous_close` in a future source file.

## 3. Re-verification results

- Backend suite on this tree: **114 passed, 0 failed** (1 unrelated
  Starlette deprecation warning). Includes the Phase 6 tests.
- Ruff check, Phase 6 scope only (`backend/app/services/
  technical_indicators`, `backend/app/api/v1/endpoints/indicators.py`,
  `scripts/run_technical_indicators.py`, `backend/tests`): **all checks
  passed**. The 7 pre-existing `scripts/run_phase4_pg_check.py` issues
  (Phase 4 scope) and the ruff-format version drift on 7 Phase 6 files
  are unchanged from the completion run and were NOT touched.
- Endpoint is GET-only by code inspection:
  `backend/app/api/v1/endpoints/indicators.py` exposes exactly four
  routes, all `@router.get`: `/indicators/coverage`,
  `/indicators/coverage/{ticker}`, `/indicators/values`,
  `/indicators/signals`. No POST/PUT/DELETE/PATCH route exists.
- Signals separation confirmed: `ACTIVATED_RULES` is an empty tuple
  by design (`signals.py` line 51); zero signal events exist; no
  buy/sell language is produced.
- Immutability triggers confirmed in the live schema: UPDATE and
  DELETE triggers on exactly four tables —
  `technical_indicator_values`, `technical_signal_events`,
  `quantitative_market_features`, `market_regime_observations`.
  `technical_calculation_runs` is intentionally unguarded (the runner
  itself updates run status).
- No indicator value, signal event, quantitative market feature, or
  regime observation exists anywhere in the live DB (all counts 0).

## 4. Scope-gap dispositions (closed by explicit scoping, with reasons)

The completion run left four scope gaps to be "closed or explicitly
scoped out". They are disposed of here; none is silently dropped:

1. **Validated trading calendar — SCOPED OUT.** Weekly (ISO) and
   monthly aggregation remain "partial" by design without a validated
   calendar. A validated calendar requires an official PSX trading /
   holiday schedule, which is not available and is itself PSX
   exchange data subject to the same Terms gate. Daily-only
   computation is unaffected. This is a documented limitation, not a
   defect, and it does not block the daily COMPLETE conditions.
2. **Corporate-action adjustment methodology — SCOPED OUT.** No
   adjustment methodology exists because no adjustment data source
   exists: adjustments require corporate-action announcements, which
   are not collected anywhere in Phases 1–6. All values are computed
   on unadjusted closes with `is_adjusted=False`, stated on every
   response. Designing a methodology without adjustment data would be
   fabrication. Revisit only when a verified adjustment source exists.
3. **Activated signal rules — SCOPED OUT by design.** Rules need
   calculable indicator inputs first; there are none yet. Activation
   additionally needs a separate rule-approval decision, since signals
   are probabilistic proposals only and must never read as buy/sell
   recommendations. Empty `ACTIVATED_RULES` is the correct state
   until both conditions hold.
4. **Regime features — DATA-BLOCKED, not scoped out.** Regime
   features are derived from calculable indicator values, of which
   there are zero. This gap closes only when (a) more trading days
   arrive and produce first values, and (b) the Terms gate clears.
   It is not closed by redefinition.

## 5. COMPLETE conditions — status

| Condition | Status | Exact unblocker |
|---|---|---|
| ≥4 more trading days → first SMA(5) values in a committed run (value rows > 0) | NOT AVAILABLE | Written PSX Terms resolution permitting further dated collection, then 4+ trading days of source files with the same validation |
| Written PSX Terms resolution | OPEN | Written permission evidence, produced and verified for its exact terms (internal, non-commercial, private-database use). None exists; the user's permission side is user-owned. This run sent no PSX email and collected no market data |
| Scope gaps | DISPOSED above, except regime features (data-blocked) | Regime features: first calculable values (see row 1) |
| No VERIFIED promotion | HELD | All prices remain single-source UNVERIFIED; no indicator, price, or registry row was promoted by this run |

## 6. Verdict: PARTIALLY COMPLETE (unchanged)

The framework, tests, GET-only API, immutability guards, and live-run
bookkeeping are verified and (after the recovery-#4 loss) restored to
the exact recorded state. COMPLETE is not claimed: it requires more
trading days and written Terms resolution, neither of which exists,
plus regime features that depend on both. No value was invented, no
row was promoted, and no new market data was collected.

## 7. How Phase 4 / Phase 5 outcomes affect Phase 6 (unchanged)

- Phase 4 (PARTIALLY COMPLETE, scoped 470 universe, all UNVERIFIED)
  defines Phase 6's input scope exactly; the 26 no-price securities
  (13 rejected + 13 absent) are the `missing_data` population.
  GEM/Non-Compliant absence propagates unchanged.
- Phase 5 (PARTIALLY COMPLETE, sole blocker Terms resolution) supplies
  the single-day, single-source, UNVERIFIED price set. Phase 6's
  NOT_CALCULABLE headline is a consequence of that input, not of the
  indicator implementation.
- The Phase 4 SECP LEAP second-source route is field-scoped only and
  does not change Phase 6's input quality: committed prices remain
  single-source UNVERIFIED observations.

## 8. What changed in this run

- One new document (this file) on branch `phase-06-revisit`.
- Live DB bookkeeping restored after the recovery-#4 loss: 1
  calculation-run row, 124 error rows, 62 definitions, 62
  configurations, 0 values, 0 signal events — identical to the
  completion run's recorded state.
- No code, migration, or framework file changed. No merge to main.
  No push to any repository other than advisor (see commit record).
- Register files (`PHASE_COMPLETION_REGISTER.md`,
  `PROJECT_EXECUTION_STATE.md`, `MASTER_EXECUTION_LOG.md`) were NOT
  edited here, per instructions; the parent consolidates registers at
  the end of the revisit sequence.
