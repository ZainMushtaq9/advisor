"""Phase 27 observability CLI: dry-run default, --commit writes one run.

Usage (from the repo root, with database/.env sourced):
  python scripts/run_observability.py [--run-id ID] [--commit]

Dry-run computes everything and writes nothing. --commit upserts
the SLO definitions and incidents (by key), inserts the run +
measurements + source health + exceptions + performance, and
commits once; a failure rolls back instead of storing a partial
run. A second --commit with the same run_id writes nothing
(idempotency: the run row is the guard).

This CLI reads stored rows and writes observability records
only. It never writes a business row, never promotes a status,
never collects new data, and never executes anything.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import build_engine
from app.services.observability.runner import DEFAULT_RUN_ID, observe
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 27 observability runner")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL is not set (source database/.env first).", file=sys.stderr)
        return 2

    engine = build_engine(os.environ["DATABASE_URL"])
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        summary = observe(session, run_id=args.run_id, commit=args.commit)
    finally:
        session.close()
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
