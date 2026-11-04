# PSX Intelligence AI — Database Design (Phase 1 of 30)

> **Status: DESIGN ONLY — Phase 1, Team 6 (Database and Information Model).
> STOP AFTER PHASE 1. No Phase 2 work is included in this file.**
> No database has been created, migrated, populated, or tested against a
> live instance. No Docker container, PostgreSQL instance, or `psql`
> session exists in this workspace (verified 2026-11-04: Docker, `psql`,
> and `redis-cli` are NOT installed). The SQL-style type names and schema
> fragments in this document are **specification notation**, not a
> migration to run. SQLAlchemy models and Alembic migrations are the
> *specified* implementation route for a later phase; no model code,
> migration file, or application code is delivered in Phase 1, and
> nothing here has been executed against a database.
>
> **Team 6 files (this folder only — sibling teams' files are not touched):**
> `DATABASE_DESIGN.md` (this file),
> `DATABASE_ENTITY_CATALOG.md`,
> `DATABASE_RELATIONSHIPS.md`,
> `DATABASE_INDEXING_STRATEGY.md`,
> `STORAGE_ARCHITECTURE.md`,
> `DATA_RETENTION_POLICY.md`.
>
> **Reference, not dependency:** the separate scaffold at
> `~/workspace/psx-data-collection/` (stdlib collector, provenance /
> PKT / stale / conflict rules, `coverage.json` template) is REFERENCED
> here and must NOT be overwritten or modified by this phase. Where this
> design and that scaffold use the same field names, the scaffold's
> meaning wins for ingestion; this design's meaning wins for storage.

## 1. Scope and starting condition (reuse verbatim, 2026-11-04)

- Project folder `~/workspace/psx-intelligence-ai/` is new. Other teams may
  be creating sibling files; Team 6 writes only its six files listed above.
- Already verified (reuse, do not re-claim as newly verified):
  - `psx-dps`: ~496 trading symbols vs ~1,029 listed instruments,
    ~5 years EOD history, today's intraday ticks only, 38 sectors,
    symbol renames (e.g. ENGRO → ENGROH), multi-node 404 quirk,
    no official PSX API.
  - `psxdata`: daily OHLCV + live snapshots ONLY, no historical
    intraday archive, 1,000+ tickers, 37 sectors.
  - Eulerpool: NO PSX coverage established; vendor route only.
- SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED
  machine-use is **UNVERIFIED** — see §9. Economic-indicator entities
  therefore carry `source` + `verification_status` and must never be
  presented as if a feed exists.
- Tools in this workspace: Python 3.12.3, Node v24.22.1.
- Hard rules for this phase: no sign-ups, installs, purchases,
  credentials, API keys, broker connections, live polling, trading, or
  posting. Never invent an API, endpoint, price, or capability.
  Forecasts are probabilistic, never guaranteed. Recommendations are
  probabilistic with uncertainty and an audit trail, never guarantees.
- **Phase 1 data rule: data inspection is READ-ONLY only. No full-scale
  live data collection is done or specified as done in Phase 1.**
  Coverage claims therefore remain at the scaffold's level
  (`coverage.json`: `unknown` until a real, verified run documents it).

## 2. Budget: PKR 0 absolute zero-cost (merged brief)

- **Budget is PKR 0 for project software, database, and storage services.**
  No paid database, paid storage, paid API, or paid tool is specified,
  assumed, or required by this design.
- **Specified zero-cost stack (design choice, not an installed system):**
  local filesystem + Apache Parquet for file-based historical storage,
  optional self-hosted MinIO (S3-compatible object storage run locally,
  not a paid cloud service) for object storage where a later phase
  needs it, and PostgreSQL with SQLAlchemy + Alembic for the relational
  store and its migrations. All of these are free/open-source software;
  none is claimed to be installed, running, or provisioned here.
- **What "zero-cost" does NOT mean — mandatory disclosure:**
  local hardware, electricity, and internet connectivity are
  **EXTERNAL operating expenses** borne outside this project budget.
  They are never described as "free" in this design. If a later phase
  runs a local PostgreSQL instance, a MinIO instance, or a Parquet
  pipeline on a personal machine, the electricity, hardware wear, and
  connectivity used are real costs to the operator, even though no
  project fee is paid to a vendor. Any future cost statement that calls
  the whole setup "free" without this disclosure is incorrect.
- **Consequences for this design:**
  - No cloud database, managed warehouse, or paid object-storage tier
    appears in any table, storage path, or retention rule.
  - Storage layout (§8 and `STORAGE_ARCHITECTURE.md`) is designed for
    a local disk first, with MinIO as an *optional, self-hosted*
    alternative layout for the same objects — not as a second,
    paid system of record.
  - Retention and backup rules (`DATA_RETENTION_POLICY.md`) assume
    local-disk capacity is finite: archival to Parquet and
    deduplication are cost-control measures, not optional extras.
  - If local capacity is ever insufficient, the correct Phase 1
    answer is to narrow scope or archive — not to silently adopt a
    paid service. That decision needs explicit user approval and is
    out of scope for Phase 1.

## 3. Target platform

| Concern | Decision (design) |
|---|---|
| Production database | PostgreSQL (version to be pinned at provisioning time, not assumed here). Reasons: strong types, constraints, `timestamptz`, JSONB for raw-payload references, partial/exclusion constraints, native range partitioning, and mature audit patterns. |
| ORM / migrations (specified, not built) | SQLAlchemy models + Alembic migrations in a later phase. This phase specifies the logical model that those models must implement; it does not deliver model code or migration files. Alembic history must be linear and reviewable; append-only tables get additive migrations only (see §4.3). |
| Local-dev alternative | SQLite (file-based, zero-install) for **schema-shape review and unit tests only** in a later phase. It is NOT production-equivalent: no native `timestamptz` arithmetic identical to PostgreSQL, no range partitioning, weaker concurrency, and different JSON handling. Any code written against SQLite must be re-tested against PostgreSQL before it is called production-ready. Nothing in this phase claims either database exists. |
| File / object storage | Local filesystem as primary; Apache Parquet for historical, analytical files; optional self-hosted MinIO for object storage. Full design: `STORAGE_ARCHITECTURE.md`. The relational database stores *references* (paths/keys + content hashes) to files, not duplicate copies of large payloads, except where the catalog explicitly says a small payload is stored inline. |
| Caching / queues | NOT designed here. Redis is not installed and no cache or queue is assumed. If a later phase adds one, it must be a cache only — never the system of record for market history, forecasts, or audit records. |
| Migrations | NOT run in this phase. When provisioning happens, migrations must be versioned, reviewable, and reversible for mutable tables only; append-only tables get additive migrations (new columns nullable or new tables), never destructive rewrites of history. |

## 4. Design principles

### 4.1 Provenance first (from the collector scaffold)

Every market, financial, announcement, and news record carries the
provenance block defined in §6. The collector's rules are preserved
in storage, not just in code:

- `source` — the named source as recorded by the collector
  (e.g. a source identifier from the data-source registry, never a
  free-text guess). A record without a source is rejected.
- `source_timestamp` — the time the source itself published the value.
  A fetch/collection time is NEVER substituted for it.
- `collected_at_pkt` — when this system collected the record, in
  Asia/Karachi (PKT) terms (see §4.2).
- `freshness_seconds` — `collected_at_pkt − source_timestamp`, computed
  at ingest and stored, so staleness can be queried without recomputing.
- `is_stale` — boolean flag set at ingest against a per-source
  freshness threshold (thresholds live in `data_sources`, not hard-coded
  in queries). Stale data is flagged, never silently presented as live.
- Conflicts are kept, not merged. If two sources disagree on the same
  fact (e.g. two different prices for the same symbol/date), BOTH rows
  are stored with their own provenance, and the disagreement is recorded
  (see `data_quality_reports` and §4.3). No averaging, no silent
  "primary wins" overwrite in storage; a *display* preference may exist
  in application logic, but it must be labelled as a preference and
  must not delete the losing value.

### 4.2 Time: PKT for market meaning, tz-aware storage always

- **Market timestamps are expressed in Pakistan Standard Time
  (Asia/Karachi).** Trading dates are Pakistan trading dates.
- Storage rule: all timestamps are `TIMESTAMPTZ` (tz-aware), never
  naive. The canonical stored instant is unambiguous; presentation
  converts to Asia/Karachi. Fields named `*_pkt` in the catalog are
  the PKT rendering of that instant and must be derivable from the
  stored `timestamptz` — they are a presentation contract, not a
  second, divergent clock.
- Trading-day fields (`trading_date`) are `DATE` in PKT terms
  (the Pakistan calendar date of the session), distinct from the
  timestamp of any individual tick, quote, or snapshot.
- Never store a date/time as free text, never store a Unix epoch
  without its timezone interpretation documented, and never infer a
  missing source timestamp from the collection time.
- Trading-calendar rules (weekends, PSX holidays, half sessions) are
  data in `trading_calendars`, not code constants. A date with no
  trading-calendar row is "unknown", not "non-trading". Missing sessions
  are recorded as gaps (see §4.4), never filled with estimates.

### 4.3 Immutability of raw data and market history

- **Raw payloads are immutable.** The `raw_payloads` supporting entity
  stores a reference to (or, where size and licensing allow, a copy of)
  the source payload exactly as received, with a content hash. Raw rows
  are never UPDATED or DELETED in normal operation. Corrections arrive
  as new rows. File-level equivalent: original PDFs and raw JSON in
  `STORAGE_ARCHITECTURE.md` are write-once; see `DATA_RETENTION_POLICY.md`
  for what is never deleted.
- **Market history is append-only.** `market_prices`, `live_quotes`
  (as an append-only log with an `is_latest` marker — see §7.3),
  and `market_snapshots` rows are never updated in place to "fix" a
  price. A corrected price is a new row with a new provenance block, a
  `supersedes_id` / version marker, and a reason; queries for
  "current best-known" resolve to the latest non-superseded row
  (see `DATABASE_INDEXING_STRATEGY.md` for the as-of pattern).
  The same rule applies to `announcements` and `news` content:
  a correction is a new version, not an edit.
- **Mutable tables are the exception, and they are named as such**
  (see §7 and `DATABASE_RELATIONSHIPS.md`). Users, roles, portfolios,
  and portfolio holdings may change; their changes are still audited
  (see §4.5). Everything else defaults to append-only or versioned.
- Deletes are logical, not physical, wherever history matters:
  `deleted_at` / `status` flags, never `DELETE FROM` on market,
  financial, forecast, recommendation, or audit data. Physical deletion
  is reserved for a documented, approved data-removal procedure
  (e.g. a legal/licensing requirement) and must itself be audit-logged.
  Retention policy governs the rest: `DATA_RETENTION_POLICY.md`.

### 4.4 Gaps, not guesses

- A missing trading session, a missing EOD row, or a missing statement
  is stored as an absence plus, where the calendar expects a session,
  a `data_quality_reports` row of type "missing session/data".
  The system must never synthesise a price, interpolate a close, or
  carry a prior close forward and label it as that day's price.
- Intraday history limitation (verified): `psxdata` provides no
  historical intraday archive and `psx-dps` provides today's ticks
  only. The model therefore stores intraday ticks for today in
  `market_prices` with a `bar_type = 'tick'` / intraday marker, but
  makes NO schema promise of a multi-year intraday archive. Any
  module that needs historical intraday bars must treat that as
  an unmet data requirement, not as a column to fill.

### 4.5 Auditability

- Every consequential write — ingest, correction, forecast, recommendation,
  portfolio change, agent action, user/role change — produces an
  `audit_logs` row (called `audit_records` in the first spec; the merged
  name is `audit_logs`, with the alias noted in the catalog): who/what
  did it, when (PKT-rendered tz-aware timestamp), what entity/row, what
  changed (before/after or a reference to the superseding row), and why
  (reason code / run id).
- Audit rows are append-only and immutable. No application role may
  UPDATE or DELETE them. Retention is governed by
  `DATA_RETENTION_POLICY.md` (§ "never deleted" — audit and raw
  provenance are the core of that rule).
- Agent work is doubly traceable: `agent_executions` (a run) →
  `agent_outputs` (what it produced) → the business row it affected
  (forecast, recommendation, report) → `audit_logs`. An agent
  output that cannot be traced to an execution and a model version
  is not trusted.

### 4.6 Uncertainty is data, not decoration

- Forecasts store a distribution, not just a point value: point
  estimate + interval bounds + the distribution/quantiles or
  parameters that produced them, plus horizon, model version, and
  features snapshot reference (see `forecasts` in the catalog).
  A forecast without an uncertainty field is incomplete by design.
- Recommendations store a probability/confidence, the evidence
  (forecast ids, valuation ids, ratio ids) they rest on, and an
  expiry/validity window. They are never stored as guarantees, and
  no column named or implying "guaranteed" exists.
- Valuations store method, inputs, and sensitivity/assumptions, so a
  valuation can be reproduced or challenged, not just quoted.

### 4.7 Versioning, not overwriting

- Financial statements are restatable. `financial_statements` carries
  `period`, `statement_type`, `filing_version`, `is_restated`, and
  `supersedes_id`. Line items belong to a specific statement version,
  never to a floating "latest" statement.
- Forecasts, valuations, and recommendations are versioned by
  `model_versions` + their own `version` / `created_at` ordering.
  Evaluation (`forecast_evaluations`) always references the exact
  forecast row and model version evaluated — never "the model" in
  general.
- Reference data that changes over time (sector assignment, symbol
  identity, listing status) is history-tracked (effective dating),
  not overwritten. See §8 for symbols and §7 for sectors.

### 4.8 Full-market from the start; KSE-100 first in rollout, not in schema

- No table, constraint, or index assumes KSE-100-only membership.
  KSE-100 membership is data: an index-constituent relationship with
  effective dates (modelled via index-membership attributes on
  `securities` / snapshot index rows — see catalog notes),
  so the rollout order (KSE-100 first, then all supported PSX
  companies) is a data-loading order, not a schema change.
- The schema must hold the full listed universe without redesign:
  ~1,029 listed instruments claimed by `psx-dps` vs ~496 trading
  symbols is a *coverage reconciliation problem*, not a reason to
  cap a table. `companies` vs `securities` separation (§7) exists
  precisely so non-trading instruments, delisted names, and multiple
  securities per company do not corrupt the company count.
- Sector-count discrepancy is data, not schema: `psx-dps` claims
  38 sectors, `psxdata` claims 37. `sectors` therefore stores
  `source` + `source_sector_name` alongside a canonical name, and
  sector assignment is a dated history row, so two sources' sector
  taxonomies can coexist without forcing a premature merge.

## 5. Naming conventions

| Area | Convention | Examples |
|---|---|---|
| Tables | Lowercase plural snake_case, business noun, no prefix | `market_prices`, `financial_statements`, `agent_executions` |
| Primary keys | `id` as `BIGINT GENERATED ALWAYS AS IDENTITY` (surrogate) EXCEPT natural-key tables noted in the catalog (e.g. `trading_calendars` on `(exchange_id, trading_date)`). Surrogate keys never carry business meaning. | `companies.id`, `securities.id` |
| Foreign keys | `<referenced_table_singular>_id` | `company_id`, `security_id`, `source_id` (catalog uses `data_source_id` for the provenance link; see §6) |
| Timestamps | `*_at` for instants (`timestamptz`); `*_date` for calendar dates (`date`); PKT-rendered presentation fields suffixed `_pkt` where the catalog requires it | `collected_at_pkt`, `created_at`, `trading_date`, `period_end_date` |
| Booleans | `is_*` / `has_*` prefix | `is_stale`, `is_trading_day`, `is_restated`, `is_latest` |
| Money / prices | `NUMERIC(19,4)` for prices and per-share values; `NUMERIC(19,2)` for aggregate monetary amounts in PKR unless a source states otherwise. NEVER `FLOAT`/`DOUBLE` for money. Currency is explicit: `currency` = `'PKR'` by default for PSX data, never assumed for economic indicators. | `close_price NUMERIC(19,4)`, `amount_pkr NUMERIC(19,2)` |
| Percentages / ratios | `NUMERIC(12,6)` for ratios and rates, stored as decimals (e.g. 0.125 = 12.5%) with the unit documented per field | `pe_ratio`, `interest_rate` |
| Quantities / volumes | `BIGINT` for share volumes; `NUMERIC(19,4)` only where fractional quantities are genuinely possible | `volume BIGINT` |
| Enumerations | PostgreSQL `ENUM` types OR check-constrained `VARCHAR` — pick ONE per field at implementation and document it. This design writes enums as named value lists in the catalog; it does not claim an enum type already exists. Values are lowercase snake_case. | `status: 'active' \| 'delisted' \| 'suspended'` |
| JSON | `JSONB` only for genuinely schemaless content (raw-payload references, agent-output payloads, model hyperparameters snapshot). Business facts that are queried, filtered, or aggregated get real columns, not JSON. | `raw_payload_ref JSONB`, `parameters JSONB` |
| Soft delete / status | `status` enum + `deleted_at timestamptz NULL` on mutable tables; append-only tables use `supersedes_id` / `is_superseded` instead of deletion | — |
| Indexes | `idx_<table>_<columns>`; unique indexes `uq_<table>_<columns>` | `idx_market_prices_security_date` |
| File references | `storage_path` (relative, never absolute machine paths), `storage_backend` (`'local' \| 'minio'`), `content_sha256` — see `STORAGE_ARCHITECTURE.md` | — |

Reserved-word avoidance: no table or column is named `user` alone in
SQL — the business entity is `users`, and application code must quote
or alias accordingly. `order` is never a column name (use `sort_order`
or `display_order`).

## 6. Provenance block (required on market / financial / news records)

Every row in `market_prices`, `live_quotes`, `market_snapshots`,
`financial_statements`, `financial_statement_line_items` (inherited from
parent + own source where different), `announcements`, `news`,
`corporate_actions`, `dividends` (inherited from parent action where
applicable), `economic_indicators`, and `ratios` (where computed from
sourced inputs) carries this block. Fields are defined once here; the
catalog repeats them per entity with entity-specific notes.

| Field | Type | Meaning / rule |
|---|---|---|
| `data_source_id` | BIGINT → `data_sources.id`, NULL only where the catalog explicitly allows it | The registered source. Unregistered sources are not stored as free text. |
| `source` | VARCHAR(100) | Source identifier as recorded by the collector (denormalised for query convenience; must match `data_sources.source_key`). |
| `source_timestamp` | TIMESTAMPTZ, NULL only if the source genuinely provides none — then `source_timestamp_missing = TRUE` and the row is flagged, never backfilled | When the source published the value. Never the fetch time. |
| `collected_at_pkt` | TIMESTAMPTZ NOT NULL | When this system collected it, rendered in Asia/Karachi. |
| `freshness_seconds` | NUMERIC(12,3) NULL | `collected_at_pkt − source_timestamp` in seconds, at ingest. NULL only when `source_timestamp` is missing. |
| `is_stale` | BOOLEAN NOT NULL DEFAULT FALSE | Set at ingest against the source's threshold in `data_sources`. |
| `raw_payload_id` | BIGINT → `raw_payloads.id`, NULL only where the catalog allows it | Reference to the immutable raw payload (or its stored reference). Processed values must be traceable to it. |
| `verification_status` | VARCHAR(30) NOT NULL DEFAULT `'unverified'` | `'unverified' \| 'verified' \| 'conflicting' \| 'superseded' \| 'rejected'`. Only a documented verification step may set `'verified'`. |
| `conflict_note` | TEXT NULL | Human/machine-readable note when another source disagrees; the disagreeing row is kept separately, not merged here. |

Display rule (applies to every module): any UI, report, or agent
output that shows a sourced value must be able to show its `source`,
`source_timestamp` (PKT), and staleness flag alongside it. A value
shown without provenance is a presentation bug, not a shortcut.

## 7. Per-entity design summary (merged entity set)

Grouped by domain. Full field definitions are in
`DATABASE_ENTITY_CATALOG.md`; relationships and delete rules are in
`DATABASE_RELATIONSHIPS.md`; indexes are in
`DATABASE_INDEXING_STRATEGY.md`; file storage for the same entities
is in `STORAGE_ARCHITECTURE.md`.

Merged entity list (33 tables: 21 merged-minimum + 8 first-spec extras
+ forecast evaluations + 3 supporting):

- Merged minimum (21): `users`, `companies`, `securities`, `sectors`,
  `market_prices`, `live_quotes`, `financial_statements`, `ratios`,
  `dividends`, `corporate_actions`, `announcements`, `news`,
  `economic_indicators`, `valuations`, `forecasts`, `recommendations`,
  `portfolios`, `agent_executions`, `model_versions`, `data_sources`,
  `audit_logs`.
- First-spec extras, kept where they do not conflict (8):
  `roles`, `exchanges`, `trading_calendars`, `market_snapshots`,
  `financial_statement_line_items`, `portfolio_holdings`,
  `agent_outputs`, `data_quality_reports`.
- First-spec extra also kept: `forecast_evaluations`.
- Supporting (3): `symbol_history`, `raw_payloads`,
  `user_role_assignments`.
- Naming note: `audit_logs` is the merged name for the first spec's
  `audit_records`. They are the same entity; the catalog lists it
  once as `audit_logs (alias: audit_records)` so a reader of either
  spec finds it. No second audit table exists.

### 7.1 Identity, access, and audit

- **users** — Mutable. One row per person/account. Authentication
  details (password hashes, tokens) are NOT designed here: no
  credential storage is specified in this phase, and no column in
  this design stores a password, API key, or secret. If auth is added
  later, it must be a separate, reviewed design. Users carry display
  identity, contact reference, status, and audit timestamps only.
- **roles** — Mutable reference data. Role names and permissions
  scope are data, not code constants, so new roles do not require a
  schema change. The permission model itself (what each permission
  string means) is a later-phase application decision; this design
  stores the assignment, not the enforcement logic.
- **user_role_assignments** (supporting) — Mutable junction with
  effective dating (`valid_from`, `valid_to`), so a past role can be
  audited after it is revoked.
- **audit_logs** — Append-only, immutable. The "who did what to
  what, when, and why" log for every consequential write. No
  application role may mutate it. Never deleted except under a
  legal/provenance hold procedure — see `DATA_RETENTION_POLICY.md`.

### 7.2 Market reference data

- **exchanges** — Reference data. PSX is the primary exchange in
  this phase; the table exists so the model does not hard-code "PSX"
  into every other table and so a future exchange does not require
  redesign. Exchange identifiers, timezone (Asia/Karachi for PSX),
  and trading calendar linkage live here.
- **sectors** — Reference data with source taxonomy preserved
  (`source_sector_name` + canonical `name`). The 38-vs-37 sector
  discrepancy between `psx-dps` and `psxdata` is handled by keeping
  both taxonomies as rows with different `source` values and mapping
  them, not by picking a winner before verification.
- **companies** — Mutable slowly (name, status, listing history).
  One row per listed company (legal issuer), NOT per ticker. A
  company may have multiple securities over time.
- **securities** — One row per tradable instrument (ticker). This is
  the grain for prices, quotes, snapshots, and holdings. A security
  belongs to one company at a time in its current assignment, with
  history preserved via `symbol_history` (see §8) and dated company
  linkage where a transfer occurs.
- **symbol_history** (supporting) — Append-only rename/transfer
  history. The reason this exists: ENGRO → ENGROH and any future
  rename must not break price history, holdings, or forecasts.
  History is joined through the security's stable surrogate `id`,
  never through the ticker string alone.
- **trading_calendars** — One row per exchange per calendar date.
  `is_trading_day`, session type, and notes (holiday, half session).
  Absence of a row means "unknown", not "closed". This table is what
  makes "missing session" detection possible.

### 7.3 Market data (append-only)

- **market_prices** — The fact table. Grain: one row per
  security × trading date × bar type × source (see catalog for the
  uniqueness rule and why source is part of the grain — conflicting
  sources are kept side-by-side). Covers EOD OHLCV (available in
  principle from both `psx-dps` and `psxdata`) and today's intraday
  ticks (`psx-dps`-only, today-only). Historical intraday bars are
  NOT promised by the schema.
- **live_quotes** — Append-only log with a current marker, NOT an
  in-place "current price" overwrite. Grain: one row per
  security × source × quote instant. `is_latest` marks the newest
  row per (security, source); older rows remain as quote history
  and as the audit trail for what was shown as "live" at a given
  time. A quote row carries the full provenance block, so a stale
  quote can be recognised as stale instead of being mistaken for
  live. Live quotes are distinct from `market_prices` (history) and
  from `market_snapshots` (whole-market point-in-time views): a quote
  is per-security and transient; a snapshot is a market-wide as-of
  view; a price row is the durable history record. A later phase may
  materialise "current quote" as a view over `live_quotes` filtered
  to `is_latest = TRUE`.
- **market_snapshots** — Append-only point-in-time whole-market /
  index snapshots (the "as-of" view). Grain: one row per snapshot
  run × security (or index) × source. Snapshot-as-of queries resolve
  to the latest snapshot at or before a given PKT instant — see the
  indexing strategy for the as-of pattern. A snapshot is never
  overwritten by the next snapshot.
- **corporate_actions** — Append-only. Dividends (as events),
  splits, bonuses, rights, mergers as dated events with adjustment
  factors where the source provides them. Adjustment factors are
  stored, not applied destructively to historical prices: adjusted
  -price series are derived views, and the unadjusted series
  remains intact.
- **dividends** — Dividend detail, one-to-one with the dividend-type
  row in `corporate_actions` (see catalog). Cash/stock dividend
  amount, dividend type, ex-date, record date, payment date, and
  currency live here — not crammed into a generic corporate-action
  payload — so dividend queries, dividend history per security, and
  dividend-adjusted analysis do not need to parse free text. A
  dividend event gets exactly one `dividends` row; double-counting
  across `corporate_actions` and `dividends` is prevented by the
  one-to-one link, not by convention alone.
- **announcements** — Append-only, with PDF URL reference where the
  source provides one (`psx-dps` claims announcement PDF URLs —
  UNVERIFIED by a live run here). Original PDFs are stored per
  `STORAGE_ARCHITECTURE.md`; the database row stores the reference
  + hash, not a second copy of the PDF bytes. Content is stored as
  received plus provenance; corrections are new versions.
- **news** — Append-only, provenance-blocked. News is distinguished
  from announcements: announcements are issuer/exchange publications;
  news is third-party reporting. Both carry source + verification
  status; neither is assumed to be a live feed until verified.

### 7.4 Fundamentals

- **financial_statements** — Versioned. Grain: one row per
  company × period × statement type × filing version × source.
  Restatements are new versions with `supersedes_id`, never edits.
  Statement availability (annual/quarterly, PSX portal vs company
  investor-relations sites) is UNVERIFIED — see §9.
- **financial_statement_line_items** — Versioned with parent.
  Grain: one row per statement version × line-item key. Line-item
  keys are canonicalised (`revenue`, `net_income`, …) with the
  source's original label preserved, because per-company formats
  differ and a premature single taxonomy would lose information.
- **ratios** — Derived, versioned by computation run. A ratio row
  references its input statement versions and its computation
  method/version, so a ratio can be recomputed and challenged.
  Ratios are never hand-entered as facts without a method reference.

### 7.5 Economics (all source-dependent — see §9)

- **economic_indicators** — Append-only observations with
  `source` + `verification_status` mandatory. Indicator definitions
  (CPI, policy rate, …) are reference rows distinguished from
  observations: the catalog models definition + observation in one
  table with `indicator_code` + `observation_date` grain, and an
  explicit `verification_status` that defaults to `'unverified'`.
  No indicator value may be presented as verified until a source
  check documents it. SECP / SBP / PBS / Finance Division /
  World Bank / IMF / FRED machine-use is UNVERIFIED in this phase.

### 7.6 Analysis (probabilistic by design)

- **valuations** — Versioned. Method, inputs, assumptions, and
  sensitivity are stored alongside the value. A valuation references
  a security, a model version where applicable, and the statement /
  price inputs it used (by id, not by "latest at the time" prose).
- **forecasts** — Versioned, probabilistic. Point estimate +
  interval + distribution parameters/quantiles + horizon + model
  version + feature snapshot reference. No forecast row is valid
  without uncertainty fields (enforced by NOT NULL constraints in
  the catalog, with a documented exception only for a method that
  genuinely cannot produce intervals — which must then be flagged,
  not silently treated as a point forecast).
- **forecast_evaluations** — Append-only. One row per forecast ×
  evaluation date × metric, referencing the exact forecast row and
  the realised value's provenance. This is how "was the forecast
  any good?" is answered from data, not from memory.
- **recommendations** — Versioned, probabilistic, audited. Signal,
  confidence/probability, evidence links (forecasts, valuations,
  ratios), validity window, and status (active / superseded /
  expired). No guarantee language in any column or value list.

### 7.7 Portfolios (the only user-owned mutable financial data)

- **portfolios** — Mutable. One row per user portfolio (paper /
  tracked — this design does not connect to a broker and stores no
  brokerage account identifiers; see §9).
- **portfolio_holdings** — Mutable current state + history pattern:
  the current holding is mutable, but every change is audit-logged
  and, where a later phase requires full holding history, a
  dated holding-history pattern (new row per change, `valid_from` /
  `valid_to`) must be adopted instead of in-place updates. This
  phase specifies the audit requirement and the history-ready shape
  (effective dates on the table) so the change is additive, not a
  redesign. Holdings reference `securities.id`, never a bare ticker
  string, so renames do not corrupt holdings.

### 7.8 Agents, models, sources, quality

- **agent_executions** — Append-only run record: agent identity,
  trigger, input references, start/end (PKT-rendered), status,
  model version, cost/latency fields only where a later phase
  defines them (no cost is assumed here).
- **agent_outputs** — Append-only. One row per output artefact of an
  execution, with output type, payload reference (JSONB for
  genuinely schemaless content, typed columns for business facts),
  and links to the business rows it created or influenced.
  Research reports produced by agents are files (see
  `STORAGE_ARCHITECTURE.md`); `agent_outputs` stores their reference
  + hash, not a duplicate copy.
- **model_versions** — Immutable reference. One row per trained /
  configured model version: name, version string, training / config
  snapshot reference, metrics snapshot, status. Forecasts,
  valuations, and agent executions reference a version id, never a
  bare model name, so "the model changed" cannot silently rewrite
  history.
- **data_sources** — Mutable reference registry (the database twin
  of the collector's data-source registry). Source key, display name,
  source type, base reference (URL or identifier as documented in
  the registry — NOT a newly invented endpoint), freshness
  thresholds, reliability notes, and verification status. A source
  marked `'unverified'` may still be ingested for staging, but its
  rows carry that status and must not be presented as verified.
- **data_quality_reports** — Append-only. One row per detected issue
  (missing session, stale data, conflict, schema mismatch, failed
  validation) with severity, affected entity/row reference, and
  resolution status. Resolution is a status change + a new row where
  the underlying data changed — the original report is never deleted.
- **raw_payloads** (supporting) — Immutable. Content-hash-addressed
  store of source payloads (or, for large payloads such as PDFs,
  a durable reference + hash + size + storage location as documented
  at ingest). Processed tables reference this table; they never
  embed a second, divergent copy of "the raw data" as free text.
  File-level storage for the same payloads is in
  `STORAGE_ARCHITECTURE.md`; the database row and the file are two
  views of one provenance record, linked by content hash.

## 8. Symbol history and rename handling (normative)

This section is normative because renames are a verified PSX reality
(ENGRO → ENGROH), not a hypothetical.

1. **Stable identity is `securities.id` (surrogate), never the ticker.**
   Every price, quote, snapshot, holding, forecast, valuation, and
   recommendation references `security_id`. Ticker strings appear
   only as display / lookup attributes.
2. **`symbol_history` is append-only.** One row per
   security × symbol × effective period: `symbol`, `valid_from_date`,
   `valid_to_date` (NULL = current), `change_reason`
   (`'rename' | 'listing' | 'delisting' | 'transfer' | 'correction'`),
   `source`, and provenance. A rename inserts a new row and closes
   the old row's `valid_to_date`; it never updates the old row's
   symbol in place.
3. **Lookup rule:** resolving a ticker to a security MUST specify a
   date (the "as-of" date). `lookup(symbol, as_of_date)` returns the
   security whose `symbol_history` row covers that date. A lookup
   without a date returns the current symbol only and must be
   labelled as such.
4. **History continuity:** price history for a renamed security is
   ONE continuous series under one `security_id`. Queries by old
   ticker must resolve through `symbol_history` to the same id;
   they must not create a second security or split the series.
5. **Conflicts:** if two sources disagree on the current symbol for
   the same company, both claims are stored (different `source`
   values in `symbol_history`) and flagged in `data_quality_reports`.
   The display symbol is a labelled preference, not a deletion of
   the losing claim.
6. **Delisting / suspension:** a delisted or suspended security keeps
   its id and history. Its `securities.status` changes; its history
   is not deleted and its holdings are not silently zeroed.
7. **Non-trading instruments:** the ~496 trading vs ~1,029 listed
   gap means many listed instruments may have no trading series.
   They still get `companies` / `securities` rows (with
   `is_trading = FALSE` where established) so coverage can be
   measured honestly, instead of silently omitting them from the
   universe.

## 9. UNVERIFIED assumptions and source-dependent fields

Everything in this section is UNVERIFIED as of 2026-11-04 and must
not be quoted as established fact in later phases without a dated,
sourced verification run.

| # | Assumption / dependency | Affected entities / fields | What would verify it |
|---|---|---|---|
| U1 | SECP, SBP, PBS, Finance Division machine-readable feeds exist and are usable for the indicators named in the spec | `economic_indicators.*`, `data_sources` rows for those bodies | A documented fetch (or documented failure) per body: URL/endpoint as actually observed, format, coverage, licence |
| U2 | World Bank / IMF / FRED coverage for Pakistan indicators relevant to PSX analysis | `economic_indicators.*` | Same per-source check; FRED/World Bank/IMF are named in the task as unverified, not as confirmed feeds |
| U3 | PSX Portal financial statements are machine-readable per company | `financial_statements.*`, `financial_statement_line_items.*` | A per-company sample fetch with statement types and periods actually observed |
| U4 | Listed-company investor-relations sites provide statements in a usable form | `financial_statements.*` (`source` = company IR) | Per-company registry + sample fetch |
| U5 | `psx-dps` announcement PDF URLs are retrievable and stable | `announcements.pdf_url`, `announcements.pdf_storage_ref` | A live sample: fetch an announcement row and its PDF link, record HTTP outcome |
| U6 | `psxdata` fundamentals fields map cleanly to statement line items | `financial_statement_line_items.line_item_key`, `ratios.*` | A field-mapping sample for at least one company, with mismatches recorded |
| U7 | KSE-100 constituent list + weights are available with effective dates | Index membership attributes on `securities` / snapshot index rows | A dated constituent list as actually observed, with effective dates |
| U8 | Sector taxonomies (38 vs 37) can be mapped to one canonical list without loss | `sectors.*`, company sector history | A mapping table built from both sources' actual sector lists, with unmapped sectors flagged |
| U9 | Broker / portfolio account linkage is in scope at all | `portfolios.broker_reference` (deliberately ABSENT — see below) | An explicit user decision; no broker connection is assumed in Phase 1 |
| U10 | Intraday ticks beyond today will become available | `market_prices` intraday rows beyond one day | A source that actually provides a historical intraday archive (none verified) |
| U11 | Any specific price, quote, ratio, valuation, or forecast value | All value columns in `market_prices`, `live_quotes`, `ratios`, `valuations`, `forecasts` | A live, provenance-blocked ingest run. This design contains NO example prices. |
| U12 | PostgreSQL version, hosting, and backup/retention policy (operational) | Whole schema (operational, not logical) | A provisioning decision in a later phase; retention itself is specified in `DATA_RETENTION_POLICY.md`, but its operational enforcement is not yet built |
| U13 | Self-hosted MinIO is suitable/needed for this project's object volume | `STORAGE_ARCHITECTURE.md` MinIO layout, `storage_backend = 'minio'` | A later-phase volume test on local disk; MinIO is optional, local filesystem is primary, and neither is provisioned in Phase 1 |
| U14 | Dividend announcement fields (ex-date, record date, payment date) are available per dividend from the same source as the corporate action | `dividends.ex_date`, `record_date`, `payment_date` | A per-source dividend sample; missing dates stay NULL and flagged, never estimated |
| U15 | Live-quote freshness thresholds per source | `live_quotes.is_stale`, `data_sources.freshness_threshold_seconds` | A per-source observation of quote update cadence during market hours; thresholds in the catalog are placeholders to be calibrated, not measured values |

Deliberate omissions (not oversights):

- No `portfolios.broker_account_id`, no brokerage credentials, no
  order/execution tables. No broker connection is authorised in
  Phase 1, so the schema must not imply one.
- No password/API-key/secret columns on `users` or `data_sources`.
  Credentials, if ever needed, belong in a separate secret-management
  design, never in this database design.
- No `guaranteed_return`, `guaranteed_price`, or similar columns.
  Forecasts and recommendations are probabilistic by schema (see §4.6).
- No example prices, example tickers beyond the verified rename
  example (ENGRO → ENGROH), and no invented endpoints. Where the
  catalog shows an example value, it is labelled `EXAMPLE — not data`.

## 10. Phase 1 workflow (11 stages) — where this design sits

The merged brief requires the 11-stage workflow. This file records
Team 6's position per stage honestly; it does not claim stages that
have not happened.

| Stage | Team 6 position in Phase 1 |
|---|---|
| 1. Brainstorm | Done as design exploration: entity set, provenance, PKT, immutability, and zero-cost storage options were scoped before writing. No alternative that required a paid service was adopted. |
| 2. Research | Done from the supplied starting condition and the referenced collector scaffold / registry (READMEs and portal landing page as documented there). No new live source research is claimed. |
| 3. Validate | Partial: starting-condition facts were reused verbatim from the 2026-11-04 verification; everything else is marked UNVERIFIED in §9. Validation of a live feed is NOT claimed. |
| 4. Data inspection | READ-ONLY only. The collector scaffold and registry were read; no full-scale live data collection was performed, and no dataset was ingested, in Phase 1. |
| 5. Architecture planning | This file + its five companions. Relational model (PostgreSQL/SQLAlchemy/Alembic, specified not built) + file/object model (local filesystem + Parquet + optional self-hosted MinIO). |
| 6. Implementation specification | The catalog, relationships, indexing, storage, and retention files ARE the implementation specification for a later phase. They contain no runnable code. |
| 7. Documentation | These six files, written for a later implementer and an independent auditor to read without the author present. |
| 8. Testing strategy | DEFINED, not claimed passed. See §11. No test has been run against a database in Phase 1, because no database exists. |
| 9. Independent audit | NOT DONE in Phase 1 — it is a checkpoint gate for a later phase (see §12). This design is written to be auditable (provenance, versioning, audit logs), but auditability is not the same as having been audited. |
| 10. Correction | Corrections to this design itself are expected after audit; no correction cycle is claimed complete. |
| 11. Checkpoint | This Phase 1 checkpoint: six design files delivered, STOP AFTER PHASE 1, no Phase 2 code, migration, or collection started. |

## 11. Testing strategy (defined, NOT claimed passed)

No test outcome is claimed in Phase 1. A later phase must, before any
production claim, define and run at least:

1. **Constraint tests:** provenance-block NOT NULL rules, money-type
   (NUMERIC, not FLOAT) checks, forecast-uncertainty NOT NULL rules,
   and the `live_quotes` one-current-row-per-(security, source) rule.
2. **Rename tests:** ENGRO → ENGROH-style rename: old ticker resolves
   to the same `security_id` as-of its old date; price history is
   continuous; holdings do not split.
3. **Conflict tests:** two sources, same symbol/date, different price
   → both rows stored, conflict flagged, neither silently overwritten.
4. **Staleness tests:** a quote with an old `source_timestamp` is
   flagged `is_stale = TRUE` and is never displayed as live.
5. **Gap tests:** a missing trading session produces a quality report
   and an absence — never a synthesised price.
6. **Audit tests:** every write path in the test suite produces an
   `audit_logs` row; audit rows cannot be updated/deleted by
   application roles.
7. **Storage tests:** content-hash deduplication, Parquet round-trip
   (write → read → identical values), backup → restore → hash match.
   See `STORAGE_ARCHITECTURE.md` and `DATA_RETENTION_POLICY.md`.
8. **Zero-cost tests:** the test/provisioning checklist must confirm
   no paid service credential, subscription, or endpoint is required
   to run the stack locally; external operating expenses (hardware /
   electricity / internet) are disclosed in run documentation, not
   hidden.

Until those tests exist and pass, any statement of the form "the
database works" is premature and must not be made.

## 12. What this design does NOT do (Phase 1 boundary)

- It does not create, migrate, or seed a database.
- It does not deliver SQLAlchemy models, Alembic migrations, or any
  application code. Those are specified as the later-phase route only.
- It does not choose an ORM configuration, application framework, or
  API shape beyond the SQLAlchemy/Alembic specification above.
- It does not set operational backup schedules, hosting, or
  access-control enforcement beyond the audit/status columns and the
  retention policy those policies will need.
- It does not perform full-scale live data collection, live polling,
  or trading.
- It does not start Phase 2.

## 13. Review checklist for the next phase (before any migration)

1. Re-verify §9 items that the next phase depends on, with dated runs.
2. Pin the PostgreSQL version and the local-dev SQLite limitations
   in writing, and re-test every constraint type that differs
   between them.
3. Confirm the enum-vs-check-constraint choice per field (§5) and
   apply it consistently — do not mix both for the same field.
4. Confirm partitioning for `market_prices` (see
   `DATABASE_INDEXING_STRATEGY.md`) before the first bulk load;
   partitioning an already-large table is harder than partitioning
   an empty one.
5. Confirm that no module queries a sourced value without its
   provenance block (§6), and that stale/conflicting rows have a
   display rule before they reach any user or agent output.
6. Confirm the zero-cost stack in writing (local filesystem + Parquet
   + optional self-hosted MinIO + PostgreSQL/SQLAlchemy/Alembic, no
   paid service) and disclose external operating expenses
   (hardware / electricity / internet) in provisioning notes.
7. Obtain independent audit (workflow stage 9) before treating this
   design as approved for implementation.
