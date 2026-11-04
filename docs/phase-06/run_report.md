# Phase 6 — Run report (live assessment, 2026-11-04)

## Dry-run first (no writes)

Command: scripts/run_technical_indicators.py --dry-run
Result: run_key phase06-coverage-2026-11-03, dry_run true,
as_of 2026-11-03, securities 470, indicators 62,
any_calculable 0, values_written 0, error_rows 0.
Exit 0. No row was written; the database was verified
unchanged afterwards (runs 0, errors 0, values 0 for Phase 6).

## Commit

Command: scripts/run_technical_indicators.py --commit
Result: dry_run false, securities 470, any_calculable 0,
values_written 0, error_rows 124. Exit 0.

## Database state after the commit

- technical_calculation_runs: 1 row
  (phase06-coverage-2026-11-03, completed, 470 processed, 0
  records written).
- technical_calculation_errors: 124 rows — missing_data 63,
  insufficient_warmup 61. Arithmetic: 61 indicators x 2 groups
  (444 securities with 1 bar each + 26 securities with 0 bars)
  = 122, plus daily_return split by bars_available into 2
  missing_data rows = 124. The remaining missing_data rows are
  the 61 zero-bar aggregates (one per non-daily_return
  indicator) plus 1 daily_return 1-bar aggregate = 63 total
  missing_data.
- technical_indicator_values: 0 rows.
- technical_indicator_definitions: 62 rows (seeded).
- technical_indicator_configurations: 62 rows (one active
  config per indicator, version 1.0, default parameters).
- technical_signal_events: 0 rows.
- Immutability triggers present on all four output tables
  (information_schema lists each trigger once per event,
  UPDATE and DELETE — normal PostgreSQL behaviour for one
  BEFORE UPDATE OR DELETE trigger, not duplication).

## What the run proves and what it does not

It proves the framework runs end-to-end on production data,
assesses every security, writes an honest run record, and
stores nothing it cannot justify. It does NOT prove any
indicator value: none exists, because one trading day cannot
supply any warm-up. The next run that matters is the first
run after a second trading day lands — SMA(5) still will not
be calculable then (needs 5 closes), but the run record will
show the counts moving, and the API will say so.
