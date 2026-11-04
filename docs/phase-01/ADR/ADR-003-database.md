# ADR-003 — Database: PostgreSQL (production) + SQLAlchemy + Alembic; SQLite dev-only

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04

## Context

PSX prices, fundamentals, PDF metadata, jobs, and audit records are naturally
relational and typed, with transactional guarantees. The fixed stack names
PostgreSQL / SQLAlchemy / Alembic. Docker, `psql`, and `redis-cli` are not
installed on this machine (VERIFIED), so local development needs a zero-service
path without silently changing the production database.

## Decision

- **Production database:** PostgreSQL, self-hosted, from the first production
  deployment. No managed instance is assumed or budgeted.
- **ORM:** SQLAlchemy — the single ORM; one model definition for all dialects.
- **Migrations:** Alembic — schema changes are versioned and reviewable, never
  applied by hand in production.
- **Local-dev database:** SQLite, explicitly dev-only (see Decisions §7 for the
  full migration rules). The switch to PostgreSQL is a configuration change
  (`DATABASE_URL`) plus a tested data migration, never a silent code edit.
- **Bulk storage is separate:** see ADR-011 (Parquet / filesystem / MinIO).

## Consequences

- Positive: typed, transactional system of record; migrations auditable;
  PKR 0 (PostgreSQL liberal BSD-style licence, VERIFIED).
- Negative: developers on SQLite can hit dialect divergences (type strictness,
  single-writer concurrency, PostgreSQL-specific types/indexes). Mitigation is
  mandatory, not optional: every migration must pass against a real PostgreSQL
  instance before any production release, even if it passed on SQLite.
- Constraint: raw source payloads are stored separately from processed records,
  and every record keeps `source`, `source_timestamp`, `collected_at_pkt`, and
  `freshness` (scaffold rules, inherited).

## Alternatives considered

- SQLite as production — rejected: single-writer, no server story.
- MySQL/MariaDB — rejected: no Phase 1 feature requires a second dialect.
- MongoDB/document store — rejected: trades away relational constraints.
- TimescaleDB — deferred: a PostgreSQL extension, only on a measured OHLCV
  bottleneck (none claimed).

## Verification / open checks

- [ ] At Phase 2 setup: pin SQLAlchemy/Alembic + driver variant; read and record
  their LICENSE files (UNVERIFIED in Phase 1); run the migration suite against
  PostgreSQL, not only SQLite.
