# Phase 7 — Taxonomy and Mapping Register (v1.0, sample run)

Three layers, never collapsed: (1) the company's ORIGINAL label as
printed, (2) the canonical key used for comparison, (3) the
normalized value in PKR (reported_unit × scale). A company-specific
item is never forced into a wrong canonical bucket; unknown items
stay preserved with mapping_status `pending` and are NOT silently
dropped from the load (they load with their original label and a
`pending` key note).

## Canonical keys (balance sheet)

`total_assets`, `non_current_assets_total`, `current_assets_total`,
`property_plant_equipment`, `intangibles`, `long_term_investments`,
`long_term_deposits`, `stores_spares_consumables`, `stock_in_trade`,
`trade_debts`, `loans_advances`,
`deposits_prepayments_other_receivables`, `short_term_investments`,
`cash_and_bank_balances`, `share_capital_issued`, `share_premium`,
`operation_maintenance_reserve`, `unappropriated_profit`,
`equity_attributable_owners`, `non_controlling_interests`,
`total_equity`, `long_term_loans`, `long_term_lease_liabilities`,
`deferred_taxation`, `non_current_liabilities_total`,
`trade_and_other_payables`, `provision_for_taxation`,
`unclaimed_dividend`, `unpaid_dividend`, `interest_markup_accrued`,
`refund_liability`, `short_term_borrowings`,
`current_maturity_long_term_loans`,
`current_maturity_lease_liabilities`, `current_liabilities_total`,
`total_liabilities`, `total_equity_and_liabilities`.

## Canonical keys (profit or loss)

`revenue`, `gross_profit`, `operating_profit`,
`profit_before_tax`, `profit_after_tax`, `eps_basic`. (Full P&L
line detail beyond these headlines is loaded with original labels
and `pending` canonical keys where no safe mapping exists.)

## HUBC — Consolidated SFP, PDF p.277 (Rs. '000s)

Original label → canonical key. Subtotal rows print as bare numbers
in text extraction; their position (after a section's last item, on
the same page) identifies them — flagged `subtotal_position_inferred`
in the load, never presented as a printed label.

| Original label | Canonical key |
|---|---|
| Property, plant and equipment | property_plant_equipment |
| Intangibles | intangibles |
| Long term investments | long_term_investments |
| Long term deposits | long_term_deposits |
| (section total, bare number) | non_current_assets_total |
| Stores, spares and consumables | stores_spares_consumables |
| Stock-in-trade | stock_in_trade |
| Trade debts | trade_debts |
| Loans and advances | loans_advances |
| Deposits, prepayments and other receivables | deposits_prepayments_other_receivables |
| Short term investments | short_term_investments |
| Cash and bank balances | cash_and_bank_balances |
| (section total, bare number) | current_assets_total |
| TOTAL ASSETS | total_assets |
| Issued, subscribed and paid-up (Share Capital) | share_capital_issued |
| Share premium | share_premium |
| Operation and maintenance reserve | operation_maintenance_reserve |
| Unappropriated profit | unappropriated_profit |
| ATTRIBUTABLE TO OWNERS OF THE HOLDING COMPANY | equity_attributable_owners |
| NON-CONTROLLING INTERESTS | non_controlling_interests |
| (equity section total, bare number) | total_equity |
| Long term loans | long_term_loans |
| Long term lease liabilities | long_term_lease_liabilities |
| Deferred taxation | deferred_taxation |
| (section total, bare number) | non_current_liabilities_total |
| Trade and other payables | trade_and_other_payables |
| Provision for taxation | provision_for_taxation |
| Unclaimed dividend | unclaimed_dividend |
| Unpaid dividend | unpaid_dividend |
| Interest / mark-up accrued | interest_markup_accrued |
| Refund liability | refund_liability |
| Short term borrowings | short_term_borrowings |
| Current maturity of long term loans | current_maturity_long_term_loans |
| Current maturity of long term lease liabilities | current_maturity_lease_liabilities |
| (section total, bare number) | current_liabilities_total |
| TOTAL EQUITY AND LIABILITIES | total_equity_and_liabilities |

Balance identity used: total_assets == total_equity +
non_current_liabilities_total + current_liabilities_total, where
total_equity already INCLUDES non-controlling interests (as printed).
2026: 258,007,509 + 97,833,209 + 66,722,726 = 422,563,444 ✓.
2025: 243,921,905 + 107,689,918 + 63,110,364 = 414,722,187 ✓.
Note: HUBC prints "Short term investments 2025: -" → NULL, not 0.

## NML — Consolidated condensed interim SFP, PDF pp.35–36 (Rupees in thousand)

| Original label | Canonical key |
|---|---|
| Issued, subscribed and paid-up share capital | share_capital_issued |
| Reserves | reserves (no finer split printed on the face; note-level detail pending) |
| Equity attributable to equity holders of the Holding Company | equity_attributable_owners |
| Non-controlling interest | non_controlling_interests |
| Total equity | total_equity |
| Long term financing - secured | long_term_financing (CORRECTED 2026-11-04: was `long_term_loans`, which collided with the asset-side row below; the line-item grain (statement_id, line_item_key) is unique, so liability and asset rows must have distinct keys) |
| Lease liabilities | long_term_lease_liabilities |
| Security deposits | security_deposits (pending canonical bucket — preserved, not forced) |
| Retirement benefit obligation | retirement_benefit_obligation (pending) |
| Deferred liabilities | deferred_liabilities (pending) |
| (non-current section total, bare number) | non_current_liabilities_total |
| Trade and other payables | trade_and_other_payables |
| Accrued mark-up | interest_markup_accrued |
| Short term borrowings | short_term_borrowings |
| Current portion of non-current liabilities | current_maturity_non_current_liabilities (pending) |
| Unclaimed dividend | unclaimed_dividend |
| Provision for taxation and levy - net | provision_for_taxation |
| (current section total, bare number) | current_liabilities_total |
| TOTAL LIABILITIES | total_liabilities |
| TOTAL EQUITY AND LIABILITIES | total_equity_and_liabilities |
| Property, plant and equipment | property_plant_equipment |
| Intangible Assets | intangibles |
| Right-of-use assets | right_of_use_assets (pending) |
| Long term investments | long_term_investments |
| Long term loans (asset side) | long_term_loans_asset (CORRECTED 2026-11-04: distinct from `long_term_financing` above) |
| Long term deposits | long_term_deposits |
| (non-current section total, bare number) | non_current_assets_total |
| Stores, spare parts and loose tools | stores_spares_consumables |
| Stock-in-trade | stock_in_trade |
| Trade debts | trade_debts |
| Loans and advances | loans_advances |
| Short term deposits and prepayments | deposits_prepayments_other_receivables |
| Other receivables | other_receivables (pending) |
| Accrued interest | accrued_interest (pending) |
| Short term investments | short_term_investments |
| Cash and bank balances | cash_and_bank_balances |
| (current section total, bare number) | current_assets_total |
| TOTAL ASSETS | total_assets |

Balance identity used: total_assets == total_equity +
total_liabilities (NML prints TOTAL LIABILITIES as a face total).
31 Mar 2025: 159,920,849 + 133,212,040 = 293,132,889 ✓.
30 Jun 2024: 157,847,811 + 115,858,545 = 273,706,356 ✓.

## OGDC — mapping addendum (OCR parse + visual page-match complete)

Consolidated SFP = OCR p.7 (two-panel: left = equity/liabilities,
right = assets), consolidated P&L = OCR p.8. Units Rupees '000.
All rows below were extracted by the two-panel OCR parser and
matched against rendered page images (see run report).

### OGDC SFP — left panel (equity and liabilities)

Note on order: the register groups rows by panel for readability,
but the loader's OGDC SFP page map lists specs in embedded-text
document order (panels interleaved top-to-bottom as PyMuPDF
returns them). Keys are identical either way.


| Original label | Canonical key |
|---|---|
| Share capital | share_capital |
| Reserves | reserves |
| Unappropriated profit | unappropriated_profit |
| (total equity, bare number) | total_equity |
| Deferred taxation | deferred_taxation |
| Deferred employee benefits | deferred_employee_benefits |
| Provision for decommissioning cost | provision_decommissioning_cost |
| Long term lease liability | long_term_lease_liability |
| (non-current liabilities total, bare number) | non_current_liabilities_total |
| Short term lease liability | short_term_lease_liability |
| Trade and other payables | trade_and_other_payables |
| Unpaid dividend | unpaid_dividend |
| Unclaimed dividend | unclaimed_dividend |
| (current liabilities total, bare number) | current_liabilities_total |
| TOTAL LIABILITIES | total_liabilities |
| (grand total, bare number) | total_equity_and_liabilities |

### OGDC SFP — right panel (assets)

| Original label | Canonical key |
|---|---|
| Property, plant and equipment | property_plant_equipment |
| Development and production assets | development_production_assets |
| Exploration and evaluation assets | exploration_evaluation_assets |
| (operating non-current subtotal, bare number) | operating_non_current_subtotal |
| Long term Investments in subsidiary and associates | long_term_investments_subsidiary_associates |
| Long term Investments at amortized cost | long_term_investments_amortized_cost |
| Long term loans - secured (asset side) | long_term_loans_asset |
| Long term advances, prepayments and other receivables | long_term_advances_prepayments |
| Lease receivables | lease_receivables |
| (non-current assets total, bare number) | non_current_assets_total |
| Stores, spare parts and loose tools | stores_spare_parts |
| Stock in trade | stock_in_trade |
| Trade debts | trade_debts |
| Loans and advances | loans_and_advances |
| Deposits and short term prepayments | deposits_short_term_prepayments |
| Other receivables | other_receivables |
| Income tax - advance | income_tax_advance |
| Current portion of long term investments | current_portion_long_term_investments |
| Current portion of lease receivables | current_portion_lease_receivables |
| Other financial assets | other_financial_assets |
| Cash and bank balances | cash_and_bank_balances |
| (current assets total, bare number) | current_assets_total |
| (grand total, bare number) | total_assets |

Balance identity used: total_assets == total_equity +
total_liabilities. 31 Dec 2025: 1,383,637,471 + 302,979,745 =
1,686,617,216 ✓. 30 Jun 2025: 1,348,236,596 + 306,369,374 =
1,654,605,970 ✓.

## P&L headline mappings (all three sample companies)

| Original label (per company) | Canonical key |
|---|---|
| HUBC: Revenue from contracts with customers - net / NML: REVENUE / OGDC: Sales - net | revenue (HUBC/NML) / sales_net (OGDC) |
| HUBC: Cost of revenue / NML: COST OF SALES | cost_of_revenue (HUBC) / cost_of_sales (NML) |
| HUBC: GROSS PROFIT / NML: GROSS PROFIT / OGDC: Gross profit | gross_profit |
| HUBC: PROFIT FROM OPERATIONS / NML: PROFIT FROM OPERATIONS | profit_from_operations |
| HUBC: Finance costs / NML: FINANCE COST | finance_costs (HUBC) / finance_cost (NML) |
| HUBC: Share of profit from associates and joint ventures - net | share_of_profit_associates |
| HUBC: PROFIT BEFORE LEVY AND TAXATION FROM CONTINUING OPERATIONS | profit_before_levy_and_tax |
| HUBC: Levy - final tax | levy_final_tax |
| HUBC: PROFIT BEFORE TAXATION FROM CONTINUING OPERATIONS / NML: PROFIT BEFORE TAXATION / OGDC: Profit before taxation | profit_before_tax_continuing (HUBC) / profit_before_taxation (NML/OGDC) |
| HUBC: Taxation / NML: TAXATION | taxation |
| HUBC: PROFIT FOR THE YEAR FROM CONTINUING OPERATIONS | profit_for_year_continuing |
| HUBC: NET PROFIT FOR THE YEAR / NML: PROFIT / (LOSS) AFTER TAXATION / OGDC: Profit for the period | net_profit_for_year (HUBC) / profit_after_taxation (NML) / profit_for_period (OGDC) |
| HUBC: Continuing operations (EPS) / Discontinued operations (EPS) / (EPS total, bare) | eps_continuing / eps_discontinued / eps_total |
| NML: EARNINGS / (LOSS) PER SHARE - BASIC AND DILUTED (RUPEES) / OGDC: Earnings per share - basic and diluted (Rupees) | eps_basic (per-share Rupees, NOT scaled by unit_scale) |

Key-authority note: the page maps under `docs/phase-07/page_maps/`
are authoritative for the loader. Where this register's earlier
"pending" wording differs from a page-map key, the page-map key is
the one loaded; original labels are always preserved verbatim in
`original_label` on every line-item row.
