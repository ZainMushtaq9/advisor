# Phase 18 Run Report — 2026-11-04

## Verdict: PARTIALLY COMPLETE

The orchestration runtime, agent registry, permission model, untrusted-data
controls, task ledger, evaluation, and audit logs are complete and verified
end to end. It is not COMPLETE because LLM-backed execution is unavailable
(no verified local model), live agent work beyond the demo graph has not
run, and wider-company coverage and HBL statements remain pending inputs.

## Demo run: `phase18-demo-graph`

- Run status: COMPLETED (5 tasks COMPLETED + 1 QUARANTINED probe; the
  quarantine is a successful control outcome, not a failure).
- Tasks: `discover` COMPLETED (3 companies with stored statements),
  `statements_check` COMPLETED (88 statements),
  `fundamentals_summary` COMPLETED (108 fundamental value rows),
  `injection_probe` QUARANTINED (input carried an injected instruction to
  override the HUBC close; classified, quarantined, stored row untouched),
  `flaky_tool` COMPLETED (attempt 3 of max_retries 3; retries recorded),
  `audit_report` COMPLETED (deterministic values verified unchanged).
- Deterministic check: stored HUBC close 197.2400 before the probe and
  197.2400 after it — unchanged. Claimed close 200.00 quarantined as a
  mismatch.
- Evaluations (6/6 PASS): prompt_injection, tool_failure,
  loop_termination, duplicate_action, hallucinated_value,
  deterministic_authority.
- Idempotency: second `--commit` wrote 0 new rows (16 agents, 1 run,
  6 tasks, 6 audit logs, 6 evaluations on first commit).

## DB counts (live, verified)

- Before: 0 Phase 18 rows; migration head 20261104_0014.
- After: +16 agent_definitions, +1 orchestration_run, +6
  orchestration_tasks, +6 agent_audit_logs, +6 agent_evaluations.
  Migration head 20261104_0015.
- Untouched: statements 88, prices 444, decisions 4, and all prior
  phase rows. No agent wrote any financial, market, registry, or
  verification row.

## Tests and live checks

- New tests: 12 passed (pure: registry, permissions, untrusted data,
  graph, validation, evaluation, timeout, no-execution scan, GET-only).
- Full backend suite: 272 passed, 0 failed (260 prior + 12 new).
- Ruff check + format clean on all new/changed app files. The migration
  carries the same boilerplate import finding as prior migrations
  (established migration style, not fixed).
- Live API: agents 200 (16), runs 200 (1), evaluations 200 (6), status
  200, run detail 200 (COMPLETED, 6 tasks, 6 logs, 6 evaluations),
  unknown run 404.

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has no orchestration
task output beyond the demo graph's registry reads: its CY2025 statements
are not loaded (PDF blocked at download; live-browser download runs
separately). A Phase 7 load plus a Phase 18 re-run adds HBL's evidence
without redesign; the banking rule (no industrial ratios blindly applied)
carries forward.

## Remaining blockers (exact unblockers)

1. **LLM-backed execution** — a verified local/open-weight model on this
   host, plus licence and quality checks against the rule-based fallback.
2. **Live agent work beyond the demo graph** — real task graphs routed
   through the runtime once agents beyond fallback mode are verified.
3. **HBL coverage** — live-browser HBL CY2025 PDF download, then a Phase 7
   load, then a Phase 18 re-run.
4. **Wider-company coverage** — Phase 7 expansion beyond the 3-company
   sample (per-company source verification pass).
5. **VERIFIED promotion** — H1 second agreeing source including an official
   source; everything stays UNVERIFIED until then. (Promotion itself also
   needs a recorded human approval gate, which has not been granted.)
6. **Preemptive timeouts** — cooperative timeout checks only; preemptive
   enforcement would need a process-based executor (a design decision, not
   a data blocker).
