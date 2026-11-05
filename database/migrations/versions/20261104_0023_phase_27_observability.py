"""phase_27_observability

Revision ID: 20261104_0023
Revises: 20261104_0022
Create Date: 2026-11-05

Phase 27 (observability, data quality operations, performance and
reliability) tables: observability_runs (one row per invocation,
unique run_id idempotency key), observability_slo_definitions
(measurable freshness/completeness targets BY SOURCE CATEGORY,
not one universal threshold), observability_slo_measurements
(value or NULL + status + reason + evidence; an unmet SLO is a
stored fact, never hidden or averaged away),
observability_source_health (latest observation, coverage,
freshness days, fresh/stale/unknown per source threshold),
observability_exceptions (the exception queue with lifecycle
status, never silently deleted), observability_incidents
(incident reports with severity, evidence, runbook reference,
lifecycle status), observability_performance (baseline probes:
API latency samples, database query timings, storage sizes;
single samples labelled as such, no percentile claimed from
one sample).

Precedent note (Phases 11-26): Phase 27 stores its own tables
rather than retrofitting Phase 3 tables. These tables carry no
quality_status: they are operational records, not business
data, and no quality-status promotion ever applies to them.
No order, execution, external-send, or publication concept
exists in these tables. No credentials are stored anywhere.
No log text is stored here — structured logs go to
stdout/stderr, never to the database.
Integer primary keys (not IdMixin Identity): see
backend/app/models/observability.py for the SQLite portability reason.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0023"
down_revision: str | None = "20261104_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _pk() -> sa.Column:
    return sa.Column(
        "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
    )


def _created() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


def upgrade() -> None:
    op.create_table(
        "observability_runs",
        _pk(),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False, server_default="full"),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="completed"
        ),
        sa.Column("summary", sa.JSON(), nullable=True),
        _created(),
        sa.UniqueConstraint("run_id", name="uq_observability_runs_run_id"),
        sa.CheckConstraint(
            "status IN ('completed', 'failed')",
            name="ck_observability_runs_status",
        ),
    )
    op.create_table(
        "observability_slo_definitions",
        _pk(),
        sa.Column("slo_key", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("metric_key", sa.String(length=100), nullable=False),
        sa.Column("target_value", sa.Numeric(24, 6), nullable=False),
        sa.Column("comparison", sa.String(length=10), nullable=False),
        sa.Column("unit", sa.String(length=100), nullable=False, server_default="ratio"),
        sa.Column("rationale", sa.String(length=1000), nullable=False),
        _created(),
        sa.UniqueConstraint("slo_key", name="uq_observability_slo_definitions_key"),
        sa.CheckConstraint(
            "comparison IN ('ge', 'le', 'eq')",
            name="ck_observability_slo_definitions_comparison",
        ),
    )
    op.create_table(
        "observability_slo_measurements",
        _pk(),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("slo_key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Numeric(24, 6), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        _created(),
        sa.UniqueConstraint(
            "run_id", "slo_key", name="uq_observability_slo_measurements_grain"
        ),
        sa.CheckConstraint(
            "status IN ('met', 'unmet', 'not_evaluable')",
            name="ck_observability_slo_measurements_status",
        ),
    )
    op.create_table(
        "observability_source_health",
        _pk(),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("latest_observation_date", sa.Date(), nullable=True),
        sa.Column("coverage_numerator", sa.Integer(), nullable=True),
        sa.Column("coverage_denominator", sa.Integer(), nullable=True),
        sa.Column("freshness_days", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=False),
        _created(),
        sa.UniqueConstraint(
            "run_id", "source_key", name="uq_observability_source_health_grain"
        ),
        sa.CheckConstraint(
            "status IN ('fresh', 'stale', 'unknown')",
            name="ck_observability_source_health_status",
        ),
    )
    op.create_table(
        "observability_exceptions",
        _pk(),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("exception_key", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("resolution_note", sa.String(length=1000), nullable=True),
        _created(),
        sa.UniqueConstraint(
            "run_id", "exception_key", name="uq_observability_exceptions_grain"
        ),
        sa.CheckConstraint(
            "severity IN ('info', 'low', 'medium', 'high', 'critical')",
            name="ck_observability_exceptions_severity",
        ),
        sa.CheckConstraint(
            "status IN ('open', 'acknowledged', 'resolved')",
            name="ck_observability_exceptions_status",
        ),
    )
    op.create_table(
        "observability_incidents",
        _pk(),
        sa.Column("incident_key", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("runbook_ref", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("resolution_note", sa.String(length=1000), nullable=True),
        _created(),
        sa.UniqueConstraint("incident_key", name="uq_observability_incidents_key"),
        sa.CheckConstraint(
            "severity IN ('sev4', 'sev3', 'sev2', 'sev1')",
            name="ck_observability_incidents_severity",
        ),
        sa.CheckConstraint(
            "status IN ('open', 'acknowledged', 'resolved')",
            name="ck_observability_incidents_status",
        ),
    )
    op.create_table(
        "observability_performance",
        _pk(),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("probe_key", sa.String(length=100), nullable=False),
        sa.Column("metric_key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Numeric(24, 6), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=False),
        _created(),
        sa.UniqueConstraint(
            "run_id", "probe_key", name="uq_observability_performance_grain"
        ),
    )


def downgrade() -> None:
    op.drop_table("observability_performance")
    op.drop_table("observability_incidents")
    op.drop_table("observability_exceptions")
    op.drop_table("observability_source_health")
    op.drop_table("observability_slo_measurements")
    op.drop_table("observability_slo_definitions")
    op.drop_table("observability_runs")
