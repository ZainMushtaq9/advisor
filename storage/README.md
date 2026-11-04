# Storage root — PSX Intelligence AI, Phase 2 (Team D)

Local filesystem store. Full setup, naming, sidecar schema, permissions,
and backup rules: `docs/phase-02/STORAGE_SETUP.md`.

Directories (Phase 1 layout, relative paths only in the database):

- `raw/` — write-once originals, per source (`psx-dps/`, `psxdata/`,
  `pdf/` for PDFs that ARE the raw payload), `<YYYY>/<MM>/`.
- `processed/` — derived, versioned documents (never overwrite raw).
- `financial_reports/` — statement/report PDFs and extracts.
- `parquet/` — partitioned analytical datasets (`<dataset>/` + partition
  dirs; business date, never collection date, as the partition key).
- `research_reports/` — agent/analyst reports, referenced not duplicated.
- `backups/` — `database/backup.sh` output (`<timestamp>-PKT/` + manifest).
- `manifests/` — dataset/backup manifests.
- `quarantine/` — files that cannot be ingested yet (unknown source/time);
  90-day review per retention policy, never a trash can.
- `tmp/` — scratch only, freely deletable, never a system of record.

MinIO is OPTIONAL / NOT ADOPTED (gate G-07, Phase 1 ADR-011): no MinIO
code path exists here, and no paid tier is used. Every file written via
`storage_helper.py` gets a SHA-256 sidecar (`.sidecar.json`) and is
verified on read. No PSX dataset has been downloaded in Phase 2; the
only files present are test fixtures, clearly labelled as such.
