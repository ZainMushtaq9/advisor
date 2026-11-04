# PSX Intelligence AI — System Architecture (Phase 1)

**Phase:** 1 of 30 — Architecture / specification only. No application code in this
document beyond tiny illustrative snippets. No Phase 2 work is started here.

**Status date:** 2026-11-04 (verified starting condition, reused verbatim in §1).

**Hard rules that bind every layer:**

- No sign-ups, installs, purchases, credentials, API keys, broker connections,
  live polling, trading, or posting are authorised or described as done in this phase.
- Never invent an API, endpoint, data source, integration, price, or capability.
  Anything not verified is marked **UNVERIFIED**.
- Forecasts and recommendations are **probabilistic and evidence-based, never
  guaranteed**. Every forecast/recommendation shown to a user must carry its
  evidence, inputs, date, and uncertainty/limitations.
- Financial calculations are **deterministic Python functions**. An LLM must
  **NEVER invent a numerical financial result** — it may explain, summarise, or
  select a calculation, but the number itself comes only from a deterministic
  function run over stored, provenance-tagged data, and is recorded for audit.
- Never silently merge conflicting values from different sources. Keep both
  values with provenance and route the conflict (Layer 2, §4.2).
- Never bypass authentication, access controls, or rate limits. Never resell or
  republish a live PSX feed without first verifying PSX licensing.

---
## 0. Revised brief — merged 2026-11-04 (governing additions, no duplicate build)

- **Budget PKR 0 absolute zero-cost.** No paid hosting, database, storage,
  monitoring, or AI subscription in any configuration. Local hardware,
  electricity, and internet are **external operating expenses** — disclosed,
  never called free. No permanent free hosting is assumed (including GitHub
  Free terms, which can change; code/data stay portable to a local machine).
- **Fixed zero-cost stack (design only).** Frontend: Next.js / React /
  TypeScript / Tailwind / shadcn. Backend: Python / FastAPI / Pydantic.
  Database (production design): PostgreSQL / SQLAlchemy / Alembic; local-dev
  alternative: SQLite (dev-only, same logical schema). File storage: local
  filesystem + Apache Parquet + optional self-hosted MinIO (optional, never
  required). Queue/cache: Redis (design target, NOT installed). AI: Ollama
  local inference only (no cloud AI subscription). Testing: Pytest /
  Playwright (strategy defined, not claimed passed). Version control:
  Git / GitHub Free. Containers: Docker Engine / local dev (NOT installed).
  Only Python 3.12.3 and Node v24.22.1 are VERIFIED versions; all other
  stack versions are to-be-pinned in Phase 2 and are UNVERIFIED here.
  Layer 3, 7, and 8 specifications in §4 must be read with this stack: where
  §4 says "PostgreSQL in production design", that means PostgreSQL /
  SQLAlchemy / Alembic; where it says local-dev SQLite, that is the §0
  alternative; Layer 8 surfaces are Next.js/React/TypeScript/Tailwind/shadcn
  designs; Layer 7 queue/cache is Redis as a design target.
- **No real trades initially — invariant.** The system must NOT execute real
  trades initially. There is no broker connection, no order-placement path,
  and no execution branch in any layer. See Layer 6 (§4) and
  `DEPLOYMENT_ARCHITECTURE.md` §10. Any future execution proposal is a new
  design decision requiring separate approval.
- **Canonical diagrams.** `SYSTEM_ARCHITECTURE.mmd` is the canonical system
  diagram; `SYSTEM_ARCHITECTURE_DIAGRAM.md` §1 embeds it verbatim.
  Likewise `DATA_FLOW_DIAGRAM.mmd`, `AGENT_INTERACTION_DIAGRAM.mmd`, and
  `DEPLOYMENT_ARCHITECTURE.mmd` are canonical for their `.md` companions.
- **STOP AFTER PHASE 1.** No Phase 2 code, install, deployment, or live
  collection is started by this document set.

---

## 1. Verified starting condition (2026-11-04, reused verbatim)

- Project folder `~/workspace/psx-intelligence-ai/` is new. Other teams may be
  creating sibling files; this document writes no other team's files.
- Existing separate scaffold to **REFERENCE but NEVER overwrite or touch**:
  `~/workspace/psx-data-collection/` — README, `DATA_SOURCE_REGISTRY.md`,
  `psx_collector.py` (stdlib-only collector with provenance / PKT timestamps /
  stale / conflict rules), offline tests passing, `coverage.json` template.
  That scaffold is the Phase 1 data-layer reference for Layers 1–2 below. This
  architecture does **not** duplicate its code; it defines the interfaces the
  scaffold's rules plug into.
- Tools verified on this machine on 2026-11-04: **Python 3.12.3, Node v24.22.1**.
  **Docker, `psql`, and `redis-cli` are NOT installed** — see
  `DEPLOYMENT_ARCHITECTURE.md` for the local-dev alternative (SQLite for local
  dev only, Python venv, no Docker required). Do not assume they exist.
- Already verified (reuse, do not re-claim beyond what the sources state):
  - PSX Data Portal `dps.psx.com.pk`.
  - `psx-dps` (MIT, zero dependencies, no API key): ~496 trading symbols vs
    ~1029 listed instruments, ~5 years EOD, today's ticks only, 38 sectors,
    224k+ announcements, multi-node 404 quirk (some nodes return 404 for data
    routes while serving the website; the library probes a pool of nodes and
    pins one that serves data), no official PSX API.
  - `psxdata` (MIT, PyPI, alpha 0.1.0a1): daily OHLCV + live snapshots ONLY,
    no historical intraday archive, tickers 1000+, 37 sectors.
  - Eulerpool: **NO PSX coverage verified** — vendor only, no paid API approved.
- **UNVERIFIED for machine use:** SECP, SBP, PBS, Finance Division, World Bank,
  IMF, FRED interfaces. Their interfaces are marked UNVERIFIED everywhere in
  this phase; no endpoint is invented for them.

## 2. Architectural principles

1. **Layered, one-way data dependence.** Data flows downward in the normal
   path: 1 → 2 → 3 → 4 → 5 → 6 → 8, with Layer 7 orchestrating work across
   layers. No layer reaches past its neighbour to a raw external source except
   Layer 1 (the only layer that talks to external sources). Layers 4–6 read
   only from Layer 3 (storage), never directly from a portal or library.
2. **Raw vs processed separation, always.** Raw payloads are stored exactly as
   received, with provenance, and are never overwritten by processed values.
   Processed records are derived, versioned, and traceable back to raw records.
3. **Provenance on every record.** Every stored record carries at minimum:
   `source`, `source_timestamp`, `collected_at_pkt` (Asia/Karachi), and
   `freshness` (see §4.2 and `DATA_FLOW_DIAGRAM.md`). A value without
   provenance is not shown as a fact.
4. **Stale and missing are states, not gaps to fill.** Stale data is flagged,
   never presented as live. Missing sessions are recorded, never filled with
   estimates. A quote is never called "real-time" merely because it was fetched
   recently — its source timestamp is shown.
5. **Deterministic numbers, probabilistic language.** Layers 4–6 compute with
   deterministic functions; uncertainty is expressed in words and ranges that
   come from those functions and their validation, not from LLM invention.
6. **Human-in-the-loop and independent audit for decisions.** No recommendation
   reaches a user without passing the Layer 6 audit path and, where defined,
   a human gate (see `AGENT_INTERACTION_DIAGRAM.md`). The audit agent can veto
   or flag a recommendation; a veto blocks publication.
7. **Fail closed on data quality.** When validation, provenance, or audit
   fails, the layer emits a flagged/absent result with a reason — not a
   plausible-looking substitute.

## 3. Layer map (summary)

| Layer | Name | Owns | Must never |
|---|---|---|---|
| 1 | Data Acquisition | Collecting from external sources, within their limits | Bypass rate limits, auth, or licensing; invent a source |
| 2 | Data Validation | Checking, deduplicating, reconciling conflicts | Silently merge conflicts; fill missing data with estimates |
| 3 | Storage | Durable raw + processed stores, provenance, audit log | Overwrite raw payloads; store a number without provenance |
| 4 | Financial Analysis | Fundamental, technical, sector, macro, health, valuation | Present an analysis as a recommendation or a guarantee |
| 5 | Forecasting | Statistical / quantitative / AI-assisted research, scenarios | Fabricate a number; present a forecast as certain |
| 6 | Investment Decisions | Risk, recommendation engine, portfolio optimisation, audit | Publish an unaudited recommendation; execute a trade |
| 7 | Agent Orchestration | Registry use, tasks, scheduling, retries, monitoring, cost | Run two sending/computation methods for the same job at once; hide cost |
| 8 | User Interface | Public site, dashboard, company pages, reports, admin | Show stale data as live; show an unaudited recommendation |

Communication boundaries in one line: **Layer N talks to Layer N−1 and N+1
through versioned, typed interfaces (defined per layer below); Layer 7
orchestrates but does not itself compute financial numbers; Layer 8 reads only
from Layers 3–6 outputs that have passed audit.**

---

## 4. Layer specifications

Each layer below follows the same template: purpose, inputs, outputs,
interfaces to adjacent layers, failure modes, and what it must NOT do.

### LAYER 1 — Data Acquisition

**Purpose.** Collect market, financial-report, announcement, economic, and news
data from external sources, within each source's stated limits, and hand
complete, provenance-tagged raw payloads to Layer 2. This is the **only** layer
that contacts external sources.

**Collectors in scope (Phase 1):**

- **PSX market collectors** — via the reference scaffold
  (`~/workspace/psx-data-collection/`): PSX Data Portal via `psx-dps` as
  primary market snapshot source, `psxdata` as backup for daily OHLCV / live
  snapshots. See the scaffold's registry for the exact claimed coverage and
  limits; this architecture adds no new market-source claim.
- **Historical collector** — end-of-day (EOD) history per symbol, within the
  verified limits: ~5 years via `psx-dps`; daily OHLCV via `psxdata`. No
  historical intraday archive is claimed (psxdata's README states it does not
  exist publicly; psx-dps offers today's ticks only).
- **Snapshot collector** — whole-market snapshot / live quotes during market
  hours, subject to each library's caching and rate rules.
- **Financial-report collector** — listed-company annual/quarterly reports and
  statements. Source set is per-company investor-relations sites and the PSX
  Portal financials/announcements — **machine-readable coverage UNVERIFIED**;
  no per-company coverage is claimed until a live sample check documents it.
- **Announcement collector** — PSX announcements (psx-dps claims 224k+
  announcements with PDF URLs; PDF content extraction is a separate,
  unverified step — a PDF URL is not the same as extracted, validated data).
- **Economic collector** — SECP / SBP / PBS / Finance Division / World Bank /
  IMF / FRED. **All interfaces UNVERIFIED in Phase 1.** This collector exists
  in the architecture as a named, gated slot: it may be designed and its
  interface specified, but it must not be claimed as working, and no endpoint,
  field, or update frequency is asserted for any of these bodies until verified
  against an official source.
- **News collector** — named slot only in Phase 1. No news source, feed, or
  endpoint is specified or verified here; any future news source needs its own
  registry entry (source, licence, freshness, limits) before collection.

**Inputs:** Source registry entries (from `DATA_SOURCE_REGISTRY.md` and any
future registry additions); a collection schedule/task from Layer 7; per-source
rate-limit, cache, backoff, and retry policy.

**Outputs (to Layer 2 only):** Raw payloads, each tagged with `source`,
`source_timestamp` (as stated by the source, or `null` with a reason if the
source gives none), `collected_at_pkt`, `freshness`, collector identity, and
the raw payload itself (unmodified). Plus collection telemetry: attempts,
success/failure, HTTP/library status where available, node used (for the
psx-dps multi-node quirk), and backoff state.

**Interfaces:**

- **From Layer 7:** collection tasks (what to collect, which source slot,
  schedule). Layer 1 does not self-schedule beyond the task it was given.
- **To Layer 2:** raw-payload stream/batches with provenance (above). Layer 1
  does not validate beyond transport-level integrity (e.g. truncated payload);
  all content validation belongs to Layer 2.
- **To Layer 3 (raw store only, via Layer 2):** Layer 1 does not write to
  storage directly; Layer 2 stores raw payloads after its intake check, so a
  corrupt payload is never stored as if valid. (Implementation detail for
  Phase 2: if a direct raw landing zone is added, it must still be gated by
  Layer 2's intake check before any processed use.)

**Failure modes:**

- Source endpoint changes without notice (no official PSX API/documentation):
  collector fails loudly, falls back to the backup source slot where one is
  defined, and records the failure; it does not guess a new endpoint.
- Multi-node 404 quirk: a 404 from one node is treated as a node problem, not
  as "data does not exist"; re-probe per the library's behaviour and record
  which node served data.
- Rate limit / 429: stop, back off with escalating cooldown, do not retry in a
  tight loop, and report the limit hit to Layer 7 (which may reschedule).
- Source returns no timestamp: record `source_timestamp = null`, mark
  freshness as unknown, and never present the value as live.
- Symbol rename (e.g. ENGRO → ENGROH, noted in the scaffold registry):
  record the rename mapping explicitly; do not silently merge histories under
  one symbol.

**Must NOT do:**

- Bypass rate limits, authentication, or access controls; scrape a source that
  forbids machine access; resell/republish a live PSX feed without licence
  verification.
- Invent a source, endpoint, field, or coverage claim (especially for the
  UNVERIFIED economic/news slots).
- Present a fetched value as "real-time" without its source timestamp.
- Fill a missing session, backfill intraday history that does not exist, or
  merge conflicting source values (that is Layer 2's job, and it never merges
  silently).

### LAYER 2 — Data Validation

**Purpose.** Turn Layer 1 raw payloads into trusted, deduplicated, stored
records — or into explicitly flagged problems. This layer is the quality gate
for everything downstream; Layers 4–6 must be able to trust that a record in
Layer 3 passed Layer 2 or is flagged with its exact defect.

**Checks (all five required, in this order):**

1. **Source / timestamp validation** — Is the source a registered source? Is
   `source_timestamp` present, parseable, and in a sane range? Is
   `collected_at_pkt` present (Asia/Karachi)? Is the record stale relative to
   its source's stated freshness/TTL, and if so, is it flagged `stale` rather
   than dropped silently? (Stale data may still be stored and shown, labelled
   stale — dropping it would hide history.)
2. **Duplicate detection** — Same source + symbol/instrument + source
   timestamp + field set already stored? Deduplicate on that key (plus a
   content hash of the raw payload where available). A re-fetch of an
   unchanged value is a duplicate, not a new observation; a re-fetch with a
   changed value for the same source timestamp is a *revision*, stored as a
   new version linked to the original, never an overwrite.
3. **Missing-data detection** — Expected sessions/symbols/fields absent?
   Record a `missing` entry (what was expected, for which period/symbol, from
   which source) instead of leaving a silent gap. Missing is never filled with
   an estimate, interpolation, or a value from a different period.
4. **Financial validation** — Deterministic, rule-based checks only, e.g.:
   OHLC ordering (high ≥ open/close ≥ low, where applicable), non-negative
   volumes/quantities where the field requires it, price-change arithmetic
   consistent with the stored values, currency/unit consistency, and
   cross-field consistency within a single source record. A failed check flags
   the record; it does not "correct" the value.
5. **Conflicting-source reconciliation — never silently merge.** When two
   registered sources disagree on the same fact (e.g. different closing prices
   for the same symbol/date), **both values are kept, each with full
   provenance**, and a `conflict` record is created (sources, values,
   timestamps, and the rule that would resolve it *if* a resolution policy
   exists). Downstream layers must either use a declared primary source for
   that field (recorded in the conflict record) or surface the conflict to the
   user; they must not average, pick silently, or hide the disagreement.
   Resolution policy itself (which source is primary for which field) is a
   configuration decision recorded in the registry — not an LLM judgement call
   at query time.

**Inputs:** Layer 1 raw payloads + provenance; registry (registered sources,
primary-source policy per field, expected symbols/sessions); Layer 3 read
access for duplicate/revision checks.

**Outputs (to Layer 3):** Validated records (with validation status), flagged
records (`stale`, `missing`, `invalid`, `conflict`), revision links, and
validation telemetry (counts per check, per source). Invalid records are
stored as flagged, not discarded, so the failure is auditable.

**Interfaces:**

- **From Layer 1:** raw payloads (above).
- **To Layer 3:** validated/flagged records and conflict records; read-back for
  duplicate checks.
- **To Layer 7:** validation failures that need operator attention (e.g.
  sustained source failure, mass conflicts) as alerts, not as silent logs.
- **To Layers 4–6 (indirect, via Layer 3):** only validated or explicitly
  flagged records are visible; downstream queries must be able to filter by
  validation status.

**Failure modes:**

- Registry out of date (source changed format): validation fails loudly for
  affected records; do not relax rules to make data pass.
- Clock/timezone error: PKT conversion failure flags the record; never store a
  timestamp in an ambiguous timezone.
- Conflict storm (backup disagrees systematically with primary): record every
  conflict, alert Layer 7, and do not auto-switch primary source without a
  recorded configuration change.

**Must NOT do:**

- Silently merge, average, or pick between conflicting sources.
- Fill missing data with estimates, interpolation, or prior-period values
  presented as observed data.
- "Correct" a source value, overwrite a raw payload, or drop a failed record
  without a flag.
- Validate using an LLM's judgement about plausibility — checks are
  deterministic rules; an LLM may summarise validation output but may not
  override a rule result.

### LAYER 3 — Storage

**Purpose.** Durably store raw payloads, validated/processed records,
derived analysis/forecast/decision outputs, and the audit log — with
provenance intact and raw data immutable.

**Production design: PostgreSQL.** (Design target, not installed — see
`DEPLOYMENT_ARCHITECTURE.md`. No PostgreSQL instance exists on this machine in
Phase 1, and no connection is claimed.)

**Local-dev alternative (stated here and in the deployment doc):** SQLite
(local file, for development only) with the same logical schema and the same
provenance fields, plus JSON/CSV exports for inspection. Local-dev storage is
not a production store and must not be presented as one.

**Logical stores (same in both configs):**

- `raw_store` — raw payloads exactly as received, immutable, keyed by
  source + collection id. Never updated, never deleted except by a recorded
  retention policy (Phase 2+ decision, not assumed here).
- `validated_store` — Layer 2 outputs: validated records, flags, revisions,
  conflicts, missing entries.
- `derived_store` — Layer 4–6 outputs: analysis results, forecasts, scenarios,
  recommendations, each linked to the input record ids and function versions
  that produced them.
- `audit_log` — append-only: who/what produced each derived output, which
  inputs and function versions, which audit checks ran, veto/flag decisions,
  and human-gate outcomes. The audit log is the evidence chain for any number
  shown to a user.

**Provenance fields (required on every record in every store):**
`source`, `source_timestamp`, `collected_at_pkt`, `freshness`, plus
`record_id`, `created_at_pkt`, `validation_status`, and for derived records,
`input_record_ids` and `function_version`. See `DATA_FLOW_DIAGRAM.md` for the
full field list and stale/missing handling.

**Inputs:** Layer 2 validated/flagged records; Layer 4–6 derived outputs;
Layer 7 task/audit metadata.

**Outputs:** Query interfaces for Layers 4–6 (by symbol, date range,
validation status, provenance) and for Layer 8 (read-only, audit-passed views
only — Layer 8 never writes to these stores except via admin actions defined
in its own spec).

**Interfaces:**

- **From Layer 2:** write validated/flagged/conflict records.
- **To Layers 4–6:** read validated records (with status filtering); write
  derived outputs with input linkage.
- **To Layer 7:** task state, scheduling state, and monitoring counters
  (storage may be shared with Layer 7's own state store, but task state must
  not be confused with financial data — separate tables/schemas).
- **To Layer 8:** read-only views; admin writes go through Layer 7 tasks, not
  direct table edits.

**Failure modes:**

- Disk/full or connection loss: writes fail loudly, upstream layers retry via
  Layer 7 (bounded retries, see Layer 7), and no partial derived output is
  published.
- Schema migration: versioned migrations only; a migration never rewrites raw
  payloads or drops provenance columns.
- Local-dev SQLite limits (concurrency, size): documented as a dev-only
  limitation; exceeding them is a signal to move to the production config, not
  to silently drop data.

**Must NOT do:**

- Overwrite raw payloads or derived outputs in place (append a new version).
- Store a financial number without provenance and input linkage.
- Allow Layer 8 or any LLM path to write financial records directly.
- Present local-dev SQLite as production storage.

### LAYER 4 — Financial Analysis

**Purpose.** Compute descriptive, evidence-based analysis from validated
stored data only: fundamental, technical, sector, macro, health scoring, and
valuation. Analysis describes what the data shows; it does not recommend, and
it does not predict.

**Sub-areas:**

- **Fundamental analysis** — from validated financial-report data (where
  available and validated; coverage UNVERIFIED per company until documented):
  ratios and trends computed by deterministic functions over stored
  statements. Where a statement field is missing, the ratio is absent with a
  reason, not estimated.
- **Technical analysis** — from validated EOD/snapshot data: deterministic
  indicators (e.g. moving averages, volatility measures) defined as functions
  with stated lookback windows and input requirements. No indicator is
  computed over a series with flagged gaps unless the gap handling is stated
  and the output is flagged.
- **Sector analysis** — aggregation by sector (38 sectors per psx-dps claim;
  37 per psxdata claim — the discrepancy itself is recorded, not harmonised
  silently; sector membership comes from the registered source, with its
  provenance). Sector aggregates state which symbols were included/excluded
  and why.
- **Macro analysis** — economic indicators from Layer 1's economic slot,
  **only where a source interface has been verified**. In Phase 1, with all
  economic interfaces UNVERIFIED, macro analysis has no verified inputs and
  must say so; it must not present macro claims from unverified sources.
- **Health scoring** — a deterministic composite score from stated component
  indicators and weights. Weights and components are configuration, recorded
  with the score's function version; the score is not a recommendation and
  carries its components so a user can see what drove it.
- **Valuation** — deterministic valuation computations (e.g. ratio-based
  comparisons) over validated inputs, each labelled with its method, inputs,
  and limitations. A valuation is a computed reference point, not a price
  target or a guarantee.

**Inputs:** Validated records from Layer 3 only (with validation status and
provenance). Function definitions + configuration (weights, windows, methods).

**Outputs (to Layer 3 derived store, for Layers 5–6 and 8):** Analysis results
with input record ids, function version, computation date (PKT), and stated
limitations. Every output states which inputs were missing/flagged and how
that affected the result.

**Interfaces:**

- **From Layer 3:** read validated records.
- **To Layer 3:** write derived analysis outputs.
- **To Layer 5:** analysis outputs as forecasting inputs (via Layer 3, not
  direct calls — forecasting reads stored analysis, so it is reproducible).
- **To Layer 8 (via Layer 3):** analysis views for company pages and dashboards.

**Failure modes:**

- Insufficient validated history (e.g. indicator needs 200 days, only 50
  validated days exist): output is absent or flagged insufficient-data, not
  computed over a shorter window silently.
- Sector membership conflict between sources: aggregate is flagged, both
  memberships recorded.
- Missing statement fields: dependent ratios absent, not estimated.

**Must NOT do:**

- Present analysis as a recommendation, a forecast, or a guarantee.
- Compute over unvalidated, stale-as-live, or conflict-hidden data.
- Invent a ratio, indicator value, or valuation number via an LLM.
- Use an UNVERIFIED macro source as if verified.

### LAYER 5 — Forecasting

**Purpose.** Produce probabilistic, scenario-based forecasts from validated
data and Layer 4 analysis, with explicit validation of the forecasting method
itself. Forecasting is research: it explores what *could* happen under stated
assumptions; it never states what *will* happen.

**Sub-areas:**

- **Statistical forecasting** — deterministic statistical models over
  validated series, with stated assumptions, lookback, and fit/validation
  metrics computed on held-out data where applicable.
- **Quantitative forecasting** — deterministic quantitative models, same
  discipline: assumptions, inputs, and validation metrics recorded.
- **AI-assisted research** — LLM/agent assistance is limited to: selecting
  among pre-defined models, summarising results, drafting explanations, and
  proposing scenarios for human/validation review. The LLM **never generates
  the forecast numbers**; numbers come from deterministic functions, and any
  LLM-drafted text that cites a number must cite the stored function output
  it came from.
- **Scenarios** — each forecast is presented as scenarios (e.g. base / upside /
  downside *as defined by the model's own parameters*, not as invented labels),
  each with its assumptions and the inputs that would invalidate it.
- **Validation** — backtesting / out-of-sample checks where the data allows,
  with results recorded alongside the forecast. A model whose validation fails
  is flagged and not published as if validated. Validation metrics themselves
  are deterministic computations.

**Inputs:** Validated records and Layer 4 analysis from Layer 3; model
definitions + parameters; validation configuration.

**Outputs (to Layer 3 derived store, for Layers 6 and 8):** Forecast outputs
with model id/version, inputs, assumptions, scenarios, uncertainty/limitations,
validation results, and computation date. Every forecast carries a
"probabilistic, not guaranteed" label in any UI surface that shows it.

**Interfaces:**

- **From Layer 3:** read validated data + analysis.
- **To Layer 3:** write forecast outputs with full input linkage.
- **To Layer 6:** forecasts as decision inputs (via Layer 3).
- **To Layer 8 (via Layer 3, after Layer 6 audit where applicable):**
  forecasting views.

**Failure modes:**

- Model produces a result outside sane bounds: flagged by deterministic sanity
  checks, not published, and routed to Layer 7 as an alert.
- Insufficient history or flagged gaps in inputs: forecast absent or flagged,
  not extrapolated silently.
- Validation failure: forecast withheld from decision use until reviewed.

**Must NOT do:**

- Fabricate, smooth, or "adjust" a forecast number by hand or by LLM.
- Present a forecast as certain, guaranteed, or as a price target promise.
- Forecast from unvalidated data, from a single unverified source, or from
  data whose provenance is missing.
- Hide assumptions, scenarios, or validation failures from the user view.

### LAYER 6 — Investment Decisions

**Purpose.** Turn analysis (Layer 4) and forecasts (Layer 5) into
risk-aware, audited decision support: risk assessment, recommendation engine
output, and portfolio optimisation — **without executing trades and without
publishing unaudited recommendations**.

**Sub-areas:**

- **Risk assessment** — deterministic risk measures over validated inputs and
  stated assumptions (e.g. volatility-based measures, concentration measures),
  each with its method, inputs, and limitations. Risk is reported, not hidden
  behind a single score without components.
- **Recommendation engine** — deterministic rules + recorded configuration
  that map analysis/forecast/risk outputs to a recommendation *candidate*
  (e.g. a watchlist flag or a research note). The engine's rules are
  configuration, versioned, and auditable; an LLM may draft the explanatory
  text but may not change the candidate or its numbers.
- **Portfolio optimisation** — deterministic optimisation over validated
  inputs, stated constraints (from configuration, not from a user's unstated
  preferences), and stated objectives. Optimisation output is a *proposed*
  allocation for review, not an executed portfolio, and it states its
  constraints and what would change the result.
- **Independent audit** — a separate audit path (see
  `AGENT_INTERACTION_DIAGRAM.md`): an independent audit agent/function checks
  every recommendation candidate against its inputs, function versions,
  validation status, conflicts, and audit rules, and can **veto** or flag it.
  A vetoed candidate is never shown as a recommendation. Audit results are
  written to the Layer 3 audit log. The audit path is independent of the
  recommendation path: it does not share the recommendation engine's
  configuration as its only check, and its veto cannot be overridden by the
  recommending agent — only by a recorded human decision where the design
  allows it (see the interaction diagram for the gate).

**Inputs:** Layer 4 analysis, Layer 5 forecasts, risk configuration, and
recommendation/optimisation rules — all from Layer 3.

**Outputs (to Layer 3 derived store + audit log, for Layer 8):**
Recommendation candidates with audit status (`passed`, `flagged`, `vetoed`),
risk outputs, and proposed allocations — each with input linkage, rule
version, and audit record. Only `passed` outputs (and, where the design
requires it, human-gated outputs) reach Layer 8 as recommendations.

**Interfaces:**

- **From Layer 3:** read analysis + forecasts.
- **To Layer 3:** write decision outputs + audit records.
- **To Layer 7:** audit vetoes/flags as alerts; human-gate tasks (see
  interaction diagram).
- **To Layer 8 (via Layer 3, audit-passed only):** portfolio advisor and
  report views.

**Failure modes:**

- Audit veto: candidate blocked, reason recorded, Layer 7 alerted; no fallback
  "soft" publication.
- Missing/conflicting inputs: recommendation absent or flagged, not computed
  over substitutes.
- Optimisation infeasible under stated constraints: reported as infeasible
  with the binding constraint, not relaxed silently.

**Must NOT do:**

- Publish an unaudited, flagged, or vetoed recommendation.
- Execute, place, or simulate a real trade or broker order (no broker
  connection exists in Phase 1, and none is assumed).
- Present a recommendation as guaranteed, as personal financial advice for a
  specific user without the required human gate, or without its evidence and
  limitations.
- Let an LLM invent, adjust, or override a recommendation number or audit
  outcome.

### LAYER 7 — Agent Orchestration

**Purpose.** Coordinate all work across layers: which agents/tasks run, in
what order, with what retries, under what cost and monitoring — without itself
computing financial numbers or bypassing Layer 6's audit.

**Components (this layer defines interaction and control; the agent registry
itself belongs to another team and is NOT duplicated here):**

- **Registry use** — Layer 7 looks up agents by role from the registry owned
  by the other team; it does not redefine agents here. If a role is missing
  from the registry, the task fails loudly rather than substituting an
  unregistered agent.
- **Task manager** — task definitions, dependencies (e.g. Layer 2 must complete
  before Layer 4 reads new data), task state (pending / running / done /
  failed / vetoed), and idempotency keys so a retried task does not duplicate
  a send, a write, or a computation.
- **Communication** — typed messages between orchestrator and agents (task
  assignment, result, failure, audit verdict, human-gate request). Message
  formats are versioned; an agent must not act on an unversioned or
  unauthenticated message in a production config (local-dev may log a warning
  instead — see deployment doc).
- **Scheduling** — schedules for collection, validation, analysis, forecasting,
  and reporting tasks. Schedules are configuration, recorded with timezone
  (Asia/Karachi for market tasks). No schedule runs two methods for the same
  job at once (see principle: one sending/computation method active per job).
- **Retries** — bounded retries with backoff for transient failures only
  (network/library errors, temporary storage unavailability). Permanent
  failures (validation failure, audit veto, unregistered agent) are NOT
  retried; they are flagged and alerted.
- **Monitoring** — task success/failure counts, latency, source health (per
  Layer 1 telemetry), validation failure rates, audit veto rates, and data
  freshness dashboards for operators (not end users).
- **Cost control** — every task records its cost drivers (calls, compute,
  storage) where measurable; tasks with a cost budget stop or alert when the
  budget is reached rather than running unbounded. No paid API is used in
  Phase 1, so cost here means compute/time/storage and any future paid-service
  budget — not an invented price.

**Inputs:** Task definitions, schedules, registry lookups, agent results,
audit verdicts, human-gate decisions, telemetry from Layers 1–3.

**Outputs:** Task assignments, task state, alerts, monitoring views, and cost
records (to Layer 3's task/audit stores).

**Interfaces:**

- **To Layer 1:** collection tasks.
- **To Layer 2:** validation tasks and failure alerts.
- **To Layers 4–6:** analysis/forecast/decision tasks, in dependency order.
- **To Layer 8 (admin):** operator views and human-gate tasks (see Layer 8).

**Failure modes:**

- Orchestrator unavailable: tasks queue (do not run unsupervised); on
  recovery, tasks resume from recorded state, not from scratch where
  idempotency allows.
- Duplicate task execution: prevented by idempotency keys; a duplicate
  detection is logged, not executed twice.
- Agent failure mid-task: task marked failed with reason; bounded retry only
  if transient; otherwise alert.

**Must NOT do:**

- Compute financial numbers itself, override a Layer 2 validation result, or
  override a Layer 6 audit veto.
- Run two methods for the same job at once, hide cost, or retry a permanent
  failure in a loop.
- Invent an agent, role, or capability not in the registry.

### LAYER 8 — User Interface

**Purpose.** Present audit-passed, provenance-labelled information to users
and administrators — and collect no financial data directly from users except
through defined admin/portfolio inputs that go through Layer 7 tasks.

**Surfaces:**

- **Public site** — project/market information pages; every market figure
  shown carries its source, source timestamp, and freshness label.
- **Dashboard** — market overview from validated stored data; stale figures
  labelled stale, missing figures shown as missing.
- **Company pages** — per-company analysis (Layer 4) with inputs, methods, and
  limitations visible; no company page claims coverage that is not documented
  in `coverage.json` / the registry.
- **Forecasting views** — Layer 5 outputs with scenarios, assumptions,
  uncertainty, and "probabilistic, not guaranteed" labelling.
- **Portfolio advisor** — Layer 6 audit-passed outputs only, with evidence,
  risk, and limitations; no trade execution button or broker link in Phase 1.
- **Reports** — generated reports that cite stored outputs by id/version, so
  a report can be reproduced from Layer 3.
- **Admin** — operator views (Layer 7 monitoring, validation/audit queues,
  human gates, registry/schedule configuration). Admin actions are tasks via
  Layer 7, not direct database edits, and are logged in the audit log.

**Inputs:** Audit-passed derived outputs and validated records from Layer 3
(read-only); user navigation/filter choices; admin task requests (via Layer 7).

**Outputs:** Rendered pages/reports; admin task requests; usage telemetry
(anonymous counts only — no personal financial data is collected in Phase 1
design).

**Interfaces:**

- **From Layer 3:** read-only views (audit-passed only for recommendations).
- **From Layer 7:** human-gate tasks and monitoring views for admin.
- **To Layer 7:** admin task requests; never direct writes to financial stores.

**Failure modes:**

- Upstream data stale/missing: UI shows the stale/missing label, not a cached
  value presented as fresh.
- Audit-passed output withdrawn (later veto/correction): UI reflects the
  withdrawal with a reason; a previously shown recommendation is not left
  standing silently.

**Must NOT do:**

- Show stale data as live, an unaudited recommendation as a recommendation,
  or a forecast as certain.
- Execute trades, connect to a broker, collect credentials or API keys, or
  accept a payment in Phase 1.
- Write financial records directly to Layer 3.

---

## 5. Cross-layer contracts

- **Provenance contract:** No layer accepts a record without `source`,
  `source_timestamp` (or explicit `null` + reason), `collected_at_pkt`, and
  `freshness`. A layer that receives such a record flags it and does not use
  it as a fact.
- **Validation-status contract:** Layers 4–6 read only records whose
  `validation_status` is `valid`, or explicitly flagged records where the flag
  is part of the analysis (e.g. a missing-data report). They never silently
  include `invalid` records.
- **Conflict contract:** A conflict record in Layer 3 blocks silent use of
  either conflicting value for a decision; the decision layer must record which
  source it used and why (per registry primary-source policy) or surface the
  conflict.
- **Audit contract:** No Layer 6 output reaches Layer 8 without an audit
  record in Layer 3 stating `passed`, `flagged`, or `vetoed`, with reasons.
  `vetoed` never reaches Layer 8 as a recommendation.
- **Determinism contract:** Every financial number in Layers 4–6 is produced
  by a named deterministic function version over named input record ids. If
  either is missing, the number is not published.
- **Timezone contract:** Market timestamps are Asia/Karachi (PKT). Any other
  timezone in a source payload is converted and the conversion recorded; an
  unconvertible timestamp flags the record.

## 8. 11-stage workflow — Phase 1 position (revised brief)

1. **Brainstorm** — Phase 1: scope, layers, rules in this document set.
2. **Research** — Phase 1: verified sources reused from the scaffold registry;
   UNVERIFIED items listed, not researched into false claims.
3. **Validate** — Phase 1: validation, conflict, and audit rules specified;
   live claims validated only where the scaffold already verified them.
4. **Data inspection, read-only only** — Phase 1 limit: inspect READMEs,
   portal pages, and sample shapes; **NO full-scale live data collection**.
5. **Architecture planning** — Phase 1: this document set.
6. **Implementation specification** — Phase 1: layer contracts, message shapes,
   fixed stack, deployment design — specifications, not code.
7. **Documentation** — Phase 1: this document set, including canonical `.mmd`
   diagrams.
8. **Testing strategy defined, not claimed passed** — Phase 1: strategy in
   `DEPLOYMENT_ARCHITECTURE.md` §8. No application test is claimed passed
   (the scaffold's offline tests are a separate scaffold fact, not a claim
   about this application).
9. **Independent audit** — Phase 1: audit *design* (independent audit agent +
   veto path); audit of a built system belongs to later phases.
10. **Correction** — Phase 1: this revision (PKR 0 budget, canonical `.mmd`
    files, fixed stack, no-trade invariant) applied to the Phase 1 docs.
11. **Checkpoint** — Phase 1 ends here. **STOP AFTER PHASE 1.**

## 6. What this architecture deliberately does NOT define (Phase 2+ or other teams)

- Application code, database schemas in DDL, API endpoint paths, or UI
  implementation (Phase 2+; tiny snippets here are illustrative only).
- The agent registry itself (another team owns it; Layer 7 only uses it).
- Per-company coverage claims (Phase 2 live runs document these in
  `coverage.json`).
- Any economic/news source interface (UNVERIFIED until checked against an
  official source).
- Any price, hosting cost, or paid-service tier (see deployment doc:
  ESTIMATE/UNVERIFIED only, no purchase).

## 7. Illustrative snippet (not application code)

The determinism contract, in miniature — a function signature shape only, not
an implementation to run in Phase 1:

```python
# Illustrative only: every Layer 4-6 number comes from a function like this,
# never from LLM text. Inputs are stored record ids; output is recorded with
# function_version and input_record_ids in Layer 3.
def compute_indicator(input_record_ids: list[str], function_version: str) -> dict:
    ...
```

---

*Related Phase 1 docs (same folder): `SYSTEM_ARCHITECTURE_DIAGRAM.md`,
`DATA_FLOW_DIAGRAM.md`, `AGENT_INTERACTION_DIAGRAM.md`,
`DEPLOYMENT_ARCHITECTURE.md`. The data-layer reference scaffold lives at
`~/workspace/psx-data-collection/` and is not modified by this phase.*
