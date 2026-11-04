"""Phase 18 task graph: scheduling, state transitions, cancellation.

A task graph is a DAG of task_keys with depends_on lists. The
runtime:

- topologically sorts tasks (Kahn's algorithm); a cycle is an
  error, never silently broken;
- runs a task only when every dependency is COMPLETED (a
  QUARANTINED dependency blocks its dependents: they are
  SKIPPED with a reason, except the audit task, which is
  designed to run after a quarantine and verifies the
  deterministic values — the runner handles that explicitly);
- moves tasks through PENDING -> QUEUED -> RUNNING ->
  COMPLETED / FAILED / QUARANTINED, with CANCELLED reachable
  from PENDING, QUEUED, or RUNNING (cooperative: a RUNNING
  task is cancelled at its next checkpoint; COMPLETED tasks are
  never un-completed);
- supports recovery: a failed run resumes from its checkpoint,
  re-running only non-terminal tasks, never duplicating the
  side effects of completed ones (idempotency keys enforce this
  at the database layer too).
"""

from __future__ import annotations

from app.services.orchestration import TASK_TERMINAL

# Allowed transitions. Anything else is rejected by transition().
_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "PENDING": ("QUEUED", "CANCELLED", "SKIPPED"),
    "QUEUED": ("RUNNING", "CANCELLED", "SKIPPED"),
    "RUNNING": ("COMPLETED", "FAILED", "CANCELLED", "QUARANTINED"),
    "COMPLETED": (),
    "FAILED": ("QUEUED",),  # recovery: re-queue a failed task
    "CANCELLED": (),
    "SKIPPED": (),
    "QUARANTINED": (),
}


def topological_order(tasks: list[dict]) -> list[str]:
    """Return task_keys in dependency order, or raise on a cycle.

    Unknown dependencies are an error, not an assumption: a task
    may not depend on a task_key that is not in the graph.
    """
    keys = {t["task_key"] for t in tasks}
    depends = {t["task_key"]: list(t.get("depends_on", [])) for t in tasks}
    for key, deps in depends.items():
        for dep in deps:
            if dep not in keys:
                raise ValueError(f"task {key} depends on unknown task {dep}")
    order: list[str] = []
    remaining = dict(depends)
    while remaining:
        ready = sorted(k for k, deps in remaining.items() if not deps)
        if not ready:
            raise ValueError(f"cycle detected among tasks: {sorted(remaining)}")
        for key in ready:
            order.append(key)
            del remaining[key]
        for deps in remaining.values():
            deps[:] = [d for d in deps if d not in ready]
    return order


def transition(current: str, target: str) -> str:
    """Validate a state transition, returning the target or raising."""
    allowed = _TRANSITIONS.get(current, ())
    if target not in allowed:
        raise ValueError(f"invalid task transition {current} -> {target}")
    return target


def is_terminal(status: str) -> bool:
    """Whether a task status is terminal (no further transitions)."""
    return status in TASK_TERMINAL


def ready_tasks(tasks: list[dict], statuses: dict[str, str]) -> list[str]:
    """Task_keys whose dependencies are all COMPLETED and which are PENDING.

    A QUARANTINED or FAILED dependency blocks its dependents;
    the runner SKIPs them with a reason instead of running them.
    """
    ready = []
    for task in tasks:
        key = task["task_key"]
        if statuses.get(key) != "PENDING":
            continue
        if all(statuses.get(d) == "COMPLETED" for d in task.get("depends_on", [])):
            ready.append(key)
    return ready


def blocked_tasks(tasks: list[dict], statuses: dict[str, str]) -> list[str]:
    """PENDING tasks blocked by a terminal non-COMPLETED dependency."""
    blocked = []
    for task in tasks:
        key = task["task_key"]
        if statuses.get(key) != "PENDING":
            continue
        deps = task.get("depends_on", [])
        if deps and any(
            statuses.get(d) in ("FAILED", "CANCELLED", "QUARANTINED", "SKIPPED") for d in deps
        ):
            blocked.append(key)
    return blocked


def cancel_tasks(statuses: dict[str, str]) -> dict[str, str]:
    """Cancel a run: non-terminal tasks become CANCELLED.

    COMPLETED, FAILED, QUARANTINED, and SKIPPED tasks are left
    exactly as they are — cancellation never rewrites history.
    Returns the new status map.
    """
    out = dict(statuses)
    for key, status in out.items():
        if status not in TASK_TERMINAL:
            out[key] = "CANCELLED"
    return out


def run_loop_guard(iterations: int, max_iterations: int) -> str:
    """Loop-termination guard for agent step loops.

    Returns "CONTINUE" while under the cap, else
    "LOOP_TERMINATED". A loop that never converges is failed
    closed, never allowed to run unbounded.
    """
    if iterations >= max_iterations:
        return "LOOP_TERMINATED"
    return "CONTINUE"
