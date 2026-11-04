# Phase 4 — Registry Statistics (actual counts)

Date: 2026-11-04 (Asia/Karachi). All counts are live database
counts queried in this phase. Nothing here is estimated.

## Production registry (live PostgreSQL)

| Entity | Count |
|---|---|
| Companies | 0 |
| Securities | 0 |
| Sectors | 0 |
| Registry evidence rows | 0 |
| Companies by status | {} (empty) |
| Securities by status | {} (empty) |

Source of counts: `GET /api/v1/registry/statistics` against the
live database (uvicorn port 8003 check and the PG check script),
and direct `SELECT count(*)` queries at gate-check time
(companies 0, securities 0, sectors 0, exchanges 0, before any
import; the importer test used a rolled-back transaction only).

## Why zero is the correct production count

No usable official registry source was obtainable in this phase
(see source_research.md): DPS Listing Status yields 0 rows to a
text fetch, DPS direct access fails from this VM, the DPS
market-watch text copy is a stale 2026-01-25 cache with no
company names, and the PSX homepage gives 26 partial scrip rows
with no names, sectors, or statuses. Creating companies from
ticker-only rows would require inventing legal names — which
this phase refuses to do. The engine, APIs, and frontend are
verified; the population is blocked, and the registry honestly
reports empty.

## Test-run counts (NOT production)

- Pytest fake-session imports: 2 companies, 2 securities,
  2 sectors per batch (in-memory only, never in PostgreSQL).
- Live-PostgreSQL check: 2 companies, 2 securities created in
  a transaction, then ROLLED BACK. Final live counts remain 0.
- Reconciliation fixture (pytest): snapshot 2 tickers, registry
  2 tickers, matched 1, missing 1, extra 1, coverage 0.5 —
  a fixture calculation, not a market claim.

## Schema counts (for context, not registry population)

- Phase 3 tables: 54 model tables, 56 public tables incl.
  alembic_version + phase2_probe.
- Phase 4 addition: 1 table (registry_evidence), migration
  head a909e8449cdd, 57 public tables after upgrade.
  (Verify with `alembic current` + information_schema at audit
  time; the auditor's count governs if it differs.)
