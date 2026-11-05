# Agentic Technical Recommendations for PSX Intelligence AI

**Purpose.** This document extracts only the *actionable technical recommendations* from material already read earlier in this project (agentic-AI articles and guides) and maps each one onto PSX Intelligence AI. It contains no article summaries, no marketing language, and no re-reading of source articles or linked guides.

**Governing rules (override everything below).** PKR 0 / free and open-source only. No real trades, no broker or order path, no guaranteed returns, no fabricated prices, statements, or historical data. Deterministic Python functions compute every financial number; LLMs produce prose only, over logged deterministic outputs, dual-validated by Statistical Forecasting and the Independent Audit agent. Every record carries source, source timestamp, collected-at time (Asia/Karachi), and freshness. Conflicting records are kept side-by-side, never silently merged. Missing observations are recorded, never zero-filled. Raw data stays separate from processed data. Nothing here authorises commercial redistribution of PSX data, which requires separate written permission.

**Evidence convention.** Each recommendation ends with an EVIDENCE STATUS line. "Article claim" means a figure or practice as published in the source material, not independently verified and not a measured PSX fact. "PSX-verified" means it has been established inside this project (code, database, or test evidence). The two are never mixed.

**Stack referenced throughout.** The already-fixed Phase 1 stack: Next.js/React/TypeScript frontend; Python/FastAPI/Pydantic backend; PostgreSQL/SQLAlchemy/Alembic; local filesystem + Parquet; Redis; Celery; Ollama local-only inference. No new paid dependency is introduced by any recommendation below.

---

## 1. AI agent security and permission controls

### 1.1 Permission tiers with least privilege per agent

**WHAT.** Give each of the 18 agents only the permissions its job needs, and grade actions into tiers: read-only (safe to run unattended), internal write (writes to staging/quarantine tables only), and consequential (publishes a record, changes a verification status, sends anything outside the system). Consequential actions require a recorded approval gate, not an agent's own say-so. This mirrors the published control set for agentic applications (input/output validation, tool-access restriction, identity and permission scoping, audit logging, and human oversight of high-impact actions).

**PSX APPLICATION.** Market Data, Company Discovery, and Historical Research agents run read-only against sources and write only to raw/quarantine tables. Only the Independent Audit agent may promote a record's quality status, and only the Report Generation agent may assemble a published output. The orchestrator enforces the tier at the tool-call boundary, not inside each agent's prompt. Maps to Phase 5 validation statuses and Phase 22 (recommendation engine) gating.

**WHAT NOT TO DO.** Do not give every agent a shared, all-powerful toolset, and do not let a data-collection agent mark its own output VERIFIED. A compromised or hallucinating agent must be able to damage at most its own staging area.

**EVIDENCE STATUS.** Article claim (published agentic-security control set, including the OWASP Top 10 for agentic applications, as published — not independently verified); PSX-verified in part (Phase 3 schema already separates raw/processed tables and carries quality_status CHECKs; tier enforcement at the orchestrator is still to be implemented).

### 1.2 Human approval gates for consequential actions; never auto-approve 100%

**WHAT.** No pipeline stage auto-approves everything. Route each output through a confidence threshold with a human review queue for everything below it, and require explicit human approval for any externally visible or status-changing action. Published document-processing practice puts that threshold at 0.85–0.95 with a review queue; the exact PSX threshold must be calibrated per agent, not copied blindly.

**PSX APPLICATION.** Applies to registry verification (a lone-source import stays UNVERIFIED — see the Phase 4 audit rule), financial-statement extraction (OCR output is never treated as verified), valuation outputs, and any future recommendation text. Low-confidence extractions go to PENDING_REVIEW with their source page reference attached, never to silent acceptance. The Monitoring and Recovery agent owns the queue, not the agent that produced the output.

**WHAT NOT TO DO.** Do not set a threshold of 1.0 in disguise (e.g. "auto-approve unless obviously wrong"), do not let the review queue silently drain into approval on timeout, and do not present a queued item as verified while it waits.

**EVIDENCE STATUS.** Article claim (0.85–0.95 threshold range and never-auto-approve-100% rule, as published); PSX-verified in part (Phase 4 H1 rule and UNVERIFIED-by-default behaviour are already implemented and database-verified).

### 1.3 Input validation, prompt-injection resistance, and secret hygiene

**WHAT.** Validate every tool input and every external text blob (scraped page, announcement PDF, news item) before it reaches an agent: schema-check it, strip or neutralise embedded instructions, and never let retrieved text override system instructions. Keep credentials out of prompts, logs, code, and commits entirely; agents receive scoped, short-lived access to the tools they need and nothing else.

**PSX APPLICATION.** All Phase 5+ collectors and Phase 7 document ingestion pass through a validation layer that rejects malformed records into quarantine with a reason code (see §4). No agent prompt ever contains a password, token, or API key — the project has no paid API keys by design, and the rule also covers database credentials and GitHub access. Tool results that contain instructional language ("ignore previous instructions", "send this elsewhere") are treated as data, logged, and never followed.

**WHAT NOT TO DO.** Do not paste tool output into a prompt without a boundary, do not log full tool payloads that could contain secrets, and do not let a news article or announcement PDF re-task an agent.

**EVIDENCE STATUS.** Article claim (published injection and tool-misuse controls, as published); PSX governance rule already adopted project-wide (no secrets in code/commits/logs).

### 1.4 EXCLUDED: paid security and monitoring platforms

**WHAT.** Commercial agent-security dashboards, hosted guardrail APIs, and paid monitoring suites are excluded from this architecture.

**PSX APPLICATION.** Their functions are covered inside the fixed stack: PostgreSQL audit/execution logs, Redis-backed rate limiting and caching, FastAPI request validation (Pydantic), and the Independent Audit agent. No data leaves the local machine for a security verdict.

**WHAT NOT TO DO.** Do not route PSX records through a third-party moderation or guardrail API, paid or free-tier, without a separate licence and privacy review — the free tier of a paid service is still an external data flow.

**EVIDENCE STATUS.** PSX governance decision (PKR 0, local-only); the excluded products' capabilities are article claims, not evaluated here.

---

## 2. Agent orchestration and coordination

### 2.1 Supervisor–worker orchestration with a router, not a free-for-all

**WHAT.** One orchestrator (supervisor) owns task decomposition, routing, and completion criteria; worker agents own single responsibilities and return structured results. A lightweight router classifies each incoming task (deterministic calculation vs retrieval vs prose) and sends it to the cheapest capable path. Published workflow patterns distinguish fixed multi-step workflows (use when the steps are known in advance) from autonomous agents (use when the path genuinely cannot be written up front) — and recommend the workflow whenever the steps can be written up front.

**PSX APPLICATION.** This is the existing 18-agent registry plus orchestrator design. The orchestrator routes: deterministic work (indicators, ratios, valuations) to Python functions, never to an LLM; retrieval/extraction work to the relevant specialist agent; prose work to the AI Forecasting / Report Generation agents over logged deterministic outputs. The 5-step chain pattern (collect → analyse → resolve conflicts → construct → verify) is preserved as a fixed workflow wherever the steps are known, which is most of Phases 5–10.

**WHAT NOT TO DO.** Do not let worker agents spawn each other recursively, do not give the router authority to reclassify a deterministic calculation as an LLM task, and do not run an autonomous agent where a fixed pipeline already describes the work.

**EVIDENCE STATUS.** Article claim (workflow-vs-agent rule and supervisor/router patterns, as published); PSX-verified in part (18-agent registry and orchestrator are specified in Phase 1; orchestration code is a later-phase deliverable).

### 2.2 Keep tool results, not chatter, at the centre of agent context

**WHAT.** Published measurements of agent runs report tool results occupying roughly 60–70% of context tokens, with the system prompt only a small fraction. Design prompts accordingly: a short, static system prompt (which also caches better) plus dynamic context injected in a clearly delimited block, and structured tool outputs that agents can quote rather than re-derive.

**PSX APPLICATION.** Agent prompts carry: role, objective, tool list, constraints, output schema, and one or two few-shot examples (published guidance: 1–2 for simple tasks, 3–5 for multi-step tasks, more only with measured benefit). The dynamic block carries the exact database rows, source references, and validation statuses the agent must work from. Agents return structured JSON matching a Pydantic schema, not free prose, for anything that enters the database.

**WHAT NOT TO DO.** Do not stuff full documents into prompts when a page reference plus extracted fields will do; do not let an agent re-state a number from memory when the deterministic output is available as a tool result; do not grow the system prompt per task (that defeats caching and makes behaviour unrepeatable).

**EVIDENCE STATUS.** Article claim (60–70% tool-result share, few-shot sizing, static-prompt caching, as published); PSX application is a design rule, not yet measured in this project — measure token/context behaviour when the orchestrator is built and record it before asserting any figure.

### 2.3 Iteration limits with human escalation, and a five-step chain discipline

**WHAT.** Cap autonomous loops (published practice: roughly 10–25 iterations) and escalate to a human — or, in this project, to a quarantine + review queue — when the cap is hit, rather than letting an agent spin. Keep chain steps fixed and few: the published five-step pattern and this project's existing chain discipline both argue against adding steps casually.

**PSX APPLICATION.** Every agent loop in Phases 5–10 gets a configured iteration cap, a timeout, and an escalation path to PENDING_REVIEW with the partial trace preserved. The five-step agent chain is preserved: step 1 may carry a validation summary, but no step is added or removed without a spec change. The Monitoring and Recovery agent watches for loops that hit caps and for agents that repeatedly return the same failed result.

**WHAT NOT TO DO.** Do not raise the cap instead of fixing the underlying failure, do not silently truncate a loop's trace on escalation, and do not add a sixth chain step as a workaround for a validation failure.

**EVIDENCE STATUS.** Article claim (10–25 iteration range, as published); PSX chain discipline is a project rule (Phase 5 spec and Portfolio Agent plan both preserve five steps).

### 2.4 Memory in layers, stored locally

**WHAT.** Separate working memory (current task, in Redis), episodic memory (what happened in past runs, in PostgreSQL), semantic memory (durable facts such as sector mappings and formula versions, in PostgreSQL), and procedural memory (how tasks are done — the runbooks and checklists themselves). Published guidance stresses invalidation and time-to-live handling, and provenance for recalled facts, because stale recalled context is a silent failure mode.

**PSX APPLICATION.** Working context lives in Redis with short TTLs; run history, agent execution logs, and quality decisions live in PostgreSQL (Phase 3 already provides agent/model execution logs); formula versions, sector mappings, and alias mappings are versioned rows, never bare prompt text. Every recalled fact used in an output carries its source and version, so a stale mapping (e.g. a renamed ticker) can be traced and corrected rather than silently reused.

**WHAT NOT TO DO.** Do not let an agent treat recalled context as verified truth; do not store unversioned mappings in prompt text; do not keep episodic memory without a retention and invalidation policy (see Phase 1 data-retention policy).

**EVIDENCE STATUS.** Article claim (memory taxonomy, hot/cold latency figures, and invalidation pitfalls, as published — latency figures are not PSX measurements); PSX mapping is a design rule using the fixed stack only.

### 2.5 EXCLUDED: hosted memory and orchestration services

**WHAT.** Hosted agent-memory services, hosted orchestration platforms, and paid workflow-automation platforms are excluded.

**PSX APPLICATION.** Their roles are covered by PostgreSQL (episodic/semantic), Redis (working memory), Celery (scheduled and chained work), and the FastAPI orchestrator. No agent state is stored outside the local stack.

**WHAT NOT TO DO.** Do not adopt a paid automation platform's free tier as the scheduler or orchestrator — that reintroduces an external dependency and a data flow the PKR 0 rule forbids relying on.

**EVIDENCE STATUS.** PSX governance decision (fixed stack, PKR 0).

---

## 3. Autonomous workflow execution

### 3.1 Design for 95%, handle the remaining 5% explicitly

**WHAT.** Published automation practice recommends designing a workflow to handle about 95% of cases straight through, and giving the remaining cases an explicit path (review queue, quarantine, or a defined fallback) instead of pretending coverage is total. A workflow that claims 100% autonomous handling is usually silently mishandling the hard cases.

**PSX APPLICATION.** Phase 5 ingestion, Phase 7 extraction, and Phase 8 ratio computation each define their straight-through criteria (valid source, complete fields, validation passed) and their explicit non-straight-through paths (PENDING_REVIEW, CONFLICTED, MISSING, REJECTED — see §4). Coverage reports always state their denominator (e.g. "470 of 470 snapshot securities" for one view) and never present partial-view coverage as full-market coverage.

**WHAT NOT TO DO.** Do not report a phase complete on straight-through volume alone while the review queue holds unexamined records, and do not widen straight-through criteria to clear a queue.

**EVIDENCE STATUS.** Article claim (design-for-95% heuristic, as published); PSX application is already partially demonstrated (snapshot import: 470/470 matched for one view, with GEM/Non-Compliant explicitly out of scope).

### 3.2 Shadow-mode rollout before autonomous promotion

**WHAT.** Run a new autonomous step in shadow mode first: it executes and logs its decisions, but its outputs do not change production records, until its decisions match the existing (or human-reviewed) baseline at an agreed rate. Only then is it promoted to write production data.

**PSX APPLICATION.** Every new collector, extractor, or scoring step in Phases 5–10 runs shadow-first against already-validated data (e.g. the 470-row snapshot, or a hand-checked statement sample): compare its outputs field-by-field with the baseline, record the mismatch rate, and promote only on a written promotion decision recorded in the phase docs. The existing dry-run pattern (import script `--dry-run` before `--commit`) is the template.

**WHAT NOT TO DO.** Do not promote on a single successful run, do not shadow-test on production tables, and do not treat shadow agreement as verification — it is a rollout gate, not a quality status.

**EVIDENCE STATUS.** Article claim (shadow-mode rollout, as published); PSX-verified in part (dry-run-then-commit is already practised in the snapshot import).

### 3.3 Idempotent retries with backoff, and safe scheduler catch-up

**WHAT.** Every autonomous step must be safe to re-run: re-processing the same input produces the same result without duplicating records. Retries use bounded backoff and a hard stop on repeated failure (including rate-limit responses, which are a stop signal, not a cue to retry harder). Schedulers that missed a run must catch up without double-ingesting or silently skipping the missed window.

**PSX APPLICATION.** Importers and collectors are idempotent by key (company + security + source + period) — the snapshot import already demonstrates this (re-import skipped 470/470). Celery tasks carry bounded retries with backoff; a 429 or equivalent rate-limit response halts that source's collection and is logged as a blocker, not retried in a loop. The Phase 5 scheduler records the last successful window per source and, on restart, replays exactly the missed window once, marking any still-unobtainable window MISSING with its reason.

**WHAT NOT TO DO.** Do not retry on a fixed tight loop, do not catch up by re-ingesting an already-ingested window, and do not fill a missed window with an estimate.

**EVIDENCE STATUS.** Article claim (backoff and retry discipline, as published); PSX-verified in part (idempotent import demonstrated; scheduler catch-up is a Phase 5 deliverable).

### 3.4 Quarantine, not deletion, for failed records

**WHAT.** Records that fail validation, parsing, or matching go to quarantine with their raw payload, source reference, and failure reason preserved — never deleted, never silently dropped, never auto-corrected by guessing.

**PSX APPLICATION.** Phase 3 storage already provides quarantine; Phase 5 and Phase 7 must use it for malformed rows, unparseable PDF pages, and unmatched securities. Quarantine contents are reported in every phase test report (counts by failure reason), and a quarantined record can only leave quarantine through a reviewed correction, recorded as a new version.

**WHAT NOT TO DO.** Do not auto-repair a failed record with an LLM guess, do not drop a failed row to make a coverage figure look complete, and do not let quarantine grow unbounded without a review cadence (monthly, aligned with the source re-read cadence).

**EVIDENCE STATUS.** PSX-verified in part (quarantine exists in the Phase 3 storage engine; per-phase quarantine reporting is a deliverable, not yet demonstrated for market data).

---

## 4. Error detection and recovery

### 4.1 Validation statuses as the single error language

**WHAT.** Every computed or ingested value carries one quality status from a fixed vocabulary, and downstream consumers filter on it. No status may be upgraded by the agent that produced the value.

**PSX APPLICATION.** The vocabulary is VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, CONFLICTED, MISSING, REJECTED, STALE. Rules already fixed: VERIFIED requires at least two distinct agreeing sources including one official (Phase 4 audit rule H1); a single-source import stays UNVERIFIED; rejected or conflicted values are never silently included in indicators, ratios, valuations, or forecasts. Phase 6 indicators, Phase 8 ratios, and Phase 9 valuations must each state which statuses they accept as inputs, and what they emit when inputs are insufficient (NOT_CALCULABLE / INSUFFICIENT_DATA, never zero).

**WHAT NOT TO DO.** Do not invent a new status per phase, do not treat UNVERIFIED as "probably fine" in a downstream calculation, and do not average a CONFLICTED pair into a single value.

**EVIDENCE STATUS.** PSX-verified (vocabulary and H1 rule implemented; snapshot import produced 470/470 UNVERIFIED with 0 VERIFIED, 0 conflicts, 0 rejections).

### 4.2 Reconciliation coverage as a first-class metric

**WHAT.** For every ingestion, report matched / missing / extra against the authoritative reference, as a coverage ratio with its denominator stated. A coverage figure without its denominator is not a metric.

**PSX APPLICATION.** The Phase 4 `reconcile()` function is the template: snapshot 470 vs registry 470, matched 470, missing 0, extra 0, coverage 1.0 — for the Main Board / Normal Counter view only. Phase 5 market ingestion, Phase 7 statement collection, and Phase 10 macro collection each produce the same report against their own dated reference (expected securities, expected periods, expected documents). A coverage drop between runs is a defect to investigate, not a number to smooth over.

**WHAT NOT TO DO.** Do not report coverage against a reference you also generated (that is self-grading — see §5); do not change the reference mid-run to improve the ratio; do not present view-scoped coverage as universe coverage.

**EVIDENCE STATUS.** PSX-verified for the registry snapshot (470/470, coverage 1.0, dry-run and commit runs agreeing); market-data reconciliation is a Phase 5 deliverable.

### 4.3 Duplicate detection, stale-data flags, and conflict preservation

**WHAT.** Detect duplicates on deterministic keys before insertion (never on name similarity alone); flag stale data by comparing source timestamps against the current date and the source's expected refresh cadence, never by fetch time; and preserve conflicting values side-by-side with provenance so a human or audit agent can adjudicate.

**PSX APPLICATION.** Duplicate detection keys: company + security + source + period for market data; document hash for statements and announcements. Staleness uses the source timestamp (e.g. the DPS page header date), not the fetch time — a snapshot fetched today but dated weeks ago is STALE, not current. Conflicts (two sources disagreeing on a price, a name, or a sector) are stored as parallel records with both provenances and a CONFLICTED status; the resolver reports the conflict, it does not pick a winner silently. This directly reuses the Phase 4 engine's conflict → CONFLICTED and ambiguous → PENDING_REVIEW behaviour.

**WHAT NOT TO DO.** Do not deduplicate on fuzzy name matching (distinct securities sharing a name, such as ordinary vs preference vs rights variants, must stay distinct); do not refresh a stale flag by re-fetching the same old source; do not resolve a conflict by averaging or by preferring the newest value without a rule.

**EVIDENCE STATUS.** PSX-verified in part (duplicate handling and conflict behaviour demonstrated in the snapshot import and Phase 4 adversarial checks; staleness labelling is specified and partially demonstrated — the DPS header date vs fetch date distinction is recorded).

### 4.4 Recovery runbooks, not ad-hoc fixes

**WHAT.** For each known failure class (source unreachable, rate-limited, malformed payload, schema drift, downstream validation failure), write a runbook: symptom, diagnosis query, recovery action, and the record of what was changed. Recovery actions are themselves logged and versioned.

**PSX APPLICATION.** The defect register already records D-51 (direct DPS access failure), D-52 (JavaScript-driven table), and D-54 (gate failure) with causes and required fixes. Phase 5+ runbooks extend this: source-outage runbook (switch to the dated snapshot, mark the window MISSING, retry on the next scheduled window — never scrape around a block), schema-drift runbook (quarantine new fields, do not auto-map them), and validation-failure runbook (quarantine, review queue, corrected re-ingestion as a new version).

**WHAT NOT TO DO.** Do not fix a production record in place without a versioned correction; do not close a defect on the basis of a single successful retry; do not let a recovery action bypass the validation statuses.

**EVIDENCE STATUS.** PSX-verified in part (defect register practice exists; per-class runbooks are a Phase 5+ deliverable).

---

## 5. Independent verification and auditing

### 5.1 Dual validation: no agent grades its own output

**WHAT.** Every consequential output is checked by a second, independent path: a different agent, a deterministic recomputation, or both. Published agentic practice separates the quality/compliance layer from the action layer for exactly this reason, and financial-governance practice here requires it: AI Forecasting prose is dual-validated by Statistical Forecasting and Independent Audit.

**PSX APPLICATION.** Indicators are recomputed by an independent implementation and compared field-by-field (Phase 6 requires hand-calculated cases plus an independent reference implementation). Ratios and valuations are recomputed from source statements, not from a previous agent's summary. The Independent Audit agent (Agent 16) is organisationally separate from the producing agents: it reads source documents and database rows, not the producing agent's self-report.

**WHAT NOT TO DO.** Do not let the producing agent also write its own audit verdict; do not validate against the same intermediate output the producer generated; do not count a passing self-test as an audit.

**EVIDENCE STATUS.** Article claim (separate quality/compliance layer, as published); PSX governance rule adopted in Phase 1 and practised in Phases 3–4 (independent audit reports with severity-graded findings, plus a second verification of the Phase 3 migration cycle).

### 5.2 Spot-checks against source files, with a fixed sample discipline

**WHAT.** In addition to full-population checks (reconciliation, duplicate detection), run human-or-audit-agent spot-checks against the original source file or page, on a stated sample that always includes edge cases (variant securities, blank fields, displayed typos) — not a random sample alone.

**PSX APPLICATION.** The snapshot import spot-check is the template: 24/24 rows passed, deliberately including 7 blank-Clearing-Type rows, rights/preference variants, and verbatim displayed spellings. Phase 5 market ingestion, Phase 7 statement extraction, and Phase 8 ratio computation each define their spot-check sample in their test report (minimum 20 rows, edge cases mandatory) and report pass/fail per row.

**WHAT NOT TO DO.** Do not spot-check only clean rows; do not sample from the processed table instead of the source file; do not report a spot-check pass rate without the sample definition.

**EVIDENCE STATUS.** PSX-verified (24/24 snapshot spot-check, documented in the import record).

### 5.3 Audit findings graded, tracked, and closed only on evidence

**WHAT.** Audit findings carry severity (CRITICAL / HIGH / MEDIUM / LOW), a fix or a written acceptance, and closure only when re-verification demonstrates the fix. Accepted findings stay visible in the record with their rationale; they are not deleted.

**PSX APPLICATION.** This is already the practice in Phases 3–4 (e.g. Phase 3: 0 CRITICAL, 3 HIGH, 9 MEDIUM, 10 LOW, all fixed or accepted in writing; Phase 4: 0 CRITICAL, 1 HIGH, 5 MEDIUM, 6 LOW, HIGH fixed by the H1 rule change). The same discipline applies to every later phase's independent audit report, and to the Portfolio Agent universe work's audit.

**WHAT NOT TO DO.** Do not close a finding on the basis of a code change alone without a re-run; do not downgrade severity to clear a gate; do not let an accepted finding disappear from the defect register.

**EVIDENCE STATUS.** PSX-verified (Phases 3–4 audit reports and defect register practice).

### 5.4 Provenance and reproducibility as audit prerequisites

**WHAT.** An output is auditable only if its inputs, versions, and parameters can be reproduced: source, source timestamp, collected-at time, formula/model version, parameters, and the exact input rows. Without that tuple, an audit cannot distinguish a correct result from a lucky one.

**PSX APPLICATION.** Every Phase 6 indicator value stores security, indicator, parameters, frequency, calculation timestamp, last input date, quality status, version, and source lineage, with version history never overwritten. Forecasts store model version, inputs, and uncertainty. Recommendations store the evidence list they rest on. This is why deterministic functions, not LLM prose, own every number: prose cannot be reproduced from a prompt alone.

**WHAT NOT TO DO.** Do not publish a value whose inputs cannot be re-fetched or recomputed; do not overwrite a versioned value with a correction (store the correction as a new version); do not strip provenance when moving data from staging to production tables.

**EVIDENCE STATUS.** PSX governance rule (Phase 1 specification) and Phase 3 schema implementation (versioned statements, formula/model versions, full history tables).

---

## 6. Efficient local and free AI model usage

### 6.1 Ollama local-only, with model selection by task difficulty

**WHAT.** All inference runs locally via Ollama; no prompt, document, or record leaves the local machine for inference. Published model-selection guidance distinguishes simple/classification work (small, fast models suffice) from complex multi-step reasoning (larger models justified) and recommends routing between them — applied here entirely within local open-weight models.

**PSX APPLICATION.** Simple work (document classification, field extraction triage, ticker matching suggestions that a deterministic matcher then confirms or rejects) uses a small local model. Complex work (multi-document synthesis prose, audit narrative) uses a larger local model, still via Ollama. No model, large or small, computes a financial number — that is deterministic Python's job, and a model is never used where a function already answers the question.

**WHAT NOT TO DO.** Do not send PSX records, statements, or user data to any hosted LLM API; do not use the largest available model for every task "to be safe" (that is the most expensive habit in local inference too — it costs time and GPU memory); do not let a model output enter the database without passing through deterministic validation.

**EVIDENCE STATUS.** Article claim (model routing by task difficulty, as published); PSX governance rule (Ollama local-only, fixed in Phase 1). No local model has been benchmarked in this project yet — see §6.3.

### 6.2 Never use an expensive model for deterministic work

**WHAT.** If a calculation, lookup, match, or validation can be expressed as a deterministic function, it must be one. LLM calls are reserved for work that genuinely needs language understanding or synthesis, and even there the model works over deterministic outputs it cannot alter.

**PSX APPLICATION.** Indicators, ratios, valuations, forecasts' numerical cores, reconciliation, duplicate detection, and quality-status assignment are Python functions. The AI Forecasting agent writes prose *about* logged statistical outputs; it does not generate, adjust, or select the numbers. The same rule applies to the Portfolio Agent universe work: alias *suggestions* may come from a model, but alias *decisions* come from a verified source and a versioned mapping.

**WHAT NOT TO DO.** Do not ask a model to compute RSI, ROE, or a fair value; do not ask a model to decide whether two records conflict (that is a deterministic comparison with provenance); do not use a model as a database lookup.

**EVIDENCE STATUS.** PSX governance rule (Phase 1, restated in every phase spec); the cost side is an article claim (expensive agents for deterministic work waste budget — here, time and local compute rather than money).

### 6.3 Pin models and versions; benchmark before claiming performance

**WHAT.** Record the exact model name, version or digest, and inference parameters for every model-assisted step, alongside the code version that called it. Published guidance warns against pinning versions on unverified benchmarks — so record versions, and benchmark locally on PSX-representative samples before asserting any speed or quality figure.

**PSX APPLICATION.** Model/version pinning is a Phase 1 gate item (G-04: versions and Ollama model unpinned — Phase 2 pinned actually installed versions only). Every model-assisted phase document records model + version + parameters + the sample it was evaluated on. No latency, accuracy, or cost figure is asserted for a local model until measured on this VM with a stated method and date (Phase 1 gate G-08: no measured figures asserted anywhere without method and date).

**WHAT NOT TO DO.** Do not cite a vendor benchmark as a PSX performance claim; do not upgrade a model mid-phase without re-running the affected tests; do not leave "latest" as a model version in any production path.

**EVIDENCE STATUS.** PSX governance rules (G-04, G-08, still open as gates); no local benchmark has been run yet — this is a known gap, not a result.

### 6.4 EXCLUDED: paid LLM APIs, paid model hosting, and paid data feeds

**WHAT.** Hosted LLM APIs (any vendor), paid model endpoints, paid market-data APIs, paid financial subscriptions, and paid automation/monitoring platforms are excluded from this architecture — including their free tiers where use would create an external data flow or a future paywall dependency for a core function.

**PSX APPLICATION.** Inference is Ollama local-only with open-weight models. Market and company data come from free public sources only (DPS listing status, PSX public pages, SECP/SBP/PBS/Finance Division public material where machine-use is verified), with licensing verified before any commercial use. Scheduling and orchestration are Celery + Redis, not a paid platform.

**WHAT NOT TO DO.** Do not add a hosted API key "temporarily" for a benchmark or a demo — a temporary external dependency becomes a permanent architecture decision; do not present a free-tier hosted service as a PKR 0 solution for a core function.

**EVIDENCE STATUS.** PSX governance decision (PKR 0, fixed stack); excluded products are named only to record the exclusion.

---

## Adopt / Defer / Reject

| Recommendation | Decision | Reason / next step |
|---|---|---|
| Permission tiers + least privilege per agent (§1.1) | **Adopt** | Enforce at the orchestrator's tool-call boundary in the next agent-building phase. |
| Human approval gates, never auto-approve 100% (§1.2) | **Adopt** | Already partially in place (H1, UNVERIFIED-by-default); extend to extraction and recommendation outputs. |
| Input validation + prompt-injection resistance + secret hygiene (§1.3) | **Adopt** | Validation layer required before Phase 5/7 ingestion scales. |
| Supervisor–worker orchestration with a router (§2.1) | **Adopt** | Existing 18-agent design; implement router's deterministic-vs-LLM classification explicitly. |
| Tool-result-centred context, static system prompts (§2.2) | **Adopt** | Apply to all agent prompts; measure context behaviour when the orchestrator is built. |
| Iteration limits with escalation (§2.3) | **Adopt** | Configure per agent with quarantine escalation; never raise caps to hide failures. |
| Layered local memory (§2.4) | **Adopt** | PostgreSQL + Redis only; versioned mappings, never prompt-embedded facts. |
| Design for 95%, explicit path for the rest (§3.1) | **Adopt** | Already demonstrated for the registry view; require per-phase coverage denominators. |
| Shadow-mode rollout (§3.2) | **Adopt** | Template is the import dry-run; require a written promotion decision per new step. |
| Idempotent retries, backoff, safe catch-up (§3.3) | **Adopt** | Import idempotence demonstrated; scheduler catch-up is a Phase 5 deliverable. |
| Quarantine, not deletion (§3.4) | **Adopt** | Storage engine supports it; require per-phase quarantine reporting. |
| Fixed validation-status vocabulary (§4.1) | **Adopt** | Implemented; enforce downstream filtering by status in Phases 6–10. |
| Reconciliation coverage with stated denominator (§4.2) | **Adopt** | Template is `reconcile()` at 470/470 for one view; require per-ingestion reports. |
| Duplicate detection, stale flags, conflict preservation (§4.3) | **Adopt** | Engine behaviour demonstrated; staleness must use source timestamps, never fetch time. |
| Recovery runbooks (§4.4) | **Adopt** | Extend the defect register into per-class runbooks in Phase 5. |
| Dual validation, no self-grading (§5.1) | **Adopt** | Governance rule; independent recomputation required for indicators, ratios, valuations. |
| Source-file spot-checks with edge cases (§5.2) | **Adopt** | Template is the 24/24 import spot-check; require per-phase sample definitions. |
| Severity-graded, evidence-closed audit findings (§5.3) | **Adopt** | Already practised in Phases 3–4. |
| Provenance + reproducibility prerequisites (§5.4) | **Adopt** | Schema already supports it; enforce in every later phase. |
| Ollama local-only, task-routed model selection (§6.1) | **Adopt** | Fixed stack; small models for simple work, larger local models only for complex prose. |
| No LLM for deterministic work (§6.2) | **Adopt** | Governance rule; enforce in code review for every phase. |
| Model/version pinning + local benchmarks before claims (§6.3) | **Defer** | Adopt the pinning rule now; defer any performance claim until a local benchmark is run (G-04/G-08 still open). |
| Paid security/monitoring platforms (§1.4) | **Reject** | PKR 0 + local-only; covered by PostgreSQL logs, Pydantic validation, Independent Audit. |
| Hosted memory / orchestration / automation platforms (§2.5) | **Reject** | Covered by PostgreSQL + Redis + Celery + FastAPI orchestrator; external dependency forbidden for core functions. |
| Paid LLM APIs, paid model hosting, paid data feeds (§6.4) | **Reject** | PKR 0 rule; Ollama local-only and free public sources only. |
| Auto-applying ticker renames from a single source (§2, §5) | **Reject** | Single-source aliases stay report-only until a second authoritative source verifies them (Portfolio Agent decision). |
| Presenting partial-view coverage as full-market coverage (§3.1, §4.2) | **Reject** | 470 rows cover Main Board / Normal Counter only; GEM and Non-Compliant views are separate, uncaptured integrations. |
| Treating a fetched page's date as its source date (§4.3) | **Reject** | Fetch time is never a source timestamp; staleness uses the source header date. |
