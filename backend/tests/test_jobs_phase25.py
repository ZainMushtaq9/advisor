"""Phase 25 job automation tests — pure + SQLite-backed + API.

No real PostgreSQL, no network. SQLite strips tzinfo on read;
the runner reattaches UTC (see runner._as_aware), so leases,
backoff and watermarks behave identically on both backends.

Every acceptance item is tested: idempotency (same key
replays, handler called once); recoverability (lease
reclaim after a simulated crash, checkpoint resume after a
mid-run failure); bounded catch-up (cap 7, oldest first);
retry with exponential backoff then dead-letter;
non-retryable collection stubs dead-letter immediately;
dependency gating (waiting -> blocked -> unblocked);
paused refusal; cancellation rules; schedules matching
source cadence (weekday post-close, quarterly filings,
monthly macro, manual never due); no paid service or
unbounded polling (single-pass runner, sequential, capped
catch-up); offline limitations stated (no holiday calendar,
no daemon).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.main import create_app
from app.models.jobs import (
    JobCheckpoint,
    JobDeadLetter,
    JobDefinition,
    JobRun,
)
from app.services.jobs import calendar as cal
from app.services.jobs.registry import JOB_DEFINITIONS
from app.services.jobs import handlers as job_handlers
from app.services.jobs import runner as jobs_runner

JOB_TABLES = ("job_definitions", "job_runs", "job_checkpoints", "job_dead_letters")


def _engine(tmp_path: Path, name: str = "jobs.db"):
    from app.database import Base

    engine = create_engine(f"sqlite:///{tmp_path}/{name}")
    tables = [t for n, t in Base.metadata.tables.items() if n in JOB_TABLES]
    Base.metadata.create_all(engine, tables=tables)
    return engine


def _session(engine):
    return sessionmaker(bind=engine)()


def _define(session, job_key, handler_key, **overrides):
    definition = JobDefinition(
        job_key=job_key,
        title=f"test {job_key}",
        handler_key=handler_key,
        schedule_kind=overrides.get("schedule_kind", "daily"),
        schedule_spec=overrides.get("schedule_spec", {"time": "07:00"}),
        dependencies=overrides.get("dependencies", []),
        timeout_seconds=overrides.get("timeout_seconds", 300),
        max_attempts=overrides.get("max_attempts", 3),
        backoff_base_seconds=overrides.get("backoff_base_seconds", 60),
        priority=overrides.get("priority", 10),
        status=overrides.get("status", "active"),
        pause_reason=overrides.get("pause_reason"),
    )
    session.add(definition)
    session.commit()
    return definition


# ---------------------------------------------------------------------------
# Pure: calendar
# ---------------------------------------------------------------------------


def test_daily_weekdays_only() -> None:
    # 2026-11-02 is a Monday; 2026-11-08 is a Sunday.
    found = cal.occurrences(
        "daily",
        {"weekdays": [0, 1, 2, 3, 4]},
        date(2026, 11, 2),
        date(2026, 11, 8),
    )
    assert found == [date(2026, 11, d) for d in (2, 3, 4, 5, 6)]
    assert all(cal.is_trading_weekday(d) for d in found)


def test_weekly_monthly_quarterly_annual() -> None:
    assert cal.occurrences("weekly", {"weekday": 0}, date(2026, 11, 1), date(2026, 11, 30)) == [
        date(2026, 11, d) for d in (2, 9, 16, 23, 30)
    ]
    assert cal.occurrences("monthly", {"day": 3}, date(2026, 11, 1), date(2026, 12, 31)) == [
        date(2026, 11, 3),
        date(2026, 12, 3),
    ]
    assert cal.occurrences(
        "quarterly",
        {"months": [1, 4, 7, 10], "day": 15},
        date(2026, 1, 1),
        date(2026, 12, 31),
    ) == [date(2026, m, 15) for m in (1, 4, 7, 10)]
    assert cal.occurrences(
        "annual", {"month": 6, "day": 30}, date(2026, 1, 1), date(2027, 12, 31)
    ) == [date(2026, 6, 30), date(2027, 6, 30)]


def test_nonexistent_day_is_skipped_never_moved() -> None:
    # Day 31 in February: skipped, not moved to 28 Feb or 1 Mar.
    found = cal.occurrences("monthly", {"day": 31}, date(2026, 1, 1), date(2026, 3, 31))
    assert found == [date(2026, 1, 31), date(2026, 3, 31)]
    # 29 February in a non-leap year: skipped.
    assert (
        cal.occurrences("annual", {"month": 2, "day": 29}, date(2026, 1, 1), date(2026, 12, 31))
        == []
    )
    assert cal.occurrences(
        "annual", {"month": 2, "day": 29}, date(2028, 1, 1), date(2028, 12, 31)
    ) == [date(2028, 2, 29)]


def test_manual_never_due_and_catchup_capped() -> None:
    assert cal.due_occurrences("manual", {}, None, date(2026, 11, 5)) == []
    # 20 missed weekdays: only the 7 oldest are due.
    due = cal.due_occurrences(
        "daily",
        {"weekdays": [0, 1, 2, 3, 4]},
        date(2026, 10, 1),
        date(2026, 11, 5),
    )
    assert len(due) == 7
    assert due[0] == date(2026, 10, 2)  # oldest first
    assert due == sorted(due)
    # Brand-new job: window starts 30 days back, not at epoch.
    due_new = cal.due_occurrences("daily", {}, None, date(2026, 11, 5))
    assert due_new[0] == date(2026, 10, 6)


def test_idempotency_key_format() -> None:
    assert cal.idempotency_key("system_health", date(2026, 11, 5)) == ("system_health:2026-11-05")
    assert cal.idempotency_key("retention_purge", None) == "retention_purge:manual"


# ---------------------------------------------------------------------------
# Runner: registry
# ---------------------------------------------------------------------------


def test_register_inserts_and_preserves_operator_status(tmp_path) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    result = jobs_runner.register_definitions(session)
    # Count derives from the registry, not a hardcoded number: the
    # News Intelligence Engine adds 3 definitions (8 Phase 25 + 3
    # news), and the test's intent is "register inserts everything".
    assert len(result["inserted"]) == len(JOB_DEFINITIONS)
    assert session.query(JobDefinition).count() == len(JOB_DEFINITIONS)
    assert "news_collection_daily" in result["inserted"]
    assert "news_digest" in result["inserted"]
    # Operator pauses an active job; re-register must NOT re-enable it.
    health = jobs_runner.get_definition(session, "system_health")
    health.status = "paused"
    health.pause_reason = "operator pause for test"
    session.commit()
    result2 = jobs_runner.register_definitions(session)
    assert result2["inserted"] == []
    assert jobs_runner.get_definition(session, "system_health").status == "paused"
    # Paused collection jobs stay paused with their reasons.
    market = jobs_runner.get_definition(session, "market_post_close")
    assert market.status == "paused"
    assert "written PSX permission" in (market.pause_reason or "")


# ---------------------------------------------------------------------------
# Runner: idempotency, claim overlap, retry, dead-letter
# ---------------------------------------------------------------------------


def test_idempotent_replay_calls_handler_once(tmp_path, monkeypatch) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "counter_job", "test_counter")
    calls: list[str] = []

    def _counter(ctx):
        calls.append("ran")
        return {"n": len(calls)}

    monkeypatch.setitem(jobs_runner.HANDLERS, "test_counter", _counter)
    day = date(2026, 11, 5)
    first = jobs_runner.run_one(session, "counter_job", scheduled_for=day)
    assert first["status"] == "succeeded"
    second = jobs_runner.run_one(session, "counter_job", scheduled_for=day)
    assert second["status"] == "succeeded"
    assert second["idempotent_replay"] is True
    assert calls == ["ran"]
    assert session.query(JobRun).count() == 1


def test_claim_overlap_second_runner_loses(tmp_path) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "counter_job", "test_counter")
    session2 = _session(engine)
    run = JobRun(
        job_key="counter_job",
        idempotency_key="counter_job:2026-11-05",
        scheduled_for=date(2026, 11, 5),
        status="queued",
    )
    session.add(run)
    session.commit()
    assert jobs_runner.claim_run(session, run, "owner-a", 300) is True
    # Second runner, fresh session object, same row: loses.
    run2 = session2.query(JobRun).filter_by(id=run.id).one()
    assert jobs_runner.claim_run(session2, run2, "owner-b", 300) is False
    assert session2.query(JobRun).filter_by(id=run.id).one().status == "running"


def test_retry_backoff_then_dead_letter(tmp_path, monkeypatch) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(
        session,
        "flaky_job",
        "test_flaky",
        max_attempts=2,
        backoff_base_seconds=60,
    )

    def _flaky(ctx):
        raise RuntimeError("boom")

    monkeypatch.setitem(jobs_runner.HANDLERS, "test_flaky", _flaky)
    day = date(2026, 11, 5)
    # Watermark yesterday so run-due does not also materialise
    # 30 days of catch-up occurrences for this test job.
    jobs_runner.write_checkpoint(session, "flaky_job", "last_processed_occurrence", "2026-11-04")
    first = jobs_runner.run_one(session, "flaky_job", scheduled_for=day)
    assert first["status"] == "failed"
    assert first["attempt"] == 1
    run = session.query(JobRun).one()
    nxt = run.next_attempt_at
    assert nxt is not None
    # Backoff: base 60 * 2 ** (attempt-1) = 60s after attempt 1.
    started = run.started_at
    assert started is not None
    delta = (nxt.replace(tzinfo=timezone.utc) if nxt.tzinfo is None else nxt) - (
        started.replace(tzinfo=timezone.utc) if started.tzinfo is None else started
    )
    assert 55 <= delta.total_seconds() <= 65
    # Retry too early via run-due: still failed (backoff running).
    jobs_runner.run_due(session, day)
    assert session.query(JobRun).one().status == "failed"
    # Move the retry time into the past: second attempt exhausts.
    run.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    session.commit()
    jobs_runner.run_due(session, day)
    run = session.query(JobRun).one()
    assert run.status == "dead"
    assert session.query(JobDeadLetter).count() == 1
    letter = session.query(JobDeadLetter).one()
    assert letter.idempotency_key == "flaky_job:2026-11-05"
    assert letter.resolved is False


def test_non_retryable_collection_stub_dead_letters_immediately(
    tmp_path,
) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    # Test-only: activate the market collection job to prove the
    # stub dead-letters on first attempt (production seed: paused).
    _define(session, "market_post_close", "collection_market_post_close", max_attempts=3)
    result = jobs_runner.run_one(session, "market_post_close", scheduled_for=date(2026, 11, 5))
    assert result["status"] == "dead"
    run = session.query(JobRun).one()
    assert run.attempt == 1  # no retries spent
    assert session.query(JobDeadLetter).count() == 1


def test_unknown_handler_dead_letters(tmp_path) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "ghost_job", "no_such_handler")
    result = jobs_runner.run_one(session, "ghost_job", scheduled_for=date(2026, 11, 5))
    assert result["status"] == "dead"
    assert "unknown handler" in result["error"]


# ---------------------------------------------------------------------------
# Runner: lease reclaim, checkpoints, cancellation, dependencies
# ---------------------------------------------------------------------------


def test_lease_reclaim_after_crash_and_live_lease_untouched(tmp_path) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "counter_job", "test_counter")
    now = datetime.now(timezone.utc)
    crashed = JobRun(
        job_key="counter_job",
        idempotency_key="counter_job:2026-11-05",
        scheduled_for=date(2026, 11, 5),
        status="running",
        attempt=1,
        lease_owner="dead-process",
        lease_expires_at=now - timedelta(seconds=10),
        started_at=now - timedelta(minutes=5),
    )
    live = JobRun(
        job_key="counter_job",
        idempotency_key="counter_job:2026-11-06",
        scheduled_for=date(2026, 11, 6),
        status="running",
        attempt=1,
        lease_owner="live-process",
        lease_expires_at=now + timedelta(minutes=5),
        started_at=now,
    )
    session.add_all([crashed, live])
    session.commit()
    reclaimed = jobs_runner.reclaim_stale(session, now)
    assert crashed.id in reclaimed["requeued"]
    assert live.id not in reclaimed["requeued"] + reclaimed["dead"]
    assert session.query(JobRun).filter_by(id=crashed.id).one().status == "queued"
    assert (
        session.query(JobRun).filter_by(id=crashed.id).one().error == "reclaimed_after_lease_expiry"
    )
    assert session.query(JobRun).filter_by(id=live.id).one().status == "running"


def test_checkpoint_resume_after_mid_run_failure(tmp_path, monkeypatch) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "step_job", "test_steps", max_attempts=3)
    executed: list[str] = []

    def _steps(ctx):
        # Occurrence-scoped checkpoint key: step state must not
        # leak across occurrences of the same job.
        key = f"step:{ctx.run.scheduled_for}"
        done = (
            ctx.session.query(JobCheckpoint)
            .filter_by(job_key="step_job", watermark_key=key)
            .first()
        )
        step = done.watermark_value if done else "0"
        if step == "0":
            executed.append("step1")
            ctx.checkpoint(key, "1")
        if step in ("0", "1"):
            executed.append("step2")
            ctx.checkpoint(key, "2")
            raise RuntimeError("crash after step 2")
        executed.append("step3")
        return {"done": True}

    monkeypatch.setitem(jobs_runner.HANDLERS, "test_steps", _steps)
    day = date(2026, 11, 5)
    # Watermark yesterday so run-due retries only this occurrence.
    jobs_runner.write_checkpoint(session, "step_job", "last_processed_occurrence", "2026-11-04")
    first = jobs_runner.run_one(session, "step_job", scheduled_for=day)
    assert first["status"] == "failed"
    # Partial checkpoints survived the failure (committed immediately).
    assert (
        session.query(JobCheckpoint)
        .filter_by(job_key="step_job", watermark_key=f"step:{day}")
        .one()
        .watermark_value
        == "2"
    )
    run = session.query(JobRun).one()
    run.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    session.commit()
    jobs_runner.run_due(session, day)
    assert session.query(JobRun).one().status == "succeeded"
    assert executed == ["step1", "step2", "step3"]  # steps 1-2 NOT redone


def test_cancel_rules_and_watermark(tmp_path, monkeypatch) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "counter_job", "test_counter")
    monkeypatch.setitem(jobs_runner.HANDLERS, "test_counter", lambda ctx: {"ok": True})
    queued = JobRun(
        job_key="counter_job",
        idempotency_key="counter_job:2026-11-05",
        scheduled_for=date(2026, 11, 5),
        status="queued",
    )
    running = JobRun(
        job_key="counter_job",
        idempotency_key="counter_job:2026-11-06",
        scheduled_for=date(2026, 11, 6),
        status="running",
        attempt=1,
        lease_owner="someone",
        lease_expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    session.add_all([queued, running])
    session.commit()
    assert jobs_runner.cancel_run(session, queued.id)["status"] == "cancelled"
    # Cancellation is terminal: the watermark advances past it.
    assert jobs_runner.last_processed_occurrence(session, "counter_job") == date(2026, 11, 5)
    assert "error" in jobs_runner.cancel_run(session, running.id)
    assert jobs_runner.cancel_run(session, 999999)["error"] == "unknown run"


def test_dependency_gate_blocks_then_unblocks(tmp_path, monkeypatch) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "upstream", "test_ok")
    _define(session, "downstream", "test_ok", dependencies=["upstream"])
    monkeypatch.setitem(jobs_runner.HANDLERS, "test_ok", lambda ctx: {"ok": True})
    day = date(2026, 11, 5)
    # Downstream first: blocked (upstream run exists but unrun).
    upstream_run = JobRun(
        job_key="upstream",
        idempotency_key="upstream:2026-11-05",
        scheduled_for=day,
        status="queued",
    )
    session.add(upstream_run)
    session.commit()
    blocked = jobs_runner.run_one(session, "downstream", scheduled_for=day)
    assert blocked["status"] == "blocked"
    assert "upstream" in (blocked["blocked_reason"] or "")
    # Upstream succeeds -> downstream unblocks and runs.
    assert jobs_runner.run_one(session, "upstream", scheduled_for=day)["status"] == "succeeded"
    assert jobs_runner.run_one(session, "downstream", scheduled_for=day)["status"] == "succeeded"


def test_dependency_dead_keeps_dependent_blocked(tmp_path, monkeypatch) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "upstream", "test_flaky", max_attempts=1)
    _define(session, "downstream", "test_ok", dependencies=["upstream"])

    def _flaky(ctx):
        raise RuntimeError("boom")

    monkeypatch.setitem(jobs_runner.HANDLERS, "test_flaky", _flaky)
    monkeypatch.setitem(jobs_runner.HANDLERS, "test_ok", lambda ctx: {"ok": True})
    day = date(2026, 11, 5)
    assert jobs_runner.run_one(session, "upstream", scheduled_for=day)["status"] == "dead"
    blocked = jobs_runner.run_one(session, "downstream", scheduled_for=day)
    assert blocked["status"] == "blocked"
    assert "dead" in (blocked["blocked_reason"] or "")


def test_paused_job_refused_without_creating_a_run(tmp_path) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    jobs_runner.register_definitions(session)
    result = jobs_runner.run_one(session, "market_post_close", scheduled_for=date(2026, 11, 5))
    assert result["error"] == "job is paused"
    assert session.query(JobRun).count() == 0
    assert jobs_runner.run_one(session, "no_such_job")["error"] == "unknown job"


def test_retry_dead_letter_creates_fresh_run(tmp_path, monkeypatch) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "flaky_job", "test_flaky", max_attempts=1)
    monkeypatch.setitem(
        jobs_runner.HANDLERS,
        "test_flaky",
        lambda ctx: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    day = date(2026, 11, 5)
    assert jobs_runner.run_one(session, "flaky_job", scheduled_for=day)["status"] == "dead"
    letter = session.query(JobDeadLetter).one()
    retry = jobs_runner.retry_dead_letter(session, letter.id)
    assert retry["status"] == "queued"
    assert retry["new_idempotency_key"] == "flaky_job:2026-11-05:retry-1"
    assert session.query(JobDeadLetter).one().resolved is True
    assert "error" in jobs_runner.retry_dead_letter(session, letter.id)


def test_run_due_materialises_bounded_catchup_and_executes(tmp_path, monkeypatch) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    _define(session, "daily_job", "test_ok", schedule_spec={"time": "07:00"})
    monkeypatch.setitem(jobs_runner.HANDLERS, "test_ok", lambda ctx: {"ok": True})
    # Watermark 20 days back: only 7 oldest occurrences materialise.
    jobs_runner.write_checkpoint(session, "daily_job", "last_processed_occurrence", "2026-10-16")
    summary = jobs_runner.run_due(session, date(2026, 11, 5))
    assert len(summary["materialised"]["created"]) == 7
    assert len(summary["executed"]) == 7
    assert all(e["status"] == "succeeded" for e in summary["executed"])
    assert jobs_runner.last_processed_occurrence(session, "daily_job") == date(2026, 10, 23)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _business_tables(session, tables: dict[str, int]) -> None:
    for name in tables:
        session.execute(text(f"CREATE TABLE {name} (id INTEGER PRIMARY KEY)"))
    session.commit()
    for name, count in tables.items():
        for i in range(count):
            session.execute(text(f"INSERT INTO {name} (id) VALUES (:i)"), {"i": i + 1})
    session.commit()


def test_drift_check_reports_differences_but_succeeds(tmp_path, monkeypatch) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    tables = {name: 0 for name in job_handlers.EXPECTED_COUNTS}
    _business_tables(session, tables)
    # Empty tables vs the Phase 24 baseline: every table with
    # a nonzero expectation drifts (the four legitimately-zero
    # tables match), but drift is a finding, so the handler
    # still succeeds.
    result = job_handlers.handle_drift_check(
        job_handlers.JobContext(
            session=session,
            run=JobRun(job_key="drift_check", idempotency_key="x"),
            params={},
            checkpoint=lambda *a, **k: None,
        )
    )
    expected_drift = sum(1 for v in job_handlers.EXPECTED_COUNTS.values() if v != 0)
    assert result["drift_count"] == expected_drift
    # With a matching baseline, drift is zero.
    monkeypatch.setattr(job_handlers, "EXPECTED_COUNTS", {"companies": 0, "alerts": 0})
    result2 = job_handlers.handle_drift_check(
        job_handlers.JobContext(
            session=session,
            run=JobRun(job_key="drift_check", idempotency_key="x"),
            params={},
            checkpoint=lambda *a, **k: None,
        )
    )
    assert result2["drift_count"] == 0
    # Missing table is infrastructure failure, not drift.
    monkeypatch.setattr(job_handlers, "EXPECTED_COUNTS", {"no_such_table": 0})
    with pytest.raises(job_handlers.HandlerError):
        job_handlers.handle_drift_check(
            job_handlers.JobContext(
                session=session,
                run=JobRun(job_key="drift_check", idempotency_key="x"),
                params={},
                checkpoint=lambda *a, **k: None,
            )
        )


def test_alert_digest_baseline_and_watermark(tmp_path) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    session.execute(
        text(
            "CREATE TABLE alerts (id INTEGER PRIMARY KEY, severity TEXT, "
            "status TEXT, processing_time DATETIME)"
        )
    )
    session.execute(
        text(
            "INSERT INTO alerts VALUES (1, 'INFO', 'NEW', '2026-11-04 10:00:00'), "
            "(2, 'CRITICAL', 'NEW', '2026-11-04 11:00:00')"
        )
    )
    session.commit()
    ctx = job_handlers.JobContext(
        session=session,
        run=JobRun(job_key="alert_digest", idempotency_key="x"),
        params={},
        checkpoint=lambda k, v, d=None: jobs_runner.write_checkpoint(
            session, "alert_digest", k, v, d
        ),
    )
    first = job_handlers.handle_alert_digest(ctx)
    assert first["baseline"] is True
    assert first["alerts_total"] == 2
    assert first["by_severity"] == {"INFO": 1, "CRITICAL": 1}
    assert first["delivery"] == "in_app_only"
    second = job_handlers.handle_alert_digest(ctx)
    assert second["baseline"] is False
    assert second["new_since_last_digest"] == 0
    # PKT boundary: an alert processed 2026-11-04 22:30 UTC is
    # 2026-11-05 03:30 PKT, so it counts as new against a
    # 2026-11-04 PKT watermark (a UTC-date watermark would miss it).
    session.execute(text("INSERT INTO alerts VALUES (3, 'WARNING', 'NEW', '2026-11-04 22:30:00')"))
    session.execute(
        text(
            "UPDATE job_checkpoints SET watermark_value = '2026-11-04' "
            "WHERE job_key = 'alert_digest' "
            "AND watermark_key = 'last_digest_date'"
        )
    )
    session.commit()
    third = job_handlers.handle_alert_digest(ctx)
    assert third["new_since_last_digest"] == 1


def test_retention_purge_dry_run_then_confirm(tmp_path) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    session.execute(
        text("CREATE TABLE auth_audit_logs (id INTEGER PRIMARY KEY, created_at DATETIME)")
    )
    old = (datetime.now(timezone.utc) - timedelta(days=400)).strftime("%Y-%m-%d %H:%M:%S")
    new = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    session.execute(
        text("INSERT INTO auth_audit_logs VALUES (1, :old), (2, :new)"),
        {"old": old, "new": new},
    )
    session.commit()
    ctx = job_handlers.JobContext(
        session=session,
        run=JobRun(job_key="retention_purge", idempotency_key="x"),
        params={},
        checkpoint=lambda *a, **k: None,
    )
    dry = job_handlers.handle_retention_purge(ctx)
    assert dry["dry_run"] is True and dry["deleted"] == 0
    assert dry["candidates_older_than_12_months"] == 1
    assert session.execute(text("SELECT COUNT(*) FROM auth_audit_logs")).first()[0] == 2
    ctx.params = {"confirm": True}
    confirmed = job_handlers.handle_retention_purge(ctx)
    assert confirmed["deleted"] == 1
    assert session.execute(text("SELECT COUNT(*) FROM auth_audit_logs")).first()[0] == 1


def test_report_qa_audit_asserts_no_publish_path(tmp_path) -> None:
    engine = _engine(tmp_path)
    session = _session(engine)
    session.execute(text("CREATE TABLE reports (id INTEGER PRIMARY KEY, status TEXT)"))
    session.execute(text("CREATE TABLE report_figures (id INTEGER PRIMARY KEY, report_id INTEGER)"))
    session.execute(text("INSERT INTO reports VALUES (1, 'DRAFT'), (2, 'DRAFT')"))
    session.execute(text("INSERT INTO report_figures VALUES (1, 1), (2, 1), (3, 2)"))
    session.commit()
    result = job_handlers.handle_report_qa_audit(
        job_handlers.JobContext(
            session=session,
            run=JobRun(job_key="report_qa_audit", idempotency_key="x"),
            params={},
            checkpoint=lambda *a, **k: None,
        )
    )
    assert result["reports_total"] == 2
    assert result["by_status"] == {"DRAFT": 2}
    assert result["figures_total"] == 3
    assert result["empty_reports"] == []
    assert result["publish_columns"] == []
    assert result["published_externally"] == 0


# ---------------------------------------------------------------------------
# API + scans
# ---------------------------------------------------------------------------


def test_jobs_router_is_get_only() -> None:
    from app.api.v1.endpoints import jobs as jobs_endpoint

    methods = {tuple(sorted(route.methods)) for route in jobs_endpoint.router.routes}
    assert methods == {("GET",)}


def test_jobs_api_endpoints(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "jobs_api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    from app.database import Base

    app = create_app()
    engine = app.state.engine
    assert engine is not None
    tables = [t for n, t in Base.metadata.tables.items() if n in JOB_TABLES]
    Base.metadata.create_all(engine, tables=tables)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        jobs_runner.register_definitions(session)
        run = JobRun(
            job_key="system_health",
            idempotency_key="system_health:2026-11-05",
            scheduled_for=date(2026, 11, 5),
            status="succeeded",
            result_summary={"database": "reachable"},
        )
        session.add(run)
        session.commit()
        run_id = run.id
    with TestClient(app, raise_server_exceptions=False) as client:
        defs = client.get("/api/v1/jobs/definitions")
        assert defs.status_code == 200
        assert len(defs.json()["definitions"]) == len(JOB_DEFINITIONS)
        paused = [d for d in defs.json()["definitions"] if d["status"] == "paused"]
        assert {d["job_key"] for d in paused} == {
            "market_post_close",
            "filing_check",
            "macro_release_check",
            "news_collection_daily",
            "news_reconciliation_post_close",
        }
        runs = client.get("/api/v1/jobs/runs")
        assert runs.status_code == 200
        assert runs.json()["total"] == 1
        one = client.get(f"/api/v1/jobs/runs/{run_id}")
        assert one.status_code == 200
        assert one.json()["idempotency_key"] == "system_health:2026-11-05"
        assert client.get("/api/v1/jobs/runs/999999").status_code == 404
        assert client.get("/api/v1/jobs/runs?limit=0").status_code == 400
        assert client.get("/api/v1/jobs/checkpoints").status_code == 200
        assert client.get("/api/v1/jobs/dead-letters").status_code == 200
        status = client.get("/api/v1/jobs/status")
        assert status.status_code == 200
        assert status.json()["runs_by_status"] == {"succeeded": 1}
    get_settings.cache_clear()


def test_no_execution_identifiers_in_new_code() -> None:
    import re

    root = Path(__file__).resolve().parents[1]
    identifiers = (
        "place_order",
        "execute_order",
        "submit_order",
        "execute_trade",
        "place_trade",
    )
    hits = []
    for path in (
        root / "app" / "services" / "jobs",
        root / "app" / "api" / "v1" / "endpoints" / "jobs.py",
        root / "app" / "models" / "jobs.py",
        Path(__file__).resolve().parents[2] / "scripts" / "run_jobs.py",
    ):
        if path.is_dir():
            files = sorted(path.glob("*.py"))
        else:
            files = [path]
        for f in files:
            for name in identifiers:
                if re.search(rf"\b{name}\b", f.read_text()):
                    hits.append(f"{f.name}:{name}")
    assert hits == []
