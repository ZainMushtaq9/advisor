"""Governance tables — Phase 3: sources, quality, raw payloads, audit,
agents and models. These are the tables every other domain references
for provenance; they are defined here so no circular import exists."""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin


class DataSource(IdMixin, CreatedMixin, Base):
    """Database twin of the collector's data-source registry. A source
    marked 'UNVERIFIED' may be staged, but its rows must never be
    presented as verified (see data_sources.verification_status)."""

    __tablename__ = "data_sources"
    __table_args__ = (
        # Audit L6 fix: uppercase vocabulary, CHECK-enforced, matching
        # the quality vocabulary. The rule "an unverified source's rows
        # must not be presented as verified" remains a presentation
        # rule for Phase 5 consumers — it is enforced nowhere in code
        # in Phase 3, and is recorded as such.
        CheckConstraint(
            "verification_status IN ('UNVERIFIED','PARTIALLY_VERIFIED',"
            "'VERIFIED','CONFLICTED','PENDING_REVIEW')",
            name="ck_data_sources_verification_status",
        ),
    )
    source_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    base_reference: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # URL/identifier as documented, never invented
    freshness_threshold_seconds: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reliability_notes: Mapped[str] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="UNVERIFIED"
    )
    terms_summary: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # redistribution limits, in plain words


class DataQualityReport(IdMixin, CreatedMixin, Base):
    """Issue log. Resolution is a status change (resolution_status +
    resolved_at, the ONLY columns a trigger allows to change) plus a
    new row where underlying data changed — the original report is
    never deleted and its detail is never edited (audit H2 fix)."""

    __tablename__ = "data_quality_reports"
    __table_args__ = (Index("idx_dqr_entity", "affected_entity", "affected_row_id"),)
    issue_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # missing_session, stale, conflict, schema_mismatch, failed_validation
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    affected_entity: Mapped[str] = mapped_column(String(100), nullable=False)
    affected_row_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    resolved_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)


class RawPayload(IdMixin, CreatedMixin, Base):
    """Immutable, content-hash-addressed store of source payloads.
    For large payloads (PDFs) the file lives on disk per STORAGE_ARCHITECTURE
    and this row holds reference + hash + size + storage location."""

    __tablename__ = "raw_payloads"
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )  # SHA-256 hex
    payload_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_location: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # storage-relative path, or 'inline' for small payloads
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data_source_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True
    )


class AuditLog(IdMixin, CreatedMixin, Base):
    """Append-only 'who did what to what, when, and why'. No application
    role may mutate it (database trigger enforces this in Phase 3)."""

    __tablename__ = "audit_logs"
    __table_args__ = (Index("idx_audit_entity", "entity_type", "entity_id"),)
    actor_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # user, agent, system, scheduler
    actor_ref: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # id or name — never a secret
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    payload_ref: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # reference only, never secret material


class ModelVersion(IdMixin, CreatedMixin, Base):
    """Immutable reference. Forecasts/valuations/executions reference a
    version id, never a bare model name, so a model change cannot
    silently rewrite history."""

    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("model_name", "version_string", name="uq_model_versions_name_version"),
    )
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    version_string: Mapped[str] = mapped_column(String(100), nullable=False)
    config_snapshot_ref: Mapped[str] = mapped_column(Text, nullable=True)
    metrics_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")


class AgentExecution(IdMixin, CreatedMixin, Base):
    """Run record. Input references only — no secret payloads. Status
    and ended_at may update as a run progresses (marker-only trigger);
    every other column change is rejected."""

    __tablename__ = "agent_executions"
    agent_name: Mapped[str] = mapped_column(String(200), nullable=False)
    trigger: Mapped[str] = mapped_column(String(100), nullable=False)
    input_refs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")
    model_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True
    )


class AgentOutput(IdMixin, CreatedMixin, Base):
    """One row per output artefact of an execution. Research reports are
    files on disk; this row stores reference + hash, not a duplicate."""

    __tablename__ = "agent_outputs"
    execution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False
    )
    output_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_ref: Mapped[str] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # genuinely schemaless content only; business facts are typed columns elsewhere
