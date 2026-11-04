"""Test / probe tasks only (Phase 2, Team E).

These tasks prove the Celery + Redis path end to end. They carry NO
market data, NO fabricated PSX figures, and NO agent/scheduler logic.
Real jobs (collection, PDF extraction, reports) are later-phase work
and must be added as their own tasks with their own specs — not by
extending these probes.

Task logging: every task logs its task id, inputs (never credentials),
and result at INFO level, so a run is auditable from worker logs alone.
"""

from __future__ import annotations

import logging
import platform
from datetime import datetime, timezone

from celery import Task

from .celery_app import app

logger = logging.getLogger("psx_intelligence_ai.worker.tasks")


class LoggedTask(Task):
    """Base task: structured start/finish logging + bounded retries."""

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 300
    max_retries = 3
    default_retry_delay = 30

    def on_success(self, retval, task_id, args, kwargs):  # type: ignore[no-untyped-def]
        logger.info("task succeeded task_id=%s name=%s result=%r", task_id, self.name, retval)

    def on_failure(self, exc, task_id, args, kwargs, einfo):  # type: ignore[no-untyped-def]
        logger.error("task failed task_id=%s name=%s error=%r", task_id, self.name, exc)

    def on_retry(self, exc, task_id, args, kwargs, einfo):  # type: ignore[no-untyped-def]
        logger.warning("task retrying task_id=%s name=%s error=%r", task_id, self.name, exc)


@app.task(base=LoggedTask, bind=True, name="psx_intelligence_ai.add")
def add(self, a: int, b: int) -> int:
    """Smoke-test task: returns ``a + b``. Used for the Phase 2 proof run."""
    logger.info("task started task_id=%s name=add a=%r b=%r", self.request.id, a, b)
    return a + b


@app.task(base=LoggedTask, bind=True, name="psx_intelligence_ai.health_probe")
def health_probe(self) -> dict:
    """Worker health probe: proves a worker is alive and can reply.

    Returns only worker identity and time — no data, no credentials.
    The backend ``/health`` endpoint (other team) may call this task and
    report its result; this task itself does not serve HTTP.
    """
    logger.info("task started task_id=%s name=health_probe", self.request.id)
    return {
        "status": "ok",
        "worker": platform.node(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
