# Phase 17 — Backtest methodology and metric minima

## No-look-ahead

- A signal dated D may only fill at the first observed close
  strictly after D (next eligible price rule). A signal with no
  later observed price can never fill.
- A backtest window may only use prices and publications dated
  on or before the simulated decision date (2026-11-04).
- Walk-forward discipline is implemented (chronological folds,
  never shuffled) and fixture-tested in Phase 13; Phase 17 has no
  production fold because no series yields one.

## Metric minima (enforced by assess_metric)

| Metric | Minimum | Production (window 2026-11-03) |
|---|---|---|
| total_return | 2 closes | 1 close / 0 for multi-name -> insufficient |
| cagr | 2 closes + positive years | window length 0 days -> insufficient |
| volatility | 30 returns | 0 returns -> insufficient |
| sharpe_ratio | 30 returns + risk-free series | 0 returns, no risk-free -> insufficient |
| sortino_ratio | 30 returns + risk-free series | 0 returns, no risk-free -> insufficient |
| max_drawdown | 2 closes | insufficient |
| win_rate | 1 return | 0 returns -> insufficient |
| turnover | 2 snapshots + trades | 1 snapshot, 0 trades -> insufficient |
| exposure (window-average) | 2 snapshots | 1 snapshot -> insufficient |
| benchmark_relative_return | benchmark series exists | none loaded -> not_applicable |
| tail_loss | 20 returns | 0 returns -> insufficient |

## What unlocks each metric

- 1 more trading day (2 closes): total_return, cagr, max_drawdown,
  win_rate become computable; turnover/exposure need a second
  valuation snapshot.
- 30 returns: volatility, Sharpe, Sortino (Sharpe/Sortino also
  need a validated risk-free series, e.g. T-bill rates).
- 20 returns: tail_loss.
- A loaded benchmark series: benchmark_relative_return.
- A validated fee/tax/slippage source plus trades: cost-adjusted
  metrics and cost sensitivity.

## Formulas

Simple returns; total return = end/start - 1; CAGR annualised
from total return; volatility = sample stdev x sqrt(252);
Sharpe = excess mean / stdev x sqrt(252); Sortino = excess mean /
downside deviation x sqrt(252); max drawdown = largest
peak-to-trough fall; win rate = share of positive returns;
turnover = traded value / average portfolio value; exposure =
mean invested / capital; tail loss = mean of worst 5% of returns.
All in Decimal; None is never converted to zero.
