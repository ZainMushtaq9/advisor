# Phase 5 — Coverage and Limitations (READ BEFORE CITING ANY NUMBER)

## What is covered

- Universe: 470 Main Board / Normal Counter snapshot
  securities (DPS Listing Status, Nov 4, 2026 1:17 PM PKT),
  37 sectors, all UNVERIFIED, reconciliation coverage 1.0
  FOR THIS VIEW ONLY (matched 470, missing 0, extra 0).
- Engine: validation, quality, ingestion, catch-up, APIs,
  CLI, frontend page — implemented and tested (see
  `phase_05_test_report.md`).

## What is NOT covered (do not claim otherwise)

- Market observations: production `market_prices` = 0. No
  price, index, or intraday observation has been ingested.
  Any price quoted from this system in this phase is a
  fabrication unless it comes from a future validated ingest.
- VERIFIED registry: VERIFIED = 0. Every registry record is
  UNVERIFIED (single source). No second distinct agreeing
  source including one official exists yet.
- Full market: GEM Board (5) and Main Board Non-Compliant /
  Winding-Up (93) are NOT in the registry. The 470 is one
  view, not the market.
- KSE-100: completeness NOT established. No "KSE-100 first"
  claim is made; KSE-100 membership was not checked against
  the snapshot.
- Identifiers: company_identifiers = 0, symbol_history = 0.
  No ISIN or identifier history is covered; absence is
  recorded, not zero-filled.
- Intraday: OUT OF SCOPE (no legally accessible free
  historical intraday verified; psxdata states none exists
  publicly; psx-dps claims today's ticks only, unverified).
- Indices: no index price is served. Index ingestion needs
  its own verified source and fields.
- Live collection: BLOCKED (D-51/D-52 + PSX Terms). No live
  adapter exists; no DPS data route was fetched in this
  phase (research probes were one HEAD to each site root
  only, and do not close D-51/D-52).
- Licensing: the PSX Terms internal-use question (database
  ingestion vs single personal copy) is UNRESOLVED in
  writing. Internal use is the working assumption for the
  local snapshot file; republication is NOT permitted on
  this evidence and needs separate written permission.

## Accepted implementation limitations

- A1 (reporting): the implementer's "42 new / 43 pre-existing"
  test split was off by one; verified split is 41 new / 44
  pre-existing, total 85 passed. Corrected in the test
  report and audit; no test was added or removed to force it.
- A2 (freshness): STALE is a separate label, not a
  quality_status replacement (single-column constraint).
- A3 (conflicts): cross-run conflicts cannot retroactively
  re-flag the earlier immutable row; the conflict remains
  visible via the later CONFLICTED row + differing values.
- A4 (frontend nav): the implementer left nav.ts untouched;
  the coordinator added the `/market` nav entry and
  re-verified typecheck/lint clean.
- A5 (SQLite fixtures): Phase 3 ids use PostgreSQL Identity,
  which SQLite renders without auto-generation; tests/CLI
  smoke runs use a test-only max(id)+1 fallback. Production
  PostgreSQL generates ids normally; the shipped CLI is
  unchanged and correct for PostgreSQL.
