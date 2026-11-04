# Portfolio Review: rule_screen_pass_conservative

Report date: 2026-11-04 | Data cut-off: 2026-11-04 | Price date: 2026-11-03 | Audience: internal_research | Status: DRAFT

## Executive summary

SIMULATED portfolio rule_screen_pass_conservative (rule_based_screen_pass, hypothetical capital 1000000.0000 PKR, price date 2026-11-03). Holdings: HUBC: 2281.0000 units, 449904.4400 PKR; OGDC: 1482.0000 units, 449979.6600 PKR See portfolio_invested and portfolio_return.

## Holdings

HUBC: 2281.0000 units, 449904.4400 PKR; OGDC: 1482.0000 units, 449979.6600 PKR See portfolio_holding_count.

## Exclusions

HBL (SCREEN_NOT_RUNNABLE: Phase 15 screening is not SCREEN_PASS; gate reasons: {'gates': ['no_statements', 'too_few_dimensions']}.); NML (SCREEN_FAIL: Phase 15 screening failed; gate reasons: {'gates': ['stale_latest_statement', 'publication_date_unknown', 'valuation_publication_unknown']}.) See portfolio_holding_count.

## Comparison

rule_based_screen_pass: COMPUTED See portfolio_return.

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
| Invested value | 899884.1000 PKR | computed | deterministic_calculation | simulated_portfolio_holdings |
| Holdings | 2 holdings | computed | deterministic_calculation | simulated_portfolio_holdings |
| Portfolio return | not available | insufficient_inputs | model_output | simulated_portfolio_holdings |
| Holding HUBC | 449904.4400 PKR | computed | deterministic_calculation | simulated_portfolio_holdings |
| Holding OGDC | 449979.6600 PKR | computed | deterministic_calculation | simulated_portfolio_holdings |
| Sector OIL & GAS EXPLORATION COMPANIES invested | 449979.6600 PKR | computed | deterministic_calculation | portfolio_sector_allocations |
| Sector POWER GENERATION & DISTRIBUTION invested | 449904.4400 PKR | computed | deterministic_calculation | portfolio_sector_allocations |
