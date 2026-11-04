"""Phase 9 valuation CLI.

Reads ONLY already-committed Phase 7 statement rows, Phase 8 period
configuration, and Phase 5 price rows, and assesses every registered
valuation method for the configured company-periods. Writes nothing
by default (--dry-run); --commit writes valuation rows idempotently
(a second --commit writes 0 new rows).

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_valuation.py --dry-run
  python scripts/run_valuation.py --commit [--company HUBC,NML,OGDC]

Exit codes: 0 ok; 1 operational failure; 2 bad arguments / missing
DATABASE_URL. The report is JSON on stdout; the summary line goes
to stderr so the JSON stays parseable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import build_engine
from app.models.reference import Security
from app.services.fundamental_analysis import PERIODS
from app.services.valuation import runner
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--company",
        default=None,
        help="Comma-separated tickers to assess (default: all configured companies).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument(
        "--commit", action="store_true", help="Actually write valuation rows."
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
        company_ids = None
        if args.company:
            wanted = [t.strip() for t in args.company.split(",") if t.strip()]
            rows = session.query(Security).filter(Security.ticker.in_(wanted)).all()
            found = {r.ticker: r.company_id for r in rows}
            missing = [t for t in wanted if t not in found]
            if missing:
                print(f"Unknown tickers: {', '.join(missing)}", file=sys.stderr)
                return 2
            company_ids = [found[t] for t in wanted if found[t] in PERIODS]
            if not company_ids:
                print(
                    "No configured company-periods among the requested tickers.",
                    file=sys.stderr,
                )
                return 2
        report = runner.run_valuation(
            session, company_ids=company_ids, dry_run=not args.commit
        )
    except Exception as exc:  # operational failure; session rolls back
        session.rollback()
        print(f"Run failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
        engine.dispose()
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
