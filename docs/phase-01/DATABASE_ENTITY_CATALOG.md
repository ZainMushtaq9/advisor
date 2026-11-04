# PSX Intelligence AI — Database Entity Catalog (Phase 1 of 30)

> **Status: DESIGN ONLY — Phase 1, Team 6. STOP AFTER PHASE 1.**
> No table in this catalog has been created. Field types are PostgreSQL
> specification notation for a later SQLAlchemy/Alembic implementation;
> no model code or migration is delivered here. See
> `DATABASE_DESIGN.md` §§2–6 for budget (PKR 0, local filesystem +
> Parquet + optional self-hosted MinIO + PostgreSQL/SQLAlchemy/Alembic;
> hardware/electricity/internet are external operating expenses, never
> "free"), principles, naming conventions, and the provenance block.
>
> **How to read each entry:**
> - **PK** = primary key. **FK** = foreign key (`→ table.column`).
> - **P** = the provenance block from `DATABASE_DESIGN.md` §6
>   (`data_source_id`, `source`, `source_timestamp`,
>   `source_timestamp_missing`, `collected_at_pkt`, `freshness_seconds`,
>   `is_stale`, `raw_payload_id`, `verification_status`, `conflict_note`).
>   Where an entry says "P: yes", all ten fields apply unless the entry
>   says otherwise. Where it says "P: no", the entity is not a sourced
>   fact and does not carry the block.
> - **Versioning** states the historical rule for that entity; "append-only"
>   means no in-place UPDATE of business values (see
>   `DATABASE_RELATIONSHIPS.md` for delete rules).
> - Money is `NUMERIC`, never `FLOAT`. Timestamps are `TIMESTAMPTZ`,
>   dates are `DATE`. `EXAMPLE — not data` values are illustrations only.
> - **UNVERIFIED** marks any field whose source is unverified (§9 of the
>   design doc). Do not present such a field as populated until verified.

---

## 0. Merged entity list (33 tables)

Merged minimum (21): users, companies, securities, sectors,
market_prices, live_quotes, financial_statements, ratios, dividends,
corporate_actions, announcements, news, economic_indicators,
valuations, forecasts, recommendations, portfolios, agent_executions,
model_versions, data_sources, audit_logs.
First-spec extras kept (9): roles, exchanges, trading_calendars,
market_snapshots, financial_statement_line_items, portfolio_holdings,
agent_outputs, data_quality_reports, forecast_evaluations.
Supporting (3): symbol_history, raw_payloads, user_role_assignments.
Total: 33. `audit_logs` is the merged name for the first spec's
`audit_records` — one entity, listed once, not two tables.

---

## 1. users — Mutable

**Purpose:** One row per person/account who uses the system. Identity
and status only; no credentials are stored here (see design §9).

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `display_name` | VARCHAR(200) NOT NULL | As the user provides it |
| `email` | VARCHAR(320) NULL | Contact reference only; uniqueness to be decided at implementation (do not assume verified email ownership) |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'active'` | `'active' \| 'suspended' \| 'deactivated'` |
| `timezone` | VARCHAR(50) NOT NULL DEFAULT `'Asia/Karachi'` | Display timezone; market timestamps remain PKT regardless |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | Mutable-table audit timestamp; every change also writes `audit_logs` |
| `deleted_at` | TIMESTAMPTZ NULL | Soft delete only |

- **FK:** none. **Indexes:** `uq_users_email` (only if email uniqueness is confirmed at implementation; otherwise a non-unique index on `email`).
- **Relationships:** 1:N → `user_role_assignments`, `portfolios`, `audit_logs` (as actor).
- **Constraints:** `status` check constraint to the value list above.
- **Versioning / history:** Mutable. Past state is recoverable only via `audit_logs`; there is no separate user-history table in Phase 1.
- **P:** no.

## 2. roles — Mutable reference data

**Purpose:** Named roles whose assignment to users is stored, so access
scope can change without a schema change. This table stores role
identity, not enforcement logic.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `role_key` | VARCHAR(100) NOT NULL | Unique, lowercase snake_case. EXAMPLE — not data: `'analyst'`, `'viewer'`, `'admin'` are illustrative keys only, not a confirmed role set |
| `display_name` | VARCHAR(200) NOT NULL | |
| `description` | TEXT NULL | What the role is intended to allow, in prose for audit |
| `permissions` | JSONB NOT NULL DEFAULT `'[]'` | List of permission strings; their *meaning* is a later-phase application decision — this design does not define an enforcement engine |
| `is_system` | BOOLEAN NOT NULL DEFAULT FALSE | System roles must not be deletable by ordinary admin action |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |
| `deleted_at` | TIMESTAMPTZ NULL | Soft delete only |

- **FK:** none. **Indexes:** `uq_roles_role_key`.
- **Relationships:** 1:N → `user_role_assignments`.
- **Constraints:** `role_key` unique; `permissions` must be a JSON array.
- **Versioning:** Mutable reference data; assignment history lives in `user_role_assignments`.
- **P:** no.

## 3. user_role_assignments — Mutable junction, effective-dated (supporting)

**Purpose:** Who held which role, when. Effective dating preserves audit
after revocation.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `user_id` | BIGINT NOT NULL | FK → `users.id` |
| `role_id` | BIGINT NOT NULL | FK → `roles.id` |
| `valid_from` | TIMESTAMPTZ NOT NULL | |
| `valid_to` | TIMESTAMPTZ NULL | NULL = currently held |
| `granted_by_user_id` | BIGINT NULL | FK → `users.id`; NULL only if granted by system process, then `granted_by_system` must be set |
| `granted_by_system` | VARCHAR(100) NULL | System process name, if applicable |
| `revoked_reason` | TEXT NULL | Required when `valid_to` is set by revocation (application rule) |

- **Indexes:** `idx_user_roles_user`, `idx_user_roles_role`, partial unique on (`user_id`, `role_id`) where `valid_to IS NULL` (one current assignment per user+role).
- **Relationships:** N:1 → `users`, `roles`.
- **Constraints:** `valid_to IS NULL OR valid_to > valid_from`; exactly one of `granted_by_user_id` / `granted_by_system` set (check constraint at implementation).
- **Versioning:** Effective-dated history; revocation closes the row, never deletes it.
- **P:** no.

## 4. exchanges — Reference data

**Purpose:** Trading venues. PSX is primary; the table prevents
hard-coding "PSX" into every other table.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `exchange_key` | VARCHAR(50) NOT NULL | Unique. EXAMPLE — not data: `'PSX'` |
| `display_name` | VARCHAR(200) NOT NULL | |
| `country` | VARCHAR(100) NULL | |
| `timezone` | VARCHAR(50) NOT NULL DEFAULT `'Asia/Karachi'` | PSX = Asia/Karachi |
| `currency` | CHAR(3) NOT NULL DEFAULT `'PKR'` | PSX = PKR |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'active'` | `'active' \| 'inactive'` |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

- **Indexes:** `uq_exchanges_exchange_key`.
- **Relationships:** 1:N → `trading_calendars`, `securities` (via listing exchange), `market_snapshots` (index rows).
- **Constraints:** `exchange_key` unique.
- **Versioning:** Slowly mutable reference data; no history table in Phase 1.
- **P:** no (exchange identity is configuration, not a sourced fact; its calendar rows carry their own source where applicable).

## 5. sectors — Reference data, source taxonomy preserved

**Purpose:** Sector classification. Two sources disagree on the count
(`psx-dps` 38, `psxdata` 37 — verified as *claimed*, not reconciled),
so both taxonomies are stored, not merged prematurely.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `canonical_name` | VARCHAR(200) NOT NULL | Canonical display name, once mapped |
| `source_sector_name` | VARCHAR(200) NULL | The source's own label, verbatim |
| `source` | VARCHAR(100) NULL | Source identifier; NULL only for a manually canonicalised row, which must then carry `mapping_note` |
| `data_source_id` | BIGINT NULL | FK → `data_sources.id` |
| `mapping_note` | TEXT NULL | How this row maps to another source's taxonomy, or `'unmapped'` |
| `is_canonical` | BOOLEAN NOT NULL DEFAULT FALSE | TRUE only for the chosen canonical row per sector concept, once mapping is verified |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'active'` | `'active' \| 'deprecated'` |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

- **Indexes:** `idx_sectors_canonical_name`, `idx_sectors_source_name`.
- **Relationships:** 1:N → company sector history (see note below).
- **Constraints:** (`source`, `source_sector_name`) unique where both are non-NULL.
- **Versioning:** Sector assignment to a company is effective-dated history. Phase 1 models this as a dated assignment: `companies` carries `current_sector_id` (FK → `sectors.id`, NULL allowed) for the current assignment, and sector *changes* must be recorded as `audit_logs` rows plus, in a later phase, a dedicated `company_sector_history` table if assignment history queries become a requirement. Do not overwrite assignment history silently; the audit requirement is normative even though the dedicated history table is deferred.
- **P:** partial — `source` / `data_source_id` on this table are taxonomy provenance, not the full §6 block. **UNVERIFIED:** canonical mapping (design U8).

## 6. companies — Slowly mutable

**Purpose:** One row per listed company (legal issuer), NOT per ticker.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `legal_name` | VARCHAR(300) NOT NULL | |
| `short_name` | VARCHAR(200) NULL | |
| `current_sector_id` | BIGINT NULL | FK → `sectors.id` (current assignment; history per §5 note) |
| `incorporation_country` | VARCHAR(100) NULL | Do not guess; NULL if unverified |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'active'` | `'active' \| 'delisted' \| 'suspended' \| 'merged' \| 'unknown'` |
| `listing_date` | DATE NULL | First listing date, if verified |
| `delisting_date` | DATE NULL | Required when `status = 'delisted'` (application rule) |
| `website` | VARCHAR(500) NULL | Company investor-relations / official site, if verified — NOT an invented URL |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |
| `deleted_at` | TIMESTAMPTZ NULL | Soft delete only; delisting is a status, not a deletion |

- **Indexes:** `idx_companies_sector`, `idx_companies_status`, `idx_companies_legal_name`.
- **Relationships:** 1:N → `securities`, `financial_statements`, `announcements` (via company or security — see entry 15).
- **Constraints:** `delisting_date IS NULL OR status = 'delisted'` (with `merged` allowed a successor reference in a later phase if needed; not specified here).
- **Versioning:** Slowly mutable; material changes audit-logged. Full company-history versioning is deferred; status/date changes must be audit-logged.
- **P:** no (company identity is reference data; its statements, prices, and announcements carry P).

## 7. securities — One row per tradable instrument

**Purpose:** The grain for prices, quotes, snapshots, holdings, forecasts,
valuations, and recommendations. Never confuse with `companies`.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK — the stable identity; tickers are attributes, never keys |
| `company_id` | BIGINT NOT NULL | FK → `companies.id` |
| `exchange_id` | BIGINT NOT NULL | FK → `exchanges.id` |
| `current_symbol` | VARCHAR(50) NOT NULL | Current display ticker; history in `symbol_history`. Must match the open `symbol_history` row (application invariant, checked at implementation) |
| `security_type` | VARCHAR(50) NOT NULL DEFAULT `'ordinary_share'` | `'ordinary_share' \| 'preference_share' \| 'debt' \| 'other'` — extend only with a documented source value; do not invent types per company |
| `is_trading` | BOOLEAN NOT NULL DEFAULT TRUE | FALSE for listed-but-non-trading instruments (the ~496 vs ~1,029 gap) |
| `is_kse100_constituent` | BOOLEAN NOT NULL DEFAULT FALSE | Current membership flag; dated membership history is via index snapshot rows — this flag alone is NOT membership history |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'active'` | `'active' \| 'suspended' \| 'delisted' \| 'unknown'` |
| `face_value_pkr` | NUMERIC(19,4) NULL | If verified from a source; NULL otherwise |
| `lot_size` | BIGINT NULL | If verified; NULL otherwise |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

- **Indexes:** `idx_securities_company`, `idx_securities_exchange`, `idx_securities_current_symbol`, `idx_securities_kse100` (partial, where `is_kse100_constituent = TRUE`).
- **Relationships:** 1:N → `symbol_history`, `market_prices`, `live_quotes`, `market_snapshots`, `corporate_actions`, `dividends` (via corporate action), `announcements`, `valuations`, `forecasts`, `recommendations`, `portfolio_holdings`. N:1 → `companies`, `exchanges`.
- **Constraints:** `current_symbol` non-empty; `is_kse100_constituent` membership with effective dates is UNVERIFIED (design U7) — the flag must not be presented as dated membership history.
- **Versioning:** Mutable current attributes + append-only `symbol_history`. Price/holding history is never re-keyed on rename.
- **P:** no on the row itself; every price/quote/snapshot row for the security carries P.

## 8. symbol_history — Append-only (supporting)

**Purpose:** Rename/transfer history. Normative rules: design §8.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `security_id` | BIGINT NOT NULL | FK → `securities.id` |
| `symbol` | VARCHAR(50) NOT NULL | Ticker valid for the period |
| `valid_from_date` | DATE NOT NULL | First date this symbol applied |
| `valid_to_date` | DATE NULL | NULL = current; closed by a later row, never edited to erase history |
| `change_reason` | VARCHAR(30) NOT NULL | `'rename' \| 'listing' \| 'delisting' \| 'transfer' \| 'correction'` |
| `source` | VARCHAR(100) NOT NULL | Source of the rename claim |
| `data_source_id` | BIGINT NULL | FK → `data_sources.id` |
| `note` | TEXT NULL | EXAMPLE — not data: a rename note must cite its source; the ENGRO → ENGROH example is the only rename cited in this design, from the verified starting condition |
| `created_at` | TIMESTAMPTZ NOT NULL | Append-only: no `updated_at` (a correction is a new row) |

- **Indexes:** `uq_symbol_history_security_symbol_from` on (`security_id`, `symbol`, `valid_from_date`); `idx_symbol_history_symbol_date` on (`symbol`, `valid_from_date`, `valid_to_date`).
- **Relationships:** N:1 → `securities`.
- **Constraints:** No overlapping valid periods for the same security unless sources conflict — in which case both rows are kept with different `source` values and a `data_quality_reports` row is raised (see design §8 rule 5). Overlapping-period validation must therefore allow multi-source conflict rows and flag them, not reject them silently.
- **Versioning:** Append-only by definition.
- **P:** partial (source fields above); full §6 block applies to the price rows that use the symbol, not to this reference row.

## 9. trading_calendars — Natural-key reference data

**Purpose:** Which dates are trading days, per exchange. Enables
"missing session" detection. Absence = unknown, not closed.

| Field | Type | Constraints / notes |
|---|---|---|
| `exchange_id` | BIGINT NOT NULL | FK → `exchanges.id`; part of PK |
| `trading_date` | DATE NOT NULL | PKT calendar date; part of PK |
| `is_trading_day` | BOOLEAN NOT NULL | |
| `session_type` | VARCHAR(30) NOT NULL DEFAULT `'full'` | `'full' \| 'half' \| 'closed' \| 'unknown'` |
| `note` | TEXT NULL | Holiday name / reason, if verified from a source — never guessed |
| `source` | VARCHAR(100) NULL | Source of the calendar claim |
| `data_source_id` | BIGINT NULL | FK → `data_sources.id` |
| `created_at` | TIMESTAMPTZ NOT NULL | |

- **PK:** (`exchange_id`, `trading_date`). **Indexes:** PK index + `idx_trading_calendars_date` on (`trading_date`, `is_trading_day`).
- **Relationships:** N:1 → `exchanges`.
- **Constraints:** `is_trading_day = FALSE` implies `session_type IN ('closed', 'unknown')` (application rule at implementation).
- **Versioning:** Calendar corrections are new information: a corrected row replaces the calendar *fact* for that date but the change must be audit-logged, and any `data_quality_reports` raised from the old calendar must not be silently deleted.
- **P:** partial (source fields above). **UNVERIFIED:** no PSX holiday calendar source is verified in Phase 1; calendar rows must not be fabricated for future dates.

## 10. market_prices — Append-only fact table

**Purpose:** Durable price history: EOD OHLCV + today's intraday ticks.
The largest table in the system; partitioning is a design decision, not
a claimed implementation (see indexing strategy).

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK (surrogate; business grain is below) |
| `security_id` | BIGINT NOT NULL | FK → `securities.id` |
| `trading_date` | DATE NOT NULL | PKT trading date |
| `bar_type` | VARCHAR(30) NOT NULL | `'eod' \| 'tick' \| 'intraday'` — `'intraday'` only for aggregated intraday bars if a source ever provides them; historical intraday archive is UNVERIFIED (design U10) |
| `bar_timestamp` | TIMESTAMPTZ NULL | Required for `tick`/`intraday`; NULL for `eod` (date is the grain) |
| `open_price` / `high_price` / `low_price` / `close_price` | NUMERIC(19,4) NULL | NULL allowed individually (e.g. a tick has a price, not OHLC); at least one price field must be non-NULL (check constraint) |
| `price` | NUMERIC(19,4) NULL | Single price for tick rows (convenience; must equal the tick's trade price, not a second value) |
| `volume` | BIGINT NULL | Share volume; NULL if the source does not provide it — never zero-filled |
| `turnover_pkr` | NUMERIC(19,2) NULL | If provided; never computed silently from price × volume unless the method is documented on the row |
| `currency` | CHAR(3) NOT NULL DEFAULT `'PKR'` | |
| `is_adjusted` | BOOLEAN NOT NULL DEFAULT FALSE | TRUE only for derived adjusted series; unadjusted rows are the record |
| `adjustment_note` | TEXT NULL | Required when `is_adjusted = TRUE` (which corporate action(s) were applied, by id) |
| `supersedes_id` | BIGINT NULL | FK → `market_prices.id`; set on a correction row pointing to the row it supersedes; the superseded row gets `is_superseded = TRUE` via application logic, never by deleting it |
| `is_superseded` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `supersede_reason` | TEXT NULL | Required when `supersedes_id` is set |
| P: yes | — | Full §6 block; `raw_payload_id` links to the immutable payload |

- **Indexes:** See `DATABASE_INDEXING_STRATEGY.md` (hot: `security_id + trading_date`, `security_id + bar_timestamp`, as-of/latest queries). Business uniqueness: (`security_id`, `trading_date`, `bar_type`, `bar_timestamp`, `source`) — source is part of the grain so conflicting sources coexist; a unique constraint on this tuple is RECOMMENDED at implementation, with conflict rows handled as separate source rows, not as constraint violations to be dropped.
- **Relationships:** N:1 → `securities`, `data_sources`, `raw_payloads`; self-FK `supersedes_id`.
- **Constraints:** Price/volume non-negativity checks (`>= 0` where applicable); `high >= low` when both present; `bar_timestamp` required for tick/intraday; at least one price non-NULL.
- **Versioning:** Append-only + supersede chain. Never UPDATE a price in place.
- **UNVERIFIED:** No price value is given in this design (design U11).

## 11. live_quotes — Append-only log with current marker

**Purpose:** Per-security latest quote per source, with full provenance
and staleness, so "live" is never a bare number. Distinct from durable
`market_prices` history and whole-market `market_snapshots`.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `security_id` | BIGINT NOT NULL | FK → `securities.id` |
| `quote_timestamp` | TIMESTAMPTZ NOT NULL | Source's quote instant (PKT-rendered); distinct from `source_timestamp` in P where the source distinguishes them — if it does not, both carry the same instant and that equivalence must be documented per source |
| `last_price` | NUMERIC(19,4) NULL | |
| `open_price` / `high_price` / `low_price` | NUMERIC(19,4) NULL | Day's OHLC as quoted, if provided |
| `volume` | BIGINT NULL | |
| `bid_price` / `ask_price` | NUMERIC(19,4) NULL | If the source provides an order-book quote; NULL otherwise — never synthesised |
| `bid_volume` / `ask_volume` | BIGINT NULL | |
| `change_pkr` | NUMERIC(19,4) NULL | As quoted, if provided; not recomputed silently |
| `change_pct` | NUMERIC(12,6) NULL | Decimal (0.01 = 1%); as quoted, if provided |
| `currency` | CHAR(3) NOT NULL DEFAULT `'PKR'` | |
| `market_status` | VARCHAR(30) NULL | `'open' \| 'closed' \| 'pre_open' \| 'unknown'` — as stated by the source, if stated; NULL if unstated |
| `is_latest` | BOOLEAN NOT NULL DEFAULT TRUE | TRUE only for the newest row per (`security_id`, `source`); older rows are history, not garbage |
| P: yes | — | Full §6 block; staleness is the point of this table — `is_stale` + `freshness_seconds` must be shown with any quote |

- **Indexes:** Partial unique `uq_live_quotes_current` on (`security_id`, `source`) where `is_latest = TRUE`; `idx_live_quotes_security_time` on (`security_id`, `quote_timestamp` DESC).
- **Relationships:** N:1 → `securities`, `data_sources`, `raw_payloads`.
- **Constraints:** At least one price field non-NULL; `is_latest` uniqueness enforced by the partial unique index (implementation must flip the old row's flag in the same transaction as inserting the new row).
- **Versioning:** Append-only log; "current" is a marker, not an overwrite.
- **UNVERIFIED:** Quote freshness thresholds per source are placeholders to be calibrated (design U15); no quote cadence is claimed as measured.

## 12. market_snapshots — Append-only as-of views

**Purpose:** Whole-market / index snapshot runs: the market as it stood
at one instant, per security (or index) per source.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `snapshot_run_id` | UUID NOT NULL | Groups all rows of one snapshot run (one fetch = one run id) |
| `snapshot_at` | TIMESTAMPTZ NOT NULL | Run instant, PKT-rendered |
| `security_id` | BIGINT NULL | FK → `securities.id`; NULL only for index-level rows, which then require `index_code` |
| `index_code` | VARCHAR(50) NULL | EXAMPLE — not data: `'KSE-100'` as an index label; constituent weights/effective dates are UNVERIFIED (design U7) |
| `exchange_id` | BIGINT NULL | FK → `exchanges.id` |
| `last_price` / `open_price` / `high_price` / `low_price` | NUMERIC(19,4) NULL | As snapshotted |
| `volume` | BIGINT NULL | |
| `index_level` | NUMERIC(19,4) NULL | Index rows only |
| `index_change_pct` | NUMERIC(12,6) NULL | Index rows only, as provided |
| `constituent_weight` | NUMERIC(12,6) NULL | Index-constituent rows only, if provided; UNVERIFIED (U7) |
| `currency` | CHAR(3) NOT NULL DEFAULT `'PKR'` | |
| P: yes | — | Full §6 block per row (a snapshot run shares a source, but each row keeps its own provenance for audit) |

- **Indexes:** `idx_snapshots_run` on (`snapshot_run_id`); `idx_snapshots_asof` on (`security_id`, `snapshot_at` DESC) + `idx_snapshots_index_asof` on (`index_code`, `snapshot_at` DESC). See indexing strategy for the as-of pattern.
- **Relationships:** N:1 → `securities`, `exchanges`, `data_sources`, `raw_payloads`.
- **Constraints:** Exactly one of (`security_id`, `index_code`) set (check constraint); `snapshot_run_id` groups rows atomically (all-or-nothing per run at implementation).
- **Versioning:** Append-only; a new run never overwrites a prior run.
- **UNVERIFIED:** Whole-market snapshot coverage (~496 trading symbols claim) is README-claimed, not run-verified here.

## 13. financial_statements — Versioned

**Purpose:** A filed statement (annual/quarterly, consolidated/standalone)
for a company, in a specific filing version. Restatements are new versions.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `company_id` | BIGINT NOT NULL | FK → `companies.id` |
| `statement_type` | VARCHAR(50) NOT NULL | `'balance_sheet' \| 'income_statement' \| 'cash_flow' \| 'changes_in_equity' \| 'other'` |
| `period_type` | VARCHAR(30) NOT NULL | `'annual' \| 'quarterly' \| 'half_yearly' \| 'other'` |
| `period_end_date` | DATE NOT NULL | Period end (PKT calendar date) |
| `period_start_date` | DATE NULL | |
| `fiscal_year` | INTEGER NULL | As stated by the filer; NULL if unstated |
| `is_consolidated` | BOOLEAN NULL | NULL = unstated; never default-guessed |
| `is_audited` | BOOLEAN NULL | NULL = unstated |
| `filing_version` | INTEGER NOT NULL DEFAULT 1 | 1 = original; increments on restatement/re-filing |
| `is_restated` | BOOLEAN NOT NULL DEFAULT FALSE | TRUE when this version restates a prior version |
| `supersedes_id` | BIGINT NULL | FK → `financial_statements.id` |
| `is_superseded` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `filing_date` | DATE NULL | As stated; NULL if unstated |
| `original_document_ref` | VARCHAR(1000) NULL | Storage reference (path/key + hash) to the original PDF/document per `STORAGE_ARCHITECTURE.md`; NOT the PDF bytes |
| `currency` | CHAR(3) NOT NULL DEFAULT `'PKR'` | Stated currency; never assumed for a non-PKR filer without evidence |
| `unit_scale` | VARCHAR(30) NULL | `'units' \| 'thousands' \| 'millions'` as stated; line-item values must be interpreted with this scale — the scale is data, not a display guess |
| P: yes | — | Full §6 block; `source` distinguishes PSX Portal vs company IR vs other, once verified |

- **Indexes:** `idx_statements_company_period` on (`company_id`, `period_end_date`, `statement_type`); `uq_statements_version` on (`company_id`, `statement_type`, `period_end_date`, `filing_version`, `source`).
- **Relationships:** 1:N → `financial_statement_line_items`; N:1 → `companies`, `data_sources`, `raw_payloads`; self-FK `supersedes_id`.
- **Constraints:** `filing_version >= 1`; `is_restated = TRUE` requires `supersedes_id` non-NULL.
- **Versioning:** Versioned + supersede chain; line items belong to a version.
- **UNVERIFIED:** Machine-readable availability per company, statement types, and periods (design U3, U4).

## 14. financial_statement_line_items — Versioned with parent

**Purpose:** One reported line within one statement version. Canonical
key + verbatim source label, because per-company formats differ.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `financial_statement_id` | BIGINT NOT NULL | FK → `financial_statements.id` (the specific version) |
| `line_item_key` | VARCHAR(200) NOT NULL | Canonical key. EXAMPLE — not data: `'revenue'`, `'net_income'` are illustrative keys; the canonical taxonomy itself is UNVERIFIED (design U6) and must be built from observed labels, not assumed complete |
| `source_label` | VARCHAR(500) NOT NULL | The filer's/source's own label, verbatim |
| `value` | NUMERIC(19,2) NULL | In the statement's `currency` × `unit_scale`; NULL = reported as nil/unstated, distinguished from zero by `value_status` |
| `value_status` | VARCHAR(30) NOT NULL DEFAULT `'reported'` | `'reported' \| 'nil' \| 'not_disclosed' \| 'not_applicable'` |
| `is_total` | BOOLEAN NOT NULL DEFAULT FALSE | TRUE for subtotal/total rows, so summations do not double-count |
| `parent_line_item_id` | BIGINT NULL | FK → `financial_statement_line_items.id` (hierarchy within the statement, if the source structure supports it) |
| `display_order` | INTEGER NULL | Order as presented in the source |
| P: inherited | — | Inherits parent statement's provenance; own `source`/`data_source_id` only where the line's source differs from the parent's, in which case both are stored and the difference is noted |

- **Indexes:** `idx_line_items_statement` on (`financial_statement_id`); `idx_line_items_key` on (`line_item_key`, `financial_statement_id`).
- **Relationships:** N:1 → `financial_statements`; self-FK for hierarchy.
- **Constraints:** (`financial_statement_id`, `line_item_key`) unique unless the source genuinely repeats a key (then `source_label` disambiguates — flagged in quality reports, not silently merged).
- **Versioning:** Versioned with parent; editing a line means a new statement version, not an UPDATE.
- **UNVERIFIED:** Line-item taxonomy mapping (U6).

## 15. ratios — Derived, versioned by computation run

**Purpose:** Computed ratios (profitability, liquidity, leverage, valuation
multiples, …) that can be recomputed and challenged from their inputs.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `company_id` | BIGINT NOT NULL | FK → `companies.id` |
| `security_id` | BIGINT NULL | FK → `securities.id` (for per-security multiples; NULL for company-only ratios) |
| `ratio_key` | VARCHAR(200) NOT NULL | Canonical key. EXAMPLE — not data: `'pe_ratio'`, `'roe'` are illustrative; the ratio set and formulas live in the sibling financial-formulas work, not invented here |
| `ratio_value` | NUMERIC(12,6) NULL | Decimal; NULL only with `computation_status != 'computed'` |
| `unit_note` | VARCHAR(200) NULL | Unit/definition note (e.g. "decimal; 0.15 = 15%") |
| `period_end_date` | DATE NULL | Period the inputs cover |
| `computation_method` | VARCHAR(200) NOT NULL | Method/formula identifier + version (e.g. method name + version string); a ratio without a method is incomplete |
| `computation_run_id` | UUID NULL | Groups one computation run |
| `input_statement_ids` | BIGINT[] NULL | Array of `financial_statements.id` used (PostgreSQL array; SQLite-dev equivalent is a JSON list — re-test on PostgreSQL) |
| `input_price_id` | BIGINT NULL | FK → `market_prices.id`, for price-based multiples |
| `computation_status` | VARCHAR(30) NOT NULL DEFAULT `'computed'` | `'computed' \| 'failed' \| 'insufficient_inputs'` |
| `computation_note` | TEXT NULL | Required when status != `'computed'` |
| `computed_at` | TIMESTAMPTZ NOT NULL | |
| P: partial | — | Provenance of *inputs* is via input ids; own `source` = `'computed'` with `data_source_id` NULL, plus `verification_status` default `'unverified'` until a review step verifies the computation |

- **Indexes:** `idx_ratios_company_period` on (`company_id`, `period_end_date`, `ratio_key`); `idx_ratios_security` on (`security_id`, `ratio_key`).
- **Relationships:** N:1 → `companies`, `securities`, `market_prices` (input price).
- **Constraints:** `ratio_value` NULL ⟺ `computation_status != 'computed'` (application rule).
- **Versioning:** New computation = new row (new `computed_at` / run id); old rows are not overwritten, so a ratio's history is auditable.
- **UNVERIFIED:** Ratio definitions/formulas themselves are sibling-team work; this catalog does not invent them.

## 16. corporate_actions — Append-only events

**Purpose:** Dated corporate events: splits, bonuses, rights, mergers,
and dividend events (detail in `dividends`). Adjustment factors are
stored, not applied destructively.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `security_id` | BIGINT NOT NULL | FK → `securities.id` |
| `action_type` | VARCHAR(50) NOT NULL | `'dividend' \| 'split' \| 'bonus' \| 'rights' \| 'merger' \| 'other'` |
| `announcement_date` | DATE NULL | |
| `ex_date` | DATE NULL | |
| `record_date` | DATE NULL | |
| `effective_date` | DATE NULL | When the action takes effect |
| `ratio_numerator` | NUMERIC(19,6) NULL | e.g. split/bonus ratio numerator, if applicable |
| `ratio_denominator` | NUMERIC(19,6) NULL | e.g. split/bonus ratio denominator, if applicable |
| `adjustment_factor` | NUMERIC(19,8) NULL | Price-adjustment factor, if provided by the source; NULL = not provided (never estimated) |
| `description` | TEXT NULL | Source's description, verbatim where possible |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'announced'` | `'announced' \| 'effective' \| 'cancelled' \| 'superseded'` |
| `supersedes_id` | BIGINT NULL | FK → `corporate_actions.id` |
| P: yes | — | Full §6 block |

- **Indexes:** `idx_corp_actions_security_date` on (`security_id`, `ex_date`); `idx_corp_actions_type` on (`action_type`, `effective_date`).
- **Relationships:** 1:1 (optional) → `dividends` (dividend-type actions only); N:1 → `securities`, `data_sources`, `raw_payloads`.
- **Constraints:** `action_type = 'dividend'` ⟺ a `dividends` row links here (enforced at application level + checked by audit queries; see §17 note on double-counting).
- **Versioning:** Append-only + supersede chain (a cancelled action gets a new row with `status = 'cancelled'`, not a deletion).
- **UNVERIFIED:** Adjustment-factor availability per source (no source is verified to provide factors in Phase 1).

## 17. dividends — Dividend detail (1:1 with dividend corporate actions)

**Purpose:** Dividend-specific fields, queryable without parsing free
text. One dividend event = one row here + one `corporate_actions` row
of type `'dividend'`; the link prevents double-counting.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `corporate_action_id` | BIGINT NOT NULL | FK → `corporate_actions.id`, UNIQUE (1:1). The corporate action is the event envelope; this row is its dividend detail. |
| `security_id` | BIGINT NOT NULL | FK → `securities.id` (denormalised from the action for dividend-history queries; must match the action's security — checked at implementation) |
| `dividend_type` | VARCHAR(50) NOT NULL | `'cash' \| 'stock' \| 'mixed' \| 'other'` |
| `dividend_per_share_pkr` | NUMERIC(19,4) NULL | Cash amount per share, if cash/mixed and provided |
| `stock_dividend_pct` | NUMERIC(12,6) NULL | Stock dividend as decimal (0.10 = 10%), if stock/mixed and provided |
| `ex_date` | DATE NULL | Duplicated from the action for query convenience; must match the action's `ex_date` where both are set |
| `record_date` | DATE NULL | Same matching rule |
| `payment_date` | DATE NULL | |
| `currency` | CHAR(3) NOT NULL DEFAULT `'PKR'` | |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'announced'` | Mirrors the action's lifecycle; a mismatch between the two statuses is a quality-report condition |
| P: inherited | — | Inherits the corporate action's provenance; own source fields only where the dividend detail's source differs |

- **Indexes:** `uq_dividends_action` on (`corporate_action_id`); `idx_dividends_security_date` on (`security_id`, `ex_date`).
- **Relationships:** 1:1 → `corporate_actions`; N:1 → `securities`.
- **Constraints:** `corporate_action_id` unique; `dividend_type = 'cash'` requires `dividend_per_share_pkr` non-NULL OR a quality flag if the source omits it (never zero-filled); dates NULL when unverified, never estimated.
- **Versioning:** Append-only with parent action; a corrected dividend is a new action + new dividend row superseding the old pair.
- **UNVERIFIED:** Ex/record/payment date availability per source (design U14). Double-counting rule: dividend totals must count `dividends` rows OR dividend-type `corporate_actions` rows, never both — the 1:1 link is what makes that rule enforceable.

## 18. announcements — Append-only

**Purpose:** Issuer/exchange publications (results, notices, filings).
Original PDFs are files, referenced — not embedded — here.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `company_id` | BIGINT NULL | FK → `companies.id`; NULL only for market-wide announcements |
| `security_id` | BIGINT NULL | FK → `securities.id`; NULL only for company/market-wide announcements |
| `announcement_type` | VARCHAR(100) NOT NULL | Source's category, verbatim where possible; canonicalisation is UNVERIFIED |
| `title` | VARCHAR(1000) NOT NULL | |
| `body_text` | TEXT NULL | Extracted text, if available; NULL if only a PDF exists |
| `announced_at` | TIMESTAMPTZ NULL | Source publication instant, PKT-rendered; distinct from P `source_timestamp` only where the source distinguishes them |
| `pdf_url` | VARCHAR(2000) NULL | As provided by the source — NOT a newly constructed URL; `psx-dps` PDF-URL claim is UNVERIFIED (design U5) |
| `pdf_storage_path` | VARCHAR(1000) NULL | Relative storage path/key per `STORAGE_ARCHITECTURE.md` (original PDF), NULL until actually stored |
| `pdf_content_sha256` | CHAR(64) NULL | Hash of the stored PDF; required when `pdf_storage_path` is set |
| `language` | VARCHAR(20) NULL | e.g. `'en'`, `'ur'` — only if stated/observed, never guessed |
| `supersedes_id` | BIGINT NULL | FK → `announcements.id` (corrections) |
| `is_superseded` | BOOLEAN NOT NULL DEFAULT FALSE | |
| P: yes | — | Full §6 block; `raw_payload_id` links the announcement record payload |

- **Indexes:** `idx_announcements_company_date` on (`company_id`, `announced_at` DESC); `idx_announcements_security_date` on (`security_id`, `announced_at` DESC); full-text index on (`title`, `body_text`) is RECOMMENDED at implementation (PostgreSQL `tsvector`; SQLite-dev equivalent differs — re-test).
- **Relationships:** N:1 → `companies`, `securities`, `data_sources`, `raw_payloads`; self-FK `supersedes_id`.
- **Constraints:** At least one of (`company_id`, `security_id`) set, or the announcement is explicitly market-wide (then `is_market_wide = TRUE` — add this boolean at implementation if market-wide rows are needed; do not leave both FKs NULL unexplained).
- **Versioning:** Append-only + supersede chain.
- **UNVERIFIED:** PDF retrievability/stability (U5); announcement taxonomy.

## 19. news — Append-only

**Purpose:** Third-party reporting about companies, sectors, or the
market. Deliberately separate from issuer announcements.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `company_id` | BIGINT NULL | FK → `companies.id` |
| `security_id` | BIGINT NULL | FK → `securities.id` |
| `sector_id` | BIGINT NULL | FK → `sectors.id` |
| `headline` | VARCHAR(1000) NOT NULL | |
| `body_text` | TEXT NULL | |
| `article_url` | VARCHAR(2000) NULL | As provided; never constructed by guessing a URL pattern |
| `published_at` | TIMESTAMPTZ NULL | Source publication instant; NULL only if the source gives none (then flagged) |
| `author` | VARCHAR(300) NULL | As stated |
| `sentiment_label` | VARCHAR(30) NULL | `'positive' \| 'negative' \| 'neutral'` — ONLY if produced by a documented, versioned method (see `agent_outputs`/`model_versions` linkage); otherwise NULL. Sentiment is analysis, not a sourced fact, and must never be stored as if the source stated it |
| `sentiment_model_version_id` | BIGINT NULL | FK → `model_versions.id`, required when `sentiment_label` is set |
| P: yes | — | Full §6 block; news `verification_status` defaults to `'unverified'` |

- **Indexes:** `idx_news_company_date` on (`company_id`, `published_at` DESC); `idx_news_security_date` on (`security_id`, `published_at` DESC).
- **Relationships:** N:1 → `companies`, `securities`, `sectors`, `data_sources`, `raw_payloads`, `model_versions` (sentiment only).
- **Constraints:** `sentiment_label` non-NULL ⟹ `sentiment_model_version_id` non-NULL.
- **Versioning:** Append-only; corrections are new rows.
- **UNVERIFIED:** No news feed is verified in Phase 1; every news source row starts unverified.

## 20. economic_indicators — Append-only observations

**Purpose:** Macroeconomic observations (CPI, policy rate, …) with
mandatory source + verification status. Definitions and observations
share this table by grain (`indicator_code` + `observation_date`).

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `indicator_code` | VARCHAR(100) NOT NULL | Canonical code. EXAMPLE — not data: `'CPI_YOY'`, `'SBP_POLICY_RATE'` are illustrative; the indicator set is UNVERIFIED (design U1, U2) |
| `indicator_name` | VARCHAR(300) NOT NULL | Display name as defined by the source or, once verified, the canonical name |
| `observation_date` | DATE NOT NULL | Reference date of the observation (not the publication date — that is P `source_timestamp`) |
| `value` | NUMERIC(19,6) NULL | NULL only with a documented reason (`value_status`) |
| `value_status` | VARCHAR(30) NOT NULL DEFAULT `'reported'` | `'reported' \| 'revised' \| 'not_available' \| 'estimated_by_source'` — note: `'estimated_by_source'` means the SOURCE labelled it an estimate; this system never adds its own estimates |
| `unit` | VARCHAR(100) NULL | e.g. `'percent'`, `'index'`, `'PKR billions'` — as stated by the source |
| `frequency` | VARCHAR(30) NULL | `'daily' \| 'monthly' \| 'quarterly' \| 'annual' \| 'irregular'` |
| `country` | VARCHAR(100) NULL | `'Pakistan'` where applicable; NULL if unstated |
| `supersedes_id` | BIGINT NULL | FK → `economic_indicators.id` (revisions are new rows) |
| `is_superseded` | BOOLEAN NOT NULL DEFAULT FALSE | |
| P: yes, mandatory | — | Full §6 block; `verification_status` defaults to `'unverified'` and NOTHING in this table may be displayed as verified without a documented source check |

- **Indexes:** `idx_econ_code_date` on (`indicator_code`, `observation_date` DESC); `uq_econ_observation` on (`indicator_code`, `observation_date`, `source`) — source is part of the grain so conflicting sources coexist.
- **Relationships:** N:1 → `data_sources`, `raw_payloads`; self-FK `supersedes_id`.
- **Constraints:** `value` NULL ⟹ `value_status != 'reported'`; `verification_status = 'verified'` requires a verification record (application rule: a dated verification note linked via `audit_logs` or `data_quality_reports` — the mechanism is specified here, the verified rows do not yet exist).
- **Versioning:** Append-only + supersede chain for revisions.
- **UNVERIFIED:** Entire source set (U1, U2). This is the most source-dependent entity in the catalog.

## 21. valuations — Versioned

**Purpose:** A valuation of a security at a point in time, with method,
inputs, and sensitivity — reproducible, not just quotable.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `security_id` | BIGINT NOT NULL | FK → `securities.id` |
| `company_id` | BIGINT NULL | FK → `companies.id` (denormalised for company-level queries; must match the security's company) |
| `valuation_date` | DATE NOT NULL | Date the valuation is as-of |
| `method` | VARCHAR(200) NOT NULL | Method identifier + version (e.g. method name + version string); formulas are sibling-team work, not invented here |
| `model_version_id` | BIGINT NULL | FK → `model_versions.id`, where the method is model-based |
| `intrinsic_value_pkr` | NUMERIC(19,4) NULL | Per-share intrinsic value, if the method produces one |
| `fair_value_low_pkr` / `fair_value_high_pkr` | NUMERIC(19,4) NULL | Sensitivity range; both NULL if the method produces no range (never a single point disguised as a range) |
| `assumptions` | JSONB NOT NULL DEFAULT `'{}'` | Key assumptions (growth, discount rate, …) as data, so the valuation can be challenged |
| `sensitivity` | JSONB NULL | Sensitivity table (assumption → value), if computed |
| `input_statement_ids` | BIGINT[] NULL | Statement versions used |
| `input_price_id` | BIGINT NULL | FK → `market_prices.id` (reference price used) |
| `agent_execution_id` | BIGINT NULL | FK → `agent_executions.id`, where agent-produced |
| `created_at` | TIMESTAMPTZ NOT NULL | New valuation = new row |
| `supersedes_id` | BIGINT NULL | FK → `valuations.id` |

- **Indexes:** `idx_valuations_security_date` on (`security_id`, `valuation_date` DESC, `method`).
- **Relationships:** N:1 → `securities`, `companies`, `model_versions`, `market_prices`, `agent_executions`.
- **Constraints:** At least one of (`intrinsic_value_pkr`, `fair_value_low_pkr`, `fair_value_high_pkr`) non-NULL; `fair_value_low_pkr <= fair_value_high_pkr` when both present.
- **Versioning:** Versioned by (`valuation_date`, `method`, `created_at`) + supersede chain; never UPDATE a valuation in place.
- **UNVERIFIED:** Valuation methods/formulas are sibling work; no method is endorsed by this catalog.

## 22. forecasts — Versioned, probabilistic (mandatory uncertainty)

**Purpose:** A probabilistic forecast for a security (price, return, or
other target — the target must be explicit on every row).

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `security_id` | BIGINT NOT NULL | FK → `securities.id` |
| `model_version_id` | BIGINT NOT NULL | FK → `model_versions.id` — a forecast without a model version is incomplete |
| `target` | VARCHAR(100) NOT NULL | What is forecast. EXAMPLE — not data: `'close_price'`, `'return'` are illustrative; the target set must be fixed at implementation from verified model outputs, not assumed |
| `forecast_origin_date` | DATE NOT NULL | Date the forecast was made (as-of) |
| `horizon_days` | INTEGER NOT NULL | Forecast horizon in days; `> 0` |
| `target_date` | DATE NOT NULL | `forecast_origin_date + horizon_days` (checked at implementation; stored explicitly so evaluation joins are trivial) |
| `point_estimate` | NUMERIC(19,4) NOT NULL | Point forecast — never presented alone (see below) |
| `interval_low` / `interval_high` | NUMERIC(19,4) NOT NULL | Prediction interval bounds; the interval level (e.g. 80%, 95%) is in `interval_level_pct` |
| `interval_level_pct` | NUMERIC(5,2) NOT NULL | e.g. 80.00, 95.00 |
| `distribution_params` | JSONB NULL | Distribution parameters, if the method produces a parametric distribution |
| `quantiles` | JSONB NULL | Quantile map (e.g. `{"0.1": …, "0.5": …, "0.9": …}`), if produced; at least one of (`distribution_params`, `quantiles`) should be present for a genuinely probabilistic method — if neither is available, `uncertainty_note` must explain why and the row is flagged |
| `uncertainty_note` | TEXT NULL | Required when neither distribution nor quantiles are present |
| `feature_snapshot_ref` | VARCHAR(1000) NULL | Storage reference to the feature snapshot used (Parquet/file per `STORAGE_ARCHITECTURE.md`), so the forecast can be reproduced |
| `agent_execution_id` | BIGINT NULL | FK → `agent_executions.id` |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `supersedes_id` | BIGINT NULL | FK → `forecasts.id` |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'active'` | `'active' \| 'superseded' \| 'expired'` |

- **Indexes:** `idx_forecasts_security_target` on (`security_id`, `target_date`, `forecast_origin_date`); `idx_forecasts_model` on (`model_version_id`, `forecast_origin_date`).
- **Relationships:** 1:N → `forecast_evaluations`; N:1 → `securities`, `model_versions`, `agent_executions`; self-FK `supersedes_id`.
- **Constraints:** `interval_low <= point_estimate <= interval_high` (application check; a violation is a quality report, not a silent fix); `horizon_days > 0`; `target_date` consistent with origin + horizon; interval fields NOT NULL (the documented exception: a method that genuinely cannot produce intervals must set `uncertainty_note` AND still provide interval fields as NULL only under an explicitly approved exception — Phase 1 does not grant that exception, so implementation must treat interval NULLs as invalid until such approval exists).
- **Versioning:** Versioned by origin + model version + creation; evaluation always references the exact row.
- **UNVERIFIED:** No forecast value, accuracy, or model performance is claimed.

## 23. forecast_evaluations — Append-only

**Purpose:** How good was a specific forecast, once the target date
arrived? One row per forecast × evaluation date × metric.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `forecast_id` | BIGINT NOT NULL | FK → `forecasts.id` (the exact row evaluated) |
| `model_version_id` | BIGINT NOT NULL | FK → `model_versions.id` (must match the forecast's model version — checked at implementation) |
| `evaluation_date` | DATE NOT NULL | Date of evaluation |
| `metric` | VARCHAR(100) NOT NULL | EXAMPLE — not data: `'absolute_error'`, `'interval_coverage'` are illustrative; the metric set must be fixed at implementation |
| `metric_value` | NUMERIC(19,6) NULL | NULL only with `evaluation_note` explaining why |
| `realised_value` | NUMERIC(19,4) NULL | The realised outcome, with provenance below |
| `realised_price_id` | BIGINT NULL | FK → `market_prices.id` (the realised price row, where the target is a price) |
| `inside_interval` | BOOLEAN NULL | Whether the realised value fell inside the forecast interval; NULL if not applicable |
| `evaluation_note` | TEXT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | |

- **Indexes:** `idx_forecast_eval_forecast` on (`forecast_id`, `evaluation_date`); `idx_forecast_eval_model_metric` on (`model_version_id`, `metric`, `evaluation_date`).
- **Relationships:** N:1 → `forecasts`, `model_versions`, `market_prices`.
- **Constraints:** (`forecast_id`, `evaluation_date`, `metric`) unique.
- **Versioning:** Append-only; re-evaluation is a new row, not an edit.
- **P:** partial — realised value provenance via `realised_price_id` + the forecast's own provenance; evaluation rows themselves are computed, not sourced.

## 24. recommendations — Versioned, probabilistic, audited

**Purpose:** A probabilistic recommendation (signal + confidence +
evidence + validity window). Never a guarantee.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `security_id` | BIGINT NOT NULL | FK → `securities.id` |
| `user_id` | BIGINT NULL | FK → `users.id`; NULL for system/market-wide recommendations (then `audience` must state the scope) |
| `portfolio_id` | BIGINT NULL | FK → `portfolios.id`, where portfolio-specific |
| `signal` | VARCHAR(50) NOT NULL | Value list to be fixed at implementation from verified product decisions — Phase 1 does NOT invent a signal vocabulary. Illustrative shape only: a short signal token, never `'guaranteed_buy'` or similar |
| `confidence` | NUMERIC(5,4) NULL | Probability/confidence in [0, 1]; NULL only if the method genuinely produces no confidence, in which case `confidence_note` is required |
| `confidence_note` | TEXT NULL | |
| `evidence_forecast_ids` | BIGINT[] NULL | Forecasts relied on |
| `evidence_valuation_ids` | BIGINT[] NULL | Valuations relied on |
| `evidence_ratio_ids` | BIGINT[] NULL | Ratios relied on |
| `rationale` | TEXT NULL | Human/machine-readable reasoning summary; must not contain guarantee language |
| `valid_from` | TIMESTAMPTZ NOT NULL | |
| `valid_to` | TIMESTAMPTZ NULL | NULL = open-ended (discouraged; a validity window is preferred and its absence must be visible) |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'active'` | `'active' \| 'superseded' \| 'expired' \| 'withdrawn'` |
| `agent_execution_id` | BIGINT NULL | FK → `agent_executions.id` |
| `model_version_id` | BIGINT NULL | FK → `model_versions.id` |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `supersedes_id` | BIGINT NULL | FK → `recommendations.id` |

- **Indexes:** `idx_recommendations_security_status` on (`security_id`, `status`, `valid_from` DESC); `idx_recommendations_user` on (`user_id`, `valid_from` DESC).
- **Relationships:** N:1 → `securities`, `users`, `portfolios`, `agent_executions`, `model_versions`; self-FK `supersedes_id`.
- **Constraints:** `confidence` in [0, 1] when present; `valid_to IS NULL OR valid_to > valid_from`; at least one evidence array non-empty OR `rationale` non-NULL (a recommendation with no evidence and no rationale is incomplete).
- **Versioning:** Versioned + supersede chain; withdrawal/supersession is a status change on a new row or a status update audit-logged — the original row's content is never rewritten.
- **UNVERIFIED:** Signal vocabulary, confidence calibration, and any recommendation performance claim.

## 25. portfolios — Mutable

**Purpose:** A user's tracked/paper portfolio. No broker linkage.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `user_id` | BIGINT NOT NULL | FK → `users.id` |
| `name` | VARCHAR(200) NOT NULL | |
| `description` | TEXT NULL | |
| `base_currency` | CHAR(3) NOT NULL DEFAULT `'PKR'` | |
| `portfolio_type` | VARCHAR(50) NOT NULL DEFAULT `'paper'` | `'paper' \| 'tracked'` — `'live_broker'` is DELIBERATELY ABSENT (no broker connection in Phase 1) |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'active'` | `'active' \| 'archived'` |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |
| `deleted_at` | TIMESTAMPTZ NULL | Soft delete only |

- **Indexes:** `idx_portfolios_user` on (`user_id`, `status`).
- **Relationships:** 1:N → `portfolio_holdings`, `recommendations` (portfolio-specific).
- **Constraints:** No broker account column exists by design.
- **Versioning:** Mutable; every change audit-logged.
- **P:** no.

## 26. portfolio_holdings — Mutable current state, history-ready

**Purpose:** What a portfolio holds, in what quantity. References
`securities.id`, never a ticker string.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `portfolio_id` | BIGINT NOT NULL | FK → `portfolios.id` |
| `security_id` | BIGINT NOT NULL | FK → `securities.id` |
| `quantity` | NUMERIC(19,4) NOT NULL | `>= 0`; fractional only where genuinely applicable |
| `average_cost_pkr` | NUMERIC(19,4) NULL | Average cost per share, if tracked; NULL if not tracked (never zero-filled) |
| `currency` | CHAR(3) NOT NULL DEFAULT `'PKR'` | |
| `valid_from` | TIMESTAMPTZ NOT NULL | Effective dating (history-ready shape) |
| `valid_to` | TIMESTAMPTZ NULL | NULL = current holding |
| `note` | TEXT NULL | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

- **Indexes:** `uq_holdings_current` partial unique on (`portfolio_id`, `security_id`) where `valid_to IS NULL`; `idx_holdings_portfolio` on (`portfolio_id`, `valid_from`).
- **Relationships:** N:1 → `portfolios`, `securities`.
- **Constraints:** `quantity >= 0`; one current row per (portfolio, security).
- **Versioning:** Current row mutable in Phase 1 shape, BUT every change must be audit-logged, and a later phase requiring full holding history must adopt the dated-row pattern (close old row, insert new row) instead of in-place updates. The `valid_from`/`valid_to` columns exist now so that change is additive.
- **P:** no (user-owned data, not sourced facts; its valuation uses sourced prices via `market_prices`).

## 27. agent_executions — Append-only run record

**Purpose:** One run of one agent: what ran, why, with what inputs,
what model, when, and how it ended.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `agent_key` | VARCHAR(200) NOT NULL | Agent identifier (must match the sibling agent registry's keys — the registry itself is sibling-team work; this design does not invent agent names) |
| `trigger_type` | VARCHAR(50) NOT NULL | `'scheduled' \| 'manual' \| 'event' \| 'other'` |
| `trigger_ref` | VARCHAR(500) NULL | Schedule/event/manual reference |
| `input_refs` | JSONB NULL | References to inputs (entity ids, file refs) — not free-text input dumps |
| `model_version_id` | BIGINT NULL | FK → `model_versions.id`, where model-based |
| `started_at` | TIMESTAMPTZ NOT NULL | PKT-rendered |
| `ended_at` | TIMESTAMPTZ NULL | NULL while running |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'running'` | `'running' \| 'succeeded' \| 'failed' \| 'cancelled'` |
| `error_message` | TEXT NULL | Required when `status = 'failed'` (truncated at implementation if needed; never a credential) |
| `user_id` | BIGINT NULL | FK → `users.id`, where user-triggered |

- **Indexes:** `idx_agent_exec_agent_time` on (`agent_key`, `started_at` DESC); `idx_agent_exec_status` on (`status`, `started_at`).
- **Relationships:** 1:N → `agent_outputs`, `valuations`, `forecasts`, `recommendations` (agent-produced rows); N:1 → `model_versions`, `users`.
- **Constraints:** `ended_at IS NULL OR ended_at >= started_at`; `status = 'failed'` requires `error_message`.
- **Versioning:** Append-only; a re-run is a new row.
- **P:** no (execution metadata, not a sourced fact; its outputs link to sourced rows).

## 28. agent_outputs — Append-only

**Purpose:** One output artefact of one execution, linked to the
business rows it created or influenced. Research reports are files;
this row is their reference.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `agent_execution_id` | BIGINT NOT NULL | FK → `agent_executions.id` |
| `output_type` | VARCHAR(100) NOT NULL | EXAMPLE — not data: `'report'`, `'forecast'`, `'recommendation'` are illustrative; the output-type vocabulary must match the sibling agent registry |
| `title` | VARCHAR(500) NULL | |
| `payload` | JSONB NULL | Genuinely schemaless content only; business facts that are queried belong in typed tables, not here |
| `storage_path` | VARCHAR(1000) NULL | Relative path/key for file artefacts (research reports, documents) per `STORAGE_ARCHITECTURE.md` |
| `content_sha256` | CHAR(64) NULL | Required when `storage_path` is set |
| `related_forecast_id` | BIGINT NULL | FK → `forecasts.id` |
| `related_recommendation_id` | BIGINT NULL | FK → `recommendations.id` |
| `related_valuation_id` | BIGINT NULL | FK → `valuations.id` |
| `related_report_id` | VARCHAR(200) NULL | Research-report identifier, if the report has its own registry in a later phase (not defined here) |
| `created_at` | TIMESTAMPTZ NOT NULL | |

- **Indexes:** `idx_agent_outputs_execution` on (`agent_execution_id`, `created_at`).
- **Relationships:** N:1 → `agent_executions`, `forecasts`, `recommendations`, `valuations`.
- **Constraints:** At least one of (`payload`, `storage_path`) set; `content_sha256` required with `storage_path`.
- **Versioning:** Append-only.
- **P:** no on the row; linked business rows carry their own provenance.

## 29. model_versions — Immutable reference

**Purpose:** One trained/configured model version. Forecasts, valuations,
agent executions, and sentiment labels reference an id, never a name.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `model_name` | VARCHAR(200) NOT NULL | |
| `version` | VARCHAR(100) NOT NULL | Version string as assigned by the model owner (semantic or dated — must be documented per model) |
| `model_type` | VARCHAR(100) NULL | e.g. model family, if known — never guessed |
| `config_snapshot_ref` | VARCHAR(1000) NULL | Storage reference to the config/hyperparameters snapshot (file per `STORAGE_ARCHITECTURE.md`) |
| `hyperparameters` | JSONB NULL | Small hyperparameter snapshot inline, if appropriate; large snapshots belong in files, referenced above |
| `training_data_ref` | VARCHAR(1000) NULL | Reference to the training-data snapshot (what data, what date range, what hash) — provenance for the model itself |
| `metrics_snapshot` | JSONB NULL | Evaluation metrics as measured at versioning time, with metric names and dates — never a bare "accuracy" without context |
| `status` | VARCHAR(30) NOT NULL DEFAULT `'active'` | `'active' \| 'deprecated' \| 'retired'` |
| `created_at` | TIMESTAMPTZ NOT NULL | No `updated_at`: a changed model is a new version, not an edit (status changes are the sole exception and must be audit-logged) |

- **Indexes:** `uq_model_versions_name_version` on (`model_name`, `version`).
- **Relationships:** 1:N → `forecasts`, `forecast_evaluations`, `valuations`, `agent_executions`, `news` (sentiment), `recommendations`.
- **Constraints:** (`model_name`, `version`) unique.
- **Versioning:** Immutable by definition.
- **P:** no (model metadata; its training-data reference carries provenance separately).

## 30. data_sources — Mutable reference registry

**Purpose:** The database twin of the collector's data-source registry.
Every sourced row must resolve to a row here (via `data_source_id`)
or be rejected.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `source_key` | VARCHAR(100) NOT NULL | Unique identifier; must match the `source` value on sourced rows. EXAMPLE — not data: `'psx-dps'`, `'psxdata'` are the registry's keys as documented in the collector scaffold |
| `display_name` | VARCHAR(300) NOT NULL | |
| `source_type` | VARCHAR(50) NOT NULL | `'market' \| 'fundamental' \| 'announcement' \| 'news' \| 'economic' \| 'other'` |
| `base_reference` | VARCHAR(1000) NULL | URL or identifier AS DOCUMENTED in the data-source registry — never a newly invented endpoint. NULL only for a source whose reference is genuinely not a URL (then `reference_note` is required) |
| `reference_note` | TEXT NULL | |
| `freshness_threshold_seconds` | NUMERIC(12,3) NULL | Staleness threshold for this source; NULL = no threshold defined (rows are then never auto-flagged stale — a gap to be closed, not a default to guess) |
| `verification_status` | VARCHAR(30) NOT NULL DEFAULT `'unverified'` | `'unverified' \| 'verified' \| 'partial' \| 'deprecated'` — only a documented check may set `'verified'` |
| `licence_note` | TEXT NULL | Licensing/redistribution constraint as documented; PSX data licensing must be verified before commercial use (see collector README) |
| `is_active` | BOOLEAN NOT NULL DEFAULT TRUE | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

- **Indexes:** `uq_data_sources_source_key`.
- **Relationships:** 1:N → every P-carrying table (via `data_source_id`), `sectors`, `trading_calendars`, `announcements`, `news`, `economic_indicators`.
- **Constraints:** `source_key` unique; `verification_status = 'verified'` requires a verification note/date (application rule; the verification record itself is an `audit_logs` entry or a registry update with a date — not a bare flag flip).
- **Versioning:** Mutable registry; changes audit-logged. Historical rows keep their original `data_source_id` even if the registry row is later deprecated.
- **P:** no (this IS the source registry).
- **UNVERIFIED:** Every source row except the README-documented `psx-dps`/`psxdata` claims starts unverified; SECP/SBP/PBS/Finance Division/World Bank/IMF/FRED rows, if created, start `'unverified'` (design U1, U2).

## 31. data_quality_reports — Append-only

**Purpose:** One detected data problem: missing session, stale data,
conflict, schema mismatch, failed validation — with severity and
resolution status. The original report is never deleted.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `issue_type` | VARCHAR(100) NOT NULL | `'missing_session' \| 'missing_data' \| 'stale_data' \| 'conflict' \| 'schema_mismatch' \| 'validation_failed' \| 'other'` |
| `severity` | VARCHAR(30) NOT NULL | `'low' \| 'medium' \| 'high' \| 'critical'` |
| `affected_entity` | VARCHAR(100) NOT NULL | Table name, e.g. `'market_prices'` |
| `affected_row_id` | BIGINT NULL | Row id, where a single row is affected; NULL for range/market-wide issues (then `affected_scope` is required) |
| `affected_scope` | TEXT NULL | e.g. symbol + date range, or snapshot run id |
| `security_id` | BIGINT NULL | FK → `securities.id`, where applicable |
| `detail` | TEXT NOT NULL | What was detected, with values (never a credential) |
| `detected_at` | TIMESTAMPTZ NOT NULL | |
| `detected_by` | VARCHAR(200) NULL | Process/agent that detected it |
| `resolution_status` | VARCHAR(30) NOT NULL DEFAULT `'open'` | `'open' \| 'investigating' \| 'resolved' \| 'wont_fix' \| 'superseded'` |
| `resolution_note` | TEXT NULL | Required when status != `'open'` |
| `resolved_at` | TIMESTAMPTZ NULL | |

- **Indexes:** `idx_quality_entity` on (`affected_entity`, `affected_row_id`); `idx_quality_status` on (`resolution_status`, `detected_at` DESC); `idx_quality_security` on (`security_id`, `detected_at` DESC).
- **Relationships:** N:1 → `securities` (optional).
- **Constraints:** `affected_row_id` NULL ⟹ `affected_scope` non-NULL; `resolution_status != 'open'` ⟹ `resolution_note` non-NULL.
- **Versioning:** Append-only; resolution is a status change on the same row PLUS a new row wherever underlying data changed — the original report row's `detail` is never rewritten.
- **P:** no (quality metadata about sourced rows, which carry P themselves).

## 32. audit_logs (alias: audit_records) — Append-only, immutable

**Purpose:** Who/what did what to what, when, and why — for every
consequential write. The merged name is `audit_logs`; the first spec's
`audit_records` refers to this same entity. There is exactly one audit
table.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `actor_type` | VARCHAR(50) NOT NULL | `'user' \| 'agent' \| 'system' \| 'ingest'` |
| `actor_user_id` | BIGINT NULL | FK → `users.id`, where a user acted |
| `actor_agent_execution_id` | BIGINT NULL | FK → `agent_executions.id`, where an agent acted |
| `actor_system` | VARCHAR(200) NULL | System process name, where applicable |
| `action` | VARCHAR(100) NOT NULL | `'insert' \| 'update' \| 'supersede' \| 'status_change' \| 'login' \| 'role_grant' \| 'role_revoke' \| 'other'` — extend only with documented actions |
| `entity` | VARCHAR(100) NOT NULL | Table/entity affected |
| `entity_row_id` | BIGINT NULL | Row affected; NULL only for actions without a single row (then `entity_scope` is required) |
| `entity_scope` | TEXT NULL | |
| `before_state` | JSONB NULL | Before-image (typed snapshot, not a credential dump) |
| `after_state` | JSONB NULL | After-image, or a reference to the superseding row |
| `reason_code` | VARCHAR(100) NULL | Machine reason code |
| `reason_note` | TEXT NULL | Human reason |
| `occurred_at` | TIMESTAMPTZ NOT NULL | PKT-rendered |
| `ip_ref` | VARCHAR(100) NULL | Network reference ONLY if the application legitimately records it and privacy rules allow; never a credential. NULL is always acceptable. |

- **Indexes:** See `DATABASE_INDEXING_STRATEGY.md` (hot: `entity + entity_row_id + occurred_at`, `actor_user_id + occurred_at`, `occurred_at` range). No index on `before_state`/`after_state` JSONB content (see "what NOT to index").
- **Relationships:** N:1 → `users`, `agent_executions` (optional actor links).
- **Constraints:** At least one actor field set; `action` from the value list (or a documented extension); NO application role may UPDATE or DELETE rows in this table (enforced by database permissions at provisioning, not by application convention alone).
- **Versioning:** Append-only, immutable. Retention: see `DATA_RETENTION_POLICY.md` — audit logs are in the "never deleted" class except under a documented legal/provenance hold procedure.
- **P:** no (audit metadata; the audited rows carry P themselves).

## 33. raw_payloads — Immutable (supporting)

**Purpose:** Content-hash-addressed store of source payloads exactly as
received, or a durable reference to them. Processed tables reference
this table; they never embed a second, divergent "raw" copy.

| Field | Type | Constraints / notes |
|---|---|---|
| `id` | BIGINT IDENTITY | PK |
| `content_sha256` | CHAR(64) NOT NULL | SHA-256 of the payload bytes (or of the referenced file, where the payload is stored as a file) |
| `payload_type` | VARCHAR(50) NOT NULL | `'json' \| 'pdf' \| 'csv' \| 'html' \| 'other'` |
| `source` | VARCHAR(100) NOT NULL | |
| `data_source_id` | BIGINT NULL | FK → `data_sources.id` |
| `storage_backend` | VARCHAR(30) NOT NULL DEFAULT `'local'` | `'local' \| 'minio'` — local filesystem primary, self-hosted MinIO optional (zero-cost design; see `STORAGE_ARCHITECTURE.md`) |
| `storage_path` | VARCHAR(1000) NULL | Relative path/key; NULL only for small payloads stored inline in `payload_inline` |
| `payload_inline` | JSONB NULL | Small JSON payloads inline ONLY (size limit to be set at implementation, e.g. a documented KB threshold); large payloads must use `storage_path`, never inline |
| `byte_size` | BIGINT NULL | Payload size in bytes |
| `collected_at_pkt` | TIMESTAMPTZ NOT NULL | |
| `source_timestamp` | TIMESTAMPTZ NULL | As in P; NULL only if the source provides none (then flagged on the processed row) |
| `created_at` | TIMESTAMPTZ NOT NULL | Append-only: no `updated_at` |

- **Indexes:** `uq_raw_payloads_hash` on (`content_sha256`) — the deduplication key (see storage architecture: same hash = same payload, stored once, referenced many times); `idx_raw_payloads_source_time` on (`source`, `collected_at_pkt` DESC).
- **Relationships:** 1:N → every P-carrying table (via `raw_payload_id`).
- **Constraints:** Exactly one of (`storage_path`, `payload_inline`) set; `content_sha256` unique (a second ingest of identical bytes reuses the row and links to it — duplicate prevention, not duplicate storage).
- **Versioning:** Immutable. Never deleted except under the retention policy's legal/provenance procedure (see `DATA_RETENTION_POLICY.md` — raw provenance is in the "never deleted" class).
- **P:** this table IS the provenance anchor; its own `source`/`collected_at_pkt` fields are the P values that processed rows repeat.

---

## Symbol-history / rename handling note (applies to all entities)

- Every entity that references a security references `securities.id`.
  No entity references a bare ticker string as its security key.
- Ticker-as-of-date resolution goes through `symbol_history`
  (entry 8): `lookup(symbol, as_of_date)` → `security_id`.
  A lookup without a date returns the current symbol only and must be
  labelled as such.
- A rename (verified example: ENGRO → ENGROH) inserts a new
  `symbol_history` row and closes the old row's `valid_to_date`. It
  never re-keys `market_prices`, `live_quotes`, `market_snapshots`,
  `portfolio_holdings`, `forecasts`, `valuations`, or `recommendations`.
- If two sources disagree on a symbol, both `symbol_history` rows are
  kept (different `source` values) and a `data_quality_reports` row is
  raised. The display symbol is a labelled preference.
- Delisted/suspended securities keep their id and history; status
  changes, history does not disappear.

## Entities whose fields depend on an unverified source

| Entity | Dependent fields | Unverified source / design ref |
|---|---|---|
| `economic_indicators` (all fields) | `value`, `unit`, `frequency`, indicator set | SECP/SBP/PBS/Finance Division/World Bank/IMF/FRED — U1, U2 |
| `financial_statements`, `financial_statement_line_items` | Statement availability, types, periods, line-item taxonomy | PSX Portal / company IR machine-use — U3, U4, U6 |
| `announcements` | `pdf_url`, `pdf_storage_path`, taxonomy | `psx-dps` PDF-URL claim — U5 |
| `ratios` | Formula/method set | Sibling financial-formulas work; `psxdata` fundamentals mapping — U6 |
| `securities` | `is_kse100_constituent` (dated membership), sector assignment | KSE-100 list + weights — U7; sector mapping — U8 |
| `sectors` | Canonical mapping | 38-vs-37 taxonomy reconciliation — U8 |
| `live_quotes` | `is_stale` thresholds | Per-source quote cadence — U15 |
| `dividends` | `ex_date`, `record_date`, `payment_date` | Per-source dividend-field availability — U14 |
| `market_prices` (intraday) | Intraday rows beyond today | Historical intraday archive — U10 (none verified) |
| `market_snapshots` | Whole-market coverage, constituent weights | README-claimed, not run-verified — U7 |
| All value tables | Every price/quote/ratio/valuation/forecast value | No live run in Phase 1 — U11 |

## What is NOT in this catalog (deliberate)

- No broker/order/execution tables, no broker account id on portfolios.
- No password, API-key, or secret column on any entity.
- No guarantee column on forecasts or recommendations.
- No example price, quote, or forecast value presented as data.
- No invented endpoint, URL pattern, or source field. Where a URL
  appears, it is a stored reference as provided by a source, not a
  constructed address.
