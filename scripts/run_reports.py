"""Phase 22 report generation CLI.

Generates the 22 seed reports (8 templates: company dossier,
earnings update, valuation report, sector outlook, event
brief, portfolio review, risk report, market overview) from
already-stored rows only. Writes nothing by default
(--dry-run); --commit writes idempotently (templates by
(template_key, version); reports by (template_key,
subject_key, report_date, data_cutoff_date,
template_version) among current rows; a second --commit
reuses existing reports and writes nothing new).

Lifecycle actions (--approve, --reject) act on one report id
each and always write: they are operator actions, not
generation runs. They refuse invalid transitions and unknown
ids with exit code 1. APPROVED means internally reviewed
only: there is no publish step and no external send anywhere
in this project, so an APPROVED report is still internal.

No HTTP fetch happens in this script; no new market data is
collected; no price, ratio, forecast, or recommendation is
generated; no external message is ever sent; no live
execution exists anywhere in this project. Reports assemble
stored figures only, and every figure inherits its inputs'
quality status.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_reports.py --dry-run
  python scripts/run_reports.py --commit
  python scripts/run_reports.py --template company_dossier --commit
  python scripts/run_reports.py --template event_brief --subject "news:HUBC:earning" --commit
  python scripts/run_reports.py --list
  python scripts/run_reports.py --approve 12
  python scripts/run_reports.py --reject 12

Exit codes: 0 ok; 1 operational failure (including invalid
lifecycle transitions); 2 bad arguments / missing DATABASE_URL.
The report is JSON on stdout; the summary line goes to stderr
so the JSON stays parseable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import build_engine
from app.services.reports import runner as reports_runner
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument(
        "--commit", action="store_true", help="Actually write Phase 22 rows."
    )
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="Generate one template key only (default: all seed reports).",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default=None,
        help="Generate one subject key only (default: all seed reports).",
    )
    parser.add_argument("--list", action="store_true", help="List current reports.")
    parser.add_argument(
        "--approve", type=int, default=None, help="Approve one report id."
    )
    parser.add_argument(
        "--reject", type=int, default=None, help="Reject one report id."
    )
    args = parser.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL is not set (source database/.env first).", file=sys.stderr)
        return 2

    engine = build_engine(os.environ["DATABASE_URL"])
    session = sessionmaker(bind=engine)()
    try:
        if args.approve is not None:
            result = reports_runner.approve(session, args.approve)
            if "error" in result:
                print(result["error"], file=sys.stderr)
                return 1
            print(json.dumps(result, indent=2, default=str))
            print(f"report {args.approve}: APPROVED", file=sys.stderr)
            return 0
        if args.reject is not None:
            result = reports_runner.reject(session, args.reject)
            if "error" in result:
                print(result["error"], file=sys.stderr)
                return 1
            print(json.dumps(result, indent=2, default=str))
            print(f"report {args.reject}: REJECTED", file=sys.stderr)
            return 0
        if args.list:
            rows = reports_runner.list_reports(session)
            print(json.dumps({"reports": rows}, indent=2, default=str))
            print(f"listed {len(rows)} current reports", file=sys.stderr)
            return 0
        result = reports_runner.generate(
            session,
            template_key=args.template,
            subject_key=args.subject,
            commit=bool(args.commit),
        )
        print(json.dumps(result, indent=2, default=str))
        generated = result.get("generated", [])
        created = sum(1 for g in generated if g["status"] == "created")
        skipped = sum(1 for g in generated if g["status"] == "skipped_existing")
        would = sum(1 for g in generated if g["status"] == "would_write")
        failed = sum(
            1 for g in generated if g["status"] in ("build_failed", "qa_failed")
        )
        print(
            f"reports: {len(generated)} evaluated, {created} created, "
            f"{skipped} skipped_existing, {would} would_write, {failed} failed",
            file=sys.stderr,
        )
        return 1 if failed else 0
    except Exception as exc:  # noqa: BLE001 - CLI reports, never hides
        print(f"run_reports failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
