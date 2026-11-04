# Phase 3 — Parquet and Analytical Storage

## Design (Phase 1 STORAGE_ARCHITECTURE, as implemented)

- PostgreSQL is the system of record for structured records and
  metadata: grains, versions, provenance, quality, relationships.
- The filesystem is the system of record for files: raw payloads,
  PDFs, research reports, backups, and (from Phase 5) large
  analytical time series in Parquet.
- Parquet is for large analytical time series where row-by-row
  PostgreSQL access is wasteful (e.g. full-market daily history).
  It is NOT a second source of truth: every Parquet dataset has a
  manifest (see storage_engine.md) and its rows are traceable to
  PostgreSQL provenance (source, source timestamp, quality).

## Phase 3 status: layout ready, writer guarded

- Directories exist: storage/parquet, storage/processed,
  storage/manifests.
- Writer exists: `storage/phase3_engine.py::write_parquet_dataset`.
- Writer is GUARDED: pyarrow is not installed on this VM, so it
  raises instead of faking a file. No .parquet file is claimed in
  Phase 3, and no test asserts one exists.
- When pyarrow is installed (free, Apache-2.0, Phase 5), the same
  function writes real Parquet, refuses to overwrite an existing
  dataset (a new version is a new file), and returns hash + size
  for the manifest.

## What is NOT in Phase 3

No Parquet partitioning scheme is implemented (partitioning a
zero-row dataset is premature), no DuckDB/Polars reader is
introduced, and no analytical query layer is built. Those are
Phase 5/6 decisions, to be made after measuring real ingest
volumes. Any Phase 3 document that appears to promise a Parquet
dataset should be read as this guarded design, not as data.
