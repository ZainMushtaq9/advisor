"""Phase 18 permission model: least privilege at the tool boundary.

The orchestrator enforces the tier at the tool-call boundary, not
inside an agent's prompt. Rules:

- A tool is permitted only if it is in the agent's allowed_tools
  AND its cost does not exceed the agent's cost envelope (PKR 0
  for every agent in this phase).
- Consequential tools (publish a record, change a verification
  status, send anything outside the system, write to staging)
  require a recorded human approval gate. No gate has been
  granted in this phase, so they are denied to every agent,
  including the audit agent: the audit agent may FLAG, never
  promote.
- There is no order tool in the vocabulary at all, so no
  permission can ever grant one.
- Approval gates are explicit: ``grant_approval`` records a
  gate in memory only for the calling process (it is NOT
  persisted and NOT used by the runner); the runner always runs
  with zero granted gates, which is what makes consequential
  tools denied in production. Tests may grant a gate in-process
  to prove the gate mechanism itself works, without persisting
  any approval.
"""

from __future__ import annotations

from app.services.orchestration import (
    AGENT_REGISTRY,
    CONSEQUENTIAL_TOOLS,
    TIER_CONSEQUENTIAL,
)

_AGENT_BY_NAME = {a["name"]: a for a in AGENT_REGISTRY}

# In-process approval gates only. Never persisted, never loaded
# from disk, never granted by the runner. A test may add a gate
# to prove the mechanism; production runs with an empty set.
_granted_gates: set[str] = set()


def grant_approval(gate: str) -> None:
    """Record an in-process approval gate (tests only)."""
    _granted_gates.add(gate)


def revoke_all_approvals() -> None:
    """Clear all in-process approval gates."""
    _granted_gates.clear()


def agent_contract(agent_name: str) -> dict:
    """Return the registry contract for an agent, or raise."""
    contract = _AGENT_BY_NAME.get(agent_name)
    if contract is None:
        raise ValueError(f"unknown agent: {agent_name}")
    return contract


def check_tool_permission(agent_name: str, tool: str, cost_pkr: int = 0) -> tuple[bool, str]:
    """Decide whether an agent may call a tool.

    Returns (allowed, reason). Denials are fail-closed: unknown
    agents, unknown tools, over-envelope costs, and ungranted
    consequential tools are all denied with a reason.
    """
    try:
        contract = agent_contract(agent_name)
    except ValueError:
        return False, "unknown_agent"
    if tool not in contract["allowed_tools"]:
        if tool in CONSEQUENTIAL_TOOLS:
            return False, "consequential_tool_requires_approval_gate"
        return False, "tool_not_in_allowed_tools"
    if cost_pkr > contract["cost_envelope_pkr"]:
        return False, "cost_exceeds_envelope"
    if contract["permissions_tier"] == TIER_CONSEQUENTIAL and tool in CONSEQUENTIAL_TOOLS:
        gate = f"{agent_name}:{tool}"
        if gate not in _granted_gates:
            return False, "consequential_tool_requires_approval_gate"
    return True, "allowed"


def check_write_to_protected(agent_name: str, table: str) -> tuple[bool, str]:
    """Decide whether an agent may write to a table.

    Protected tables are every financial, market, registry, and
    verification table. Only orchestration/audit tables may be
    written, and only by ORCHESTRATION_WRITE agents. Financial
    tables are never writable by any agent in this phase.
    """
    contract = agent_contract(agent_name)
    if table.startswith(("agent_", "orchestration_")):
        if contract["permissions_tier"] == "ORCHESTRATION_WRITE":
            return True, "allowed"
        return False, "read_only_agent_may_not_write"
    return False, "protected_table_never_writable_by_agent"


def check_timeout(elapsed_seconds: float, timeout_seconds: int) -> tuple[bool, str]:
    """Cooperative timeout check between checkpoints.

    The runtime cannot preemptively kill a step; it checks
    elapsed time at each checkpoint and fails the task with
    TIMEOUT when the budget is exceeded. Documented limitation.
    """
    if elapsed_seconds > timeout_seconds:
        return False, "timeout_exceeded"
    return True, "within_timeout"
