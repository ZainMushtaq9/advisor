# PSX Intelligence AI — Phase Breakdown (Phases 01–30, Full Detail)

> **Purpose.** Implementation-grade detail for every phase in the exact
> named list from `MASTER_ROADMAP.md` (docs version, canonical). Another
> agent must be able to implement a phase from its section without
> guessing. Where a value is not verified it is labelled ESTIMATE or
> UNVERIFIED — never stated as fact.
>
> **Global rules (every phase).** BUDGET PKR 0 ABSOLUTE: no paid APIs,
> subscriptions, hosting, DB, storage, monitoring, or AI services; if a
> free solution cannot satisfy a requirement, document the limitation,
> reduce or defer scope, and never introduce a paid alternative. Local
> hardware / electricity / internet are EXTERNAL operating expenses,
> disclosed, never called free. No sign-ups, installs, purchases,
> credentials, API keys, broker connections, live polling, trading, or
> posting without separate explicit authorisation. **The system must NOT
> execute real trades initially** — Phases 19, 22, 23, 25, 26 are analysis
> and reporting only. Forecasts / targets / recommendations are
> probabilistic with uncertainty stated, never guaranteed. No full-scale
> live data collection in Phase 01 — Phase 01 data work is read-only
> inspection only. PKT is the display timezone for market dates;
> provenance records store retrieval time with timezone.
>
> **Per-phase fields.** Objectives · Tasks/subtasks · Dependencies ·
> Inputs · Outputs · Required files · DB requirements · API requirements ·
> Agent requirements · Free resources · Test cases · Acceptance criteria ·
> Known risks · Completion conditions. "None in this phase" means out of
> scope for that phase, not forgotten.
>
> **Shared vocabulary.** Trading universe ~496 symbols; listed universe
> ~1029 symbols (VERIFIED 2026-11-04; track separately, never conflate).
> 38 sectors (VERIFIED). EOD = end-of-day OHLCV. Snapshot = today's values,
> labelled as snapshot, never as history. Quarantine = suspect rows held
> out of analytic outputs pending review. Provenance record = source,
> retrieval timestamp with timezone, symbols/dates requested vs received,
> gaps, conflicts.
>
> **Phase 01 workflow (11 stages, applied to Phase 01).** (1) Brainstorm.
> (2) Research. (3) Validate. (4) Data inspection, read-only only — NO
> full-scale live data collection in Phase 1. (5) Architecture planning.
> (6) Implementation specification. (7) Documentation. (8) Testing strategy
> defined, not claimed passed. (9) Independent audit. (10) Correction.
> (11) Checkpoint. Phase 01 completes only at stage 11; then STOP — do
> not begin Phase 02 under this roadmap.

---

## Phase 01 — Requirements and architecture

- **Objectives.** Produce the complete, auditable Phase 1 specification:
  scope, non-goals, architecture, source status, provenance rules,
  30-phase sequence, cost/resource model, and acceptance rules — with no
  application code and no later phase started.
- **Tasks/subtasks.** 1.1 Fix scope/non-goals (incl. no-trade rule, PKR 0
  rule). 1.2 Record verified starting condition + UNVERIFIED list.
  1.3 Run the 11-stage workflow and record its evidence. 1.4 Define
  architecture, module boundaries, and data contracts as intent, not code.
  1.5 Adopt provenance / PKT / stale / conflict rules from the referenced
  scaffold (read-only reference). 1.6 Write the full Phase 1 document set.
  1.7 Submit to coordinator audit without claiming a pass.
- **Dependencies.** None within the project, except the verified starting
  condition and the read-only scaffold reference.
- **Inputs.** Verified starting condition (2026-11-04); scaffold README /
  registry / collector / offline tests (read-only); Python 3.12.3, Node
  v24.22.1; Docker / `psql` / `redis-cli` absent.
- **Outputs.** Roadmap (canonical + root summary), this breakdown,
  dependency map, acceptance matrix, cost estimation, resource
  requirements, free-vs-paid comparison, plus sibling teams' Phase 1 specs.
- **Required files.** `docs/phase-01/MASTER_ROADMAP.md`,
  `PHASE_BREAKDOWN.md`, `PHASE_DEPENDENCY_MAP.md`,
  `TASK_ACCEPTANCE_MATRIX.md`, `COST_ESTIMATION.md`,
  `RESOURCE_REQUIREMENTS.md`, `FREE_VS_PAID_COMPARISON.md`, root
  `MASTER_ROADMAP.md`.
- **DB requirements.** None implemented; schema intent only (Phase 03).
- **API requirements.** None implemented; contract conventions only (Phase 05/28 context).
- **Agent requirements.** None implemented; agent intent + approval gates only (Phase 25).
- **Free resources.** Local editor / Python / Node (already present);
  scaffold (read-only); verified free source documentation.
- **Test cases.** Consistency check (same 30 names/order in all docs);
  labelling check (every cost/volume figure VERIFIED/ESTIMATE/UNVERIFIED);
  no-code check (no application code delivered); no-later-phase check.
- **Acceptance criteria.** All 30 phases defined with the full field set;
  no invented price/benchmark/API/endpoint/capability; UNVERIFIED sources
  listed as blockers; Phase 1 rows in the matrix PENDING-AUDIT.
- **Known risks.** Sibling specs contradicting this set; an unverified
  source treated as verified elsewhere; scope creep into Phase 02.
- **Completion conditions.** Coordinator audit passes AND audit findings
  are corrected AND the Phase 01 checkpoint is frozen. Until then, Phase 01
  is not complete, regardless of document volume.

## Phase 02 — Repository and development environment

- **Objectives.** A version-controlled repository and reproducible local
  development environment on free tooling, so every later phase builds the
  same way on any developer machine with no paid tooling.
- **Tasks/subtasks.** 2.1 Initialise the repository (or adopt the existing
  project folder under version control) with a documented layout. 2.2 Pin
  the toolchain baseline (Python 3.12.3, Node v24.22.1 as verified) and
  record how a different local version is handled. 2.3 Define dependency
  policy: stdlib-first, free licences only, lockfile, no paid package.
  2.4 Provide local setup/run/test instructions and a smoke check.
  2.5 Define branching, review, and contribution workflow for later teams.
- **Dependencies.** Phase 01.
- **Inputs.** Phase 01 architecture intent; verified tool versions;
  project folder `~/workspace/psx-intelligence-ai/`.
- **Outputs.** Repository layout, environment setup docs, dependency
  policy, smoke check.
- **Required files.** Repository README, environment setup guide,
  dependency lockfile(s), contribution workflow note, smoke-check script.
- **DB requirements.** None (database itself is Phase 03; this phase only
  ensures the DB tooling choice can run locally).
- **API requirements.** None.
- **Agent requirements.** None.
- **Free resources.** Local Python/Node, version control tooling already
  available locally, free-licence packages only.
- **Test cases.** Fresh-checkout setup test (follow the guide on a clean
  checkout, reach the smoke check); dependency-licence check (no paid /
  unknown-licence dependency); smoke check passes locally.
- **Acceptance criteria.** A new developer can set up locally from the
  guide alone; no paid tool is required; the smoke check is documented
  and runnable.
- **Known risks.** Tool versions drifting from the verified baseline;
  a dependency introducing a paid or incompatible licence.
- **Completion conditions.** Setup guide verified by a fresh-checkout run;
  dependency policy recorded; repository layout frozen for Phase 03+.

## Phase 03 — Database architecture

- **Objectives.** Design (and prepare for implementation) the local-first
  database covering registry, market data, statements, announcements,
  macro data, analysis outputs, and provenance, with migrations, indexes,
  and backup/restore defined before any collector writes to it.
- **Tasks/subtasks.** 3.1 Design tables for all Phase 04–27 data domains,
  including per-field source + as-of columns. 3.2 Choose SQLite for local
  development; design the schema PostgreSQL-compatible (types, constraints,
  migrations) so a later move is a migration, not a rewrite — without
  claiming a live PostgreSQL deployment (tooling not installed). 3.3 Write
  numbered, reversible-where-feasible migrations. 3.4 Add indexes for hot
  queries (symbol+date, sector, latest snapshot, screen filters). 3.5 Define
  backup/restore + retention (EOD history vs snapshots vs provenance).
  3.6 Define fixture/seed strategy (fixtures labelled as fixtures).
- **Dependencies.** Phases 01, 02.
- **Inputs.** Phase 01 intent; Phase 02 environment; volume estimates in
  `RESOURCE_REQUIREMENTS.md`.
- **Outputs.** Schema definition, migrations, index plan, backup/restore
  and retention procedures.
- **Required files.** Schema/migration files, seed/fixture files, DB
  design document, backup/restore runbook section.
- **DB requirements.** This phase IS the DB design: ACID storage; unique
  (symbol, date, source) constraint for EOD idempotency; foreign keys to
  registry; provenance linkage; quarantine flags.
- **API requirements.** Internal data-access layer conventions only.
- **Agent requirements.** None.
- **Free resources.** SQLite (stdlib-adjacent, free), local file backup,
  Python stdlib.
- **Test cases.** Migration up/down on empty DB; duplicate-EOD constraint
  test; query-plan check on fixtures for hot queries; backup-then-restore
  round-trip on fixtures.
- **Acceptance criteria.** Migrations run cleanly on empty local DB;
  duplicates cannot silently accumulate; backup/restore round-trip passes;
  no PostgreSQL deployment is claimed.
- **Known risks.** PostgreSQL tooling absent locally; schema missing a
  later domain (e.g. sector-membership history) forcing a breaking change.
- **Completion conditions.** Schema + migrations + backup/restore
  procedure reviewed and test-passing on fixtures; Phase 04 may proceed.

## Phase 04 — PSX company registry

- **Objectives.** The authoritative company registry for the PSX universe,
  kept distinct from price data, so identity, listing status, and sector
  membership are never confused with market history.
- **Tasks/subtasks.** 4.1 Model symbols: identifier, name, listing status
  (trading vs listed-only), sector (38 verified sectors). 4.2 Populate
  from verified sources only; record per-record source + as-of date.
  4.3 Handle symbol changes / delistings as history, not silent overwrites
  (where source data supports it; otherwise record the gap). 4.4 Reconcile
  the ~496 trading vs ~1029 listed counts and report the difference
  explicitly. 4.5 Provide the registry dataset consumed by Phases 06–13, 26, 28.
- **Dependencies.** Phases 01, 02, 03 (schema), 05 (backend conventions
  may be applied in parallel — see dependency map for the 04/05 ordering note).
- **Inputs.** Verified universe counts and sector count; verified source
  symbol data; Phase 03 schema.
- **Outputs.** Registry store, registry report (counts by status/sector),
  change-history handling.
- **Required files.** Registry model/loader, registry report generator,
  registry documentation (field + source definitions).
- **DB requirements.** Registry table(s) with status, sector, source,
  as-of columns; history handling for status/sector changes.
- **API requirements.** Internal registry lookup only in this phase.
- **Agent requirements.** None.
- **Free resources.** Verified free sources (`psx-dps` / `psxdata`
  symbol data where they provide it), local DB.
- **Test cases.** Count reconciliation test (trading + listed-only =
  listed total on fixtures, with gaps reported); duplicate-symbol test;
  source-label test (every record has a source); sector-count test.
- **Acceptance criteria.** Every registry record has source + as-of date;
  trading vs listed counts are reported separately and reconcile (or gaps
  are listed); no symbol appears without a status.
- **Known risks.** Source symbol lists disagreeing; sector assignments
  changing over time without a history feed.
- **Completion conditions.** Registry report published with counts,
  coverage, and gaps; collectors (Phases 06–07) may key off it.

## Phase 05 — Backend foundation

- **Objectives.** Shared backend foundation — configuration, logging,
  provenance recording, error handling, module boundaries — on free local
  tooling, so collectors and engines share conventions instead of each
  inventing its own.
- **Tasks/subtasks.** 5.1 Configuration: environment-based, local-first,
  no secrets in code/config files (see Phase 29 for hardening). 5.2 Logging:
  structured, local, per-module, with provenance-aware log fields.
  5.3 Provenance module: every fetch/derivation records source, retrieval
  time with timezone, coverage, gaps, conflicts. 5.4 Error handling +
  retry/backoff conventions; stale-data and conflict rules adopted from
  the scaffold. 5.5 Module boundaries: collectors vs engines vs API vs UI
  contracts (internal only at this stage).
- **Dependencies.** Phases 01, 02, 03. (Phase 04 may run in parallel once
  the schema exists; the dependency map records 05 as a soft dependency
  of 04's loader implementation, not of its model.)
- **Inputs.** Phase 01 architecture; Phase 03 schema; scaffold provenance
  / PKT / stale / conflict rules (reference).
- **Outputs.** Backend foundation modules, configuration + logging +
  provenance conventions, error-handling guide.
- **Required files.** Config module, logging module, provenance module,
  error-handling module, backend conventions document.
- **DB requirements.** Provenance records persistable/queryable by source,
  symbol, date (schema from Phase 03).
- **API requirements.** Internal module interfaces only; no user-facing API yet.
- **Agent requirements.** None (foundation only; agents arrive Phase 25).
- **Free resources.** Python stdlib, local logging, SQLite.
- **Free resources note.** All free resources in this phase are local and
  licence-free; no external service is required.
- **Test cases.** Provenance-recording test (every operation writes a
  record); stale-marking test; conflict-recording test (both values kept);
  config test (no secret in code/config fixtures); offline test run.
- **Acceptance criteria.** Every fetch/derivation produces a provenance
  record; stale data is flagged, never silently fresh; conflicts keep both
  values; no secret appears in code or config.
- **Known risks.** Conventions ignored by a later module; provenance
  overhead slowing collectors (measure in Phase 27, do not pre-optimise).
- **Completion conditions.** Foundation modules test-passing and adopted
  as the import path for Phases 06+; conventions document frozen.

## Phase 06 — Historical market data collector

- **Objectives.** Resumable, idempotent collection of ~5 years of EOD
  history for the trading universe from verified sources, with provenance
  per fetch and no historical intraday claim.
- **Tasks/subtasks.** 6.1 Implement the backfill runner (symbol-by-symbol
  or batched, polite pacing, retry with backoff). 6.2 Handle the `psx-dps`
  multi-node 404 quirk via the documented fallback path; record which
  path succeeded/failed — do not invent an endpoint. 6.3 Resume state
  (per-symbol progress, last successful date, failure list). 6.4 Enforce
  idempotency via Phase 03 constraints. 6.5 Validate every batch (quality
  rules defined here and reused later; full validation layer is part of
  this collector's acceptance, not a separate phase). 6.6 Backfill report:
  rows/symbol, coverage, gaps, failures, quarantine counts, request counts.
  6.7 Track listed-only symbols separately (no data vs fetch failure).
- **Dependencies.** Phases 02, 03, 04, 05.
- **Inputs.** Registry (Phase 04); backend foundation (Phase 05); verified
  sources `psx-dps` / `psxdata`; ~5y EOD coverage claim (VERIFIED as a
  source property, re-measured by the backfill report).
- **Outputs.** Backfilled EOD store (or verified partial store + gap
  report), resume state, backfill report.
- **Required files.** Backfill runner, resume-state store, backfill report
  generator, collector runbook.
- **DB requirements.** EOD tables at full-market scale (ESTIMATE arithmetic
  in `RESOURCE_REQUIREMENTS.md`); resume-state + run-log tables.
- **API requirements.** None user-facing; operator CLI hooks only.
- **Agent requirements.** None.
- **Free resources.** `psx-dps` (MIT, zero deps, no API key), `psxdata`
  (MIT, PyPI alpha), Python stdlib, SQLite.
- **Test cases.** Idempotency (run twice, same row count); resume
  (interrupt on fixtures, resume, complete); 404-quirk fixture test;
  gap-report test; quarantine-exclusion test.
- **Acceptance criteria.** Re-run adds zero duplicates; interrupted run
  resumes without loss; report accounts for every symbol (complete /
  partial with gaps / failed with reason); no symbol reported complete
  while quarantined rows are unresolved without a note.
- **Known risks.** Source rate limits/coverage changes (UNVERIFIED until
  measured); 404 failures on a subset; long local run times.
- **Completion conditions.** Backfill report published; coverage/gaps
  known; Phases 07, 11–13 may consume the covered universe/dates only —
  never assumed coverage.

## Phase 07 — Market snapshot collector

- **Objectives.** Today's snapshot / tick-view collection from verified
  sources only, labelled as snapshots (not history), with freshness
  timestamps and stale marking, and no live polling or guaranteed
  real-time claim.
- **Tasks/subtasks.** 7.1 Implement snapshot fetch from verified sources.
  7.2 Store snapshots with retrieval timestamp + source; short retention
  per Phase 03 policy. 7.3 Freshness indicators: last successful refresh,
  symbols missing today, stale flags for all downstream consumers.
  7.4 Scheduling documentation for local operation (manual / OS scheduler);
  no polling loop that hammers a source. 7.5 Distinguish non-trading days
  from fetch failures only where a verified calendar basis exists;
  otherwise report neutrally ("no new rows") without asserting a holiday.
- **Dependencies.** Phases 03, 04, 05, 06.
- **Inputs.** Registry; backfill state; verified snapshot coverage
  (`psx-dps` today's ticks, `psxdata` live snapshots — VERIFIED as source
  properties).
- **Outputs.** Snapshot store, freshness indicators, refresh reports,
  scheduling documentation.
- **Required files.** Snapshot collector, freshness module, refresh report
  generator, scheduling documentation.
- **DB requirements.** Snapshot table (short retention), refresh-run log,
  freshness state per symbol.
- **API requirements.** None user-facing in this phase; exposed later via dashboard (Phase 28).
- **Agent requirements.** None.
- **Free resources.** `psx-dps`, `psxdata` (as above), Python stdlib, local scheduler.
- **Test cases.** Snapshot-vs-history labelling test; stale-flag test;
  same-day idempotency test; non-trading-day neutral-report test on fixtures.
- **Acceptance criteria.** Every snapshot carries retrieval timestamp +
  source; stale data is flagged downstream; refresh failures name failed
  symbols; no real-time guarantee is made anywhere.
- **Known risks.** Snapshot availability varying by source; no verified
  standalone market-calendar feed (UNVERIFIED); refresh/backfill overlap.
- **Completion conditions.** Snapshot + freshness behaviour verified on
  fixtures and at least one real refresh cycle report; dashboard phases
  may consume freshness indicators.

## Phase 08 — Financial statement collector

- **Objectives.** Design, and only after source verification implement,
  collection of financial-statement data. Until verification, ship the
  framework, field model, and checklist — not data from an assumed source.
- **Tasks/subtasks.** 8.1 Define the statement field model (statement
  types, periods, line items — as a model, with per-field source labels).
  8.2 Build the collector framework (fetch → validate → provenance →
  store → quarantine) reusing Phases 05–06 patterns. 8.3 Execute the
  verification checklist per candidate source: licence, machine-readable
  access, coverage, update frequency, attribution. Record results with
  dates; do not pre-fill passes. 8.4 Only on a verified source: implement
  the source adapter and populate statements. 8.5 Missing-field display
  rule: missing = "not available from verified sources", never zero.
- **Dependencies.** Phases 03, 04, 05. Data-ingestion sub-tasks depend
  additionally on a VERIFIED source (blocker until then).
- **Inputs.** Registry; backend foundation; candidate-source names only
  (their machine-use is UNVERIFIED — no endpoint or licence is asserted here).
- **Outputs.** Statement field model + framework + verification results;
  statement data ONLY if a source verifies.
- **Required files.** Statement model, collector framework, verification
  checklist results, adapter (only on verification), missing-field rules.
- **DB requirements.** Statement tables with per-field source, period,
  as-of columns; quarantine linkage.
- **API requirements.** None user-facing in this phase.
- **Agent requirements.** None.
- **Free resources.** Python stdlib, SQLite, local validation tooling.
  No free statement source is asserted as available.
- **Test cases.** Framework test on fixtures (fetch→validate→store→
  quarantine path); verification-gate test (unverified source cannot be
  enabled); missing-field test (no silent zero); source-label test.
- **Acceptance criteria.** No statement field ships without a source label;
  no UNVERIFIED source's data appears; framework works on fixtures even
  with zero verified sources.
- **Known risks.** No verified machine-readable statement source may be
  found — the known blocker; statement formats differing by company.
- **Completion conditions.** Framework + checklist complete AND either
  (a) a source is verified and populated, or (b) the phase closes with a
  documented limitation and Phases 11/15/16 proceed on verified data alone.
  The phase does not stay "in progress" forever waiting for a source.

## Phase 09 — Corporate announcement collector

- **Objectives.** Design, and only after source verification implement,
  collection of corporate announcements, with the same gated pattern as
  Phase 08.
- **Tasks/subtasks.** 9.1 Define the announcement model (company, date,
  category, title/text reference, source link where lawfully available).
  9.2 Build the collector framework reusing Phases 05–06 patterns.
  9.3 Execute the verification checklist per candidate announcement
  source (access, licence/redistribution terms, coverage, timeliness).
  9.4 Only on a verified source: implement the adapter and populate.
  9.5 Deduplication: same announcement from multiple paths stored once,
  with provenance for each path.
- **Dependencies.** Phases 03, 04, 05. Data ingestion blocked on a VERIFIED source.
- **Inputs.** Registry; backend foundation; candidate-source names only (UNVERIFIED).
- **Outputs.** Announcement model + framework + verification results;
  announcement data ONLY if a source verifies.
- **Required files.** Announcement model, collector framework,
  verification checklist results, adapter (only on verification),
  deduplication rules.
- **DB requirements.** Announcement tables with source, date, category,
  deduplication keys, provenance linkage.
- **API requirements.** None user-facing in this phase.
- **Agent requirements.** None.
- **Free resources.** Python stdlib, SQLite. No free announcement source
  is asserted as available.
- **Test cases.** Framework test on fixtures; verification-gate test;
  deduplication test (same announcement twice → one record); source-label test.
- **Acceptance criteria.** No announcement ships without source + date;
  no UNVERIFIED source's data appears; duplicates are not double-counted.
- **Known risks.** No verified machine-readable announcement source may
  be found; announcement text redistribution may be licence-limited even
  if headlines are available (check, do not assume).
- **Completion conditions.** Framework + checklist complete AND either a
  source is verified and populated, or the phase closes with a documented
  limitation and downstream phases proceed without announcement inputs.

## Phase 10 — Macroeconomic data collector

- **Objectives.** Design, and only after verification implement,
  collection of macroeconomic series. SECP / SBP / PBS / Finance Division /
  World Bank / IMF / FRED machine-use is UNVERIFIED, so this phase is
  gated: framework and checklist first, ingestion only on a verified source.
- **Tasks/subtasks.** 10.1 Define the macro series model (series, unit,
  frequency, vintage/revision handling — revisions stored, not overwritten
  silently). 10.2 Build the collector framework reusing Phases 05–06.
  10.3 Execute the verification checklist per candidate source (SECP, SBP,
  PBS, Finance Division, World Bank, IMF, FRED — each separately):
  licence, machine-readable endpoint, coverage, frequency, attribution.
  10.4 Only on a verified source: implement the adapter and populate.
  10.5 Document which analyses may use macro data and which must not
  depend on it (fallback: verified PSX data alone).
- **Dependencies.** Phases 03, 05. Data ingestion blocked on a VERIFIED source per series.
- **Inputs.** Backend foundation; candidate-source names only (UNVERIFIED).
- **Outputs.** Macro series model + framework + per-source verification
  results; macro data ONLY for verified series.
- **Required files.** Macro model, collector framework, per-source
  verification results, adapter(s) (only on verification), revision policy.
- **DB requirements.** Macro series tables with series, date, value, unit,
  source, vintage, revision flag.
- **API requirements.** None user-facing in this phase.
- **Agent requirements.** None.
- **Free resources.** Python stdlib, SQLite. No free macro feed is
  asserted as available until verified.
- **Test cases.** Framework test on fixtures; per-source verification-gate
  test; revision test (revised value stored as new vintage, history kept);
  source-label test.
- **Acceptance criteria.** No macro series ships without source + vintage;
  no UNVERIFIED source's data appears; downstream phases have a documented
  no-macro fallback.
- **Known risks.** All listed macro sources may remain UNVERIFIED;
  series revisions breaking naive comparisons; differing frequencies.
- **Completion conditions.** Framework + per-source checklist complete
  AND either verified series are populated, or the phase closes with a
  documented limitation and Phases 11/17 proceed on verified PSX data alone.

---

## Phase 11 — Fundamental analysis

- **Objectives.** Compute fundamental analysis from verified, stored data
  (registry + statements once available + market data), every figure
  traceable to a stored source and as-of date, missing inputs shown as missing.
- **Tasks/subtasks.** 11.1 Define fundamental metrics and their formulas
  (fixed by the implementing team and documented — no benchmark invented
  here). 11.2 Compute metrics over stored data only; exclude quarantined
  rows. 11.3 Attach source + as-of + coverage to every output. 11.4 Handle
  missing statements/macro inputs explicitly (metric withheld or flagged).
  11.5 Provide the fundamental dataset for Phases 15, 16, 22, 26, 28.
- **Dependencies.** Phases 04, 06, 07; Phase 08 and Phase 10 inputs are
  optional (used only if those phases verified a source).
- **Inputs.** Registry, EOD/snapshot data, statement data (if verified),
  macro data (if verified).
- **Outputs.** Fundamental metrics store + metric definitions document.
- **Required files.** Fundamental metric definitions, computation modules,
  output store definitions, missing-input handling rules.
- **DB requirements.** Fundamental metric tables keyed by (symbol, period,
  metric) with source + as-of columns.
- **API requirements.** Internal computation interface; user-facing
  exposure via Phase 28.
- **Agent requirements.** None (deterministic computation; agents may
  explain it in Phase 25+, not compute it opaquely).
- **Free resources.** Python stdlib, SQLite, stored verified data.
- **Test cases.** Hand-computed fixture test per metric; missing-input
  test (withheld/flagged, not zero); quarantine-exclusion test;
  traceability test (output → stored source rows).
- **Acceptance criteria.** Every metric matches a hand-computed fixture;
  every output carries source + as-of; missing inputs never silently
  zero-filled.
- **Known risks.** Statement/macro gaps (Phases 08/10 gated) limiting
  metric coverage; period misalignment (fiscal vs calendar) if not documented.
- **Completion conditions.** Metrics computed for the covered universe
  with coverage report; gaps listed; downstream phases may consume the
  covered set only.

## Phase 12 — Technical analysis

- **Objectives.** Deterministic technical-analysis engine over validated
  EOD data, documented per indicator, with no indicator presented as a
  standalone buy/sell signal.
- **Tasks/subtasks.** 12.1 Implement trend, momentum, volatility, and
  volume measures (windows/formulas documented by the implementing team).
  12.2 Document per indicator: formula, window, minimum history, edge
  behaviour. 12.3 Insufficient history → "insufficient data", never a
  fabricated value. 12.4 Wire to validated EOD only (quarantined excluded).
  12.5 Default compute-on-demand; cache only if Phase 27 measurement
  proves a need (do not pre-optimise).
- **Dependencies.** Phases 06, 07.
- **Inputs.** Validated EOD data; registry.
- **Outputs.** Indicator library + indicator documentation.
- **Required files.** Indicator modules, indicator documentation, unit
  tests with hand-computed fixtures.
- **DB requirements.** Optional indicator cache tables only if stored
  results are chosen; otherwise none new.
- **API requirements.** Internal engine interface; exposure via Phase 28.
- **Agent requirements.** None.
- **Free resources.** Python stdlib, SQLite, validated EOD data.
- **Test cases.** Hand-computed fixture per indicator; insufficient-history
  test; quarantine-exclusion test; determinism test (same input → same output).
- **Acceptance criteria.** Every indicator matches a hand-computed fixture;
  insufficient history yields "insufficient data"; no output is labelled
  a buy/sell signal; results are deterministic.
- **Known risks.** Long windows unusable on newly listed symbols;
  window choices needing user-visible rationale.
- **Completion conditions.** Library + documentation test-passing;
  Phases 20, 22, 28 may consume indicators with their insufficiency states.

## Phase 13 — Sector intelligence

- **Objectives.** Sector intelligence across the 38 verified sectors and
  market breadth from validated data, recomputable from constituents, with
  denominators and coverage stated.
- **Tasks/subtasks.** 13.1 Sector aggregates: constituent count, aggregate
  performance over documented windows, within-sector breadth. 13.2 Market
  breadth: advancers/decliners/unchanged per day, participation rates,
  denominator = symbols with valid data that day (stated). 13.3 Index
  context only where a verified index series exists; otherwise state
  unavailability — do not synthesise an index. 13.4 Store aggregates with
  as-of dates + constituent lists for recomputation.
- **Dependencies.** Phases 04, 06, 07, 11 (fundamental context where available).
- **Inputs.** Validated EOD data; registry sector membership; fundamentals (optional).
- **Outputs.** Sector aggregate tables, breadth tables, sector-comparison dataset.
- **Required files.** Sector/breadth modules, aggregate store definitions,
  recomputation documentation.
- **DB requirements.** Aggregate tables keyed by (sector, date) and
  (breadth, date), with constituent-count + coverage columns.
- **API requirements.** Internal dataset interface; exposure via Phase 28.
- **Agent requirements.** None.
- **Free resources.** Python stdlib, SQLite, validated data.
- **Test cases.** Hand-computed fixture (small set, known advancers/
  decliners); denominator test (valid-data count, not listed total);
  recomputation test (same constituents → same aggregate).
- **Acceptance criteria.** Every aggregate recomputes from stored
  constituents; breadth denominators stated; no synthesised index;
  quarantined rows excluded.
- **Known risks.** Sector membership changes over time not captured;
  partial backfill coverage skewing breadth.
- **Completion conditions.** Aggregates + breadth published with coverage
  notes ("based on N of ~496 symbols with valid data on this date");
  dashboard phases may display them with that note.

## Phase 14 — News intelligence

- **Objectives.** Design, and only after source verification implement,
  news collection and classification. Until a verified, lawfully usable
  news source is established, ship framework, taxonomy, and checklist —
  not news content from an assumed source.
- **Tasks/subtasks.** 14.1 Define the news model (item, date, source,
  company linkage, category taxonomy). 14.2 Build collection + classification
  framework (company linkage rules, category rules, deduplication).
  14.3 Execute the verification checklist per candidate source (access,
  licence/redistribution, coverage, timeliness, attribution). 14.4 Only on
  a verified source: implement adapter + populate. 14.5 Sentiment or
  classification outputs, if any, are labelled as model outputs with
  method stated — never as facts about a company.
- **Dependencies.** Phases 03, 04, 05. Data ingestion blocked on a VERIFIED source.
- **Inputs.** Registry; backend foundation; candidate-source names only (UNVERIFIED).
- **Outputs.** News model + framework + taxonomy + verification results;
  news data ONLY if a source verifies.
- **Required files.** News model, classification framework, taxonomy,
  verification results, adapter (only on verification).
- **DB requirements.** News tables with source, date, company linkage,
  category, provenance; classification outputs with method label.
- **API requirements.** None user-facing in this phase.
- **Agent requirements.** None in this phase (agents consume news in Phase 25+ only if verified).
- **Free resources.** Python stdlib, SQLite. No free news source is
  asserted as available.
- **Test cases.** Framework test on fixtures; verification-gate test;
  company-linkage test (ambiguous linkage → flagged, not guessed);
  deduplication test.
- **Acceptance criteria.** No news item ships without source + date;
  no UNVERIFIED source's content appears; classification method is stated
  wherever a classification is shown.
- **Known risks.** No verified lawfully usable news source may be found;
  copyright/redistribution limits even for headlines (check, do not assume).
- **Completion conditions.** Framework + taxonomy + checklist complete
  AND either a source is verified and populated, or the phase closes with
  a documented limitation and Phases 22/26 proceed without news inputs.

## Phase 15 — Financial health scoring

- **Objectives.** Transparent financial-health scores from verified
  fundamentals and market data, with formula, inputs, and limitations
  published alongside every score; no score as a guarantee of future
  health or performance.
- **Tasks/subtasks.** 15.1 Define the scoring formula, input metrics,
  weights/bands, and edge behaviour (documented by the implementing team).
  15.2 Compute scores over verified stored data only; withhold/flag where
  inputs are missing. 15.3 Publish formula + inputs + limitations with
  every score. 15.4 Version the formula: score history keeps the formula
  version that produced it.
- **Dependencies.** Phases 11, 12 (market context), 13 (sector context, optional).
- **Inputs.** Fundamental metrics, technical/market context, sector context.
- **Outputs.** Health-score store + scoring documentation.
- **Required files.** Scoring model, computation modules, scoring
  documentation, version-history handling.
- **DB requirements.** Score tables keyed by (symbol, date, formula
  version) with input references.
- **API requirements.** Internal interface; exposure via Phase 28.
- **Agent requirements.** None (deterministic scoring; explanation only via Phase 25+).
- **Free resources.** Python stdlib, SQLite, verified stored data.
- **Test cases.** Hand-computed fixture per score band; missing-input
  test; formula-version test (old scores keep old version); determinism test.
- **Acceptance criteria.** Every score matches a hand-computed fixture;
  formula + inputs + limitations accompany every score; no score is
  presented as a guarantee.
- **Known risks.** Statement gaps (Phase 08 gated) limiting coverage;
  weights perceived as judgement — mitigated by publishing them, not by hiding them.
- **Completion conditions.** Scores computed for the covered universe
  with coverage report; formula versioned; Phases 16, 22 may consume scores.

## Phase 16 — Valuation engine

- **Objectives.** Valuation calculations from verified inputs with
  methods, assumptions, and sensitivity ranges stated per output; where a
  required input is UNVERIFIED or missing, valuation is withheld or
  range-bounded and labelled — never completed with an invented input.
- **Tasks/subtasks.** 16.1 Define valuation methods and their required
  inputs (fixed/documented by the implementing team). 16.2 Implement
  calculations with assumption + sensitivity-range outputs. 16.3 Withhold
  or range-bound outputs where inputs are missing/UNVERIFIED, with the
  reason stated. 16.4 Store method + assumptions + inputs with every output.
- **Dependencies.** Phases 11, 15; Phase 08 inputs optional (only if verified).
- **Inputs.** Fundamental metrics, health scores, market data; statements
  (if verified).
- **Outputs.** Valuation store + method/assumption documentation.
- **Required files.** Valuation method definitions, calculation modules,
  sensitivity-range handling, output documentation.
- **DB requirements.** Valuation tables keyed by (symbol, date, method)
  with assumption + input references.
- **API requirements.** Internal interface; exposure via Phase 28.
- **Agent requirements.** None.
- **Free resources.** Python stdlib, SQLite, verified stored data.
- **Test cases.** Hand-computed fixture per method; missing-input test
  (withheld/range-bounded with reason); sensitivity test (input change →
  range change in the documented direction); traceability test.
- **Acceptance criteria.** Every valuation matches a hand-computed fixture
  or is withheld with reason; methods + assumptions + ranges accompany
  every output; no invented input completes a valuation.
- **Known risks.** Statement gaps limiting method coverage; valuation
  methods misread as price predictions (mitigated by on-screen method +
  range + limitation text in Phase 28).
- **Completion conditions.** Valuations computed for the covered universe
  with coverage + withheld-reason report; Phases 19, 22 may consume them.

## Phase 17 — Statistical forecasting

- **Objectives.** Transparent statistical forecasting baselines over EOD
  history, evaluated out-of-sample with error bands, reported as
  probabilistic forecasts with limitations — never guaranteed future prices.
- **Tasks/subtasks.** 17.1 Define baseline models (trend/seasonal/
  regression-style, fixed/documented by the implementing team). 17.2 Train
  on history, evaluate out-of-sample (no look-ahead: training data strictly
  before evaluation data). 17.3 Output forecasts with error bands +
  horizon + method + training window. 17.4 Publish evaluation reports
  (error metrics on held-out data, limitations). 17.5 Macro features only
  if Phase 10 verified a source; baselines must work on verified PSX data alone.
- **Dependencies.** Phases 06, 11, 12, 13.
- **Inputs.** Validated EOD history, technicals, sector context, fundamentals
  (optional), macro (optional, only if verified).
- **Outputs.** Forecast baselines, forecast store with uncertainty fields,
  evaluation reports.
- **Required files.** Baseline model definitions, training/evaluation
  modules, forecast store definitions, evaluation reports.
- **DB requirements.** Forecast tables keyed by (symbol, horizon, method,
  forecast date) with error-band + training-window columns.
- **API requirements.** Internal interface; exposure via Phase 28.
- **Agent requirements.** None (statistical baselines; AI layer is Phase 18).
- **Free resources.** Python stdlib + free-licence scientific libraries
  available locally (only those already free; no paid library); SQLite.
- **Test cases.** No-look-ahead test (training/evaluation split enforced);
  hand-computed fixture for a simple baseline; error-band test (bands
  present and non-degenerate); determinism/reproducibility test.
- **Acceptance criteria.** Out-of-sample evaluation exists for every
  baseline; every forecast carries horizon + method + error band; no
  forecast is presented as guaranteed.
- **Known risks.** Overfitting on short histories; regime change making
  held-out performance unrepresentative (stated in limitations).
- **Completion conditions.** Baselines evaluated + reported; forecasts
  stored with uncertainty; Phases 18–20, 22 may consume them.

## Phase 18 — AI forecasting

- **Objectives.** AI-assisted forecasting and interpretation that cites
  stored numbers, states uncertainty, and never invents figures, papers,
  or sources — an explanation layer over Phases 11–17, not a replacement.
- **Tasks/subtasks.** 18.1 Define AI tasks narrowly (explain a forecast,
  summarise evidence, flag what would change it). 18.2 Implement citation
  rules: every AI numeric claim must match a stored figure or be withheld.
  18.3 Implement uncertainty + limitation text on every AI output.
  18.4 Log token usage and model/method per output (PKR 0 rule: free/local
  options only; no paid AI service). 18.5 Human-review path for AI outputs
  shown in Phase 28 (review flag, not silent publication).
- **Dependencies.** Phases 11, 12, 13, 15, 16, 17.
- **Inputs.** Fundamental/technical/sector outputs, scores, valuations,
  statistical forecasts, stored provenance.
- **Outputs.** AI interpretation/forecast layer, citation rules, token-usage log.
- **Required files.** AI task definitions, prompt/template definitions,
  citation rules, token-usage logging, review-flag handling.
- **DB requirements.** AI output tables with cited-figure references,
  method/model label, token-usage fields.
- **API requirements.** Internal interface; exposure via Phase 28 with review flags.
- **Agent requirements.** This phase defines AI behaviour consumed by
  Phase 25 orchestration; it does not itself grant agents outward actions.
- **Free resources.** Free/local AI options only (no paid service; the
  specific free/local option is chosen by the implementing team and its
  free terms recorded — no paid option is introduced as an alternative).
  If no free/local option satisfies a sub-task, that sub-task is documented
  as a limitation and reduced/deferred.
- **Test cases.** Citation test (AI claim without a stored figure →
  withheld/flagged); invented-figure test on fixtures; uncertainty-text
  test (every output carries it); token-log test.
- **Acceptance criteria.** No AI output contains an uncited numeric claim;
  uncertainty + limitations accompany every output; token usage is logged;
  no paid AI service is used.
- **Known risks.** AI hallucination despite citation rules (mitigated by
  citation checks + review flags, not by trusting the model); free/local
  model capability limits (documented, not solved by purchase).
- **Completion conditions.** AI layer test-passing on citation/uncertainty
  cases; Phases 19, 22, 25, 28 may consume AI outputs with their flags.

## Phase 19 — Price target engine

- **Objectives.** Probabilistic, range-based price targets as analysis
  outputs with method, inputs, horizon, and uncertainty shown.
  **The system must NOT execute real trades initially, and no price target
  is a buy/sell instruction or a guaranteed outcome.**
- **Tasks/subtasks.** 19.1 Define target methods combining valuations,
  forecasts, and technicals (documented by the implementing team). 19.2 Compute
  targets as ranges (not point guarantees) with horizon + method + inputs.
  19.3 Show uncertainty + limitations with every target. 19.4 Store target
  history (targets are versioned; past targets are not rewritten). 19.5
  Explicit no-trade guard: no code path from a target to an order, broker,
  or external action exists in this phase.
- **Dependencies.** Phases 16, 17, 18, 12.
- **Inputs.** Valuations, statistical forecasts, AI outputs, technicals.
- **Outputs.** Price-target store + target method documentation.
- **Required files.** Target method definitions, computation modules,
  target history handling, no-trade guard documentation.
- **DB requirements.** Target tables keyed by (symbol, horizon, method,
  target date) with range + input references.
- **API requirements.** Internal interface; exposure via Phase 28.
- **Agent requirements.** None (targets are computed, not agent-issued).
- **Free resources.** Python stdlib, SQLite, verified stored analysis.
- **Test cases.** Range test (target is a range with stated uncertainty);
  no-trade-guard test (no order/broker code path exists); history test
  (past targets immutable); missing-input test.
- **Acceptance criteria.** Every target carries method + inputs + horizon +
  range + limitations; no target is presented as guaranteed or as an
  instruction to trade; no trade-execution path exists.
- **Known risks.** Targets misread as guarantees (mitigated by on-screen
  range + limitation text); forecast error compounding into target ranges.
- **Completion conditions.** Targets computed for the covered universe
  with coverage report; Phases 20–22, 28 may consume them as information only.

## Phase 20 — Backtesting

- **Objectives.** Honest backtests of screens, rules, and forecasts over
  historical EOD data with survivorship, look-ahead, and cost/slippage
  limitations stated; EOD only; backtest results never presented as future guarantees.
- **Tasks/subtasks.** 20.1 Define backtest rules (entry/exit logic as
  analysis rules, not orders). 20.2 Enforce no look-ahead (only data
  available at the simulated date). 20.3 Handle survivorship explicitly
  (universe at each date, delisted handling documented). 20.4 State
  cost/slippage limitations (no invented cost figure; state what is and
  is not modelled). 20.5 Publish backtest reports with limitations.
- **Dependencies.** Phases 06, 12, 17, 18, 19.
- **Inputs.** Historical EOD data, technicals, forecasts, targets,
  registry history.
- **Outputs.** Backtest engine + backtest reports + limitations report.
- **Required files.** Backtest engine, rule definitions, report generator,
  limitations documentation.
- **DB requirements.** Backtest run tables (rules, universe, period,
  results) with reproducibility fields.
- **API requirements.** Internal interface; exposure via Phase 28.
- **Agent requirements.** None.
- **Free resources.** Python stdlib, SQLite, historical EOD data.
- **Test cases.** No-look-ahead test (future data cannot affect a past
  simulated decision); reproducibility test (same rules + data → same
  result); survivorship test on fixtures; limitation-text test.
- **Acceptance criteria.** Every backtest report states universe, period,
  rules, and limitations; no look-ahead; no result presented as a future guarantee.
- **Known risks.** Survivorship bias if delisted symbols are mishandled;
  intraday effects invisible in EOD backtests (stated as a limitation).
- **Completion conditions.** Backtests run + reported for the covered
  rules/forecasts; limitations report published; Phases 22, 24 may cite them.

---

## Phase 21 — Risk management

- **Objectives.** Risk measurement and reporting (volatility, drawdown,
  concentration, scenario views over validated history) as analysis and
  disclosure — not as a trading control. No position is opened, closed,
  or sized into a live order by this system.
- **Tasks/subtasks.** 21.1 Define risk measures and their windows/formulas
  (documented by the implementing team). 21.2 Compute risk views for
  symbols, sectors, and user-entered (manual) portfolios (Phase 23 data
  model may be referenced, but this phase does not execute portfolio changes).
  21.3 Scenario views: documented historical scenarios, labelled as
  historical, not predictions. 21.4 Publish risk + limitation text with
  every risk view.
- **Dependencies.** Phases 06, 12, 13, 17.
- **Inputs.** Validated EOD history, technicals, sector context, forecasts (optional).
- **Outputs.** Risk measures store + risk documentation.
- **Required files.** Risk measure definitions, computation modules,
  scenario definitions, risk documentation.
- **DB requirements.** Risk tables keyed by (entity, date, measure) with
  window + input references.
- **API requirements.** Internal interface; exposure via Phase 28.
- **Agent requirements.** None.
- **Free resources.** Python stdlib, SQLite, validated history.
- **Test cases.** Hand-computed fixture per measure; scenario test
  (historical scenario labelled as historical); no-order-path test
  (no code path from a risk view to an order).
- **Acceptance criteria.** Every measure matches a hand-computed fixture;
  every risk view carries method + window + limitations; no trading
  control path exists.
- **Known risks.** Risk measures misread as safety guarantees; short
  histories understating risk (stated per entity with history length).
- **Completion conditions.** Risk views computed for the covered universe
  with coverage report; Phases 22, 23, 28 may consume them as disclosure.

## Phase 22 — Investment recommendation engine

- **Objectives.** Transparent recommendation records combining analysis,
  scores, valuations, forecasts, targets, backtests, and risk views, with
  inputs, reasoning, uncertainty, and limitations shown.
  **Recommendations are information only — the system must NOT execute
  real trades, and no recommendation is a guaranteed outcome.**
- **Tasks/subtasks.** 22.1 Define the recommendation model (inputs, rules/
  weights, reasoning template, confidence/uncertainty fields). 22.2 Compute
  recommendations over verified stored analysis only. 22.3 Attach full
  reasoning trace: every input, its source, and its weight/rule. 22.4 Show
  uncertainty + limitations + backtest context with every recommendation.
  22.5 Explicit no-trade guard: no code path from a recommendation to an
  order, broker, or external action. 22.6 Recommendation history (past
  recommendations immutable).
- **Dependencies.** Phases 11, 12, 13, 15, 16, 17, 18, 19, 20, 21.
  (Phases 08/09/10/14 inputs only if those phases verified a source.)
- **Inputs.** Fundamentals, technicals, sector intelligence, health scores,
  valuations, forecasts, AI outputs, targets, backtests, risk views.
- **Outputs.** Recommendation store + recommendation model documentation.
- **Required files.** Recommendation model, computation modules, reasoning
  template, history handling, no-trade guard documentation.
- **DB requirements.** Recommendation tables keyed by (symbol, date,
  model version) with input + reasoning references.
- **API requirements.** Internal interface; exposure via Phase 28.
- **Agent requirements.** None in this phase (agents explain
  recommendations in Phase 25+; they do not issue them opaquely).
- **Free resources.** Python stdlib, SQLite, verified stored analysis.
- **Test cases.** Reasoning-trace test (every recommendation lists its
  inputs); no-trade-guard test; history-immutability test; missing-input
  test (recommendation withheld/flagged, not invented).
- **Acceptance criteria.** Every recommendation carries inputs + reasoning +
  uncertainty + limitations + backtest context; no recommendation is
  presented as guaranteed or as an instruction to trade; no trade path exists.
- **Known risks.** Recommendations misread as advice/guarantees (mitigated
  by on-screen reasoning + limitation text); input gaps silently narrowing
  the recommendation set (mitigated by coverage reporting).
- **Completion conditions.** Recommendations computed for the covered
  universe with coverage report; Phases 23, 24, 28 may consume them as
  information only.

## Phase 23 — Portfolio optimization

- **Objectives.** Portfolio analysis and optimisation suggestions over
  user-entered (manual) holdings and validated market data, as analysis
  only. No live portfolio is managed, rebalanced by order, or connected
  to a broker; suggested allocations are probabilistic analysis, not
  instructions to trade.
- **Tasks/subtasks.** 23.1 Define the manual-holdings model (user-entered
  holdings, clearly labelled as user-entered, never as broker-verified).
  23.2 Compute portfolio views: allocation, concentration, risk (from
  Phase 21), historical performance over validated EOD data. 23.3 Compute
  optimisation suggestions with method, constraints, and uncertainty stated.
  23.4 Show limitations + no-trade text with every suggestion. 23.5 No
  code path from a suggestion to an order or broker.
- **Dependencies.** Phases 04, 06, 12, 21, 22.
- **Inputs.** Registry, validated EOD data, risk views, recommendations
  (as analysis inputs, not instructions).
- **Outputs.** Manual-portfolio store + portfolio views + optimisation
  suggestions with method documentation.
- **Required files.** Holdings model, portfolio computation modules,
  optimisation modules, suggestion documentation, no-trade guard note.
- **DB requirements.** Holdings tables (user-entered flag), portfolio
  view/suggestion tables with method + input references.
- **API requirements.** Internal interface; exposure via Phase 28.
- **Agent requirements.** None.
- **Free resources.** Python stdlib, SQLite, validated market data.
- **Test cases.** User-entered labelling test; allocation hand-computed
  fixture; optimisation constraint test; no-trade-guard test;
  missing-history test.
- **Acceptance criteria.** Holdings are labelled user-entered; every
  suggestion carries method + constraints + uncertainty + limitations;
  no suggestion is presented as an instruction to trade; no broker path exists.
- **Known risks.** Manual holdings going stale (user must update; system
  shows last-updated date); optimisation suggestions misread as instructions.
- **Completion conditions.** Portfolio views + suggestions working on
  manual holdings with coverage/limitation notes; Phase 28 may display them.

## Phase 24 — Independent audit

- **Objectives.** Independent audit of data, calculations, provenance, and
  outputs against the acceptance matrix — by a party other than the
  implementing team — reporting pass / fail / UNVERIFIED per item, with
  findings corrected before rollout.
- **Tasks/subtasks.** 24.1 Re-run acceptance checks from
  `TASK_ACCEPTANCE_MATRIX.md` independently (not the implementers marking
  their own work). 24.2 Audit data: provenance completeness, quarantine
  handling, coverage vs claims. 24.3 Audit calculations: sample
  hand-recomputation of fundamentals, technicals, scores, valuations,
  forecasts, targets, recommendations. 24.4 Audit disclosures: uncertainty,
  limitations, source labels, no-trade text present where required.
  24.5 Audit PKR 0 compliance: no paid service in use or proposed as a
  solution. 24.6 Issue findings + required corrections; verify corrections.
- **Dependencies.** Phases 02–23 (all built layers audited).
- **Inputs.** All prior phase outputs, acceptance matrix, provenance +
  quality reports, backtest + limitations reports.
- **Outputs.** Audit report (pass/fail/UNVERIFIED per item), findings
  register, correction-verification notes.
- **Required files.** Audit report, findings register, audit checklists,
  correction-verification notes.
- **DB requirements.** Read-only audit queries; audit findings store
  (or document) linked to phase/item.
- **API requirements.** None new; audit uses existing internal interfaces.
- **Agent requirements.** None (audit is human/independent process;
  agents do not audit themselves).
- **Free resources.** Local tooling, Python stdlib, existing test suites.
- **Test cases.** Audit checklist execution itself is the test: every
  matrix item gets a recorded verdict with evidence; sample
  hand-recomputation cases; disclosure-presence checks.
- **Acceptance criteria.** Every matrix item has an independent verdict
  with evidence; all "fail" findings have corrections verified or are
  carried as open items to Phase 30; no implementer self-marks a pass.
- **Known risks.** Audit scope creep; findings that require rework in
  gated phases (08/09/10/14) where the fix is a documented limitation,
  not invented data.
- **Completion conditions.** Audit report issued; corrections verified or
  open items registered; Phases 25–30 may proceed only on audited layers.

## Phase 25 — Multi-agent orchestration

- **Objectives.** Orchestrated agents (researcher, validator, analyst,
  reporter roles) with explicit task boundaries, read-only defaults,
  human-approval gates for any outward action, and complete execution logs.
  Agents never trade, post, or send on their own authority.
- **Tasks/subtasks.** 25.1 Define agent roles, permitted inputs, permitted
  outputs, and forbidden actions per role. 25.2 Implement orchestration:
  task dispatch, sequencing, timeout/failure handling, execution logging.
  25.3 Read-only defaults: agents read stored verified data; any write or
  outward action requires an explicit approval gate. 25.4 Validator agent:
  checks citations, uncertainty text, and provenance before an output is
  shown. 25.5 Execution log: every agent run recorded (task, inputs,
  outputs, approvals, failures).
- **Dependencies.** Phases 05, 11–23 (layers agents consume), 24 (audited layers only).
- **Inputs.** Audited analysis layers, stored verified data, AI layer (Phase 18).
- **Outputs.** Agent registry, orchestration engine, execution logs,
  approval-gate definitions.
- **Required files.** Agent role definitions, orchestration modules,
  approval-gate handling, execution-log store definitions, agent documentation.
- **DB requirements.** Agent run log tables (task, inputs, outputs,
  approvals, failures); agent output tables with citation references.
- **API requirements.** Internal orchestration interface; no outward
  (posting/sending/trading) API in this phase.
- **Agent requirements.** This phase IS the agent phase: roles, boundaries,
  gates, logs as above. No agent gains an outward action without a gate.
- **Free resources.** Python stdlib, SQLite, free/local AI options only
  (PKR 0 rule; no paid AI service).
- **Test cases.** Role-boundary test (agent cannot exceed its role);
  approval-gate test (outward action without approval is blocked);
  read-only test (default agent run writes nothing); execution-log test
  (every run logged); citation-check test (validator flags uncited claims).
- **Acceptance criteria.** Every agent run is logged; no agent can trade,
  post, or send without a recorded human approval; validator flags uncited
  or guarantee-worded outputs.
- **Known risks.** Agent autonomy drifting beyond its role (mitigated by
  gates + logs + audit); free/local AI limits (documented, not solved by purchase).
- **Completion conditions.** Orchestration test-passing on gate/log cases;
  Phase 26 may use orchestrated agents on audited data.

## Phase 26 — Autonomous company research

- **Objectives.** Scheduled, autonomous company-research runs assembling a
  research dossier per company from verified stored data only, every claim
  cited to a stored figure, every gap labelled. Autonomy means scheduled
  assembly and reporting — not autonomous trading, posting, or external action.
- **Tasks/subtasks.** 26.1 Define the dossier template (registry, market,
  fundamentals, technicals, sector, health, valuation, forecast, target,
  recommendation, risk — each section with source + as-of + limitations).
  26.2 Implement dossier assembly via Phase 25 orchestration (researcher
  → validator → reporter). 26.3 Gap handling: missing sections labelled
  missing with reason (e.g. statements unverified), never filled by invention.
  26.4 Schedule dossiers (see Phase 27) and store dossier history (past
  dossiers immutable). 26.5 Human-review flag before any dossier is shown
  as a finished report.
- **Dependencies.** Phases 04, 06–23, 24, 25.
- **Inputs.** Audited analysis layers; registry; stored verified data.
- **Outputs.** Research dossiers + dossier history + gap reports.
- **Required files.** Dossier template, assembly modules, gap-handling
  rules, dossier history handling, review-flag handling.
- **DB requirements.** Dossier tables (company, date, sections, citations,
  gaps) with history/versioning.
- **API requirements.** Internal interface; exposure via Phase 28.
- **Agent requirements.** Uses Phase 25 orchestration; researcher/
  validator/reporter roles; read-only data access; review gate before
  finished-report status.
- **Free resources.** Python stdlib, SQLite, free/local AI options only.
- **Test cases.** Citation test (every dossier claim traces to a stored
  figure); gap test (missing section labelled, not invented); history test
  (past dossiers immutable); review-flag test.
- **Acceptance criteria.** Every dossier claim is cited; every gap is
  labelled with reason; no dossier is marked finished without review flag
  clearance; no dossier triggers trading, posting, or sending.
- **Known risks.** Dossier staleness between runs (mitigated by as-of
  dates + freshness flags); statement/news gaps (Phases 08/14) leaving
  thin dossiers for some companies (labelled, not padded).
- **Completion conditions.** Dossiers assembled for the covered universe
  with gap report; Phase 27 schedules them; Phase 28 may display them.

## Phase 27 — Scheduling and monitoring

- **Objectives.** Scheduling (daily refresh, research runs, reports) and
  monitoring (freshness, failures, health) on free/local tooling, so a
  stale feed or failed job is visible before any user acts on old data,
  with alerting limited to channels the user has explicitly approved.
- **Tasks/subtasks.** 27.1 Define schedules: daily refresh (Phase 07),
  dossier runs (Phase 26), reports, quality checks — with non-overlapping
  windows and a lock so jobs never run concurrently on the same data.
  27.2 Implement local scheduling (documented manual / OS-scheduler
  procedure + schedule definitions for deployment). 27.3 Monitoring:
  freshness monitors, failure logs, health checks for collectors, DB, and
  dashboard data. 27.4 Alerting: user-approved channels only, rate limits,
  quiet hours, full alert history. 27.5 Performance measurement baseline
  for collectors/engines (feeds Phase 29 hardening decisions).
- **Dependencies.** Phases 05, 06, 07, 25, 26.
- **Inputs.** Collector/refresh jobs, dossier jobs, backend logging,
  freshness indicators.
- **Outputs.** Schedule definitions, monitoring reports, health checks,
  alert history.
- **Required files.** Schedule definitions, monitoring modules, health
  checks, alerting rules + history, operations runbook section.
- **DB requirements.** Job-run log tables, freshness-monitoring state,
  alert-history tables.
- **API requirements.** Internal health/status interface; no outward
  sending except user-approved alert channels.
- **Agent requirements.** Agents may be scheduled (Phase 26 runs) but
  remain under Phase 25 gates; scheduling does not grant new agent powers.
- **Free resources.** Local OS scheduler, Python stdlib, SQLite, local logs.
  No paid monitoring service.
- **Test cases.** Schedule-lock test (concurrent same-data jobs blocked);
  freshness-alert test (stale feed triggers a visible flag); failure-log
  test (failed job named with reason); alert-channel test (unapproved
  channel never used).
- **Acceptance criteria.** Every scheduled job is logged with outcome;
  stale/failed state is visible before downstream use; alerts go only to
  approved channels with history.
- **Known risks.** Scheduler differences across machines (documented per
  OS, not assumed); alert fatigue (mitigated by rate limits + quiet hours).
- **Completion conditions.** Schedules + monitoring verified on local
  runs; Phase 28 displays freshness/health; Phase 30 rollout uses these monitors.

## Phase 28 — Frontend and dashboard integration

- **Objectives.** Frontend and dashboard integrating registry, market,
  fundamental, technical, sector, forecast, target, recommendation, and
  portfolio views, with source, as-of date, uncertainty, and limitations
  visible on the same screen as any figure or recommendation.
- **Tasks/subtasks.** 28.1 Build views: market overview, company detail,
  fundamentals, technicals, sector, health, valuation, forecast, target,
  recommendation, portfolio, dossier. 28.2 Every figure: source + as-of
  date shown; every forecast/target/recommendation: uncertainty +
  limitations + no-trade text on the same screen. 28.3 Freshness/health
  banners from Phase 27 (stale data visibly flagged). 28.4 Saved views /
  user preferences stored locally (no paid service). 28.5 Accessibility +
  usability checks on the built views (not a separate design phase).
- **Dependencies.** Phases 04, 06–23, 26, 27.
- **Inputs.** All analysis layers, dossiers, freshness/health state,
  recommendation + portfolio models.
- **Outputs.** Dashboard application + view documentation + user guide
  inputs (full guide is not this phase; see Phase 30 handover).
- **Required files.** Frontend modules/pages/components, view
  documentation, freshness-banner handling, user-preference store.
- **DB requirements.** User-preference store (local); dashboard reads
  existing analysis tables (no new analytic tables except preferences).
- **API requirements.** Internal data-access interface consumed by views
  (the dashboard does not reach past the backend foundation's interfaces
  into raw tables where an interface exists).
- **Agent requirements.** Agent outputs (Phase 25/26) displayed with
  review flags + citations; no agent action is triggered from the
  dashboard without an approval gate.
- **Free resources.** Free frontend tooling available locally (Node
  v24.22.1 baseline; free-licence libraries only, no paid component).
- **Test cases.** Label-presence test (sample each view: source + as-of
  present); uncertainty-presence test (forecast/target/recommendation
  views carry uncertainty + limitations + no-trade text); stale-banner
  test; preference-persistence test.
- **Acceptance criteria.** No view shows a figure without source + as-of;
  no forecast/target/recommendation view lacks uncertainty + limitations
  + no-trade text; stale data is banner-flagged; preferences persist locally.
- **Known risks.** Disclosure text crowded out by design (mitigated by
  label-presence tests, not by trusting layout review alone); view
  performance on full-universe tables (measured in Phase 29).
- **Completion conditions.** All views built + label/uncertainty tests
  passing; Phase 29 hardens the built dashboard; Phase 30 verifies it.

## Phase 29 — Security and production hardening

- **Objectives.** Harden the system for production: input validation,
  credential handling (no credential in code or chat), access control,
  licence/attribution compliance, backup/restore, and a security review —
  on the PKR 0 constraint, using free/local controls only.
- **Tasks/subtasks.** 29.1 Input validation + output encoding on all
  user-facing inputs and dashboard/API boundaries. 29.2 Credential handling
  audit: no secret in code, config, logs, or chat; local secret handling
  documented (no hosted identity provider invented). 29.3 Access control:
  local-first roles (viewer/analyst/admin as defined by the implementing
  team) enforced on admin and write paths. 29.4 Licence/attribution
  register: every source's licence + attribution requirement checked and
  recorded; non-compliant uses removed. 29.5 Backup/restore + rollback
  tested end-to-end (from Phase 03 procedure, now on the full system).
  29.6 Performance re-measurement (from Phase 27 baseline): caching /
  pagination only where measurement proves a need. 29.7 Security review
  checklist signed off with findings or open items.
- **Dependencies.** Phases 02, 03, 05, 24, 27, 28.
- **Inputs.** Built system, audit report (Phase 24), licence texts,
  performance baseline (Phase 27).
- **Outputs.** Hardening changes, licence/attribution register, security
  review, tested backup/restore + rollback.
- **Required files.** Security review document, licence/attribution
  register, hardening change notes, backup/restore + rollback runbook.
- **DB requirements.** Role/permission store (local-first), audit log for
  admin/write actions, backup/restore procedures for all tables.
- **API requirements.** Access-control enforcement on internal interfaces
  and dashboard actions.
- **Agent requirements.** Agent gates re-verified under hardening (no new
  agent powers; approval gates still enforced).
- **Free resources.** Local security tooling, Python/Node stdlib and
  free-licence libraries, local backup.
- **Test cases.** Validation test (malformed input rejected, not stored);
  secret-scan test (no secret pattern in code/config/logs fixtures);
  role test (viewer cannot perform admin writes); licence-register test
  (every source has a recorded licence entry); backup/restore + rollback test.
- **Acceptance criteria.** Security review complete with findings resolved
  or registered as open items; no secret in code/config/logs; licence
  register complete; backup/restore + rollback tested.
- **Known risks.** A source licence forbidding a planned use (fix by
  removing that use, not by ignoring the licence); local-only access
  control limits if online deployment is later chosen (see Phase 30 caveat).
- **Completion conditions.** Security review signed off (or open items
  registered); hardening changes test-passing; Phase 30 may roll out.

## Phase 30 — Full PSX rollout and final verification

- **Objectives.** Roll out across the full PSX universe covered by
  verified data, run final verification (data completeness, calculation
  audit, UI checks, limitation disclosures), publish the handover pack and
  open-items register (including every UNVERIFIED item still open), and
  freeze the release. Any zero-cost online deployment is used only where
  a legitimate free service is verified, with the permanent-free-hosting caveat.
- **Tasks/subtasks.** 30.1 Full-universe rollout: collectors, analysis,
  dossiers, dashboard verified across the covered universe (not just
  fixtures). 30.2 Final verification: completeness reports, sample
  hand-recomputation, UI label/uncertainty checks, freshness/health checks.
  30.3 Handover pack: runbooks, known issues, cost/resource actuals vs
  Phase 01 estimates, open UNVERIFIED items. 30.4 Online deployment
  decision (conditional): only a verified legitimate free service, with
  the caveat that free terms can change/withdraw and the local system
  remains the fallback; if no such service covers a component, that
  component stays local and the limitation is documented. 30.5 Release
  freeze + Phase-2 readiness note (Phase 2 listed, not started).
- **Dependencies.** Phases 24–29 (audit, agents, dossiers, scheduling,
  dashboard, hardening).
- **Inputs.** Hardened system, audit report, handover inputs, cost/resource actuals.
- **Outputs.** Release notes, handover pack, open-items register,
  final verification report, Phase-2 readiness note.
- **Required files.** Release notes, handover pack, open-items register,
  final verification report, deployment decision record (incl. free-hosting caveat).
- **DB requirements.** Full-universe tables verified (completeness +
  integrity checks); backup taken before release freeze.
- **API requirements.** Internal interfaces verified at full-universe scale.
- **Agent requirements.** Agent runs verified under final gates; no agent
  power added at rollout.
- **Free resources.** Local deployment (primary); verified free online
  service ONLY where legitimately available (conditional, see caveat).
- **Test cases.** Full-universe completeness test; final label/uncertainty
  sample checks; backup-before-freeze test; deployment-fallback test
  (system still runs locally if the free online service is unavailable).
- **Acceptance criteria.** Final verification report covers completeness,
  calculations, UI disclosures, and freshness; handover pack + open-items
  register published; no UNVERIFIED item is presented as resolved;
  no paid service is in use; no trade-execution path exists.
- **Known risks.** Free online service terms changing/withdrawn (mitigated
  by local fallback, never by purchase); full-universe gaps (Phases 06–10)
  surfacing at rollout (reported, not hidden).
- **Completion conditions.** Release frozen; handover pack + open-items
  register delivered; final verification report signed off; Phase 2 is
  listed only — this roadmap does not start it.

---

## Cross-phase notes for implementers

- **Gated phases (08, 09, 10, 14) never block the programme.** Their
  completion condition explicitly allows closing with a documented
  limitation. Downstream phases must implement the no-input fallback.
- **No-trade guard is tested, not just stated.** Phases 19, 21, 22, 23,
  25, 26 each carry a no-trade / no-order-path test case; Phase 24 audits
  it; Phase 30 re-verifies it at rollout.
- **PKR 0 is tested.** Phase 24 audits PKR 0 compliance; any phase that
  cannot meet a requirement for free documents the limitation instead of
  proposing a purchase.
- **STOP AFTER PHASE 01.** This breakdown documents Phases 02–30; it does
  not authorise starting them. A separate explicit instruction is required
  for Phase 02.
