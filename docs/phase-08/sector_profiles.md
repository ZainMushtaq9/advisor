# Phase 8 — Sector-specific metric profiles

Sector profiles state which metrics apply to a sector and how to
read them. They never change a value. Rows are stored in
`sector_metric_profiles` (one per sector × metric) for the three
sectors with computed statements. HBL's sector (COMMERCIAL BANKS)
gets no profile until its statements exist — a bank profile must
not be written from industrial assumptions.

## POWER GENERATION & DISTRIBUTION (HUBC)

- **Applicable as printed:** margins, returns, liquidity, leverage,
  interest coverage, cash-flow and growth metrics.
- **receivables_days — read as settlement lag.** Trade debts are
  offtaker settlement receivables, not retail collections; 157.5
  days for HUBC FY2026 describes settlement timing, not customer
  delinquency.
- **inventory_days — low relevance.** Fuel and stores only; there
  is no finished-goods stock to manage.
- **net_margin — read with the associates note.** HUBC FY2026 net
  margin (0.7909) includes Rs 45,315,750 thousand of post-tax share
  of profit from associates and joint ventures on revenue of
  Rs 71,126,352 thousand. The margin is arithmetically correct and
  structurally inflated versus an operations-only margin; the
  operations margin (0.4790) is the comparable figure.
- **payables_days — upper bound.** Uses total trade_and_other_
  payables as printed (no trade-only split available).

## TEXTILE COMPOSITE (NML)

- **Applicable as printed:** all statement-based metrics.
- **inventory_days — primary working-capital metric.** Large raw
  cotton / yarn stock: 145.7 days for the nine months to Mar 2025
  is the sector's central working-capital fact, not an anomaly.
- **Negative earnings are reported, not hidden.** Nine-month PAT
  is a loss (Rs −1,182,815 thousand) after a Rs 7,993,455 thousand
  profit in the prior nine months; margins, returns, and growth
  rates are negative and sign-change flagged. Negative OCF
  (Rs −5,371,036 thousand) with a dividend still paid
  (Rs 2,607,008 thousand) is flagged for review.
- **Interim averages.** Return denominators average the 30 Jun 2024
  comparative balance sheet with the 31 Mar 2025 balance sheet;
  they are interim averages, not annual averages.

## OIL & GAS EXPLORATION COMPANIES (OGDC)

- **Not applicable by structure:** interest_coverage (no
  finance-cost line, no interest-bearing loans — lease liabilities
  only). This is recorded as `not_applicable`, never as zero and
  never as missing data.
- **Not available:** operating_margin, roce (no operating-profit
  line), roe_owners (no owners-attributable profit line).
- **ib_debt_to_equity — lease liabilities only** (0.0018). It is
  not comparable to loan-funded peers' leverage.
- **receivables_days — settlement structure.** 571.3 days reflects
  the sector's circular-debt settlement receivables; it is flagged
  for review as a structural pattern, not as proof of distress.
- **current_ratio — read with composition.** 9.62 is driven by the
  current portion of long-term investments and large trade debts,
  not by operating cash (cash ratio is 0.0989).
- **Derived cost.** Cost of sales is derived exactly as sales_net
  − gross_profit (no printed cost line); inventory and payables
  days carry the derivation flag.

## COMMERCIAL BANKS (HBL) — pending

No profile is written. When HBL statements arrive, its profile must
be built from banking metrics (net interest margin, cost-to-income,
advances-to-deposits, NPL coverage, capital adequacy) — industrial
ratios must not be applied blindly to a bank, per the brief.
