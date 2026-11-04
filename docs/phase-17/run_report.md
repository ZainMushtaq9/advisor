# Phase 17 — Run report (2026-11-04)

## Verdict: PARTIALLY COMPLETE

The backtesting engine, strategy registry, paper ledger, and bias
audit are complete and independently verified. No production
backtest is runnable: the window holds a single price observation
(2026-11-03), hence zero return intervals. Nothing is claimed
as done that is not evidenced.

## DB counts before / after

| Table | Before | After |
|---|---|---|
| backtest_strategies | 0 | 5 |
| backtest_runs | 0 | 5 (all NOT_RUNNABLE) |
| backtest_metrics | 0 | 55 (0 computed, 50 insufficient_inputs, 5 not_applicable) |
| paper_orders | 0 | 0 (intentionally) |
| paper_ledger_entries | 0 | 13 (7 positions + 3 cash + 3 valuations) |
| backtest_bias_reports | 0 | 7 |
| Migration head | 20261104_0013 | 20261104_0014 |

Prior rows untouched: statements 88, prices 444, decisions 4,
simulated portfolios 3, Phase 3 portfolios 0.

## What ran vs what did not

- Ran (computed): paper ledger re-derivation for all 3 Phase 16
  simulated portfolios; every valuation reconciles to PKR
  1,000,000.00 exactly; bias audit over live evidence.
- Did not run (NOT_RUNNABLE, with reasons): all 5 strategy
  backtests over 2026-11-03 → 2026-11-03 (zero return intervals).
- Did not compute (with reasons): all 55 metric rows; no
  benchmark-relative return (no benchmark series); no Sharpe /
  Sortino (no validated risk-free series); no cost sensitivity
  in production (zero trades, UNVALIDATED rates).
- Not generated (by rule): paper orders — Phase 15 user-facing
  values are all WITHHELD and no price exists after 2026-11-03.

## Tests and live checks

- New tests: 13 passed (pure: metrics, gating, no-look-ahead,
  ledger reconciliation, costs, bias, registry, no-execution
  scan, GET-only endpoints).
- Full backend suite: 260 passed, 0 failed (247 prior + 13 new).
- Ruff check + format clean on all new/changed files.
- Live API: strategies 200 (5), runs 200 (5), bias 200 (7),
  status 200, metrics 200 (11 per run), ledger 200 (4 for the
  balanced portfolio), unknown portfolio 404, unknown run 404.
- Idempotency proven: second --commit wrote 0 new rows.
- Audit corrections during this run: 4 ruff findings fixed
  (unused imports, unused variable, long line); multi-name
  strategy series corrected (no single price series exists for
  a multi-name strategy, so closes is empty rather than a
  meaningless cross-ticker minimum); survivorship evidence now
  uses the live DELISTED query instead of a hardcoded empty list.

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has no
backtest position and no paper order: its CY2025 statements are
not loaded (PDF blocked at download; live-browser download runs
separately). It appears in the ledger evidence only as a priced
security (2026-11-03 close) excluded from rule-based portfolios
(Phase 15 SCREEN_NOT_RUNNABLE). A Phase 7 load plus Phase 17
re-run adds HBL's evidence without redesign.

## Remaining blockers (exact unblockers)

1. Runnable backtests — more trading days of price data (Phase 5
   Terms-gated): 2 closes unlock total return, CAGR, max
   drawdown, win rate; 30 returns unlock volatility, Sharpe,
   Sortino; 20 returns unlock tail loss.
2. Benchmark-relative return — a loaded benchmark series
   (e.g. KSE-100).
3. Sharpe/Sortino — a validated risk-free series (T-bill rates;
   the SBP policy rate is not one).
4. Cost sensitivity in production — validated fee/tax/slippage
   sources plus production trades.
5. HBL coverage — live-browser HBL CY2025 PDF download, then a
   Phase 7 load, then a Phase 17 re-run.
6. Wider-company coverage — Phase 7 expansion beyond the
   3-company sample.
7. VERIFIED promotion — H1 second agreeing source including an
   official source; everything stays UNVERIFIED until then.
