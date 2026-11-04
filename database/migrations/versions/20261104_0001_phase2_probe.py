"""Phase 2 probe table only.

Revision ID: 20261104_0001
Revises: (none — first migration)

SCOPE GUARD: this migration creates ONLY the minimal phase2_probe table
needed for a Phase 2 insert/retrieve test. It deliberately does NOT create
any Phase 3 entity (companies, securities, market_prices, financial
statements, forecasts, recommendations, portfolios, audit_logs, etc.).
Those belong to Phase 3, after the Phase 1 catalog is implemented as
SQLAlchemy models by the backend team. Adding a Phase 3 table here would
be scope creep, not progress.

phase2_probe is a throwaway infrastructure probe, not business data:
it must never be presented as PSX data, and it may be dropped in Phase 3
once the real schema lands (a follow-up migration, not a silent drop).
"""
from alembic import op
import sqlalchemy as sa

revision = "20261104_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "phase2_probe",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("probe_label", sa.String(length=100), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_phase2_probe"),
    )
    op.create_index(
        "idx_phase2_probe_label", "phase2_probe", ["probe_label"]
    )


def downgrade() -> None:
    op.drop_index("idx_phase2_probe_label", table_name="phase2_probe")
    op.drop_table("phase2_probe")
