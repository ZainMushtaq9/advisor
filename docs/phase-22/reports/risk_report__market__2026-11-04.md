# Risk Report: Market

Report date: 2026-11-04 | Data cut-off: 2026-11-04 | Price date: 2026-11-03 | Audience: internal_research | Status: DRAFT

## Executive summary

Risk report for Market. Risk rows: 43; flags: 0; controls: 5; stress scenarios: 10. See risk_forecast_abstention_rate and risk_priced_coverage.

## Risk metrics

Stored risk metrics are in the figures table; see risk_priced_coverage.

## Controls

drawdown_warning_pct: {'threshold': '-10', 'unit': 'pct_or_shares'}; min_daily_volume_shares: {'threshold': '50000', 'unit': 'pct_or_shares'}; min_diversification_names: {'threshold': '3', 'unit': 'pct_or_shares'}; sector_cap_pct: {'threshold': '50', 'unit': 'pct_or_shares'}; single_name_cap_pct: {'threshold': '25', 'unit': 'pct_or_shares'} See control_single_name_cap_pct_SIMULATED_PORTFOLIO.

## Stress scenarios

Stress impacts are simulation arithmetic on stored closes only. See stress_commodity_oil_minus_10.

## Thesis

Risk is described from stored rows only; no new risk number is introduced. See risk_forecast_abstention_rate.

## Counter-thesis

Series risk metrics are unavailable on one price date, so this report cannot speak to volatility, beta, or drawdown. See risk_technical_coverage_rate.

## Uncertainty

All inputs are UNVERIFIED; flags are review-only. See risk_forecast_abstention_rate.

## Methodology, sources and disclosures

Methodology: figures are pulled from stored platform rows only, as described in the template methodology above; no new market data was collected for this report. Source tables used: risk_control_checks, risk_metric_values, stress_results. Every figure states its computation status and inherits its inputs' quality status; a figure with status insufficient_inputs or not_applicable carries its reason in the figures table, never a number. INTERNAL RESEARCH DOCUMENT — NOT INVESTMENT ADVICE. This report assembles figures already stored in the PSX Intelligence platform; it introduces no new market data. Every figure inherits its inputs' quality status (all statement, price, ratio, valuation, macro, news, ownership, forecast, risk, decision, portfolio, backtest, screen, and alert inputs in this run are UNVERIFIED unless a figure note says otherwise). Screen matches are filter results, not investment opportunities. Phase 15 user-facing values are WITHHELD and Phase 13 forecasts are abstained; neither is reintroduced here. No price target is stated anywhere in this report, and no section recommends a trade. This report is not published externally; APPROVED means internally reviewed only.

## Figures

| Figure | Value | Status | Kind | Source |
|---|---|---|---|---|
| Risk forecast_abstention_rate | 100.000000 | computed | model_output | risk_metric_values |
| Risk input_drift | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk priced_coverage | 94.468085 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 96.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 93.750000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 83.333333 | computed | model_output | risk_metric_values |
| Risk sector_participation | 96.153846 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 86.206897 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 66.666667 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 94.117647 | computed | model_output | risk_metric_values |
| Risk sector_participation | 95.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 80.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 79.166667 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 95.454545 | computed | model_output | risk_metric_values |
| Risk sector_participation | 84.848485 | computed | model_output | risk_metric_values |
| Risk sector_participation | 94.117647 | computed | model_output | risk_metric_values |
| Risk sector_participation | 83.333333 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_participation | 100.000000 | computed | model_output | risk_metric_values |
| Risk sector_volume_hhi | not available | insufficient_inputs | model_output | risk_metric_values |
| Risk technical_coverage_rate | 0.000000 | computed | model_output | risk_metric_values |
| Risk top10_volume_share | 49.249694 | computed | model_output | risk_metric_values |
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
