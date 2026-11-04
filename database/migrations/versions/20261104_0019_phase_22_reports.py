"""phase_22_reports

Revision ID: 20261104_0019
Revises: 20261104_0018
Create Date: 2026-11-04

Phase 22 (research reports, investment memos, company
dossiers) tables: report_templates (versioned definitions),
reports (one generated instance per template/subject/cut-off;
DRAFT at generation, APPROVED only by an explicit CLI
transition, never published externally — no publish step
exists), report_sections (ordered Markdown bodies),
report_figures (every key figure with kind, computation
status, source table, source row ids, and inherited quality
status; value_text carries non-numeric facts such as dates),
report_warnings (stale/missing/conflict evidence shown in the
report), report_exports (format, SHA-256, storage location).

Precedent note (Phases 11-21): Phase 22 stores its own tables
rather than retrofitting Phase 3 tables. Markdown and HTML
exports are archived under docs/phase-22/reports/; PDF
exports go to storage/research_reports/ (gitignored — the
project never commits PDFs) and only their hash and path are
recorded. No CSVs or PDFs are committed by this migration.
No credentials are stored anywhere. No order, execution, or
external-send concept exists in these tables.

Quality vocabulary CHECK mirrors migration 20261104_0003.
created_at carries a server default (as in the Phase 20
migration); the ORM models do not declare it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0019"
down_revision: str | None = "20261104_0018"
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
        server_default=sa.text("now()"),
        nullable=False,
    )


def _provenance(table: str) -> list:
    return [
        sa.Column("data_source_id", sa.BigInteger, nullable=True),
        sa.Column("source_key", sa.String(100), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "quality_status", sa.String(30), nullable=False, server_default="UNVERIFIED"
        ),
        _qc(table),
    ]


def upgrade() -> None:
    op.create_table(
        "report_templates",
        sa.Column("id", sa.BigInteger, primary_key=True),
        _created(),
        sa.Column("template_key", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, server_default="v1"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("audience", sa.String(100), nullable=False),
        sa.Column("sections", sa.JSON, nullable=False),
        sa.Column("methodology", sa.Text, nullable=False),
        sa.Column("disclosure", sa.Text, nullable=False),
        *_provenance("report_templates"),
        sa.UniqueConstraint(
            "template_key", "version", name="uq_report_templates_key_version"
        ),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.BigInteger, primary_key=True),
        _created(),
        sa.Column(
            "template_id",
            sa.BigInteger,
            sa.ForeignKey("report_templates.id"),
            nullable=False,
        ),
        sa.Column("template_key", sa.String(100), nullable=False),
        sa.Column(
            "template_version", sa.String(50), nullable=False, server_default="v1"
        ),
        sa.Column("subject_type", sa.String(50), nullable=False),
        sa.Column("subject_key", sa.String(200), nullable=False),
        sa.Column("subject_label", sa.String(300), nullable=False),
        sa.Column("report_date", sa.Date, nullable=False),
        sa.Column("data_cutoff_date", sa.Date, nullable=False),
        sa.Column("price_date", sa.Date, nullable=True),
        sa.Column("audience", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("version_number", sa.BigInteger, nullable=False, server_default="1"),
        sa.Column(
            "supersedes_id", sa.BigInteger, sa.ForeignKey("reports.id"), nullable=True
        ),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("snapshot", sa.JSON, nullable=False),
        *_provenance("reports"),
        # No UNIQUE on (template, subject, dates): versioning is
        # via supersedes_id/is_current, and the runner enforces
        # one current row per key in code. A UNIQUE would block
        # a future superseding version with the same dates.
    )
    op.create_table(
        "report_sections",
        sa.Column("id", sa.BigInteger, primary_key=True),
        _created(),
        sa.Column(
            "report_id", sa.BigInteger, sa.ForeignKey("reports.id"), nullable=False
        ),
        sa.Column("section_key", sa.String(100), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("body_markdown", sa.Text, nullable=False),
        *_provenance("report_sections"),
    )
    op.create_table(
        "report_figures",
        sa.Column("id", sa.BigInteger, primary_key=True),
        _created(),
        sa.Column(
            "report_id", sa.BigInteger, sa.ForeignKey("reports.id"), nullable=False
        ),
        sa.Column("figure_key", sa.String(200), nullable=False),
        sa.Column("label", sa.String(300), nullable=False),
        sa.Column("value", sa.Numeric(24, 6), nullable=True),
        sa.Column("value_text", sa.Text, nullable=True),
        sa.Column("unit", sa.String(100), nullable=True),
        sa.Column("computation_status", sa.String(30), nullable=False),
        sa.Column("figure_kind", sa.String(50), nullable=False),
        sa.Column("source_table", sa.String(100), nullable=False),
        sa.Column("source_row_ids", sa.JSON, nullable=False),
        sa.Column("source_note", sa.Text, nullable=False),
        *_provenance("report_figures"),
    )
    op.create_table(
        "report_warnings",
        sa.Column("id", sa.BigInteger, primary_key=True),
        _created(),
        sa.Column(
            "report_id", sa.BigInteger, sa.ForeignKey("reports.id"), nullable=False
        ),
        sa.Column("warning_kind", sa.String(50), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("source_table", sa.String(100), nullable=False),
        sa.Column("source_row_ids", sa.JSON, nullable=False),
        *_provenance("report_warnings"),
    )
    op.create_table(
        "report_exports",
        sa.Column("id", sa.BigInteger, primary_key=True),
        _created(),
        sa.Column(
            "report_id", sa.BigInteger, sa.ForeignKey("reports.id"), nullable=False
        ),
        sa.Column("export_format", sa.String(30), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("storage_location", sa.Text, nullable=False),
        *_provenance("report_exports"),
    )


def downgrade() -> None:
    op.drop_table("report_exports")
    op.drop_table("report_warnings")
    op.drop_table("report_figures")
    op.drop_table("report_sections")
    op.drop_table("reports")
    op.drop_table("report_templates")
