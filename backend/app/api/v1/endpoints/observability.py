"""Phase 27 observability read-only endpoints (GET only).

Everything here is read from stored rows or explained as
absent with a reason. No endpoint writes anything: observability
runs, SLO seeding, and incident recording run through the CLI.
An observability record is not a promotion, a publication, a
send, or a trade — none of those capabilities exist in this
project, and this API grants none of them.

Endpoints:
  GET /api/v1/observability/summary
      Latest run highlights: SLO met/unmet/not_evaluable,
      stale/unknown sources, open exceptions, open incidents.
  GET /api/v1/observability/readiness
      Subsystem readiness: database probe, migration head vs
      the expected Phase 27 head, latest observability run,
      auth mode. A subsystem that cannot be probed reports
      unavailable with its reason, never a hardcoded ok.
  GET /api/v1/observability/slos
      SLO definitions with the latest measurement each.
  GET /api/v1/observability/source-health
      Latest source-health snapshot.
  GET /api/v1/observability/exceptions?status=
      Exception queue, optionally filtered by lifecycle status.
  GET /api/v1/observability/incidents
      Incident reports with lifecycle status.
  GET /api/v1/observability/performance
      Latest performance baseline probes.
  GET /api/v1/observability/runs
      Observability runs, paginated (limit 1..100, offset >= 0).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.database import check_database, get_session_factory
from app.models.observability import (
    ObservabilityException,
    ObservabilityIncident,
    ObservabilityRun,
    PerformanceBaseline,
    SloDefinition,
    SloMeasurement,
    SourceHealth,
)

router = APIRouter(tags=["observability"])

# Current LIVE migration head. History: the endpoint hardcoded
# "20261104_0023" (a Phase 27 artifact) and therefore reported
# migration_matches False / ready False against the branch chain
# head 20261104_0024. The blocker-resolution run first retargeted
# it to 0024, then the live head moved to 20261104_0025 when the
# news-intelligence coordinator applied migration 0025 (9 news
# tables) to the live database as gated Phase B work. The constant
# tracks the LIVE head, not this branch's migration chain head
# (0024): this branch does not carry the 0025 migration file, so a
# checkout of this branch alone would truthfully report not-ready
# until the news migration is merged into its chain. If a future
# migration lands, update this constant AND the regression tests
# together, never one alone.
EXPECTED_MIGRATION_HEAD = "20261104_0025"


def _session(request: Request):
    factory = get_session_factory(request.app.state.engine)
    return factory()


def _paginate(items: list, limit: int, offset: int) -> dict:
    if limit < 1 or limit > 100 or offset < 0:
        raise HTTPException(status_code=400, detail="bad pagination")
    return {
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "items": items[offset : offset + limit],
    }


def _latest_run(session):  # type: ignore[no-untyped-def]
    return session.query(ObservabilityRun).order_by(ObservabilityRun.id.desc()).first()


def _run_id(session) -> str | None:  # type: ignore[no-untyped-def]
    run = _latest_run(session)
    return run.run_id if run else None


@router.get("/observability/summary")
def observability_summary(request: Request) -> dict:
    session = _session(request)
    try:
        run = _latest_run(session)
        if run is None:
            return {
                "latest_run_id": None,
                "latest_run_status": None,
                "slos_total": 0,
                "slos_met": 0,
                "slos_unmet": 0,
                "slos_not_evaluable": 0,
                "sources_total": 0,
                "sources_stale": [],
                "sources_unknown": [],
                "exceptions_open": 0,
                "incidents_open": 0,
                "performance_probes": 0,
            }
        measurements = (
            session.query(SloMeasurement).filter(SloMeasurement.run_id == run.run_id).all()
        )
        health = session.query(SourceHealth).filter(SourceHealth.run_id == run.run_id).all()
        exceptions_open = (
            session.query(ObservabilityException)
            .filter(ObservabilityException.status == "open")
            .count()
        )
        incidents_open = (
            session.query(ObservabilityIncident)
            .filter(ObservabilityIncident.status == "open")
            .count()
        )
        probes = (
            session.query(PerformanceBaseline)
            .filter(PerformanceBaseline.run_id == run.run_id)
            .count()
        )
        return {
            "latest_run_id": run.run_id,
            "latest_run_status": run.status,
            "slos_total": len(measurements),
            "slos_met": sum(1 for m in measurements if m.status == "met"),
            "slos_unmet": sum(1 for m in measurements if m.status == "unmet"),
            "slos_not_evaluable": sum(1 for m in measurements if m.status == "not_evaluable"),
            "sources_total": len(health),
            "sources_stale": [h.source_key for h in health if h.status == "stale"],
            "sources_unknown": [h.source_key for h in health if h.status == "unknown"],
            "exceptions_open": exceptions_open,
            "incidents_open": incidents_open,
            "performance_probes": probes,
        }
    finally:
        session.close()


@router.get("/observability/readiness")
def observability_readiness(request: Request) -> dict:
    settings = get_settings()
    engine = request.app.state.engine
    database_url = getattr(settings, "DATABASE_URL", None)
    db_probe = check_database(engine, database_url)
    # No session factory means no database at all: report that
    # truthfully instead of crashing (a readiness endpoint that
    # 500s when the database is down is worse than useless).
    factory = get_session_factory(engine) if engine is not None else None
    if factory is None:
        return {
            "database": db_probe,
            "migration_head": None,
            "migration_expected": EXPECTED_MIGRATION_HEAD,
            "migration_matches": False,
            "latest_observability_run": None,
            "auth_enforcement": getattr(settings, "AUTH_ENFORCEMENT", "off"),
            "ready": False,
        }
    session = factory()
    try:
        migration_head = None
        try:
            from sqlalchemy import text as sql_text

            migration_head = session.execute(
                sql_text("SELECT version_num FROM alembic_version")
            ).scalar()
        except Exception:
            migration_head = None
        run = _latest_run(session)
        return {
            "database": db_probe,
            "migration_head": migration_head,
            "migration_expected": EXPECTED_MIGRATION_HEAD,
            "migration_matches": migration_head == EXPECTED_MIGRATION_HEAD,
            "latest_observability_run": run.run_id if run else None,
            "auth_enforcement": getattr(settings, "AUTH_ENFORCEMENT", "off"),
            "ready": bool(db_probe.get("reachable") and migration_head == EXPECTED_MIGRATION_HEAD),
        }
    finally:
        session.close()


@router.get("/observability/slos")
def observability_slos(request: Request) -> dict:
    session = _session(request)
    try:
        run_id = _run_id(session)
        definitions = session.query(SloDefinition).all()
        measurements = {}
        if run_id is not None:
            for m in session.query(SloMeasurement).filter(SloMeasurement.run_id == run_id):
                measurements[m.slo_key] = m
        items = []
        for d in definitions:
            m = measurements.get(d.slo_key)
            items.append(
                {
                    "slo_key": d.slo_key,
                    "category": d.category,
                    "metric_key": d.metric_key,
                    "target_value": float(d.target_value),
                    "comparison": d.comparison,
                    "unit": d.unit,
                    "rationale": d.rationale,
                    "latest_value": (
                        float(m.value) if m is not None and m.value is not None else None
                    ),
                    "latest_status": m.status if m is not None else None,
                    "latest_reason": m.reason if m is not None else None,
                }
            )
        return {"run_id": run_id, "items": items}
    finally:
        session.close()


@router.get("/observability/source-health")
def observability_source_health(request: Request) -> dict:
    session = _session(request)
    try:
        run_id = _run_id(session)
        if run_id is None:
            return {"run_id": None, "items": []}
        rows = (
            session.query(SourceHealth)
            .filter(SourceHealth.run_id == run_id)
            .order_by(SourceHealth.source_key)
            .all()
        )
        return {
            "run_id": run_id,
            "items": [
                {
                    "source_key": r.source_key,
                    "category": r.category,
                    "latest_observation_date": (
                        str(r.latest_observation_date) if r.latest_observation_date else None
                    ),
                    "coverage_numerator": r.coverage_numerator,
                    "coverage_denominator": r.coverage_denominator,
                    "freshness_days": r.freshness_days,
                    "status": r.status,
                    "notes": r.notes,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/observability/exceptions")
def observability_exceptions(request: Request, status: str | None = None) -> dict:
    session = _session(request)
    try:
        query = session.query(ObservabilityException).order_by(ObservabilityException.id.desc())
        if status is not None:
            if status not in ("open", "acknowledged", "resolved"):
                raise HTTPException(status_code=400, detail="bad status filter")
            query = query.filter(ObservabilityException.status == status)
        rows = query.all()
        return {
            "items": [
                {
                    "run_id": r.run_id,
                    "exception_key": r.exception_key,
                    "severity": r.severity,
                    "title": r.title,
                    "evidence": r.evidence,
                    "status": r.status,
                    "resolution_note": r.resolution_note,
                }
                for r in rows
            ]
        }
    finally:
        session.close()


@router.get("/observability/incidents")
def observability_incidents(request: Request) -> dict:
    session = _session(request)
    try:
        rows = session.query(ObservabilityIncident).order_by(ObservabilityIncident.id).all()
        return {
            "items": [
                {
                    "incident_key": r.incident_key,
                    "severity": r.severity,
                    "title": r.title,
                    "evidence": r.evidence,
                    "runbook_ref": r.runbook_ref,
                    "status": r.status,
                    "resolution_note": r.resolution_note,
                }
                for r in rows
            ]
        }
    finally:
        session.close()


@router.get("/observability/performance")
def observability_performance(request: Request) -> dict:
    session = _session(request)
    try:
        run_id = _run_id(session)
        if run_id is None:
            return {"run_id": None, "items": []}
        rows = (
            session.query(PerformanceBaseline)
            .filter(PerformanceBaseline.run_id == run_id)
            .order_by(PerformanceBaseline.probe_key)
            .all()
        )
        return {
            "run_id": run_id,
            "items": [
                {
                    "probe_key": r.probe_key,
                    "metric_key": r.metric_key,
                    "value": float(r.value) if r.value is not None else None,
                    "unit": r.unit,
                    "notes": r.notes,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/observability/runs")
def observability_runs(request: Request, limit: int = 20, offset: int = 0) -> dict:
    session = _session(request)
    try:
        rows = session.query(ObservabilityRun).order_by(ObservabilityRun.id.desc()).all()
        items = [
            {"run_id": r.run_id, "kind": r.kind, "status": r.status, "summary": r.summary}
            for r in rows
        ]
        return _paginate(items, limit, offset)
    finally:
        session.close()
