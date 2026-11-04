"""Worker health check (Phase 2, Team E; exit logic fixed by coordinator 2026-11-04).

Checks, in order:
  1. Redis PING on the broker URL (env ``CELERY_BROKER_URL``).
  2. Worker heartbeat key ``psx:worker:heartbeat`` (written by the worker
     ONLY on ``worker_ready``; TTL 120 s). It therefore expires ~2 minutes
     after startup even while the worker is alive — a missing/stale key
     alone must NOT be read as "worker not running" (coordinator defect
     D-22, found 2026-11-04 when the script reported NOT RUNNING while
     ``celery inspect ping`` ponged and live tasks succeeded).
  3. Celery ``inspect().ping()`` — the authoritative liveness check:
     a reply from at least one node proves a worker is online.

Usage::

    python workers/healthcheck.py            # exit 0 if Redis OK and
                                             # (fresh heartbeat OR inspect ping replies)
    python workers/healthcheck.py --json     # machine-readable output

Exit codes: 0 = Redis reachable AND worker proven up by heartbeat or
inspect ping; 2 = Redis unreachable; 3 = Redis OK but neither heartbeat
nor inspect ping proves a worker up. Heartbeat status is always reported
separately, so a missing heartbeat remains visible even when inspect
ping passes.
This script never starts, stops, or restarts anything.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
HEARTBEAT_KEY = "psx:worker:heartbeat"
HEARTBEAT_MAX_AGE_SECONDS = 180


def check() -> dict:
    """Run the checks; never raise — failures are reported in the dict."""
    result: dict = {
        "redis": "unknown",
        "redis_version": None,
        "worker_heartbeat": "missing",
        "worker_heartbeat_age_seconds": None,
        "worker_inspect": "not_attempted",
    }
    try:
        import redis

        client = redis.Redis.from_url(BROKER_URL, socket_connect_timeout=3)
        if client.ping():
            result["redis"] = "ok"
            info = client.info("server")
            result["redis_version"] = info.get("redis_version")
            raw = client.get(HEARTBEAT_KEY)
            if raw:
                try:
                    ts = datetime.fromisoformat(raw.decode())
                    age = (datetime.now(timezone.utc) - ts).total_seconds()
                    result["worker_heartbeat_age_seconds"] = round(age, 1)
                    result["worker_heartbeat"] = "fresh" if age <= HEARTBEAT_MAX_AGE_SECONDS else "stale"
                except ValueError:
                    result["worker_heartbeat"] = "unparseable"
            client.close()
        else:
            result["redis"] = "no_pong"
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        result["redis"] = f"error: {exc.__class__.__name__}"

    if result["redis"] == "ok":
        try:
            # Works both as ``python -m workers.healthcheck`` (package
            # import) and as ``python workers/healthcheck.py`` (script):
            # the script form has no package, so fall back to the
            # repo-root package import.
            # Script form puts workers/ (not the repo root) on sys.path,
            # so add the repo root explicitly before the package import.
            import pathlib

            repo_root = str(pathlib.Path(__file__).resolve().parent.parent)
            if repo_root not in sys.path:
                sys.path.insert(0, repo_root)
            try:
                from workers.celery_app import app
            except ImportError:
                from .celery_app import app  # type: ignore[no-redef]

            replies = app.control.inspect(timeout=5).ping()
            result["worker_inspect"] = replies if replies else "no_workers_replied"
        except Exception as exc:  # noqa: BLE001 - reported, not raised
            result["worker_inspect"] = f"error: {exc.__class__.__name__}"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PSX worker health check")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args(argv)
    result = check()
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    if result["redis"] != "ok":
        return 2
    inspect_ok = isinstance(result["worker_inspect"], dict) and bool(result["worker_inspect"])
    if result["worker_heartbeat"] == "fresh" or inspect_ok:
        return 0
    return 3


if __name__ == "__main__":
    sys.exit(main())
