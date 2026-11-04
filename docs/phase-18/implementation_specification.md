# Phase 18 Implementation Specification — Multi-Agent Orchestration and Agent Runtime

## Objective (brief, playbook lines 1388–1447)

Coordinate specialized research agents reliably while keeping deterministic
financial services authoritative and all agent actions auditable.

## What was built

| Component | Location | Purpose |
|---|---|---|
| Agent registry | `backend/app/services/orchestration/__init__.py` | 16 capability contracts |
| Permission model | `backend/app/services/orchestration/permissions.py` | Least-privilege tool boundary |
| Untrusted-data controls | `backend/app/services/orchestration/untrusted.py` | Instruction classification + quarantine |
| Task graph | `backend/app/services/orchestration/graph.py` | DAG scheduling, transitions, cancellation |
| Deterministic authority | `backend/app/services/orchestration/validation.py` | Numeric-claim validation |
| Evaluation cases | `backend/app/services/orchestration/evaluation.py` | 6 pure evaluation functions |
| Runner | `backend/app/services/orchestration/runner.py` | Demo graph execution, ledger, audit |
| Models | `backend/app/models/orchestration.py` | 5 tables (migration 20261104_0015) |
| API (GET-only) | `backend/app/api/v1/endpoints/orchestration.py` | agents, runs, tasks, audit, evaluations, status |
| CLI | `scripts/run_orchestration.py` | `--dry-run` default / `--commit` |
| Tests | `backend/tests/test_orchestration_phase18.py` | 12 pure tests |

## Design decisions

1. **Agents are advisory only.** No worker writes a financial, market,
   registry, or verification row. Outputs live in task checkpoints and audit
   logs; persistence goes through the deterministic services of Phases 4–17.
2. **16 workers + orchestrator + router = 18.** The brief names 16 worker
   roles; the Phase 1 spec spoke of 18 agents. The reconciliation is recorded
   here: the orchestrator (supervisor) and router are runtime functions, not
   worker agents, so the persisted registry holds exactly the 16 brief roles.
3. **No consequential permission is granted.** Publish, quality-status change,
   external send, and staging-write tools require a recorded human approval
   gate. None has been granted in this phase, so they are denied to every
   agent, including the audit agent (which may FLAG, never promote).
4. **No order path exists.** The tool vocabulary deliberately contains no
   order concept, and a test scans application source for order-execution
   identifiers (0 hits) and asserts the orchestration endpoint is GET-only.
5. **LLM execution unavailable.** No local model has been verified on this
   host, so every agent runs in rule-based fallback mode
   (`rule-based-fallback-v1`, token use NULL). The LLM path is a future
   capability requiring a verified local/open-weight model, licence, and
   quality check.
6. **Jobs do not run when the host is off.** The runtime is in-process and
   standard-library only, with a persistent ledger. No external orchestrator
   dependency was added, and no schedule is promised.
7. **Timeouts are cooperative.** The runner checks elapsed time between
   checkpoints; it cannot preemptively kill a step. Documented limitation.

## Demo graph (stored rows only)

`phase18-demo-graph`, 6 tasks in dependency order:

1. `discover` (company_discovery) — companies with stored statements.
2. `statements_check` (statements) — stored statement count.
3. `fundamentals_summary` (fundamentals) — stored fundamental value count.
4. `injection_probe` (monitoring) — control probe; input carries an injected
   instruction to override the HUBC close; classified and QUARANTINED.
5. `flaky_tool` (monitoring) — simulated tool fails twice, succeeds on
   attempt 3 within max_retries 3; checkpoint records retries.
6. `audit_report` (audit) — runs when dependencies are terminal (it exists
   to verify values after a quarantine); verifies stored values unchanged.

Run status is COMPLETED when every task is terminal and every non-probe task
completed. The quarantined probe is a successful control outcome, recorded
explicitly — not a failure. Any genuinely FAILED task would make the run
PARTIALLY_COMPLETE instead.

## Acceptance gate (brief) — verdict per item

- **Every agent has bounded scope and permissions.** PASS — 16 contracts,
  each with scope, inputs, outputs, tools, tier, timeout, retries, cost
  envelope (PKR 0), failure mode; unit-tested.
- **Task execution is observable and recoverable.** PASS — task ledger with
  idempotency keys and checkpoints; recovery re-queues failed tasks without
  duplicating completed side effects; second `--commit` writes 0 new rows.
- **Prompt injection and tool failures are tested.** PASS — 6 evaluation
  categories stored; injection, tool failure, loop termination, duplicate
  action, hallucinated value, deterministic authority all PASS.
- **Agent output cannot override verified numeric calculations.** PASS —
  mismatch quarantines; the runner re-reads the stored HUBC close after the
  probe and the gate passes only if the row is unchanged.

## Verdict: PARTIALLY COMPLETE

The runtime, registry, permission model, controls, evaluation, and audit
logs are complete and verified. It is not COMPLETE because LLM-backed
execution is unavailable (no verified local model), live agent work beyond
the demo graph has not run, and wider-company coverage (Phase 7 expansion)
and HBL statements remain pending inputs. Nothing mandatory is claimed as
done that is not evidenced.
