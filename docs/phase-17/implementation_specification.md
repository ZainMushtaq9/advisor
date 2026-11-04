# Phase 17 — Implementation specification

## Brief source

Playbook text extract, lines 1329–1387 (Phase 17: backtesting,
paper trading and strategy evaluation). The brief's phase-transition
text (auto-start the next phase, update all state files) is NOT
followed: the parent brief for this run requires stopping after the
Phase 17 report and forbids register edits, and the parent brief
governs over brief boilerplate.

## Architecture

```
backend/app/services/backtesting/
  __init__.py   strategy registry (5 strategies), production window,
                execution assumptions, metric minima
  metrics.py    pure Decimal metric functions + assess_metric gating
  paper.py      next-eligible-price rule, order lifecycle, ledger
                derivation, cost model
  bias.py       pure bias-audit checks over runner-built evidence
  runner.py     DB reads -> strategies, runs, metrics, ledger, bias
backend/app/models/backtesting.py
  backtest_strategies, backtest_runs, backtest_metrics,
  paper_orders, paper_ledger_entries, backtest_bias_reports
scripts/run_backtesting.py   --dry-run (default) / --commit
backend/app/api/v1/endpoints/backtesting.py   GET-only (6 routes)
database/migrations/versions/20261104_0014_phase_17_backtesting.py
```

## Production truth (derived live from the database, not assumed)

- Price dates in the window: exactly one (2026-11-03).
- Return intervals in the window: zero.
- Previous closes present: zero, so no return series exists at all.
- Phase 15 user-facing values: all WITHHELD, so no
  decision-driven paper order may be created.
- Prices after 2026-11-03: none, so no paper order could fill.

## Consequences (all enforced by gating, not by convention)

- Every production run is NOT_RUNNABLE with its reason stored.
- Every return-based metric is insufficient_inputs, except
  benchmark_relative_return, which is not_applicable (no benchmark
  series is loaded at all).
- The paper ledger IS computed: opening positions, opening cash
  (capital minus recomputed holdings total), and a valuation
  snapshot, all dated 2026-11-03, all labelled SIMULATION.
- Paper orders: zero production rows. The lifecycle engine exists
  and is fixture-tested; it is not fed production orders.
- Bias: seven checks, each with evidence; disclosed biases are
  findings, not hidden adjustments.

## What this phase does NOT do

- No price series is invented, extended, or interpolated.
- No single-day snapshot is presented as a backtest result.
- No SBP policy rate is used as a risk-free rate.
- No cost rate is invented: fees/taxes/slippage are UNVALIDATED
  assumption parameters, and production cost sensitivity is
  not_applicable (zero trades).
- No execution path exists: proven by a test scanning application
  source for execution identifiers (0 hits) and asserting the
  backtesting endpoint carries only GET routes.
- No Phase 3 table is reused or altered; Phase 3 portfolios stay
  at 0 rows.
- No register file is edited by this run (parent consolidates).
