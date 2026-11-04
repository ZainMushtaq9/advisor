# PSX Intelligence AI — Agent Registry (Phase 1)

> **Team:** Team 5 — Multi-Agent Architecture
> **Phase:** Phase 1 of 30 — design only. No application code, no Phase 2 work.
> **Companion files:** `AGENT_ARCHITECTURE.md` (ecosystem, responsibility map),
> `AGENT_COMMUNICATION_SPEC.md` (message protocol), `AGENT_PERMISSION_MATRIX.md`
> (permissions). In case of conflict, the permission matrix governs access, the
> communication spec governs messages, and this registry governs what each agent
> may do.
> **REVISED BRIEF (merged 2026-11-04):** Budget **PKR 0 absolute** — Ollama local
> open-weight inference only, no paid AI/LLM APIs or subscriptions. Local hardware,
> electricity, and internet are **external operating expenses** — disclosed, never
> called free. Phase 1 data work is **read-only inspection only — NO full-scale live
> data collection in Phase 1**. The system must **NOT execute real trades initially**
> — no agent has trade-execution permission; recommendations/reports only.
> **STOP AFTER PHASE 1.** Testing strategy is defined, not claimed passed.
> **Date / starting condition:** 2026-11-04 — same verified starting condition as
> `AGENT_ARCHITECTURE.md` §0 (Python 3.12.3, Node v24.22.1; Docker, `psql`,
> `redis-cli` NOT installed; `psx-dps` / `psxdata` as verified there; SECP/SBP/
> PBS/Finance Division/World Bank/IMF/FRED machine-use UNVERIFIED).

## 0. How to read this registry

- **One agent = one responsibility domain.** See the responsibility map in
  `AGENT_ARCHITECTURE.md` §9. If two entries appear to overlap, the map's
  "single owner" column decides; the non-owner reads, it does not reproduce.
- **Every agent that touches numbers** must call a named, versioned deterministic
  Python function and log `function@version` + input refs + outputs. An agent
  whose entry says "No numeric output" must not introduce numbers in prose
  either, except by quoting a logged deterministic output with its reference.
- **Schemas are logical Phase 1 schemas.** Field names below are the contract
  for task messages (see communication spec). Physical field types in Phase 2
  must preserve these names and meanings; renaming a field is a schema-version
  change (communication spec §5).
- **Frequencies are Phase 1 policy defaults** (human-admin changeable), not
  market schedules and not live polling. "Per approved job" means the agent runs
  only when the orchestrator dispatches a task for an approved job — never
  continuously, never on its own initiative.
- **Resource estimates are planning tiers** (Low / Medium), not measured
  benchmarks. No monetary cost is asserted: project budget is PKR 0, no paid API
  approved, and local-inference budgets are policy caps on local compute — see
  architecture §7 and §1A. Wherever an entry says "LLM use", it means Ollama
  local open-weight inference only.
- **Error codes** (`E_*`) are defined in `AGENT_COMMUNICATION_SPEC.md` §6 and
  used identically here.
- **UNVERIFIED** means: the input/source is not approved for machine use in
  Phase 1. The agent's fallback is always **skip with an audit note — never
  invent data**.

### Common fields on every output (all 18 agents)

Every output record carries, in addition to its agent-specific schema below:
`record_id`, `run_id`, `task_id`, `agent_id`, `schema_version`,
`created_at_pkt`, `input_refs[]` (shared-context record ids + versions),
`provenance` (source + method), `function_log[]` (empty only if the agent
produces no numbers — and then it must quote no numbers), `status`
(`DRAFT` until audit, never `RELEASED` by the producing agent), and
`audit_note` (empty, or the reason for any skip / gap / fallback).

---

## Agent 1 — Market Data

- **Purpose:** Retrieve PSX market data through already-verified libraries only,
  stamp it with provenance and PKT freshness, and store it for all downstream
  agents. The single owner of market-data retrieval (R1).
- **Responsibilities:** (a) Retrieve EOD / snapshot data only via the
  `psx-data-collection` scaffold's rules; (b) apply the scaffold's provenance,
  PKT timestamping, stale-data, and conflict rules; (c) record gaps (including
  the `psx-dps` multi-node 404 quirk and the ~496 trading vs ~1029 listed gap)
  as data, never by backfilling; (d) never claim intraday history from
  `psxdata` (it has none — daily OHLCV + live snapshots only).
- **Input schema:** `{ job_id, symbols[] (optional filter; empty = approved universe from Agent 2), date_range {from_pkt, to_pkt}, source_preference [psx-dps | psxdata], freshness_window (from job approval) }`
- **Output schema:** `{ market_data_batch_id, as_of_pkt, source, symbols[] { symbol, sector (as returned), ohlcv {open, high, low, close, volume} (where the source provides it), tick_snapshot (only where the source provides it), retrieval_status [OK | PARTIAL | FAILED], gap_note }, staleness [FRESH | STALE | UNKNOWN], conflict_note }`
- **Required tools:** Python stdlib; `psx-dps` and `psxdata` libraries via the
  `psx-data-collection` scaffold only (no direct invented endpoint, no new
  scraper, no broker feed). Shared-context write to its own output group only.
- **Data dependencies:** `psx-dps`, `psxdata`, the `psx-data-collection`
  scaffold. No other external source. No official PSX API exists to call.
- **Execution frequency:** Per approved job; at most once per job's approved
  refresh (later-phase default: daily at most). No live polling, no continuous stream.
  **Phase 1 qualifier:** in Phase 1 itself Agent 1 does NOT run full-scale live
  collection — its behaviour above is specified for later phases, and Phase 1
  activity is read-only inspection only (architecture §1A stage 4).
- **Failure handling:** Partial retrieval → `PARTIAL` with per-symbol gap notes,
  downstream agents decide per the job's stale/partial rule. Total retrieval
  failure → task `failed`, no fabricated batch. Stale data beyond the freshness
  window → flagged `STALE`, never relabelled fresh.
- **Retry strategy:** Retryable transient source errors (`E_TRANSIENT_SOURCE`,
  `E_TIMEOUT`): up to 2 retries, orchestrator-enforced backoff between attempts
  (policy: wait, then retry once; a second failure escalates — exact backoff
  interval is a human-admin policy value, not asserted here as a measured optimum).
  Non-retryable: `E_UNVERIFIED_SOURCE`, `E_SCHEMA`, `E_PERMISSION` → dead-letter,
  no retry.
- **Audit requirements:** Every batch logs source, retrieval method, `as_of_pkt`,
  symbol coverage vs the approved universe, and gap/conflict notes.
- **Estimated resource requirements:** CPU Low, memory Low, network: the only
  Phase 1 agent with approved external access (via verified libraries only).
  LLM use: None — retrieval and stamping are deterministic.
- **Expected output:** One versioned market-data batch per task, with explicit
  coverage and gaps, ready for Agents 3, 5, 6, 7, 10, 11 to read by reference.

## Agent 2 — Company Discovery

- **Purpose:** Define and maintain the company universe: which companies exist
  in scope, their identity, and their sector membership. Single owner of the
  universe (R2).
- **Responsibilities:** (a) Build the universe from Market Data outputs and
  operator-supplied, provenance-stamped company lists (if any); (b) assign each
  company to exactly one of the 38 sectors as returned/approved (no invented
  sector); (c) deduplicate by symbol + company identity (a name alone is not a
  key); (d) record additions/removals as new versions, never by editing history.
- **Input schema:** `{ job_id, market_data_batch_ref, operator_company_list_ref (optional), sector_list_ref }`
- **Output schema:** `{ universe_version, companies[] { symbol, company_name (as sourced), sector, status [ACTIVE | INACTIVE | UNVERIFIED], provenance, first_seen_pkt, last_seen_pkt }, universe_note (coverage vs ~1029 listed / ~496 trading, as observed — not asserted as a live count unless the batch proves it) }`
- **Required tools:** Python stdlib; shared-context read (Market Data group) and
  write (own group only). No external network.
- **Data dependencies:** Agent 1 outputs; operator-supplied lists if provided.
  No unverified external company database.
- **Execution frequency:** Per approved job, after each Market Data refresh that
  the job names; otherwise on human-approved universe review only.
- **Failure handling:** Symbol/company ambiguity → status `UNVERIFIED`, excluded
  from analysis until resolved by the human admin or a verified source; never
  guessed. Missing sector → company held as `UNVERIFIED`, not assigned a
  plausible sector.
- **Retry strategy:** Retryable: `E_TIMEOUT` (up to 2 retries). Non-retryable:
  `E_SCHEMA`, `E_PERMISSION` → dead-letter.
- **Audit requirements:** Every universe version logs its input batch ref, its
  deduplication decisions, and every `UNVERIFIED` holding with its reason.
- **Estimated resource requirements:** CPU Low, memory Low, LLM use: None.
- **Expected output:** One versioned universe per task, which every downstream
  agent must reference (no agent invents its own universe).

## Agent 3 — Historical Research

- **Purpose:** Research patterns and context over already-stored history.
  Single owner of historical-series research (R3). It never retrieves fresh
  market data — that is Agent 1's job.
- **Responsibilities:** (a) Assemble stored series for named symbols/periods
  from shared-context records; (b) summarise history in words and in
  deterministic descriptive statistics (via logged functions — e.g. counts,
  ranges, and other descriptive measures the function catalogue defines);
  (c) flag data gaps, suspensions in the stored record, and regime changes that
  are visible in the stored data, without explaining them by invented events.
- **Input schema:** `{ job_id, symbol, universe_ref, market_data_batch_refs[], period {from_pkt, to_pkt}, research_questions[] }`
- **Output schema:** `{ historical_brief_id, symbol, period_covered, data_completeness, descriptive_stats_ref (function log), findings[] { observation, evidence_refs[], confidence_qualifier }, gaps[] }`
- **Required tools:** Python stdlib; deterministic descriptive functions (via
  Agent 11's catalogue where statistical); shared-context read/write (own group).
  No external network.
- **Data dependencies:** Agents 1 and 2 outputs only.
- **Execution frequency:** Per approved company-analysis job.
- **Failure handling:** Incomplete stored history → brief states its coverage
  explicitly and narrows its findings; it never extrapolates over a gap as if
  the gap were data.
- **Retry strategy:** Retryable: `E_TIMEOUT` (up to 2 retries). Non-retryable:
  `E_SCHEMA`, `E_MISSING_INPUT` (if an input ref does not exist — re-dispatch
  with a valid ref is a new task, not a retry) → dead-letter.
- **Audit requirements:** Every finding cites evidence refs; every descriptive
  number traces to a function log.
- **Estimated resource requirements:** CPU Low–Medium, memory Low, LLM use:
  Low (prose brief over deterministic stats only).
- **Expected output:** One historical brief per symbol per job, used by Agents
  5, 6, 10, 11, 13 as context — never as a substitute for their own outputs.

## Agent 4 — Financial Statement

- **Purpose:** Extract and structure financial-statement data from
  operator-supplied, provenance-stamped documents only. Single owner of
  statement extraction/structuring (R4).
- **Responsibilities:** (a) Parse supplied statements into a structured,
  versioned record (period, line items as stated in the document, units as
  stated); (b) preserve the document's own wording/units — never convert,
  annualise, or restate a figure without a logged deterministic function and an
  explicit note; (c) flag missing periods, restatements visible in the document,
  and unreadable sections as gaps.
- **Input schema:** `{ job_id, symbol, universe_ref, document_refs[] (operator-supplied, provenance-stamped), statement_period }`
- **Output schema:** `{ statement_record_id, symbol, period, document_refs[], line_items[] { label_as_stated, value_as_stated, unit_as_stated, function_log_ref (only if transformed) }, gaps[], extraction_note }`
- **Required tools:** Python stdlib document reading as applicable to the
  supplied format; shared-context read/write (own group). No external network.
- **Data dependencies:** Operator-supplied documents only. **UNVERIFIED:**
  SECP machine-use as a filing source — Agent 4 must NOT fetch filings from
  SECP in Phase 1. If no supplied document exists for a symbol/period, the
  agent outputs a gap record (skip with audit note), never a reconstructed
  statement.
- **Execution frequency:** Per approved company-analysis job, when documents
  are supplied for that job.
- **Failure handling:** Unreadable/missing document → gap record, task
  `completed` with gaps (not `failed`), so downstream agents see the absence
  explicitly. Ambiguous line item → preserved as stated with an ambiguity note,
  never resolved by guess.
- **Retry strategy:** Retryable: `E_TIMEOUT` (up to 2 retries). Non-retryable:
  `E_UNVERIFIED_SOURCE` (an instruction to fetch from an unverified source is
  refused, not retried), `E_SCHEMA` → dead-letter.
- **Audit requirements:** Every line item traces to a document ref + location
  within it (page/section as supplied); every transformation traces to a
  function log.
- **Estimated resource requirements:** CPU Low, memory Low, LLM use: Low
  (structuring only; numbers copied, never computed in prose).
- **Expected output:** One structured statement record per symbol/period, or an
  explicit gap record — never a partially invented statement.

## Agent 5 — Fundamental Analysis

- **Purpose:** Assess a company's fundamental quality from its statements and
  history. Single owner of fundamental assessment (R5). It does not extract
  statements (Agent 4) and does not run valuation models (Agent 10).
- **Responsibilities:** (a) Read Agents 3 and 4 outputs by reference; (b) apply
  deterministic fundamental functions (ratios/quality measures defined in the
  catalogue) and log every call; (c) write a fundamental assessment in words
  that quotes only logged numbers, with strengths, weaknesses, and open
  questions stated as questions (not as assumed answers).
- **Input schema:** `{ job_id, symbol, universe_ref, statement_record_refs[], historical_brief_ref }`
- **Output schema:** `{ fundamental_assessment_id, symbol, period_covered, ratio_refs[] (function logs), assessment { strengths[], weaknesses[], open_questions[] }, data_limitations[] }`
- **Required tools:** Python stdlib; deterministic fundamental functions;
  shared-context read/write (own group). No external network.
- **Data dependencies:** Agents 3, 4 (and 1/2 by reference). If statement data
  is a gap record, the assessment says so and narrows its scope — it does not
  substitute market prices for fundamentals.
- **Execution frequency:** Per approved company-analysis job.
- **Failure handling:** Missing statement data → narrowed assessment with
  `data_limitations`, not a failure of the whole job unless the job required
  statements (then the orchestrator, on human instruction, decides whether the
  job proceeds). Invented-number detection by the agent itself → self-flag and
  stop; the draft is not delivered.
- **Retry strategy:** Retryable: `E_TIMEOUT`, `E_FUNCTION_ERROR` (function
  failed on valid inputs — e.g. division by zero on a stated zero — up to 2
  retries after input check; if the input itself is the cause, the output
  records the limitation instead of retrying forever). Non-retryable:
  `E_SCHEMA`, `E_INVENTED_NUMBER` → dead-letter + audit flag.
- **Audit requirements:** Every ratio/number traces to a function log; every
  judgement cites an assessment input ref.
- **Estimated resource requirements:** CPU Low, memory Low, LLM use: Low–Medium
  (assessment prose over logged ratios).
- **Expected output:** One fundamental assessment per symbol per job, consumed
  by Agents 10, 13, 14.

## Agent 6 — Technical Analysis

- **Purpose:** Compute technical indicators and chart-based signals from stored
  market data, using deterministic functions only. Single owner of technical
  signals (R6).
- **Responsibilities:** (a) Read Agent 1 batches by reference; (b) compute
  indicators only via catalogue functions (no hand-computed indicator in
  prose); (c) state each signal's lookback window, data completeness, and
  limitation (e.g. a signal over a gap is flagged, not smoothed over silently).
- **Input schema:** `{ job_id, symbol, market_data_batch_refs[], indicator_set[] (named catalogue functions only), lookback }`
- **Output schema:** `{ technical_assessment_id, symbol, period_covered, data_completeness, indicators[] { function@version, window, value_ref (function log), signal_reading }, signals_summary, limitations[] }`
- **Required tools:** Python stdlib; deterministic indicator functions;
  shared-context read/write (own group). No external network. No intraday
  indicators may be claimed from `psxdata` (no historical intraday archive).
- **Data dependencies:** Agent 1 outputs; Agent 2 universe for symbol validity.
- **Execution frequency:** Per approved company-analysis job; at most per
  Market Data refresh named by the job.
- **Failure handling:** Insufficient history for a window → that indicator is
  omitted with a limitation note, not computed over a shorter window silently.
  A shorter window, if used, is a different, explicitly named computation.
- **Retry strategy:** Retryable: `E_TIMEOUT`, `E_FUNCTION_ERROR` (up to 2
  retries after input check). Non-retryable: `E_SCHEMA`,
  `E_INVENTED_NUMBER` → dead-letter + audit flag.
- **Audit requirements:** Every indicator value traces to a function log with
  its window and input batch refs.
- **Estimated resource requirements:** CPU Low–Medium, memory Low, LLM use: Low
  (signal readings over logged indicators).
- **Expected output:** One technical assessment per symbol per job, consumed by
  Agents 11 (as context, not as forecast input unless the job names it), 13, 14.


## Agent 7 — Sector Analysis

- **Purpose:** Aggregate and compare sectors within the universe Agent 2 defines.
  Single owner of sector aggregation/comparison (R7). It never adds, removes,
  or reassigns a company — that is Agent 2's job.
- **Responsibilities:** (a) Read universe + Market Data batches by reference;
  (b) compute sector aggregates only via deterministic functions (counts,
  averages, and other catalogue-defined aggregates, with the exact function
  logged); (c) compare sectors on the same window and same completeness basis,
  and state where a sector's coverage is partial so a comparison is not read as
  complete.
- **Input schema:** `{ job_id, universe_ref, market_data_batch_refs[], sectors[] (subset of the 38, as approved), window }`
- **Output schema:** `{ sector_assessment_id, sectors[] { sector, company_count_in_universe, companies_with_data, aggregate_refs[] (function logs), reading }, comparisons[], coverage_limitations[] }`
- **Required tools:** Python stdlib; deterministic aggregation functions;
  shared-context read/write (own group). No external network.
- **Data dependencies:** Agents 1 and 2 outputs. A sector with no data is
  reported as no-data, never estimated from another sector.
- **Execution frequency:** Per approved job (company-analysis or sector-review job).
- **Failure handling:** Partial sector coverage → aggregate flagged partial with
  its company count shown; the reading must not generalise the partial set to
  the whole sector.
- **Retry strategy:** Retryable: `E_TIMEOUT`, `E_FUNCTION_ERROR` (up to 2
  retries after input check). Non-retryable: `E_SCHEMA`,
  `E_INVENTED_NUMBER` → dead-letter + audit flag.
- **Audit requirements:** Every aggregate traces to a function log + its input
  batch refs + the universe version used.
- **Estimated resource requirements:** CPU Low–Medium, memory Low, LLM use: Low
  (Ollama local open-weight only — see §0 note on inference; no paid LLM API).
- **Expected output:** One sector assessment per job, consumed by Agents 13, 14, 15.

## Agent 8 — News Intelligence

- **Purpose:** Intake, date, and relevance-tag news items — only from
  operator-supplied, provenance-stamped items in Phase 1. Single owner of news
  intake/tagging (R8). It does not create news, and no other agent re-tags news
  as a side effect.
- **Responsibilities:** (a) Accept supplied items with source, publication
  timestamp (PKT), and full text/reference as supplied; (b) tag each item by
  symbol/sector relevance and by type as defined in the job (no invented
  relevance); (c) reject items with missing provenance or an unverifiable date
  — held, not dated by guess; (d) never summarise an item into a claim the item
  does not contain, and never turn a news item into a number (no price, no
  forecast) unless a deterministic function over supplied data produces it and
  logs it separately.
- **Input schema:** `{ job_id, news_items_supplied_refs[] (each with source_as_supplied, published_at_pkt_as_supplied, text_or_ref_as_supplied), universe_ref }`
- **Output schema:** `{ news_brief_id, items[] { item_ref, source_as_supplied, published_at_pkt, symbols_tagged[], sectors_tagged[], relevance_note, status [ACCEPTED | HELD] }, held_reasons[], coverage_note }`
- **Required tools:** Python stdlib; Ollama local open-weight inference only for
  tagging/summarising prose (no paid LLM API, no subscription); shared-context
  read/write (own group). **No external network in Phase 1.**
- **Data dependencies:** Operator-supplied items only. **UNVERIFIED:** every
  news feed / news vendor as a machine source — no specific feed is verified in
  Phase 1, so Agent 8 has no approved external feed to call. Fallback if no
  items are supplied: brief with zero accepted items + audit note (skip, never
  invent).
- **Execution frequency:** Per approved job, only when items are supplied for
  that job; otherwise the agent outputs the zero-item brief.
- **Failure handling:** Item with missing provenance/date → `HELD` with reason,
  excluded from downstream briefs. Duplicate item (same source + timestamp +
  text) → deduplicated by that triple, counted once, with the duplicate noted.
- **Retry strategy:** Retryable: `E_TIMEOUT` (up to 2 retries). Non-retryable:
  `E_UNVERIFIED_SOURCE` (an instruction to fetch from an unverified feed is
  refused, not retried), `E_SCHEMA` → dead-letter.
- **Audit requirements:** Every accepted item cites its supplied ref; every
  held item states its reason; no item is dated, sourced, or worded beyond what
  was supplied.
- **Estimated resource requirements:** CPU Low, memory Low, LLM use: Low
  (Ollama local only).
- **Expected output:** One news brief per job (possibly zero-item), consumed as
  context by Agents 5, 13, 14 — never as a price or forecast input.

## Agent 9 — Macroeconomic

- **Purpose:** Compile macroeconomic context from verified or
  operator-supplied inputs only. Single owner of macro context (R9). It does
  not compile a macro series from an unverified source, and Risk Management
  (13) reads its context rather than recompiling it.
- **Responsibilities:** (a) Accept only inputs that are verified or supplied
  with provenance (source, release date in PKT, value as stated, unit as
  stated); (b) structure them by indicator and period without converting or
  re-basing a figure except via a logged deterministic function with an explicit
  note; (c) state plainly which requested indicators are absent.
- **Input schema:** `{ job_id, macro_inputs_supplied_refs[] (each with source_as_supplied, indicator_as_supplied, period, value_as_stated, unit_as_stated, released_at_pkt_as_supplied) }`
- **Output schema:** `{ macro_brief_id, indicators[] { indicator, period, value_as_stated, unit_as_stated, source_as_supplied, function_log_ref (only if transformed) }, absent_indicators[] { indicator, reason [UNVERIFIED_SOURCE | NOT_SUPPLIED] }, context_reading (words only, quoting stated values with refs) }`
- **Required tools:** Python stdlib; deterministic transformation functions
  only where a transformation is approved; Ollama local open-weight only for
  prose (no paid LLM API). Shared-context read/write (own group).
  **No external network in Phase 1.**
- **Data dependencies:** Operator-supplied inputs only. **UNVERIFIED — all of
  the following as machine sources, each listed separately:** SECP, SBP, PBS,
  Finance Division, World Bank, IMF, FRED. Agent 9 must NOT fetch from any of
  them in Phase 1. Fallback for each: skip with an audit note in
  `absent_indicators[]` — never invent a figure, never substitute a figure
  from a different indicator, period, or country.
- **Execution frequency:** Per approved job, only when macro inputs are
  supplied or a prior verified brief is named; otherwise the agent outputs a
  brief listing all requested indicators as absent with reasons.
- **Failure handling:** Supplied input with missing source/period/unit → held
  as absent with reason, not repaired by guess. Conflicting supplied values
  for the same indicator/period → both preserved with a conflict note; the
  reading states the conflict and does not pick a winner silently.
- **Retry strategy:** Retryable: `E_TIMEOUT` (up to 2 retries). Non-retryable:
  `E_UNVERIFIED_SOURCE`, `E_SCHEMA` → dead-letter.
- **Audit requirements:** Every indicator value traces to a supplied ref;
  every absent indicator states its reason; every transformation traces to a
  function log.
- **Estimated resource requirements:** CPU Low, memory Low, LLM use: Low
  (Ollama local only).
- **Expected output:** One macro brief per job (possibly all-absent), consumed
  as context by Agents 13 and 14 — never as a substitute for company data.

## Agent 10 — Valuation

- **Purpose:** Produce valuation outputs from fundamental, technical, sector,
  and market inputs using deterministic valuation functions only. Single owner
  of valuation outputs (R10). It does not redo fundamental judgement (Agent 5)
  and it does not issue a recommendation (Agent 14).
- **Responsibilities:** (a) Read Agents 1, 5, 6, 7 outputs by reference;
  (b) run only catalogue-named valuation functions, logging every call with its
  inputs (including which statement period and which price batch were used);
  (c) state each output's assumptions as function inputs (not as prose
  adjustments), its sensitivity to stated inputs where the function provides
  it, and its limitations (especially where statement data was a gap record).
- **Input schema:** `{ job_id, symbol, fundamental_assessment_ref, technical_assessment_ref (optional), sector_assessment_ref (optional), market_data_batch_refs[], valuation_functions[] (named catalogue functions only) }`
- **Output schema:** `{ valuation_id, symbol, as_of_pkt, inputs_used { statement_period, price_batch_refs[] }, outputs[] { function@version, inputs_logged, value_ref (function log), assumption_note }, limitations[], uncertainty_note }`
- **Required tools:** Python stdlib; deterministic valuation functions;
  shared-context read/write (own group). No external network. No paid model.
- **Data dependencies:** Agents 1, 5 (and 6, 7 where the job names them). If a
  required input is a gap record, the affected valuation function is omitted
  with a limitation note — never run on a substitute input.
- **Execution frequency:** Per approved company-analysis job.
- **Failure handling:** Function failure on valid inputs (e.g. zero denominator
  from a stated figure) → that output omitted with a limitation note, not
  retried into a different answer. Missing input → omission + note, per above.
- **Retry strategy:** Retryable: `E_TIMEOUT`, `E_FUNCTION_ERROR` (up to 2
  retries after input check). Non-retryable: `E_SCHEMA`,
  `E_INVENTED_NUMBER` → dead-letter + audit flag.
- **Audit requirements:** Every valuation value traces to a function log with
  its full input set; the audit reproduction check (Agent 16) must be able to
  re-run each function and match.
- **Estimated resource requirements:** CPU Low–Medium, memory Low, LLM use:
  None for computation; Low (Ollama local only) for the limitations/uncertainty
  prose that quotes logged values.
- **Expected output:** One valuation record per symbol per job, consumed by
  Agent 14 (and read by Agent 13 for risk context).

## Agent 11 — Statistical Forecasting

- **Purpose:** Produce every forecast number in the system, deterministically,
  and own the statistical/forecasting function catalogue. Single owner of
  forecast numbers and of the catalogue's statistical functions (R11).
- **Responsibilities:** (a) Own catalogue definitions/versions/input schemas
  for statistical and forecasting functions (other agents own their own domain
  functions — see architecture §5 — but no agent redefines a statistical/
  forecasting function); (b) run forecasts only over named input batches and
  windows; (c) output, for each fixed horizon (**1 day, 1 week, 1 month,
  3 months, 6 months, 12 months** — no other horizon may be introduced by an
  agent), a probabilistic result: point/interval/distribution summary as the
  function defines it, plus method, input window, and uncertainty statement —
  all from the function log, never from prose; (d) never word a forecast as a
  guarantee.
- **Input schema:** `{ job_id, symbol, market_data_batch_refs[], historical_brief_ref (optional), technical_assessment_ref (optional, only if the job names it as a forecast input), horizons[] (subset of the six fixed horizons), forecast_functions[] (named catalogue functions only), seed (only if the function requires one, logged) }`
- **Output schema:** `{ forecast_id, symbol, horizons[] { horizon, function@version, input_window, point_or_distribution_ref (function log), interval_or_distribution_summary_ref (function log), method_note, uncertainty_statement }, data_limitations[] }`
- **Required tools:** Python stdlib; deterministic statistical/forecasting
  functions (catalogue owner); shared-context read/write (own group).
  No external network. No paid model, no LLM arithmetic.
- **Data dependencies:** Agents 1, 3 (and 6 where named). A horizon whose input
  window is incomplete is omitted with a limitation note, not forecast over a
  silently shortened window.
- **Execution frequency:** Per approved forecast job; at most per Market Data
  refresh named by the job.
- **Failure handling:** Insufficient data for a horizon/function → that horizon
  omitted with a note; other horizons proceed only if the job allows partial
  output (otherwise the task reports the limitation and the orchestrator, on
  human instruction, decides). Function failure → see retry; repeated failure
  on the same inputs is a limitation, not a reason to substitute another method
  silently.
- **Retry strategy:** Retryable: `E_TIMEOUT`, `E_FUNCTION_ERROR` (up to 2
  retries after input check). Non-retryable: `E_SCHEMA`,
  `E_INVENTED_NUMBER`, `E_UNVERIFIED_SOURCE` → dead-letter + audit flag.
- **Audit requirements:** Full reproduction: Agent 16 must be able to re-run
  every forecast function on the logged inputs (including seed, where used)
  and match the logged outputs exactly (within the function's own stated
  tolerance, if any — a tolerance must be part of the function definition, not
  added at audit time).
- **Estimated resource requirements:** CPU Medium (the heaviest deterministic
  agent, by design — this is where compute belongs, not in LLM prose),
  memory Low–Medium, LLM use: None.
- **Expected output:** One forecast record per symbol per job, which is the
  SOLE source of forecast numbers for Agent 12's synthesis, Agent 14's decision
  input, and any report.

## Agent 12 — AI Forecasting

- **Purpose:** Synthesise and interpret deterministic forecast outputs in prose
  for human readers. Single owner of forecast synthesis prose (R12). This agent
  produces **no numbers of its own**.
- **Responsibilities:** (a) Read Agent 11's forecast record by reference —
  this is its ONLY numeric source; (b) write synthesis prose that explains, in
  words, what the deterministic outputs show across horizons, where they agree
  or diverge, and what evidence limits them; (c) quote numbers ONLY by copying
  them verbatim from Agent 11's function log with their horizon + function ref;
  (d) flag (never hide) uncertainty, missing horizons, and data limitations.
- **Input schema:** `{ job_id, symbol, forecast_ref (Agent 11 output, required), fundamental_assessment_ref (optional, words-only context), sector_assessment_ref (optional, words-only context), news_brief_ref (optional, words-only context), macro_brief_ref (optional, words-only context) }`
- **Output schema:** `{ ai_synthesis_id, symbol, forecast_ref, synthesis_prose, quoted_numbers[] { value_as_quoted, horizon, function@version, forecast_log_ref }, uncertainties_restated[], limitations_restated[], no_new_numbers_attestation }`
- **Required tools:** **Ollama local open-weight inference ONLY** — no paid
  AI/LLM API, no subscription, no API key. Python stdlib for quoting/checking.
  Shared-context read/write (own group). No external network.
- **Data dependencies:** Agent 11 (numeric, sole source); Agents 5, 7, 8, 9 for
  words-only context. If Agent 11's record is absent, incomplete, or unaudited,
  Agent 12 outputs nothing except a holding note stating that fact — it never
  forecasts from market data, news, or its own judgement.
- **Execution frequency:** Per approved forecast job, only after Agent 11's
  record for that job is `completed`.
- **Failure handling:** Any draft containing a number not in Agent 11's log →
  the draft is discarded (self-check before delivery) and the task reports
  `E_INVENTED_NUMBER` handling (see retry). A synthesis that cannot be written
  without a new number is not written.
- **Retry strategy:** Retryable: `E_TIMEOUT` (up to 2 retries, each retry
  re-checking quoted numbers against the log). Non-retryable:
  `E_INVENTED_NUMBER` on a delivered draft → dead-letter + audit flag; the
  agent does not "fix" the number in prose — the fix, if any, is a new Agent 11
  run (new task, new forecast record), after which synthesis may be re-attempted.
- **Audit requirements (mandatory, two-step validation — no release without both):**
  1. **Statistical Forecasting (11) validation:** Agent 11 (or, to avoid
     self-review of its own synthesis, the orchestrator routing Agent 11's
     check) confirms every `quoted_numbers[]` entry matches its forecast log
     exactly (value, horizon, function@version).
  2. **Independent Audit (16) validation:** Agent 16 independently re-checks
     the same quoted numbers against the log, re-runs the underlying functions
     where applicable, and checks the prose for any additional number (including
     numbers in words, percentages, or rounded restatements that differ from the
     log — a rounded restatement is a new number unless the log itself contains
     that rounded form).
  - Either check failing → synthesis `BLOCKED`, not released, with reasons.
  - The attestation field `no_new_numbers_attestation` is a claim by Agent 12
    that is *verified* by steps 1–2; it is never accepted on its own.
- **EXPLICIT BAN:** Agent 12 must NEVER invent, adjust, round (beyond a logged
  form), annualise, extrapolate, interpolate, or otherwise create a numerical
  financial result. It must NEVER state a price target, return, probability, or
  interval that Agent 11's log does not contain. It must NEVER present a
  forecast as guaranteed. Violation is `E_INVENTED_NUMBER` and blocks the
  artefact.
- **Estimated resource requirements:** CPU Low–Medium (local Ollama inference),
  memory per the local model in use (human-admin choice; no model is named or
  endorsed here — naming a model is a later-phase, human-approved choice),
  LLM use: Medium relative to other agents (this is the main prose-synthesis
  agent, and its local-inference budget in architecture §7 applies in full).
- **Expected output:** One AI synthesis per forecast record per job — prose
  only, every number traceable, dual-validated before any downstream use.

## Agent 13 — Risk Management

- **Purpose:** Measure risk and state limits, deterministically. Single owner
  of risk measurement (R13). It does not decide a recommendation (Agent 14)
  and does not set portfolio weights (Agent 15).
- **Responsibilities:** (a) Read Agents 1, 5, 6, 7, 9, 10, 11 outputs by
  reference as the job names them; (b) run only catalogue-named risk functions
  (volatility/drawdown/exposure/limit measures as the catalogue defines them),
  logging every call; (c) state risk limits and breaches in the job's own terms
  (limits come from the job approval, never invented by the agent); (d) state
  what risk cannot be measured from the available data (e.g. where macro or
  statement inputs are gap records).
- **Input schema:** `{ job_id, symbol_or_portfolio_ref, market_data_batch_refs[], assessment_refs[] (as named by the job), forecast_ref (optional), job_risk_limits[] (from job approval, required if limits are to be checked) }`
- **Output schema:** `{ risk_assessment_id, scope, risk_measures[] { function@version, inputs_logged, value_ref (function log) }, limit_checks[] { limit_as_approved, result [WITHIN | BREACH | NOT_MEASURABLE], evidence_ref }, unmeasurable_risks[], limitations[] }`
- **Required tools:** Python stdlib; deterministic risk functions;
  shared-context read/write (own group). No external network.
- **Data dependencies:** Agents 1, 5, 6, 7, 9, 10, 11 as named. Missing inputs →
  `NOT_MEASURABLE` for the affected measures, never estimated.
- **Execution frequency:** Per approved company-analysis, forecast, or
  portfolio job, as the job names it.
- **Failure handling:** Unmeasurable risk is a reported outcome, not a task
  failure, unless the job required that measure — then the orchestrator, on
  human instruction, decides whether the job proceeds.
- **Retry strategy:** Retryable: `E_TIMEOUT`, `E_FUNCTION_ERROR` (up to 2
  retries after input check). Non-retryable: `E_SCHEMA`,
  `E_INVENTED_NUMBER` → dead-letter + audit flag.
- **Audit requirements:** Every risk measure traces to a function log; every
  limit check cites the limit exactly as approved.
- **Estimated resource requirements:** CPU Low–Medium, memory Low, LLM use:
  Low (Ollama local only, for limit/limitation prose quoting logged measures).
- **Expected output:** One risk assessment per scope per job, consumed by
  Agents 14 and 15.

## Agent 14 — Investment Decision

- **Purpose:** Propose BUY / HOLD / SELL / WATCHLIST recommendations with
  uncertainty shown. **Single owner of recommendation proposals (R14) — the
  ONLY agent that may write recommendation content.** No other agent, including
  the orchestrator, may create, edit, or relabel a recommendation.
- **Responsibilities:** (a) Read Agents 5, 6, 7, 10, 11, 12, 13 outputs by
  reference as the job names them; (b) weigh them (fundamental, technical,
  sector, valuation, forecast, synthesis, risk) and propose exactly one label
  per symbol per job from {BUY, HOLD, SELL, WATCHLIST}, with the evidence refs
  and uncertainty that support it; (c) state what would change the proposal
  (in words, as conditions — not as new numbers); (d) never word a proposal as
  a certainty, a promised return, or a trading instruction; (e) never execute,
  route, or imply execution of a trade — recommendations/reports only.
- **Input schema:** `{ job_id, symbol, fundamental_assessment_ref, technical_assessment_ref (optional), sector_assessment_ref (optional), valuation_ref, forecast_ref (optional), ai_synthesis_ref (optional, only if dual-validated), risk_assessment_ref, news_brief_ref (optional), macro_brief_ref (optional) }`
- **Output schema:** `{ recommendation_id, symbol, as_of_pkt, label [BUY | HOLD | SELL | WATCHLIST], evidence_refs[], uncertainty_statement (quoting forecast/risk logs where numeric), rationale_prose, conditions_that_would_change_it[], audit_status [PENDING | CLEARED | FLAGGED | BLOCKED] (set by Agent 16 only — Agent 14 writes PENDING) }`
- **Required tools:** Python stdlib; Ollama local open-weight only for
  rationale prose (no paid LLM API). Shared-context write to the recommendation
  group only (its sole write group besides its own draft group, which the
  permission matrix treats as one recommendation-writing right — see matrix
  notes). No external network. **No trade-execution tool exists for this agent
  and none may be added in Phase 1.**
- **Data dependencies:** Agents 5, 10, 13 (required) and 6, 7, 11, 12, 8, 9
  (where the job names them). If a required input is missing or blocked, the
  agent does not propose on a partial basis unless the job explicitly allows a
  partial-input proposal and the proposal states its partial basis.
- **Execution frequency:** Per approved company-analysis / decision job, only
  after all named inputs are `completed` (and, for Agent 12 input, dual-validated).
- **Failure handling:** Blocked/flagged input → proposal held as `PENDING`
  with a note, not proposed as clean. Conflicting inputs → rationale states
  the conflict and how it was weighed, in words; it does not hide the conflict
  or invent a tie-breaking number.
- **Retry strategy:** Retryable: `E_TIMEOUT` (up to 2 retries). Non-retryable:
  `E_SCHEMA`, `E_INVENTED_NUMBER`, `E_AUDIT_BLOCK` (an audit-blocked input
  cannot be retried into a proposal) → dead-letter / held, per the error.
- **Audit requirements:** Every proposal starts `PENDING` and reaches a reader
  only after Agent 16 sets `CLEARED` (or `FLAGGED`, with flags shown). Every
  number in the rationale traces to a function log via its evidence refs.
- **Estimated resource requirements:** CPU Low, memory Low, LLM use: Low–Medium
  (Ollama local only).
- **Expected output:** One recommendation proposal per symbol per job, in
  `PENDING` state, for Agent 16 to audit. **No trade is executed, ordered, or
  routed as a result of this output — ever, in Phase 1.**

## Agent 15 — Portfolio Optimization

- **Purpose:** Propose portfolio weights/allocations deterministically, within
  approved constraints. Single owner of weights/allocations (R15). A weight is
  NOT a recommendation, and this agent must NOT issue BUY/HOLD/SELL labels.
- **Responsibilities:** (a) Read Agents 1, 7, 10, 11, 13 outputs and, where
  the job names them, Agent 14 proposals (as inputs to be weighed, not to be
  edited); (b) run only catalogue-named optimisation functions, logging every
  call with its constraints exactly as approved; (c) state the constraints,
  the resulting weights, and the limitations (especially where inputs were
  partial or risk was unmeasurable).
- **Input schema:** `{ job_id, portfolio_scope { symbols[], universe_ref }, assessment_refs[] (as named), risk_assessment_ref, constraints_as_approved[] (required — no constraint may be invented), optimisation_functions[] (named catalogue functions only) }`
- **Output schema:** `{ portfolio_proposal_id, scope, constraints_as_approved[], weights[] { symbol, weight_ref (function log) }, optimisation_function_refs[] (function logs), limitations[], note_weights_are_not_recommendations }`
- **Required tools:** Python stdlib; deterministic optimisation functions;
  shared-context read/write (own group). No external network.
  **No trade-execution tool; no recommendation-write permission.**
- **Data dependencies:** Agents 1, 7, 10, 11, 13 (and 14 proposals as read-only
  input where named). Missing/unmeasurable inputs → affected symbols held at
  an explicitly stated treatment (per job approval) or excluded with a note —
  never allocated a plausible weight silently.
- **Execution frequency:** Per approved portfolio job only (not per company job
  by default).
- **Failure handling:** Infeasible constraints (as approved) → proposal reports
  infeasibility with evidence, not a relaxed-constraint solution presented as
  if it met the approved constraints. A relaxed run, if the human admin approves
  it, is a new task with new constraints.
- **Retry strategy:** Retryable: `E_TIMEOUT`, `E_FUNCTION_ERROR` (up to 2
  retries after input check). Non-retryable: `E_SCHEMA`,
  `E_INVENTED_NUMBER` → dead-letter + audit flag.
- **Audit requirements:** Every weight traces to a function log + its approved
  constraints; the `note_weights_are_not_recommendations` field must be present
  in every proposal.
- **Estimated resource requirements:** CPU Medium, memory Low–Medium, LLM use:
  Low (Ollama local only, for limitations prose).
- **Expected output:** One portfolio proposal per portfolio job, consumed by
  Agent 16 (audit) and Agent 17 (rendering, with the not-a-recommendation note
  shown) — never executed as trades.

## Agent 16 — Independent Audit

- **Purpose:** Independently verify every releasable artefact before a human
  reader sees it as clean, and block or flag what fails. Single owner of audit
  verdicts (R16). Audit does not write analysis content and does not silently
  rewrite a recommendation's substance.
- **Responsibilities:** (a) For each artefact submitted: check schema version,
  input refs exist and are the versions named, provenance is present, every
  number traces to a function log, and (where applicable) re-run deterministic
  functions on logged inputs and compare outputs; (b) check Agent 12 syntheses
  under the dual-validation rule (with Agent 11's check — see entry 12);
  (c) check recommendations: label is from the allowed set, uncertainty is
  shown, no certainty/promise/trading-instruction wording, evidence refs are
  present; (d) set `audit_status` to `CLEARED`, `FLAGGED` (with reasons, still
  releasable only with flags shown), or `BLOCKED` (not releasable as clean);
  (e) for `BLOCKED` items, record reasons and the remediation required — the
  fix is a new version/task by the owning agent, never an audit edit to substance.
- **Input schema:** `{ job_id, artefact_refs[] (any agent's output records + their function logs + input refs), audit_checklist_version }`
- **Output schema:** `{ audit_report_id, artefact_refs[], checks[] { check_name, result [PASS | FAIL], evidence }, audit_status_per_artefact[] { artefact_ref, status [CLEARED | FLAGGED | BLOCKED], reasons[] }, remediation_required[] }`
- **Required tools:** Python stdlib; deterministic function re-runner (same
  catalogue, same versions); shared-context read (all output groups, read-only
  except the audit-status field — see permission matrix) and write (audit group
  + audit-status field only). No external network. No paid model; audit prose
  via Ollama local only where prose is needed, but verdicts themselves are
  check outcomes, not LLM judgements.
- **Data dependencies:** All agents' outputs + function logs for the job.
  Audit never audits its own audit report as a clean artefact — a second audit
  pass on a corrected artefact is a new audit record.
- **Execution frequency:** Per job, after each artefact set is `completed` and
  before Report Generation renders it; plus a final pre-release audit pass.
- **Failure handling:** A check that cannot be performed (missing log, missing
  input ref) → `FAIL` for that check and `BLOCKED` (or `FLAGGED` only if the
  job's audit policy explicitly allows that failure class to be flagged rather
  than blocked — the policy is human-approved, not decided by Audit per item
  without a rule). Audit never passes an artefact on trust.
- **Retry strategy:** Audit checks are deterministic and do not retry on
  failure — a `FAIL` is a verdict, not a transient error. `E_TIMEOUT` on the
  audit task itself (not on a check) is retryable up to 2 times. A corrected
  artefact triggers a NEW audit task, not a retry of the old verdict.
- **Audit requirements:** This agent IS the audit requirement for others; its
  own records must show checklist version, every check outcome, and reasons.
  Audit records are immutable once issued; a superseding audit is a new record
  referencing the old one.
- **Estimated resource requirements:** CPU Low–Medium (function re-runs),
  memory Low, LLM use: Low (Ollama local only, prose reasons only).
- **Expected output:** One audit report per artefact set, with a per-artefact
  verdict that the orchestrator enforces: `BLOCKED` artefacts are never
  dispatched to Report Generation as clean; `FLAGGED` artefacts go forward only
  with flags shown.

## Agent 17 — Report Generation

- **Purpose:** Render audit-cleared (or audit-flagged, with flags shown)
  artefacts into a human-readable report. Single owner of report rendering
  (R17). It creates no number, no analysis, and no recommendation.
- **Responsibilities:** (a) Assemble only artefacts whose audit status the
  orchestrator confirms as releasable (`CLEARED`, or `FLAGGED` with flags);
  (b) render recommendation labels, forecast numbers, valuations, and risk
  measures VERBATIM from their source records (with refs); (c) show audit
  flags, limitations, uncertainty statements, data gaps, and UNVERIFIED-input
  notes prominently — never in a footnote that contradicts the body;
  (d) include the PKR 0 / Ollama-local disclosure and the no-trade statement
  (recommendations/reports only) in every report; (e) never edit substance to
  "improve" readability where the edit would change a number, label, or verdict.
- **Input schema:** `{ job_id, artefact_refs[] (audit-cleared/flagged only, with audit_report_ref), report_template_version, language_and_format_as_approved }`
- **Output schema:** `{ report_id, artefact_refs_rendered[], audit_flags_shown[], rendered_content_ref, report_note (limitations, gaps, UNVERIFIED notes, PKR 0 / Ollama-local disclosure, no-trade statement), release_status [DRAFT | RELEASED] (RELEASED only after the final audit pass confirms the rendered draft matches its sources) }`
- **Required tools:** Python stdlib rendering only; shared-context read
  (cleared artefacts + audit reports) and write (report group only).
  No external network. No paid model; any prose templating via Ollama local
  only, and templated prose must not introduce numbers.
- **Data dependencies:** Agents 1–16 outputs as audited. A `BLOCKED` artefact
  is never rendered as clean; if a report cannot be completed without it, the
  report states the omission and its reason.
- **Execution frequency:** Per approved job, after the final audit pass.
- **Failure handling:** Rendered draft mismatching a source (number, label, or
  flag differs) → draft rejected by the final audit pass, returned for
  re-rendering (new report version), never released with the mismatch.
- **Retry strategy:** Retryable: `E_TIMEOUT` (up to 2 retries). Non-retryable:
  `E_AUDIT_BLOCK` (attempting to render a blocked artefact as clean),
  `E_SCHEMA` → dead-letter + audit flag.
- **Audit requirements:** The rendered draft itself receives a final audit pass
  (Agent 16) confirming verbatim rendering before `RELEASED`.
- **Estimated resource requirements:** CPU Low, memory Low, LLM use: None–Low
  (Ollama local only, templating only).
- **Expected output:** One report per job (or per job part, as approved), in
  `DRAFT` until the final audit pass, then `RELEASED` — recommendations/reports
  only, no trade execution.

## Agent 18 — Monitoring and Recovery

- **Purpose:** Report on run health, detect failures and backlogs, and
  RECOMMEND recovery — never dispatch tasks itself. Single owner of run-health
  reporting and recovery recommendations (R18).
- **Responsibilities:** (a) Observe queue depth, task states, retries,
  dead-letters, timeouts, audit blocks, and local-inference budget use, from
  orchestrator records (read-only); (b) produce a run-health report per run
  (counts, states, budget use, wall-clock time — no currency, PKR 0 project
  spend + external-operating-expense disclosure); (c) recommend recovery actions
  (e.g. requeue a dead-lettered task after a fix, pause a run, narrow a job's
  scope) — recommendations only; only the human admin approves and only the
  orchestrator executes them; (d) alert on queue-depth, budget-exhaustion, and
  repeated audit blocks as policy thresholds are crossed.
- **Input schema:** `{ job_id, run_id, orchestrator_records_ref (queue/task/budget logs), alert_thresholds_as_approved }`
- **Output schema:** `{ health_report_id, run_id, summary { tasks_by_state, retries, dead_letters[], audit_blocks[], budget_use, wall_clock }, alerts[], recovery_recommendations[] { action, reason, requires_human_approval [always true] } }`
- **Required tools:** Python stdlib; shared-context / orchestrator-log read
  (read-only) and write (health-report group only). No external network.
  No dispatch tool, no requeue tool, no budget-raising tool.
- **Data dependencies:** Orchestrator records only. Monitoring never reads
  market data or analysis content to judge health — health is judged from
  task/budget/audit-state records, not from whether results "look good".
- **Execution frequency:** During a run (at orchestrator checkpoints as
  approved) and at run end; plus on alert thresholds being crossed.
- **Failure handling:** Missing orchestrator records → health report states
  the gap and does not infer health. A monitoring failure never pauses or
  alters a run by itself — it alerts the human admin.
- **Retry strategy:** Retryable: `E_TIMEOUT` (up to 2 retries).
  Non-retryable: `E_SCHEMA`, `E_PERMISSION` → dead-letter (and an alert, since
  a monitoring failure itself needs human attention).
- **Audit requirements:** Health reports are retained with the run record;
  every recovery recommendation states that human approval is required.
- **Estimated resource requirements:** CPU Low, memory Low, LLM use: Low
  (Ollama local only, report prose).
- **Expected output:** One health report per run (plus alert reports as
  triggered), consumed by the human admin and the orchestrator's pause/resume
  decisions — never acted on unilaterally by Agent 18.

---

## Notes that apply to all 18 entries (revised brief, merged 2026-11-04)

1. **Inference is Ollama local open-weight only.** Wherever an entry above says
   "LLM use", it means Ollama local inference. No paid AI/LLM API, no
   subscription, no API key is permitted for any agent. A task claim naming a
   paid LLM tool is rejected by the orchestrator.
2. **Budget is PKR 0 absolute.** No agent's work may require a purchase. Local
   hardware, electricity, and internet are external operating expenses —
   disclosed, never called free (see architecture §1A).
3. **Phase 1 is read-only inspection for data, and design/specification for
   everything else.** The frequencies above are the *specified* later-phase
   behaviour; in Phase 1 itself there is NO full-scale live data collection,
   NO live polling, and NO execution of these agents at scale. Testing strategy
   is defined (architecture §1A stage 8), not claimed passed.
4. **No agent executes real trades, initially or in Phase 1.** There is no
   trade-execution permission for any agent row in the permission matrix, and
   no trade-execution tool in any entry above. Recommendations/reports only.
5. **STOP AFTER PHASE 1.** These entries specify the system; they do not start
   Phase 2, implementation, live collection, or trading.

## Registry version

- **Version:** Phase 1, 2026-11-04 (original + revised-brief merge, same day).
- **Change rule:** Any addition, removal, renaming, schema change, permission
  change, or frequency change creates a new registry version, requires a
  permission-matrix review, and requires human-admin approval. Agents in a run
  always reference the registry version the run was approved under.
