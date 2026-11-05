"""Phase 14 risk analytics CLI.

Builds the risk metric library, per-security/market risk values,
risk flags, versioned control rules and their checks, and stress
scenarios with results — from already-stored rows only. Writes
nothing by default (--dry-run); --commit writes idempotently (a
second --commit writes 0 new rows). No HTTP fetch happens in this
script; no live execution exists anywhere in this project.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_risk_analytics.py --dry-run
  python scripts/run_risk_analytics.py --commit
  python scripts/run_risk_analytics.py --commit --company HUBC

Exit codes: 0 ok; 1 operational failure; 2 bad arguments / missing
DATABASE_URL. The report is JSON on stdout; the summary line goes to
stderr so the JSON stays parseable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import build_engine
from app.services.risk_analytics import runner
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument(
        "--commit", action="store_true", help="Actually write Phase 14 rows."
    )
    parser.add_argument(
        "--company", default=None, help="Limit to one ticker (e.g. HUBC)."
    )
    parser.add_argument(
        "--as-of-date",
        default=None,
        help="ISO date (YYYY-MM-DD) for the model-risk section only "
        "(forecast_abstention_rate, technical_coverage_rate, "
        "input_drift). Writes NEW versioned rows for that date and "
        "preserves prior vintages; it never overwrites stored rows. "
        "Default: 2026-11-04 (the run's analysis date).",
    )
    args = parser.parse_args()
    model_as_of = None
    if args.as_of_date is not None:
        try:
            model_as_of = date.fromisoformat(args.as_of_date)
        except ValueError:
            print(
                f"--as-of-date must be an ISO date (YYYY-MM-DD), got {args.as_of_date!r}.",
                file=sys.stderr,
            )
            return 2
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
        report = runner.run_risk(
            session,
            commit=bool(args.commit),
            company_filter=args.company,
            model_as_of=model_as_of,
        )
        if args.commit:
            session.commit()
    except Exception as exc:  # noqa: BLE001 - CLI reports and exits non-zero
        session.rollback()
        print(f"Risk run failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
    print(json.dumps(report, indent=2, default=str))
    print(
        "Risk run: "
        f"definitions={report['definitions_written']}/{report['definitions_skipped']} "
        f"values={report['values_written']}/{report['values_skipped']} "
        f"computed={report['values_computed']} "
        f"insufficient={report['values_insufficient']} "
        f"flags={report['flags_written']}/{report['flags_skipped']} "
        f"checks={report['checks_written']} "
        f"(pass={report['checks_pass']} breach={report['checks_breach']} "
        f"blocked={report['checks_blocked']}) "
        f"stress={report['stress_written']}/{report['stress_skipped']} "
        f"computed={report['stress_computed']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
