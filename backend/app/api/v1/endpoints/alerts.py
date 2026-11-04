"""Phase 21 alert center read-only endpoints (GET only).

Everything here is read from stored rows or explained as
absent with a reason. No value is ever fabricated, and no
endpoint writes anything: alert creation, delivery, and
lifecycle transitions run through the CLI. An alert is a
notification about a stored event, not an investment
opportunity, not a recommendation, and not a forecast: Phase
15 user-facing values are WITHHELD, Phase 13 forecasts are
abstained, and this phase reintroduces neither. Delivery is
in-app only. No order path exists anywhere in this project.

Endpoints:
  GET /api/v1/alerts/rules
      Seeded alert rule definitions.
  GET /api/v1/alerts/preferences
      The local notification preference profile.
  GET /api/v1/alerts
      Alerts, paginated and filterable (limit 1..100,
      offset >= 0; sort=event_time|processing_time;
      status, severity, rule_key, ticker, subject_type
      optional).
  GET /api/v1/alerts/{id}
      One alert with its rule key.
  GET /api/v1/alerts/{id}/deliveries
      Delivery attempts for one alert.
  GET /api/v1/alerts/runs
      Evaluation runs, most recent first.
  GET /api/v1/alerts/status
      Counts by status/severity/rule and the latest run totals.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.database import get_session_factory
from app.models.alerts import (
    Alert,
    AlertDelivery,
    AlertRule,
    AlertRun,
    NotificationPreference,
)
from app.services.alerts import DISCLAIMER
from app.services.alerts.evaluation import paginate

router = APIRouter(tags=["alerts"])


def _session(request: Request):
    factory = get_session_factory(request.app.state.engine)
    return factory()


def _rule_keys(session) -> dict[int, str]:
    return {row.id: row.rule_key for row in session.query(AlertRule).all()}


def _alert_view(row: Alert, rule_key: str | None) -> dict:
    return {
        "id": row.id,
        "rule_key": rule_key,
        "subject_type": row.subject_type,
        "ticker": row.ticker,
        "company_id": row.company_id,
        "sector": row.sector,
        "event_time": row.event_time.isoformat() if row.event_time else None,
        "processing_time": row.processing_time.isoformat() if row.processing_time else None,
        "as_of_date": row.as_of_date.isoformat() if row.as_of_date else None,
        "severity": row.severity,
        "origin": row.origin,
        "title": row.title,
        "evidence": row.evidence,
        "dedup_key": row.dedup_key,
        "status": row.status,
        "quality_status": row.quality_status,
    }


@router.get("/alerts/rules")
def list_rules(request: Request):
    session = _session(request)
    try:
        return {
            "disclaimer": DISCLAIMER,
            "rules": [
                {
                    "rule_key": row.rule_key,
                    "name": row.name,
                    "version": row.version,
                    "category": row.category,
                    "origin": row.origin,
                    "severity": row.severity,
                    "trigger": row.trigger,
                    "description": row.description,
                    "max_event_age_days": row.max_event_age_days,
                    "daily_limit": row.daily_limit,
                    "enabled": row.enabled,
                }
                for row in session.query(AlertRule).order_by(AlertRule.rule_key).all()
            ],
        }
    finally:
        session.close()


@router.get("/alerts/preferences")
def get_preferences(request: Request):
    session = _session(request)
    try:
        row = session.query(NotificationPreference).order_by(NotificationPreference.id).first()
        if row is None:
            return {
                "disclaimer": DISCLAIMER,
                "preferences": None,
                "note": "No preference profile seeded yet.",
            }
        return {
            "disclaimer": DISCLAIMER,
            "preferences": {
                "profile": row.profile,
                "channels": row.channels,
                "external_consent": row.external_consent,
                "quiet_start": row.quiet_start.isoformat() if row.quiet_start else None,
                "quiet_end": row.quiet_end.isoformat() if row.quiet_end else None,
                "muted_rule_keys": row.muted_rule_keys,
            },
        }
    finally:
        session.close()


@router.get("/alerts")
def list_alerts(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    sort: str = "event_time",
    status: str | None = None,
    severity: str | None = None,
    rule_key: str | None = None,
    ticker: str | None = None,
    subject_type: str | None = None,
):
    session = _session(request)
    try:
        if sort not in ("event_time", "processing_time"):
            raise HTTPException(
                status_code=400, detail="sort must be event_time or processing_time"
            )
        query = session.query(Alert)
        if status is not None:
            query = query.filter(Alert.status == status)
        if severity is not None:
            query = query.filter(Alert.severity == severity)
        if ticker is not None:
            query = query.filter(Alert.ticker == ticker)
        if subject_type is not None:
            query = query.filter(Alert.subject_type == subject_type)
        if rule_key is not None:
            rule = session.query(AlertRule).filter(AlertRule.rule_key == rule_key).first()
            if rule is None:
                raise HTTPException(status_code=404, detail=f"Unknown rule: {rule_key}")
            query = query.filter(Alert.rule_id == rule.id)
        order = Alert.event_time.desc() if sort == "event_time" else Alert.processing_time.desc()
        rows = query.order_by(order).all()
        keys = _rule_keys(session)
        try:
            page = paginate(rows, limit, offset)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {
            "disclaimer": DISCLAIMER,
            "total": len(rows),
            "limit": limit,
            "offset": offset,
            "alerts": [_alert_view(row, keys.get(row.rule_id)) for row in page],
        }
    finally:
        session.close()


@router.get("/alerts/runs")
def list_runs(request: Request, limit: int = 50, offset: int = 0):
    session = _session(request)
    try:
        rows = session.query(AlertRun).order_by(AlertRun.processing_time.desc()).all()
        keys = _rule_keys(session)
        try:
            page = paginate(rows, limit, offset)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {
            "disclaimer": DISCLAIMER,
            "total": len(rows),
            "runs": [
                {
                    "id": row.id,
                    "rule_key": keys.get(row.rule_id),
                    "as_of_date": row.as_of_date.isoformat() if row.as_of_date else None,
                    "processing_time": row.processing_time.isoformat()
                    if row.processing_time
                    else None,
                    "evaluated": row.evaluated,
                    "created": row.created,
                    "duplicates_skipped": row.duplicates_skipped,
                    "suppressed": row.suppressed,
                    "status": row.status,
                }
                for row in page
            ],
        }
    finally:
        session.close()


@router.get("/alerts/status")
def get_status(request: Request):
    session = _session(request)
    try:
        alerts = session.query(Alert).all()
        keys = _rule_keys(session)
        by_status: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_rule: dict[str, int] = {}
        for row in alerts:
            by_status[row.status] = by_status.get(row.status, 0) + 1
            by_severity[row.severity] = by_severity.get(row.severity, 0) + 1
            key = keys.get(row.rule_id, "unknown")
            by_rule[key] = by_rule.get(key, 0) + 1
        runs = session.query(AlertRun).order_by(AlertRun.processing_time.desc()).all()
        latest: dict[str, dict] = {}
        for run in runs:
            key = keys.get(run.rule_id, "unknown")
            latest.setdefault(
                key,
                {
                    "evaluated": run.evaluated,
                    "created": run.created,
                    "duplicates_skipped": run.duplicates_skipped,
                    "suppressed": run.suppressed,
                    "processing_time": run.processing_time.isoformat()
                    if run.processing_time
                    else None,
                },
            )
        return {
            "disclaimer": DISCLAIMER,
            "total_alerts": len(alerts),
            "by_status": by_status,
            "by_severity": by_severity,
            "by_rule": by_rule,
            "latest_run_by_rule": latest,
            "false_positive_note": (
                "False-positive rate is NOT_MEASURABLE: no user feedback "
                "labels (acknowledgement outcomes) exist yet. Volume, "
                "duplicates skipped, and suppression reasons are reported "
                "instead; they are not a false-positive rate."
            ),
        }
    finally:
        session.close()


@router.get("/alerts/{alert_id}")
def get_alert(request: Request, alert_id: int):
    session = _session(request)
    try:
        row = session.query(Alert).filter(Alert.id == alert_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Unknown alert id: {alert_id}")
        keys = _rule_keys(session)
        return {"disclaimer": DISCLAIMER, "alert": _alert_view(row, keys.get(row.rule_id))}
    finally:
        session.close()


@router.get("/alerts/{alert_id}/deliveries")
def get_deliveries(request: Request, alert_id: int):
    session = _session(request)
    try:
        alert = session.query(Alert).filter(Alert.id == alert_id).first()
        if alert is None:
            raise HTTPException(status_code=404, detail=f"Unknown alert id: {alert_id}")
        rows = (
            session.query(AlertDelivery)
            .filter(AlertDelivery.alert_id == alert_id)
            .order_by(AlertDelivery.attempted_at)
            .all()
        )
        return {
            "disclaimer": DISCLAIMER,
            "alert_id": alert_id,
            "deliveries": [
                {
                    "id": row.id,
                    "channel": row.channel,
                    "outcome": row.outcome,
                    "attempted_at": row.attempted_at.isoformat() if row.attempted_at else None,
                    "detail": row.detail,
                }
                for row in rows
            ],
        }
    finally:
        session.close()
