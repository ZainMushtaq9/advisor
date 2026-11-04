"""Phase 4 registry evidence table.

One row per (entity, source, source record key). This is what makes
verification rules auditable: a company's status is derived from the
evidence rows that actually exist, never from an import's success.

A company/security is:
- VERIFIED when at least one evidence row comes from an OFFICIAL
  source (PSX official site or SECP) and agrees on the match key, or
- PARTIALLY_VERIFIED when evidence from at least two DISTINCT
  non-official sources agrees on the match key, or
- otherwise UNVERIFIED / PENDING_REVIEW / CONFLICTED as recorded.

OFFICIAL_SOURCES is a code-level constant, not a database flag, so a
source cannot promote itself to official by editing a row.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin

OFFICIAL_SOURCES: frozenset[str] = frozenset({"psx_official", "secp"})


class RegistryEvidence(IdMixin, CreatedMixin, Base):
    __tablename__ = "registry_evidence"
    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "entity_id",
            "source_key",
            "source_record_key",
            name="uq_registry_evidence_entity_source_key",
        ),
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # company | security
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_key: Mapped[str] = mapped_column(String(100), nullable=False)
    source_record_key: Mapped[str] = mapped_column(String(200), nullable=False)
    observed_name: Mapped[str] = mapped_column(String(300), nullable=True)
    observed_sector: Mapped[str] = mapped_column(String(200), nullable=True)
    collected_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_note: Mapped[str] = mapped_column(Text, nullable=True)
