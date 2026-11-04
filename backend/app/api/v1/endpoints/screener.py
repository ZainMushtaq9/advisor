"""Phase 20 screener read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent
with a reason. No value is ever fabricated, and no endpoint
writes anything. A screen result is a filter outcome, not an
investment opportunity, not a recommendation, and not a
forecast: Phase 15 user-facing values are WITHHELD, Phase 13
forecasts are abstained, and this screener does not reintroduce
either. No order path exists anywhere in this project.

Endpoints:
  GET /api/v1/screener/filters
      The filter registry with units, sources, and sector
      applicability.
  GET /api/v1/screener/screens
      Saved screen definitions with their latest run summary.
  GET /api/v1/screener/screens/{name}/results
      Results of the latest run for one screen, paginated and
      sortable (limit 1..100, offset >= 0; sort=score|ticker;
      outcome=MATCH|NO_MATCH|INSUFFICIENT_DATA optional).
  GET /api/v1/screener/status
      Coverage counts and the honest Phase 20 summary.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.database import get_session_factory
from app.models.reference import Security
from app.models.screener import ScreenDefinition, ScreenResult, ScreenRun
from app.services.screener import DISCLAIMER, FILTER_REGISTRY
from app.services.screener.ranking import paginate, sort_results

router = APIRouter(tags=["screener"])


def _session(request: Request):
    factory = get_session_factory(request.app.state.engine)
    return factory()


@router.get("/screener/filters")
def list_filters():
    return {
        "disclaimer": DISCLAIMER,
        "filters": [
            {
                "filter": key,
                "category": spec["category"],
                "unit": spec["unit"],
                "source": spec["source"],
                "sector_applicability": spec["sector_applicability"],
                "kinds": list(spec["kinds"]),
                "description": spec["description"],
            }
            for key, spec in FILTER_REGISTRY.items()
        ],
    }


@router.get("/screener/screens")
def list_screens(request: Request):
    session = _session(request)
    try:
        definitions = session.query(ScreenDefinition).order_by(ScreenDefinition.name).all()
        out = []
        for definition in definitions:
            run = (
                session.query(ScreenRun)
                .filter(ScreenRun.screen_definition_id == definition.id)
                .order_by(ScreenRun.as_of_date.desc())
                .first()
            )
            out.append(
                {
                    "name": definition.name,
                    "version": definition.version,
                    "description": definition.description,
                    "universe": definition.universe,
                    "filters": definition.filters,
                    "latest_run": (
                        {
                            "as_of_date": str(run.as_of_date),
                            "universe_size": run.universe_size,
                            "matched_count": run.matched_count,
                            "insufficient_count": run.insufficient_count,
                            "status": run.status,
                        }
                        if run
                        else None
                    ),
                }
            )
        return {"disclaimer": DISCLAIMER, "screens": out}
    finally:
        session.close()


@router.get("/screener/screens/{name}/results")
def screen_results(
    name: str,
    request: Request,
    limit: int = 20,
    offset: int = 0,
    sort: str = "score",
    outcome: str | None = None,
):
    session = _session(request)
    try:
        definition = (
            session.query(ScreenDefinition)
            .filter(ScreenDefinition.name == name)
            .order_by(ScreenDefinition.version.desc())
            .first()
        )
        if definition is None:
            raise HTTPException(status_code=404, detail=f"Unknown screen: {name}")
        run = (
            session.query(ScreenRun)
            .filter(ScreenRun.screen_definition_id == definition.id)
            .order_by(ScreenRun.as_of_date.desc())
            .first()
        )
        if run is None:
            return {
                "screen": name,
                "version": definition.version,
                "run": None,
                "results": [],
                "pagination": {"total": 0, "limit": limit, "offset": offset, "returned": 0},
                "note": "Screen defined but never run.",
            }
        rows = (
            session.query(ScreenResult, Security)
            .join(Security, Security.id == ScreenResult.security_id)
            .filter(ScreenResult.screen_run_id == run.id)
            .all()
        )
        # Scores stay Decimal through sorting and pagination:
        # stringifying first would break score-descending sort
        # (unary minus on a string). Conversion happens only
        # on the final page, below.
        results = [
            {
                "ticker": security.ticker,
                "outcome": result.outcome,
                "score": result.score,
                "passed_count": result.passed_count,
                "scored_count": result.scored_count,
                "reason_codes": result.reason_codes,
                "evidence": result.evidence,
            }
            for result, security in rows
        ]
        if outcome is not None:
            if outcome not in ("MATCH", "NO_MATCH", "INSUFFICIENT_DATA"):
                raise HTTPException(status_code=400, detail=f"Unknown outcome: {outcome}")
            results = [r for r in results if r["outcome"] == outcome]
        try:
            results = sort_results(results, sort)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        try:
            page, page_info = paginate(results, limit, offset)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        for row in page:
            row["score"] = str(row["score"]) if row["score"] is not None else None
        return {
            "disclaimer": DISCLAIMER,
            "screen": name,
            "version": definition.version,
            "run": {
                "as_of_date": str(run.as_of_date),
                "universe_size": run.universe_size,
                "matched_count": run.matched_count,
                "insufficient_count": run.insufficient_count,
                "status": run.status,
            },
            "results": page,
            "pagination": page_info,
        }
    finally:
        session.close()


@router.get("/screener/status")
def screener_status(request: Request):
    session = _session(request)
    try:
        definitions = session.query(ScreenDefinition).count()
        runs = session.query(ScreenRun).count()
        results = session.query(ScreenResult).count()
        matches = session.query(ScreenResult).filter(ScreenResult.outcome == "MATCH").count()
        return {
            "disclaimer": DISCLAIMER,
            "definitions": definitions,
            "runs": runs,
            "results": results,
            "matches": matches,
            "scope_note": (
                "Price/volume screens cover all 470 registry "
                "securities (444 priced on 2026-11-03, 26 "
                "without a price). Fundamental, valuation, and "
                "dividend screens cover the 4 decision "
                "companies (HUBC, NML, OGDC, HBL) only. "
                "Technical filters match nothing: Phase 6 "
                "holds 0 calculable values. Nothing here is "
                "investment advice or a forecast."
            ),
        }
    finally:
        session.close()
