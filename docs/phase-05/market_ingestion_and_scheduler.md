# Phase 5 — Ingestion and Scheduler

## 1. Ingestion flow (CLI)

```
scripts/run_market_ingestion.py --input <csv> --source-key <key>
  [--from-date YYYY-MM-DD --to-date YYYY-MM-DD] [--catch-up]
  [--dry-run | --commit]
```

- `--dry-run` is the default: rows are flushed for counting and
  then rolled back; the database is left untouched.
- `--commit` commits only after the whole file validates.
  Fail-fast rules apply in both modes: a wrong header aborts
  before any DB work; any unknown ticker aborts the whole run
  (exit 2, JSON error) before any write.
- The CLI prints the ingestion report as JSON and never prints
  DATABASE_URL. It makes no network call.
- The ingestion module itself never commits; the caller (CLI)
  controls commit/rollback.

## 2. Ingestion report fields

`source_key`, `bar_type` ("daily"), `dry_run`, `ingested`,
`skipped`, `rejected`, `conflicted`, `stale`,
`quality_breakdown`, `rejected_rows` (raw values + code),
`missing_sessions` (per security, dates with no stored
observation for that security from this source),
`catch_up`, `catch_up_filtered`, `scope_note`,
`freshness_rule_note`, plus a note that missing sessions are
reported, never zero-filled, and no price row is stored for them.

## 3. Idempotency and immutability

Re-ingesting the same grain (security, trading_date, "daily",
data_source_id) SKIPS: per-row SAVEPOINT on unique-constraint
failure, counted as skipped, never updated. This holds because
Phase 3 triggers make `market_prices` immutable. Quality is
precomputed across the whole batch before any insert, so two
disagreeing rows in one file both land CONFLICTED.

## 4. Scheduler / catch-up (pure functions, `scheduler.py`)

- `stored_dates_for_source(session, security_id, source_id)` —
  dates already stored.
- `compute_missing_dates(stored, from_date, to_date)` — the
  requested range minus stored dates.
- `missing_sessions_by_security(...)` — per-security missing
  lists for a range (or, without an explicit range, the span of
  validated trading dates in the file).
- `filter_rows_to_missing(rows, missing)` — catch-up filter:
  only rows for missing dates proceed.
- `--catch-up` requires `--from-date` and `--to-date`; without
  them it is refused rather than guessed.

## 5. What the scheduler is NOT

It is not a background daemon, not a cron/Beat schedule, and not
a live collector. A future schedule may call these functions,
but only against validated dated files through an authorised
route, preserving idempotency and fail-fast rules. A live
adapter requires a new gate (see `market_source_research.md`).

## 6. Worked CLI behaviour (throwaway SQLite, TEST ONLY)

Dry-run reported ingested=2 with the DB unchanged; `--commit`
ingested 2; re-commit skipped 2; unknown-ticker `--commit`
aborted exit 2 with no write; bad header aborted before DB
work; catch-up filtered 2 already-stored rows and reported the
remaining missing date. These are test-fixture results, not
production ingestion: production `market_prices` remains 0.
