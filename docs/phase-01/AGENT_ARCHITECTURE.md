# PSX Intelligence AI — Agent Architecture (Phase 1)

> **Team:** Team 5 — Multi-Agent Architecture
> **Phase:** Phase 1 of 30 — design only. No application code, no Phase 2 work.
> **Date / starting condition verified:** 2026-11-04 (reused verbatim from the Phase 1 brief)
> **Status:** Design specification. Nothing in this document authorises a trade, a purchase,
> a sign-up, an install, a credential, an API key, a broker connection, live polling,
> or posting.
>
> **REVISED BRIEF (merged 2026-11-04, not a duplicate build):** Budget is **PKR 0 absolute
> zero-cost** — agents use **Ollama local open-weight inference only**; no paid AI/LLM
> APIs or subscriptions. Local hardware, electricity, and internet are **EXTERNAL
> operating expenses** — they must be disclosed as such and must never be called
> "free". Phase 1 follows the 11-stage workflow in §1A, with data inspection
> **read-only only** and **NO full-scale live data collection in Phase 1**. The system
> must **NOT execute real trades initially** — see rule 6 and §6: no agent has
> trade-execution permission; recommendations/reports only. **STOP AFTER PHASE 1.**
> Testing strategy is defined in §1A, not claimed as passed — no test result is
> asserted in Phase 1.

## 0. Starting condition (reuse verbatim, do not re-verify by inventing)

- Project folder `~/workspace/psx-intelligence-ai/` is new. Other teams may be creating
  sibling files; Team 5 writes only the four files listed in §10 of this document.
- Existing separate scaffold to **REFERENCE but NEVER overwrite or touch**:
  `~/workspace/psx-data-collection/` — a standard-library (stdlib) collector with
  provenance / Pakistan Time (PKT) / stale-data / conflict rules.
- Tools available in this environment: Python 3.12.3, Node v24.22.1.
  Docker, `psql`, and `redis-cli` are **NOT installed**. This architecture therefore
  assumes **no Docker, no PostgreSQL, and no Redis in Phase 1**. Any queue, store,
  or context described below is a *logical* design; its Phase 1 physical form must
  be implementable with the Python standard library alone (for example, files and
  `sqlite3`, which ships with Python) or deferred to a later phase with explicit
  approval. No team may silently assume an uninstalled service.
- Already verified (reused, not re-claimed here as new research):
  - `psx-dps` — MIT licence, zero dependencies, no API key, ~496 trading symbols
    vs ~1029 listed symbols, ~5 years of end-of-day (EOD) data, today's ticks,
    38 sectors, a multi-node 404 quirk, and no official PSX API.
  - `psxdata` — MIT licence, PyPI, alpha `0.1.0a1`, daily OHLCV + live snapshots
    ONLY, no historical intraday archive.
  - Eulerpool: **NO PSX coverage**, vendor only, no paid API approved.
- **UNVERIFIED — do not use as if verified:** machine-use of SECP, SBP, PBS,
  Finance Division, World Bank, IMF, and FRED is UNVERIFIED. Any agent that would
  consume those inputs must list them as UNVERIFIED and define a fallback:
  **skip the input with an audit note — never invent data.** See §8 and
  `AGENT_REGISTRY.md` (Agents 8 and 9 in particular).
- No paid API is approved. No broker connection exists or is authorised.

## 1. Governing rules (apply to every agent, no exceptions)

1. **Deterministic calculations only for numbers.** Every financial number in any
   output must be produced by a named, versioned, deterministic Python function.
   An LLM/agent must NEVER invent, estimate by prose, round by hand, or "fill in"
   a numerical financial result.
2. **LLMs/agents interpret; functions compute.** An agent may select which named
   function to call, check its inputs, and interpret its output in words. It may
   not replace the function, and it may not report a number the function did not
   return.
3. **Every number-carrying output logs:** function name + version, input identifiers
   (symbol, date range, source, as-of timestamp in PKT), output value(s), and the
   agent + run id that called it. If the log is missing, the output is not releasable.
4. **Forecasts are probabilistic and evidence-based, never guaranteed.**
   Horizons are fixed: **1 day, 1 week, 1 month, 3 months, 6 months, 12 months**.
   Every forecast carries its horizon, its method, its input window, and an
   uncertainty statement (interval / distribution summary produced by a
   deterministic function — never a prose-only confidence claim).
5. **BUY / HOLD / SELL / WATCHLIST are probabilistic recommendations with
   uncertainty shown, not guarantees.** No recommendation may be worded as a
   certainty, a promise of return, or a trading instruction.
6. **Recommendations/reports only — NO real trades, initially and in Phase 1.**
   The system produces recommendations and reports. It does **not** execute real
   trades, place orders, connect to a broker, or send orders. **No agent — including
   the orchestrator and the human admin acting through the agent path — has
   trade-execution permission** (see the permission matrix, where the
   trade-execution column is denied for every row). There is no trading path in
   this architecture to enable later by accident; adding one would be a new,
   separately approved design change, and is explicitly out of Phase 1.
7. **No invented capability.** Never invent an API, endpoint, price, filing,
   news item, macro figure, or data-source capability. If a source is not verified,
   the agent skips it with an audit note (§8).
8. **Least privilege.** An agent can read only what its row in
   `AGENT_PERMISSION_MATRIX.md` allows, and can write only to its own output
   group. See §6.
9. **Audit before release.** No recommendation or report reaches a human reader
   without passing through Independent Audit (Agent 16). Audit can block or flag;
   it cannot silently rewrite a recommendation's substance (see §6 and the registry).
10. **Cheap before expensive; Ollama local only.** A task that a deterministic
    function can perform must not be assigned to an LLM-heavy agent. Where an
    agent needs language inference, it uses **Ollama local open-weight inference
    only — no paid AI/LLM APIs, no subscriptions, no API keys**. LLM use is capped
    by local-inference policy (§7), not by a purchased quota — there is no
    purchased quota, and the project budget is PKR 0 (see §1A cost disclosure).

## 1A. Phase 1 scope: 11-stage workflow, zero-cost rule, and what Phase 1 does NOT do

Phase 1 follows these 11 stages, in order. Team 5's four files are the
architecture-planning / implementation-specification / documentation contribution
to this workflow; they are not themselves a running system, and no stage below
may be skipped by claiming a later stage's outcome early.

| Stage | What it means for Team 5's architecture work |
|---|---|
| 1. Brainstorm | Agent ecosystem options considered; the 18-agent split in the registry is the recorded outcome, with the responsibility map (§9) as the proof against duplication. |
| 2. Research | Reuse of the verified starting condition (§0): `psx-dps` / `psxdata` properties, the separate stdlib scaffold, and the UNVERIFIED list. No new source is claimed as verified by this document. |
| 3. Validate | Every agent definition is checked against the governing rules (§1): deterministic numbers only, single ownership, least privilege, audit before release, no trade execution. Unverifiable claims are removed or marked UNVERIFIED. |
| 4. Data inspection — READ-ONLY ONLY | **No full-scale live data collection in Phase 1.** Phase 1 inspection means reading already-available material (this brief, the separate scaffold's files, and small samples already in hand) to validate schemas, provenance fields, and staleness handling. It does not authorise a full market refresh, a bulk download, live polling, or a new collector run. Agent 1's full retrieval behaviour is therefore *specified* in the registry for later phases, not executed at scale in Phase 1. Any later-phase collection needs its own human approval. |
| 5. Architecture planning | This file + the registry, communication spec, and permission matrix. |
| 6. Implementation specification | Logical schemas, message envelope, lifecycle, permission rows, function-logging rules, and execution limits — specified here so a later phase can implement them without re-deciding them. No application code is written in Phase 1. |
| 7. Documentation | The four Team 5 files themselves, written so another team can implement from them without asking Team 5 to re-explain the design. |
| 8. Testing strategy — DEFINED, NOT CLAIMED PASSED | Strategy (to be executed in a later phase, not asserted now): (a) schema-validation tests — every registry input/output schema rejects a malformed message; (b) determinism tests — re-running a named function on logged inputs reproduces logged outputs; (c) idempotency tests — duplicate delivery yields one record; (d) permission tests — a forbidden write (especially any recommendation write by a non-owner, and any trade-execution attempt) is denied and logged; (e) audit tests — an output with an unlogged number is blocked; (f) fallback tests — an UNVERIFIED input produces a skip-with-audit-note, never invented data. **No test is claimed passed in Phase 1, and no test result is reported as if it had run.** |
| 9. Independent audit | Agent 16's design (registry entry 16) + the audit gates in §6/§9 of this file. In Phase 1 this is a designed gate, not a completed audit of a running system. |
| 10. Correction | Corrections are new versions referencing (never overwriting) prior versions — for documents as for data records. This revised brief is merged as an edit to the existing files, not as a duplicate set. |
| 11. Checkpoint | **STOP AFTER PHASE 1.** Phase 1 ends at the checkpoint: four files delivered, UNVERIFIED list stated, no Phase 2 code, no live collection, no trade path. A later phase starts only on a new explicit instruction. |

### Cost disclosure (PKR 0 rule)

- **Project budget: PKR 0 absolute.** No paid AI/LLM API, no subscription, no
  paid data vendor, no broker fee, and no purchase is authorised by this
  architecture. Eulerpool is already excluded (no PSX coverage, vendor only,
  no paid API approved).
- **Inference: Ollama local open-weight only.** No agent may call a paid LLM
  API, and no agent may require an API key or subscription to function. If a
  later phase proposes a paid model, that is a budget change requiring explicit
  human approval — it is not permitted by silence or by this document.
- **External operating expenses — disclosed, never called free:** the local
  machine/hardware used to run Ollama, electricity, and internet connectivity
  are real operating expenses borne outside this PKR 0 project budget. They are
  **not** project spend, but they are also **not free** — no document in this
  set may describe the system as "free to run" without this disclosure. Cost
  monitoring (§7) therefore tracks local-inference counts and wall-clock time,
  not currency, and reports PKR 0 project spend alongside this disclosure.
- **Cost controls are policy, not a purchased quota:** per-run and per-agent
  local-inference budgets (§7) are human-set caps on local compute use. There
  is no quota to buy, top up, or exhaust into a payment.

## 2. System overview (text diagram)

```
                        ┌─────────────────────────────┐
                        │        HUMAN ADMIN          │
                        │  approvals, budgets, blocks │
                        │  (only human approval gate) │
                        └──────────────┬──────────────┘
                                       │ approves / blocks / sets limits
                                       ▼
┌──────────────┐    tasks    ┌─────────────────────────────┐    results   ┌──────────────┐
│  TASK QUEUE  │ ◄────────── │   CENTRAL ORCHESTRATOR      │ ───────────► │  SHARED      │
│  (logical;   │ ──────────► │   (Agent 0, not a domain    │ ◄─────────── │  CONTEXT     │
│   §4)        │   claims   │    analyst; see §3.1)       │   reads      │  STORE       │
└──────┬───────┘            └──────┬──────────┬───────────┘              │  (versioned, │
       │                           │          │                        │   immutable  │
       │ dispatch                  │          │ dispatch               │   inputs,    │
       ▼                           ▼          ▼                        │   provenance)│
┌─────────────┐  ┌─────────────┐  ┌─────────────┐        ┌─────────────┐└──────┬───────┘
│ DATA AGENTS │  │ ANALYSIS    │  │ SYNTHESIS   │        │ ASSURANCE   │
│ 1 Market    │  │ AGENTS      │  │ AGENTS      │        │ AGENTS      │
│   Data      │  │ 5 Fundamental│ │ 10 Valuation│        │ 16 Independent│
│ 2 Company   │  │ 6 Technical │  │ 11 Statistical│      │    Audit    │
│   Discovery │  │ 7 Sector    │  │    Forecasting│      │ 17 Report   │
│ 3 Historical│  │ 8 News Intel│  │ 12 AI Forecast│      │    Generation│
│   Research  │  │ 9 Macro     │  │ 13 Risk Mgmt│        │ 18 Monitoring│
│ 4 Financial │  │             │  │ 14 Investment│        │    & Recovery│
│   Statement │  │             │  │    Decision │        └─────────────┘
└─────────────┘  └─────────────┘  │ 15 Portfolio│
                                  │    Optimiz. │
                                  └─────────────┘
       ▲                           │                         ▲
       │              DETERMINISTIC FUNCTION LAYER (§5)      │
       │   every number: named function + version + log      │
       └─────────────────────────────────────────────────────┘
```

Reading order of a normal run (the orchestrator enforces it; agents do not
re-order it on their own):

1. Data agents (1–4) produce versioned, provenance-stamped inputs.
2. Analysis agents (5–9) read only those inputs and produce analysis artefacts.
3. Synthesis agents (10–15) call deterministic functions over analysis artefacts.
4. Assurance agents (16–18) audit, render, and watch — in that order for release.
   Report Generation (17) renders only audit-cleared (or audit-flagged, with the
   flag shown) content; it never creates a new number or recommendation.

The orchestrator never performs domain analysis itself. If it did, it would
duplicate an analyst agent's responsibility (see §9).

## 3. Core components

### 3.1 Central orchestrator (Agent 0 — coordination only)

- **Purpose:** Own the run lifecycle: accept a human-approved job, break it into
  tasks from the registry, enqueue them in dependency order, dispatch to exactly
  one owning agent per task, collect results, enforce limits, and hand the
  completed set to audit.
- **Owns:** task queue state, run ids, dispatch order, timeout/retry bookkeeping,
  budget accounting, dead-letter routing.
- **Does NOT own:** any market, company, financial, technical, valuation,
  forecast, risk, recommendation, or portfolio content. It must not summarise,
  reinterpret, or "improve" an agent's output. It passes artefacts by reference
  (id + version), never by rewriting them.
- **Single point of dispatch, not a single point of silent failure:** if the
  orchestrator stops, queued tasks remain queued (durable logical queue, §4) and
  no partial output is released. Monitoring and Recovery (Agent 18) reports the
  stall; only the human admin restarts a run, and the restart resumes from the
  last completed task, never by re-running already-completed tasks without an
  idempotency check (see `AGENT_COMMUNICATION_SPEC.md`).
- **Human gates the orchestrator enforces (it cannot waive them):**
  - a new job type, a new data source, or a raised budget/limit needs human-admin
    approval before dispatch;
  - a blocked recommendation (Audit status `BLOCKED`) is never dispatched to
    Report Generation for release as a clean recommendation;
  - a dead-lettered task is never silently retried by the orchestrator.

### 3.2 Agent registry

`AGENT_REGISTRY.md` is the single authoritative list of the 18 agents. The
orchestrator dispatches **only** to agents and task types named there, with the
input/output schemas named there. Adding an agent, renaming one, or changing a
schema is a registry change: it requires a new registry version, a permission
-matrix review, and human-admin approval. Agents must not invent a new agent
role at run time (for example, an agent must not spawn a "news summariser" or
a "trading executor" that is not in the registry).

Each registry entry fixes: purpose, responsibilities, input schema, output
schema, required tools, data dependencies, execution frequency, failure
handling, retry strategy, audit requirements, estimated resources, and expected
output. The orchestrator validates every task claim against that entry before
dispatch; a mismatch is rejected, not adapted on the fly.

### 3.3 Shared context store (logical)

- **What it is:** a versioned, append-only store of run inputs and agent outputs,
  each record carrying: `record_id`, `run_id`, `agent_id`, `schema_version`,
  `created_at_pkt`, `provenance` (source + retrieval/derivation method), and,
  for numbers, the deterministic-function log (§5).
- **What it is not:** a chat transcript, a mutable scratchpad, or a place where
  an agent edits another agent's output. Published records are immutable; a
  correction is a new version that references (never overwrites) the old one.
- **Read rules:** an agent reads only the record versions its task names, and
  only the groups its permission row allows. Reading "the latest of everything"
  is not permitted — the task must name the input version, so a rerun reproduces
  the same result from the same inputs.
- **Write rules:** an agent writes only its own output group, once per task
  (idempotent re-delivery returns the existing record — see the communication
  spec). No agent writes to another agent's group, to the recommendation group
  (except as §6 states), or directly to a released report.
- **Retention (Phase 1 policy):** every record that feeds a released report or
  recommendation is retained with its provenance for audit. No Phase 1 retention
  period is asserted as a legal/compliance rule here; the human admin sets it,
  and Monitoring and Recovery reports records approaching it. Deletion, if ever
  approved, is by the human admin only, logged, and never silent.

### 3.4 Task queue (logical)

See §4. The queue is the orchestrator's work list, not a second orchestrator:
it stores tasks, it does not decide what a task means.

### 3.5 Message protocol (summary — full spec governs)

Full definition: `AGENT_COMMUNICATION_SPEC.md`. Summary:

- Every inter-agent exchange is a **message** with a fixed envelope
  (`message_id`, `run_id`, `task_id`, `idempotency_key`, `sender`, `recipient`,
  `schema_version`, `created_at_pkt`, `payload_ref`).
- Payloads travel **by reference** to shared-context records, not as large
  inline blobs, so the message log stays auditable and replays stay exact.
- Task lifecycle: `queued → running → completed | failed | retry → dead-letter`
  (dead-letter is terminal for that attempt; only the human admin may requeue
  with a new task id after fixing the cause).
- Idempotency keys are deterministic (derived from run + task + input versions),
  so a retried or duplicated delivery produces one output, not two.
- Error taxonomy and retry limits are fixed in the communication spec; agents
  do not invent retry behaviour per incident.

### 3.6 Deterministic function layer (summary — §5 governs)

Between every agent and every numerical output sits a named deterministic
function. Agents request a computation; they do not perform it in prose. The
orchestrator records the call; Statistical Forecasting (Agent 11) owns the
function catalogue for forecasting/statistics, and Independent Audit (Agent 16)
verifies that every released number traces to a logged call.

## 4. Task queue — design

| Property | Phase 1 design |
|---|---|
| Nature | Logical FIFO-with-priority queue owned by the orchestrator. Priority is by dependency and human-approved job priority only — never by an agent's self-asserted urgency. |
| Physical form (Phase 1) | Implementable with Python stdlib only (files / `sqlite3`). No Redis, no PostgreSQL, no Docker assumed. If a later phase adopts another broker, the message envelope and lifecycle in the communication spec do not change; only the transport adapter changes, with human approval. |
| Task record | `task_id`, `run_id`, `agent_id`, `task_type` (from registry), `input_refs` (shared-context record ids + versions), `idempotency_key`, `state`, `attempt_count`, `max_attempts`, `created_at_pkt`, `deadline_pkt` (policy, §7). |
| Claiming | One agent claims one task; the claim is exclusive until timeout or completion. An unclaimed task after its claim timeout returns to `queued` (not to `failed`) once, then follows the retry policy. |
| Ordering | Dependency order enforced by the orchestrator: a task is not dispatched until every input ref it names is in state `completed` and audit-relevant inputs are present. Agents never poll for inputs that do not exist yet; they wait for dispatch. |
| Backpressure | Queue-depth and concurrency caps (§7). When a cap is hit, the orchestrator stops dispatching new tasks and Monitoring and Recovery reports the backlog. It does not drop tasks silently. |
| Dead letter | After `max_attempts` failures, or on a non-retryable error (see error taxonomy), the task moves to `dead-letter` with its error code and last input refs preserved. No output from a dead-lettered task is used downstream. |
| No live polling | The queue is not a live-market poller. Market refresh is a scheduled/approved job (see registry frequencies), not a continuous stream. Nothing in this architecture authorises live polling of a market feed. |

## 5. Deterministic calculation functions — how they sit between agents and outputs

```
Agent request ──► [Function catalogue: name + version + input schema]
                      │
                      ▼
              Deterministic Python function
              (pure: same inputs → same outputs; no network,
               no clock-dependent randomness unless the seed is
               an explicit, logged input)
                      │
                      ▼
              Function log ──► Shared context (with the output)
                      │
                      ▼
              Agent interpretation (words only, numbers quoted
              from the log) ──► Downstream agent / Audit / Report
```

Rules:

1. **Catalogue ownership:** Statistical Forecasting (Agent 11) owns the
   catalogue's statistical/forecasting functions (their definitions, versions,
   and input schemas). Other agents own their own domain functions only where
   the registry says so (for example, Valuation owns valuation formulas,
   Technical Analysis owns indicator formulas, Risk Management owns risk
   formulas, Portfolio Optimization owns optimisation routines). No agent may
   redefine another agent's function. The catalogue itself is a versioned
   artefact; a function change creates a new version and never rewrites history.
2. **Naming:** every function is referenced as `module.function@version`
   (illustrative naming pattern only — actual module names are a Phase 2
   implementation choice, not asserted here). A reference without a version is
   invalid and Audit rejects the output.
3. **Purity:** a deterministic function takes explicit inputs and returns
   explicit outputs. It does not read the network, the wall clock (except a
   logged `as_of_pkt` passed in as an input), or an agent's prose. Randomness,
   where a method genuinely needs it (for example, a simulation), uses a seed
   that is an explicit input and is logged, so the run is reproducible.
4. **Validation chain for forecasts (mandatory):**
   - Statistical Forecasting (11) produces the deterministic forecast
     (point/interval/distribution, per fixed horizon).
   - AI Forecasting (12) may **only** synthesise and interpret those outputs
     in words, over the logged numbers. It must not produce, adjust, or restate
     a number that the deterministic output does not contain. See its registry
     entry for the explicit ban and the validation step.
   - Independent Audit (16) re-checks: function name/version, input versions,
     output reproduction (re-running the function on the logged inputs gives
     the logged outputs), and that the AI synthesis quotes no unlogged number.
   - If any check fails, the forecast is blocked/flagged and is not released.
5. **No LLM arithmetic:** if an agent's draft contains a number that is not in
   a function log for that run, Audit treats it as an invented number and blocks
   the artefact. The fix is to call (or correct the call to) the function, not
   to edit the prose number.
6. **Tiny illustrative snippet (pattern only, not application code):**

```python
# Illustrative pattern ONLY — not a valuation, forecast, or trading routine.
# A real Phase 2 function must be pure, versioned, and logged as in §5 above.
def compute_example_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        raise ValueError("denominator must not be zero")
    return numerator / denominator
```

   This snippet proves the *shape* of a deterministic function. It is not a
   claim about any PSX figure, and no Phase 1 output may cite it as a result.

## 6. Agent permissions — summary (full matrix governs)

Full matrix: `AGENT_PERMISSION_MATRIX.md`. Summary of the non-negotiable lines:

- **Recommendations:** ONLY Investment Decision (Agent 14) **proposes**
  BUY/HOLD/SELL/WATCHLIST content. ONLY Independent Audit (Agent 16) may
  **block or flag** a recommendation (by setting its audit status, with reasons).
  Every other agent — including the orchestrator, Report Generation, Portfolio
  Optimization, and AI Forecasting — has **NO write access** to recommendations.
  Portfolio Optimization may propose portfolio *weights/allocations* as its own
  output group, but it may not create, edit, or relabel a recommendation.
  Report Generation renders recommendations verbatim (with audit flags shown);
  it never edits their substance.
- **External network:** ONLY Market Data (Agent 1) has approved external access
  in a later-phase run, and only through the already-verified libraries (`psx-dps`,
  `psxdata`) via the separate `psx-data-collection` scaffold's rules. **In Phase 1
  itself there is no full-scale live data collection** (§1A stage 4): Agent 1's
  retrieval is specified, not executed at scale, and Phase 1 inspection is
  read-only. All other
  agents have NO external network access in Phase 1. In particular:
  News Intelligence (8) and Macroeconomic (9) have NO approved external source
  in Phase 1 — their would-be inputs (news feeds; SECP/SBP/PBS/Finance Division/
  World Bank/IMF/FRED) are UNVERIFIED, so they work only on operator-supplied,
  provenance-stamped inputs if any are provided, and otherwise skip with an
  audit note.
- **Human admin:** the only role that can approve a new source, raise a limit,
  requeue a dead-lettered task, release a blocked item after remediation, or
  delete a record. The human admin does not write analysis content through the
  agent path; admin actions are themselves logged.
- **Least-privilege default:** every agent starts with no access and gains only
  the rows its registry entry names. A permission not listed is denied.

## 7. Execution limits and cost monitoring

These are **Phase 1 policy defaults**, set by the human admin and changeable
only by the human admin. They are not measured benchmarks and not purchased
quotas (no paid API is approved).

| Limit | Phase 1 policy default | Notes |
|---|---|---|
| Max concurrent agent tasks per run | 4 | Prevents runaway parallelism; orchestrator enforces. |
| Max concurrent runs | 1 | Phase 1 is sequential by design; a second run queues behind the first. |
| Per-task timeout | Set per task type in the registry; orchestrator default if unspecified: 30 minutes wall-clock for a data/analysis task, 15 minutes for a synthesis task | Timeout returns the task to `queued` once (see §4), then counts as a failed attempt. |
| Max attempts per task | 3 (initial + 2 retries) for retryable errors; 1 for non-retryable errors | See error taxonomy in the communication spec. |
| Queue depth alert | Monitoring and Recovery alerts the human admin when queued tasks exceed 50 for a single run | Alert, not auto-drop. |
| LLM / expensive-agent use (Ollama local only) | Deterministic functions first (§1 rule 10). Any task an agent could do with a function must not use an LLM-heavy path. All language inference is Ollama local open-weight only — no paid LLM API or subscription. | The orchestrator rejects a task claim that names a paid LLM tool or an API-key-based tool where the registry names a function or Ollama local inference. |
| Local-inference budget (policy, not quota; PKR 0) | Per-run and per-agent Ollama local-inference budgets (call count / token-equivalent local work, as the human admin defines them) are set by the human admin before the run starts, recorded in the run record, and enforced by the orchestrator as a hard stop: when the budget is exhausted, no further local-LLM calls are dispatched in that run and the run is paused for human decision. | No paid API, no subscription, no purchased quota to "top up". Exhaustion is a pause, not an auto-purchase, and never a reason to silently degrade to invented numbers. Project spend stays PKR 0; hardware/electricity/internet remain external operating expenses (see §1A). |
| Cost monitoring | The orchestrator logs, per run and per agent: tasks dispatched, tasks completed/failed, retries, Ollama local-inference calls (count + local tokens processed, where the local runtime reports them), function calls, and wall-clock time. Monitoring and Recovery (18) summarises these in its run-health report. | Project spend is PKR 0 by design. Reports show counts and time, not currency, and carry the §1A disclosure that hardware/electricity/internet are external operating expenses, never described as free. |
| Kill switch | The human admin may pause or abort a run at any time. Abort preserves completed records and audit logs; it does not delete them, and it does not release partial outputs. | Orchestrator implements pause/abort; agents cannot override it. |

## 8. Data sources and UNVERIFIED dependencies

| Source / input | Phase 1 status | Which agents | Fallback |
|---|---|---|---|
| `psx-dps` (MIT, zero deps, no API key) | Verified (reused) — subject to its known limits: ~496 trading vs ~1029 listed, ~5y EOD, today's ticks, 38 sectors, multi-node 404 quirk, no official PSX API | Market Data (1), via the `psx-data-collection` scaffold | On retrieval failure: stale-data / conflict rules from the scaffold; record the gap, never backfill by invention. |
| `psxdata` (MIT, PyPI, alpha 0.1.0a1) | Verified (reused) — daily OHLCV + live snapshots ONLY, no historical intraday archive | Market Data (1), via the scaffold | Same as above; do not claim intraday history from this source. |
| `psx-data-collection` scaffold (stdlib, provenance/PKT/stale/conflict) | Reference only — never overwritten/touched by Team 5 | Market Data (1) reads/follows its rules | If the scaffold is unavailable, Market Data pauses and reports; it does not invent a replacement collector in-run. |
| SECP machine-use | **UNVERIFIED** | Macroeconomic (9), Financial Statement (4) if it would use SECP filings | Skip with audit note; never invent a filing or figure. |
| SBP machine-use | **UNVERIFIED** | Macroeconomic (9) | Skip with audit note. |
| PBS machine-use | **UNVERIFIED** | Macroeconomic (9) | Skip with audit note. |
| Finance Division machine-use | **UNVERIFIED** | Macroeconomic (9) | Skip with audit note. |
| World Bank machine-use | **UNVERIFIED** | Macroeconomic (9) | Skip with audit note. |
| IMF machine-use | **UNVERIFIED** | Macroeconomic (9) | Skip with audit note. |
| FRED machine-use | **UNVERIFIED** | Macroeconomic (9) | Skip with audit note. |
| News feeds / news vendors | **UNVERIFIED** (no specific feed is verified in Phase 1) | News Intelligence (8) | Work only on operator-supplied, provenance-stamped items if provided; otherwise skip with audit note. Never invent a news item. |
| Eulerpool | NO PSX coverage; vendor only; no paid API approved — **not a Phase 1 source** | None | Do not use for PSX data. |
| Company filings / annual reports (generic) | **UNVERIFIED as a machine source** until a specific filing source is verified and approved | Financial Statement (4) | Work only on operator-supplied, provenance-stamped documents if provided; otherwise skip with audit note. |

**Stale-data rule (from the scaffold, restated as architecture policy):** an
output that depends on market data must name the data's `as_of_pkt` and its
freshness status. If data is stale beyond the job's approved freshness window,
the downstream agent does not proceed as if it were fresh: it either uses the
scaffold's conflict/stale handling or pauses with an audit note, per the job's
approved rule. It never silently substitutes a newer-looking number.

## 9. Responsibility map — proof of no duplication

Each responsibility domain has exactly **one** owning agent. "Reads" or
"validates" a domain is not ownership: for example, several agents read market
data, but only Market Data (1) *produces* it; several agents are checked by
Audit, but only Audit (16) *blocks*.

| # | Responsibility domain (single owner) | Owner | Who else touches it, and how (non-owning) |
|---|---|---|---|
| R1 | Market price/volume retrieval + provenance/staleness | **1 Market Data** | All downstream agents read it; none re-retrieve it. |
| R2 | Company universe, identity, sector membership | **2 Company Discovery** | Sector Analysis (7) reads membership; it does not define the universe. |
| R3 | Historical price/series research over stored data | **3 Historical Research** | Technical Analysis (6) reads its series summaries; it does not rebuild history. |
| R4 | Financial-statement extraction/structuring | **4 Financial Statement** | Fundamental Analysis (5) reads statements; it does not extract them. |
| R5 | Fundamental assessment (quality, earnings, balance-sheet reading) | **5 Fundamental Analysis** | Valuation (10) reads it; it does not redo fundamental judgement. |
| R6 | Technical indicators / chart-based signals (deterministic functions) | **6 Technical Analysis** | Investment Decision (14) reads signals; it does not compute indicators. |
| R7 | Sector aggregation, comparison, rotation reading | **7 Sector Analysis** | Portfolio Optimization (15) reads sector views; it does not aggregate sectors. |
| R8 | News item intake, dating, relevance tagging | **8 News Intelligence** | All readers cite its tags; none re-tag news as a side effect. |
| R9 | Macroeconomic context (only verified/supplied inputs; UNVERIFIED skipped) | **9 Macroeconomic** | Risk Management (13) reads macro context; it does not compile macro series. |
| R10 | Valuation outputs (deterministic valuation functions) | **10 Valuation** | Investment Decision (14) reads valuation; it does not run valuation models. |
| R11 | Statistical forecasting + deterministic function catalogue (stats/forecast) | **11 Statistical Forecasting** | AI Forecasting (12) interprets its outputs only; Audit (16) reproduces them. |
| R12 | AI synthesis/interpretation over deterministic outputs ONLY | **12 AI Forecasting** | No other agent synthesises forecasts in prose; Statistical (11) owns the numbers. |
| R13 | Risk measurement, limits, stress reading (deterministic risk functions) | **13 Risk Management** | Investment Decision (14) reads risk; Portfolio (15) reads risk limits; neither recomputes risk. |
| R14 | BUY/HOLD/SELL/WATCHLIST proposals (+ uncertainty) | **14 Investment Decision** | Audit (16) blocks/flags only; Report (17) renders verbatim; no one else writes recommendations. |
| R15 | Portfolio weights/allocations + optimisation (deterministic) | **15 Portfolio Optimization** | Investment Decision (14) reads allocations as input, not as recommendations; Portfolio does not issue BUY/SELL. |
| R16 | Independent audit: reproduction, provenance, number-trace, block/flag | **16 Independent Audit** | No other agent audits its own output; Report (17) never releases unaudited content as clean. |
| R17 | Report rendering (layout, verbatim content, flags shown) | **17 Report Generation** | No other agent renders a release report; Audit (16) checks the rendered draft before release. |
| R18 | Run health, failure detection, recovery reporting, queue/backlog alerts | **18 Monitoring and Recovery** | Orchestrator owns dispatch; Monitoring owns *reporting* on health and *recommending* recovery — it does not dispatch tasks itself, and only the human admin approves a recovery requeue. |
| R0 | Run orchestration, dispatch order, budget/limit enforcement | **Orchestrator (Agent 0)** | No domain agent dispatches, reorders, or raises its own limits. |

**Overlaps resolved during design (so they do not recur at run time):**

1. *Forecasting (11 vs 12):* resolved by splitting numbers from prose — 11 owns
   every forecast number; 12 owns only prose synthesis over 11's logged outputs,
   with a ban on new numbers and a dual validation step (11 + 16). See registry
   entry 12.
2. *Recommendation vs portfolio (14 vs 15):* resolved by output-group split —
   14 owns recommendation labels; 15 owns weights/allocations. A weight is not
   a recommendation and a recommendation is not a weight.
3. *Audit vs reporting (16 vs 17):* resolved by order — 17 renders only after
   16's verdict, and renders flags verbatim. 17 cannot clear a flag.
4. *Market data vs historical research (1 vs 3):* resolved by time direction —
   1 retrieves and stamps current/stored market data; 3 researches patterns over
   already-stored history. 3 never retrieves fresh market data.
5. *Company universe vs sector (2 vs 7):* resolved by definition vs aggregation
   — 2 defines which companies exist and their sector membership; 7 aggregates
   within that membership and never adds/removes a company.
6. *Risk vs decision (13 vs 14):* resolved by measurement vs judgement — 13
   measures risk and states limits; 14 weighs risk among other inputs to propose
   a recommendation. 14 does not recompute risk figures.
7. *Orchestrator vs monitoring (0 vs 18):* resolved by action vs reporting —
   the orchestrator acts (dispatch/pause); Monitoring reports and recommends
   recovery. Monitoring never dispatches, and the orchestrator never grades its
   own run's health as "healthy" without Monitoring's report.

## 10. Files in this Team 5 Phase 1 set (and nothing else)

1. `AGENT_ARCHITECTURE.md` — this file.
2. `AGENT_REGISTRY.md` — all 18 agents in full.
3. `AGENT_COMMUNICATION_SPEC.md` — message protocol in full.
4. `AGENT_PERMISSION_MATRIX.md` — permission matrix in full.

Team 5 writes only these four files under
`~/workspace/psx-intelligence-ai/docs/phase-01/`. It does not write application
code, does not start Phase 2, does not touch `~/workspace/psx-data-collection/`,
and does not create files for other teams. **STOP AFTER PHASE 1** — no Phase 2
code, implementation, live collection, or trade path follows from these files
without a new explicit instruction.

## 11. Open design questions for the human admin (Phase 1 — not decided by agents)

1. Which (if any) news feed and which macro source should be verified first, so
   Agents 8 and 9 have an approved input instead of a skip-with-note fallback?
2. What are the approved per-run / per-agent Ollama local-inference budgets (§7),
   and the freshness window for market data (§8)? (Budgets are local-compute caps
   under the PKR 0 rule, not purchases.)
3. What is the approved retention period for audit records (§3.3)?
4. What physical queue/context store (stdlib-only) should Phase 2 implement
   first, given Docker/PostgreSQL/Redis are not installed?

Until the human admin answers, the defaults in this document govern, and
UNVERIFIED inputs stay skipped — never invented.
