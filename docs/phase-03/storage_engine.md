# Phase 3 — Storage Engine

Canonical code: `storage/phase3_engine.py`, built on the Phase 2
`storage/storage_helper.py` (write-once, SHA-256 sidecars, slug
paths, relative paths only). No backend duplicate of this engine
exists; the backend data-quality helpers
(`backend/app/services/data_quality.py`) are pure validation
functions, not a second storage implementation.

## Layout (existing Phase 2 directories, now governed)

raw/{psx-dps,psxdata,pdf}, processed, parquet, financial_reports,
research_reports, backups, manifests, quarantine, tmp.

## Dataset manifests

`register_dataset(root, key, files, provenance)` writes
`manifests/<key>.manifest.json` (manifest_version
phase3-dataset-v1, PKT timestamp, provenance, per-file SHA-256 +
byte size). `verify_dataset` re-hashes every listed file and
returns mismatches (missing file, hash mismatch) — a mismatch is a
finding, never a silent pass. The manifest is never listed inside
itself.

## Quarantine

`quarantine_file` moves a failed-integrity file (and its sidecar)
into quarantine/ with a reason JSON. Quarantined files are never
silently deleted; they are quality issues awaiting review.
Audit L5 fixes: a same-named second quarantine gets a hash
suffix (file AND sidecar), so it cannot overwrite the first;
re-registering an existing dataset key raises instead of
overwriting its manifest; `verify_dataset` checks byte_size as
well as SHA-256; `retention_for()` lets callers consult the
RETENTION policy, and `prune_tmp` refuses to run if tmp/ is not
marked prunable.

## Retention (see also data_retention_policy.md)

- raw, research_reports, financial_reports, backups, manifests,
  quarantine: NEVER deleted by the engine.
- processed, parquet: regenerable from raw + code version; may be
  rebuilt, never edited in place as if they were source.
- tmp: the ONLY prunable directory, age-gated at 7 days, and only
  when explicitly asked. `prune_tmp` defaults to dry-run (lists
  candidates, deletes nothing).

## Parquet — honest guard

pyarrow is NOT installed on this VM. `write_parquet_dataset`
therefore raises RuntimeError ("refusing to write a fake .parquet
file") instead of writing a file with a .parquet extension. No
Parquet dataset is claimed to exist in Phase 3. Installing pyarrow
(free, Apache-2.0) is a Phase 5 task, at which point this function
writes real Parquet and the test's pyarrow-present branch covers it.
The Phase 3 test asserts the guard branch on this VM.

## File hashes for news/research

News and research rows in PostgreSQL store content_hash + a storage
reference, not file bytes. The file on disk and the database row
are two views of one provenance record, linked by that hash.
