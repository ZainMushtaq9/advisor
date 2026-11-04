"""Phase 15 decision read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent
with a reason. No value is ever fabricated, and no endpoint writes
anything. An unknown ticker returns 404; a known ticker with no
decision returns 200 with an empty result and a note. Nothing here
is investment advice, a buy/sell signal, or a forecast: research
conclusions are labelled candidates, every user-facing value in
this run is WITHHELD, and no execution path exists anywhere in
this project.

Endpoints:
  GET /api/v1/decisions/rules
      The versioned decision rule set.
  GET /api/v1/decisions?ticker=
      Decisions for one company (or all companies with no ticker).
  GET /api/v1/decisions/status
      Coverage counts and the honest Phase 15 summary.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.decision import Decision, DecisionOutcome, DecisionRule
from app.models.reference import Security

router = APIRouter(tags=["decisions"])

SCOPE_NOTE = (
    "Scope: analysis universe is HUBC, NML, OGDC (the statement "
    "companies) plus HBL, recorded as an explicit abstention "
    "pending its Phase 7 load. Decision date 2026-11-04, price "
    "reference 2026-11-03. Technical evidence is absent for every "
    "company, forecasts are abstained on every target, and all "
    "inputs are UNVERIFIED, so every research conclusion carries "
    "LOW confidence and every user-facing value is WITHHELD. "
    "Research conclusions are candidates, never orders and never "
    "personalized advice. No live execution exists."
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


def _serialize(decision: Decision) -> dict:
    return {
        "company_id": decision.company_id,
        "security_id": decision.security_id,
        "decision_date": str(decision.decision_date),
        "rules_version": decision.rules_version,
        "screening_outcome": decision.screening_outcome,
        "research_conclusion": decision.research_conclusion,
        "user_facing": decision.user_facing,
        "confidence": decision.confidence,
        "total_score": str(decision.total_score) if decision.total_score is not None else None,
        "scored_dimensions": decision.scored_dimensions,
        "completeness": str(decision.completeness) if decision.completeness is not None else None,
        "evidence_snapshot": decision.evidence_snapshot,
        "conflicts": decision.conflicts,
        "gate_reasons": decision.gate_reasons,
        "quality_status": decision.quality_status,
    }


def _resolve_ticker(session: Session, ticker: str) -> Security:
    security = session.query(Security).filter(Security.ticker == ticker).one_or_none()
    if security is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    return security


@router.get("/decisions/rules")
def get_rules(session: Session = Depends(get_session)) -> dict:
    rules = session.query(DecisionRule).order_by(DecisionRule.id.desc()).all()
    return {
        "rules": [
            {
                "version": rule.version,
                "dimensions": rule.dimensions,
                "weights": rule.weights,
                "thresholds": rule.thresholds,
                "gates": rule.gates,
                "precedence": rule.precedence,
                "confidence_rules": rule.confidence_rules,
            }
            for rule in rules
        ],
        "note": SCOPE_NOTE,
    }


@router.get("/decisions")
def get_decisions(ticker: str | None = None, session: Session = Depends(get_session)) -> dict:
    if ticker is not None:
        security = _resolve_ticker(session, ticker)
        rows = (
            session.query(Decision)
            .filter(Decision.company_id == security.company_id)
            .order_by(Decision.decision_date.desc())
            .all()
        )
        if not rows:
            return {
                "ticker": ticker,
                "decisions": [],
                "note": (
                    "Known ticker with no decision rows. HBL has no "
                    "statements loaded yet; its abstention is recorded "
                    "only once a decision run covers it."
                    if ticker == "HBL"
                    else "No decision rows for this ticker."
                ),
            }
        return {"ticker": ticker, "decisions": [_serialize(row) for row in rows]}
    rows = session.query(Decision).order_by(Decision.decision_date.desc()).all()
    return {"decisions": [_serialize(row) for row in rows], "note": SCOPE_NOTE}


@router.get("/decisions/status")
def get_status(session: Session = Depends(get_session)) -> dict:
    rows = session.query(Decision).all()
    outcomes = session.query(DecisionOutcome).count()
    by_conclusion: dict[str, int] = {}
    by_facing: dict[str, int] = {}
    for row in rows:
        by_conclusion[row.research_conclusion] = by_conclusion.get(row.research_conclusion, 0) + 1
        by_facing[row.user_facing] = by_facing.get(row.user_facing, 0) + 1
    return {
        "decisions": len(rows),
        "by_conclusion": by_conclusion,
        "by_user_facing": by_facing,
        "outcomes": outcomes,
        "note": (
            "Phase 15 is PARTIALLY COMPLETE: the engine, rules, "
            "audit model and APIs are complete, but every "
            "user-facing value is WITHHELD (LOW confidence: "
            "UNVERIFIED inputs, calibration NOT_ESTABLISHED, "
            "technical evidence absent) and two of four companies "
            "are abstentions. Outcomes are 0 until a later "
            "observation arrives after the decision date."
        ),
    }
