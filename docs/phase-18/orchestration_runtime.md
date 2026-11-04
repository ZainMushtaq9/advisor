# Phase 18 Orchestration Runtime

Implemented in `backend/app/services/orchestration/graph.py` and
`backend/app/services/orchestration/runner.py`.

## Task graph

- A graph is a DAG of task_keys with `depends_on` lists.
- Topological sort (Kahn's algorithm). A cycle is an error, never silently
  broken. An unknown dependency is an error, never an assumption.
- A task runs only when every dependency is COMPLETED — except the audit
  task, which runs when its dependencies are terminal, because it exists
  to verify values after a quarantine.
- A QUARANTINED or FAILED dependency blocks its dependents: they are
  SKIPPED with a recorded reason (except the audit task, above).

## State transitions

```
PENDING -> QUEUED -> RUNNING -> COMPLETED / FAILED / QUARANTINED
PENDING / QUEUED / RUNNING -> CANCELLED
FAILED -> QUEUED   (recovery re-queue)
```

COMPLETED, FAILED (until re-queued), CANCELLED, SKIPPED, and QUARANTINED
are terminal in their respective senses; cancellation never rewrites
history — COMPLETED tasks stay COMPLETED.

## Queue policy

In-process FIFO queue in topological order. No external queue dependency
was added: the Phase 2 Redis/Celery proof exists as a verified optional
transport, but the Phase 18 ledger runtime does not depend on it, so the
runtime has no new dependency and no host-off promise. Priority is
topological order; there is no preemption.

## Idempotency and recovery

- Run reuse by `graph_name`; task reuse by globally unique
  `idempotency_key` (`<graph>:<task_key>`); evaluation reuse by
  (`run_id`, `case_name`). A second `--commit` writes 0 new rows.
- Checkpoints record retries, the last completed step, and quarantine
  reasons. A failed run resumes from its checkpoint, re-running only
  non-terminal tasks, never duplicating completed side effects.
- Partial completion is a first-class outcome: a run with genuinely
  FAILED tasks is PARTIALLY_COMPLETE, with the failed tasks and reasons
  in the ledger.

## Cancellation

Cancelling a run marks every non-terminal task CANCELLED and leaves
terminal tasks exactly as they are. Cancellation of a RUNNING task is
cooperative (applied at its next checkpoint), matching the cooperative
timeout model.

## Loop termination

Agent step loops are capped at `MAX_LOOP_ITERATIONS = 10`. A loop that
never converges is terminated with LOOP_TERMINATED (fail closed), never
allowed to run unbounded. Iteration limits with human escalation apply to
any future LLM-backed step loop as well.
