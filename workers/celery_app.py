"""Celery application for PSX Intelligence AI (Phase 2, Team E).

Fixed stack (Phase 1): Celery + self-hosted Redis, PKR 0 licence cost.
Broker and result backend are both Redis, configured only from the
environment — no credential or URL is hardcoded here beyond the local-dev
defaults (broker ``redis://127.0.0.1:6379/0``, results
``redis://127.0.0.1:6379/1``; no password; loopback only).

Run a worker (from the repo root, with the venv active)::

    celery -A workers.celery_app worker --loglevel=info

Or from ``workers/`` itself::

    celery -A celery_app worker --loglevel=info

This module defines NO scheduled jobs and NO agent scheduler. Celery
Beat is deliberately not configured here: scheduling is a later-phase
decision owned by the backend / operations runbook, not by this app.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from celery import Celery
from celery.signals import worker_ready, worker_shutdown

logger = logging.getLogger("psx_intelligence_ai.worker")

# Broker DB 0, result DB 1 — matching the Team A configuration contract
# (docs/phase-02/LOCAL_DEVELOPMENT_GUIDE.md §3: broker /0, results /1).
# CELERY_BROKER_URL wins; REDIS_URL is accepted as a broker alias.
BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL", os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
)
RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"
)
HEARTBEAT_KEY = "psx:worker:heartbeat"
HEARTBEAT_TTL_SECONDS = 120

# ``include`` must match how the app is imported: as a package from the
# repo root (``workers.tasks``) or as a top-level module from workers/.
_TASK_MODULE = "workers.tasks" if __package__ else "tasks"

app = Celery(
    "psx_intelligence_ai",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[_TASK_MODULE],
)

app.conf.update(
    # JSON only: never pickle task payloads (untrusted-payload risk).
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # UTC internally; display timezone is Asia/Karachi for operator logs.
    timezone="Asia/Karachi",
    enable_utc=True,
    # Retries: bounded, with exponential back-off. A task that keeps
    # failing is reported failed, not retried forever.
    task_default_retry_delay=30,
    task_max_retries=3,
    task_autoretry_behavior=True,
    # Results expire so the result backend does not grow unbounded.
    result_expires=3600,
    # A worker that dies mid-task does not silently lose the task record:
    # the result backend keeps the last known state.
    task_track_started=True,
)


def _heartbeat_payload() -> str:
    return datetime.now(timezone.utc).isoformat()


@worker_ready.connect
def _write_heartbeat(**kwargs: object) -> None:
    """Record a worker heartbeat in Redis (TTL'd, best-effort).

    The backend ``/health`` / ``scripts/healthcheck.sh`` worker check reads
    this key. If Redis is unreachable the worker still starts; the missing
    key is itself the signal that the heartbeat path is down.
    """
    try:
        import redis

        client = redis.Redis.from_url(BROKER_URL, socket_connect_timeout=2)
        client.set(HEARTBEAT_KEY, _heartbeat_payload(), ex=HEARTBEAT_TTL_SECONDS)
        client.close()
        logger.info("worker heartbeat written to %s", HEARTBEAT_KEY)
    except Exception:  # noqa: BLE001 - heartbeat must never crash startup
        logger.warning("worker heartbeat write failed (Redis unreachable?)", exc_info=True)


@worker_shutdown.connect
def _clear_heartbeat(**kwargs: object) -> None:
    try:
        import redis

        client = redis.Redis.from_url(BROKER_URL, socket_connect_timeout=2)
        client.delete(HEARTBEAT_KEY)
        client.close()
    except Exception:  # noqa: BLE001 - best-effort cleanup only
        pass
