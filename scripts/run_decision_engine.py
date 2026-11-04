"""Phase 15 decision engine CLI.

Builds versioned decision rules and per-company decisions
(screening outcome, research conclusion, user-facing value,
confidence, scores, evidence snapshot, conflicts, gates) — from
already-stored rows only. Writes nothing by default (--dry-run);
--commit writes idempotently (a second --commit writes 0 new
rows). No HTTP fetch happens in this script; no forecast is
generated; no live execution exists anywhere in this project.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_decision_engine.py --dry-run
  python scripts/run_decision_engine.py --commit
  python scripts/run_decision_engine.py --commit --company HUBC

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
from app.services.decision_engine import runner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument("--commit", action="store_true", help="Actually write Phase 15 rows.")
    parser.add_argument("--company", default=None, help="Limit to one ticker (e.g. HUBC).")
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
        report = runner.run_decisions(
            session, commit=bool(args.commit), company_filter=args.company
        )
        if args.commit:
            session.commit()
    except Exception as exc:  # noqa: BLE001 - CLI reports and exits non-zero
        session.rollback()
        print(f"Decision run failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
    print(json.dumps(report, indent=2, default=str))
    summary = " | ".join(
        f"{d['ticker']}: screen={d['screening']} conclusion={d['conclusion']} "
        f"facing={d['user_facing']} conf={d['confidence']} "
        f"score={d['total_score']} ({d['scored_dimensions']} dims)"
        for d in report["decisions"]
    )
    print(
        "Decision run: "
        f"rules={report['rules_written']}/{report['rules_skipped']} "
        f"decisions={report['decisions_written']}/{report['decisions_skipped']} "
        f"outcomes_existing={report['outcomes_existing']} :: {summary}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
