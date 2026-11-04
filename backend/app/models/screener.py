"""Phase 20 market screener and opportunity discovery models.

Three tables. Design rules from the Phase 20 brief:

- A screen definition is a versioned, reusable filter set: name,
  version, filter list (JSON), logic (AND of all filters, with
  scoring over the filters that could be evaluated), universe
  scope, and as-of discipline. Re-running the same definition
  version at the same as-of date reproduces identical results:
  results are keyed by (run, security), never overwritten.
- A screen run records the universe size, matched count, and
  status for one (definition, as-of date) pair. Runs are
  idempotent: a second commit of the same pair writes nothing.
- A screen result is one universe member's outcome: matched /
  no_match / insufficient_data, explainable score
  (passed / scored), per-filter outcomes with values, source
  row references, quality, and reason codes. A missing value
  is stored as a reason, never as a substituted number. A
  result is NEVER labelled a guaranteed investment
  opportunity, a recommendation, or a forecast: Phase 15
  user-facing values are WITHHELD and Phase 13 forecasts are
  abstained, and the screener does not reintroduce either —
  decision context rides along as evidence only, never as a
  score input.
- Quality vocabulary mirrors migration 20261104_0003. A screen
  result never upgrades a statement, price, calculation,
  decision, or verification row.
- No order path exists anywhere in this project, and none is
  added here: screening is read-only filtering over stored
  rows plus stored results.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScreenDefinition(Base):
    __tablename__ = "screen_definitions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    universe: Mapped[str] = mapped_column(String(50), nullable=False)
    filters: Mapped[object] = mapped_column(JSON, nullable=False)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_screen_definitions_name_version"),
        CheckConstraint(
            "quality_status IN ('VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','CONFLICTED',"
            "'MISSING','REJECTED','STALE','PENDING_REVIEW')",
            name="ck_screen_definitions_quality_status",
        ),
    )


class ScreenRun(Base):
    __tablename__ = "screen_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    screen_definition_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("screen_definitions.id"), nullable=False
    )
    as_of_date: Mapped[object] = mapped_column(Date, nullable=False)
    universe_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    matched_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    insufficient_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    evidence: Mapped[object] = mapped_column(JSON, nullable=True)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")

    __table_args__ = (
        UniqueConstraint(
            "screen_definition_id", "as_of_date", name="uq_screen_runs_definition_asof"
        ),
        CheckConstraint(
            "quality_status IN ('VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','CONFLICTED',"
            "'MISSING','REJECTED','STALE','PENDING_REVIEW')",
            name="ck_screen_runs_quality_status",
        ),
        Index("ix_screen_runs_definition", "screen_definition_id"),
    )


class ScreenResult(Base):
    __tablename__ = "screen_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    screen_run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("screen_runs.id"), nullable=False
    )
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id"), nullable=False
    )
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[object | None] = mapped_column(Numeric(10, 4), nullable=True)
    passed_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    scored_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason_codes: Mapped[object] = mapped_column(JSON, nullable=False)
    evidence: Mapped[object] = mapped_column(JSON, nullable=False)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")

    __table_args__ = (
        UniqueConstraint("screen_run_id", "security_id", name="uq_screen_results_run_security"),
        CheckConstraint(
            "outcome IN ('MATCH','NO_MATCH','INSUFFICIENT_DATA')",
            name="ck_screen_results_outcome",
        ),
        CheckConstraint(
            "quality_status IN ('VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','CONFLICTED',"
            "'MISSING','REJECTED','STALE','PENDING_REVIEW')",
            name="ck_screen_results_quality_status",
        ),
        Index("ix_screen_results_run", "screen_run_id"),
    )
