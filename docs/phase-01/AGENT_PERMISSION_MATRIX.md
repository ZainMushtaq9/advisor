# PSX Intelligence AI — Agent Permission Matrix (Phase 1)

> **Team:** Team 5 — Multi-Agent Architecture
> **Phase:** Phase 1 of 30 — design only. No application code, no Phase 2 work.
> **Companion files:** `AGENT_ARCHITECTURE.md`, `AGENT_REGISTRY.md`,
> `AGENT_COMMUNICATION_SPEC.md`. This matrix governs access; the registry governs
> what each agent may do; the communication spec governs messages. In case of
> conflict on access, this matrix wins.
> **Date / starting condition:** 2026-11-04 — same verified starting condition as
> `AGENT_ARCHITECTURE.md` §0 (Python 3.12.3, Node v24.22.1; Docker, `psql`,
> `redis-cli` NOT installed; `psx-dps` / `psxdata` as verified there; SECP/SBP/
> PBS/Finance Division/World Bank/IMF/FRED machine-use UNVERIFIED).
>
> **REVISED BRIEF (merged 2026-11-04):** Budget **PKR 0 absolute** — Ollama local
> open-weight inference only, no paid AI/LLM APIs or subscriptions. Local
> hardware, electricity, and internet are **external operating expenses** —
> disclosed, never called free. Phase 1 data work is **read-only inspection
> only — NO full-scale live data collection in Phase 1**. The system must
> **NOT execute real trades initially** — the trade-execution column below is
> **DENIED for every row, without exception**, including the orchestrator and
> the human admin acting through the agent path; recommendations/reports only.
> **STOP AFTER PHASE 1.**

## 0. How to read this matrix

- **Rows:** the 18 agents (Agents 1–18) + the central orchestrator (Agent 0) +
  the human admin = 20 rows. No other row exists. An agent, tool, or role not
  listed here has no permission.
- **Columns (grouped for readability):** data sources (§2), logical data groups
  / tables (§1, §3–§4), tools (§5), external calls (§6), write permissions
  (§4), approval gates (§7), trade execution (§8), cost controls (§9).
- **Symbols:** `R` = read (by exact record reference + version only, never
  "latest of everything"); `W` = write (own group only, unless stated);
  `—` = no access; `R*` / `W*` = conditional, with the condition in the notes.
  A blank or unlisted cell means denied — least privilege by default (§10).
- **Logical groups, not physical tables:** Docker, PostgreSQL, and Redis are
  NOT installed, so no physical PostgreSQL table is asserted here. "Tables /
  groups" below are logical shared-context groups. A later phase may map them
  to a physical store (stdlib-only in the first instance) without changing the
  permission rows — the mapping itself needs human approval.
- **Phase 1 scope reminder:** the permissions below describe the *specified*
  system. In Phase 1 itself, data work is read-only inspection only and no
  agent runs at full scale; a permission in this matrix is not an instruction
  to exercise it in Phase 1.

## 1. Logical data groups (shared-context groups)

| Group | Contents | Owning writer |
|---|---|---|
| `G-market` | Market-data batches (Agent 1 outputs: provenance, `as_of_pkt`, coverage, gaps) | Agent 1 |
| `G-universe` | Company universe versions | Agent 2 |
| `G-history` | Historical briefs | Agent 3 |
| `G-statements` | Structured statement records + gap records | Agent 4 |
| `G-analysis` | Fundamental (5), technical (6), and sector (7) assessments | Agents 5, 6, 7 (each its own sub-group) |
| `G-news` | News briefs (accepted/held items) | Agent 8 |
| `G-macro` | Macro briefs (stated + absent indicators) | Agent 9 |
| `G-valuation` | Valuation records | Agent 10 |
| `G-forecast` | Statistical forecast records + function logs | Agent 11 |
| `G-synthesis` | AI synthesis records (prose only) | Agent 12 |
| `G-risk` | Risk assessments + limit checks | Agent 13 |
| `G-recommend` | Recommendation proposals + audit status field | Agent 14 (content, `PENDING` only); Agent 16 (status field only) |
| `G-portfolio` | Portfolio proposals (weights/allocations) | Agent 15 |
| `G-audit` | Audit reports + verdicts | Agent 16 |
| `G-reports` | Rendered reports (draft → released) | Agent 17 |
| `G-health` | Run-health reports + recovery recommendations | Agent 18 |
| `G-queue` | Task queue, run records, dispatch/budget logs, message log | Orchestrator (Agent 0) |
| `G-admin` | Human approvals, budget/limit policy records, block/pause decisions | Human admin |

No agent writes to a group it does not own, except the single stated exception:
Agent 16 writes the `audit_status` field inside `G-recommend` (status + reasons
only — never recommendation content, label, rationale, or evidence).

## 2. Data sources — who may use what

| Source | Status | Permitted users | Denied / fallback |
|---|---|---|---|
| `psx-dps` (MIT, zero deps, no API key; ~496 trading vs ~1029 listed, ~5y EOD, today's ticks, 38 sectors, multi-node 404 quirk, no official PSX API) | Verified (reused) | Agent 1 only, via the `psx-data-collection` scaffold | All other agents: no direct use; they read `G-market` by reference. Phase 1: specified, not run at full scale (read-only inspection only). |
| `psxdata` (MIT, PyPI, alpha 0.1.0a1; daily OHLCV + live snapshots ONLY, no historical intraday archive) | Verified (reused) | Agent 1 only, via the scaffold | All others denied direct use. No intraday history may be claimed from it by any agent. |
| `psx-data-collection` scaffold (stdlib; provenance/PKT/stale/conflict rules) | Reference only — NEVER overwritten/touched by Team 5 | Agent 1 (follows its rules) | No agent modifies the scaffold. If unavailable, Agent 1 pauses + reports. |
| SECP machine-use | **UNVERIFIED** | Nobody in Phase 1 | Agents 4, 9: skip with audit note. Fetching = `E_UNVERIFIED_SOURCE`, refused. |
| SBP machine-use | **UNVERIFIED** | Nobody in Phase 1 | Agent 9: skip with audit note. |
| PBS machine-use | **UNVERIFIED** | Nobody in Phase 1 | Agent 9: skip with audit note. |
| Finance Division machine-use | **UNVERIFIED** | Nobody in Phase 1 | Agent 9: skip with audit note. |
| World Bank machine-use | **UNVERIFIED** | Nobody in Phase 1 | Agent 9: skip with audit note. |
| IMF machine-use | **UNVERIFIED** | Nobody in Phase 1 | Agent 9: skip with audit note. |
| FRED machine-use | **UNVERIFIED** | Nobody in Phase 1 | Agent 9: skip with audit note. |
| News feeds / news vendors (no specific feed verified) | **UNVERIFIED** | Nobody in Phase 1 | Agent 8: operator-supplied items only, else zero-item brief + audit note. |
| Company filings / annual reports as a generic machine source | **UNVERIFIED** | Nobody in Phase 1 | Agent 4: operator-supplied documents only, else gap record. |
| Eulerpool | NO PSX coverage; vendor only; no paid API approved | Nobody | Not a Phase 1 source for any agent. |
| Operator-supplied, provenance-stamped documents/items/lists | Permitted where the registry names them | Agents 2 (lists), 4 (documents), 8 (news items), 9 (macro inputs) — each only its own kind | Any supplied item without provenance is held, not used. |
| Paid data vendors / paid APIs (any) | NOT APPROVED (PKR 0) | Nobody | Any request = denied; no purchase path exists. |

## 3. Read matrix — logical groups (R = read by exact ref+version)

| Row | G-market | G-universe | G-history | G-statements | G-analysis | G-news | G-macro | G-valuation | G-forecast | G-synthesis | G-risk | G-recommend | G-portfolio | G-audit | G-reports | G-health | G-queue | G-admin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Orchestrator (0) | R* | R* | R* | R* | R* | R* | R* | R* | R* | R* | R* | R* | R* | R | R* | R | R/W (§4) | R |
| 1 Market Data | — | R | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 2 Company Discovery | R | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 3 Historical Research | R | R | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 4 Financial Statement | — | R | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 5 Fundamental | R* | R | R | R | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 6 Technical | R | R | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 7 Sector | R | R | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 8 News Intelligence | — | R | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 9 Macroeconomic | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 10 Valuation | R | R | — | — | R (5,6,7) | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 11 Statistical Forecasting | R | — | R | — | R (6 only, if named) | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 12 AI Forecasting | — | — | — | — | R (5,7 words-only) | R | R | — | R | — | — | — | — | — | — | — | — | — |
| 13 Risk Management | R | — | — | — | R (5,6,7) | — | R | R | R* | — | — | — | — | — | — | — | — | — |
| 14 Investment Decision | — | — | — | — | R (5,6,7) | R | R | R | R | R* | R | — | R* | — | — | — | — | — |
| 15 Portfolio Optimization | R | R | — | — | R (7) | — | — | R | R | — | R | R* | — | — | — | — | — | — |
| 16 Independent Audit | R | R | R | R | R | R | R | R | R | R | R | R | R | — | R | R | R | R |
| 17 Report Generation | R* | R* | R* | R* | R* | R* | R* | R* | R* | R* | R* | R* | R* | R | — | — | — | — |
| 18 Monitoring & Recovery | — | — | — | — | — | — | — | — | — | — | — | — | — | R* | — | — | R | R* |
| Human admin | R | R | R | R | R | R | R | R | R | R | R | R | R | R | R | R | R | R/W (§4) |

Notes on `R*` (conditional reads):

- **Orchestrator `R*`:** reads record ids, versions, states, and provenance
  metadata for routing — not domain content for interpretation. It passes
  artefacts by reference and must not summarise or reinterpret them. Its
  `G-audit` read is full (it enforces verdicts); its `G-queue` access is
  read/write (§4).
- **Agent 5 `R*` on `G-market`:** by reference via Agents 3/4 inputs, not as a
  direct market-data consumer; it must not re-derive prices as fundamentals.
- **Agent 13 `R*` on `G-forecast`:** only where the job names a forecast as a
  risk input.
- **Agent 14 `R*` on `G-synthesis`:** only if dual-validated (Agent 11 check +
  Agent 16 audit, per registry entry 12). An unvalidated synthesis is unreadable
  for decision purposes. Agent 14 `R*` on `G-portfolio`:** read-only, where the
  job names a prior portfolio proposal as decision context; it does not edit it.
- **Agent 15 `R*` on `G-recommend`:** read-only, where the job names Agent 14
  proposals as optimisation inputs; it does not edit them.
- **Agent 17 `R*`:** reads ONLY artefacts whose audit status is `CLEARED`, or
  `FLAGGED` with flags to be shown. A `BLOCKED` artefact is unreadable for
  clean rendering (it may be listed as omitted, with its reason, but its
  content is not rendered as clean).
- **Agent 18 `R*` on `G-audit` / `G-admin`:** reads audit verdicts and approved
  thresholds/budgets for health reporting — not to override them.
- **Agent 16** is the only domain agent with read access to every output group.
  That breadth is for verification only; it confers no content-writing right
  (§4).

## 4. Write matrix — who may write what (W = write; — = no write)

| Row | Own group only | G-recommend content | G-recommend audit_status only | G-queue / task state | G-admin / policy | G-reports release status | Any other group |
|---|---|---|---|---|---|---|---|
| Orchestrator (0) | — (no domain group) | — | — | W | — | — | — |
| 1 Market Data | W (`G-market`) | — | — | — | — | — | — |
| 2 Company Discovery | W (`G-universe`) | — | — | — | — | — | — |
| 3 Historical Research | W (`G-history`) | — | — | — | — | — | — |
| 4 Financial Statement | W (`G-statements`) | — | — | — | — | — | — |
| 5 Fundamental | W (`G-analysis`, own sub-group) | — | — | — | — | — | — |
| 6 Technical | W (`G-analysis`, own sub-group) | — | — | — | — | — | — |
| 7 Sector | W (`G-analysis`, own sub-group) | — | — | — | — | — | — |
| 8 News Intelligence | W (`G-news`) | — | — | — | — | — | — |
| 9 Macroeconomic | W (`G-macro`) | — | — | — | — | — | — |
| 10 Valuation | W (`G-valuation`) | — | — | — | — | — | — |
| 11 Statistical Forecasting | W (`G-forecast`) | — | — | — | — | — | — |
| 12 AI Forecasting | W (`G-synthesis`) | — | — | — | — | — | — |
| 13 Risk Management | W (`G-risk`) | — | — | — | — | — | — |
| 14 Investment Decision | W (`G-recommend` content, `PENDING` only) | **W — SOLE content writer** | — (cannot set CLEARED/FLAGGED/BLOCKED) | — | — | — | — |
| 15 Portfolio Optimization | W (`G-portfolio`) | — | — | — | — | — | — |
| 16 Independent Audit | W (`G-audit`) | — (never content/label/rationale/evidence) | **W — SOLE status writer** (`CLEARED`/`FLAGGED`/`BLOCKED` + reasons) | — | — | — | — |
| 17 Report Generation | W (`G-reports`, draft only) | — | — | — | — | — (release only after final audit pass confirms verbatim rendering; Agent 17 writes `DRAFT`, the orchestrator marks `RELEASED` on Audit's verdict) | — |
| 18 Monitoring & Recovery | W (`G-health`) | — | — | — | — | — | — |
| Human admin | — (no domain group via agent path) | — | — | — (does not dispatch) | W (approvals, budgets, limits, blocks, requeue-as-new-task authorisations) | — | — |

**Recommendation rule, stated once and binding on every row:**

- **ONLY Investment Decision (Agent 14) proposes** BUY/HOLD/SELL/WATCHLIST
  content, and only in state `PENDING`.
- **ONLY Independent Audit (Agent 16) can block or flag** a recommendation,
  by setting its audit status with reasons. Audit cannot change the label,
  rationale, or evidence — a substance change requires a new Agent 14 version.
- **Every other row — including the orchestrator, Report Generation, Portfolio
  Optimization, AI Forecasting, and the human admin acting through the agent
  path — has NO write access to recommendations.** Report Generation renders
  them verbatim; Portfolio Optimization's weights are a different group and a
  different thing (see registry entries 14 vs 15).

## 5. Tools matrix

| Row | Python stdlib | Deterministic functions (own catalogue area only) | Ollama local open-weight inference | Any paid LLM API / subscription / API key | Market-data libraries (`psx-dps`/`psxdata` via scaffold) | Queue/context write tools | Dispatch / requeue tools |
|---|---|---|---|---|---|---|---|
| Orchestrator (0) | Yes | No (does not compute) | No | **No** | No | Yes (`G-queue`) | Yes (dispatch; requeue only as new task on human approval) |
| 1 Market Data | Yes | No numeric computation beyond stamping/provenance | No | **No** | **Yes — sole user, via scaffold only** | Own group only | No |
| 2 Company Discovery | Yes | Deduplication/identity logic only | No | **No** | No | Own group only | No |
| 3 Historical Research | Yes | Descriptive functions (via catalogue) | Yes (prose brief only) | **No** | No | Own group only | No |
| 4 Financial Statement | Yes | Transformation functions only where approved + logged | Yes (structuring prose only; numbers copied, never computed) | **No** | No | Own group only | No |
| 5 Fundamental | Yes | Fundamental functions | Yes | **No** | No | Own group only | No |
| 6 Technical | Yes | Indicator functions | Yes (signal readings only) | **No** | No | Own group only | No |
| 7 Sector | Yes | Aggregation functions | Yes | **No** | No | Own group only | No |
| 8 News Intelligence | Yes | None (no numbers from news) | Yes (tagging/summarising only) | **No** | No | Own group only | No |
| 9 Macroeconomic | Yes | Transformation functions only where approved + logged | Yes (context prose only) | **No** | No | Own group only | No |
| 10 Valuation | Yes | Valuation functions | Yes (limitations prose only) | **No** | No | Own group only | No |
| 11 Statistical Forecasting | Yes | Statistical/forecasting functions (catalogue owner) | No (numbers only; no LLM arithmetic) | **No** | No | Own group only | No |
| 12 AI Forecasting | Yes (quoting/checking) | No (must not compute; quotes Agent 11 logs only) | **Yes — main synthesis agent** | **No** | No | Own group only | No |
| 13 Risk Management | Yes | Risk functions | Yes (limit prose only) | **No** | No | Own group only | No |
| 14 Investment Decision | Yes | No (weighs logged outputs; does not recompute them) | Yes (rationale prose only) | **No** | No | Recommendation group (content, `PENDING`) | No |
| 15 Portfolio Optimization | Yes | Optimisation functions | Yes (limitations prose only) | **No** | No | Own group only | No |
| 16 Independent Audit | Yes | Function re-runner (same catalogue/versions) | Yes (verdict reasons prose only; verdicts are check outcomes) | **No** | No | Audit group + status field | No |
| 17 Report Generation | Yes | No | Yes (templating only; must not introduce numbers) | **No** | No | Report group (draft) | No |
| 18 Monitoring & Recovery | Yes | None | Yes (health-report prose only) | **No** | No | Health group only | **No — recommends only; never dispatches or requeues** |
| Human admin | — (oversight, not an agent tool user) | — | — | **No** | No | Admin group only | Approves (does not itself dispatch) |

**Tool rule:** a task claim naming a tool outside its row is rejected by the
orchestrator before dispatch (`E_PERMISSION`). In particular, a claim naming
a paid LLM tool, a broker tool, a payment tool, or a credential tool is
rejected as `E_FORBIDDEN_ACTION` and logged.

## 6. External network access — who has any, and who has none

| Access | Rows |
|---|---|
| **Approved external access (later-phase runs only; Phase 1 is read-only inspection, no full-scale collection)** | **Agent 1 ONLY**, and only through `psx-dps` / `psxdata` via the `psx-data-collection` scaffold's rules. No direct endpoint, scraper, or broker feed. |
| **NO external network access in Phase 1 (and no approved external source in the specified system)** | Agents 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 — all of them. Agents 8 and 9 in particular have no approved feed/source to call: news feeds and SECP/SBP/PBS/Finance Division/World Bank/IMF/FRED are UNVERIFIED (§2). |
| **NO external network access (by design)** | Orchestrator (routes by reference; fetches nothing) and human admin acting through the agent path (approvals are local messages, not external calls). |

Any external call by a "NO" row, or any call by Agent 1 outside the scaffold /
verified libraries, is `E_PERMISSION` (or `E_UNVERIFIED_SOURCE` where the source
is unverified, or `E_FORBIDDEN_ACTION` where it is a paid/broker/payment call)
and is blocked before it is made where the orchestrator can intercept it, or
flagged + dead-lettered where it is detected after the fact.

## 7. Approval gates — what needs a human decision before it happens

| Gate | Approver | Applies to |
|---|---|---|
| New job / job type | Human admin | Any run start; the orchestrator dispatches nothing without an approved job. |
| New data source (including verifying a currently UNVERIFIED source) | Human admin | Agents 1, 4, 8, 9 in particular; no agent self-approves a source. |
| New agent, schema, permission, or registry version | Human admin (+ matrix review) | Any registry/spec/matrix change. |
| Raised budget / limit (local-inference budget, concurrency, timeout, queue depth) | Human admin | Orchestrator enforcement values; agents cannot raise their own limits. |
| Release of a `BLOCKED` item | Human admin, only after remediation (new version by owning agent + new audit) | Any blocked recommendation, forecast, or report. Audit alone does not "unblock" by editing. |
| Dead-letter requeue | Human admin, as a NEW task id | Any dead-lettered task. The orchestrator never silently retries a dead letter. |
| Run pause / abort / resume | Human admin | Any run, at any time. Agents cannot override a pause/abort. |
| Report `RELEASED` | Final audit pass (Agent 16) + orchestrator marking (not Agent 17 alone) | Every report. See §4. |
| Record deletion (if ever) | Human admin, logged | Any shared-context record. No agent deletes. |
| **No gate waived by standing instruction** | — | A standing "send without review" style instruction, if ever given for another workflow, does NOT transfer to this system and does NOT waive a system approval gate here. Gates above are enforced by the orchestrator regardless of chat wording. |

**No per-email / per-artefact review in chat is defined here** — this system has
no email-sending path in Phase 1 at all. Approval travels as a logged
`HUMAN_APPROVAL` message (§7 of the communication spec), not as an informal chat
assurance.

## 8. Trade execution — denied for every row (explicit, no exceptions)

| Row | Trade execution / order placement / broker connection / order routing |
|---|---|
| Orchestrator (0) | **DENIED** |
| Agents 1–18 (each) | **DENIED** |
| Human admin (through the agent path) | **DENIED** |

The system **must NOT execute real trades initially**, and in Phase 1 it must
not execute them at all. It produces **recommendations and reports only**.
There is no trade-execution tool, message type, permission, or approval gate
that could enable trading, because no such gate is defined — adding one would
be a new, separately approved design change outside Phase 1, and is not
authorised by this matrix, by silence, or by any agent's request. A
recommendation label (BUY/HOLD/SELL/WATCHLIST) is a probabilistic proposal with
uncertainty shown, not a trading instruction, and no row may convert it into
one.

## 9. Cost controls (PKR 0 — policy, not a purchased quota)

| Control | Rule |
|---|---|
| Project budget | **PKR 0 absolute.** No purchase, subscription, paid API, paid vendor, broker fee, or payment is authorised for any row. |
| Inference | **Ollama local open-weight only** for every row that uses inference (§5). No row may use, request, or fall back to a paid LLM API. |
| Local-inference budgets | Per-run and per-agent budgets set by the human admin before a run, recorded in the run record, enforced by the orchestrator as a hard stop. Exhaustion → run paused + `BUDGET_EXHAUSTED` message; never an auto-purchase, never a silent downgrade to invented numbers. |
| Deterministic-first | A task computable by a deterministic function must not use inference (§5 of the architecture). The orchestrator rejects inference claims for computable tasks. |
| Concurrency / queue / attempts | Architecture §7 defaults (max 4 concurrent tasks per run, 1 concurrent run, max 3 attempts for retryable errors, queue-depth alert at 50). Agents cannot raise these. |
| Monitoring | The orchestrator logs counts + wall-clock time per run/agent; Agent 18 reports them. Reports show **PKR 0 project spend** and carry the disclosure that local hardware, electricity, and internet are **external operating expenses — never called free**. No currency figure beyond PKR 0 project spend may be reported without a human-approved price source, and in Phase 1 none exists. |
| Kill switch | Human admin pause/abort at any time (§7). Abort preserves completed records + audit logs and releases no partial output. |

## 10. Least-privilege defaults and change rules

1. **Default deny.** A permission not listed in §§3–6 is denied. An agent that
   needs a new permission requests it as a matrix change, not by using it.
2. **No privilege escalation by message.** No message from an agent can grant
   itself, another agent, or the orchestrator a permission. Only a human-approved
   matrix version change grants one.
3. **No self-audit, no self-release.** No agent audits its own output, clears
   its own flag, releases its own report, or requeues its own dead letter.
4. **Separation of proposal, audit, and rendering.** Agent 14 proposes,
   Agent 16 verdicts, Agent 17 renders, the orchestrator marks release on
   Audit's verdict. Collapsing any two of these into one row would violate
   this matrix and must be rejected as a design change, not adopted as a
   shortcut.
5. **UNVERIFIED stays denied until verified.** Verifying a source (e.g. a
   macro source or news feed) requires: a named source, a verification check
   recorded by the human admin, a matrix update naming the permitted agent(s),
   and a new matrix version. Until then, §2's fallback (skip with audit note)
   is the only permitted behaviour.
6. **Phase 1 boundary.** This matrix specifies permissions for the designed
   system. Exercising them at full scale, collecting live data at scale, or
   executing any trade is out of Phase 1. **STOP AFTER PHASE 1.**

## 11. Matrix version

- **Version:** Phase 1, 2026-11-04 (original + revised-brief merge, same day).
- **Change rule:** Any row, column, group, tool, external-access, or gate change
  is a matrix version change, requires a registry review, and requires
  human-admin approval. Runs stay pinned to the matrix version they were
  approved under.
