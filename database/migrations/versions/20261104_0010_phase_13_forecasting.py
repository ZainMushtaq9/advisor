"""phase_13_forecasting

Revision ID: 20261104_0010
Revises: 20261104_0009
Create Date: 2026-11-04

Phase 13 (forecasting and predictive analytics) tables. No CSVs or
PDFs are involved; no credentials are stored anywhere. Quality
vocabulary CHECK mirrors migration 20261104_0003.

NOTE: the Phase 3 "forecasts" table is NOT reused here: it requires
NOT NULL interval_low, interval_high and uncertainty, and Phase 13
writes no forecast with an interval that cannot be validated from
residual history. With one trading date of prices, no interval is
validatable, so the Phase 3 table stays empty and Phase 13 stores
its target registry, feature snapshots and per-target assessments
in these three new tables instead. (Precedent: Phase 11's news
tables beside the Phase 3 "news" table, and Phase 12's
corporate_action_records beside the Phase 3 "corporate_actions".)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0010"
down_revision: Union[str, None] = "20261104_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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


def _quality_check(table: str) -> str:
    values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
    return f"quality_status IN ({values})"


def _provenance_columns() -> list:
    return [
        sa.Column("data_source_id", sa.BigInteger(), nullable=True),
        sa.Column("source_key", sa.String(100), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "quality_status",
            sa.String(30),
            nullable=False,
            server_default="UNVERIFIED",
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "forecast_targets",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        *_provenance_columns(),
        sa.Column("target_key", sa.String(100), nullable=False),
        sa.Column("horizon", sa.String(30), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("scope", sa.String(30), nullable=False),
        sa.Column("min_observations", sa.BigInteger(), nullable=False),
        sa.Column("method_requirements", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="defined"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "target_key", "horizon", name="uq_forecast_targets_key_horizon"
        ),
        sa.CheckConstraint(
            _quality_check("forecast_targets"), name="ck_forecast_targets_quality"
        ),
    )
    op.create_index("idx_forecast_targets_key", "forecast_targets", ["target_key"])

    op.create_table(
        "forecast_feature_snapshots",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        *_provenance_columns(),
        sa.Column("security_id", sa.BigInteger(), nullable=True),
        sa.Column("origin_date", sa.Date(), nullable=False),
        sa.Column("feature_key", sa.String(200), nullable=False),
        sa.Column("feature_value", sa.Numeric(24, 6), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["security_id"], ["securities.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "security_id",
            "origin_date",
            "feature_key",
            name="uq_forecast_feature_snapshots_grain",
        ),
        sa.CheckConstraint(
            _quality_check("forecast_feature_snapshots"),
            name="ck_forecast_feature_snapshots_quality",
        ),
    )
    op.create_index(
        "idx_forecast_feature_snapshots_origin",
        "forecast_feature_snapshots",
        ["origin_date"],
    )

    op.create_table(
        "forecast_assessments",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        *_provenance_columns(),
        sa.Column("security_id", sa.BigInteger(), nullable=True),
        sa.Column("target_key", sa.String(100), nullable=False),
        sa.Column("horizon", sa.String(30), nullable=False),
        sa.Column("origin_date", sa.Date(), nullable=False),
        sa.Column("method", sa.String(100), nullable=False),
        sa.Column("computation_status", sa.String(30), nullable=False),
        sa.Column("point_estimate", sa.Numeric(24, 6), nullable=True),
        sa.Column("interval_low", sa.Numeric(24, 6), nullable=True),
        sa.Column("interval_high", sa.Numeric(24, 6), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["security_id"], ["securities.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "security_id",
            "target_key",
            "horizon",
            "origin_date",
            name="uq_forecast_assessments_grain",
        ),
        sa.CheckConstraint(
            _quality_check("forecast_assessments"),
            name="ck_forecast_assessments_quality",
        ),
    )
    op.create_index(
        "idx_forecast_assessments_security", "forecast_assessments", ["security_id"]
    )


def downgrade() -> None:
    op.drop_table("forecast_assessments")
    op.drop_table("forecast_feature_snapshots")
    op.drop_table("forecast_targets")
