# PSX Intelligence AI — Agent Communication Specification (Phase 1)

> **Team:** Team 5 — Multi-Agent Architecture
> **Phase:** Phase 1 of 30 — design only. No application code, no Phase 2 work.
> **Companion files:** `AGENT_ARCHITECTURE.md`, `AGENT_REGISTRY.md`,
> `AGENT_PERMISSION_MATRIX.md`. This spec governs messages; the registry governs
> what each agent may do; the permission matrix governs access.
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
> **NOT execute real trades initially** — no message type in this spec carries
> a trade order, and no agent may send or accept one; recommendations/reports
> only. **STOP AFTER PHASE 1.** Testing strategy is defined in
> `AGENT_ARCHITECTURE.md` §1A stage 8, not claimed passed — no test result is
> asserted by this spec.

## 0. Principles

1. **Messages are the only inter-agent communication.** Agents do not share
   memory, do not call each other directly, and do not read each other's
   working files. Everything an agent needs from another agent arrives as a
   message from the orchestrator, referencing shared-context records.
2. **Payloads by reference, never by large inline blob.** A message carries
   record ids + versions (`payload_refs[]`); the actual artefact lives once in
   the shared context. This keeps the message log small, replayable, and
   auditable, and prevents two copies of a number drifting apart.
3. **No number travels without its log.** A message that references a
   number-carrying artefact must reference its function log as well. A message
   that introduces a number in its own prose fields (outside a referenced log)
   is invalid and is rejected (see error `E_INVENTED_NUMBER`).
4. **No trade message exists.** There is no message type, envelope field, or
   payload schema for an order, execution, broker instruction, or trade
   confirmation in this spec. An agent that emits anything resembling one has
   violated the spec; the orchestrator rejects it and Audit flags it.
5. **No paid-LLM message exists.** No message may name, request, or route to a
   paid AI/LLM API or subscription service. Language-inference tasks name
   Ollama local inference only (see §7).
6. **Deterministic replay.** Given the same run id, task id, input refs, and
   schema/function versions, replaying the message log must reproduce the same
   task outcomes. Anything that breaks replay (an unnamed input, an unversioned
   function, a "latest" reference) is a spec violation.
7. **Human approval travels as a message too.** Approvals, blocks, pauses, and
   budget changes from the human admin are logged messages with the same
   envelope (sender `human_admin`), so no approval is ever "verbal" or
   off-the-record for audit purposes.

## 1. Message envelope — fields (all required unless marked optional)

Every message, of every type, carries this envelope. A message missing a
required field, or carrying an unknown field that changes meaning, is rejected
with `E_SCHEMA` before dispatch.

| Field | Type / format (logical) | Meaning and rules |
|---|---|---|
| `message_id` | Unique id, assigned once by the sender (orchestrator for dispatched tasks; agent for results; human admin for approvals) | Never reused. A redelivered message keeps its original `message_id`. |
| `message_type` | One of §2 | Determines which payload schema applies. Unknown type → `E_SCHEMA`. |
| `run_id` | Id of the approved job run | All messages in a run share it. A message without a run that the orchestrator has approved is rejected. |
| `task_id` | Id of the task this message concerns | For job-level messages (approval, pause), `task_id` may be `null` and `run_id` governs. |
| `idempotency_key` | Deterministic string — see §4 | Required on every task dispatch, result, and artefact publication. |
| `sender` | `orchestrator` \| agent id (`agent_01` … `agent_18`) \| `human_admin` | The actual sender, never impersonated. An agent may not send as the orchestrator or as another agent. |
| `recipient` | `orchestrator` \| agent id \| `human_admin` \| `all` (broadcast alerts only, §2) | Point-to-point by default. Broadcast is allowed only for alerts/pause messages. |
| `schema_version` | Semantic version string, e.g. `1.0.0` (pattern — the registry version in force for the run) | The version of the message + payload schemas in force. A receiver on a different version rejects with `E_VERSION_MISMATCH` rather than guessing. |
| `created_at_pkt` | Timestamp in Pakistan Time (PKT) | All times in this system are PKT. A message without a PKT timestamp, or with a timestamp in another zone without conversion, is rejected with `E_SCHEMA`. |
| `payload_refs[]` | List of `{ record_id, record_version }` in shared context | The artefacts this message is about. Empty only for control messages (pause/abort/approval) that name a run, not an artefact. |
| `payload_summary` | Short human-readable summary (no new numbers — see principle 3) | For logs and alerts. It must not introduce a number, label, or verdict that is not in a referenced record. |
| `function_log_refs[]` | List of function-log record ids (optional — required when `payload_refs[]` includes a number-carrying artefact) | Lets Audit verify numbers without re-reading whole artefacts. |
| `correlation_id` | Optional; the `message_id` of the message this one replies to | Preserves request/response pairing for audit. |
| `trace_id` | Optional; set by the orchestrator at run start, copied on every message in the run | Lets Monitoring (Agent 18) follow a run across agents without reading content. |

**Field-naming rule:** field names above are the contract. Renaming, adding a
meaning-changing field, or changing a field's meaning is a schema-version
change (§5), never a silent edit.

## 2. Message types

| Type | Sender → Recipient | Purpose |
|---|---|---|
| `TASK_DISPATCH` | orchestrator → agent | Assigns one task (task type from registry, input refs, idempotency key, deadline, budget allocation). The ONLY way an agent receives work. |
| `TASK_CLAIM` | agent → orchestrator | Agent accepts the dispatched task exclusively. A task claimed by one agent cannot be claimed by another until timeout/release. |
| `TASK_RESULT` | agent → orchestrator | Delivers a completed artefact (by ref) or reports failure (with error code, §6). Never carries a second, undisclosed artefact. |
| `TASK_PROGRESS` | agent → orchestrator | Optional heartbeat/progress note (no numbers, no partial artefact). Used only for long tasks; absence of progress does not fail a task before its timeout. |
| `TASK_RETRY` | orchestrator → agent | Re-dispatch after a retryable failure, with the same `idempotency_key` and incremented `attempt_count`. |
| `TASK_DEAD_LETTER` | orchestrator → `human_admin` (+ log) | Terminal failure notice: task id, error code, last input refs, attempt count. No downstream dispatch follows from it. |
| `AUDIT_REQUEST` | orchestrator → `agent_16` | Submits artefact refs for audit, with the checklist version. |
| `AUDIT_VERDICT` | `agent_16` → orchestrator | Per-artefact verdict (`CLEARED` / `FLAGGED` / `BLOCKED`) with reasons. The ONLY message that may set an audit status. |
| `REPORT_REQUEST` | orchestrator → `agent_17` | Asks for rendering of audited artefacts only (refs + audit report ref). A request naming a `BLOCKED` artefact as clean is rejected. |
| `HEALTH_REPORT` | `agent_18` → orchestrator + `human_admin` | Run-health summary / alert (counts, states, budget use — no currency, PKR 0 + external-expense disclosure). |
| `RECOVERY_RECOMMENDATION` | `agent_18` → `human_admin` | Recommends a recovery action. Advisory only; it dispatches nothing. |
| `HUMAN_APPROVAL` | `human_admin` → orchestrator | Approves a job, source, budget/limit change, dead-letter requeue (as a NEW task), or release of a remediated blocked item. |
| `HUMAN_BLOCK` | `human_admin` → orchestrator | Blocks/pauses/aborts a run or item. Effective immediately on receipt; in-flight tasks finish or abort per §3, but no new dispatch follows. |
| `RUN_PAUSE` / `RUN_ABORT` | orchestrator → `all` (broadcast) | Pause/abort notice. Agents stop claiming new tasks; running tasks are handled per §3. |
| `BUDGET_EXHAUSTED` | orchestrator → `human_admin` (+ log) | Local-inference budget for the run is exhausted; no further local-LLM dispatch in that run until a human decision. Never an auto-purchase trigger (there is nothing to purchase under PKR 0). |

**Forbidden message types (must never be defined or accepted):** any trade
order, execution, broker, payment, purchase, subscription, paid-API call, or
credential message. Receipt of one is `E_FORBIDDEN_ACTION` (see §6) and is
logged for the human admin.

## 3. Task lifecycle

```
                    ┌─────────────┐
                    │   (job      │
                    │   approved) │
                    └──────┬──────┘
                           │ TASK_DISPATCH
                           ▼
                     ┌───────────┐
                     │  queued   │◄──────────────────────────────┐
                     └─────┬─────┘                               │ claim timeout
                           │ TASK_CLAIM                          │ (once, then
                           ▼                                     │  counts as failed
                     ┌───────────┐                               │  attempt)
                     │  running  │───────────────────────────────┘
                     └─────┬─────┘
           ┌───────────────┼───────────────┬───────────────────┐
           │ TASK_RESULT   │ TASK_RESULT   │ timeout /         │ HUMAN_BLOCK /
           │ (success)     │ (retryable    │ retryable failure │ RUN_ABORT
           ▼               │  failure)     │ (attempts left)   ▼
     ┌───────────┐         ▼               ▼             ┌───────────┐
     │ completed │      ┌──────┐        ┌──────┐         │  aborted  │
     └─────┬─────┘      │ retry│───────►│queued│         └───────────┘
           │            └──────┘        └──────┘         (terminal for
           │                               ▲  ▲             the run;
           │                               │  │             completed records
           │            non-retryable     │  │             + audit logs
           │            failure, or       │  │             preserved)
           │            attempts exhausted│  │             ┌───────────┐
           │                               │  └─────────────┤ dead-letter│
           └───────────────────────────────┴────────────────└───────────┘
                                                     (terminal for that
                                                      attempt; requeue only
                                                      as a NEW task on
                                                      HUMAN_APPROVAL)
```

State rules:

- `queued`: task exists, inputs named, not yet claimed. Only the orchestrator
  moves a task out of `queued`.
- `running`: exactly one agent holds the claim. The claim has a deadline
  (task timeout, registry/architecture §7). Expiry without a result returns the
  task to `queued` once (claim-timeout path above); a second expiry counts as a
  failed attempt.
- `completed`: a `TASK_RESULT` with artefact refs was accepted (schema-valid,
  permission-valid, function logs present where required). `completed` is
  final for that task id — a later correction is a new task/version, never an
  edit to the completed record.
- `failed` (transient state in the log, not a resting state): a result
  reporting failure. The orchestrator immediately routes it to `retry` or
  `dead-letter` per §6 — a task does not rest in `failed`.
- `retry`: orchestrator re-dispatch (`TASK_RETRY`) with the same
  `idempotency_key`, incremented `attempt_count`, and (where the error allows)
  the same input refs. Max attempts: 3 total (initial + 2 retries) for
  retryable errors; 1 for non-retryable errors (which go straight to
  dead-letter).
- `dead-letter`: terminal for that attempt. Its error code, input refs, and
  attempt history are preserved. No downstream task may consume a dead-lettered
  task's partial output (there is none — partial outputs are not published).
  Requeue requires `HUMAN_APPROVAL` and creates a NEW task id (so history is
  never rewritten).
- `aborted`: run-level terminal state on `RUN_ABORT`. Completed records and
  audit logs survive; queued/running tasks in that run do not silently complete
  afterwards.
- **Pause:** `RUN_PAUSE` freezes dispatch. Running tasks may finish and publish
  (their results are still audited); no new task is claimed until resume on
  human approval. Pause never releases a partial or unaudited output.

## 4. Idempotency keys

- **Construction (deterministic, no randomness, no wall-clock):**
  `idempotency_key = hash(run_id + "|" + task_type + "|" + agent_id + "|" + sorted_input_refs_with_versions + "|" + schema_version)`
  where `hash` is a deterministic hash function available in the Python
  standard library (the exact function is a Phase 2 implementation choice
  within stdlib; the key property — same inputs → same key — is fixed here).
  The key deliberately excludes timestamps, attempt counts, and message ids,
  so a retry carries the same key as the original.
- **Effect:** on receiving a `TASK_RESULT` (or artefact publication) whose
  `idempotency_key` already has a `completed` record, the orchestrator returns
  the existing record and discards the duplicate — it does not create a second
  artefact, a second recommendation, or a second report. On a retry, the agent
  re-delivers under the same key; if the first attempt had in fact completed
  but its result message was lost, the retry resolves to the original record.
- **Scope:** one key covers one task (one agent, one task type, one input set).
  Changing any input version creates a different key and therefore a different
  (new) task — which is correct, because the computation is genuinely different.
- **Audit:** the key is logged on dispatch, result, and publication. A result
  without a key, or with a key that does not match its dispatch, is rejected
  with `E_IDEMPOTENCY_MISMATCH`.

## 5. Shared-context rules

1. **Immutability:** a published shared-context record is never edited. A
   correction is a new record version that references the superseded version.
2. **Versioned reads:** a task's input refs name exact record versions. An
   agent must not substitute "latest" for a named version, and the orchestrator
   must not dispatch a task whose input refs are unversioned.
3. **Write-once per task:** an agent publishes at most one output record per
   task (idempotent re-delivery returns the existing record, §4). It writes
   only to its own output group (permission matrix), except Agent 16's
   audit-status field (see matrix).
4. **Provenance on every record:** `source + method + as_of_pkt` (for data) or
   `input_refs + function_log_refs` (for derived artefacts). A record without
   provenance is not dispatchable downstream.
5. **No cross-talk:** agents never write to, or read from, each other's private
   working state. If Agent A needs something from Agent B, it arrives as a
   dispatched task result via the orchestrator, by reference.
6. **Retention:** records feeding a released report/recommendation are retained
   with provenance (retention period set by the human admin — see architecture
   §3.3). Deletion, if ever approved, is a logged human-admin action only.

## 6. Versioning

- **Message + payload schemas:** semantic versioning (`MAJOR.MINOR.PATCH`
  pattern). `MAJOR` = breaking change (renamed/removed field, changed meaning);
  `MINOR` = additive, backward-compatible field; `PATCH` = clarification with
  no field change.
- **Run pinning:** a run is pinned to the schema version + registry version +
  function-catalogue versions it was approved under. Mid-run upgrades are not
  permitted; a new version applies to new runs only (or to a remediated
  re-run approved as a new run).
- **Function versions:** a deterministic function reference without a version
  is invalid. A function change creates a new version; old outputs keep their
  old version and remain reproducible.
- **Mismatch handling:** a receiver that sees a `schema_version` it does not
  implement rejects with `E_VERSION_MISMATCH` and does not attempt to interpret
  the message. The orchestrator, on such a rejection, dead-letters the task
  (version errors are non-retryable — retrying the same bytes cannot fix them)
  and alerts the human admin.
- **Registry changes:** any registry change (agent, schema, permission,
  frequency) bumps the registry version and requires a permission-matrix review
  + human approval before any run uses it.

## 7. Error taxonomy

`retryable` = the orchestrator may retry (up to max attempts). `non-retryable`
= dead-letter (or audit verdict, where noted). No other error codes may be
invented per incident; an unlisted failure is reported as `E_UNKNOWN` with its
full context logged, and the human admin classifies it — agents do not invent a
code to make a failure look retryable.

| Code | Meaning | Retryable? | Handling |
|---|---|---|---|
| `E_SCHEMA` | Message/payload fails its schema (missing/unknown field, wrong type, non-PKT time, unversioned ref) | No | Dead-letter; fix is a corrected dispatch (new task), not a retry. |
| `E_VERSION_MISMATCH` | Schema/registry/function version not implemented by receiver, or version missing | No | Dead-letter + human alert. |
| `E_PERMISSION` | Sender lacks permission for the requested read/write/action (see matrix) | No | Dead-letter + audit log. Never retried into permission. |
| `E_FORBIDDEN_ACTION` | Trade order/execution, broker, payment, purchase, paid-API, or credential action attempted or messaged | No | Dead-letter + audit flag + human alert. The action is not performed. |
| `E_MISSING_INPUT` | A named input ref does not exist (or is not `completed`) | No | Dead-letter; re-dispatch with a valid ref is a new task. |
| `E_UNVERIFIED_SOURCE` | Task requires fetching/using an UNVERIFIED source (SECP/SBP/PBS/Finance Division/World Bank/IMF/FRED, unverified news feed, unverified filing source, paid vendor) | No | Refused, not retried. Agent outputs a skip-with-audit-note record where its registry entry defines one (Agents 4, 8, 9); otherwise dead-letter. |
| `E_INVENTED_NUMBER` | A number in prose or output has no function log, or a quoted number does not match its log | No | Dead-letter + audit flag. Fix is a new deterministic run (Agent 11 or owning agent), never a prose edit. |
| `E_FUNCTION_ERROR` | A deterministic function failed on the given inputs (e.g. zero denominator from a stated figure, insufficient window) | Yes, with input check* | Up to 2 retries after checking inputs; if inputs are the cause, the output records the limitation instead of retrying forever. |
| `E_TRANSIENT_SOURCE` | Verified source temporarily unavailable (e.g. the `psx-dps` multi-node 404 quirk on a retryable node) | Yes | Up to 2 retries; then partial/failure per the scaffold's stale/conflict rules, with gaps recorded. |
| `E_TIMEOUT` | Task exceeded its timeout (claim or execution) | Yes (once as claim return, then as failed attempt) | See §3 claim-timeout rule; then up to max attempts. |
| `E_AUDIT_BLOCK` | Artefact or input is audit-`BLOCKED` and cannot proceed as clean | No | Held/dead-letter per the artefact; remediation is a new version/task by the owning agent + new audit. |
| `E_BUDGET_EXHAUSTED` | Run's local-inference budget exhausted | No (pause, not retry) | Run paused; `BUDGET_EXHAUSTED` to human admin. No auto-purchase (PKR 0). Resume only on human decision (new budget or narrowed scope, as a new/continued run per human approval). |
| `E_UNKNOWN` | Unlisted failure | No | Logged in full, dead-lettered, classified by the human admin. |

\* `E_FUNCTION_ERROR` retry note: a retry is useful only if the failure was
transient (e.g. a transient compute fault). If the same inputs fail the same
function twice, the second failure is treated as an input limitation and the
task completes with that limitation recorded (where the registry allows) rather
than consuming a third attempt on identical inputs.

## 8. Inference routing (Ollama local only)

- A task that needs language inference names `inference: ollama_local` in its
  dispatch. It never names a vendor, model-as-a-service, API endpoint, or API
  key. (No specific local model is named or endorsed in Phase 1 — model
  selection is a later-phase, human-approved choice, and must remain an
  open-weight local model to preserve the PKR 0 rule.)
- The orchestrator enforces the run's local-inference budget (§7 of the
  architecture): when exhausted, it stops dispatching inference tasks and emits
  `BUDGET_EXHAUSTED`. It never falls back to a paid service.
- Deterministic-function tasks never route through inference. An agent that
  routes a computable task through inference has mis-dispatched it; the
  orchestrator rejects the claim.

## 9. Worked example flows

Notation: `O` = orchestrator, `A<n>` = Agent n, `H` = human admin, `→` = one
message (type in brackets). Input/output refs are abbreviated (`M1`, `U1`, …)
for readability; in a real run they are full record ids + versions. No external
API, endpoint, price, or figure is invented in these examples — values are
shown as refs, not as numbers.

### 9.1 Market-data refresh (later-phase behaviour, specified — NOT executed at scale in Phase 1)

Phase 1 note: this flow is specified here so a later phase can implement it.
In Phase 1 itself, data work is read-only inspection only (architecture §1A
stage 4); no full-scale refresh is run.

```
H → O  [HUMAN_APPROVAL]  approve job J (refresh, symbols = approved universe, freshness window W)
O → A1 [TASK_DISPATCH]  task T1, inputs: universe_ref U0, date_range, source_preference,
                        idempotency_key K1, deadline, budget (no inference)
A1 → O [TASK_CLAIM]     T1 claimed exclusively
A1 → O [TASK_RESULT]   success, payload_refs: [M1 (market_data_batch)], function_log_refs: []
                        (retrieval has no computed numbers; provenance + as_of_pkt + gaps in M1)
O → A2 [TASK_DISPATCH]  task T2, inputs: [M1], idempotency_key K2
A2 → O [TASK_RESULT]   success, payload_refs: [U1 (universe_version)]
O → A16 [AUDIT_REQUEST] artefacts [M1, U1], checklist vX
A16 → O [AUDIT_VERDICT] M1: CLEARED, U1: CLEARED (provenance + coverage checks pass)
O → A18 [TASK_DISPATCH] health report for run J (implicit: Monitoring observes O's records)
A18 → O/H [HEALTH_REPORT] tasks_by_state, budget_use (PKR 0, local counts only)
```

Failure variant: if A1's retrieval is `PARTIAL` (e.g. a symbol hit the
multi-node 404 quirk), M1 still publishes with `retrieval_status=PARTIAL` and
per-symbol gap notes; downstream tasks proceed only per job J's approved
stale/partial rule, and A18's health report lists the gaps. No symbol is
backfilled by invention.

### 9.2 Company analysis (single symbol, later-phase run)

```
H → O  [HUMAN_APPROVAL]  job J: analyse symbol S (universe U1, batches [M1], docs supplied D1)
O → A3 [TASK_DISPATCH]  historical brief for S over [M1]
O → A4 [TASK_DISPATCH]  statement record for S from D1 (operator-supplied only)
A3 → O [TASK_RESULT]   brief H1 (descriptive stats via logged functions)
A4 → O [TASK_RESULT]   statement record F1, OR gap record if D1 absent (skip + audit note;
                        SECP fetch would be E_UNVERIFIED_SOURCE, refused, not retried)
O → A5 [TASK_DISPATCH]  fundamental assessment, inputs [H1, F1]
O → A6 [TASK_DISPATCH]  technical assessment, inputs [M1]  (parallel with A5 — different owners)
A5 → O [TASK_RESULT]   assessment FA1 (ratios via logged functions)
A6 → O [TASK_RESULT]   assessment TA1 (indicators via logged functions)
O → A7 [TASK_DISPATCH]  sector assessment, inputs [U1, M1]
O → A10 [TASK_DISPATCH] valuation, inputs [FA1, TA1, M1]
A7 → O [TASK_RESULT]   sector assessment SE1
A10 → O [TASK_RESULT]  valuation V1 (functions logged)
O → A16 [AUDIT_REQUEST] [H1, F1, FA1, TA1, SE1, V1]
A16 → O [AUDIT_VERDICT] all CLEARED (or any FAIL → that artefact BLOCKED, held from downstream)
```

Note the ordering rule: A5/A6 run in parallel only because they have different
owners and disjoint inputs; A10 waits for FA1. No agent reorders this on its own.

### 9.3 Forecast run (statistical → AI synthesis → dual validation)

```
H → O  [HUMAN_APPROVAL]  job J: forecast symbol S, horizons [1d, 1w, 1m, 3m, 6m, 12m]
O → A11 [TASK_DISPATCH] forecast, inputs [M1, H1], horizons as approved, functions named
A11 → O [TASK_RESULT]  forecast FC1 (per-horizon function logs; no prose numbers beyond logs)
O → A12 [TASK_DISPATCH] synthesis, inputs [FC1] (+ words-only context refs as approved)
                        inference: ollama_local (only inference routing in this flow)
A12 → O [TASK_RESULT]  synthesis SY1, quoted_numbers[] each citing FC1 log refs,
                        no_new_numbers_attestation = true (a claim, not proof)
O → A11 [TASK_DISPATCH] validation check: confirm SY1.quoted_numbers[] == FC1 logs
       (routed via O so A12 is not validated by itself; A11 checks numbers only, not prose quality)
A11 → O [TASK_RESULT]  validation: MATCH (or MISMATCH → SY1 BLOCKED, see below)
O → A16 [AUDIT_REQUEST] [FC1, SY1] + validation result
A16 → O [AUDIT_VERDICT] FC1: CLEARED (functions re-run, outputs match);
                        SY1: CLEARED (prose contains no unlogged number) — or BLOCKED on any mismatch
O → A14 [TASK_DISPATCH] decision, inputs [FA1, V1, FC1, SY1 (only if CLEARED), RA1]
       (RA1 = risk assessment from A13, dispatched in parallel with the forecast flow)
```

Failure variant: if SY1 quotes a number not in FC1's log (including a rounded
restatement that differs from the logged form), validation step 1 and/or the
audit both fail with `E_INVENTED_NUMBER`; SY1 is `BLOCKED` and never reaches
A14 or a report. The fix is a new A11 run (new task, new forecast record) if a
different number is genuinely needed — never a prose edit to SY1.

### 9.4 Recommendation audit (proposal → verdict → report, with block path)

```
O → A14 [TASK_DISPATCH] decision, inputs [FA1, V1, FC1, SY1(CLEARED), RA1]
A14 → O [TASK_RESULT]  recommendation R1, label from {BUY,HOLD,SELL,WATCHLIST},
                        audit_status = PENDING (A14 cannot set any other status)
O → A16 [AUDIT_REQUEST] [R1 + all evidence refs + function logs]
A16 → O [AUDIT_VERDICT] R1: CLEARED  →  O → A17 [REPORT_REQUEST] render [R1, ...] with audit ref
                        R1: FLAGGED (reasons) → O → A17 renders R1 WITH flags shown verbatim
                        R1: BLOCKED (reasons + remediation) → O does NOT dispatch to A17 as clean;
                          H notified; remediation = new A14 task (new version) + new audit
A17 → O [TASK_RESULT]  report draft RP1 (verbatim rendering, flags/limitations/uncertainty shown,
                        PKR 0 / Ollama-local disclosure + no-trade statement included)
O → A16 [AUDIT_REQUEST] final pass: RP1 matches its sources verbatim?
A16 → O [AUDIT_VERDICT] RP1: CLEARED → O marks RP1 RELEASED
                        RP1: BLOCKED on mismatch → re-render as new version, re-audit
A18 → O/H [HEALTH_REPORT] run summary (including any blocks, retries, budget use)
```

In every path above, no message carries a trade order, no agent other than A14
writes recommendation content, and no agent other than A16 sets an audit status.
A report is `RELEASED` only after the final audit pass — never by Report
Generation alone.

## 10. What this spec does NOT define (deferred, not silently assumed)

- Physical transport (stdlib files / `sqlite3` in Phase 1 logic; any later
  broker is a transport adapter change with human approval — the envelope and
  lifecycle above do not change).
- Specific local Ollama model names (human-approved later-phase choice;
  open-weight local only, PKR 0 preserved).
- Specific paid services, endpoints, or vendor schemas (none approved; none
  may be added by a message).
- Retention periods, budget numbers, timeout seconds beyond the architecture's
  policy defaults, and backoff intervals (human-admin policy values, recorded
  in the run record when set).

## 11. Spec version

- **Version:** Phase 1, 2026-11-04 (original + revised-brief merge, same day).
- **Change rule:** Any envelope-field, message-type, lifecycle, idempotency,
  versioning, or error-taxonomy change is a spec version change, requires a
  registry + permission-matrix review, and requires human-admin approval.
  Runs stay pinned to the version they were approved under.
