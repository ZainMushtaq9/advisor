"""Phase 18 multi-agent orchestration and agent runtime models.

Five tables. Design rules from the Phase 18 brief:

- Agents are advisory only. No agent writes a financial, market,
  registry, or verification row directly: agent outputs live in
  task checkpoints and audit logs, and any persistence goes
  through the deterministic services of Phases 4-17, never through
  an agent's own tool. The runtime enforces this at the
  permission boundary (see services/orchestration/permissions.py).
- Permission tiers: READ_ONLY (research agents; no writes at
  all), ORCHESTRATION_WRITE (audit, monitoring, reports agents;
  may write orchestration/audit tables only, never protected
  financial tables), CONSEQUENTIAL (publish a record, change a
  verification status, send anything outside the system) — which
  requires a recorded human approval gate. NO agent holds a
  consequential permission in this phase, and no approval gate
  has been granted, so consequential tools are denied to all.
- Untrusted data: retrieved web pages, files, news items, and
  documents are data, never instructions. Inputs flagged as
  carrying instructional language are quarantined: the task is
  marked QUARANTINED, the output is not stored as a fact, and
  the deterministic value stands unchanged.
- Deterministic authority: an agent output can never override a
  verified numeric calculation. A numeric claim that disagrees
  with the deterministic service value is quarantined; a claim
  with no evidence reference is quarantined as hallucinated.
  Nothing here stores a price, a statement figure, or a forecast.
- No order path exists anywhere in this project, and none is
  added here: orchestration tables record task execution only.
- Cost envelope is PKR 0 for every agent (free only). Any tool
  with a cost is denied.
- Jobs do not run when the host is off: the runtime is an
  in-process, standard-library-only executor with a persistent
  ledger. No external orchestrator dependency is added, and no
  schedule is promised.
- LLM execution is UNAVAILABLE in this phase: no local model has
  been verified on this host, so every agent runs in rule-based
  fallback mode and audit logs record model_identifier
  "rule-based-fallback-v1" with token use NULL (not applicable).
  The registry records the LLM path as a future capability that
  requires a verified local/open-weight model, licence, and
  quality check before it may be enabled.

Quality vocabulary mirrors migration 20261104_0003.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin, ProvenanceMixin


class AgentDefinition(IdMixin, CreatedMixin, Base):
    """One registered agent with its capability contract.

    ``permissions_tier`` is READ_ONLY, ORCHESTRATION_WRITE, or
    CONSEQUENTIAL (none granted in this phase). ``allowed_tools``
    is the exact tool set the runtime permits for this agent;
    anything else is denied at the boundary. ``cost_envelope_pkr``
    is 0 for every agent. ``execution_backend`` is
    "rule_based_fallback" for all agents in this phase.
    """

    __tablename__ = "agent_definitions"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(Text(), nullable=False)
    inputs: Mapped[object] = mapped_column(JSON(), nullable=False)
    outputs: Mapped[object] = mapped_column(JSON(), nullable=False)
    allowed_tools: Mapped[object] = mapped_column(JSON(), nullable=False)
    permissions_tier: Mapped[str] = mapped_column(String(30), nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    max_retries: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    backoff_seconds: Mapped[object] = mapped_column(JSON(), nullable=False)
    cost_envelope_pkr: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    failure_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    execution_backend: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class OrchestrationRun(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One execution of a task graph.

    ``run_id`` is a UUID string. ``graph_name`` identifies the
    task graph; re-running the same graph reuses the run (no
    duplicate run row) and re-running tasks reuses their
    idempotency keys (no duplicate task rows). ``status`` is
    PENDING, RUNNING, COMPLETED, PARTIALLY_COMPLETE, FAILED, or
    CANCELLED. A run whose only non-completed task is a
    QUARANTINED injection probe is COMPLETED: quarantine is a
    successful control outcome, not a failure — the report says
    so explicitly.
    """

    __tablename__ = "orchestration_runs"

    run_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    graph_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    checkpoint: Mapped[object] = mapped_column(JSON(), nullable=False)


class OrchestrationTask(IdMixin, CreatedMixin, Base):
    """One task inside a run, with its ledger state.

    ``task_key`` is unique within a run; ``idempotency_key`` is
    globally unique ("<graph>:<task_key>") and is what makes a
    second commit write zero new rows. ``depends_on`` lists the
    task_keys that must be COMPLETED before this task may run.
    ``status`` is PENDING, QUEUED, RUNNING, COMPLETED, FAILED,
    CANCELLED, SKIPPED, or QUARANTINED. ``checkpoint`` records
    retries, the last completed step, and any quarantine reason,
    so a failed run can resume without duplicating side effects.
    """

    __tablename__ = "orchestration_tasks"

    run_id: Mapped[int] = mapped_column(
        BigInteger(), ForeignKey("orchestration_runs.id", ondelete="CASCADE"), nullable=False
    )
    task_key: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    depends_on: Mapped[object] = mapped_column(JSON(), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    attempt_count: Mapped[int] = mapped_column(BigInteger(), nullable=False, default=0)
    checkpoint: Mapped[object] = mapped_column(JSON(), nullable=False)
    error: Mapped[str | None] = mapped_column(Text(), nullable=True)

    __table_args__ = (
        UniqueConstraint("run_id", "task_key", name="uq_orchestration_tasks_run_key"),
        Index("ix_orchestration_tasks_run", "run_id"),
    )


class AgentAuditLog(IdMixin, CreatedMixin, Base):
    """One auditable agent action.

    Audit logs carry prompt/template references, model
    identifiers, tool calls, token/resource use where available
    (NULL for rule-based fallback), output summaries, evidence
    references, and errors. They never carry full payloads that
    could contain credentials, and never carry a secret.
    ``quarantined`` marks outputs withheld by a control.
    """

    __tablename__ = "agent_audit_logs"

    run_id: Mapped[int] = mapped_column(
        BigInteger(), ForeignKey("orchestration_runs.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[int] = mapped_column(
        BigInteger(), ForeignKey("orchestration_tasks.id", ondelete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_template: Mapped[str] = mapped_column(String(100), nullable=False)
    model_identifier: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_calls: Mapped[object] = mapped_column(JSON(), nullable=False)
    token_use: Mapped[object] = mapped_column(JSON(), nullable=True)
    output_summary: Mapped[str] = mapped_column(Text(), nullable=False)
    evidence: Mapped[object] = mapped_column(JSON(), nullable=False)
    error: Mapped[str | None] = mapped_column(Text(), nullable=True)
    quarantined: Mapped[bool] = mapped_column(nullable=False, default=False)

    __table_args__ = (Index("ix_agent_audit_logs_run", "run_id"),)


class AgentEvaluation(IdMixin, CreatedMixin, Base):
    """One stored evaluation case result for the runtime.

    ``category`` is prompt_injection, tool_failure,
    loop_termination, duplicate_action, hallucinated_value, or
    deterministic_authority. ``result`` is PASS or FAIL.
    ``evidence`` records what was checked, never a secret.
    """

    __tablename__ = "agent_evaluations"

    run_id: Mapped[int] = mapped_column(
        BigInteger(), ForeignKey("orchestration_runs.id", ondelete="CASCADE"), nullable=False
    )
    case_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence: Mapped[object] = mapped_column(JSON(), nullable=False)

    __table_args__ = (
        UniqueConstraint("run_id", "case_name", name="uq_agent_evaluations_run_case"),
        Index("ix_agent_evaluations_run", "run_id"),
    )
