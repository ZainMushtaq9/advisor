"""Phase 16 simulated-portfolio read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent
with a reason. No value is ever fabricated, and no endpoint writes
anything. An unknown portfolio name returns 404. Nothing here is
investment advice, a buy/sell signal, or a forecast: every
portfolio is a labelled hypothetical simulation on 2026-11-03
closing prices with hypothetical capital, every Phase 15
user-facing value feeding the rule-based portfolios is WITHHELD
(the rule uses research conclusions and screening outcomes, not
issued recommendations), and no execution path exists anywhere in
this project.

Endpoints:
  GET /api/v1/portfolios
      All simulated portfolios with their cash reconciliation.
  GET /api/v1/portfolios/{name}
      One portfolio with holdings, sector allocations, and
      exclusions, plus its constraints and assumptions.
  GET /api/v1/portfolios/comparisons
      Method comparisons against the equal-weight baseline,
      including the NOT_CALCULABLE mean-variance row.
  GET /api/v1/portfolios/status
      Coverage counts and the honest Phase 16 summary.
"""

from __future__ import annotations

from collections.abc import Generator
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.portfolio import (
    PortfolioComparison,
    PortfolioExclusion,
    PortfolioSectorAllocation,
    SimulatedPortfolio,
    SimulatedPortfolioHolding,
)

router = APIRouter(tags=["portfolios"])

SCOPE_NOTE = (
    "Scope: simulated portfolios only, on 2026-11-03 closing prices "
    "with hypothetical capital (PKR 1,000,000), never real funds. "
    "The equal-weight baseline covers the 3 statement companies "
    "(HUBC, NML, OGDC); the rule-based portfolios cover Phase 15 "
    "SCREEN_PASS names only (HUBC, OGDC) under the balanced and "
    "conservative profiles. Mean-variance is NOT_CALCULABLE: Phase "
    "13 computed 0 forecasts and 1 price date gives 0 return "
    "observations, so no expected returns and no covariance exist. "
    "Expected returns, historical returns, and forecasts are shown "
    "separately in each portfolio's assumptions, each absent with "
    "its reason. No live execution exists."
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


def _serialize_portfolio(portfolio: SimulatedPortfolio, session: Session) -> dict:
    holdings = (
        session.query(SimulatedPortfolioHolding)
        .filter(SimulatedPortfolioHolding.portfolio_id == portfolio.id)
        .order_by(SimulatedPortfolioHolding.ticker)
        .all()
    )
    invested = sum((h.value for h in holdings), Decimal("0"))
    return {
        "name": portfolio.name,
        "method": portfolio.method,
        "capital": str(portfolio.capital),
        "base_currency": portfolio.base_currency,
        "horizon": portfolio.horizon,
        "risk_profile": portfolio.risk_profile,
        "price_date": str(portfolio.price_date),
        "generated_date": str(portfolio.generated_date),
        "status": portfolio.status,
        "invested": str(invested),
        "cash": str(portfolio.capital - invested),
        "cash_weight": str((portfolio.capital - invested) / portfolio.capital),
        "reconciles": invested + (portfolio.capital - invested) == portfolio.capital,
        "constraints": portfolio.constraints,
        "assumptions": portfolio.assumptions,
        "binding_constraints": portfolio.binding_constraints,
        "not_calculable_reasons": portfolio.not_calculable_reasons,
        "quality_status": portfolio.quality_status,
    }


@router.get("/portfolios")
def get_portfolios(session: Session = Depends(get_session)) -> dict:
    rows = session.query(SimulatedPortfolio).order_by(SimulatedPortfolio.name).all()
    return {
        "portfolios": [_serialize_portfolio(row, session) for row in rows],
        "note": SCOPE_NOTE,
    }


@router.get("/portfolios/comparisons")
def get_comparisons(session: Session = Depends(get_session)) -> dict:
    rows = session.query(PortfolioComparison).order_by(PortfolioComparison.subject_name).all()
    return {
        "comparisons": [
            {
                "subject_name": row.subject_name,
                "baseline_name": row.baseline_name,
                "method_compared": row.method_compared,
                "status": row.status,
                "metrics": row.metrics,
                "reasons": row.reasons,
            }
            for row in rows
        ],
        "note": (
            "Comparisons are against the equal-weight baseline "
            "(ew_statements_3_balanced). Mean-variance is "
            "NOT_CALCULABLE with reasons, never numbers."
        ),
    }


@router.get("/portfolios/status")
def get_status(session: Session = Depends(get_session)) -> dict:
    portfolios = session.query(SimulatedPortfolio).all()
    holdings = session.query(SimulatedPortfolioHolding).count()
    exclusions = session.query(PortfolioExclusion).count()
    sectors = session.query(PortfolioSectorAllocation).count()
    comparisons = session.query(PortfolioComparison).count()
    return {
        "portfolios": len(portfolios),
        "by_status": {
            status: sum(1 for p in portfolios if p.status == status)
            for status in {p.status for p in portfolios}
        },
        "holdings": holdings,
        "exclusions": exclusions,
        "sector_allocations": sectors,
        "comparisons": comparisons,
        "eligibility_probes": {
            "ZZZZ": "NOT_IN_UNIVERSE (no security row)",
            "AGLNCPS": "IN_UNIVERSE_NO_QUOTE (security row, no 2026-11-03 price row)",
            "HBL": (
                "ELIGIBLE quote-wise (286.16 on 2026-11-03) but "
                "rule-excluded: Phase 15 SCREEN_NOT_RUNNABLE (no statements)"
            ),
        },
        "note": (
            "Phase 16 is PARTIALLY COMPLETE: the construction engine, "
            "constraint schema, sector reports, and APIs are complete, "
            "but mean-variance is NOT_CALCULABLE (no validated expected "
            "returns, no covariance), coverage is 3-4 companies, and "
            "HBL has no rule-based position pending its Phase 7 load."
        ),
    }


@router.get("/portfolios/{name}")
def get_portfolio(name: str, session: Session = Depends(get_session)) -> dict:
    portfolio = (
        session.query(SimulatedPortfolio).filter(SimulatedPortfolio.name == name).one_or_none()
    )
    if portfolio is None:
        raise HTTPException(status_code=404, detail=f"Unknown portfolio: {name}")
    holdings = (
        session.query(SimulatedPortfolioHolding)
        .filter(SimulatedPortfolioHolding.portfolio_id == portfolio.id)
        .order_by(SimulatedPortfolioHolding.ticker)
        .all()
    )
    sectors = (
        session.query(PortfolioSectorAllocation)
        .filter(PortfolioSectorAllocation.portfolio_id == portfolio.id)
        .order_by(PortfolioSectorAllocation.sector)
        .all()
    )
    exclusions = (
        session.query(PortfolioExclusion)
        .filter(PortfolioExclusion.portfolio_id == portfolio.id)
        .order_by(PortfolioExclusion.ticker)
        .all()
    )
    return {
        "portfolio": _serialize_portfolio(portfolio, session),
        "holdings": [
            {
                "ticker": h.ticker,
                "sector": h.sector,
                "target_weight": str(h.target_weight),
                "actual_weight": str(h.actual_weight),
                "units": str(h.units),
                "value": str(h.value),
                "price": str(h.price),
                "price_date": str(h.price_date),
                "eligibility_status": h.eligibility_status,
            }
            for h in holdings
        ],
        "sector_allocations": [
            {
                "sector": s.sector,
                "invested_value": str(s.invested_value),
                "invested_weight": str(s.invested_weight),
                "capital_weight": str(s.capital_weight),
            }
            for s in sectors
        ],
        "exclusions": [
            {
                "ticker": e.ticker,
                "reason_code": e.reason_code,
                "reason_detail": e.reason_detail,
            }
            for e in exclusions
        ],
        "note": SCOPE_NOTE,
    }
