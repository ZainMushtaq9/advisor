# Portfolio Review: ew_statements_3_balanced

Report date: 2026-11-04 | Data cut-off: 2026-11-04 | Price date: 2026-11-03 | Audience: internal_research | Status: DRAFT

## Executive summary

SIMULATED portfolio ew_statements_3_balanced (equal_weight_baseline, hypothetical capital 1000000.0000 PKR, price date 2026-11-03). Holdings: HUBC: 1689.0000 units, 333138.3600 PKR; NML: 2696.0000 units, 333252.5600 PKR; OGDC: 1097.0000 units, 333082.1100 PKR See portfolio_invested and portfolio_return.

## Holdings

HUBC: 1689.0000 units, 333138.3600 PKR; NML: 2696.0000 units, 333252.5600 PKR; OGDC: 1097.0000 units, 333082.1100 PKR See portfolio_holding_count.

## Exclusions

HBL (SCREEN_NOT_RUNNABLE: Baseline scope is the statement companies; HBL has no statements loaded (Phase 15 SCREEN_NOT_RUNNABLE) and is therefore out of baseline scope, not out of the universe. HBL's quote itself is ELIGIBLE.) See portfolio_holding_count.

## Comparison

mean_variance: NOT_CALCULABLE (no validated expected returns: Phase 13 computed 0 forecasts (all 120 assessments insufficient_inputs, live forecasting abstained); no covariance matrix: 0 return observation(s) from 1 price date (at least 2 closes are needed for a single return)); rule_based_screen_pass: COMPUTED; rule_based_screen_pass: COMPUTED See portfolio_return.

## Thesis

The simulated construction follows its stated method on stored closes only. See portfolio_invested.

## Counter-thesis

One price date means no return, no covariance, and no risk-adjusted comparison exists. See portfolio_return.

## Risks

All inputs are UNVERIFIED; this is a simulation, never a real holding. See portfolio_capital.

## Uncertainty

Returns are insufficient_inputs; forecasts are abstained; user-facing values are WITHHELD. See portfolio_return.

## Methodology, sources and disclosures

Methodology: figures are pulled from stored platform rows only, as described in the template methodology above; no new market data was collected for this report. Source tables used: portfolio_sector_allocations, simulated_portfolio_holdings, simulated_portfolios. Every figure states its computation status and inherits its inputs' quality status; a figure with status insufficient_inputs or not_applicable carries its reason in the figures table, never a number. INTERNAL RESEARCH DOCUMENT — NOT INVESTMENT ADVICE. This report assembles figures already stored in the PSX Intelligence platform; it introduces no new market data. Every figure inherits its inputs' quality status (all statement, price, ratio, valuation, macro, news, ownership, forecast, risk, decision, portfolio, backtest, screen, and alert inputs in this run are UNVERIFIED unless a figure note says otherwise). Screen matches are filter results, not investment opportunities. Phase 15 user-facing values are WITHHELD and Phase 13 forecasts are abstained; neither is reintroduced here. No price target is stated anywhere in this report, and no section recommends a trade. This report is not published externally; APPROVED means internally reviewed only.

## Figures

| Figure | Value | Status | Kind | Source |
|---|---|---|---|---|
| Hypothetical capital | 1000000.0000 PKR | computed | assumption | simulated_portfolios |
| Invested value | 999473.0300 PKR | computed | deterministic_calculation | simulated_portfolio_holdings |
| Holdings | 3 holdings | computed | deterministic_calculation | simulated_portfolio_holdings |
| Portfolio return | not available | insufficient_inputs | model_output | simulated_portfolio_holdings |
| Holding HUBC | 333138.3600 PKR | computed | deterministic_calculation | simulated_portfolio_holdings |
| Holding NML | 333252.5600 PKR | computed | deterministic_calculation | simulated_portfolio_holdings |
| Holding OGDC | 333082.1100 PKR | computed | deterministic_calculation | simulated_portfolio_holdings |
| Sector OIL & GAS EXPLORATION COMPANIES invested | 333082.1100 PKR | computed | deterministic_calculation | portfolio_sector_allocations |
| Sector POWER GENERATION & DISTRIBUTION invested | 333138.3600 PKR | computed | deterministic_calculation | portfolio_sector_allocations |
| Sector TEXTILE COMPOSITE invested | 333252.5600 PKR | computed | deterministic_calculation | portfolio_sector_allocations |

## Warnings

- [not_calculable] Comparison mean_variance is NOT_CALCULABLE: no validated expected returns: Phase 13 computed 0 forecasts (all 120 assessments insufficient_inputs, live forecasting abstained); no covariance matrix: 0 return observation(s) from 1 price date (at least 2 closes are needed for a single return)
