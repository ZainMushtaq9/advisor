"""Phase 22 report tables (models only; created_at carries a
server default, as in the Phase 20 migration, and is not
declared here).

Reports are descriptive/analytical documents only. They are
never investment advice, never a buy/sell signal presented as
executable, never a forecast presented as fact, and never a
price target. Generation sets status DRAFT; an explicit CLI
transition moves DRAFT to APPROVED (internally reviewed) or
REJECTED. There is no publish step and no external-send path:
an APPROVED report is still internal. Quality status is
inherited from the report's inputs, never higher than them,
and never promoted by this phase. Versioning is via
supersedes_id/is_current; a report is never edited in place.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)

from app.models.base import Base


class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id = Column(BigInteger, primary_key=True)
    template_key = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False, default="v1")
    title = Column(String(300), nullable=False)
    audience = Column(String(100), nullable=False)
    sections = Column(JSON, nullable=False)
    methodology = Column(Text, nullable=False)
    disclosure = Column(Text, nullable=False)
    quality_status = Column(String(30), nullable=False, default="UNVERIFIED")


class Report(Base):
    __tablename__ = "reports"

    id = Column(BigInteger, primary_key=True)
    template_id = Column(BigInteger, ForeignKey("report_templates.id"), nullable=False)
    template_key = Column(String(100), nullable=False)
    template_version = Column(String(50), nullable=False, default="v1")
    subject_type = Column(String(50), nullable=False)
    subject_key = Column(String(200), nullable=False)
    subject_label = Column(String(300), nullable=False)
    report_date = Column(Date, nullable=False)
    data_cutoff_date = Column(Date, nullable=False)
    price_date = Column(Date, nullable=True)
    audience = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default="DRAFT")
    version_number = Column(BigInteger, nullable=False, default=1)
    supersedes_id = Column(BigInteger, ForeignKey("reports.id"), nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    snapshot = Column(JSON, nullable=False)
    quality_status = Column(String(30), nullable=False, default="UNVERIFIED")


class ReportSection(Base):
    __tablename__ = "report_sections"

    id = Column(BigInteger, primary_key=True)
    report_id = Column(BigInteger, ForeignKey("reports.id"), nullable=False)
    section_key = Column(String(100), nullable=False)
    title = Column(String(300), nullable=False)
    position = Column(Integer, nullable=False)
    body_markdown = Column(Text, nullable=False)
    quality_status = Column(String(30), nullable=False, default="UNVERIFIED")


class ReportFigure(Base):
    __tablename__ = "report_figures"

    id = Column(BigInteger, primary_key=True)
    report_id = Column(BigInteger, ForeignKey("reports.id"), nullable=False)
    figure_key = Column(String(200), nullable=False)
    label = Column(String(300), nullable=False)
    value = Column(Numeric(24, 6), nullable=True)
    value_text = Column(Text, nullable=True)
    unit = Column(String(100), nullable=True)
    computation_status = Column(String(30), nullable=False)
    figure_kind = Column(String(50), nullable=False)
    source_table = Column(String(100), nullable=False)
    source_row_ids = Column(JSON, nullable=False)
    source_note = Column(Text, nullable=False)
    quality_status = Column(String(30), nullable=False, default="UNVERIFIED")


class ReportWarning(Base):
    __tablename__ = "report_warnings"

    id = Column(BigInteger, primary_key=True)
    report_id = Column(BigInteger, ForeignKey("reports.id"), nullable=False)
    warning_kind = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    source_table = Column(String(100), nullable=False)
    source_row_ids = Column(JSON, nullable=False)
    quality_status = Column(String(30), nullable=False, default="UNVERIFIED")


class ReportExport(Base):
    __tablename__ = "report_exports"

    id = Column(BigInteger, primary_key=True)
    report_id = Column(BigInteger, ForeignKey("reports.id"), nullable=False)
    export_format = Column(String(30), nullable=False)
    content_hash = Column(String(64), nullable=False)
    storage_location = Column(Text, nullable=False)
    quality_status = Column(String(30), nullable=False, default="UNVERIFIED")
