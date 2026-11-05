"""Phase 20 screener CLI.

Seeds the five v1 screens and runs them over stored rows.
Writes nothing by default (--dry-run); --commit writes
idempotently (definitions by (name, version); runs by
(definition, as-of date); results by (run, security)).

No HTTP fetch happens in this script; no price, ratio, or
forecast is generated; no live execution exists anywhere in
this project. Screen matches are filter results, not
investment opportunities, recommendations, or forecasts.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_screener.py --dry-run
  python scripts/run_screener.py --commit
  python scripts/run_screener.py --screen cheap_profitable --commit

Exit codes: 0 ok; 1 operational failure; 2 bad arguments /
missing DATABASE_URL. The report is JSON on stdout; the
summary line goes to stderr so the JSON stays parseable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy.orm import sessionmaker

from app.database import build_engine
from app.services.screener import SEED_SCREENS
from app.services.screener import runner as screener_runner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument("--commit", action="store_true", help="Actually write Phase 20 rows.")
    parser.add_argument(
        "--screen",
        type=str,
        default=None,
        help="Run one seed screen by name (default: all).",
    )
    parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help="Snapshot date ISO (default 2026-11-04). A later date creates a new "
        "run snapshot; the HBL re-run batch uses 2026-11-05 for dividend_payers only.",
    )
    args = parser.parse_args()
    commit = bool(args.commit)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2
    engine = build_engine(database_url)
    session = sessionmaker(bind=engine)()
    try:
        seeded = screener_runner.seed_definitions(session, commit=commit)
        screens = SEED_SCREENS
        if args.screen:
            screens = [s for s in SEED_SCREENS if s["name"] == args.screen]
            if not screens:
                print(f"Unknown screen: {args.screen}", file=sys.stderr)
                return 2
        from datetime import date as _date

        as_of = _date.fromisoformat(args.as_of) if args.as_of else None
        runs = [
            screener_runner.run_screen(session, s, commit=commit, as_of=as_of)
            for s in screens
        ]
        report = {"seeded": seeded, "runs": runs, "committed": commit}
        print(json.dumps(report, indent=2, default=str))
        if commit:
            print(
                f"Screener: {len(runs)} runs, "
                f"{sum(r.get('written', 0) for r in runs)} rows written.",
                file=sys.stderr,
            )
        else:
            print(
                f"Screener dry-run: {len(runs)} runs, "
                f"{sum(r.get('would_write', 0) for r in runs)} rows would be written.",
                file=sys.stderr,
            )
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
