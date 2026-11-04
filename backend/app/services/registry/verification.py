"""Evidence-driven verification promotion for the registry.

Rules (docs/phase-04/data_quality_policies.md):
- A company/security is VERIFIED only when evidence from at least
  TWO DISTINCT sources agrees on the normalized name AND at least
  one of those sources is OFFICIAL (psx_official or secp).
  A single official-source import, on its own, does NOT verify:
  the importer writes the evidence row from the same record it
  imports, so a lone official row agrees with itself trivially,
  and source_key is caller-supplied with no provenance check.
  Corroboration is therefore mandatory for VERIFIED (audit H1).
- It is PARTIALLY_VERIFIED when evidence from at least two DISTINCT
  sources agrees on the normalized name (no official source needed).
- Evidence rows with an empty observed_name never count as
  agreeing (audit LOW finding): agreement requires an observed
  name that normalizes to the stored name.
- Lifecycle statuses (CONFLICTED, PENDING_REVIEW, SUSPENDED,
  DELISTED, INACTIVE) are never promoted: a lifecycle status is
  not a verification state, and promotion must not overwrite it.
- Otherwise its status is left untouched: the importer sets
  UNVERIFIED / PENDING_REVIEW / CONFLICTED / lifecycle statuses,
  and this module never demotes a lifecycle/conflict status.
- Statuses are a presentation of evidence, not a claim about the
  whole registry: one verified company does not verify the registry.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.reference import Company, Security
from app.models.registry import OFFICIAL_SOURCES, RegistryEvidence
from app.services.registry.normalization import normalize_name


def _distinct_agreeing_sources(
    session: Session, entity_type: str, entity_id: int, stored_name: str | None
) -> set[str]:
    try:
        norm_stored = normalize_name(stored_name) if stored_name else None
    except (ValueError, TypeError):
        norm_stored = None
    sources: set[str] = set()
    for row in (
        session.query(RegistryEvidence)
        .filter_by(entity_type=entity_type, entity_id=entity_id)
        .all()
    ):
        # An empty observed_name never counts as agreement: without an
        # observed name there is nothing that agrees with the stored
        # name (audit LOW finding).
        if norm_stored and row.observed_name:
            try:
                if normalize_name(row.observed_name) == norm_stored:
                    sources.add(row.source_key)
            except (ValueError, TypeError):
                continue
    return sources


def apply_verification_rules(session: Session, *, company_id: int) -> None:
    """Promote one company (and its securities) from evidence only."""
    company = session.query(Company).filter_by(id=company_id).first()
    if company is None:
        return
    if company.status in ("CONFLICTED", "PENDING_REVIEW", "SUSPENDED", "DELISTED", "INACTIVE"):
        return
    sources = _distinct_agreeing_sources(session, "company", company_id, company.legal_name)
    # Audit H1: VERIFIED needs corroboration — at least two distinct
    # agreeing sources, at least one official. A lone official row
    # (written by the very import being verified) proves nothing.
    if len(sources) >= 2 and (sources & set(OFFICIAL_SOURCES)):
        company.status = "VERIFIED"
    elif len(sources) >= 2:
        company.status = "PARTIALLY_VERIFIED"
    session.flush()

    for security in session.query(Security).filter_by(company_id=company_id).all():
        if security.status in ("CONFLICTED", "PENDING_REVIEW", "SUSPENDED", "DELISTED", "INACTIVE"):
            continue
        sec_sources = _distinct_agreeing_sources(
            session, "security", security.id, company.legal_name
        )
        if len(sec_sources) >= 2 and (sec_sources & set(OFFICIAL_SOURCES)):
            security.status = "VERIFIED"
        elif len(sec_sources) >= 2:
            security.status = "PARTIALLY_VERIFIED"
        session.flush()
