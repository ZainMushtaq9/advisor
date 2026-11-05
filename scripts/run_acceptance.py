"""Phase 29 acceptance CLI: end-to-end integration, system acceptance
and independent audit.

Dry-run default (computes everything, writes nothing). --commit
stores one acceptance run (scenarios, recomputations, defects) in
a single transaction; a second --commit with the same --run-id
writes nothing.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_acceptance.py [--run-id ID] [--dry-run | --commit]

Exit codes: 0 ok; 1 operational failure; 2 bad arguments / missing
DATABASE_URL. The report is JSON on stdout; the summary line goes
to stderr so the JSON stays parseable.

This CLI never writes a business row, never promotes a status,
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
from app.services.acceptance.runner import DEFAULT_RUN_ID, accept
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True)
    group.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print(
            "DATABASE_URL is not set (source database/.env first).",
            file=sys.stderr,
        )
        return 2

    engine = build_engine(os.environ["DATABASE_URL"])
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        report = accept(session, run_id=args.run_id, commit=bool(args.commit))
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        print(f"acceptance failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()

    print(json.dumps(report, indent=2, default=str))
    if report.get("already_exists"):
        print(
            f"acceptance: run {args.run_id} already exists; 0 rows written.",
            file=sys.stderr,
        )
    elif report["committed"]:
        print(
            f"acceptance: committed run {args.run_id} verdict "
            f"{report['verdict']} "
            f"({report['scenarios_created']} scenarios, "
            f"{report['recomputations_created']} recomputations, "
            f"{report['defects_created']} defects).",
            file=sys.stderr,
        )
    else:
        print(
            f"acceptance: dry-run run {args.run_id} verdict "
            f"{report['verdict']} (nothing written).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
