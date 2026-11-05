"""Phase 29 acceptance models: runs, scenarios, recomputations, defects.

Four tables, all owned by this phase (precedent: Phases 11-28 store
their own tables rather than retrofitting Phase 3 tables):

- ``acceptance_runs``: one row per acceptance invocation, keyed by a
  unique run_id (idempotency key: a second --commit with the same
  run_id writes nothing). Carries the run date, the overall verdict,
  and the gate evaluation JSON.
- ``acceptance_scenarios``: one row per (run, scenario): the outcome
  (pass / fail / blocked / not_evaluable), the evidence JSON, and
  the reason. A blocked scenario is not a system failure: the chain
  cannot complete for a stated external reason. A not_evaluable
  scenario means the system has no test data for that case in scope;
  it is recorded, not passed by default.
- ``acceptance_recomputations``: one row per (run, check): the claimed
  value, the independently recomputed value, whether they match
  within the stated tolerance, and the method. A mismatch row is
  kept, not deleted: it is the audit finding.
- ``acceptance_defects``: one row per (run, defect key): severity
  (critical / high / medium / low), lifecycle status (open / fixed /
  accepted), impact, and the exact unblocker or fix. ``accepted``
  means documented and consciously deferred with a stated trigger —
  it is not a silent pass.

These tables carry no quality_status: they are audit records, not
business data, and no quality-status promotion ever applies to them.
No order, execution, external-send, or publication concept exists in
these tables. No credentials are stored anywhere here.

ID deviation, deliberate (same reason as Phase 24 auth tables,
Phase 25 job tables, Phase 26 evaluation tables, and Phase 27
observability tables): these tables do NOT use ``IdMixin``.
``IdMixin`` uses ``Identity(always=True)`` (PostgreSQL-only) and a
BigInteger PK is not a rowid alias on SQLite, so inserts fail NOT
NULL there. The acceptance tables use a plain Integer primary key
with autoincrement — SERIAL on PostgreSQL, INTEGER rowid alias on
SQLite — so the same code runs on both. The migration matches this
exactly.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AcceptanceRun(Base):
    """One acceptance invocation."""

    __tablename__ = "acceptance_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    run_date: Mapped[object] = mapped_column(Date, nullable=False)
    verdict: Mapped[str] = mapped_column(String(30), nullable=False)
    gate_evaluation: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "verdict IN ('COMPLETE', 'PARTIALLY COMPLETE', 'BLOCKED', 'FAILED')",
            name="ck_acceptance_runs_verdict",
        ),
    )


class AcceptanceScenario(Base):
    """One end-to-end scenario result within a run."""

    __tablename__ = "acceptance_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(200), ForeignKey("acceptance_runs.run_id"), nullable=False
    )
    scenario_key: Mapped[str] = mapped_column(String(100), nullable=False)
    case_name: Mapped[str] = mapped_column(String(300), nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("run_id", "scenario_key", name="uq_acceptance_scenario_grain"),
        CheckConstraint(
            "outcome IN ('pass', 'fail', 'blocked', 'not_evaluable')",
            name="ck_acceptance_scenarios_outcome",
        ),
    )


class AcceptanceRecomputation(Base):
    """One independent recomputation within a run."""

    __tablename__ = "acceptance_recomputations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(200), ForeignKey("acceptance_runs.run_id"), nullable=False
    )
    check_key: Mapped[str] = mapped_column(String(100), nullable=False)
    claimed_value: Mapped[str] = mapped_column(Text, nullable=False)
    recomputed_value: Mapped[str] = mapped_column(Text, nullable=False)
    matches: Mapped[bool] = mapped_column(nullable=False)
    tolerance: Mapped[str] = mapped_column(String(200), nullable=False)
    method: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("run_id", "check_key", name="uq_acceptance_recomputation_grain"),
    )


class AcceptanceDefect(Base):
    """One defect-register entry within a run."""

    __tablename__ = "acceptance_defects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(200), ForeignKey("acceptance_runs.run_id"), nullable=False
    )
    defect_key: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    unblocker: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("run_id", "defect_key", name="uq_acceptance_defect_grain"),
        CheckConstraint(
            "severity IN ('critical', 'high', 'medium', 'low')",
            name="ck_acceptance_defects_severity",
        ),
        CheckConstraint(
            "status IN ('open', 'fixed', 'accepted')",
            name="ck_acceptance_defects_status",
        ),
    )
