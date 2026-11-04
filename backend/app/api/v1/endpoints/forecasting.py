"""Phase 13 forecasting read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent with
a reason. No value is ever fabricated, and no endpoint writes
anything. An unknown ticker returns 404; a known ticker with no rows
returns 200 with an empty list and a note. No forecast is served:
the Phase 3 ``forecasts`` table holds 0 rows because no interval is
validatable from one trading date, and a point estimate without a
validated interval is not a Phase 13 forecast — so the assessments
endpoint serves the abstention reasons instead. Nothing here is
investment advice or a buy/sell signal.

Endpoints:
  GET /api/v1/forecasting/targets
      The 48-row target registry (8 targets x 6 horizons).
  GET /api/v1/forecasting/assessments?ticker=
      Per-target, per-horizon assessments for one company.
  GET /api/v1/forecasting/assessments/macro
      Macro-target assessments (security NULL).
  GET /api/v1/forecasting/features?ticker=
      Feature-store snapshots for one company as of the origin.
  GET /api/v1/forecasting/status
      Coverage counts, including the Phase 3 forecasts count (0)
      with the reason it is 0.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.analysis import Forecast
from app.models.forecasting import (
    ForecastAssessment,
    ForecastFeatureSnapshot,
    ForecastTarget,
)
from app.models.reference import Security

router = APIRouter(tags=["forecasting"])

SCOPE_NOTE = (
    "Scope: analysis universe is HUBC, NML, OGDC (the statement "
    "companies); HBL is pending its Phase 7 load. One trading date "
    "(2026-11-03) of prices, zero calculable technical values, "
    "single-period statements: every assessment is "
    "insufficient_inputs, no forecast is stored, and the Phase 3 "
    "forecasts table holds 0 rows because no interval is validatable "
    "from one observation. Point-only baselines are recorded as "
    "abstained in each assessment's evidence, never served as "
    "forecasts."
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


def _security(session: Session, ticker: str) -> Security:
    row = session.query(Security).filter_by(ticker=ticker).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker {ticker}.")
    return row


def _assessment_row(row: ForecastAssessment) -> dict:
    return {
        "target_key": row.target_key,
        "horizon": row.horizon,
        "origin_date": str(row.origin_date),
        "method": row.method,
        "computation_status": row.computation_status,
        "point_estimate": None if row.point_estimate is None else str(row.point_estimate),
        "reason": row.reason,
        "evidence": row.evidence,
    }


@router.get("/forecasting/targets")
def list_targets(session: Session = Depends(get_session)) -> dict:
    rows = (
        session.query(ForecastTarget)
        .order_by(ForecastTarget.target_key, ForecastTarget.horizon)
        .all()
    )
    return {
        "targets": [
            {
                "target_key": row.target_key,
                "horizon": row.horizon,
                "target_type": row.target_type,
                "scope": row.scope,
                "min_observations": row.min_observations,
                "status": row.status,
            }
            for row in rows
        ],
        "count": len(rows),
    }


@router.get("/forecasting/assessments")
def company_assessments(ticker: str, session: Session = Depends(get_session)) -> dict:
    security = _security(session, ticker)
    rows = (
        session.query(ForecastAssessment)
        .filter(ForecastAssessment.security_id == security.id)
        .order_by(ForecastAssessment.target_key, ForecastAssessment.horizon)
        .all()
    )
    if not rows:
        return {
            "ticker": ticker,
            "assessments": [],
            "note": "No assessments stored for this ticker.",
        }
    return {"ticker": ticker, "assessments": [_assessment_row(r) for r in rows]}


@router.get("/forecasting/assessments/macro")
def macro_assessments(session: Session = Depends(get_session)) -> dict:
    rows = (
        session.query(ForecastAssessment)
        .filter(ForecastAssessment.security_id.is_(None))
        .order_by(ForecastAssessment.target_key, ForecastAssessment.horizon)
        .all()
    )
    return {"assessments": [_assessment_row(r) for r in rows]}


@router.get("/forecasting/features")
def company_features(ticker: str, session: Session = Depends(get_session)) -> dict:
    security = _security(session, ticker)
    rows = (
        session.query(ForecastFeatureSnapshot)
        .filter(ForecastFeatureSnapshot.security_id == security.id)
        .order_by(ForecastFeatureSnapshot.feature_key)
        .all()
    )
    if not rows:
        return {
            "ticker": ticker,
            "features": [],
            "note": "No feature snapshots stored for this ticker.",
        }
    return {
        "ticker": ticker,
        "origin_date": str(rows[0].origin_date),
        "features": [
            {
                "feature_key": row.feature_key,
                "feature_value": None if row.feature_value is None else str(row.feature_value),
                "evidence": row.evidence,
            }
            for row in rows
        ],
    }


@router.get("/forecasting/status")
def status(session: Session = Depends(get_session)) -> dict:
    return {
        "scope_note": SCOPE_NOTE,
        "targets": session.query(ForecastTarget).count(),
        "feature_snapshots": session.query(ForecastFeatureSnapshot).count(),
        "assessments": session.query(ForecastAssessment).count(),
        "assessments_computed": session.query(ForecastAssessment)
        .filter(ForecastAssessment.computation_status == "computed")
        .count(),
        "phase3_forecasts": session.query(Forecast).count(),
        "phase3_forecasts_note": (
            "0 by design: the Phase 3 forecasts table requires non-null "
            "intervals, and no interval is validatable from one trading "
            "date. See docs/phase-13/abstention_report.md."
        ),
    }
