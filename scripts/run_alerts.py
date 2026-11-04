"""Phase 21 alerts CLI.

Seeds the nine v1 alert rules and the local preference profile,
evaluates the rules over stored rows, creates deduplicated
alerts, and delivers them in-app only. Writes nothing by
default (--dry-run); --commit writes idempotently (rules by
(rule_key, version); preferences by profile; alerts by
dedup_key; deliveries skipped once DELIVERED; runs keyed by
(rule, as-of date, processing time)).

Lifecycle actions (--acknowledge, --mute, --resolve, --unmute)
act on one alert id each and always write: they are operator
actions, not evaluation runs. They refuse invalid transitions
and unknown ids with exit code 1.

No HTTP fetch happens in this script; no price, ratio,
forecast, or recommendation is generated; no external message
is ever sent; no live execution exists anywhere in this
project. Alerts notify about stored events only.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_alerts.py --dry-run
  python scripts/run_alerts.py --commit
  python scripts/run_alerts.py --rule high_volume --commit
  python scripts/run_alerts.py --acknowledge 12
  python scripts/run_alerts.py --mute 12 --until 2026-11-20
  python scripts/run_alerts.py --resolve 12
  python scripts/run_alerts.py --unmute 12

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
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import build_engine
from app.services.alerts import SEED_RULES
from app.services.alerts import runner as alerts_runner
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument(
        "--commit", action="store_true", help="Actually write Phase 21 rows."
    )
    parser.add_argument(
        "--rule",
        type=str,
        default=None,
        help="Evaluate one seed rule by rule_key (default: all).",
    )
    parser.add_argument(
        "--acknowledge", type=int, default=None, help="Acknowledge one alert id."
    )
    parser.add_argument("--mute", type=int, default=None, help="Mute one alert id.")
    parser.add_argument(
        "--until",
        type=str,
        default=None,
        help="Mute-until date (YYYY-MM-DD) for --mute.",
    )
    parser.add_argument(
        "--resolve", type=int, default=None, help="Resolve one alert id."
    )
    parser.add_argument("--unmute", type=int, default=None, help="Unmute one alert id.")
    args = parser.parse_args()
    commit = bool(args.commit)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2
    engine = build_engine(database_url)
    session = sessionmaker(bind=engine)()
    try:
        lifecycle = [
            (args.acknowledge, "acknowledge"),
            (args.mute, "mute"),
            (args.resolve, "resolve"),
            (args.unmute, "unmute"),
        ]
        chosen = [
            (alert_id, action) for alert_id, action in lifecycle if alert_id is not None
        ]
        if chosen:
            if len(chosen) > 1:
                print("Pass exactly one lifecycle action.", file=sys.stderr)
                return 2
            alert_id, action = chosen[0]
            muted_until = None
            if action == "mute":
                if args.until is None:
                    print("--mute requires --until YYYY-MM-DD.", file=sys.stderr)
                    return 2
                try:
                    muted_until = date.fromisoformat(args.until)
                except ValueError:
                    print(f"Bad --until date: {args.until}", file=sys.stderr)
                    return 2
            try:
                result = alerts_runner.apply_lifecycle(
                    session, alert_id, action, muted_until=muted_until
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            print(json.dumps(result, indent=2, default=str))
            return 0
        seeded = alerts_runner.seed_rules(session, commit=commit)
        rules = SEED_RULES
        if args.rule:
            rules = [r for r in SEED_RULES if r["rule_key"] == args.rule]
            if not rules:
                print(f"Unknown rule: {args.rule}", file=sys.stderr)
                return 2
        runs = [alerts_runner.run_rule(session, r, commit=commit) for r in rules]
        report = {"seeded": seeded, "runs": runs, "committed": commit}
        print(json.dumps(report, indent=2, default=str))
        total_created = sum(r["created"] for r in runs)
        total_delivered = sum(r["delivered"] for r in runs)
        if commit:
            print(
                f"Alerts: {len(runs)} rules, {total_created} alerts created, "
                f"{total_delivered} in-app deliveries.",
                file=sys.stderr,
            )
        else:
            print(
                f"Alerts dry-run: {len(runs)} rules, {total_created} alerts would be "
                f"created, {total_delivered} in-app deliveries projected.",
                file=sys.stderr,
            )
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
