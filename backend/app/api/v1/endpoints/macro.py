"""Phase 10 macro/sector read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent with a
reason. No value is ever fabricated, and no endpoint writes anything.
Point-in-time retrieval uses only data publicly available on the
chosen date (publication date where known, else collection date).

Endpoints:
  GET /api/v1/macro
      Indicator registry + latest current observation per indicator.
  GET /api/v1/macro/point-in-time?indicator=&as_of=
      The observation publicly known at as_of (or an explicit absence).
  GET /api/v1/macro/regimes
      Regime assessments with their evidence and not-assigned labels.
  GET /api/v1/macro/exposures?ticker=
      Issuer-evidenced exposures for one company (pending for HBL).
  GET /api/v1/macro/events
      Dated policy/release event calendar.
  GET /api/v1/macro/sectors
      Sector indicator profiles (framework notes, not company claims).

When no database is configured, endpoints answer 503 with a truthful
reason, never a fake empty market. An unknown ticker returns 404; a
known ticker with no statements returns 200 with an empty exposure
list and a no_inputs note. Macro context is descriptive only — never
a forecast presented as fact, never investment advice, never a
buy/sell signal.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.analysis import EconomicIndicator, SectorMetricProfile
from app.models.macro import CompanyMacroExposure, MacroEvent, MacroRegime
from app.models.reference import Security
from app.services.macro_analysis import INDICATORS, NOT_STORED, PENDING_COMPANIES, formulas

router = APIRouter(tags=["macro"])

PKT = ZoneInfo("Asia/Karachi")

SCOPE_NOTE = (
    "Scope: 12 macro observations from two official sources read directly "
    "(SBP Monetary Policy Statement 2026-10-26; PBS homepage) — 6 VERIFIED "
    "under rule H1, 6 UNVERIFIED. October 2026 CPI YoY, KIBOR/yields, "
    "USD/PKR, commodity prices, remittance/trade levels, fiscal balances "
    "and budget dates are NOT stored (see /macro/not-stored in the run "
    "report); they are absent, never estimated. HBL (Habib Bank Limited) "
    "is PENDING — its CY2025 statements are not loaded yet, so it has no "
    "exposures. Macro context is descriptive only: not a forecast, not "
    "investment advice, not a buy/sell signal."
)


def get_session(request: Request) -> Generator[Session, None, None]:
    factory = get_session_factory(request.app.state.engine)
    if factory is None:
        raise HTTPException(status_code=503, detail="No database configured.")
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _resolve_company(session: Session, ticker: str) -> Security:
    security = session.query(Security).filter(Security.ticker == ticker).first()
    if security is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    return security


def _obs_to_dict(row: EconomicIndicator) -> dict:
    return {
        "indicator_code": row.indicator_code,
        "indicator_name": row.indicator_name,
        "observation_date": str(row.observation_date),
        "value": str(row.value) if row.value is not None else None,
        "unit": row.unit,
        "frequency": row.frequency,
        "source_key": row.source_key,
        "source_timestamp": row.source_timestamp.astimezone(PKT).date().isoformat()
        if row.source_timestamp is not None
        else None,
        "collected_at": row.collected_at.astimezone(PKT).date().isoformat()
        if row.collected_at is not None
        else None,
        "quality_status": row.quality_status,
        "version_number": row.version_number,
    }


@router.get("/macro")
def list_macro(session: Session = Depends(get_session)):
    """Indicator registry + latest current observation per indicator."""
    out = []
    for code, meta in INDICATORS.items():
        row = (
            session.query(EconomicIndicator)
            .filter(
                EconomicIndicator.indicator_code == code,
                EconomicIndicator.is_current.is_(True),
            )
            .order_by(EconomicIndicator.observation_date.desc())
            .first()
        )
        out.append(
            {
                "indicator_code": code,
                "name": meta["name"],
                "unit": meta["unit"],
                "frequency": meta["frequency"],
                "publisher": meta["publisher"],
                "latest": _obs_to_dict(row) if row is not None else None,
            }
        )
    return {"indicators": out, "scope_note": SCOPE_NOTE}


@router.get("/macro/point-in-time")
def point_in_time(
    indicator: str,
    as_of: str,
    session: Session = Depends(get_session),
):
    """Observation publicly known at as_of (or an explicit absence)."""
    if indicator not in INDICATORS:
        raise HTTPException(status_code=404, detail=f"Unknown indicator: {indicator}")
    try:
        date.fromisoformat(as_of)
    except ValueError:
        raise HTTPException(status_code=422, detail="as_of must be YYYY-MM-DD") from None
    rows = (
        session.query(EconomicIndicator)
        .filter(
            EconomicIndicator.indicator_code == indicator,
            EconomicIndicator.is_current.is_(True),
        )
        .all()
    )
    dicts = []
    for row in rows:
        d = _obs_to_dict(row)
        d["source_timestamp"] = d["source_timestamp"]
        d["collected_at"] = d["collected_at"]
        dicts.append(d)
    found = formulas.point_in_time(dicts, as_of)
    if found is None:
        return {
            "indicator_code": indicator,
            "as_of": as_of,
            "status": "absent",
            "reason": "no observation for this indicator was publicly available on that date",
            "observation": None,
        }
    return {
        "indicator_code": indicator,
        "as_of": as_of,
        "status": "known",
        "observation": found,
    }


@router.get("/macro/regimes")
def list_regimes(session: Session = Depends(get_session)):
    """Regime assessments with evidence and not-assigned labels."""
    rows = session.query(MacroRegime).order_by(MacroRegime.observation_date.desc()).all()
    return {
        "regimes": [
            {
                "observation_date": str(r.observation_date),
                "regime_label": r.regime_label,
                "method_version": r.method_version,
                "evidence": r.evidence,
                "quality_status": r.quality_status,
            }
            for r in rows
        ],
        "scope_note": SCOPE_NOTE,
    }


@router.get("/macro/exposures")
def list_exposures(ticker: str, session: Session = Depends(get_session)):
    """Issuer-evidenced exposures for one company."""
    security = _resolve_company(session, ticker)
    company_id = security.company_id
    if company_id in PENDING_COMPANIES:
        return {
            "ticker": ticker,
            "status": "pending",
            "reason": PENDING_COMPANIES[company_id],
            "exposures": [],
            "scope_note": SCOPE_NOTE,
        }
    rows = (
        session.query(CompanyMacroExposure)
        .filter(
            CompanyMacroExposure.company_id == company_id,
            CompanyMacroExposure.is_current.is_(True),
        )
        .all()
    )
    return {
        "ticker": ticker,
        "company_id": company_id,
        "status": "ok" if rows else "no_inputs",
        "exposures": [
            {
                "exposure_key": r.exposure_key,
                "exposure_name": r.exposure_name,
                "direction": r.direction,
                "evidence_type": r.evidence_type,
                "evidence_ref": r.evidence_ref,
                "note": r.note,
                "quality_status": r.quality_status,
            }
            for r in rows
        ],
        "scope_note": SCOPE_NOTE,
    }


@router.get("/macro/events")
def list_events(session: Session = Depends(get_session)):
    """Dated policy/release event calendar."""
    rows = session.query(MacroEvent).order_by(MacroEvent.event_date).all()
    return {
        "events": [
            {
                "event_date": str(r.event_date),
                "event_type": r.event_type,
                "title": r.title,
                "note": r.note,
                "source_key": r.source_key,
                "quality_status": r.quality_status,
            }
            for r in rows
        ],
        "scope_note": SCOPE_NOTE,
    }


@router.get("/macro/sectors")
def list_sector_profiles(session: Session = Depends(get_session)):
    """Sector indicator profiles (framework notes, not company claims)."""
    rows = (
        session.query(SectorMetricProfile)
        .filter(SectorMetricProfile.metric_key.like("macro:%"))
        .order_by(SectorMetricProfile.sector_id, SectorMetricProfile.metric_key)
        .all()
    )
    return {
        "profiles": [
            {
                "sector_id": r.sector_id,
                "metric_key": r.metric_key,
                "applicability": r.applicability,
                "source_requirements": r.source_requirements,
                "is_active": r.is_active,
            }
            for r in rows
        ],
        "not_stored": NOT_STORED,
        "scope_note": SCOPE_NOTE,
    }
