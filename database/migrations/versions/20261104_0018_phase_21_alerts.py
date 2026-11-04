"""phase_21_alerts

Revision ID: 20261104_0018
Revises: 20261104_0017
Create Date: 2026-11-04

Phase 21 (alerts and event-driven monitoring) tables:
alert_rules (versioned trigger definitions), notification_
preferences (single local profile; in-app only), alerts (the
event ledger, deduplicated by dedup_key), alert_deliveries
(one attempt row per alert per channel), alert_runs (one
evaluation pass per rule, with suppression reasons).

Precedent note (Phases 11-20): Phase 21 stores its own tables
rather than retrofitting Phase 3 tables. No Phase 3 alert
table exists. Alerts notify about stored events only: they are
not investment opportunities, recommendations, or forecasts,
and no order or execution concept exists in these tables.
Delivery is in-app only: no email, SMS, push, or paid service
is introduced, and no external consent is recorded. No CSVs
or PDFs are committed by this migration. No credentials are
stored anywhere.

Quality vocabulary CHECK mirrors migration 20261104_0003.
created_at carries a server default (as in the Phase 20
migration); the ORM models do not declare it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0018"
down_revision: str | None = "20261104_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

QUALITY_VALUES = (
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "UNVERIFIED",
    "CONFLICTED",
    "MISSING",
    "REJECTED",
    "STALE",
    "PENDING_REVIEW",
)


def _qc(table: str) -> sa.CheckConstraint:
    values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
    return sa.CheckConstraint(
        f"quality_status IN ({values})", name=f"ck_{table}_quality_status"
    )


def _created() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.BigInteger(), nullable=False),
        _created(),
        sa.Column("rule_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("origin", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("trigger", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("max_event_age_days", sa.BigInteger(), nullable=False),
        sa.Column("daily_limit", sa.BigInteger(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_key", "version", name="uq_alert_rules_key_version"),
        sa.CheckConstraint(
            "origin IN ('OFFICIAL','DERIVED','MODEL_WARNING')",
            name="ck_alert_rules_origin",
        ),
        sa.CheckConstraint(
            "severity IN ('INFO','WARNING','CRITICAL','MAPPED')",
            name="ck_alert_rules_severity",
        ),
        _qc("alert_rules"),
    )
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.BigInteger(), nullable=False),
        _created(),
        sa.Column("profile", sa.String(length=100), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("external_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quiet_start", sa.Time(), nullable=True),
        sa.Column("quiet_end", sa.Time(), nullable=True),
        sa.Column("muted_rule_keys", sa.JSON(), nullable=False),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile", name="uq_notification_preferences_profile"),
        _qc("notification_preferences"),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        _created(),
        sa.Column("rule_id", sa.BigInteger(), nullable=False),
        sa.Column("subject_type", sa.String(length=50), nullable=False),
        sa.Column("ticker", sa.String(length=50), nullable=True),
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        sa.Column("sector", sa.String(length=200), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("origin", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("dedup_key", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="NEW"),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("muted_until", sa.Date(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["rule_id"], ["alert_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedup_key", name="uq_alerts_dedup_key"),
        sa.CheckConstraint(
            "severity IN ('INFO','WARNING','CRITICAL')", name="ck_alerts_severity"
        ),
        sa.CheckConstraint(
            "origin IN ('OFFICIAL','DERIVED','MODEL_WARNING')", name="ck_alerts_origin"
        ),
        sa.CheckConstraint(
            "status IN ('NEW','ACKNOWLEDGED','MUTED','RESOLVED')",
            name="ck_alerts_status",
        ),
        _qc("alerts"),
    )
    op.create_index("ix_alerts_rule", "alerts", ["rule_id"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_ticker", "alerts", ["ticker"])
    op.create_table(
        "alert_deliveries",
        sa.Column("id", sa.BigInteger(), nullable=False),
        _created(),
        sa.Column("alert_id", sa.BigInteger(), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "outcome IN ('DELIVERED','DEFERRED_QUIET','SKIPPED_MUTED',"
            "'BLOCKED_NO_CONSENT','FAILED')",
            name="ck_alert_deliveries_outcome",
        ),
    )
    op.create_index("ix_alert_deliveries_alert", "alert_deliveries", ["alert_id"])
    op.create_table(
        "alert_runs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        _created(),
        sa.Column("rule_id", sa.BigInteger(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("processing_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluated", sa.BigInteger(), nullable=False),
        sa.Column("created", sa.BigInteger(), nullable=False),
        sa.Column("duplicates_skipped", sa.BigInteger(), nullable=False),
        sa.Column("suppressed", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.ForeignKeyConstraint(["rule_id"], ["alert_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "rule_id", "as_of_date", "processing_time", name="uq_alert_runs_grain"
        ),
        _qc("alert_runs"),
    )
    op.create_index("ix_alert_runs_rule", "alert_runs", ["rule_id"])


def downgrade() -> None:
    op.drop_index("ix_alert_runs_rule", table_name="alert_runs")
    op.drop_table("alert_runs")
    op.drop_index("ix_alert_deliveries_alert", table_name="alert_deliveries")
    op.drop_table("alert_deliveries")
    op.drop_index("ix_alerts_ticker", table_name="alerts")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_rule", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("notification_preferences")
    op.drop_table("alert_rules")
