# Phase 2 database scope — what exists and what deliberately does NOT

Date: 2026-11-04. Source of truth for the full model: Phase 1
`docs/phase-01/DATABASE_DESIGN.md` + `DATABASE_ENTITY_CATALOG.md`
(33 tables). Phase 2 creates a fraction of that on purpose.

## Created in Phase 2 (this directory, migration 20261104_0001)

| Object | Purpose |
|---|---|
| `phase2_probe` (`id` BIGINT IDENTITY PK, `probe_label` VARCHAR(100) NOT NULL, `note` TEXT, `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()) + index `idx_phase2_probe_label` | Infrastructure probe only: proves migration up/down, insert/retrieve, backup/restore, and pooling against a real PostgreSQL instance. Contains NO PSX data. |
| `alembic_version` (created by Alembic itself) | Single-row migration bookkeeping. |

## NOT created in Phase 2 (Phase 3 work — do not add here)

`users`, `roles`, `user_role_assignments`, `companies`, `securities`,
`sectors`, `symbol_history`, `exchanges`, `trading_calendars`,
`market_prices`, `live_quotes`, `market_snapshots`,
`financial_statements`, `financial_statement_line_items`, `ratios`,
`dividends`, `corporate_actions`, `announcements`, `news`,
`economic_indicators`, `valuations`, `forecasts`,
`forecast_evaluations`, `recommendations`, `portfolios`,
`portfolio_holdings`, `agent_executions`, `agent_outputs`,
`model_versions`, `data_sources`, `data_quality_reports`,
`raw_payloads`, `audit_logs`.

Phase 3 must implement those from the Phase 1 catalog (naming §5,
provenance block §6, NUMERIC(19,4) money, TIMESTAMPTZ always,
append-only history, RESTRICT on never-deleted tables), with
SQLAlchemy models owned by the backend team and Alembic migrations
reviewed before they run. A migration that adds a Phase 3 table in
Phase 2, or that uses FLOAT for money, must be rejected in review.

## Server / role / database (provisioned 2026-11-04)

- PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1), cluster 16/main,
  port 5432, data directory /var/lib/postgresql/16/main, UTF8, C.UTF-8.
- Database `psx_intelligence` (owner postgres).
- Role `psx_app`: LOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE.
  CONNECT on the database; USAGE+CREATE on schema public; default
  privileges SELECT/INSERT/UPDATE/DELETE on future tables and
  USAGE/SELECT/UPDATE on future sequences in schema public.
- Authentication: password (scram-sha-256 for host connections),
  supplied only via environment (`DATABASE_URL` / `PGPASSWORD` in
  `database/.env`, mode 0600, gitignored). No password appears in any
  committed file, migration, script, or doc in this project.
