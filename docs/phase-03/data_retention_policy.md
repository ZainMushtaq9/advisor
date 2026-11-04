# Phase 3 — Data Retention Policy

(Implements Phase 1 DATA_RETENTION_POLICY.md for the Phase 3
schema and storage engine. Where this file and Phase 1 disagree,
the stricter rule wins and the disagreement is logged as a defect.)

## Never delete

- Raw payloads and raw files (raw/): the evidence itself.
- Published/revised financial statements (all versions).
- Market observations (all versions, all sources, including
  conflicting ones).
- Provenance records, audit logs, quality reports (all versions).
- Research reports and financial reports (all versions).
- Backups and manifests.

Deletion of any of the above requires a legal/provenance hold
procedure that does not exist in Phase 3 — so in Phase 3, it does
not happen.

## Regenerable (may be rebuilt, never edited as source)

- processed/ and parquet/ datasets: rebuild from raw + code
  version, record the rebuild in a manifest, keep the old version
  until the rebuild is verified.

## Prunable

- tmp/ only, files older than 7 days, only when explicitly asked,
  dry-run by default (see storage_engine.md).

## Backups

- Before any major schema change: a verified backup (dump +
  manifest with SHA-256s + row counts). A backup without a
  verified manifest is not a backup.
- Backup inclusion: database dump, raw/, processed/,
  financial_reports/, parquet/, research_reports/, manifests/.
- Backup exclusion: backups/ itself (would recurse), tmp/
  (scratch), quarantine/ (reviewed separately).
- Files are never auto-restored over the live store; extraction
  is a separate, explicit operator step into staging.

## Synthetic / test data

Test rows are labelled TEST ONLY, live only inside rolled-back
transactions in tests, and must never appear in production tables.
Any TEST ONLY row found in a production table is a defect, not
data. Phase 3 production tables hold zero market/financial rows
at the end of the phase (verified by table counts in the test
report).
