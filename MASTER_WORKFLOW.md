# PSX Intelligence AI — Master Workflow (mandatory, all phases)

- **Date:** 2026-11-04 (Phase 1 revision)
- **Owner:** Team 1 (Repository Audit + Product Requirements) for Phase 1 documentation; the workflow itself binds every team and every task until formally superseded.
- **Budget rule:** PKR 0 absolute. No paid API, subscription, hosting, database, storage, monitoring, or AI/LLM subscription may be introduced by following this workflow. Local hardware / electricity / internet are EXTERNAL operating expenses — disclose them, never call them free. Do not assume permanent free hosting exists.
- **Trading rule:** The system must NOT execute real trades initially. No stage in this workflow authorises broker connection, order placement, or trade execution.
- **Stop rule:** STOP AFTER PHASE 1. Do not begin Phase 2 until the Phase 1 audit passes (see `NEXT_ACTIONS.md`).

## The 11 stages — never skip a stage

Every task, in Phase 1 and in later-phase planning, must pass through all 11 stages in order. A stage may conclude "not applicable, for this stated reason" — that is a recorded outcome, not a skip. An unrecorded stage is a skipped stage and fails audit.

| # | Stage | What happens | Phase 1 meaning (documentation phase) | Exit evidence required |
|---|---|---|---|---|
| 1 | **Brainstorm** | Generate options, framings, and scope candidates before committing. Record alternatives considered and why one was chosen or deferred. | Scope candidates for the 21 modules, audit angles, and constraint framings. | A short options note: what was considered, what was chosen, what was deferred and why. |
| 2 | **Research** | Read public pages, READMEs, registries, and prior documents. Cite sources with dates. Do not invent an API, endpoint, price, or capability. | Public README / portal reads already in the starting condition + scaffold registry; no new live collection. | Source list with date + what each source actually states (vs what was assumed). |
| 3 | **Validate** | Check each research claim against its source. Separate "source states it" from "we proved it by a run". Label anything unproven UNVERIFIED. | Starting-condition claims reused verbatim; scaffold README claims kept as README claims; regulator/statistics sources kept UNVERIFIED. | Validation table: claim → source → status (verified-as-stated / UNVERIFIED / contradicted). |
| 4 | **Data inspection** | Documentation + read-only inspection ONLY in Phase 1. Inspect existing files, registries, templates, and schemas. **NO full-scale live data collection in Phase 1.** No polling, no bulk download, no live feed connection. | Directory listings, scaffold file reads, `coverage.json` template inspection, toolchain checks. No live PSX fetch, no bulk collection. | Inspection log: what was inspected, by what read-only means, what was NOT collected and why. |
| 5 | **Architecture planning** | Place the work in the system: which module(s), layer(s), dependencies, and data flows it touches. Name what it does NOT touch. | Module mapping (21 modules), layer-gap checklist (see `REPOSITORY_AUDIT.md` §6.2), dependency statements per module. Architecture decisions themselves are deferred to the architecture team; Team 1 records touch-points, not final architecture. | Touch-point map + deferred-decision list. |
| 6 | **Implementation specification** | Write the spec a later builder could follow without guessing: purpose, inputs, outputs, rules, edge cases, failure modes, acceptance criteria. No application code in Phase 1 (tiny illustrative snippets inside specs only, if needed, clearly marked illustrative). | `PRODUCT_REQUIREMENTS.md` — one full spec per module. | A spec that names inputs, outputs, dependencies, security, testing, and acceptance criteria for the item. |
| 7 | **Documentation** | Write the durable record in the project folder, in the agreed file, with dates, labels, and cross-references. Documentation is a deliverable, not an afterthought. | This file set (audit, requirements, status, log, next actions, workflow, trackers). | The file exists at its agreed path, is internally consistent, and states its own limits. |
| 8 | **Testing strategy** | Define HOW future components WILL be tested: test types, fixtures, offline vs live-sample cases, pass criteria, and what must never be claimed before a run. **Do NOT claim future tests have passed.** In Phase 1, no project test suite exists and none is claimed. | Per-module "Testing" sections in `PRODUCT_REQUIREMENTS.md`: offline/fake-client tests, golden-file checks, stale/conflict cases, uncertainty-display checks. | A testing strategy per item, with explicit "not yet run" status. |
| 9 | **Independent audit** | A party other than the author checks the work against the brief, the budget, the constraints, and internal consistency. The author does not audit their own work as "passed". | Coordinator audit (see `NEXT_ACTIONS.md`): cross-document consistency, PKR 0 check, no-trades check, UNVERIFIED labelling check, sibling-file integrity check. | Audit record: findings, pass/fail per criterion, fix list. |
| 10 | **Correction** | Fix every audit finding, or record a dated, reasoned deferral for each unfixed item. Do not silently drop a finding. | Fix loop: edit the affected file(s), re-check consistency, update trackers. | Corrected files + a finding-by-finding disposition (fixed / deferred-with-reason). |
| 11 | **Checkpoint** | Freeze the state: record what is done, what is not done, what is blocked, and what the next step is. The checkpoint is the only authorised handoff to the next phase or task. | Phase 1 checkpoint = `PROJECT_STATUS.md` + `TASK_TRACKER.md` + `WORKFLOW_STAGE_TRACKER.md` at the end of Phase 1, stating: docs only, no code/DB/deployment, stop after Phase 1. | Signed checkpoint note (coordinator) stating the phase outcome and the next authorised step. No checkpoint, no Phase 2. |

## Rules that apply at every stage

1. **No stage skipping.** If a stage genuinely does not apply, write one sentence saying why and who agreed — that sentence is the stage record.
2. **No invented facts at any stage.** An endpoint, field, price, coverage number, licence, or capability that is not in a cited source is UNVERIFIED until a documented check proves it. Examples are labelled "illustrative example" and never presented as real data.
3. **PKR 0 at every stage.** If a stage's option requires payment, it is recorded as a blocked/approval-required option, not smuggled in as a default.
4. **Provenance at every stage that touches data.** Source, source timestamp (PKT, Asia/Karachi), collected-at timestamp, freshness, stale flag, raw-vs-processed separation, and conflict visibility — carried from the scaffold's rules into every data-touching spec.
5. **Probabilistic language at every stage that touches forecasts or recommendations.** No guaranteed price, return, or outcome. BUY / HOLD / SELL / WATCHLIST are probabilistic recommendations with uncertainty shown.
6. **No real trades at any stage.** Research, analysis, and recommendation are in scope for specification; execution is explicitly out of scope initially.
7. **Testing strategy ≠ test results.** Stage 8 writes the plan. A test is "passed" only after it has actually run and its output is recorded. Phase 1 claims no passed project tests.
8. **Audit independence.** Stage 9 must not be performed by the same team claiming completion. Team 1's own acceptance checklists (e.g. in `REPOSITORY_AUDIT.md` §10) are self-checks, not the independent audit.
9. **Correction is not optional.** A checkpoint (stage 11) that lists open audit findings without dispositions is incomplete.
10. **One sending / execution method at a time (general discipline).** Where a future design involves scheduled sends, jobs, or triggers, only one authorised mechanism may be active for a given set of items. Phase 1 specifies no such mechanism and authorises none.

## How Phase 1 used this workflow (summary)

See `WORKFLOW_STAGE_TRACKER.md` for the honest per-stage status. In short: stages 1–8 and documentation were completed by Team 1 for its own files; stage 9 (independent audit) is PENDING with the coordinator; stage 10 (correction) is PENDING on audit findings; stage 11 (checkpoint) is PENDING on audit pass. Team 1 does not claim stages 9–11 as complete.

## What this workflow does NOT do

- It does not approve spending, a paid service, a broker connection, or a trade.
- It does not approve starting Phase 2.
- It does not convert a document (architecture, database, formula, agent) into a working component.
- It does not upgrade an UNVERIFIED item to verified. Only a documented verification check (see `NEXT_ACTIONS.md` §4) does that, and the check itself must go through all 11 stages for its own scope.
