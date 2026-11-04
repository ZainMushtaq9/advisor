"""Dev-only local task runner — NOT Celery, NOT a scheduler (Phase 2, Team E).

Purpose: Phase 1 Config A says local dev runs with "no Redis (in-process
task handling / direct function calls)". This module is that fallback,
for a developer machine where Redis is not installed: a tiny
SQLite-backed queue that runs the same probe functions as
``workers/tasks.py`` in-process, one at a time, with a bounded retry
count recorded in the queue table.

Explicit limits (do not remove these when reusing this file):
  - Dev only. Never use for production data, multi-worker work, or any
    job that must survive a machine restart with guarantees — SQLite
    gives a file, not a broker.
  - No periodic / cron / Beat behaviour. Nothing runs on a schedule;
    the operator runs ``run`` explicitly. The full agent scheduler is
    out of scope for Phase 2 Team E and is NOT implemented here.
  - Only the probe functions registered in ``REGISTRY`` may run. Adding
    a real job here instead of as a Celery task is a defect.

Usage (from the repo root)::

    python -m workers.dev_fallback enqueue add 2 3
    python -m workers.dev_fallback run
    python -m workers.dev_fallback status

Queue file: ``workers/dev_queue.db`` by default (runtime file, gitignored
by ``workers/.gitignore`` convention — never commit it), or
``PSX_DEV_QUEUE_PATH``.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import traceback
from datetime import datetime, timezone

DEFAULT_QUEUE_PATH = os.path.join(os.path.dirname(__file__), "dev_queue.db")
QUEUE_PATH = os.environ.get("PSX_DEV_QUEUE_PATH", DEFAULT_QUEUE_PATH)
MAX_ATTEMPTS = 3


def _add(a: int, b: int) -> int:
    return a + b


def _health_probe() -> dict:
    import platform

    return {
        "status": "ok",
        "worker": f"dev-fallback:{platform.node()}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


REGISTRY = {"add": _add, "health_probe": _health_probe}


def _connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS queue ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT NOT NULL, "
        "args_json TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, "
        "status TEXT NOT NULL DEFAULT 'pending', "
        "result_json TEXT, error TEXT, "
        "created_utc TEXT NOT NULL, updated_utc TEXT NOT NULL)"
    )
    conn.commit()
    return conn


def enqueue(task: str, args: list, path: str = QUEUE_PATH) -> int:
    if task not in REGISTRY:
        raise ValueError(f"unknown dev-fallback task: {task!r} (registry: {sorted(REGISTRY)})")
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect(path)
    cur = conn.execute(
        "INSERT INTO queue (task, args_json, created_utc, updated_utc) VALUES (?, ?, ?, ?)",
        (task, json.dumps(args), now, now),
    )
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    assert job_id is not None
    return job_id


def run_once(path: str = QUEUE_PATH) -> list[dict]:
    """Run every pending job once, in id order. Returns per-job outcomes."""
    conn = _connect(path)
    rows = conn.execute(
        "SELECT id, task, args_json, attempts FROM queue WHERE status='pending' ORDER BY id"
    ).fetchall()
    outcomes = []
    for job_id, task, args_json, attempts in rows:
        now = datetime.now(timezone.utc).isoformat()
        try:
            result = REGISTRY[task](*json.loads(args_json))
            conn.execute(
                "UPDATE queue SET status='done', result_json=?, updated_utc=? WHERE id=?",
                (json.dumps(result, default=str), now, job_id),
            )
            outcomes.append({"id": job_id, "task": task, "status": "done", "result": result})
        except Exception as exc:  # noqa: BLE001 - failure is recorded, not raised
            new_attempts = attempts + 1
            status = "pending" if new_attempts < MAX_ATTEMPTS else "failed"
            conn.execute(
                "UPDATE queue SET status=?, attempts=?, error=?, updated_utc=? WHERE id=?",
                (status, new_attempts, f"{exc.__class__.__name__}: {exc}", now, job_id),
            )
            outcomes.append({"id": job_id, "task": task, "status": status, "error": str(exc)})
        conn.commit()
    conn.close()
    return outcomes


def status(path: str = QUEUE_PATH) -> list[dict]:
    conn = _connect(path)
    rows = conn.execute(
        "SELECT id, task, status, attempts, result_json, error FROM queue ORDER BY id"
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "task": r[1], "status": r[2], "attempts": r[3], "result": r[4], "error": r[5]}
        for r in rows
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dev-only local task runner (not Celery)")
    sub = parser.add_subparsers(dest="command", required=True)
    p_enq = sub.add_parser("enqueue", help="enqueue a probe task")
    p_enq.add_argument("task", choices=sorted(REGISTRY))
    p_enq.add_argument("args", nargs="*", help="JSON values, e.g. 2 3")
    sub.add_parser("run", help="run all pending jobs once")
    sub.add_parser("status", help="list queued jobs")
    args = parser.parse_args(argv)
    try:
        if args.command == "enqueue":
            parsed = [json.loads(a) for a in args.args]
            print(f"enqueued id={enqueue(args.task, parsed)} task={args.task} args={parsed}")
        elif args.command == "run":
            for outcome in run_once():
                print(json.dumps(outcome, default=str))
        elif args.command == "status":
            for row in status():
                print(json.dumps(row, default=str))
    except Exception:
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
