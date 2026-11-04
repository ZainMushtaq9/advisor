"""Phase 16 portfolio construction CLI.

Builds simulated portfolios (equal-weight baseline, rule-based
SCREEN_PASS portfolios) from already-stored rows only, plus a
NOT_CALCULABLE mean-variance comparison row. Writes nothing by
default (--dry-run); --commit writes idempotently (a second
--commit writes 0 new rows). No HTTP fetch happens in this script;
no forecast is generated; no live execution exists anywhere in
this project. Capital is hypothetical simulation capital, never
real funds.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_portfolio_construction.py --dry-run
  python scripts/run_portfolio_construction.py --commit
  python scripts/run_portfolio_construction.py --commit --profile conservative

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
from app.services.portfolio_construction import runner
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument(
        "--commit", action="store_true", help="Actually write Phase 16 rows."
    )
    parser.add_argument(
        "--profile",
        default=None,
        choices=["conservative", "balanced", "growth"],
        help="Limit rule-based construction to one risk profile.",
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
        report = runner.run_portfolios(
            session, commit=bool(args.commit), profile_filter=args.profile
        )
        if args.commit:
            session.commit()
    except Exception as exc:  # noqa: BLE001 - CLI reports and exits non-zero
        session.rollback()
        print(f"Portfolio run failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
    print(json.dumps(report, indent=2, default=str))
    summary = " | ".join(
        f"{name}: {p['holdings']} holdings, cash={p['cash']}"
        for name, p in report["portfolios"].items()
    )
    print(
        "Portfolio run: "
        f"portfolios={report['portfolios_written']}/{report['portfolios_skipped']} "
        f"holdings={report['holdings_written']}/{report['holdings_skipped']} "
        f"sectors={report['sectors_written']}/{report['sectors_skipped']} "
        f"exclusions={report['exclusions_written']}/{report['exclusions_skipped']} "
        f"comparisons={report['comparisons_written']}/{report['comparisons_skipped']} "
        f"mean_variance={report['mean_variance']['status']} :: {summary}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
