"""Shared model base, provenance and quality-status rules — Phase 3.

Provenance block (Phase 1 DATABASE_DESIGN §6, adapted to Phase 2 code):
every market / financial / news / analysis record carries, where it is
meaningful, a source reference, a *source* timestamp, a *collection*
timestamp and a quality status. Collection time is NEVER an observation
time, and a missing observation is NEVER stored as zero — it is simply
absent, or flagged MISSING in the data-quality registry.

Quality statuses (shared vocabulary, Phase 5 spec):
VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, CONFLICTED, MISSING,
REJECTED, STALE, PENDING_REVIEW. Registry-only statuses (company /
security lifecycle) live on those tables, not here.

No model in this package stores a password, API key, token or secret.
Agent/model execution logs carry input *references*, never payloads
that could contain credentials.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

QUALITY_STATUSES = (
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "UNVERIFIED",
    "CONFLICTED",
    "MISSING",
    "REJECTED",
    "STALE",
    "PENDING_REVIEW",
)

# NOTE (audit H1, fixed 2026-11-04): an earlier draft defined a
# QUALITY_CHECK CheckConstraint here but never attached it to any
# table — dead code that looked like enforcement. It was deleted.
# Quality-vocabulary enforcement lives in migration 20261104_0003
# (21 tables) + 20261104_0004 (financial_statements, the 22nd), as
# database CHECK constraints, not in this module.


class IdMixin:
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)


class CreatedMixin:
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProvenanceMixin:
    """Provenance block. source_timestamp = when the source says the
    observation is for; collected_at = when WE fetched it (PKT, tz-aware).
    Neither may be silently substituted for the other."""

    data_source_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True
    )
    source_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")


class VersionMixin:
    """Versioning, not overwriting. A revised report is a NEW row with
    version_number incremented and supersedes_id pointing at the row it
    replaces. Old rows are never edited or deleted (see the Phase 3
    immutability migration for the database-level enforcement)."""

    version_number: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    supersedes_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)


__all__ = [
    "Base",
    "QUALITY_STATUSES",
    "IdMixin",
    "CreatedMixin",
    "ProvenanceMixin",
    "VersionMixin",
]
