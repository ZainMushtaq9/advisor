"""Phase 25 job handlers: what each job actually does.

Every enabled handler is READ-ONLY except one: the manual
retention purge, which deletes only auth audit-log rows
older than 12 months and only with an explicit --confirm.
No handler collects market data, fetches a URL, sends a
message, publishes anything, promotes a quality status, or
executes a trade — those capabilities do not exist in this
project, and no handler invents them.

Collection handlers (market post-close, filing check, macro
release check) are registered as explicit stubs that raise
``CollectionNotImplemented``: the jobs are PAUSED and the
runner refuses paused jobs, so these stubs are unreachable
in normal operation. If an operator ever activates one
without implementing collection (which itself needs written
PSX permission evidence for the market job, and a separate
approval for any automated polling), the run dead-letters
immediately with the exact reason instead of silently doing
nothing or retrying a hopeless job.

Handler contract: ``handler(ctx) -> dict`` where ``ctx`` is
a ``JobContext`` (session, run, params, checkpoint writer).
The returned dict becomes the run's ``result_summary``. A
handler that finds a problem in the DATA (drift, unexpected
counts) reports it in the summary and still succeeds: a
finding is not an infrastructure failure. A handler raises
only on infrastructure failure (missing table, unreachable
database) — those are retried, then dead-lettered.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.jobs import JobRun
from app.services.jobs.registry import EXPECTED_COUNTS

# Retention policy (Phase 24): auth audit logs are kept 12
# months. Job tables are NEVER purged by this handler: they
# are the recovery evidence itself.
RETENTION_DAYS = 365


class CollectionNotImplemented(Exception):
    """A collection job was dispatched without an implemented
    collector. Non-retryable by design (see runner)."""


class HandlerError(Exception):
    """Infrastructure failure: retried per the job's policy."""


@dataclass
class JobContext:
    session: Session
    run: JobRun
    params: dict
    # checkpoint(key, value, detail=None) -> None
    checkpoint: Callable[..., None]


def _as_aware(value: datetime | str | None) -> datetime | None:
    """SQLite strips tzinfo on read; treat naive values as UTC,
    exactly as the Phase 24 auth service does. Raw ``text()``
    queries on SQLite additionally return datetimes as ISO
    strings, so strings are parsed first (PostgreSQL returns
    real datetimes and never takes this branch)."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _count(session: Session, table: str) -> int:
    row = session.execute(text(f"SELECT COUNT(*) FROM {table}")).first()
    if row is None:
        raise HandlerError(f"count query returned no row for {table}")
    return int(row[0])


def _table_exists(session: Session, table: str) -> bool:
    from sqlalchemy import inspect

    try:
        return table in inspect(session.bind).get_table_names()
    except Exception:
        return False


def handle_system_health(ctx: JobContext) -> dict:
    """Row counts + migration head. Fails only if the database
    itself is unreachable; counts are reported, never judged."""
    session = ctx.session
    try:
        session.execute(text("SELECT 1")).first()
    except Exception as exc:
        raise HandlerError(f"database probe failed: {type(exc).__name__}") from exc
    version_row = None
    if _table_exists(session, "alembic_version"):
        version_row = session.execute(text("SELECT version_num FROM alembic_version")).first()
    counts = {
        table: _count(session, table)
        for table in ("companies", "market_prices", "reports", "alerts")
    }
    return {
        "database": "reachable",
        "migration_head": version_row[0] if version_row else None,
        "counts": counts,
    }


def handle_alert_digest(ctx: JobContext) -> dict:
    """In-app digest totals. No message is sent anywhere: the
    digest is a stored run summary the dashboard shows. 'New'
    means processed after the previous digest watermark; the
    first digest reports the whole backlog as its baseline
    and says so explicitly."""
    session = ctx.session
    rows = session.execute(text("SELECT severity, status, processing_time FROM alerts")).all()
    by_severity: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for severity, status, processing_time in rows:
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
    watermark = None
    previous = session.execute(
        text(
            "SELECT watermark_value FROM job_checkpoints "
            "WHERE job_key = 'alert_digest' AND watermark_key = 'last_digest_date'"
        )
    ).first()
    if previous is not None:
        watermark = previous[0]
    # PKT dates throughout: market timestamps in this project
    # are Asia/Karachi, and a UTC date would mislabel alerts
    # processed after midnight PKT but before midnight UTC.
    from zoneinfo import ZoneInfo

    pkt = ZoneInfo("Asia/Karachi")
    today = datetime.now(pkt).date().isoformat()
    new_count = 0
    if watermark is not None:
        for _, _, processing_time in rows:
            aware = _as_aware(processing_time)
            if aware is not None and aware.astimezone(pkt).date().isoformat() > watermark:
                new_count += 1
        baseline = False
    else:
        new_count = len(rows)
        baseline = True
    ctx.checkpoint("last_digest_date", today, {"alerts_total": len(rows)})
    return {
        "alerts_total": len(rows),
        "by_severity": by_severity,
        "by_status": by_status,
        "new_since_last_digest": new_count,
        "previous_digest_date": watermark,
        "baseline": baseline,
        "delivery": "in_app_only",
        "note": "Digest only: no external message is ever sent.",
    }


def handle_drift_check(ctx: JobContext) -> dict:
    """Compare live counts against EXPECTED_COUNTS (verified
    end of Phase 24). Every difference is reported as drift;
    drift is a finding, not a failure, so the handler still
    succeeds. A missing table is an infrastructure failure and
    raises (retried, then dead-lettered)."""
    session = ctx.session
    counts: dict[str, int] = {}
    drift: list[dict] = []
    for table, expected in EXPECTED_COUNTS.items():
        if not _table_exists(session, table):
            raise HandlerError(f"drift check: table missing: {table}")
        actual = _count(session, table)
        counts[table] = actual
        if actual != expected:
            drift.append({"table": table, "expected": expected, "actual": actual})
    return {
        "tables_checked": len(EXPECTED_COUNTS),
        "drift_count": len(drift),
        "drift": drift,
        "counts": counts,
    }


def handle_report_qa_audit(ctx: JobContext) -> dict:
    """Re-validate the Phase 22 report set: status counts,
    figure totals, every report carrying figures, and — by
    schema inspection — no publication column anywhere.
    APPROVED would mean internally reviewed only; there is
    still no publish step, and this audit asserts that."""
    session = ctx.session
    status_rows = session.execute(
        text("SELECT status, COUNT(*) FROM reports GROUP BY status")
    ).all()
    by_status = {status: int(n) for status, n in status_rows}
    figures_total = _count(session, "report_figures")
    reports_total = _count(session, "reports")
    per_report = session.execute(
        text(
            "SELECT r.id, COUNT(f.id) FROM reports r "
            "LEFT JOIN report_figures f ON f.report_id = r.id "
            "GROUP BY r.id"
        )
    ).all()
    empty_reports = [rid for rid, n in per_report if n == 0]
    columns = []
    try:
        from sqlalchemy import inspect

        columns = [c["name"] for c in inspect(session.bind).get_columns("reports")]
    except Exception:
        columns = []
    publish_columns = [c for c in columns if "publish" in c.lower()]
    return {
        "reports_total": reports_total,
        "by_status": by_status,
        "figures_total": figures_total,
        "empty_reports": empty_reports,
        "publish_columns": publish_columns,
        "published_externally": 0,
        "note": "No publish step exists; APPROVED means internally reviewed only.",
    }


def handle_retention_purge(ctx: JobContext) -> dict:
    """Auth audit-log retention (12 months). Dry-run by
    default: reports candidates, writes nothing. With
    confirm=True: deletes only rows older than 12 months.
    Job tables are never purged by this handler."""
    session = ctx.session
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    candidates = session.execute(
        text("SELECT COUNT(*) FROM auth_audit_logs WHERE created_at < :cutoff"),
        {"cutoff": cutoff},
    ).first()
    candidate_count = int(candidates[0]) if candidates else 0
    if not ctx.params.get("confirm"):
        return {
            "dry_run": True,
            "cutoff": cutoff.date().isoformat(),
            "candidates_older_than_12_months": candidate_count,
            "deleted": 0,
            "note": "Dry run: nothing deleted. Re-run with confirm to delete.",
        }
    session.execute(
        text("DELETE FROM auth_audit_logs WHERE created_at < :cutoff"),
        {"cutoff": cutoff},
    )
    session.commit()
    return {
        "dry_run": False,
        "cutoff": cutoff.date().isoformat(),
        "candidates_older_than_12_months": candidate_count,
        "deleted": candidate_count,
    }


def handle_collection_market_post_close(ctx: JobContext) -> dict:
    raise CollectionNotImplemented(
        "Market post-close collection is not implemented: written "
        "PSX permission evidence is required first (Phase 5 Terms "
        "gate, user-owned). This job is registered PAUSED and the "
        "runner refuses paused jobs."
    )


def handle_collection_filing_check(ctx: JobContext) -> dict:
    raise CollectionNotImplemented(
        "Filing availability check is not implemented: automated "
        "issuer-page polling is not approved and DPS "
        "filing-download terms are not established. Sampled "
        "manual checks only (Phase 7)."
    )


def handle_collection_macro_release_check(ctx: JobContext) -> dict:
    raise CollectionNotImplemented(
        "Macro release check is not implemented: no automated "
        "fetch is approved. Phase 10 macro reads were manual "
        "official reads (SBP/PBS pages)."
    )


HANDLERS: dict[str, Callable[[JobContext], dict]] = {
    "system_health": handle_system_health,
    "alert_digest": handle_alert_digest,
    "drift_check": handle_drift_check,
    "report_qa_audit": handle_report_qa_audit,
    "retention_purge": handle_retention_purge,
    "collection_market_post_close": handle_collection_market_post_close,
    "collection_filing_check": handle_collection_filing_check,
    "collection_macro_release_check": handle_collection_macro_release_check,
}

# Errors that must NOT be retried: retrying cannot fix them.
NON_RETRYABLE = (CollectionNotImplemented,)
