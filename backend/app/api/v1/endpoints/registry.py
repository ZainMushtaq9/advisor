"""Phase 4 registry read-only endpoints.

All endpoints return ONLY rows that actually exist in the database.
An empty registry returns empty lists and zero counts — never
fabricated companies, prices, or ratings. When no database is
configured, endpoints answer 503 with a truthful reason, never a
fake empty registry.

Endpoints:
  GET /api/v1/companies
  GET /api/v1/companies/{company_id}
  GET /api/v1/companies/{company_id}/securities
  GET /api/v1/securities
  GET /api/v1/securities/{security_id}
  GET /api/v1/sectors
  GET /api/v1/registry/statistics
  GET /api/v1/registry/quality
  GET /api/v1/registry/sources
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.governance import DataSource
from app.models.reference import Company, Sector, Security
from app.models.registry import RegistryEvidence
from app.services.registry.sync_config import DEFAULT_SYNC_CONFIGS

router = APIRouter(tags=["registry"])

MAX_LIMIT = 200


def get_session(request: Request) -> Generator[Session, None, None]:
    factory = get_session_factory(request.app.state.engine)
    if factory is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured (DATABASE_URL is not set).",
        )
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _pagination(skip: int, limit: int) -> tuple[int, int]:
    if skip < 0:
        raise HTTPException(status_code=422, detail="skip must be >= 0")
    if limit < 1 or limit > MAX_LIMIT:
        raise HTTPException(
            status_code=422, detail=f"limit must be between 1 and {MAX_LIMIT}"
        )
    return skip, limit


def _company_row(company: Company, session: Session) -> dict:
    sector = None
    if company.sector_id:
        sector = session.query(Sector).filter_by(id=company.sector_id).first()
    return {
        "id": company.id,
        "legal_name": company.legal_name,
        "short_name": company.short_name,
        "sector_id": company.sector_id,
        "sector_name": sector.name if sector else None,
        "sector_source": sector.source if sector else None,
        "status": company.status,
        "listing_date": company.listing_date.isoformat() if company.listing_date else None,
        "delisting_date": company.delisting_date.isoformat() if company.delisting_date else None,
        "website": company.website,
        "securities_count": session.query(Security).filter_by(company_id=company.id).count(),
    }


def _security_row(security: Security, session: Session) -> dict:
    company = session.query(Company).filter_by(id=security.company_id).first()
    return {
        "id": security.id,
        "company_id": security.company_id,
        "company_name": company.legal_name if company else None,
        "ticker": security.ticker,
        "security_type": security.security_type,
        "status": security.status,
        "isin": security.isin,
        "exchange_id": security.exchange_id,
    }


@router.get("/companies")
def list_companies(
    session: Session = Depends(get_session),  # noqa: B008
    search: str | None = Query(default=None, description="Substring match on legal name"),
    status: str | None = Query(default=None),
    sector_id: int | None = Query(default=None),
    sort: str = Query(default="id", pattern="^(id|legal_name)$"),
    skip: int = Query(default=0),
    limit: int = Query(default=50),
) -> dict:
    skip, limit = _pagination(skip, limit)
    query = session.query(Company)
    if search:
        query = query.filter(Company.legal_name.ilike(f"%{search}%"))
    if status:
        query = query.filter(Company.status == status.upper())
    if sector_id is not None:
        query = query.filter(Company.sector_id == sector_id)
    total = query.count()
    order = Company.id if sort == "id" else Company.legal_name
    rows = query.order_by(order).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_company_row(c, session) for c in rows],
    }


@router.get("/companies/{company_id}")
def get_company(company_id: int, session: Session = Depends(get_session)) -> dict:  # noqa: B008
    company = session.query(Company).filter_by(id=company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found.")
    return _company_row(company, session)


@router.get("/companies/{company_id}/securities")
def list_company_securities(
    company_id: int,
    session: Session = Depends(get_session),  # noqa: B008
    skip: int = Query(default=0),
    limit: int = Query(default=50),
) -> dict:
    skip, limit = _pagination(skip, limit)
    company = session.query(Company).filter_by(id=company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found.")
    query = session.query(Security).filter_by(company_id=company_id)
    total = query.count()
    rows = query.order_by(Security.id).offset(skip).limit(limit).all()
    return {
        "company_id": company_id,
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_security_row(s, session) for s in rows],
    }


@router.get("/securities")
def list_securities(
    session: Session = Depends(get_session),  # noqa: B008
    ticker: str | None = Query(default=None, description="Substring match on ticker"),
    status: str | None = Query(default=None),
    company_id: int | None = Query(default=None),
    sort: str = Query(default="id", pattern="^(id|ticker)$"),
    skip: int = Query(default=0),
    limit: int = Query(default=50),
) -> dict:
    skip, limit = _pagination(skip, limit)
    query = session.query(Security)
    if ticker:
        query = query.filter(Security.ticker.ilike(f"%{ticker}%"))
    if status:
        query = query.filter(Security.status == status.upper())
    if company_id is not None:
        query = query.filter(Security.company_id == company_id)
    total = query.count()
    order = Security.id if sort == "id" else Security.ticker
    rows = query.order_by(order).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_security_row(s, session) for s in rows],
    }


@router.get("/securities/{security_id}")
def get_security(security_id: int, session: Session = Depends(get_session)) -> dict:  # noqa: B008
    security = session.query(Security).filter_by(id=security_id).first()
    if security is None:
        raise HTTPException(status_code=404, detail="Security not found.")
    return _security_row(security, session)


@router.get("/sectors")
def list_sectors(
    session: Session = Depends(get_session),  # noqa: B008
    source: str | None = Query(default=None),
    skip: int = Query(default=0),
    limit: int = Query(default=50),
) -> dict:
    skip, limit = _pagination(skip, limit)
    query = session.query(Sector)
    if source:
        query = query.filter(Sector.source == source)
    total = query.count()
    rows = query.order_by(Sector.id).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "note": (
            "Source taxonomies are kept separate: a sector row's source and "
            "source_sector_name are the source's own values. No canonical "
            "sector is assigned by guesswork (canonical_sector_id is null "
            "unless a verified mapping exists)."
        ),
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "source_sector_name": s.source_sector_name,
                "source": s.source,
                "canonical_sector_id": s.canonical_sector_id,
            }
            for s in rows
        ],
    }


def _status_counts(session: Session, model) -> dict[str, int]:
    rows = session.query(model.status, func.count()).group_by(model.status).all()
    return {status: count for status, count in rows}


@router.get("/registry/statistics")
def registry_statistics(session: Session = Depends(get_session)) -> dict:  # noqa: B008
    return {
        "companies": session.query(Company).count(),
        "securities": session.query(Security).count(),
        "sectors": session.query(Sector).count(),
        "companies_by_status": _status_counts(session, Company),
        "securities_by_status": _status_counts(session, Security),
        "evidence_rows": session.query(RegistryEvidence).count(),
        "note": (
            "Counts are live database counts. Zero means the registry is "
            "empty, not that the market is empty."
        ),
    }


@router.get("/registry/quality")
def registry_quality(session: Session = Depends(get_session)) -> dict:  # noqa: B008
    company_status = _status_counts(session, Company)
    security_status = _status_counts(session, Security)
    return {
        "companies_by_status": company_status,
        "securities_by_status": security_status,
        "pending_review_companies": company_status.get("PENDING_REVIEW", 0),
        "conflicted_companies": company_status.get("CONFLICTED", 0),
        "verified_companies": company_status.get("VERIFIED", 0),
        "partially_verified_companies": company_status.get("PARTIALLY_VERIFIED", 0),
        "evidence_rows": session.query(RegistryEvidence).count(),
        "interpretation": (
            "VERIFIED means at least one evidence row from an official source "
            "(psx_official or secp) agrees with the stored record. "
            "PARTIALLY_VERIFIED means at least two distinct sources agree. "
            "An import succeeding never, by itself, verifies a record."
        ),
    }


@router.get("/registry/sources")
def registry_sources(session: Session = Depends(get_session)) -> dict:  # noqa: B008
    rows = session.query(DataSource).order_by(DataSource.id).all()
    return {
        "sources": [
            {
                "source_key": s.source_key,
                "display_name": s.display_name,
                "source_type": s.source_type,
                "base_reference": s.base_reference,
                "verification_status": s.verification_status,
            }
            for s in rows
        ],
        "sync_configs": [
            {
                "source_key": c.source_key,
                "frequency": c.frequency,
                "enabled": c.enabled,
                "note": c.note,
            }
            for c in DEFAULT_SYNC_CONFIGS
        ],
        "note": (
            "Sync is manual-only in Phase 4: no scheduler is started. "
            "Frequencies above are configuration values, not claims about "
            "how often a source actually updates."
        ),
    }
