# Phase 8 — Ratio dictionary v1.0

Calculation version `1.0`. All statement values are normalised to PKR
(thousands × 1,000) except EPS rows (rupees per share). Ratios are
dimensionless unless the unit says otherwise. Every value inherits
the lowest input quality: all production inputs are UNVERIFIED, so
every Phase 8 output is UNVERIFIED. A NULL value row means
NOT_CALCULABLE — never a guessed zero.

## Conventions (binding)

- **Period identity.** A period is (statement_type, period_start,
  period_end, reporting_frequency, statement_scope). Rows are never
  matched by period_end alone: NML and OGDC both carry a quarterly
  column and a cumulative column sharing one period_end.
- **No TTM, no annualisation.** A trailing twelve months needs a
  full-year flow minus a prior interim flow plus the current interim
  flow; no full-year income row exists for NML or OGDC. Interim
  ratios carry their exact periods (HUBC FY2026 annual; NML nine
  months to 31 Mar 2025; OGDC six months to 31 Dec 2025).
- **Averages.** Two-point averages of the current and prior
  balance-sheet dates. NML's prior point is the 30 Jun 2024
  comparative column (not the flow start); the average is labelled
  an interim average.
- **Days.** Exact inclusive calendar days in the current flow period
  (HUBC 365, NML 274, OGDC 184), computed from the dates.
- **Signs.** Cost, finance-cost, capex, and dividend lines are
  negative as printed; formulas take absolute values where stated.
- **Negative earnings.** A negative PAT produces negative margins /
  returns (reported, flagged), not NOT_CALCULABLE. A growth rate
  that flips sign is computed and flagged `sign_change`.
- **Derived inputs (exact arithmetic from printed lines, flagged).**
  OGDC cost = sales_net − gross_profit (no printed cost line).
  HUBC total_liabilities = total_assets − total_equity (no printed
  total-liabilities line). Payables days use total
  trade_and_other_payables as printed (no trade-only split), so they
  are upper bounds.

## Metrics

### Profitability

| Key | Formula | Unit |
|---|---|---|
| gross_margin | gross_profit / revenue | ratio |
| operating_margin | profit_from_operations / revenue | ratio |
| net_margin | profit_after_tax / revenue | ratio |
| roa | profit_after_tax / average total_assets | ratio |
| roe_total | profit_after_tax / average total_equity | ratio |
| roe_owners | profit_attributable_to_owners / average equity_attributable_to_owners | ratio |
| roce | profit_from_operations / average capital_employed (total_equity + interest-bearing debt) | ratio |
| roic | NOT_CALCULABLE in v1.0 (see below) | ratio |

### Liquidity

| Key | Formula | Unit |
|---|---|---|
| current_ratio | current_assets / current_liabilities | x |
| quick_ratio | (current_assets − inventory) / current_liabilities; inventory = stock_in_trade + stores/spares | x |
| cash_ratio | cash_and_bank_balances / current_liabilities | x |

### Leverage

| Key | Formula | Unit |
|---|---|---|
| debt_to_assets | total_liabilities / total_assets | ratio |
| debt_to_equity | total_liabilities / total_equity | ratio |
| ib_debt_to_equity | interest_bearing_debt / total_equity | ratio |
| interest_coverage | profit_from_operations / absolute finance_cost | x |

Interest-bearing debt: HUBC = long-term loans + long-term leases +
current maturities + short-term borrowings; NML = long-term
financing + lease liabilities + current portion + short-term
borrowings; OGDC = lease liabilities only.

### Efficiency

| Key | Formula | Unit |
|---|---|---|
| receivables_days | average trade_debts / revenue × period_days | days |
| inventory_days | average inventory / cost × period_days | days |
| payables_days | average trade_and_other_payables / cost × period_days | days |
| receivables_turnover | revenue / average trade_debts | x |

### Growth (same-length comparison only)

| Key | Formula | Unit |
|---|---|---|
| revenue_growth | (revenue − prior revenue) / prior revenue | ratio |
| pat_growth | (pat − prior pat) / prior pat | ratio |
| eps_growth | (eps − prior eps) / prior eps | ratio |
| assets_growth | (total_assets current BS − prior BS) / prior BS | ratio |
| equity_growth | (total_equity current BS − prior BS) / prior BS | ratio |

### Cash flow

| Key | Formula | Unit |
|---|---|---|
| ocf | net cash from operating activities, as printed | PKR |
| fcf | net_operating + capex (capex negative as printed) | PKR |
| cash_conversion | net_operating / profit_after_tax | ratio |
| dividend_cash_coverage | net_operating / absolute dividends_paid | x |
| accruals | profit_after_tax − net_operating | PKR |

### Earnings quality

| Key | Formula | Unit |
|---|---|---|
| accruals_to_pat | accruals / absolute profit_after_tax | ratio |
| gross_margin_change_pp | gross_margin current − gross_margin prior | pp |
| receivables_divergence_pp | trade_debts growth minus revenue growth | pp |
| inventory_growth_pct | (inventory current BS − prior BS) / prior BS | ratio |

Exceptional items are NOT_ASSESSED for all three companies: no
exceptional-item line exists in the extracted statements, and zero
is never substituted.

### Market multiples (all NOT_CALCULABLE in v1.0)

| Key | Reason |
|---|---|
| pe_ratio | Single unadjusted close (2026-11-03); no corporate-action adjustment methodology; price date not aligned to statement publication; interim EPS for NML/OGDC. |
| pb_ratio | Book value per share needs a share count, which no extracted statement provides; same price limitations. |
| dividend_yield | Needs dividends per share (needs a share count) and an aligned adjusted price; neither is available. |

## NOT_CALCULABLE catalog (this run)

- **roic, all companies.** NOPAT needs a validated tax allocation;
  HUBC operating profit includes post-tax associate earnings, so a
  group-rate NOPAT would misstate. Formula reserved, not estimated.
- **operating_margin, roce, OGDC.** No operating-profit line in the
  extracted OGDC statements.
- **roe_owners, NML and OGDC.** No owners-attributable profit line.
- **interest_coverage, OGDC — not_applicable by structure** (distinct
  from missing data): no finance-cost line and no interest-bearing
  loans in the extracted statements (lease liabilities only).
- **pe_ratio, pb_ratio, dividend_yield, all companies.** See above.
- **TTM variants of every flow ratio, NML and OGDC.** Full-year
  flows not in the statement set.
- **Market-cap and per-share balance-sheet ratios, all companies.**
  No share-count data.
