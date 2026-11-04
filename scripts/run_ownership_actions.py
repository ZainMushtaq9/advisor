"""Phase 12 ownership/actions/breadth CLI.

Loads HUBC ownership and dividend actions from verified seed data,
adjustment rule definitions, and breadth/liquidity metrics computed
from stored Phase 5 prices. Writes nothing by default (--dry-run);
--commit writes idempotently (a second --commit writes 0 new rows).
No HTTP fetch happens in this script; no adjusted price series is
stored; no investor-flow rows are written.

Usage (DATABASE_URL must be set, e.g. from database/.env): <redacted>
  python scripts/run_ownership_actions.py --dry-run
  python scripts/run_ownership_actions.py --commit

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
from app.services.ownership_actions import runner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument("--commit", action="store_true", help="Actually write Phase 12 rows.")
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
        report = runner.run_ownership(session, commit=bool(args.commit))
        if args.commit:
            session.commit()
    except Exception as exc:  # noqa: BLE001 - CLI reports and exits non-zero
        session.rollback()
        print(f"Ownership run failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
    report["mode"] = "commit" if args.commit else "dry-run"
    print(json.dumps(report, indent=2, default=str))
    print(
        f"Ownership Phase 12 [{report['mode']}]: "
        f"{report['ownership_inserted']} ownership, "
        f"{report['actions_inserted']} actions, "
        f"{report['breadth_inserted']} breadth, "
        f"{report['liquidity_inserted']} liquidity, "
        f"{report['flows_inserted']} flows, "
        f"{report['priced']}/{report['universe']} priced",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
