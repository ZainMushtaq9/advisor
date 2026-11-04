"""Phase 17 backtesting CLI.

Builds the strategy registry, backtest runs, metric rows, paper
ledger entries, and bias reports from already-stored rows only.
Writes nothing by default (--dry-run); --commit writes
idempotently (a second --commit writes 0 new rows). No HTTP
fetch happens in this script; no forecast is generated; no live
execution exists anywhere in this project. Every backtest result
is a SIMULATION, and every production run is NOT_RUNNABLE
because the window holds a single price observation.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_backtesting.py --dry-run
  python scripts/run_backtesting.py --commit

Exit codes: 0 ok; 1 operational failure; 2 bad arguments / missing
DATABASE_URL. The report is JSON on stdout; the summary line goes to
stderr so the JSON stays parseable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import build_engine
from app.services.backtesting import runner
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument(
        "--commit", action="store_true", help="Actually write Phase 17 rows."
    )
    args = parser.parse_args()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set; refusing to run.", file=sys.stderr)
        return 2
    engine = build_engine(database_url)
    if engine is None:
        print("Could not build a database engine.", file=sys.stderr)
        return 1
    session = sessionmaker(bind=engine)()
    try:
        report = runner.run_backtesting(session, commit=bool(args.commit))
    except Exception as exc:  # noqa: BLE001 - CLI reports and exits 1
        print(f"Backtesting run failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, default=str))
    print(
        "dry-run complete (nothing written)."
        if not args.commit
        else "commit complete.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
