# Phase 4 — Registry Architecture

## What exists already (Phase 3, reused — no duplicates)

- `companies` — one row per legal issuer, NOT per ticker.
- `securities` — one row per tradable instrument, joined to a
  company by a stable surrogate id, never by ticker string alone
  (the verified PSX rename case is ENGRO -> ENGROH).
- `sectors` — source taxonomy preserved: `source` +
  `source_sector_name` are the source's own values;
  `canonical_sector_id` stays NULL unless a verified mapping
  exists. The 38-vs-37 sector discrepancy is handled by keeping
  both taxonomies as separate rows, never by picking a winner.
- `company_identifiers` — all known identifiers (ISIN, PSX code,
  registrar codes); previous identifiers kept, never overwritten.
- `symbol_history` — append-only rename/transfer history with
  effective dates and source evidence.
- `exchanges` — PSX row (code PSX, timezone Asia/Karachi).
- `data_sources`, `data_quality_reports`, `raw_payloads` — provenance
  and issue logging from Phase 3 governance.

## What Phase 4 adds (one table, one migration)

- `registry_evidence` (migration `a909e8449cdd`, head after Phase 3
  `20261104_0004`): one row per (entity_type, entity_id, source_key,
  source_record_key), storing the observed name/sector and the
  collection timestamp. Verification status is DERIVED from these
  rows (see data_quality_policies.md), never from import success.
- No other new tables. No duplicate company/security/sector tables.

## Service layers (backend/app/services/registry/)

- `normalization.py` — pure string normalization (match keys only;
  originals always stored untouched).
- `matching.py` — deterministic matching (ISIN, identifier, or
  ticker+name). Ticker alone and name alone are never enough.
- `importer.py` — idempotent incremental import; never sets
  VERIFIED/PARTIALLY_VERIFIED; records symbol history on ticker
  change; writes DataQualityReport rows for ambiguity/conflict.
- `verification.py` — evidence-driven promotion only.
- `reconciliation.py` — registry vs dated snapshot comparison;
  no snapshot, no coverage claim.
- `sync_config.py` — configuration only; no scheduler is started.

## API and frontend

- Read-only API: `backend/app/api/v1/endpoints/registry.py`
  (9 endpoints — see api_documentation.md).
- Frontend: `frontend/app/companies/page.tsx` renders ONLY rows
  returned by the registry API, with explicit empty/unavailable
  states. No fabricated companies, prices, or ratings.

## Operational notes (audit LOW findings, fixed/documented)

- Alembic invocation: the WORKING invocation is from
  `database/` with `database/alembic.ini`
  (`../backend/.venv/bin/alembic -c alembic.ini current/upgrade`).
  The backend `alembic.ini` cannot locate the Phase 3/4
  revisions (its script_location points at `backend/alembic`,
  which holds only the Phase 2 baseline). Use the database
  invocation; do not "fix" this by moving migrations.
- `alembic check` reports drift ONLY for the intentional
  phase2_probe retention (Phase 3 accepted exception). It is
  not a Phase 4 schema drift.
- ISIN check digits are NOT recomputed (format-checked only);
  recomputation is a documented Phase 5 validation concern.

## What Phase 4 does NOT do

- No live DPS/PSX collection (blocked — see source_research.md).
- No scheduler, no periodic job, no agent.
- No canonical sector mapping, no name completion, no ticker
  completion from partial rows.
- No merge to main, no push claimed without a verified remote SHA.
