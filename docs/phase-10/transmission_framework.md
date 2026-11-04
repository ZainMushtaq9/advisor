# Phase 10 — Transmission framework

## Channels (modelled qualitatively; no elasticities estimated)

| Channel | Mechanism | What would evidence it (not yet held) |
|---|---|---|
| Interest rates | Policy rate -> KIBOR -> borrowing costs (HUBC, NML) and interest income (OGDC); bank margins (HBL, pending). | KIBOR series; company borrowing-rate disclosures. |
| Inflation | Energy/wheat prices -> CPI -> inflation expectations -> policy response -> borrowing costs. Core (~8.4%) vs headline (10.3%) distinction matters: the MPS flags second-round seepage risk. | PBS CPI component weights; tariff pass-through data. |
| Currency | External deficit + reserves -> PKR -> dollar-linked sales (OGDC), import costs (power fuel, textile inputs), FX translation (NML subsidiaries). | USD/PKR series; company FX sensitivity disclosures. |
| Commodities | Crude oil / gas / cotton prices -> E&P realisations, power fuel costs, textile input costs. NOT modelled quantitatively: no commodity series stored. | OGRA / World Bank commodity series; company commodity splits. |
| Fiscal policy | FBR collection, budget stance, SBP profit transfers -> fiscal space -> borrowing needs -> rates. Only FBR growth (7.0% y/y Q1-FY27) is stored. | Ministry of Finance fiscal operations; budget documents. |
| Demand | LSM, GDP, private-sector credit (14.1% y/y per MPS, not stored — no dated level held) -> order books and sales. | PBS LSM detail; SBP credit aggregates with dates. |

## Correlation is not causation

- CPI and the policy rate move together in this window (CPI 10.3%,
  rate raised to 12%), but the MPS attributes the hike to supply
  shocks (Middle East conflict, energy, wheat frictions), not to CPI
  mechanically causing the hike. The regime label "tightening" rests
  on the decision itself, not on the correlation.
- LSM recovery (+1.85%) and GDP growth (3.65%) coincide with the rate
  hike; no claim is made that tightening caused or prevented the
  recovery.
- Sector membership is never evidence of a specific exposure: OGDC's
  commodity exposure is framework-only because its loaded statements
  carry `sales_net` with no commodity breakdown.

## Company exposures (issuer-evidenced only)

| Company | Exposure | Evidence (Phase 7 statement lines) |
|---|---|---|
| HUBC | Borrowing cost (cost) | income:finance_costs; cash_flow:interest_paid; balance_sheet:short_term_borrowings |
| NML | Borrowing cost (cost) | income:finance_cost; balance_sheet:long_term_financing, short_term_borrowings |
| NML | FX via forwards (revenue) | cash_flow:exchange_gain_forward |
| NML | FX translation (balance sheet) | cash_flow:exchange_translation |
| OGDC | FX transaction (revenue) | cash_flow:exchange_gain_loss |
| OGDC | Interest income (income, NOT cost) | cash_flow:interest_income_investments, interest_income_lease |

Reviewed but NOT established (documented, not stored): HUBC FX
exposure (no FX line in loaded statements); OGDC borrowing-cost
exposure (no finance-cost line; interest coverage not_applicable by
structure); any commodity-level split of OGDC sales; any NML
export-share split.
