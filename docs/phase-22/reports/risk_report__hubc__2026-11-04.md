# Risk Report: The Hub Power Company Limited (HUBC)

Report date: 2026-11-04 | Data cut-off: 2026-11-04 | Price date: 2026-11-03 | Audience: internal_research | Status: DRAFT

## Executive summary

Risk report for The Hub Power Company Limited (HUBC). Risk rows: 13; flags: 2. See risk_volume_liquidity_tier.

## Risk metrics

Stored risk metrics are in the figures table; see risk_volume_liquidity_tier.

## Controls

drawdown_warning_pct: {'threshold': '-10', 'unit': 'pct_or_shares'}; min_daily_volume_shares: {'threshold': '50000', 'unit': 'pct_or_shares'}; min_diversification_names: {'threshold': '3', 'unit': 'pct_or_shares'}; sector_cap_pct: {'threshold': '50', 'unit': 'pct_or_shares'}; single_name_cap_pct: {'threshold': '25', 'unit': 'pct_or_shares'} See control_single_name_cap_pct_SIMULATED_PORTFOLIO.

## Stress scenarios

Stress impacts are simulation arithmetic on stored closes only. See stress_commodity_oil_minus_10.

## Thesis

Risk is described from stored rows only; no new risk number is introduced. See risk_volume_liquidity_tier.

## Counter-thesis

Series risk metrics are unavailable on one price date, so this report cannot speak to volatility, beta, or drawdown. See risk_volatility.

## Uncertainty

All inputs are UNVERIFIED; flags are review-only. See risk_volume_liquidity_tier.

## Methodology, sources and disclosures

Methodology: figures are pulled from stored platform rows only, as described in the template methodology above; no new market data was collected for this report. Source tables used: risk_control_checks, risk_metric_values, stress_results. Every figure states its computation status and inherits its inputs' quality status; a figure with status insufficient_inputs or not_applicable carries its reason in the figures table, never a number. INTERNAL RESEARCH DOCUMENT — NOT INVESTMENT ADVICE. This report assembles figures already stored in the PSX Intelligence platform; it introduces no new market data. Every figure inherits its inputs' quality status (all statement, price, ratio, valuation, macro, news, ownership, forecast, risk, decision, portfolio, backtest, screen, and alert inputs in this run are UNVERIFIED unless a figure note says otherwise). Screen matches are filter results, not investment opportunities. Phase 15 user-facing values are WITHHELD and Phase 13 forecasts are abstained; neither is reintroduced here. No price target is stated anywhere in this report, and no section recommends a trade. This report is not published externally; APPROVED means internally reviewed only.

## Figures

| Figure | Value | Status | Kind | Source |
|---|---|---|---|---|
| Risk beta_vs_benchmark | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk correlation_vs_market | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk downside_deviation | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk es95_hist | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk gap_risk | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk largest_holder_share | 38.270000 | computed | model_output | risk_metric_values |
| Risk max_drawdown | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk rate_sensitivity_coeff | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk top3_holder_share | 69.450000 | computed | model_output | risk_metric_values |
| Risk turnover_liquidity | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk var95_hist | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk volatility | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk volume_liquidity_tier | 3218965.000000 | computed | model_output | risk_metric_values |
| Control single_name_cap_pct (SIMULATED_PORTFOLIO) | breach | computed | model_output | risk_control_checks |
| Control sector_cap_pct (SIMULATED_PORTFOLIO) | pass | computed | model_output | risk_control_checks |
| Control drawdown_warning_pct (SIMULATED_PORTFOLIO) | blocked | computed | model_output | risk_control_checks |
| Control min_diversification_names (SIMULATED_PORTFOLIO) | pass | computed | model_output | risk_control_checks |
| Control min_daily_volume_shares (HUBC) | pass | computed | model_output | risk_control_checks |
| Control min_daily_volume_shares (NML) | pass | computed | model_output | risk_control_checks |
| Control min_daily_volume_shares (OGDC) | pass | computed | model_output | risk_control_checks |
| Stress commodity_oil_minus_10 | not available | insufficient_inputs | model_output | stress_results |
| Stress fx_pkr_minus_10 | not available | insufficient_inputs | model_output | stress_results |
| Stress fx_pkr_minus_10 | not available | insufficient_inputs | model_output | stress_results |
| Stress idiosyncratic_minus_20 | -6.666667 percent | computed | model_output | stress_results |
| Stress idiosyncratic_minus_20 | -6.666667 percent | computed | model_output | stress_results |
| Stress idiosyncratic_minus_20 | -6.666667 percent | computed | model_output | stress_results |
| Stress market_minus_10 | -10.000000 percent | computed | model_output | stress_results |
| Stress rate_plus_100bps | not available | insufficient_inputs | model_output | stress_results |
| Stress rate_plus_100bps | not available | insufficient_inputs | model_output | stress_results |
| Stress rate_plus_100bps | not available | insufficient_inputs | model_output | stress_results |

## Warnings

- [risk_flag] warning_low_cash_conversion (info): Review-only flag from Phase 8; not a fraud, default or solvency conclusion.
- [risk_flag] warning_receivables_growing_faster_than_revenue (info): Review-only flag from Phase 8; not a fraud, default or solvency conclusion.
