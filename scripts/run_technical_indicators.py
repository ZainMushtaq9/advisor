"""Phase 6 technical-indicator assessment CLI.

Reads ONLY already-committed daily market_prices rows and assesses
every registered indicator for every registry security. Writes
nothing by default (--dry-run); --commit writes one calculation-run
row, aggregate error rows, and value rows for CALCULABLE verdicts
only (none are expected on the current single-day data).

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_technical_indicators.py --dry-run
  python scripts/run_technical_indicators.py --commit [--as-of YYYY-MM-DD]

Exit codes: 0 ok; 1 operational failure; 2 bad arguments / missing
DATABASE_URL. The report is JSON on stdout; the summary line goes
to stderr so the JSON stays parseable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import build_engine
from app.services.technical_indicators import runner
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of", default=None, help="As-of ISO date (default: latest price date)."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Report only; write nothing (default).")
    mode.add_argument("--commit", action="store_true", help="Actually write run/error/value rows.")
    args = parser.parse_args()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set; refusing to run.", file=sys.stderr)
        return 2
    try:
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
    except ValueError:
        print(f"--as-of must be an ISO date (YYYY-MM-DD), got: {args.as_of}", file=sys.stderr)
        return 2
    engine = build_engine(database_url)
    if engine is None:
        print("Could not build a database engine.", file=sys.stderr)
        return 1
    session = sessionmaker(bind=engine)()
    try:
        report = runner.run_assessment(session, as_of=as_of, dry_run=not args.commit)
    finally:
        session.close()
        engine.dispose()
    print(json.dumps(report, indent=2, default=str))
    print(
        f"run={report['run_key']} dry_run={report['dry_run']} "
        f"securities={report['securities_assessed']} "
        f"any_calculable={report['securities_with_any_calculable']} "
        f"values_written={report['values_written']} "
        f"error_rows={report['error_rows_written']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
