# ADR-011 — Storage tiers: PostgreSQL (record) + Parquet on local filesystem (bulk) + MinIO optional only

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04

## Context

The fixed stack names PostgreSQL/SQLAlchemy/Alembic plus local filesystem +
Apache Parquet + optional self-hosted MinIO. Three storage kinds are needed:
a system of record, bulk analytical files, and (optionally) S3-compatible
object access. Each tier must have exactly one job, so a file never silently
becomes the truth.

## Decision

- **Tier 1 — system of record:** PostgreSQL (see ADR-003). Prices,
  fundamentals, PDF metadata, jobs, audit. If PostgreSQL and a file disagree,
  PostgreSQL wins and the file is regenerated.
- **Tier 2 — bulk/derived:** local filesystem + Apache Parquet (Apache-2.0,
  VERIFIED, via PyArrow, Apache-2.0 VERIFIED). OHLCV bulk exports, backtest
  frames, dataset snapshots. Every Parquet file carries its source query,
  date, and row count alongside it, and can always be regenerated from Tier 1.
  Parquet never silently replaces PostgreSQL.
- **Tier 3 — object storage: MinIO, OPTIONAL ONLY, NOT ADOPTED.** The project
  works fully on Tiers 1 + 2 + plain filesystem directories for raw PDFs and
  payloads. No core feature may depend on MinIO, and no MinIO code path is
  written in Phase 1.

## The MinIO warning (why Tier 3 is not adopted)

Public pages read for this task report: the open-source MinIO server
repository was archived/read-only in April 2026 ("no longer maintained"), with
no further upstream fixes; the vendor's current product is AIStor, whose Free
tier is a proprietary single-server licence requiring a licence key, and whose
multi-node and maintained options are paid (Docker Extended Lifecycle Support
for MinIO was also reported as a paid subscription). Consequences:

- Do not adopt MinIO as a default; do not buy or use any paid MinIO/AIStor
  tier or Docker ELS (excluded by PKR 0 in any case).
- If a future phase still wants S3-compatible storage, it must re-verify
  MinIO's status at that time, or evaluate a maintained free alternative, and
  record that decision separately.
- The safe default for raw PDFs/payloads remains the local filesystem, under
  the scaffold's rule: raw payloads stored separately from processed records.

## Consequences

- Positive: bulk analytics get columnar compression + column pruning without
  a new server; the system of record stays relational and transactional;
  PKR 0 throughout.
- Negative: two representations of overlapping data (PostgreSQL + Parquet)
  must be kept consistent by regeneration discipline, not by hope — hence the
  recorded source query/date/row count on every file.
- Constraint: a managed cloud bucket (S3/R2/GCS) is **excluded** — usage-priced
  and a hosted-service assumption, both barred by PKR 0 / no-permanent-free-
  hosting rules.

## Alternatives considered

- PostgreSQL only, no Parquet — rejected: bulk exports and backtest frames
  are needlessly expensive as row-by-row SQL.
- CSV-only bulk — rejected: no types, no compression, full scans.
- MinIO as the default object layer — rejected (warning above).
- A second columnar format alongside Parquet — rejected: duplication.

## Verification / open checks

- [ ] At Phase 2 setup: pin PyArrow; confirm Parquet round-trip (write from
  PostgreSQL query, read back, row count + checksum match). MinIO: no check
  needed — it is not adopted.
