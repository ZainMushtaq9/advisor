"""Phase 4 universe endpoint (completion addendum).

GET /api/v1/data/universe — read-only summary of the central universe,
as required by the Phase 4 brief: metadata, provenance, freshness,
validation counts, and scope limitations. It NEVER returns the ticker
list and NEVER returns a CSV dump: consumers that need identities use
the paginated /companies and /securities endpoints.

All counts are live database counts. Zero means the registry is empty,
not that the market is empty. When no database is configured, the
endpoint answers 503 with a truthful reason, never a fake universe.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.registry import get_session
from app.models.reference import Company, Sector, Security
from app.models.registry import RegistryEvidence

router = APIRouter(tags=["universe"])


def _status_counts(rows: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = getattr(row, "status", None)
        counts[status] = counts.get(status, 0) + 1
    return counts


def _iso(value) -> str | None:
    if value is None:
        return None
    iso = getattr(value, "isoformat", None)
    return iso() if callable(iso) else str(value)


@router.get("/data/universe")
def data_universe(session: Session = Depends(get_session)) -> dict:  # noqa: B008
    companies = session.query(Company).all()
    securities = session.query(Security).all()
    evidence = session.query(RegistryEvidence).all()
    collected = [e.collected_at for e in evidence if e.collected_at is not None]
    return {
        "scope": "Main Board / Normal Counter only",
        "scope_limitations": [
            "GEM (Normal and Non-Compliant) is excluded: counted, not captured.",
            "Main Board Non-Compliant / Winding-Up is excluded: counted, "
            "not captured.",
            "No KSE-100 completeness claim is made on the basis of this "
            "registry.",
            "No identifier (ISIN or other) coverage is claimed: the "
            "snapshot source carries no ISINs.",
        ],
        "companies": len(companies),
        "securities": len(securities),
        "sectors": session.query(Sector).count(),
        "companies_by_status": _status_counts(companies),
        "securities_by_status": _status_counts(securities),
        "evidence_rows": len(evidence),
        "sources": sorted({e.source_key for e in evidence}),
        "freshness": {
            "evidence_collected_earliest": _iso(min(collected)) if collected else None,
            "evidence_collected_latest": _iso(max(collected)) if collected else None,
            "note": (
                "collected_at is the time the evidence was collected, "
                "never a source timestamp. A snapshot dated 2026-11-04 "
                "stays a 2026-11-04 snapshot however late it is read."
            ),
        },
        "verification": (
            "Under rule H1, VERIFIED requires at least two distinct "
            "agreeing sources including one official (psx_official or "
            "secp); a single source leaves a record UNVERIFIED. "
            "No record in this registry is VERIFIED on a single source."
        ),
        "dump_note": (
            "This endpoint never returns the ticker list or a CSV dump. "
            "Use the paginated /companies and /securities endpoints for "
            "identity rows."
        ),
    }
