# PSX Intelligence AI — Storage Architecture (Phase 1 of 30)

> **Status: DESIGN ONLY — Phase 1, Team 6. STOP AFTER PHASE 1.**
> No storage directory, Parquet file, MinIO bucket, or backup in this
> document has been created. Paths below are *specified relative
> layouts*, not existing locations. No file has been written, uploaded,
> or restored under this design. Budget: **PKR 0 absolute zero-cost**
> for project software/storage services — local filesystem + Apache
> Parquet + optional self-hosted MinIO + PostgreSQL/SQLAlchemy/Alembic
> only. No paid cloud storage, managed database, or paid object store
> is specified. Local hardware, electricity, and internet are
> **external operating expenses** — disclose them, never call them
> "free". If a path below ever points at a paid service, that is a
> design violation, not an implementation detail.
>
> **Companions:** `DATABASE_DESIGN.md` (relational principles),
> `DATABASE_ENTITY_CATALOG.md` (row-level fields),
> `DATABASE_RELATIONSHIPS.md` (delete rules),
> `DATABASE_INDEXING_STRATEGY.md` (database indexes),
> `DATA_RETENTION_POLICY.md` (how long each class lives, what is
> never deleted, archival/deletion rules).

## 1. Two systems of record, one provenance chain

This project has TWO storage systems, and confusing them is the
central storage bug this document prevents:

| System | What it holds | What it is NOT |
|---|---|---|
| PostgreSQL (relational, specified not built) | Typed business facts: prices, quotes, statements, line items, ratios, dividends, forecasts, recommendations, holdings, executions, audit logs — plus *references* (relative path/key + SHA-256 + size + backend) to files | NOT a blob store. Large payloads (PDF bytes, multi-MB JSON, Parquet files) are never stored as database blobs in this design, except small JSON inline in `raw_payloads.payload_inline` under a documented size threshold (catalog §33). |
| Filesystem / Parquet / optional MinIO (file/object, specified not built) | Original PDFs, raw JSON payloads, processed documents, historical Parquet files, research reports, backups | NOT a second database. Files do not carry their own independent business logic; every file that matters is referenced by a database row (or, for backups, by a manifest) with a content hash, so a file without a reference is orphaned and a reference without a file is a quality issue — both are detectable. |

**Provenance chain (normative):** source → raw file/payload
(`raw_payloads` row + file, content-hashed) → processed database row
(with `raw_payload_id` + provenance block) → derived file (Parquet /
processed document / report, with its own hash + source-row references)
→ audit log. Break any link and the downstream artefact is untrusted
until re-linked. A derived file that cannot name its source rows is
not a deliverable; it is an orphan.

## 2. Storage backends (zero-cost only)

| Backend | Role | Notes |
|---|---|---|
| Local filesystem (primary) | All six classes in §3, on a local disk controlled by the operator | Relative paths only (see §4). Absolute machine paths (`/home/…`, `C:\…`) must never be stored in the database — a backup restored to another machine would break every reference. |
| Apache Parquet (analytical files) | Historical, columnar, append-friendly datasets: EOD history, snapshot history, feature snapshots, forecast evaluation extracts | Parquet is a file format, not a service. No vendor, no fee. Partitioned by date/security (see §6). Parquet files are derived/archival copies of database history, not a replacement for the database's system-of-record role — unless a later phase explicitly promotes a Parquet dataset to system-of-record for a defined analytical purpose, with a migration note. Phase 1 does not promote any Parquet file to system-of-record. |
| Self-hosted MinIO (optional) | S3-compatible object storage run locally, for the same objects as the filesystem layout, where a later phase needs object semantics (versioning, bucket policies, S3 API) | OPTIONAL, not required. MinIO here means the self-hosted open-source server on local hardware — not a paid cloud S3 service. If MinIO is adopted, the layout (§4) maps 1:1 to bucket keys, and `storage_backend` on each reference flips from `'local'` to `'minio'` — the logical layout does not change. MinIO is NOT provisioned in Phase 1, and its suitability/volume is UNVERIFIED (design U13). |
| PostgreSQL (relational) | Typed facts + references (see §1) | Version to be pinned at provisioning; SQLAlchemy/Alembic specified, not built. |
| SQLite (local-dev only) | Schema-shape review / unit tests in a later phase | Never a production store for this project's data (see design §3). |

**Explicitly excluded:** any paid cloud bucket, managed warehouse,
managed database, or paid file-hosting service. Any proposal to use
one needs explicit user approval and a budget change — it is not a
Phase 1 fallback.

## 3. The six storage classes

### 3.1 Original PDFs (write-once, never edited)

- **What:** Source PDFs exactly as received — announcement PDFs,
  financial-statement PDFs, regulatory filings, research-source PDFs
  where licensing allows local retention.
- **Rule:** Write-once. A PDF file, once stored, is never overwritten
  or edited. A corrected PDF is a new file with a new hash.
- **Reference:** `announcements.pdf_storage_path` +
  `pdf_content_sha256`; `financial_statements.original_document_ref`;
  `raw_payloads` row where the PDF is also the raw payload
  (`payload_type = 'pdf'`).
- **Licensing guard:** Storing a PDF locally does not grant a right
  to redistribute it. PSX data licensing must be verified before any
  commercial use or redistribution (collector README). Retention of
  a PDF whose licence is later found to prohibit retention follows
  the legal-hold/removal procedure in `DATA_RETENTION_POLICY.md` —
  it is not silently deleted, and it is not silently kept either;
  the procedure decides, and the decision is audit-logged.

### 3.2 Raw JSON (and other raw payloads) — write-once

- **What:** Source payloads exactly as received: JSON snapshots,
  quote payloads, EOD responses, CSV/HTML where a source provides
  them. This is the file-level twin of `raw_payloads`.
- **Rule:** Write-once, content-hash-addressed (§7). Small JSON may
  also live inline in `raw_payloads.payload_inline` (catalog §33);
  the file is still the durable copy for payloads above the inline
  threshold. Inline and file copies of the same payload must share
  the same SHA-256 — a mismatch is a quality issue.
- **Separation rule (from the collector scaffold):** raw and processed
  are stored separately, always. A processed document must never
  overwrite its raw source, and a raw file must never be "cleaned"
  in place. Cleaning produces a processed file (§3.3), not an edited
  raw file.

### 3.3 Processed documents (derived, versioned)

- **What:** Cleaned/normalised documents derived from raw payloads:
  normalised statement extracts, cleaned announcement text, processed
  news text, structured extracts (JSON) that downstream modules read
  instead of re-parsing raw payloads.
- **Rule:** Derived + versioned. Each processed document names its
  source `raw_payload_id`(s) and its processing version/method. A
  re-processing produces a new version (new file, new hash, new
  reference), not an overwrite. Processed documents are reproducible:
  given the raw file + method version, the processed file must be
  regenerable — if it is not, the method version is underspecified
  and that is a design bug to fix before relying on the document.
- **Reference:** database rows that consumed the processed document
  (e.g. statement rows) carry the processed document's reference
  where applicable, in addition to the raw reference — both links
  are kept, so "processed from what?" and "processed how?" are both
  answerable.

### 3.4 Historical Parquet files (analytical, partitioned, append-friendly)

- **What:** Columnar historical datasets for analysis and archival:
  EOD price history, snapshot history, feature snapshots for models,
  forecast-evaluation extracts, indicator series extracts.
- **Rule:** Partitioned (§6), schema-versioned (§5), append-or-replace
  -partition (never edit a row inside a Parquet file in place).
  Corrections to history produce a new partition version or a
  superseding partition, with the old partition retained per the
  retention policy — Parquet archival does not erase database history.
- **Relationship to the database:** Parquet files are derived from
  database rows (or, for archival, are the archival copy of database
  partitions). Each Parquet dataset carries a manifest (§8) naming
  its source query/table, date range, row count, schema version, and
  content hash. A Parquet file without a manifest is not trusted for
  analysis.
- **Why Parquet here, not more database indexes:** analytical queries
  (price ranges across all securities, indicator series, evaluation
  aggregates) are columnar scans. Parquet column pruning + partition
  pruning serve them without a dozen B-tree indexes on the fact table
  (see indexing strategy §7 — price/volume alone are deliberately
  not B-tree-indexed).

### 3.5 Research reports (agent outputs, referenced not duplicated)

- **What:** Reports, briefings, and documents produced by agents or
  analysts: research reports, valuation memos, forecast summaries.
- **Rule:** The file is the artefact; `agent_outputs.storage_path` +
  `content_sha256` is its reference. The database must not contain a
  second, divergent copy of the report text as a free-text column
  alongside the file — one canonical copy (the file), one reference
  (the row). If a report is revised, the revision is a new file + new
  `agent_outputs` row (or a new version linked to the same execution,
  with the supersede relationship explicit), not an overwrite.
- **Provenance:** A research report must be able to name the forecasts,
  valuations, ratios, and source rows it relied on (via
  `agent_outputs` related ids + the execution's input refs). A report
  that cites a value without a traceable source row is an opinion
  piece, not a research artefact, and must be labelled as such if it
  is stored at all.

### 3.6 Backups (manifested, restorable, tested by hash — not by hope)

- **What:** Backups of (a) the PostgreSQL database (logical dump and/or
  filesystem backup, method to be chosen at provisioning — Phase 1
  specifies the requirement, not the tool), (b) the file/object store
  (PDFs, raw JSON, processed documents, Parquet, reports), and (c) the
  manifests that bind them together.
- **Rule:** Every backup has a manifest (§8) with: backup timestamp
  (PKT-rendered), database dump hash, file inventory hashes, row
  counts per key table, schema/migration version (Alembic revision,
  once it exists), and storage-backend layout version. A backup
  without a manifest is not a backup; it is a pile of files.
- **Restore rule:** Restore is defined as: restore database +
  restore files + verify hashes + verify row counts + verify that
  every database file-reference resolves to an existing file (and
  vice versa for non-orphan classes). A restore that skips hash
  verification has not been tested. See `DATA_RETENTION_POLICY.md`
  for backup retention periods and `§9` below for restore procedure.
- **Zero-cost note:** Backups live on local disk (and, optionally,
  a second local disk / self-hosted MinIO bucket on separate hardware
  the operator already controls). No paid backup service is specified.
  The external operating expense here is disk capacity + electricity
  — disclose it; do not call local backup "free".

## 4. Directory / key layout (relative, backend-neutral)

All paths below are RELATIVE to a single project storage root, whose
absolute location is an operator/provisioning decision (not specified
here, and never stored in the database). The same layout maps to
filesystem directories or MinIO keys by replacing `/` separators —
the logical layout does not change between backends.

```
<storage-root>/
  raw/
    <source-key>/
      <YYYY>/<MM>/
        <entity>_<security-or-scope>_<collected_at_pkt-ISO>_<sha256-8>.json
        # PDF originals live under raw/ too when the PDF IS the raw payload:
      pdf/
        <source-key>/<YYYY>/<MM>/<doc-id>_<sha256-8>.pdf
  processed/
    <source-key>/
      <YYYY>/<MM>/
        <entity>_<scope>_<processing-version>_<sha256-8>.json
  parquet/
    <dataset>/
      trading_date=<YYYY-MM-DD>/        # or observation_date= / year= / month= per §6
        part-<security-or-scope>-<sha256-8>.parquet
  reports/
    <agent-key>/
      <YYYY>/<MM>/
        <report-slug>_<execution-id>_<sha256-8>.md    # or .pdf/.html as produced
  documents/
    <scope>/                              # processed documents not covered above
      <YYYY>/<MM>/<doc-slug>_<version>_<sha256-8>.<ext>
  backups/
    <YYYY-MM-DD>T<HHMM>-PKT/
      manifest.json
      database.dump                     # method TBD at provisioning
      files/                            # file-store copy for this backup
  manifests/
    <dataset-or-backup-id>_manifest.json
  tmp/
    ...                                 # scratch only; NEVER a system of record; may be deleted freely
```

Rules for the layout:

- **Relative only.** Database `storage_path` values start at the
  class directory (`raw/…`, `parquet/…`, …), never at `/` or a drive
  letter. The storage root itself is configuration, not data.
- **Date in path = collection/creation date in PKT**, not a business
  date, except for Parquet partitions where the partition key IS the
  business date (§6) — the two uses are distinguished by the directory
  (`raw/<source>/<YYYY>/<MM>/` = collection month; `parquet/…/
  trading_date=…/` = business date). Confusing them breaks both
  retention (which is collection-based for raw, business-based for
  history) and partition pruning.
- **Hash suffix.** Every file name carries the first 8 hex chars of
  its SHA-256 (full hash in the manifest/database row). Two files
  with the same content have the same full hash (§7) and must not be
  stored twice under different names.
- **`tmp/` is not storage.** Anything in `tmp/` may be deleted at any
  time without audit. Nothing that matters (raw, processed, Parquet,
  report, backup) may live only in `tmp/`.
- **No spaces or user-supplied filenames unsanitised.** Slugs are
  lowercased, hyphenated, and stripped of path separators. A filename
  containing `../` is a security/robustness bug, not an edge case.

## 5. Schemas (file-level)

### 5.1 Raw JSON schema

Raw files have NO imposed business schema — they are stored exactly
as received. What IS imposed is an envelope manifest entry per file
(or per batch, where a batch file genuinely contains many payloads):

| Manifest field | Meaning |
|---|---|
| `file_path` (relative) | §4 path |
| `content_sha256` | Full hash |
| `byte_size` | Bytes |
| `source_key` | Must match `data_sources.source_key` |
| `source_timestamp` | Source publication time, if provided (else `null` + `source_timestamp_missing: true`) |
| `collected_at_pkt` | Collection time, PKT-rendered |
| `payload_type` | `'json' \| 'pdf' \| 'csv' \| 'html' \| 'other'` |
| `record_count` | Rows/records in the payload, if countable (else `null` — never guessed) |
| `raw_payload_id` | Database row id, once ingested (null before ingest) |

A raw file whose envelope cannot be filled (unknown source, unknown
collection time) is quarantined, not ingested. Quarantine location:
`<storage-root>/quarantine/` (same layout rules, plus a
`quarantine_reason` in its envelope). Quarantined files are quality
issues (`data_quality_reports`), not silent drops.

### 5.2 Processed document schema

Processed JSON documents follow a minimal envelope (business fields
inside vary by entity; the envelope does not):

```json
{
  "schema_version": "processed-v1",
  "source_raw_payload_ids": [1, 2],
  "processing_method": "method-name",
  "processing_version": "v1",
  "processed_at_pkt": "2026-11-04T11:00:00+05:00",
  "records": [ "... business records ..." ]
}
```

`schema_version` is the processed-document envelope version, not the
business schema version. Business schema changes (new fields, renamed
keys) require a new `processing_version` AND a migration note in the
manifest — silent field renames break downstream readers.

### 5.3 Parquet schema

Each Parquet dataset has a schema document (in `manifests/`) stating:

- Dataset name, grain (one row = …), partition keys (§6).
- Column list with types (Parquet logical types), nullability, and
  unit/currency notes (PKR, decimal scale for prices — Parquet
  `DECIMAL(19,4)` for prices, never `DOUBLE`, mirroring the database).
- Schema version (`parquet-schema-vN`). A schema change produces a
  new dataset version directory or a new schema version in the
  manifest — old partitions are not rewritten to the new schema in
  place; readers must handle the declared schema version or the
  dataset is migrated as a whole, with the migration recorded.
- Source: database table(s) + query/filter + date range + row count
  + export timestamp (PKT) + export content hash.
- Freshness/provenance: the Parquet file inherits the provenance of
  its source rows in aggregate (source keys, max `source_timestamp`,
  staleness note) — a Parquet extract that hides its sources is not
  a valid analytical input.

### 5.4 Research-report schema

Reports are documents (Markdown/PDF/HTML as produced), not
machine-schema files. Their required metadata lives in
`agent_outputs` + a sidecar manifest entry:

| Field | Meaning |
|---|---|
| `report_slug` | Stable slug |
| `agent_execution_id` | Producing run |
| `related_ids` | Forecast/valuation/ratio ids relied on |
| `content_sha256` | File hash |
| `created_at_pkt` | Creation time, PKT |
| `status` | `'draft' \| 'final' \| 'superseded'` — a draft report must be labelled draft wherever it is listed |

### 5.5 Backup manifest schema

See §3.6 + §8. Backup manifests are JSON, versioned
(`backup-manifest-v1`), and themselves content-hashed. A backup whose
manifest hash does not match its manifest file is corrupt until
proven otherwise.

## 6. Partitioning (Parquet + database alignment)

Parquet partitioning mirrors the database partitioning decision
(indexing strategy §4: yearly database partitions on `trading_date`,
monthly escalation reserved):

| Dataset | Partition keys | Rationale |
|---|---|---|
| EOD price history | `trading_date` year/month (`year=YYYY/month=MM/` or `trading_date=YYYY-MM-DD/` for daily extracts) | Time-range queries prune partitions; archival by year is a directory move, not a rewrite |
| Snapshot history | `snapshot_date=YYYY-MM-DD/` | As-of queries are date-scoped |
| Feature snapshots | `model_version=` + `snapshot_date=` | Reproducibility: a forecast names its feature snapshot by (model version, date), which resolves to exactly one partition |
| Indicator series | `indicator_code=` + `year=` | Code-scoped series; code is low-cardinality enough to partition on |
| Forecast evaluations | `evaluation_year=` | Model/metric aggregates are year-scoped in practice |

Rules:

- Partition keys are business dates/codes, never collection dates
  (see §4 date distinction).
- Never partition by a high-cardinality key alone (e.g. per-security
  directories with thousands of tiny files). Security appears as a
  column inside partitions (and in filenames where useful), not as
  the sole partition key — except where a dataset is genuinely
  per-security and file counts stay manageable, in which case the
  manifest must justify it.
- Small partitions are a cost: a partition with a handful of rows
  wastes metadata and read overhead. Compact small daily partitions
  into monthly partitions on a scheduled archival pass (retention
  policy), and record the compaction in the manifest (old partitions
  retained or removed per retention rules — never silently dropped).
- Database and Parquet partitions must agree on the partition key
  semantics (same trading-date definition, same PKT calendar). A
  Parquet partition named by UTC date while the database partitions
  by PKT date is a join bug waiting to happen.

## 7. Duplicate prevention (content-hash addressing)

1. **Hash before write.** Every ingest computes SHA-256 of the payload
   bytes before storing. If `raw_payloads.content_sha256` already
   exists, the payload is NOT stored again — the new ingest links to
   the existing row/file and records its own collection/provenance
   (a second collection of identical bytes is a new collection event,
   not a new payload).
2. **Business-grain uniqueness is separate from hash uniqueness.**
   Hash dedup prevents storing the same bytes twice. Grain uniques
   (catalog: price grain, statement version, quote current-marker,
   holding current-marker, econ observation grain) prevent storing
   the same *fact* twice under different bytes. Both are required;
   neither replaces the other. A re-ingest that produces different
   bytes for the same fact (e.g. reordered JSON keys) passes hash
   dedup but must fail grain uniqueness — and that failure is a
   quality report, not a silent overwrite.
3. **Filenames carry hashes (§4)** so a filesystem listing alone can
   spot duplicates, without opening the database.
4. **Parquet dedup:** Parquet exports dedup by (dataset, partition,
   grain) — re-exporting the same partition with the same rows
   produces the same hash (if the writer is deterministic) or a
   manifest-noted re-export. Non-deterministic writers (timestamps
   embedded in files) must be avoided: export timestamps live in the
   manifest, never inside the Parquet file bytes, or hash comparison
   becomes meaningless.
5. **Report dedup:** identical report bytes = identical hash = one
   file, referenced by each `agent_outputs` row that produced it
   (rare, but the rule is uniform).

## 8. Indexing (file-level — distinct from database indexes)

File-level "indexing" means: how do you find a file without scanning
the whole store? Answer, in order:

1. **Database reference (primary).** `storage_path` + `content_sha256`
   on the owning row (`announcements`, `financial_statements`,
   `agent_outputs`, `raw_payloads`, …). This is the index. A file
   search that bypasses the database is a fallback, not the design.
2. **Manifests (secondary).** Per-dataset and per-backup manifests
   (§5, §3.6) list every file in the dataset/backup with hash, size,
   and grain. Manifests live in `manifests/` and are themselves
   versioned. A manifest is the inventory that makes backup
   verification and orphan detection possible.
3. **Directory layout (§4) as a coarse index.** Source + year/month
   directories prune a manual search, but they are not a substitute
   for (1) or (2). Do not build application logic that walks the
   filesystem to answer a business query — that logic belongs in the
   database + Parquet partition pruning.
4. **What is NOT a file index:** no separate search engine, no paid
   indexing service, no filename-only database. Full-text search over
   announcement/report bodies, where needed, uses the database
   `tsvector`/GIN index (indexing strategy §3.7) on extracted text,
   not a filesystem grep. If extracted text is not in the database,
   the search requirement is unmet — do not pretend a filesystem walk
   is a search index.

**Orphan / dangling-reference detection (scheduled, later phase):**
- Orphan file: file exists, no database row or manifest references it
  → quarantine + quality report. Orphans are not auto-deleted (they
  may be evidence of a failed ingest whose database row was lost).
- Dangling reference: database row references a missing file → quality
  report with severity by class (missing raw PDF = high; missing
  derived Parquet partition = medium if regenerable from the database).
  Neither condition is silently ignored.

## 9. Historical preservation

- **History is preserved by not overwriting.** Raw files, database
  append-only rows, and Parquet partitions follow the same rule:
  corrections are new versions, old versions remain until the
  retention policy explicitly archives or removes them — and for
  raw/audit classes, the policy says "never" except under the legal
  procedure (see `DATA_RETENTION_POLICY.md`).
- **Parquet archival of database partitions:** when a database
  partition ages past its online-retention threshold (retention
  policy), its rows are exported to Parquet (with manifest), the
  export is hash-verified against the database rows, and only then
  is the database partition detached/archived — not deleted without
  a verified Parquet copy. The Parquet copy then becomes the
  historical record for that period; the database retains the
  partition's manifest reference so "where did 2021 EOD go?" is
  answerable.
- **Schema evolution preserves history:** old Parquet schema versions
  remain readable (manifest states the version; readers handle it or
  the dataset is migrated as a whole with a migration record). Old
  database versions remain via Alembic history (once it exists) +
  supersede chains. Rewriting history to a new schema in place is
  prohibited by the same immutability principle as rewriting a price.
- **No "current only" storage class exists.** There is no class of
  file whose rule is "keep only the latest". Latest-state views
  (`live_quotes.is_latest`, current holdings, current symbols) are
  markers over history, not replacements for it.

## 10. Incremental updating

- **Raw ingest is incremental by collection time:** each ingest run
  stores only payloads collected in that run (hash-deduped per §7).
  Re-ingesting a whole history to "refresh" it is prohibited — it
  wastes local disk/time and risks grain-uniqueness collisions.
- **Processed documents are incremental by source change:** a
  processed document is regenerated only when its raw source(s) or
  its processing version changes. Unchanged sources → unchanged
  processed file (same hash). A nightly job that rewrites every
  processed file with a new timestamp is a bug (it breaks hash
  dedup and retention accounting).
- **Parquet is incremental by partition:** new data appends new
  partitions (or new files within the current partition, compacted
  later per §6). Existing partitions are never rewritten for new
  data; they are rewritten only for corrections, and then as a new
  partition version with the old version retained per retention
  policy.
- **Database ingest is incremental by grain:** inserts for new
  grains, supersede rows for corrections, nothing else. Bulk
  "truncate and reload" of a history table is prohibited — it
  destroys the supersede chains and audit trail that make history
  trustworthy.
- **Incremental state tracking (later phase):** each source/dataset
  needs a watermark (last successful collection/export timestamp +
  last grain covered), stored in the database (a later-phase
  operational table, not specified here beyond this requirement) or
  in a manifest — never in an operator's memory or an untracked file.
  A run without a watermark update is an incomplete run, even if its
  files look correct.

## 11. Backup and restoration procedure (specified, not performed)

1. **Backup:** (a) PostgreSQL dump (method TBD at provisioning) +
   (b) file-store copy (all classes in §3 except `tmp/`) +
   (c) manifest (§3.6) with hashes, row counts, schema/migration
   version, and backup timestamp (PKT). Store the backup under
   `backups/<timestamp-PKT>/` on local disk (and, optionally, a
   second local location / self-hosted MinIO bucket on separate
   hardware the operator already controls).
2. **Verify (immediately, not "later"):** recompute hashes from the
   backup copies and compare to the manifest; verify row counts;
   verify that a sample of database file-references resolves inside
   the backup. A backup that fails verification is not a backup —
   retry it and raise a quality report.
3. **Restore (test, not just theory):** restore to a separate
   location/instance (never over the live store without a prior
   verified backup of the live store); verify hashes + row counts +
   reference resolution (§3.6 restore rule); run the hot-query
   smoke set (indexing strategy HQ1, HQ2, HQ11 at minimum) against
   the restored copy. A restore procedure that has never been tested
   is not a restore procedure — Phase 1 does not claim one has been
   tested.
4. **Retention of backups:** see `DATA_RETENTION_POLICY.md` (backup
   retention periods, rotation, and the "never delete the only copy
   of raw/audit" rule).

## 12. Security and access notes (design-level, not an access system)

- No credential, API key, password, or secret is stored in any file
  class in this document. If a raw payload ever contains a credential
  (it must not, by source design), that payload is quarantined and
  the incident is a quality/security report — the credential is not
  stored, indexed, or backed up as data.
- File permissions are an operator/provisioning concern (local
  filesystem permissions, MinIO bucket policies where MinIO is used).
  Phase 1 specifies no permission scheme beyond: raw/audit/backups
  are not world-writable, and `tmp/` is the only freely deletable
  area.
- Redistribution/licensing: see §3.1. Local retention ≠ right to
  republish. Any publication path (reports, exports, shared Parquet)
  must pass a licensing check before it leaves the local store.

## 13. UNVERIFIED assumptions (storage-specific)

| # | Assumption | What would verify it |
|---|---|---|
| S1 | Self-hosted MinIO volume/suitability for this project's objects | A later-phase volume test on local disk; MinIO is optional, filesystem is primary (design U13) |
| S2 | Announcement PDF retrievability/stability (hence PDF storage volume) | A live sample fetch (design U5) |
| S3 | Parquet writer determinism (same rows → same hash) for the chosen writer/library | A writer test in a later phase; until then, hash comparison across re-exports is indicative, not conclusive |
| S4 | Local disk capacity for multi-year full-market history + backups | A capacity estimate once real row counts exist; Phase 1 has no row counts, so no capacity claim is made |
| S5 | Backup/restore tooling choice for PostgreSQL (dump vs filesystem backup) | A provisioning decision + a tested restore (procedure in §11, not yet performed) |
| S6 | Any file size, row count, or dataset volume | A real ingest/export run. This document contains NO volume numbers, because none have been measured. |
