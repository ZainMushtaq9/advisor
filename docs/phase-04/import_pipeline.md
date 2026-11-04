# Phase 4 — Import Pipeline

Entry point: `import_records(session, records, source_key,
source_display_name, collected_at)` in
`backend/app/services/registry/importer.py`.

## Steps per record

1. Validate: normalize ticker, name, ISIN (if present). Any
   failure rejects the record with a recorded error; it is not
   stored, not guessed, not zero-filled.
2. Match: deterministic matching (see
   normalization_and_matching.md) against current securities.
3. Ambiguous -> DataQualityReport (MEDIUM, "ambiguous_registry_
   record"), record skipped, no entity created or merged.
   Reports are de-duplicated: re-importing the same ambiguous
   record does not append a duplicate report (audit M3).
4. Sector: get-or-create a sector row keyed by (source,
   source_sector_name) — source taxonomy preserved, canonical
   sector left NULL.
5. No match -> create Company + Security + CompanyIdentifier
   rows (ISIN and any supplied identifiers) + two
   RegistryEvidence rows (company, security). Status is
   UNVERIFIED, or the stated lifecycle status when the source
   states suspended/delisted/inactive (audit M4: listing_status
   is stored, not dropped; unknown values are recorded as
   errors and ignored, never stored).
6. Unique match -> in this order (audit M2: conflict checked
   before any mutation):
   a. ISIN disagreement -> both company and security marked
      CONFLICTED with a HIGH DataQualityReport row; ticker,
      stored ISIN, and symbol history are NOT touched.
   b. Name disagreement on an ISIN/identifier match -> both
      marked PENDING_REVIEW with a MEDIUM report; the ticker
      is NOT changed (audit M1: a doubtful record never
      mutates the stored ticker).
   c. Ticker change on a clean match -> recorded in
      symbol_history; the security keeps its surrogate id.
   d. A new ISIN on a matched security is stored; new
      identifiers supplied on a re-import are stored when not
      already present (audit M5).
   e. A stated lifecycle status is stored (unless the record
      is CONFLICTED or PENDING_REVIEW).
   f. Idempotent re-import: if evidence rows for this
      source+record already exist, the record counts as
      skipped_as_duplicate and nothing changes.
7. Verification promotion runs per record from evidence only
   (see data_quality_policies.md). Import success alone never
   promotes; VERIFIED additionally requires corroboration
   (audit H1).

## Idempotency (tested)

Importing the same batch twice: second run creates 0 companies,
0 securities, 0 sectors, and counts every record as
skipped_as_duplicate. Proven by `test_import_creates_and_is_
idempotent` and by the live-PostgreSQL check script (rolled back).

## Caller contract

The importer takes records supplied by the caller — a file, a
verified snapshot, or a future Phase 5 collector. It does NOT
fetch from any website, does NOT assume an API, and does NOT
start a scheduler. Collection is a separate, later concern; this
phase proves the storage and matching rules, not a live feed.

## Population in this phase

Production population: ZERO records. The only imports executed
were TEST ONLY (pytest fake-session imports and the rolled-back
live-PostgreSQL check). No production company, security, or
sector row was created, because no usable official registry
source was obtainable (see source_research.md). The pipeline is
verified; the population is blocked, and that block is stated in
the completion report rather than papered over with partial rows.
