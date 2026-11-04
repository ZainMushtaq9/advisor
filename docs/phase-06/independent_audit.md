# Phase 6 — Independent audit

Auditor: independent child subagent (depth 2), read-only — no
code, docs, database rows, or git state were changed by the
audit, and no push or merge was attempted.

## Audit verdict: PASS WITH LIMITATIONS

## Phase verdict confirmed: PARTIALLY COMPLETE is justified

The framework is verified, zero indicator values are calculable
on the single-day data, Terms remain unresolved, and Phase 5 is
correctly NOT marked complete. No finding fabricates a value,
upgrades quality, or changes the honest headline (0 calculable).

## What the auditor verified correct (evidence)

- Registry: 62 indicators, 62 unique keys; categories trend 39
  / momentum 9 / volatility 6 / risk 4 / volume 4. Coverage
  matrix: 62 rows, 0 mismatches on key/category/warm-up; every
  non-daily row exactly insufficient_warmup (444),
  missing_data (26); daily_return missing_data (470).
- Formulas match conventions, no silent mixing: EMA SMA-seeded,
  RSI/ATR/ADX Wilder-smoothed, Bollinger population std
  (independently recomputed: [10,12,14] -> 12 / 15.2659863 /
  8.7340137), VaR/ES nearest-rank, MACD alignment, ADX first
  value at bar 26 -> warm-up 27, pivots from the prior bar,
  Ichimoku Senkou stored at computation date with no +26 shift.
- Live DB (read-only): head 20261104_0005; definitions 62,
  configurations 62 (all active, version 1.0), values 0, signal
  events 0, features 0, regime observations 0; runs 1
  (phase06-coverage-2026-11-03, completed, 470 processed, 0
  written); errors 124 = missing_data 63 + insufficient_warmup
  61; market_prices still 444, all 2026-11-03, all UNVERIFIED,
  all is_adjusted=False, single source, previous_close/
  turnover/source_timestamp NULL on all 444; securities 470,
  companies 470, sectors 37, evidence 940; 26 securities with
  no price row; close range 0.80–26200, OHLC violations 0,
  zero-volume rows 0, trading_sessions 0. Triggers on all four
  output tables (UPDATE + DELETE each), none on run/error
  tables. Migration claim verified.
- Tests/lint at audit time: 109 passed, Ruff clean. Spot-checked
  test values genuinely independent hand calculations.
- API live (read-only): coverage 200 -> 470/62/0; sma_5 reasons
  exact; daily_return missing_data 470; OGDC 200 -> 1 bar, 0
  calculable, scope note present; bad as_of, bad indicator_key
  and limit=0 all 422. All four endpoints GET-only; 503
  without DATABASE_URL tested.
- Scope discipline: no KSE-100 / full-market / VERIFIED /
  Terms-clearance claim anywhere in Phase 6 code, docs, or API
  responses — every such mention is an explicit negation.
  No publication/redistribution/commercial-use path; no
  network imports; no LLM-calculated numbers; ACTIVATED_RULES
  empty; no buy/sell language. No new tables. No new external
  PSX collection; no PSX email sent.

## Findings and coordinator dispositions (ALL FIXED, none merely accepted)

- H1 — Phase 6 work was uncommitted, contradicting the record.
  FIXED: committed locally on phase-06-technical-analytics
  (see completion_report.md for SHAs). Still no push, no merge.
- H2 — Conflicted-only series collapsed to missing_data in the
  runner (load_series filtered before coverage saw the rows).
  FIXED: load_series returns the flagged ticker set; coverage
  reports conflicted_input for flagged tickers (with or without
  usable bars); API endpoints pass the flag through; tests
  added (coverage flag paths + fake-session load_series test).
- H3 — Correction propagation documented but not implemented
  (hardcoded config_version 1.0, no deactivation; values API
  omitted indicator_key). FIXED: get_active_config deactivates
  superseded actives and creates a bumped-version config;
  values items now carry indicator_key, configuration id,
  config_version and parameters.
- H4 — Re-run not idempotent for run/error rows (no unique
  run_key, no existence check). FIXED: a completed run for the
  same run_key is never duplicated — a second --commit
  reports already_recorded and writes nothing. Verified live:
  second commit for 2026-11-03 wrote 0 rows; DB stayed 1 run /
  124 errors / 0 values.
- M1 — Values items omitted indicator_key. FIXED (see H3).
- M2 — Market coverage as_of was null with no parameter,
  contradicting the API doc. FIXED: returns the effective
  as-of (latest price date). Verified live: 2026-11-03.
- M3 — Zero-price bars crashed coverage (drawdown division).
  FIXED: zero/non-positive running maximum raises
  degenerate_input. Test added.
- M4 — Stochastic raised on any historical zero-range window.
  FIXED: only the windows feeding %K/%D are evaluated.
  Tests added (flat early + clean final computes; flat final
  raises). One pre-existing test expectation (a 3-bar case
  that raised degenerate before the warm-up check) was
  corrected to a 4-bar degenerate case — the old expectation
  was an artifact of loop order, not a documented convention.
- M5 — Frontend "none yet" claims were static text, never
  fetched. FIXED: page fetches values/signals totals and the
  API scope/signal notes; ticker error split into "Unknown
  ticker" (404) vs "Backend unavailable".
- M6 — Aggregation doc falsely claimed one day cannot form a
  partial week/month, and said Monday–Friday while code uses
  ISO weeks. FIXED in code comment and doc: ISO year-weeks
  (Monday–Sunday); one day forms one partial weekly and one
  partial monthly bar.
- M7 — Aggregation mishandled missing OHLC (TypeError / silent
  None). FIXED: missing OHLC raises InsufficientData
  missing_data. Test added.
- M8 — Daily_return unblocker overstated ("verified"
  previous_close). FIXED: "a present previous_close (value
  would remain UNVERIFIED on single-source data)".
- M9 — CLI bad --as-of printed a traceback, exit 1, against
  the documented exit 2. FIXED: clean message, exit 2.
  Verified live.
- M10 — Architecture diagram implied a signal write path that
  does not exist. FIXED: labelled as the future path.
- L1 — Fibonacci header listed 0%/100% as levels. FIXED: five
  intermediate levels only; endpoints are the swing itself.
- L2 — VaR/ES tie wording overstated. FIXED: rank rule stated
  precisely (ceil(0.05*n); ES = mean of worst rank returns).
- L3 — ADX zero-TR case undocumented. FIXED: documented
  (DX = 0 when smoothed TR is 0).
- L4 — MFI grouped under Wilder smoothing. FIXED: MFI sums
  flows, no Wilder smoothing.
- L5 — Ichimoku Chikou warm-up 26 unexplained. FIXED:
  conservative convention borrowed from Kijun, stated.
- L6 — (a) seed_definitions refreshed only on formula changes.
  FIXED: refreshes on parameter/warm-up changes too.
  (b) value source_key from the full unsliced series. FIXED:
  from as-of-sliced bars only.
- L7 — Values pagination ordering had no indicator tiebreak.
  FIXED: ordered by date desc, ticker, indicator_key.
- L8 — "Full-market call" phrasing collided with the
  no-full-market rule. FIXED: "full-coverage call".
- L9 — Section 2 carried the evidence UNVERIFIED attribution
  without a traceable column. FIXED: note added (status
  carried from the Phase 4 import record; registry_evidence
  carries source linkage, not a quality column).
- L10 — Frontend doc overstated the signal note rendering.
  FIXED: page now renders the API note (see M5).
- L11 — Run-report "444-bar warm-up group" ambiguous. FIXED:
  "444 securities with 1 bar each".

## Post-fix re-verification

- Backend suite: 114 passed, 0 failed (was 109; +5 audit-fix
  tests, 1 corrected expectation). Ruff clean.
- Frontend: typecheck, lint, build (12 routes incl.
  /indicators), Vitest 11 passed.
- Live: coverage as_of 2026-11-03; values 0; signals 0;
  re-run guard verified (already_recorded, 0 writes);
  CLI bad as-of exit 2 with a clean message.
- Auditor's conditions: (1) H1 resolved by the local commit;
  (2) H2–H4 fixed, M1–M2 fixed before any value exists;
  (3) M3–M10 and LOW items fixed, including the one-line
  doc/code mismatches; (4) Phase 5 NOT marked complete,
  Terms position unchanged (unresolved, user handling later),
  no new collection, local private use only.

## Conditions carried forward

- Do NOT push (standing credential failure + keep-local
  choice) and do NOT merge to main (needs separate approval).
- Do NOT mark Phase 5 complete on the basis of Phase 6.
- Do NOT claim Terms clearance, KSE-100, full-market, or
  VERIFIED status on any Phase 6 output.
