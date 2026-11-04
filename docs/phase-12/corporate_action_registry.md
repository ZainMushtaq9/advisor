# Phase 12 corporate action registry

5 dividend actions, all type DIVIDEND_CASH, all status
`appropriated` (changes-in-equity appropriation during the statement
period). All five have NULL announced/ex/record/effective/payment
dates: the loaded statements publish fiscal year and per-share amount
only, and no date is inferred. The statement period is recorded in
`source_evidence` as the only date evidence.

| Company | Fiscal year label | DPS (PKR) | Total asserted |
|---|---|---|---|
| HUBC | FY2024-25 final | 10.00 | NULL — see note 1 |
| HUBC | FY2025-26 first interim | 5.00 | NULL — see note 2 |
| HUBC | FY2025-26 second interim | 5.00 | NULL — see note 2 |
| HUBC | FY2025-26 third interim | 5.00 | NULL — see note 2 |
| NML | FY2023 final | 5.00 | NULL — see note 3 |

Note 1: two statement faces report different appropriation totals
for the HUBC final dividend (Rs 12,971,544,000 in the FY2025-26
statement; Rs 11,025,812,000 in the FY2024-25 statement). Neither is
picked and they are never averaged.

Note 2: each HUBC interim shows Rs 6,485,772,000 per statement face;
recorded as evidence only, not as an asserted action total.

Note 3: the NML total Rs 1,757,999,000 repeats across statement
components; component rows cannot be distinguished from a
total-column row in the loaded data, so no total is asserted.

OGDC: no dividend-labelled lines exist in its loaded statements, so
no OGDC action row is stored. That means "no action evidenced", not
"no action happened".

## Relation to the Phase 3 tables

The Phase 3 `corporate_actions` table (event_date NOT NULL,
adjustment_factor) and its `dividends` detail table stay EMPTY in
this run. They are the application layer: when an action gains a
known ex-date, the adjustment row is written there with its factor,
while this registry remains the evidence of record. Raw prices are
never modified by either layer.
