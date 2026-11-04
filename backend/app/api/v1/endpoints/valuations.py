"""Phase 9 valuation read-only endpoints (GET only).

Everything here is assessed from statement rows that actually exist,
or explained as NOT_CALCULABLE / not_applicable with a reason. No
value is ever fabricated, and no endpoint writes anything. The
committed record lives in valuations; these endpoints run the same
pure assessment live so every verdict carries its reason.

Endpoints:
  GET /api/v1/valuations?ticker=&valuation_date=
      Assessed methods for one company (computed values plus
      NOT_CALCULABLE reasons). valuation_date defaults to the price
      date for price-based methods; book-value rows carry their
      balance-sheet date and are listed alongside with their date.
  GET /api/v1/valuations/methods
      The method registry with applicability notes.

When no database is configured, endpoints answer 503 with a
truthful reason, never a fake empty market. An unknown ticker
returns 404; a known ticker with no statements returns 200 with an
empty assessment and a no_inputs note. Valuation outputs are
descriptive estimates with stated assumptions and uncertainty:
NOT a price target presented as fact, NOT investment advice, NOT
a buy/sell signal.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.reference import Security
from app.services.fundamental_analysis import PERIODS
from app.services.valuation import METHODS, PENDING_COMPANIES, coverage, runner

router = APIRouter(tags=["valuations"])

SCOPE_NOTE = (
    "Scope: three companies with Phase 7 statements (HUBC, NML, OGDC); "
    "all inputs UNVERIFIED. HBL (Habib Bank Limited) is PENDING — its "
    "CY2025 statements are not loaded yet, so it has no valuations. "
    "Trailing P/E is computed only where EPS is positive and the "
    "statement's publication date is known and on/before the price "
    "date. Share-count methods (P/B, P/S, market cap, EV multiples) "
    "are NOT_CALCULABLE: no share-count data exists. DCF/DDM are "
    "NOT_CALCULABLE: no source-backed discount rate, growth, or "
    "forecast assumptions exist. Valuation outputs are descriptive "
    "only, never investment advice or a buy/sell signal."
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


@router.get("/valuations")
def list_valuations(
    ticker: str,
    session: Session = Depends(get_session),
):
    """Live assessment for one ticker (all methods, all verdicts)."""
    security = _resolve_company(session, ticker)
    company_id = security.company_id
    if ticker in PENDING_COMPANIES:
        return {
            "ticker": ticker,
            "status": "pending",
            "reason": PENDING_COMPANIES[ticker],
            "methods": [],
            "scope_note": SCOPE_NOTE,
        }
    if ticker not in PERIODS:
        return {
            "ticker": ticker,
            "status": "no_inputs",
            "reason": "no configured company-period with statements",
            "methods": [],
            "scope_note": SCOPE_NOTE,
        }
    inputs = runner.load_valuation_inputs(session, ticker)
    verdicts = coverage.assess(ticker, inputs)
    return {
        "ticker": ticker,
        "company_id": company_id,
        "sector": inputs["sector"],
        "price_date": str(inputs["price_date"]),
        "price": str(inputs["price"]) if inputs["price"] is not None else None,
        "bs_date": str(inputs["bs_date"]),
        "publication_date": str(inputs["publication_date"])
        if inputs["publication_date"] is not None
        else None,
        "peers": [p.get("ticker") for p in inputs["peers"]],
        "methods": [
            {
                "method": v["method_key"],
                "status": v["status"],
                "value": str(v["value"]) if v["value"] is not None else None,
                "reason": v["reason"],
                "flags": v["flags"],
                "sensitivity": {
                    k: (str(val) if val is not None else None)
                    for k, val in (v["sensitivity"] or {}).items()
                }
                if v["sensitivity"]
                else None,
            }
            for v in verdicts
        ],
        "scope_note": SCOPE_NOTE,
    }


@router.get("/valuations/methods")
def list_methods():
    """The Phase 9 method registry with formula text and units."""
    return {
        "method_version": "1.0",
        "methods": [
            {
                "method": key,
                "family": family,
                "model": model,
                "formula": formula,
                "unit": unit,
            }
            for key, (family, model, formula, unit) in METHODS.items()
        ],
        "scope_note": SCOPE_NOTE,
    }
