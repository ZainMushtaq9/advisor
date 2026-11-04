# PSX Intelligence AI — Database Indexing Strategy (Phase 1 of 30)

> **Status: DESIGN ONLY — Phase 1, Team 6. STOP AFTER PHASE 1.**
> No index in this document has been created, and no query performance
> has been measured. Index names are specification notation for a later
> SQLAlchemy/Alembic implementation. Index choices must be re-validated
> with `EXPLAIN ANALYZE` (or the equivalent) on realistic data volumes
> before any performance claim is made. Budget: PKR 0 — indexes cost
> local disk and write time (external operating expenses: hardware /
> electricity), not a vendor fee; over-indexing is therefore a real
> cost, not a free safety net.
>
> **Companions:** `DATABASE_DESIGN.md` (principles, PKR 0 budget),
> `DATABASE_ENTITY_CATALOG.md` (field definitions),
> `DATABASE_RELATIONSHIPS.md` (cardinality / delete rules),
> `STORAGE_ARCHITECTURE.md` (file/Parquet indexing),
> `DATA_RETENTION_POLICY.md` (what may be archived or removed).

## 1. Principles

1. **Index the hot query, not every column.** Every index below is
   justified by a named hot query (HQ1–HQ12 in §2). A column without
   a hot query does not get an index in Phase 1.
2. **Composite before single-column, where the query filters on both.**
   A composite B-tree on `(security_id, trading_date)` serves
   symbol+date lookups; two single-column indexes would force the
   planner to combine them (or pick one and filter the rest). Single
   -column indexes remain only where the query genuinely filters on
   one column alone (e.g. a status scan, a source scan).
3. **Order matters, and DESC matters for as-of queries.** As-of /
   latest queries (`ORDER BY … DESC LIMIT 1`) need the time column
   in DESC order in the index, or the planner must sort. This document
   states DESC explicitly where it matters.
4. **Partial indexes for "current" rows.** Tables with an `is_latest` /
   `is_superseded` / `valid_to IS NULL` marker get a small partial
   index on the current subset, not a full-table index that must
   sift through history. Current-state queries are hot; history
   queries are rarer and can use the full index.
5. **Unique indexes are constraints, not just speed.** Where the
   catalog states a business uniqueness rule (e.g. one current quote
   per security+source, one current holding per portfolio+security),
   the index that enforces it is listed as `uq_…` and must be created
   as a UNIQUE index/constraint — not as a non-unique index plus a
   hope.
6. **Append-only tables favour insert-friendly indexes.** Wide,
   many-column indexes on `market_prices` slow every ingest. The
   strategy below keeps `market_prices` to a small set of composite
   indexes (§4) and pushes analytical slicing to Parquet files
   (`STORAGE_ARCHITECTURE.md`), where columnar pruning does the work
   a dozen B-tree indexes would otherwise have to do.
7. **Do not index what the planner will not use.** See §7 (what NOT
   to index). Low-cardinality booleans alone, JSONB payload blobs,
   free-text bodies, and audit before/after images are the classic
   traps.

## 2. Hot queries (the justification for every index below)

| ID | Hot query (plain language) | Tables | Pattern |
|---|---|---|---|
| HQ1 | Price for one symbol on / around one date; price history for one symbol over a date range | `market_prices` | Equality on `security_id` + range on `trading_date` |
| HQ2 | Latest quote for a symbol (current, per source); quote history for a symbol | `live_quotes` | Current-marker lookup; time-ordered history |
| HQ3 | Snapshot as-of: the market/index as it stood at a given PKT instant | `market_snapshots` | `snapshot_at <= :as_of ORDER BY snapshot_at DESC LIMIT 1` per security/index |
| HQ4 | All securities in a sector; all securities of a company; KSE-100 constituents (current) | `securities`, `companies` | Equality on `sector_id` / `company_id` / constituent flag |
| HQ5 | Statements for a company over periods; line items for one statement version | `financial_statements`, `financial_statement_line_items` | Equality on `company_id` + range/order on `period_end_date`; equality on `statement_id` |
| HQ6 | Ratios for a company/security over periods, by ratio key | `ratios` | Equality on `company_id`/`security_id` + `ratio_key` + period order |
| HQ7 | Dividends / corporate actions for a security, by ex-date | `dividends`, `corporate_actions` | Equality on `security_id` + order on `ex_date` |
| HQ8 | Announcements / news for a company/security, newest first | `announcements`, `news` | Equality on `company_id`/`security_id` + `announced_at`/`published_at` DESC |
| HQ9 | Economic indicator series over time, by code (+ source) | `economic_indicators` | Equality on `indicator_code` + order on `observation_date` |
| HQ10 | Forecasts for a security to a target date; evaluations for a forecast / model / metric | `forecasts`, `forecast_evaluations` | Equality on `security_id` + `target_date`; equality on `forecast_id` / `model_version_id` + `metric` |
| HQ11 | Audit trail: everything that happened to one row; everything one user/agent did, newest first | `audit_logs` | Equality on `entity` + `entity_row_id` + time order; equality on actor + time order |
| HQ12 | Quality issues: open issues by entity/security, newest first; issues for one row | `data_quality_reports` | Equality on `resolution_status` / `affected_entity` + time order |

## 3. Per-table index list

Notation: `B-tree (a, b DESC)` = composite B-tree, second column
descending. `PARTIAL … WHERE …` = partial index. `UNIQUE` = enforcing
index. Indexes already implied by a PK are not re-listed (the PK
index exists by definition).

### 3.1 users, roles, user_role_assignments

| Index | Columns / predicate | Justifies |
|---|---|---|
| `uq_users_email` | UNIQUE (`email`) — only if email uniqueness is confirmed at implementation; otherwise non-unique (`email`) | Login/contact lookup |
| `uq_roles_role_key` | UNIQUE (`role_key`) | Role lookup |
| `idx_user_roles_user` | (`user_id`, `valid_to`) | "What roles does this user hold now / held?" |
| `idx_user_roles_role` | (`role_id`, `valid_to`) | "Who holds this role?" |
| `uq_user_roles_current` | UNIQUE (`user_id`, `role_id`) WHERE `valid_to IS NULL` | One current assignment per user+role (catalog rule) |

Rationale: small tables; the partial unique is the important one —
it enforces the effective-dating invariant without a full-table scan.

### 3.2 exchanges, sectors, companies, securities, symbol_history, trading_calendars

| Index | Columns / predicate | Justifies |
|---|---|---|
| `uq_exchanges_exchange_key` | UNIQUE (`exchange_key`) | Exchange lookup |
| `idx_sectors_canonical_name` | (`canonical_name`) | Sector search |
| `idx_sectors_source_name` | (`source`, `source_sector_name`) | Taxonomy reconciliation (38 vs 37) |
| `idx_companies_sector` | (`current_sector_id`) | HQ4 (sector filter) |
| `idx_companies_status` | (`status`) | Listing-status filters (low cardinality alone — kept only because status + sector/company queries combine it; see §7 note) |
| `idx_companies_legal_name` | (`legal_name`) | Company search |
| `idx_securities_company` | (`company_id`) | HQ4 |
| `idx_securities_exchange` | (`exchange_id`) | Exchange filter |
| `idx_securities_current_symbol` | (`current_symbol`) | Ticker lookup (current only; historical lookup uses `symbol_history`) |
| `idx_securities_kse100` | (`is_kse100_constituent`) WHERE `is_kse100_constituent = TRUE` | HQ4 KSE-100 filter — partial, so the index stays tiny |
| `uq_symbol_history_security_symbol_from` | UNIQUE (`security_id`, `symbol`, `valid_from_date`) | Rename-history integrity |
| `idx_symbol_history_symbol_date` | (`symbol`, `valid_from_date`, `valid_to_date`) | Ticker-as-of-date resolution (design §8) |
| PK `trading_calendars` | (`exchange_id`, `trading_date`) | Calendar lookup; missing-session detection |
| `idx_trading_calendars_date` | (`trading_date`, `is_trading_day`) | "Which exchanges traded on this date?" |

### 3.3 market_prices (the fact table — keep it lean)

| Index | Columns / predicate | Justifies |
|---|---|---|
| `idx_market_prices_security_date` | (`security_id`, `trading_date`, `bar_type`) | HQ1 — the primary hot query. Composite, not two singles. |
| `idx_market_prices_security_time` | (`security_id`, `bar_timestamp` DESC) WHERE `bar_timestamp IS NOT NULL` | Tick/intraday time-ordered history; partial (EOD rows have NULL timestamps and must not bloat this index) |
| `idx_market_prices_current` | (`security_id`, `trading_date` DESC) WHERE `is_superseded = FALSE` | "Current best-known" price history without sifting superseded corrections |
| `uq_market_prices_grain` | UNIQUE (`security_id`, `trading_date`, `bar_type`, `bar_timestamp`, `source`) — with NULL handling for `bar_timestamp` decided at implementation (PostgreSQL treats NULLs as distinct in unique indexes; a NULLS-NOT-DISTINCT variant or a surrogate timestamp sentinel must be chosen and documented) | Grain enforcement: conflicting sources coexist as separate rows (different `source`), duplicates from re-ingest are rejected |
| `idx_market_prices_source_time` | (`source`, `collected_at_pkt` DESC) | Ingest auditing: "what did this source deliver, when?" |

Rationale (composite vs single): HQ1 filters on security AND date
together, always. Two single-column indexes would each return large
intermediate sets (all dates for a symbol, or all symbols for a date)
before intersection. The composite serves the query directly.
**Deliberately absent:** no index on `close_price` alone, on
`volume` alone, or on `is_adjusted` alone — no hot query filters on
those alone (see §7).

### 3.4 live_quotes

| Index | Columns / predicate | Justifies |
|---|---|---|
| `uq_live_quotes_current` | UNIQUE (`security_id`, `source`) WHERE `is_latest = TRUE` | HQ2 current-quote lookup + enforcement of "one current row" |
| `idx_live_quotes_security_time` | (`security_id`, `quote_timestamp` DESC) | HQ2 quote history |
| `idx_live_quotes_stale` | (`is_stale`, `quote_timestamp`) WHERE `is_stale = TRUE` | "Which quotes are stale right now?" — partial, so it stays small |

### 3.5 market_snapshots (as-of pattern)

| Index | Columns / predicate | Justifies |
|---|---|---|
| `idx_snapshots_run` | (`snapshot_run_id`) | "All rows of one run" (atomic run retrieval) |
| `idx_snapshots_asof` | (`security_id`, `snapshot_at` DESC) | HQ3 per-security as-of: `WHERE security_id = ? AND snapshot_at <= :as_of ORDER BY snapshot_at DESC LIMIT 1` |
| `idx_snapshots_index_asof` | (`index_code`, `snapshot_at` DESC) WHERE `index_code IS NOT NULL` | HQ3 per-index as-of (partial: security rows have NULL `index_code`) |
| `idx_snapshots_source_time` | (`source`, `snapshot_at` DESC) | Source-run auditing |

As-of note: the as-of query must ALSO filter to the latest row *per
run* semantics correctly — a snapshot run is atomic, so "latest
snapshot at or before T" means the latest `snapshot_at` ≤ T, then all
rows of that run. Indexing `snapshot_at` DESC per security/index is
what makes the first step an index lookup rather than a sort. Do not
implement as-of by scanning all snapshots and sorting in application
code.

### 3.6 financial_statements, line items, ratios

| Index | Columns / predicate | Justifies |
|---|---|---|
| `idx_statements_company_period` | (`company_id`, `period_end_date` DESC, `statement_type`) | HQ5 |
| `uq_statements_version` | UNIQUE (`company_id`, `statement_type`, `period_end_date`, `filing_version`, `source`) | Version integrity |
| `idx_line_items_statement` | (`financial_statement_id`, `display_order`) | HQ5 line-item retrieval in source order |
| `idx_line_items_key` | (`line_item_key`, `financial_statement_id`) | "This line across statements" (comparative queries) |
| `idx_ratios_company_period` | (`company_id`, `period_end_date` DESC, `ratio_key`) | HQ6 |
| `idx_ratios_security` | (`security_id`, `ratio_key`, `period_end_date` DESC) WHERE `security_id IS NOT NULL` | HQ6 per-security multiples (partial: company-only ratios have NULL `security_id`) |

### 3.7 corporate_actions, dividends, announcements, news, economic_indicators

| Index | Columns / predicate | Justifies |
|---|---|---|
| `idx_corp_actions_security_date` | (`security_id`, `ex_date` DESC) | HQ7 |
| `idx_corp_actions_type` | (`action_type`, `effective_date` DESC) | Action-type scans |
| `uq_dividends_action` | UNIQUE (`corporate_action_id`) | 1:1 dividend detail enforcement |
| `idx_dividends_security_date` | (`security_id`, `ex_date` DESC) | HQ7 dividend history |
| `idx_announcements_company_date` | (`company_id`, `announced_at` DESC) WHERE `company_id IS NOT NULL` | HQ8 |
| `idx_announcements_security_date` | (`security_id`, `announced_at` DESC) WHERE `security_id IS NOT NULL` | HQ8 |
| `idx_announcements_fts` | GIN/`tsvector` on (`title`, `body_text`) — PostgreSQL only; SQLite-dev equivalent differs and must be re-tested | Announcement text search (see §7: this is the ONE text index, justified by a search requirement, not a blanket rule) |
| `idx_news_company_date` | (`company_id`, `published_at` DESC) WHERE `company_id IS NOT NULL` | HQ8 |
| `idx_news_security_date` | (`security_id`, `published_at` DESC) WHERE `security_id IS NOT NULL` | HQ8 |
| `idx_econ_code_date` | (`indicator_code`, `observation_date` DESC) | HQ9 |
| `uq_econ_observation` | UNIQUE (`indicator_code`, `observation_date`, `source`) | Conflicting sources coexist; re-ingest duplicates rejected |

### 3.8 valuations, forecasts, forecast_evaluations, recommendations

| Index | Columns / predicate | Justifies |
|---|---|---|
| `idx_valuations_security_date` | (`security_id`, `valuation_date` DESC, `method`) | Valuation history by method |
| `idx_forecasts_security_target` | (`security_id`, `target_date`, `forecast_origin_date`) | HQ10 — "forecasts for this security to this date" |
| `idx_forecasts_model` | (`model_version_id`, `forecast_origin_date` DESC) | Model comparison |
| `idx_forecasts_active` | (`security_id`, `target_date`) WHERE `status = 'active'` | Active-forecast lookups without sifting superseded rows |
| `idx_forecast_eval_forecast` | (`forecast_id`, `evaluation_date`) | HQ10 evaluation history |
| `idx_forecast_eval_model_metric` | (`model_version_id`, `metric`, `evaluation_date` DESC) | HQ10 model/metric leaderboards — a genuinely hot evaluation query; without this composite, model comparison scans all evaluations |
| `uq_forecast_eval_grain` | UNIQUE (`forecast_id`, `evaluation_date`, `metric`) | One metric value per forecast per date |
| `idx_recommendations_security_status` | (`security_id`, `status`, `valid_from` DESC) | Active-recommendation lookup |
| `idx_recommendations_user` | (`user_id`, `valid_from` DESC) WHERE `user_id IS NOT NULL` | User recommendation history |

### 3.9 portfolios, holdings, agents, models, sources, quality, audit, raw

| Index | Columns / predicate | Justifies |
|---|---|---|
| `idx_portfolios_user` | (`user_id`, `status`) | User portfolio list |
| `uq_holdings_current` | UNIQUE (`portfolio_id`, `security_id`) WHERE `valid_to IS NULL` | One current holding per portfolio+security |
| `idx_holdings_portfolio` | (`portfolio_id`, `valid_from` DESC) | Holding history |
| `idx_agent_exec_agent_time` | (`agent_key`, `started_at` DESC) | Agent run history |
| `idx_agent_exec_status` | (`status`, `started_at` DESC) | "What failed recently?" |
| `idx_agent_outputs_execution` | (`agent_execution_id`, `created_at`) | Outputs of a run |
| `uq_model_versions_name_version` | UNIQUE (`model_name`, `version`) | Model-version integrity |
| `uq_data_sources_source_key` | UNIQUE (`source_key`) | Source lookup (provenance joins) |
| `idx_quality_entity` | (`affected_entity`, `affected_row_id`) | HQ12 per-row issues |
| `idx_quality_status` | (`resolution_status`, `detected_at` DESC) | HQ12 open-issue queues |
| `idx_quality_security` | (`security_id`, `detected_at` DESC) WHERE `security_id IS NOT NULL` | HQ12 per-security issues |
| `idx_audit_entity_row` | (`entity`, `entity_row_id`, `occurred_at` DESC) | HQ11 per-row audit trail — the most important audit index |
| `idx_audit_actor_time` | (`actor_user_id`, `occurred_at` DESC) WHERE `actor_user_id IS NOT NULL` | HQ11 per-user audit trail |
| `idx_audit_agent_time` | (`actor_agent_execution_id`, `occurred_at` DESC) WHERE `actor_agent_execution_id IS NOT NULL` | HQ11 per-agent audit trail |
| `idx_audit_time` | (`occurred_at` DESC) | Time-range audit scans (retention/archival queries) |
| `uq_raw_payloads_hash` | UNIQUE (`content_sha256`) | Deduplication key (storage architecture) |
| `idx_raw_payloads_source_time` | (`source`, `collected_at_pkt` DESC) | Payload provenance queries |

## 4. Partitioning consideration — market_prices (design decision, NOT a claimed implementation)

**Decision: design `market_prices` for range partitioning by time, and
defer the physical partitioning choice to provisioning.**

| Option | How it would work | Trade-offs |
|---|---|---|
| A. No partitioning (single table + §3.3 indexes) | One `market_prices` table; all queries use the composite indexes. | Simplest; fine at KSE-100 scale and for early full-market EOD data. Risk: as EOD history grows (all listed instruments × years) and tick rows accumulate, index size and vacuum/maintenance cost grow; bulk deletes/archival (per retention policy) require row-by-row deletes. |
| B. Range partition by `trading_date` (e.g. yearly, or monthly once tick volume justifies it) | PostgreSQL declarative partitioning: one partition per year (or month) on `trading_date`; PK/unique constraints must include the partition key. Queries with a date predicate prune partitions; queries without one scan all partitions. | Best for time-range queries (HQ1 is always date-scoped) and for archival: dropping/archiving an old partition is a metadata operation, not a delete scan — a major retention-policy win. Costs: PK/unique design must include `trading_date` (the §3.3 grain unique already includes it, so this is compatible); cross-partition queries without a date filter are slower; SQLite-dev cannot replicate this (dev/prod divergence must be documented); partition management (creating future partitions) becomes an operational task. |
| C. Partition by `security_id` (hash) | Partitions by instrument. | Rejected for Phase 1: HQ1 is date-scoped, not security-count-scoped; hash partitioning helps single-security queries only marginally (the composite index already does that) and hurts market-wide date queries and archival by time. Do not choose this without a measured reason. |

**Recommendation (design, to be confirmed before first bulk load):**
adopt **Option B, yearly partitions on `trading_date`**, with monthly
partitions reserved as a later escalation if tick volume makes yearly
partitions unwieldy. Rationale: HQ1/HQ3/HQ9-style queries are
time-scoped; retention/archival is time-scoped (`DATA_RETENTION_POLICY.md`);
and the grain unique key already contains `trading_date`, so the
partitioning constraint cost is already paid. **Explicitly not claimed:**
no partition exists, no partition has been tested, and the SQLite
local-dev alternative cannot validate this choice — PostgreSQL
validation is a provisioning gate (see design §13).

**What partitioning does NOT do:** it does not replace indexes
(partition pruning + the §3.3 composite indexes work together), it
does not fix a missing date predicate (a query without a date filter
still scans partitions), and it does not authorise deleting history —
archival moves partitions to Parquet (see `STORAGE_ARCHITECTURE.md`),
it does not erase them.

**Other tables and partitioning:** `live_quotes` (append-only log),
`market_snapshots`, and `audit_logs` are candidates for the same
yearly time partitioning *only if* their volumes justify it after
measurement. Do not partition them pre-emptively: each partition adds
operational overhead, and premature partitioning of small tables is
pure cost. `audit_logs` partitioning, if ever adopted, must preserve
the "never deleted" rule — partitions are archived, not dropped,
without a retention-policy decision.

## 5. Composite vs single-column — rationale summary

| Situation | Choice | Why |
|---|---|---|
| Filter always pairs an id with a date (HQ1, HQ3, HQ5–HQ10) | Composite `(id, date …)` | The pair is the query; singles force intersection of two large sets |
| Filter is an id alone, then a sort by date | Composite `(id, date DESC)` | Serves filter + order in one index pass; a single id index would still need a sort |
| Filter is a flag alone (`is_kse100_constituent`, `is_latest`, `is_stale`, `valid_to IS NULL`) | Partial index with the flag as predicate, not as a leading column | A boolean alone has ~2 distinct values — a full index on it is nearly a table scan. As a partial predicate, the index contains only the interesting subset and stays small |
| Filter is a unique business key | Unique composite | Enforcement + lookup in one structure; never a non-unique index plus application hope |
| Filter is a single lookup key (`source_key`, `role_key`, `current_symbol`, `content_sha256`) | Single-column unique | The query is genuinely single-column; a composite would add width for no benefit |

## 6. Index maintenance notes (for the later implementer)

- **Write amplification is real.** Every index on `market_prices`,
  `live_quotes`, and `market_snapshots` is paid on every ingest.
  That is why §3.3 keeps `market_prices` to five indexes: adding a
  sixth "just in case" index costs ingest throughput and local disk
  on every row, forever, for a query that may never run.
- **Reindex / vacuum are operational tasks, not design features.**
  PostgreSQL maintenance (VACUUM, ANALYZE, REINDEX where needed)
  must be scheduled at provisioning; this design does not claim a
  maintenance schedule exists.
- **Measure before adding.** Any index proposed after Phase 1 must
  cite a hot query (or a measured slow query with `EXPLAIN ANALYZE`
  output) and must state which existing index it replaces or why it
  does not duplicate one. "Might help" is not a justification.
- **SQLite-dev divergence.** Partial indexes, `tsvector`/GIN, and
  partitioning differ or are absent in SQLite. Dev tests must not
  assert PostgreSQL-only index behaviour; prod validation must
  re-check every index in §3 on PostgreSQL.

## 7. What NOT to index (explicit)

| Do NOT index | Why |
|---|---|
| `close_price`, `volume`, `turnover_pkr` alone | No hot query filters on a price/volume value alone; range scans on price across all securities are analytical queries that belong in Parquet (columnar pruning), not in a B-tree |
| Booleans alone (`is_stale`, `is_trading`, `is_superseded`, `is_adjusted`, `is_latest` as full indexes) | ~2 distinct values; a full index is a disguised table scan. Use partial indexes (§3) where the subset is genuinely hot |
| `body_text`, `title` free text with a B-tree | B-trees do not serve substring/text search. The single justified exception is the PostgreSQL `tsvector`/GIN index on announcements (§3.7); do not generalise it to every text column |
| JSONB payloads (`payload`, `assumptions`, `hyperparameters`, `before_state`, `after_state`, `parameters`) with GIN by default | GIN on large, schemaless JSONB is expensive to maintain and rarely queried by content in the hot queries. If a later phase proves a JSONB-key query is hot, add a targeted expression index for that key only, with measurement |
| `audit_logs.before_state` / `after_state` content | Audit content is retrieved by row (HQ11), never searched by content. Indexing it would bloat the most write-sensitive table for no hot query |
| `raw_payloads.payload_inline` | Inline payloads are retrieved by hash/id, never searched by content |
| Every FK column individually "just in case" | FK columns that only ever appear as the second element of a composite, or that are never filtered alone, do not need their own index. Example: `market_prices.data_source_id` alone is not indexed — source+time auditing uses `idx_market_prices_source_time`, and provenance joins go through the security+date composite first |
| `created_at` alone on every table | Time-only scans across all entities are not hot queries. Time matters paired with an entity id (HQ11 audit indexes pair actor/row with time); a bare `created_at` index on a fact table serves almost nothing |
| Low-cardinality enums alone (`status`, `action_type`, `session_type`) | Same boolean argument: use them as second columns in composites or as partial predicates, not as standalone indexes — except where §3 explicitly lists a status-combined composite (e.g. recommendations by security+status) |
| `content_sha256` on any table other than `raw_payloads` | Hash lookups go through `raw_payloads`; duplicating a hash index on every referencing table adds write cost for a join that already resolves via `raw_payload_id` |

**If a future query needs one of the above, the correct response is:**
first check whether Parquet analytics, an existing composite, or a
partial index serves it; only then propose a new index with a measured
query plan. Do not add indexes speculatively.
