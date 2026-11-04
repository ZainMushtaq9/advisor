# Phase 5 — Market-Data Architecture

## 1. Layers

```
Validated dated CSV file (operator-supplied, authorised route)
        │  scripts/run_market_ingestion.py  (--dry-run default)
        ▼
backend/app/services/market_data/
  validation.py  →  ValidatedRow or rejection (code + raw values)
  quality.py     →  quality_status + freshness label
  ingestion.py   →  idempotent store into market_prices (Phase 3 schema)
  scheduler.py   →  missing-date / catch-up computation (pure functions)
        │
        ▼
PostgreSQL market_prices (grain: security × date × bar_type × source)
        │
        ▼
GET /api/v1/market/…  →  frontend/app/market (read-only)
```

There is deliberately no live-adapter layer in this phase: every
candidate live source is BLOCKED or NOT SELECTED in
`market_source_research.md`. Adding one later is a new, separately
gated change, not a configuration flip.

## 2. Why ingestion is file-based in v1

The registry unblocker established the pattern: a live-browser read
saved as a dated file, then a validated import through an engine.
Market prices follow the same pattern because (a) direct DPS data
routes fail from this VM (D-51) and the listings table is
JavaScript-driven (D-52), and (b) PSX Terms bar automated
navigation without prior written permission. A file supplied by
the parent through an authorised route carries its own date,
source, and method — the same provenance the engine requires —
without any scraper.

## 3. Schema reuse (no new tables)

`market_prices` (Phase 3): open/high/low/close, volume, turnover,
previous_close, bar_type, trading_date, trading_session_id,
data_source_id (NOT NULL), source_key, source_timestamp,
collected_at, quality_status (CHECK-constrained vocabulary),
is_adjusted. `data_sources` resolves source_key rows; an absent
source_key is created UNVERIFIED by the CLI (mirroring the Phase 4
registry importer). Official status is NOT a column: official =
source_key in the Phase 4 `OFFICIAL_SOURCES` constant
(`psx_official`, `secp`), exactly as registry verification does.

## 4. Immutability and conflicts

Phase 3 triggers make `market_prices` immutable: a later run
cannot edit an earlier row. Consequences, both documented in code:
- Re-ingest of the same grain skips (no duplicates).
- Within one run, two disagreeing rows for the same grain from
  different sources are both stored, both CONFLICTED.
- Across runs, a disagreeing later row is itself stored
  CONFLICTED, but the earlier row cannot be retroactively
  re-flagged; the conflict stays visible via differing values
  plus the CONFLICTED row. This is an accepted limitation (audit
  A3), not a silent merge.

## 5. Scheduler model

No background daemon is introduced in v1. Catch-up is a pure
computation: given a requested date range and the dates already
stored for (security, source), ingest only the missing dates.
The CLI exposes it as `--catch-up` (requires `--from-date` /
`--to-date`). A future Celery/Beat schedule may call the same
functions; it must preserve the idempotency and fail-fast rules
and must not introduce a live adapter without a new gate.
