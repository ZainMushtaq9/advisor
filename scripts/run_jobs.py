"""Phase 25 job automation CLI.

Single-pass, operator-invoked, sequential. There is no
resident daemon and no hosted scheduler: the operator (or
a host cron) runs ``run-due``, which does one pass and
exits. Paused jobs are never executed (the market,
filing and macro collection jobs are paused: Terms-gated
or polling-not-approved — see docs/phase-25/job_registry.md).
Manual runs are idempotent only with --run-tag; without
one, each invocation is a distinct run.

Retention purge is dry-run by default: it reports auth
audit-log rows older than 12 months and deletes nothing.
Re-run with --confirm to delete. Job tables are never
purged: they are the recovery evidence itself.

No HTTP fetch happens in this script; no new market data
is collected; no message is sent; no report is published;
no quality status is promoted; no live execution exists
anywhere in this project.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_jobs.py register
  python scripts/run_jobs.py list
  python scripts/run_jobs.py due [--today YYYY-MM-DD]
  python scripts/run_jobs.py run-due [--today YYYY-MM-DD]
  python scripts/run_jobs.py run-one <job_key> [--date YYYY-MM-DD] [--run-tag TAG]
  python scripts/run_jobs.py cancel <run_id>
  python scripts/run_jobs.py retry-dead <dead_letter_id>
  python scripts/run_jobs.py status
  python scripts/run_jobs.py purge [--confirm]

Exit codes: 0 ok; 1 operational failure (unknown job/run,
paused job, invalid transition); 2 bad arguments / missing
DATABASE_URL. The report is JSON on stdout; the summary
line goes to stderr so the JSON stays parseable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import build_engine
from app.services.jobs import calendar as cal
from app.services.jobs import runner as jobs_runner
from sqlalchemy.orm import sessionmaker


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("register", help="Seed the job registry (idempotent).")
    sub.add_parser("list", help="List registered job definitions.")
    due_p = sub.add_parser("due", help="Show due occurrences; run nothing.")
    due_p.add_argument("--today", default=None, help="YYYY-MM-DD (default: today PKT).")
    run_due_p = sub.add_parser("run-due", help="One pass: reclaim, materialise, execute.")
    run_due_p.add_argument("--today", default=None, help="YYYY-MM-DD (default: today PKT).")
    run_one_p = sub.add_parser("run-one", help="Execute one job explicitly.")
    run_one_p.add_argument("job_key")
    run_one_p.add_argument("--date", default=None, help="Scheduled occurrence YYYY-MM-DD.")
    run_one_p.add_argument("--run-tag", default=None, help="Idempotency tag for manual runs.")
    run_one_p.add_argument("--confirm", action="store_true", help="Confirm retention purge.")
    cancel_p = sub.add_parser("cancel", help="Cancel a queued/blocked run.")
    cancel_p.add_argument("run_id", type=int)
    retry_p = sub.add_parser("retry-dead", help="Re-queue a dead letter.")
    retry_p.add_argument("dead_letter_id", type=int)
    sub.add_parser("status", help="Operations status.")
    purge_p = sub.add_parser("purge", help="Retention purge (dry-run unless --confirm).")
    purge_p.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL is not set (source database/.env first).", file=sys.stderr)
        return 2

    engine = build_engine(os.environ["DATABASE_URL"])
    session = sessionmaker(bind=engine)()
    try:
        if args.command == "register":
            result = jobs_runner.register_definitions(session)
            print(json.dumps(result, indent=2, default=str))
            print(
                f"registry: {len(result['inserted'])} inserted, {len(result['updated'])} updated",
                file=sys.stderr,
            )
            return 0
        if args.command == "list":
            from app.models.jobs import JobDefinition

            rows = (
                session.query(JobDefinition)
                .order_by(JobDefinition.priority, JobDefinition.job_key)
                .all()
            )
            print(
                json.dumps(
                    {
                        "definitions": [
                            {
                                "job_key": r.job_key,
                                "title": r.title,
                                "schedule_kind": r.schedule_kind,
                                "schedule_spec": r.schedule_spec,
                                "status": r.status,
                                "pause_reason": r.pause_reason,
                            }
                            for r in rows
                        ]
                    },
                    indent=2,
                    default=str,
                )
            )
            return 0
        if args.command == "due":
            today = _parse_date(args.today) or cal.today_pkt()
            due = jobs_runner.compute_due(session, today)
            print(
                json.dumps(
                    {"today": today.isoformat(), "due": due},
                    indent=2,
                    default=str,
                )
            )
            print(f"due: {len(due)} occurrences", file=sys.stderr)
            return 0
        if args.command == "run-due":
            today = _parse_date(args.today) or cal.today_pkt()
            result = jobs_runner.run_due(session, today)
            print(json.dumps(result, indent=2, default=str))
            executed = result.get("executed", [])
            succeeded = sum(1 for e in executed if e.get("status") == "succeeded")
            print(
                f"run-due: {len(result['materialised']['created'])} created, "
                f"{len(executed)} executed, {succeeded} succeeded",
                file=sys.stderr,
            )
            return 0
        if args.command == "run-one":
            params = {}
            if args.job_key == "retention_purge":
                params["confirm"] = bool(args.confirm)
            result = jobs_runner.run_one(
                session,
                args.job_key,
                scheduled_for=_parse_date(args.date),
                run_tag=args.run_tag,
                params=params,
            )
            print(json.dumps(result, indent=2, default=str))
            if "error" in result:
                print(result["error"], file=sys.stderr)
                return 1
            return 0
        if args.command == "cancel":
            result = jobs_runner.cancel_run(session, args.run_id)
            print(json.dumps(result, indent=2, default=str))
            if "error" in result:
                print(result["error"], file=sys.stderr)
                return 1
            return 0
        if args.command == "retry-dead":
            result = jobs_runner.retry_dead_letter(session, args.dead_letter_id)
            print(json.dumps(result, indent=2, default=str))
            if "error" in result:
                print(result["error"], file=sys.stderr)
                return 1
            return 0
        if args.command == "status":
            result = jobs_runner.status(session)
            print(json.dumps(result, indent=2, default=str))
            return 0
        if args.command == "purge":
            result = jobs_runner.run_one(
                session,
                "retention_purge",
                run_tag="cli",
                params={"confirm": bool(args.confirm)},
            )
            print(json.dumps(result, indent=2, default=str))
            if "error" in result:
                print(result["error"], file=sys.stderr)
                return 1
            return 0
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI reports, never hides
        print(f"run_jobs failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
