"""Phase 14 risk read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent
with a reason. No value is ever fabricated, and no endpoint writes
anything. An unknown ticker returns 404; a known ticker with no
rows returns 200 with an empty list and a note. Nothing here is
investment advice, a buy/sell signal, or a forecast: stress results
are labelled simulation arithmetic on 2026-11-03 closes, and
series risk metrics are served as insufficient_inputs rows with
their reasons, never as numbers.

Endpoints:
  GET /api/v1/risk/metrics
      The 22-row risk metric library.
  GET /api/v1/risk/profile?ticker=
      Per-security risk values (computed + insufficient).
  GET /api/v1/risk/market
      Market-scope values (sector participation, coverage, model risk).
  GET /api/v1/risk/flags?ticker=
      Risk flags for one company (or market flags with no ticker).
  GET /api/v1/risk/controls
      Control rules v1 and their checks.
  GET /api/v1/risk/stress
      Stress scenarios and results (simulation only).
  GET /api/v1/risk/status
      Coverage counts and the honest Phase 14 summary.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.reference import Security
from app.models.risk import (
    RiskControl,
    RiskControlCheck,
    RiskFlag,
    RiskMetricDefinition,
    RiskMetricValue,
    StressResult,
    StressScenario,
)

router = APIRouter(tags=["risk"])

SCOPE_NOTE = (
    "Scope: analysis universe is HUBC, NML, OGDC (the statement "
    "companies); HBL is pending its Phase 7 load. One trading date "
    "(2026-11-03) of prices, zero calculable technical values, "
    "previous_close NULL on all rows: every series risk metric is "
    "insufficient_inputs. Stress results are simulation arithmetic "
    "on a stated equal-weight reference portfolio, never a forecast "
    "and never investment advice. No live execution exists."
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


def _value_row(row: RiskMetricValue) -> dict:
    return {
        "metric_key": row.metric_key,
        "scope_key": row.scope_key,
        "as_of_date": str(row.as_of_date),
        "value": None if row.value is None else str(row.value),
        "computation_status": row.computation_status,
        "reason": row.reason,
        "evidence": row.evidence,
    }


@router.get("/risk/metrics")
def list_metrics(session: Session = Depends(get_session)) -> dict:
    rows = (
        session.query(RiskMetricDefinition)
        .order_by(RiskMetricDefinition.category, RiskMetricDefinition.metric_key)
        .all()
    )
    return {
        "metrics": [
            {
                "metric_key": r.metric_key,
                "category": r.category,
                "formula": r.formula,
                "min_observations": r.min_observations,
                "window": r.window,
                "unit": r.unit,
                "scope": r.scope,
            }
            for r in rows
        ],
        "count": len(rows),
    }


@router.get("/risk/profile")
def company_profile(ticker: str, session: Session = Depends(get_session)) -> dict:
    security = _security(session, ticker)
    rows = (
        session.query(RiskMetricValue)
        .filter(RiskMetricValue.security_id == security.id)
        .order_by(RiskMetricValue.metric_key)
        .all()
    )
    flags = (
        session.query(RiskFlag)
        .filter(RiskFlag.company_id == security.company_id)
        .order_by(RiskFlag.flag_type)
        .all()
    )
    return {
        "ticker": ticker,
        "values": [_value_row(r) for r in rows],
        "flags": [
            {
                "flag_type": f.flag_type,
                "severity": f.severity,
                "as_of_date": str(f.as_of_date),
                "evidence": f.evidence,
            }
            for f in flags
        ],
        "note": SCOPE_NOTE,
    }


@router.get("/risk/market")
def market_values(session: Session = Depends(get_session)) -> dict:
    rows = (
        session.query(RiskMetricValue)
        .filter(RiskMetricValue.security_id.is_(None))
        .order_by(RiskMetricValue.metric_key, RiskMetricValue.scope_key)
        .all()
    )
    flags = (
        session.query(RiskFlag)
        .filter(RiskFlag.company_id.is_(None))
        .order_by(RiskFlag.flag_type)
        .all()
    )
    return {
        "values": [_value_row(r) for r in rows],
        "market_flags": [
            {
                "flag_type": f.flag_type,
                "severity": f.severity,
                "evidence": f.evidence,
            }
            for f in flags
        ],
    }


@router.get("/risk/controls")
def list_controls(session: Session = Depends(get_session)) -> dict:
    rules = session.query(RiskControl).order_by(RiskControl.control_key).all()
    checks = (
        session.query(RiskControlCheck)
        .order_by(RiskControlCheck.control_key, RiskControlCheck.scope_key)
        .all()
    )
    return {
        "rules": [
            {
                "control_key": r.control_key,
                "version": r.version,
                "rule": r.rule,
                "rationale": r.rationale,
                "effective_date": str(r.effective_date),
            }
            for r in rules
        ],
        "checks": [
            {
                "control_key": c.control_key,
                "version": c.version,
                "scope_key": c.scope_key,
                "outcome": c.outcome,
                "observed_value": None if c.observed_value is None else str(c.observed_value),
                "threshold_value": None if c.threshold_value is None else str(c.threshold_value),
                "reason": c.reason,
            }
            for c in checks
        ],
    }


@router.get("/risk/stress")
def list_stress(session: Session = Depends(get_session)) -> dict:
    scenarios = session.query(StressScenario).order_by(StressScenario.scenario_key).all()
    results = (
        session.query(StressResult)
        .order_by(StressResult.scenario_key, StressResult.scope_key)
        .all()
    )
    return {
        "scenarios": [
            {
                "scenario_key": s.scenario_key,
                "shock": s.shock,
                "applies_to": s.applies_to,
                "method": s.method,
            }
            for s in scenarios
        ],
        "results": [
            {
                "scenario_key": r.scenario_key,
                "scope_key": r.scope_key,
                "impact_pct": None if r.impact_pct is None else str(r.impact_pct),
                "computation_status": r.computation_status,
                "reason": r.reason,
                "evidence": r.evidence,
            }
            for r in results
        ],
        "note": "Simulation arithmetic only — not a forecast, not investment advice.",
    }


@router.get("/risk/status")
def status(session: Session = Depends(get_session)) -> dict:
    n_defs = session.query(RiskMetricDefinition).count()
    n_vals = session.query(RiskMetricValue).count()
    n_computed = (
        session.query(RiskMetricValue)
        .filter(RiskMetricValue.computation_status == "computed")
        .count()
    )
    n_flags = session.query(RiskFlag).count()
    n_checks = session.query(RiskControlCheck).count()
    n_stress = session.query(StressResult).count()
    return {
        "metric_definitions": n_defs,
        "metric_values": n_vals,
        "metric_values_computed": n_computed,
        "metric_values_insufficient": n_vals - n_computed,
        "flags": n_flags,
        "control_checks": n_checks,
        "stress_results": n_stress,
        "note": SCOPE_NOTE,
    }
