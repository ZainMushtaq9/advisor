# PSX Intelligence AI — Storage Setup (Phase 2, Team D)

Date: 2026-11-04. Status: CREATED AND TESTED on this VM.
Budget: PKR 0 — local filesystem + Parquet format only. MinIO is
OPTIONAL / NOT ADOPTED (gate G-07, Phase 1 ADR-011: community repo
reported archived in 2026, maintained options paid) — no MinIO code
path exists, no paid tier is used, no cloud bucket is used. External
operating expenses (disk, electricity) are disclosed, never called
"free" (Phase 1 rule).

Phase 1 basis: `docs/phase-01/STORAGE_ARCHITECTURE.md`
(two systems of record, relative paths, hash addressing, write-once
raw) and `DATA_RETENTION_POLICY.md` (never-deleted classes, backup
rotation, tmp/quarantine rules). This doc records what was actually
built and tested in Phase 2.

## 1. Layout actually created (under `storage/`)

Top-level classes (Phase 1 §3/§4), all present on disk:

```
storage/
  raw/                 # write-once originals
    psx-dps/           # per-source subdirectories (Phase 1 layout)
    psxdata/
    pdf/               # PDFs that ARE the raw payload
  processed/           # derived, versioned documents (never overwrite raw)
  financial_reports/   # statement/report PDFs and extracts
  parquet/             # partitioned analytical datasets
  research_reports/    # agent/analyst reports, referenced not duplicated
  backups/             # database/backup.sh output: <YYYY-MM-DD>T<HHMM>-PKT/
  manifests/           # dataset/backup manifests
  quarantine/          # un-ingestible files (unknown source/time), 90-day review
  tmp/                 # scratch only — freely deletable, never a system of record
```

Coordination note: sibling Team A skeleton files
(`storage/*/README.md`, dated 2026-11-04 06:37 UTC) pre-existed this
task and were left untouched. Team D added: `storage/README.md`,
`storage/storage_helper.py`, `storage/test_storage_helper.py`,
`storage/size_report.sh`, `.keep` markers, the Phase 2 demo file
(§5), and the backup directory (§7). No backend file was touched
(`backend/` did not exist at the time of writing).

## 2. Storage path configuration

- **Storage root is configuration, never data.** The database stores
  RELATIVE paths only (`raw/...`, `parquet/...`), never absolute
  machine paths (`/home/...`) — a backup restored to another machine
  must not break every reference (Phase 1 §4).
- For this VM the root is the project-relative `storage/` directory:
  `<project>/storage`. The helper resolves it as:
  `PSX_STORAGE_ROOT` env var if set, else the directory containing
  `storage_helper.py` (i.e. `storage/` itself).
- `.env` (database side) carries `PSX_STORAGE_ROOT=storage` as a
  documented default for the backend team; the backend owns how it
  reads that value in `backend/` code.
- Parquet partition keys are BUSINESS dates/codes
  (`trading_date=YYYY-MM-DD/`, `year=`/`month=`, `model_version=`,
  `indicator_code=`), never collection dates — except that
  `raw/<source>/<YYYY>/<MM>/` uses the COLLECTION month. Confusing
  the two breaks both retention (collection-based for raw,
  business-based for history) and partition pruning (Phase 1 §4/§6).

## 3. File naming conventions

Phase 1 §4, implemented and enforced by `storage_helper.py`:

```
raw/<source-key>/<YYYY>/<MM>/<entity>_<security-or-scope>_<collected_at_pkt-ISO>_<sha256-8>.json
raw/pdf/<source-key>/<YYYY>/<MM>/<doc-id>_<sha256-8>.pdf
processed/<source-key>/<YYYY>/<MM>/<entity>_<scope>_<processing-version>_<sha256-8>.json
parquet/<dataset>/trading_date=<YYYY-MM-DD>/part-<security-or-scope>-<sha256-8>.parquet
research_reports/<agent-key>/<YYYY>/<MM>/<report-slug>_<execution-id>_<sha256-8>.md
backups/<YYYY-MM-DD>T<HHMM>-PKT/{manifest.json, database.dump, files.tar.gz}
```

Rules enforced by the helper (`validate_rel_path`):

- Relative only; `..` and leading `/` rejected (`UnsafePathError`).
- Top directory must be one of the nine classes in §1.
- Every path component is a slug matching `[a-z0-9][a-z0-9._-]*`
  (lowercase, no spaces, no user-supplied unsanitised filename).
- Every filename carries the first 8 hex chars of its SHA-256
  (`name_with_hash(stem, ext, sha256)`), so a directory listing
  alone can spot duplicates; the full hash lives in the sidecar.
- Never partition Parquet by a high-cardinality key alone (e.g.
  per-security directories with thousands of tiny files); security
  is a column inside partitions, not the sole partition key.

## 4. Metadata — sidecar JSON schema (not a code dump)

Every file written via `storage_helper.py` gets a sidecar next to
it named `<filename>.sidecar.json`:

```json
{
  "schema_version": "sidecar-v1",
  "file_path": "processed/phase2-demo/phase2-demo_c40483c0.txt",
  "content_sha256": "c40483c0a3347b1f91d5841699eba5f0f75b05da3cdf3f74a913435bedfb183b",
  "byte_size": 90,
  "payload_type": "test",
  "created_at_pkt": "2026-11-04T11:40:07.536887+05:00",
  "metadata": {"payload_type": "test"}
}
```

| Field | Meaning |
|---|---|
| `schema_version` | Always `sidecar-v1` in Phase 2 |
| `file_path` | Storage-relative path (§2) |
| `content_sha256` | Full SHA-256 of the exact bytes written |
| `byte_size` | Bytes |
| `payload_type` | `'json' \| 'pdf' \| 'csv' \| 'html' \| 'other'` (raw envelope, Phase 1 §5.1); `'test'` only for Phase 2 fixtures |
| `created_at_pkt` | Creation time rendered in Asia/Karachi (PKT) |
| `metadata` | Caller metadata: for raw files, source_key, source_timestamp (or `source_timestamp_missing: true`), collected_at_pkt, record_count (never guessed — `null` if uncountable), raw_payload_id once ingested; for processed files, source_raw_payload_ids, processing_method/version, processed_at_pkt; for reports, agent_execution_id, related_ids, status (`draft`/`final`/`superseded`) |

This sidecar is the file-level twin of the Phase 1 envelope/manifest
rules. A raw file whose envelope cannot be filled (unknown source or
unknown collection time) is quarantined (`quarantine/`), not ingested,
and becomes a `data_quality_reports` item in Phase 3 — never a silent
drop. A dataset/backup manifest (in `manifests/` or in a backup dir)
lists every file with hash, size, grain, date range, and schema
version; a Parquet file without a manifest is not trusted for
analysis (Phase 1 §5.3/§8). Parquet export timestamps live in the
manifest, never inside Parquet bytes, or hash comparison across
re-exports becomes meaningless.

## 5. Integrity checks — helper interface and tested evidence

Helper: `storage/storage_helper.py` (stdlib only, standalone — it is
NOT backend code and creates/modifies no `backend/` file; backend
code may import it or re-implement the same interface):

| Function | Behaviour |
|---|---|
| `write_bytes(rel_path, data, metadata, root)` / `write_text(...)` | Validates path, hashes bytes BEFORE storing, writes file + sidecar, then immediately reads back and verifies (write is not "done" until verify passes) |
| `read_and_verify(rel_path, root)` | Reads bytes, recomputes SHA-256, compares to sidecar hash AND byte size; raises `IntegrityError` on mismatch, missing sidecar, or missing file |
| `read_sidecar(rel_path, root)` | Returns the parsed sidecar dict |
| `validate_rel_path(rel_path)` | Raises `UnsafePathError` on unsafe/non-slug paths |
| `name_with_hash(stem, ext, sha256)` | Builds the `<stem>_<sha8>.<ext>` filename |
| `sha256_hex(data)` | SHA-256 hex digest |

Write-once rule: overwriting an existing file with DIFFERENT bytes
is refused (`IntegrityError` — a correction is a NEW file with a new
hash, per Phase 1 immutability). Overwriting with byte-identical
content is a no-op; if the sidecar is missing in that case it is
regenerated from the verified bytes (see §6, fix 2).

### Tested evidence (2026-11-04)

```bash
PYTHONDONTWRITEBYTECODE=1 python3 storage/test_storage_helper.py
# PASS: write returns sidecar with matching hash
# PASS: read back equals written content
# PASS: tampered file fails verification
# PASS: missing sidecar fails verification
# PASS: unsafe paths rejected
# PASS: overwrite with different bytes refused
# STORAGE TEST: ALL PASS   (exit 0)
```

Real-root write/read demo (a clearly labelled test file, NOT PSX
data — no PSX dataset was downloaded in Phase 2):

```
processed/phase2-demo/phase2-demo_c40483c0.txt   (90 bytes)
  "PHASE2-STORAGE-DEMO — NOT PSX DATA — written 2026-11-04 to prove write/read/integrity"
processed/phase2-demo/phase2-demo_c40483c0.txt.sidecar.json
  content_sha256 c40483c0a3347b1f91d5841699eba5f0f75b05da3cdf3f74a913435bedfb183b
  created_at_pkt 2026-11-04T11:40:07.536887+05:00
  real-root readback verified: True
```

### 6. Two real bugs found by the tests (kept, not hidden)

1. **Path-vs-str crash:** `write_bytes` passed its validated `Path`
   back into `read_and_verify`, whose validator called
   `.startswith()` — a `str` method — on the `Path`, raising
   `AttributeError`. The test caught it (exit 1, not a fake pass).
   Fix: `validate_rel_path` now coerces to `str` first and accepts
   both `str` and `Path`.
2. **Test-sequence sidecar gap:** the "missing sidecar" subtest
   deleted the sidecar, so the later "overwrite" subtest's identical
   rewrite failed on the missing sidecar instead of succeeding.
   Fix: identical-content rewrite regenerates a missing sidecar
   from the verified bytes. After both fixes, all six subtests pass.

## 7. Permissions, size monitoring, backup rules

### Permissions (applied 2026-11-04)

| Path | Mode | Why |
|---|---|---|
| `storage/raw/`, `storage/backups/` | 0750 | Raw/audit/backups are not world-writable (Phase 1 §12); group-only read keeps them out of casual browsing |
| Other class dirs (`processed/`, `parquet/`, etc.) | 0755 | Derived/report data readable by the operator's tools |
| Files written by the helper | 0644 (umask default; root-owned here) | Content integrity is by hash, not by secrecy — no credential may ever be stored as a file here (a payload containing one is quarantined and reported, Phase 1 §12) |
| `database/.env` | 0600 | The only file holding a real credential (see DATABASE_SETUP.md §4) |
| `storage/tmp/` | 0755, freely deletable | Scratch only |

### Size monitoring

```bash
bash storage/size_report.sh [storage-root]   # default: project storage/
# Prints per-class du -sh, per-class file counts (excluding sidecars),
# and df -h for the filesystem. No data is modified.
# 2026-11-04 result: total project disk 150G, 2.9G used, 147G free (2%).
# Phase 2 store itself is kilobytes (demo + backup + markers) — no
# volume claim is made, because no real ingest has run (Phase 1 S4).
```

Review cadence (Phase 1 retention §8, to be operated from Phase 3):
weekly size report in Phase 2; quarterly review of quarantine backlog,
hold dates, and backup-floor compliance once real data exists.
A growing `tmp/` or a stale `quarantine/` backlog is a quality
signal, not just a disk signal. Capacity order before any deletion:
compact Parquet → archive old partitions to verified Parquet →
deduplicate/orphan-check → escalate to the user. NEVER delete a
never-deleted class (audit, raw provenance, market history,
statements, forecasts/evaluations/recommendations, model versions,
symbol history, quality history) to save space.

### Backup inclusion / exclusion (file-store side)

Same rules as `database/backup.sh` (see DATABASE_SETUP.md §9):
backups include `raw/`, `processed/`, `financial_reports/`,
`parquet/`, `research_reports/`, `manifests/` as `files.tar.gz`;
they EXCLUDE `backups/` (recursion), `tmp/` (no retention value),
and `quarantine/` (separate review). Tested backup
`storage/backups/2026-11-04T1140-PKT/` (manifest + dump + archive,
both archive hashes re-verified against the manifest) contains the
Phase 2 demo file and its sidecar, proving the file-store copy path
works end to end. Restore does NOT auto-extract files over the live
store (see DATABASE_SETUP.md §9.3).

### Orphan / dangling-reference detection (Phase 3, specified now)

- Orphan file (exists, no DB row or manifest references it) →
  quarantine + quality report. Orphans are NOT auto-deleted (they
  may be evidence of a failed ingest whose DB row was lost).
- Dangling reference (DB row references a missing file) → quality
  report, severity by class (missing raw PDF = high; missing derived
  Parquet = medium if regenerable from the DB).
Neither condition is silently ignored (Phase 1 §8).

## 8. What Phase 2 does NOT do (boundaries)

- No PSX dataset downloaded, no raw market file ingested, no Parquet
  dataset produced from real data (Parquet is format + layout only
  in Phase 2; the first real Parquet round-trip is a Phase 3 test:
  write from a PostgreSQL query, read back, row count + checksum
  match — Phase 1 ADR-011 open check).
- No MinIO, no cloud bucket, no paid storage, no redistribution of
  any PDF (local retention ≠ right to republish; licensing check
  required before any publication path).
- No credential, API key, or secret stored in any file class.
- No `tmp/` file promoted to a system of record: anything valuable
  found in `tmp/` is an ingest bug and must be promoted to its
  proper class with provenance before `tmp/` is cleaned.
