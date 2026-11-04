"""Idempotent incremental import for the Phase 4 registry.

Contract:
- Importing the same source records twice creates ZERO new rows
  (second run: created=0, updated=0, skipped_as_duplicate=N).
- The importer NEVER sets VERIFIED or PARTIALLY_VERIFIED. It sets
  UNVERIFIED for a clean new record, PENDING_REVIEW for an ambiguous
  record, and CONFLICTED on an existing record when a new source
  disagrees with it on a hard identifier. Promotion happens only in
  verification.py, from evidence rows.
- A ticker change on an existing security is recorded in
  symbol_history with an effective date and source evidence; the
  security keeps its stable surrogate id.
- Source classification is kept separate from normalized
  classification: a sector row stores source + source_sector_name
  verbatim; no canonical sector is assigned by guesswork
  (canonical_sector_id stays NULL unless a verified mapping exists).
- Nothing here assumes an API, a live fetch, or a scheduler. The
  caller supplies records (from a file, a verified snapshot, or a
  future Phase 5 collector); this module only validates, matches,
  and stores them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.governance import DataQualityReport, DataSource
from app.models.reference import (
    Company,
    CompanyIdentifier,
    Exchange,
    Sector,
    Security,
    SymbolHistory,
)
from app.models.registry import RegistryEvidence
from app.services.registry import verification
from app.services.registry.matching import Candidate, match_record
from app.services.registry.normalization import (
    normalize_isin,
    normalize_name,
    normalize_sector_name,
    normalize_ticker,
)


@dataclass
class SourceRecord:
    """One row from one source. All fields are the source's own
    values; normalization happens inside the importer."""

    ticker: str
    legal_name: str
    sector_name: str | None = None
    isin: str | None = None
    listing_status: str | None = None  # active | suspended | delisted | inactive | None
    website: str | None = None
    listing_date: date | None = None
    identifiers: tuple[tuple[str, str], ...] = ()


@dataclass
class ImportResult:
    source_key: str
    records_seen: int = 0
    companies_created: int = 0
    securities_created: int = 0
    sectors_created: int = 0
    evidence_created: int = 0
    skipped_as_duplicate: int = 0
    pending_review: int = 0
    conflicts: int = 0
    rejected: int = 0
    errors: list[str] = field(default_factory=list)


def _get_or_create_exchange(session: Session) -> Exchange:
    exchange = session.query(Exchange).filter_by(code="PSX").first()
    if exchange is None:
        exchange = Exchange(
            code="PSX",
            name="Pakistan Stock Exchange",
            timezone_name="Asia/Karachi",
            country="Pakistan",
        )
        session.add(exchange)
        session.flush()
    return exchange


def _get_or_create_source(session: Session, source_key: str, display_name: str) -> DataSource:
    source = session.query(DataSource).filter_by(source_key=source_key).first()
    if source is None:
        source = DataSource(
            source_key=source_key,
            display_name=display_name,
            source_type="registry",
            base_reference=display_name,
            verification_status="UNVERIFIED",
        )
        session.add(source)
        session.flush()
    return source


def _get_or_create_sector(
    session: Session, source_key: str, sector_name: str, result: ImportResult
) -> Sector:
    sector = (
        session.query(Sector)
        .filter_by(source=source_key, source_sector_name=sector_name)
        .first()
    )
    if sector is None:
        sector = Sector(
            name=sector_name,
            source_sector_name=sector_name,
            source=source_key,
            canonical_sector_id=None,
        )
        session.add(sector)
        session.flush()
        result.sectors_created += 1
    return sector


def _record_evidence(
    session: Session,
    *,
    entity_type: str,
    entity_id: int,
    source_key: str,
    source_record_key: str,
    observed_name: str | None,
    observed_sector: str | None,
    collected_at: datetime,
    result: ImportResult,
) -> bool:
    """Returns True when a NEW evidence row was created."""
    existing = (
        session.query(RegistryEvidence)
        .filter_by(
            entity_type=entity_type,
            entity_id=entity_id,
            source_key=source_key,
            source_record_key=source_record_key,
        )
        .first()
    )
    if existing is not None:
        return False
    session.add(
        RegistryEvidence(
            entity_type=entity_type,
            entity_id=entity_id,
            source_key=source_key,
            source_record_key=source_record_key,
            observed_name=observed_name,
            observed_sector=observed_sector,
            collected_at=collected_at,
        )
    )
    session.flush()
    result.evidence_created += 1
    return True


def _report_once(
    session: Session,
    *,
    issue_type: str,
    severity: str,
    affected_entity: str,
    affected_row_id: int | None,
    detail: str,
) -> bool:
    """Add a DataQualityReport only if an identical open report does
    not already exist. Audit M3: re-importing an ambiguous or
    conflicting record must not append a duplicate report each time;
    core entities are idempotent, and so are issue reports."""
    existing = (
        session.query(DataQualityReport)
        .filter_by(
            issue_type=issue_type,
            affected_entity=affected_entity,
            affected_row_id=affected_row_id,
        )
        .all()
    )
    # A report counts as "already open" when its status is "open" or
    # unset (None): column defaults are applied by the database on
    # insert, so an in-memory stand-in may carry None for a report
    # that is open in reality. A resolved report does not block a
    # genuinely recurring issue from being reported again.
    if any(
        r.detail == detail and getattr(r, "resolution_status", None) in ("open", None)
        for r in existing
    ):
        return False
    session.add(
        DataQualityReport(
            issue_type=issue_type,
            severity=severity,
            affected_entity=affected_entity,
            affected_row_id=affected_row_id,
            detail=detail,
        )
    )
    session.flush()
    return True


# Listing-status values a source may state. Anything else is recorded
# as an error and ignored, never stored (audit M4 decision: the
# contract stores only these lifecycle statuses).
_LIFECYCLE_STATUSES = {
    "active": None,  # no lifecycle override; verification status applies
    "suspended": "SUSPENDED",
    "delisted": "DELISTED",
    "inactive": "INACTIVE",
}


def _lifecycle_status(record: SourceRecord, result: ImportResult) -> str | None:
    if record.listing_status is None:
        return None
    key = record.listing_status.strip().lower()
    if key not in _LIFECYCLE_STATUSES:
        result.errors.append(
            f"{record.ticker!r}: unknown listing_status "
            f"{record.listing_status!r} ignored (not stored)"
        )
        return None
    return _LIFECYCLE_STATUSES[key]


def import_records(
    session: Session,
    records: list[SourceRecord],
    *,
    source_key: str,
    source_display_name: str,
    collected_at: datetime | None = None,
) -> ImportResult:
    """Import one batch from one source, idempotently."""
    collected_at = collected_at or datetime.now(timezone.utc)
    result = ImportResult(source_key=source_key)
    exchange = _get_or_create_exchange(session)
    _get_or_create_source(session, source_key, source_display_name)

    # Candidates are loaded once per batch; the batch itself may add
    # entities, so the candidate list is refreshed per record.
    for record in records:
        result.records_seen += 1
        try:
            norm_ticker = normalize_ticker(record.ticker)
            normalize_name(record.legal_name)  # validates; key computed in matcher
            norm_isin = None
            if record.isin:
                norm_isin = normalize_isin(record.isin)
        except (ValueError, TypeError) as exc:
            result.rejected += 1
            result.errors.append(f"{record.ticker!r}: {exc}")
            continue

        securities = session.query(Security).all()
        companies = {c.id: c for c in session.query(Company).all()}
        candidates = [
            Candidate(
                entity_id=s.id,
                ticker=s.ticker,
                legal_name=(
                    companies[s.company_id].legal_name
                    if s.company_id in companies
                    else None
                ),
                isin=s.isin,
                identifiers=tuple(
                    (i.identifier_type, i.identifier_value)
                    for i in session.query(CompanyIdentifier)
                    .filter_by(company_id=s.company_id)
                    .all()
                ),
            )
            for s in securities
        ]
        outcome = match_record(
            ticker=record.ticker,
            legal_name=record.legal_name,
            isin=record.isin,
            identifiers=record.identifiers,
            candidates=candidates,
        )

        if outcome.outcome == "ambiguous":
            result.pending_review += 1
            _report_once(
                session,
                issue_type="ambiguous_registry_record",
                severity="MEDIUM",
                affected_entity="securities",
                affected_row_id=None,
                detail=(
                    f"Source {source_key}: record ticker={norm_ticker} "
                    f"name={record.legal_name!r} is ambiguous ({outcome.rule}: "
                    f"{outcome.detail}). Kept original, not merged."
                ),
            )
            continue

        sector = None
        if record.sector_name:
            try:
                sector_name = record.sector_name.strip()
                normalize_sector_name(sector_name)
                sector = _get_or_create_sector(session, source_key, sector_name, result)
            except (ValueError, TypeError) as exc:
                result.errors.append(f"{record.ticker!r}: bad sector name: {exc}")

        lifecycle = _lifecycle_status(record, result)
        if outcome.outcome == "none":
            company = Company(
                legal_name=record.legal_name.strip(),
                short_name=None,
                sector_id=sector.id if sector else None,
                status=lifecycle or "UNVERIFIED",
                listing_date=record.listing_date,
                website=record.website,
            )
            session.add(company)
            session.flush()
            result.companies_created += 1
            security = Security(
                company_id=company.id,
                exchange_id=exchange.id,
                ticker=norm_ticker,
                security_type="ordinary",
                status=lifecycle or "UNVERIFIED",
                isin=norm_isin,
            )
            session.add(security)
            session.flush()
            result.securities_created += 1
            if norm_isin:
                session.add(
                    CompanyIdentifier(
                        company_id=company.id,
                        identifier_type="ISIN",
                        identifier_value=norm_isin,
                        is_current=True,
                    )
                )
            for id_type, id_value in record.identifiers:
                session.add(
                    CompanyIdentifier(
                        company_id=company.id,
                        identifier_type=id_type.strip().upper(),
                        identifier_value=id_value.strip().upper(),
                        is_current=True,
                    )
                )
            session.flush()
            _record_evidence(
                session,
                entity_type="company",
                entity_id=company.id,
                source_key=source_key,
                source_record_key=norm_ticker,
                observed_name=record.legal_name.strip(),
                observed_sector=record.sector_name,
                collected_at=collected_at,
                result=result,
            )
            _record_evidence(
                session,
                entity_type="security",
                entity_id=security.id,
                source_key=source_key,
                source_record_key=norm_ticker,
                observed_name=record.legal_name.strip(),
                observed_sector=record.sector_name,
                collected_at=collected_at,
                result=result,
            )
        else:
            # Unique match: idempotent re-import of the same record.
            security = session.query(Security).filter_by(id=outcome.entity_id).first()
            if security is None:
                result.rejected += 1
                result.errors.append(
                    f"{record.ticker!r}: matched entity {outcome.entity_id} not found"
                )
                continue
            company = session.query(Company).filter_by(id=security.company_id).first()
            if company is None:
                result.rejected += 1
                result.errors.append(f"{record.ticker!r}: matched company not found")
                continue
            # ISIN disagreement is checked FIRST (audit M2): a
            # conflicting import must not mutate the ticker or write
            # symbol history before it is marked CONFLICTED.
            if norm_isin and security.isin and norm_isin != security.isin:
                result.conflicts += 1
                company.status = "CONFLICTED"
                security.status = "CONFLICTED"
                _report_once(
                    session,
                    issue_type="conflicting_isin",
                    severity="HIGH",
                    affected_entity="securities",
                    affected_row_id=security.id,
                    detail=(
                        f"Source {source_key}: ISIN {norm_isin} disagrees with "
                        f"stored ISIN for security {security.id} (ticker {security.ticker})."
                    ),
                )
                continue
            # Name disagreement on an ISIN/identifier match (audit M1):
            # the identifier matched, but the names differ, so this is
            # flagged for review rather than silently accepted as the
            # same company. Evidence is still recorded below; the
            # PENDING_REVIEW status blocks verification promotion.
            try:
                names_agree = normalize_name(record.legal_name) == normalize_name(
                    company.legal_name
                )
            except (ValueError, TypeError):
                names_agree = False
            name_disagreement = outcome.rule in ("isin", "identifier") and not names_agree
            if name_disagreement:
                company.status = "PENDING_REVIEW"
                security.status = "PENDING_REVIEW"
                _report_once(
                    session,
                    issue_type="name_disagreement_on_identifier_match",
                    severity="MEDIUM",
                    affected_entity="securities",
                    affected_row_id=security.id,
                    detail=(
                        f"Source {source_key}: record {norm_ticker} "
                        f"{record.legal_name!r} matched security {security.id} by "
                        f"{outcome.rule} but the stored name is "
                        f"{company.legal_name!r}. Flagged, not merged."
                    ),
                )
            # Ticker change (rename): record history, keep surrogate id.
            # A name-disagreement record never mutates the ticker: its
            # identity is doubtful, so the stored ticker stands.
            if not name_disagreement and security.ticker != norm_ticker:
                session.add(
                    SymbolHistory(
                        security_id=security.id,
                        previous_ticker=security.ticker,
                        new_ticker=norm_ticker,
                        previous_company_id=company.id,
                        new_company_id=company.id,
                        effective_date=collected_at.date(),
                        reason="Ticker changed in source record",
                        source_evidence=f"source={source_key}",
                    )
                )
                security.ticker = norm_ticker
                session.flush()
            if norm_isin and not security.isin:
                security.isin = norm_isin
                session.add(
                    CompanyIdentifier(
                        company_id=company.id,
                        identifier_type="ISIN",
                        identifier_value=norm_isin,
                        is_current=True,
                    )
                )
                session.flush()
            # Audit M5: identifiers supplied on a matched re-import
            # are stored when new, not merely used for matching.
            existing_ids = {
                (i.identifier_type, i.identifier_value)
                for i in session.query(CompanyIdentifier)
                .filter_by(company_id=company.id)
                .all()
            }
            for id_type, id_value in record.identifiers:
                key = (id_type.strip().upper(), id_value.strip().upper())
                if key not in existing_ids:
                    session.add(
                        CompanyIdentifier(
                            company_id=company.id,
                            identifier_type=key[0],
                            identifier_value=key[1],
                            is_current=True,
                        )
                    )
                    existing_ids.add(key)
            session.flush()
            # Lifecycle status from the source (audit M4): a stated
            # suspended/delisted/inactive status is stored, and
            # verification promotion skips lifecycle statuses.
            if lifecycle and company.status not in ("CONFLICTED", "PENDING_REVIEW"):
                company.status = lifecycle
                security.status = lifecycle
                session.flush()
            created_evidence = _record_evidence(
                session,
                entity_type="company",
                entity_id=company.id,
                source_key=source_key,
                source_record_key=norm_ticker,
                observed_name=record.legal_name.strip(),
                observed_sector=record.sector_name,
                collected_at=collected_at,
                result=result,
            )
            created_sec_evidence = _record_evidence(
                session,
                entity_type="security",
                entity_id=security.id,
                source_key=source_key,
                source_record_key=norm_ticker,
                observed_name=record.legal_name.strip(),
                observed_sector=record.sector_name,
                collected_at=collected_at,
                result=result,
            )
            if not created_evidence and not created_sec_evidence:
                result.skipped_as_duplicate += 1

        # Verification promotion is evidence-driven and runs per record;
        # it never promotes on import success alone.
        verification.apply_verification_rules(session, company_id=company.id)

    session.flush()
    return result
