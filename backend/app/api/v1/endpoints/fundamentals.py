"""Phase 8 fundamental-analysis read-only endpoints (GET only).

Everything here is computed from statement rows that actually exist,
or explained as NOT_CALCULABLE / not_applicable with a reason. No
value is ever fabricated, and no endpoint writes anything. The
committed record lives in fundamental_metric_values /
financial_health_assessments; these endpoints run the same pure
assessment live so every verdict carries its reason.

Endpoints:
  GET /api/v1/fundamentals/ratios?ticker=&period_end=
      Assessed metrics for one company-period (computed values plus
      NOT_CALCULABLE reasons). period_end defaults to the configured
      current period_end for the ticker.
  GET /api/v1/fundamentals/health?ticker=&period_end=
      Health-v1 dimension scores with evidence and the disclaimer.
  GET /api/v1/fundamentals/sector-profiles?ticker=
      Sector applicability notes for the company's sector.

When no database is configured, endpoints answer 503 with a
truthful reason, never a fake empty market. An unknown ticker
returns 404; a known ticker with no statements returns 200 with an
empty assessment and a no_inputs note. Health scores are descriptive
only: NOT a credit rating, NOT investment advice, NOT a buy/sell
signal.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.reference import Company, Security
from app.services.fundamental_analysis import (
    PENDING_COMPANIES,
    PERIODS,
    coverage,
    health,
    runner,
    warnings,
)

router = APIRouter(tags=["fundamentals"])

SCOPE_NOTE = (
    "Scope: three companies with Phase 7 statements (HUBC, NML, OGDC); "
    "all inputs UNVERIFIED. HBL (Habib Bank Limited) is PENDING — its "
    "CY2025 statements are not loaded yet, so it has no ratios. Market "
    "multiples are NOT_CALCULABLE in v1.0 (see the ratio dictionary). "
    "Health scores are descriptive only, never a credit rating."
)


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


def _resolve_company(session: Session, ticker: str) -> tuple[int, str]:
    sec = session.query(Security).filter(Security.ticker == ticker).one_or_none()
    if sec is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    return sec.company_id, ticker


def _assess(session: Session, ticker: str, period_end: str | None) -> dict:
    company_id, _ = _resolve_company(session, ticker)
    if company_id in PENDING_COMPANIES:
        return {
            "ticker": ticker,
            "status": "pending",
            "note": PENDING_COMPANIES[company_id],
            "scope": SCOPE_NOTE,
        }
    if company_id not in PERIODS:
        return {
            "ticker": ticker,
            "status": "no_configured_period",
            "note": "No Phase 8 period configuration exists for this company.",
            "scope": SCOPE_NOTE,
        }
    cfg = PERIODS[company_id]
    if period_end is not None and period_end != cfg["flow_current"][1]:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No configured Phase 8 period ends {period_end} for {ticker}; "
                f"configured period_end is {cfg['flow_current'][1]}."
            ),
        )
    inputs, stmt_ids, notes = runner.load_period_inputs(session, company_id)
    if not stmt_ids:
        return {
            "ticker": ticker,
            "status": "no_inputs",
            "note": "No current Phase 7 statements found for this company-period.",
            "scope": SCOPE_NOTE,
        }
    results = coverage.assess(company_id, inputs)
    values = {r["metric_key"]: r["value"] for r in results}
    flags = {r["metric_key"]: r.get("flags", []) for r in results}
    warn_inputs = dict(values)
    warn_inputs["_pat_cur"] = inputs.get("pat_cur")
    warn_inputs["_ocf_cur"] = inputs.get("ocf_cur")
    return {
        "ticker": ticker,
        "status": "assessed",
        "period_label": cfg["label"],
        "period_end": cfg["flow_current"][1],
        "period_days": inputs["period_days"],
        "loader_notes": notes,
        "metrics": [
            {
                "metric_key": r["metric_key"],
                "status": r["status"],
                "value": str(r["value"]) if r["value"] is not None else None,
                "reason": r["reason"],
                "flags": r["flags"],
            }
            for r in results
        ],
        "health": {
            cat: {
                "score": str(v["score"]) if v["score"] is not None else None,
                "evidence": v["evidence"],
            }
            for cat, v in health.score_dimensions(values, flags).items()
        },
        "warnings": warnings.build_warnings(warn_inputs, results),
        "scope": SCOPE_NOTE,
    }


@router.get("/fundamentals/ratios")
def get_ratios(
    ticker: str, period_end: str | None = None, session: Session = Depends(get_session)
) -> dict:
    return _assess(session, ticker, period_end)


@router.get("/fundamentals/health")
def get_health(
    ticker: str, period_end: str | None = None, session: Session = Depends(get_session)
) -> dict:
    result = _assess(session, ticker, period_end)
    return {
        "ticker": result["ticker"],
        "status": result["status"],
        "period_label": result.get("period_label"),
        "period_end": result.get("period_end"),
        "health": result.get("health"),
        "warnings": result.get("warnings"),
        "scope": SCOPE_NOTE,
    }


@router.get("/fundamentals/sector-profiles")
def get_sector_profiles(ticker: str, session: Session = Depends(get_session)) -> dict:
    company_id, _ = _resolve_company(session, ticker)
    company = session.query(Company).filter_by(id=company_id).one_or_none()
    if company is None or not getattr(company, "sector_id", None):
        raise HTTPException(status_code=404, detail=f"No sector recorded for {ticker}.")
    from app.models.analysis import SectorMetricProfile
    from app.models.reference import Sector

    sector = session.query(Sector).filter_by(id=company.sector_id).one_or_none()
    rows = (
        session.query(SectorMetricProfile)
        .filter_by(sector_id=company.sector_id)
        .order_by(SectorMetricProfile.metric_key)
        .all()
    )
    return {
        "ticker": ticker,
        "sector": sector.name if sector is not None else None,
        "profiles": [
            {
                "metric_key": r.metric_key,
                "applicability": r.applicability,
                "source_requirements": r.source_requirements,
                "is_active": r.is_active,
            }
            for r in rows
        ],
        "note": (
            "Empty until a Phase 8 commit writes the profiles; "
            "applicability rules are documented in sector_profiles.md."
            if not rows
            else None
        ),
        "scope": SCOPE_NOTE,
    }
