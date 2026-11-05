# Phase 27 — Data-Quality SLO Definitions

Targets are per source category, not one universal threshold
(brief requirement). A daily price feed and an annual statement
feed do not go stale on the same clock, so they do not share a
target. An unmet SLO is a stored fact with its exact reason,
never hidden and never averaged away. A NULL value means
not_evaluable, never zero.

## Seed run results (run `phase27-observability-2026-11-05`, 2026-11-05)

| SLO | Category | Target | Seed value | Status | Reason |
|---|---|---|---|---|---|
| registry_evidence_coverage | registry | ≥ 1.0 | 1.0 | met | 470 of 470 companies carry evidence |
| price_coverage_latest_day | market_prices | ≥ 0.95 | 0.944681 | unmet | 444 of 470 securities priced on 2026-11-03 |
| price_session_gap_weekdays | market_prices | ≤ 0 | 2 | unmet | 2026-11-04 and 2026-11-05 have no stored session (Terms-gated) |
| previous_close_completeness | market_prices | ≥ 1.0 | 0 | unmet | 0 of 444 price rows carry previous_close |
| ohlc_validity_rate | market_prices | ≥ 1.0 | 1.0 | met | 444 of 444 stored prices pass OHLC validity |
| duplicate_ticker_rate | registry | ≤ 0 | 0 | met | 0 duplicates across 470 securities |
| statement_document_lineage | statements | ≥ 1.0 | 1.0 | met | 88 of 88 statements trace to a document |
| statement_freshness_days | statements | ≤ 180 | 128 | met | Latest period end 2026-06-30 is 128 days old |
| news_company_coverage | news | ≥ 0.10 | 0.006383 | unmet | 3 of 470 companies carry news events |
| reports_published_externally | reports | ≤ 0 | 0 | met | No publish step exists (Phase 22) |
| alert_delivery_rate | alerts | ≥ 1.0 | 1.0 | met | 89 delivered deliveries across 89 alerts |
| job_success_rate | jobs | ≥ 0.95 | 1.0 | met | 71 of 71 terminal job runs succeeded |
| golden_pass_rate | evaluation | ≥ 1.0 | 1.0 | met | 14 of 14 golden cases passed |
| drift_difference_count | evaluation | ≤ 0 | 0 | met | Live counts match the Phase 24 baseline |

## Why these targets (not aspirational)

- Price coverage 0.95, not 1.0: the recorded 2026-11-03 source
  left 26 tickers without a usable quote; 1.0 would be false.
- News coverage 0.10, not 1.0: the seed is 3 companies by
  design, not a universe feed; 10% is an honest near-term bar.
- Statement freshness 180 days: annual/interim reports arrive
  on a months-long clock. NML staleness (latest period end
  2025-03-31, flagged by Phase 14) is NOT hidden by this
  maximum — it is a separate flag, not this SLO's value.
- Session gap counts weekdays with no stored session; no
  holiday calendar is claimed, so a gap is never assumed a
  holiday.

## Reconciliation, duplicates, invalid values, lineage, late revisions

- Reconciliation: drift SLO (live counts vs Phase 24 baseline).
- Duplicate rate: duplicate_ticker_rate SLO.
- Invalid value rate: ohlc_validity_rate SLO (stored rows) plus
  Phase 5 ingest rejections (13 rejected, 12 OHLC + 1
  non-positive) recorded in Phase 5, not re-counted here.
- Lineage coverage: statement_document_lineage SLO (1.0) and
  source_key/data_source_id NOT NULL grains on prices and
  statements.
- Late revisions: revisions are new versions, never edits
  (Phase 3 immutability + version discipline). No revised
  statement version exists in the seed; a revision would appear
  as a new row with an incremented version_number, and the
  lineage SLO would still measure the current grain.
