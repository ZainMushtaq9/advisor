"""Phase 15 investment decision and recommendation engine models.

Three tables. Design rules from the Phase 15 brief:

- Three levels are kept distinct and never collapsed: a SCREENING
  outcome (mechanical data-availability and freshness check), a
  RESEARCH conclusion (BUY_CANDIDATE / HOLD_CANDIDATE /
  SELL_CANDIDATE / WATCHLIST / INSUFFICIENT_EVIDENCE from the
  versioned rule set), and a USER-FACING recommendation, which is
  issued only when a research conclusion exists AND confidence is
  at least MEDIUM. In this run every user-facing value is WITHHELD:
  all inputs are UNVERIFIED, calibration is NOT_ESTABLISHED (Phase
  13 abstained on every target), and technical evidence is absent
  for every company — so no confidence above LOW is reachable.
- A proposal is never generated from an abstained forecast or a
  NOT_CALCULABLE input as if it were computed. Forecasts are not a
  decision dimension at all in rules v1: Phase 13 abstained, so
  forecast evidence contributes nothing, and that absence is
  recorded in every decision's evidence snapshot.
- Every decision carries its evidence snapshot (input row
  references, values, as-of and publication dates, rule version),
  its conflicts (preserved unresolved disagreements, never hidden
  by averaging), and its gate reasons, so any historical decision
  can be reconstructed exactly.
- No look-ahead: evidence with a publication or event date after
  the decision date is excluded by the runner, and a NULL
  publication date on valuation inputs is a blocking gate (the
  no-look-ahead check cannot be verified).
- No execution path exists anywhere in this project. These tables
  store research opinions only; there is no broker, order, or
  execution concept in the model, the services, or the API, and a
  test in this phase scans the codebase to prove it.
- Outcomes are recorded only when a later observation arrives
  with an as-of date after the decision date; nothing is
  backfilled. The outcomes table holds 0 rows until then.

Quality vocabulary mirrors migration 20261104_0003.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin, ProvenanceMixin, VersionMixin


class DecisionRule(IdMixin, CreatedMixin, Base):
    """One versioned decision rule set.

    ``dimensions`` maps each of the seven dimensions to its scoring
    rule; ``weights`` are equal (1 each) in v1 — weighting is a
    future version, not an invented number. ``thresholds`` holds the
    conclusion mapping; ``gates`` holds the blocking gates;
    ``precedence`` documents evidence precedence for conflict
    resolution (selection precedence, not score overriding:
    conflicts are preserved, never averaged away).
    """

    __tablename__ = "decision_rules"
    __table_args__ = (UniqueConstraint("version", name="uq_decision_rules_version"),)

    version: Mapped[str] = mapped_column(String(50), nullable=False)
    dimensions: Mapped[dict] = mapped_column(JSON, nullable=False)
    weights: Mapped[dict] = mapped_column(JSON, nullable=False)
    thresholds: Mapped[dict] = mapped_column(JSON, nullable=False)
    gates: Mapped[dict] = mapped_column(JSON, nullable=False)
    precedence: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence_rules: Mapped[dict] = mapped_column(JSON, nullable=False)


class Decision(IdMixin, CreatedMixin, ProvenanceMixin, VersionMixin, Base):
    """One decision for one company on one decision date.

    ``screening_outcome`` is SCREEN_PASS / SCREEN_FAIL /
    SCREEN_NOT_RUNNABLE. ``research_conclusion`` is BUY_CANDIDATE /
    HOLD_CANDIDATE / SELL_CANDIDATE / WATCHLIST /
    INSUFFICIENT_EVIDENCE. ``user_facing`` is WITHHELD unless a
    research conclusion exists and confidence is at least MEDIUM,
    in which case it mirrors the research conclusion.
    ``confidence`` is LOW / MEDIUM / HIGH / NONE (NONE when no
    conclusion exists). ``total_score`` is the sum of scored
    dimensions (ABSENT dimensions excluded); ``scored_dimensions``
    counts them. ``evidence_snapshot`` holds input row references
    with values and dates; ``conflicts`` holds preserved unresolved
    disagreements; ``gate_reasons`` holds blocking gates, empty
    when the conclusion was reached on the merits.
    """

    __tablename__ = "decisions"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "decision_date",
            "rules_version",
            name="uq_decisions_grain",
        ),
        Index("ix_decisions_company", "company_id"),
    )

    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="SET NULL"), nullable=True
    )
    decision_date: Mapped[object] = mapped_column(Date, nullable=False)
    rules_version: Mapped[str] = mapped_column(String(50), nullable=False)
    screening_outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    research_conclusion: Mapped[str] = mapped_column(String(30), nullable=False)
    user_facing: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    total_score: Mapped[object] = mapped_column(Numeric(10, 4), nullable=True)
    scored_dimensions: Mapped[int] = mapped_column(BigInteger, nullable=False)
    completeness: Mapped[object] = mapped_column(Numeric(10, 4), nullable=True)
    evidence_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    conflicts: Mapped[dict] = mapped_column(JSON, nullable=False)
    gate_reasons: Mapped[dict] = mapped_column(JSON, nullable=False)


class DecisionOutcome(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One observed outcome subsequent to a decision.

    Recorded only when a later observation arrives with an as-of
    date after the decision date. ``outcome_type`` names what was
    observed (e.g. later_close, later_statement); ``value`` is the
    observed value. This table holds 0 rows until such an
    observation exists; nothing is backfilled or estimated.
    """

    __tablename__ = "decision_outcomes"
    __table_args__ = (
        UniqueConstraint(
            "decision_id",
            "outcome_type",
            "outcome_date",
            name="uq_decision_outcomes_grain",
        ),
        Index("ix_decision_outcomes_decision", "decision_id"),
    )

    decision_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False
    )
    outcome_date: Mapped[object] = mapped_column(Date, nullable=False)
    outcome_type: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
