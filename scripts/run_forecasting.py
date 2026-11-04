"""Phase 13 forecasting CLI.

Builds the forecast target registry, the feature store (snapshots
of already-stored Phase 8/9/10 values as of the forecast origin)
and one assessment row per (security, target, horizon). Writes
nothing by default (--dry-run); --commit writes idempotently (a
second --commit writes 0 new rows). No HTTP fetch happens in this
script; no Phase 3 ``forecasts`` row is written (no interval is
validatable from one trading date — see docs/phase-13/).

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_forecasting.py --dry-run
  python scripts/run_forecasting.py --commit
  python scripts/run_forecasting.py --commit --company HUBC

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

from sqlalchemy.orm import sessionmaker

from app.database import build_engine
from app.services.forecasting import runner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument(
        "--commit", action="store_true", help="Actually write Phase 13 rows."
    )
    parser.add_argument(
        "--company", default=None, help="Limit to one ticker (e.g. HUBC)."
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
        report = runner.run_forecasting(
            session, commit=bool(args.commit), company_filter=args.company
        )
        if args.commit:
            session.commit()
    except Exception as exc:  # noqa: BLE001 - CLI reports and exits non-zero
        session.rollback()
        print(f"Forecasting run failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
    print(json.dumps(report, indent=2, default=str))
    print(
        "Forecasting run: "
        f"targets={report['targets_written']}/{report['targets_skipped']} "
        f"snapshots={report['snapshots_written']}/{report['snapshots_skipped']} "
        f"assessments={report['assessments_written']}/{report['assessments_skipped']} "
        f"computed={report['assessments_computed']} "
        f"phase3_forecasts={report['phase3_forecasts_rows']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
