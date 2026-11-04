# Phase 14 — Risk Register (17 flags, as of 2026-11-04)

Flags are review-only observations. Severity is info or warning
only. No flag is a fraud, default or solvency conclusion.

## Company flags (12)

| Flag | Company | Severity | Evidence |
|---|---|---|---|
| warning_low_cash_conversion | HUBC | info | Phase 8 warning |
| warning_receivables_growing_faster_than_revenue | HUBC | info | Phase 8 warning |
| warning_negative_profit_after_tax | NML | warning | Phase 8 warning; 9M PAT loss Rs −1,182,815 thousand |
| warning_negative_operating_cash_flow | NML | warning | Phase 8 warning |
| warning_cash_conversion_both_negative | NML | info | Phase 8 warning |
| warning_eps_growth_sign_change | NML | info | Phase 8 warning |
| warning_pat_growth_sign_change | NML | info | Phase 8 warning |
| warning_receivables_days_over_one_year | OGDC | info | Phase 8 warning; 571.3 days |
| auditor_opinion_absent | NML | info | Interim condensed statements carry no opinion row |
| auditor_opinion_absent | OGDC | info | Interim condensed statements carry no opinion row |
| publication_date_unknown | NML | warning | Latest statement publication_date NULL; point-in-time validity unverifiable |
| statement_stale | NML | warning | Latest period end 2025-03-31, age 583 days > 365-day threshold |

Not flagged: HUBC auditor opinion is unmodified (no flag); HUBC
latest period end 2026-06-30 (127 days) and OGDC 2025-12-31
(308 days) are within the 365-day threshold.

## Market flags (5)

| Flag | Severity | Evidence |
|---|---|---|
| forecast_abstention | warning | Phase 13 abstained on 120/120 assessments |
| technical_coverage_zero | warning | Phase 6 produced 0 calculable indicator values |
| previous_close_absent | info | previous_close NULL on all 444 2026-11-03 rows |
| turnover_absent | info | Turnover NULL on all 444 2026-11-03 rows |
| missing_tickers_26 | info | 26/470 securities have no 2026-11-03 price row |

## Coverage note

HBL (Habib Bank Limited, company 277) has no flags: its CY2025
statements are not loaded (PDF blocked at download; live-browser
download runs separately). A Phase 7 load plus a Phase 14 re-run
adds HBL flags without redesign.
