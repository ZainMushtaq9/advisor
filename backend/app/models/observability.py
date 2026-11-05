"""Phase 27 observability models: SLO definitions and measurements,
source health, exception queue, incident reports, observability
runs, and performance baselines.

Seven tables, all owned by this phase (precedent: Phases 11-26 store
their own tables rather than retrofitting Phase 3 tables):

- ``observability_runs``: one row per observability invocation,
  keyed by a unique run_id (idempotency key: a second --commit
  with the same run_id writes nothing).
- ``observability_slo_definitions``: measurable freshness and
  completeness targets BY SOURCE CATEGORY, not one universal
  threshold (brief requirement). Each definition states its
  category, metric, target, comparison direction, and rationale.
- ``observability_slo_measurements``: one row per (run, SLO):
  the value (NULL when not evaluable), the status (met / unmet /
  not_evaluable), the exact reason, and evidence JSON. An
  unmet SLO is a stored fact, never hidden and never averaged
  away.
- ``observability_source_health``: one row per (run, source):
  latest observation date, coverage numerator/denominator,
  freshness in days, and a status (fresh / stale / unknown)
  against that source's own threshold.
- ``observability_exceptions``: the exception queue — one row per
  (run, exception): severity, title, evidence, and lifecycle
  status (open / acknowledged / resolved). A resolved exception
  carries a resolution note; nothing is silently deleted.
- ``observability_incidents``: incident reports with severity,
  evidence, runbook reference, and lifecycle status. Historical
  incidents (VM replacements, push disconnect) are recorded as
  resolved with their evidence, not rewritten as successes.
- ``observability_performance``: baseline probes — one row per
  (run, probe): API latency samples, database query timings,
  and storage sizes. Single samples are labelled as such;
  no percentile is claimed from a single sample.

These tables carry no quality_status: they are operational
records, not business data, and no quality-status promotion
ever applies to them. No order, execution, external-send, or
publication concept exists in these tables. No credentials are
stored anywhere here. No log text is stored here either —
structured logs go to stdout/stderr, never to the database.

ID deviation, deliberate (same reason as Phase 24 auth tables,
Phase 25 job tables, and Phase 26 evaluation tables): these
tables do NOT use ``IdMixin``. ``IdMixin`` uses
``Identity(always=True)`` (PostgreSQL-only) and a BigInteger PK
is not a rowid alias on SQLite, so inserts fail NOT NULL there.
The observability tables use a plain Integer primary key with
autoincrement — SERIAL on PostgreSQL, INTEGER rowid alias on
SQLite — so the same code runs on both. The migration matches
this exactly.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin

SLO_COMPARISONS = ("ge", "le", "eq")
MEASUREMENT_STATUSES = ("met", "unmet", "not_evaluable")
SOURCE_HEALTH_STATUSES = ("fresh", "stale", "unknown")
EXCEPTION_SEVERITIES = ("info", "low", "medium", "high", "critical")
EXCEPTION_STATUSES = ("open", "acknowledged", "resolved")
INCIDENT_SEVERITIES = ("sev4", "sev3", "sev2", "sev1")
INCIDENT_STATUSES = ("open", "acknowledged", "resolved")
RUN_STATUSES = ("completed", "failed")


class ObservabilityRun(CreatedMixin, Base):
    """One observability invocation (idempotency key: run_id)."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "observability_runs"
    __table_args__ = (
        UniqueConstraint("run_id", name="uq_observability_runs_run_id"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in RUN_STATUSES)})",
            name="ck_observability_runs_status",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default="full")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    summary: Mapped[dict | None] = mapped_column(JSON)


class SloDefinition(CreatedMixin, Base):
    """One measurable SLO, defined per source category."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "observability_slo_definitions"
    __table_args__ = (
        UniqueConstraint("slo_key", name="uq_observability_slo_definitions_key"),
        CheckConstraint(
            f"comparison IN ({', '.join(repr(s) for s in SLO_COMPARISONS)})",
            name="ck_observability_slo_definitions_comparison",
        ),
    )

    slo_key: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    target_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=False)
    comparison: Mapped[str] = mapped_column(String(10), nullable=False)
    unit: Mapped[str] = mapped_column(String(100), nullable=False, default="ratio")
    rationale: Mapped[str] = mapped_column(String(1000), nullable=False)


class SloMeasurement(CreatedMixin, Base):
    """One SLO measurement within one run (value NULL = not evaluable)."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "observability_slo_measurements"
    __table_args__ = (
        UniqueConstraint("run_id", "slo_key", name="uq_observability_slo_measurements_grain"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in MEASUREMENT_STATUSES)})",
            name="ck_observability_slo_measurements_status",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    slo_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[object | None] = mapped_column(Numeric(24, 6), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON)


class SourceHealth(CreatedMixin, Base):
    """One source-health snapshot within one run."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "observability_source_health"
    __table_args__ = (
        UniqueConstraint("run_id", "source_key", name="uq_observability_source_health_grain"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in SOURCE_HEALTH_STATUSES)})",
            name="ck_observability_source_health_status",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_key: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    latest_observation_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    coverage_numerator: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coverage_denominator: Mapped[int | None] = mapped_column(Integer, nullable=True)
    freshness_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str] = mapped_column(String(1000), nullable=False)


class ObservabilityException(CreatedMixin, Base):
    """One exception-queue entry within one run."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "observability_exceptions"
    __table_args__ = (
        UniqueConstraint("run_id", "exception_key", name="uq_observability_exceptions_grain"),
        CheckConstraint(
            f"severity IN ({', '.join(repr(s) for s in EXCEPTION_SEVERITIES)})",
            name="ck_observability_exceptions_severity",
        ),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in EXCEPTION_STATUSES)})",
            name="ck_observability_exceptions_status",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    exception_key: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    resolution_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class ObservabilityIncident(CreatedMixin, Base):
    """One incident report (lifecycle status, never deleted)."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "observability_incidents"
    __table_args__ = (
        UniqueConstraint("incident_key", name="uq_observability_incidents_key"),
        CheckConstraint(
            f"severity IN ({', '.join(repr(s) for s in INCIDENT_SEVERITIES)})",
            name="ck_observability_incidents_severity",
        ),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in INCIDENT_STATUSES)})",
            name="ck_observability_incidents_status",
        ),
    )

    incident_key: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON)
    runbook_ref: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    resolution_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class PerformanceBaseline(CreatedMixin, Base):
    """One performance probe measurement within one run."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "observability_performance"
    __table_args__ = (
        UniqueConstraint("run_id", "probe_key", name="uq_observability_performance_grain"),
    )

    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    probe_key: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[object | None] = mapped_column(Numeric(24, 6), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str] = mapped_column(String(1000), nullable=False)
