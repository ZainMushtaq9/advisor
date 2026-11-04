"""Phase 12 ownership/actions/breadth read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent with
a reason. No value is ever fabricated, and no endpoint writes
anything. An unknown ticker returns 404; a known ticker with no rows
returns 200 with an empty list and a note. No adjusted price series
is served (no stored action has an ex-date); no flow data is served
(the table is intentionally empty); nothing here is investment advice
or a buy/sell signal.

Endpoints:
  GET /api/v1/ownership?ticker=
      Ownership holdings for one company (categories + named holders).
  GET /api/v1/actions?ticker=
      Corporate actions for one company.
  GET /api/v1/breadth
      Market breadth metrics for the latest trading date + scope note.
  GET /api/v1/liquidity?ticker=
      Liquidity observations for one security, or market rows without
      a ticker.
  GET /api/v1/flows
      Always an empty list with the no-data explanation.
  GET /api/v1/adjustment-rules
      Adjustment rule definitions and their application status.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.ownership_actions import (
    AdjustmentRule,
    CorporateActionRecord,
    InvestorFlow,
    LiquidityObservation,
    MarketBreadth,
    OwnershipHolding,
)
from app.models.reference import Security

router = APIRouter(tags=["ownership"])

SCOPE_NOTE = (
    "Scope: HUBC ownership as at 2026-06-30 (one issuer document); "
    "5 dividend actions (HUBC 4, NML 1) with per-share amounts but no "
    "ex/record/payment dates published in the loaded statements; "
    "breadth for 2026-11-03 only (444/470 priced; advances/declines, "
    "new highs/lows and turnover distribution not calculable); "
    "investor flows intentionally empty (no verified published series "
    "loaded; flows are never derived from price/volume)."
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


def _company_id(session: Session, ticker: str) -> int:
    row = session.query(Security).filter_by(ticker=ticker).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker {ticker}.")
    return row.company_id


def _holding_row(row: OwnershipHolding) -> dict:
    return {
        "holder_category": row.holder_category,
        "holder_name": row.holder_name,
        "folio": row.folio,
        "reporting_date": str(row.reporting_date),
        "shareholders_count": row.shareholders_count,
        "shares_held": row.shares_held,
        "percentage": str(row.percentage) if row.percentage is not None else None,
        "is_total": row.is_total,
        "quality_status": row.quality_status,
    }


@router.get("/ownership")
def ownership(ticker: str, session: Session = Depends(get_session)):
    company_id = _company_id(session, ticker)
    rows = (
        session.query(OwnershipHolding)
        .filter_by(company_id=company_id)
        .order_by(OwnershipHolding.is_total, OwnershipHolding.holder_category)
        .all()
    )
    return {
        "ticker": ticker,
        "rows": [_holding_row(row) for row in rows],
        "note": "Empty for companies other than HUBC: only the HUBC annual "
        "report shareholding tables were loaded in this run."
        if not rows
        else "Categories and named key holders as printed.",
    }


@router.get("/actions")
def actions(ticker: str, session: Session = Depends(get_session)):
    company_id = _company_id(session, ticker)
    rows = (
        session.query(CorporateActionRecord)
        .filter_by(company_id=company_id)
        .order_by(CorporateActionRecord.fiscal_year_label)
        .all()
    )
    return {
        "ticker": ticker,
        "actions": [
            {
                "action_type": row.action_type,
                "fiscal_year_label": row.fiscal_year_label,
                "amount_per_share": str(row.amount_per_share)
                if row.amount_per_share is not None
                else None,
                "total_amount": str(row.total_amount) if row.total_amount is not None else None,
                "total_amount_note": row.total_amount_note,
                "announced_date": str(row.announced_date) if row.announced_date else None,
                "ex_date": str(row.ex_date) if row.ex_date else None,
                "record_date": str(row.record_date) if row.record_date else None,
                "effective_date": str(row.effective_date) if row.effective_date else None,
                "payment_date": str(row.payment_date) if row.payment_date else None,
                "date_evidence": row.date_evidence,
                "status": row.status,
                "quality_status": row.quality_status,
            }
            for row in rows
        ],
    }


@router.get("/breadth")
def breadth(session: Session = Depends(get_session)):
    rows = (
        session.query(MarketBreadth).order_by(MarketBreadth.scope, MarketBreadth.metric_key).all()
    )
    dates = sorted({str(row.trading_date) for row in rows})
    return {
        "trading_dates": dates,
        "metrics": [
            {
                "trading_date": str(row.trading_date),
                "scope": row.scope,
                "metric_key": row.metric_key,
                "metric_value": str(row.metric_value) if row.metric_value is not None else None,
                "numerator": row.numerator,
                "denominator": row.denominator,
                "status": row.status,
                "coverage_note": row.coverage_note,
            }
            for row in rows
        ],
        "scope_note": SCOPE_NOTE,
    }


@router.get("/liquidity")
def liquidity(ticker: str | None = None, session: Session = Depends(get_session)):
    if ticker is None:
        rows = session.query(LiquidityObservation).filter_by(scope_key="MARKET").all()
        return {
            "ticker": None,
            "rows": [
                {
                    "metric_key": row.metric_key,
                    "metric_value": str(row.metric_value) if row.metric_value is not None else None,
                    "status": row.status,
                    "coverage_note": row.coverage_note,
                }
                for row in rows
            ],
        }
    company_id = _company_id(session, ticker)
    sec = session.query(Security).filter_by(company_id=company_id).first()
    rows = session.query(LiquidityObservation).filter_by(scope_key=f"SEC:{ticker}").all()
    return {
        "ticker": ticker,
        "security_id": sec.id if sec else None,
        "rows": [
            {
                "metric_key": row.metric_key,
                "metric_value": str(row.metric_value) if row.metric_value is not None else None,
                "status": row.status,
                "coverage_note": row.coverage_note,
            }
            for row in rows
        ],
        "note": "Empty when the security has no price row on the breadth date."
        if not rows
        else "Volume and volume share on the breadth date.",
    }


@router.get("/flows")
def flows(session: Session = Depends(get_session)):
    rows = session.query(InvestorFlow).all()
    return {
        "rows": [],
        "count": len(rows),
        "note": "Investor flows are intentionally empty in Phase 12: no "
        "verified published flow series was loaded, and flows are "
        "never derived from price/volume. Unblocker: a terms-reviewed "
        "SBP SCRA/FPI monthly series or NCCPL published flow series.",
    }


@router.get("/adjustment-rules")
def adjustment_rules(session: Session = Depends(get_session)):
    rows = session.query(AdjustmentRule).order_by(AdjustmentRule.rule_key).all()
    return {
        "rules": [
            {
                "rule_key": row.rule_key,
                "action_type": row.action_type,
                "formula": row.formula,
                "requires": row.requires,
                "description": row.description,
                "application_status": row.application_status,
            }
            for row in rows
        ],
        "note": "Definitions only. No rule is applied to any price series "
        "in this run because no stored action has an ex-date, and raw "
        "price rows are never modified by an adjustment.",
    }
