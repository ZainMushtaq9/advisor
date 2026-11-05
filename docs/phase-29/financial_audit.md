# Phase 29 — Independent financial calculation audit

Run: `phase29-acceptance-2026-11-05`. Fifteen recomputation rows,
each re-derived from stored statement rows and prices independently
of the phase that produced the stored value. Tolerance: exact for
identities and reconciliations, 0.0001 (absolute) for ratios, 0.01
for currency sums. Result: **14 matched, 1 mismatched — and the
mismatch is the expected HBL drift, not a failure** (see below).

## Matched (14)

| Check | Claimed | Recomputed |
|---|---|---|
| hubc_gross_margin | 0.417400 | 29,688,160 / 71,126,352 = 0.41740029… |
| hubc_trailing_pe | 5.155254 | 197.24 / 38.26 (`eps_total`) = 5.1552535… |
| ogdc_trailing_pe | 17.881625 | 303.63 / 16.98 (`eps_basic`, period 2025-07-01→2025-12-31) = 17.88162544… |
| portfolio_reconciliation | 3 portfolios reconcile | ew 999,473.03 + 526.97; balanced 999,581.14 + 418.86; conservative 899,884.10 + 100,115.90 — each = 1,000,000 capital |
| breadth_coverage | 444/470 = 0.944681 | same |
| volume_median | 54,631.5 | over 444 volumes |
| top10_volume_share | 49.249694% | 217,368,496 / 441,360,098 |
| hbl_sfp_identity_2025 | assets 7,708,144,220 = liabilities 7,219,529,515 + equity 488,614,705 | exact |
| hbl_sfp_identity_2024 | assets 6,055,112,877 = liabilities 5,644,314,783 + equity 410,798,094 | exact |
| hbl_pat_eps_2025 | PAT 66,763,916; EPS 45.48 | read from stored P&L rows |
| screen_matched_counts | liquid_leaders 194; volume_top_decile 44; cheap_profitable 1; dividend_payers 2; technical_momentum 0 | recount agrees on all five |
| alert_totals | 89 = 82 INFO + 6 WARNING + 1 CRITICAL | same |
| report_figure_census | 541 = 335 computed + 199 insufficient_inputs + 7 not_applicable | same (the original Phase 22 census, restored by recovery #7) |
| decision_completeness | HUBC 6/7, OGDC 6/7 | same; HBL 2/7, NML 4/7 recorded alongside |

## Mismatched (1) — expected difference, not a failure

**drift_vs_phase24_baseline.** The live counts are documents 4,
statements 118, line items 2,116 against the Phase 24 baseline of
3 / 88 / 1,316. The differences are exactly the HBL additions
(+1 document, +30 statements, +800 line items). This is the drift SLO
working as designed: the baseline predates the HBL extraction, and
the baseline update must be recorded with this evidence per the
Phase 25 rule — it must not be hidden by rewriting the baseline
silently, and it must not be reported as a calculation error.

## Key facts established by this audit

- HUBC trailing P/E uses `eps_total` (= 38.26; `eps_continuing` is
  also 38.26). OGDC six-month P/E uses `eps_basic` with period
  2025-07-01→2025-12-31 (= 16.98), distinct from the standalone
  quarter row 2025-10-01→2025-12-31 (= 8.07). Using the wrong EPS key
  or the standalone quarter is a look-ahead/period error; the
  runner asserts the correct keys.
- HUBC fundamentals are read via `company_id` (the `security_id`
  join returns 0 rows — values link by company_id).
- `financial_document_versions` = 0 rows: restatement versioning is
  documented but unexercised, so no restatement claim is made.
- Phase 3 `forecasts` and `recommendations` tables are 0 rows: no
  forecast or recommendation was ever stored as fact.
- No look-ahead was found: every dated input precedes the analysis
  that uses it (HUBC EPS published 2026-09-21 ≤ price date
  2026-11-03 ≤ decision date 2026-11-04).
- No fabricated financial data was found: every NOT_CALCULABLE
  output stays empty with a reason (Phase 13 abstentions, Phase 15
  WITHHELD values, Phase 17 NOT_RUNNABLE runs, Phase 6 zero values).
