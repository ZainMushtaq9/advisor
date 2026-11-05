"""Phase 19 RAG CLI.

Indexes the four permitted issuer PDFs (HBL added by the re-run batch), answers grounded
questions, runs the retrieval benchmark, and records the
access-control audit. Writes nothing by default (--dry-run);
--commit writes idempotently for index / answers / benchmark
results (access audits are a log: each audit run appends one
row per (role, document) pair).

No HTTP fetch happens in this script; no document body is ever
printed (only capped snippets plus page citations); no forecast
is generated; no live execution exists anywhere in this project.

Usage (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/run_rag.py --index --dry-run
  python scripts/run_rag.py --index --commit
  python scripts/run_rag.py --query "What was HUBC net profit for the year ended 30 June 2026?" --commit
  python scripts/run_rag.py --benchmark --commit
  python scripts/run_rag.py --access-audit --commit

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
from app.services.rag import runner
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; write nothing (default)."
    )
    mode.add_argument("--commit", action="store_true", help="Actually write Phase 19 rows.")
    parser.add_argument("--index", action="store_true", help="Index the seed issuer PDFs.")
    parser.add_argument("--query", type=str, default=None, help="Answer one grounded question.")
    parser.add_argument("--benchmark", action="store_true", help="Run the retrieval benchmark.")
    parser.add_argument("--access-audit", action="store_true", help="Record the access-control audit.")
    parser.add_argument("--role", type=str, default="internal", help="Caller role for query/benchmark.")
    parser.add_argument("--top-k", type=int, default=5, help="Retrieval top-k.")
    parser.add_argument("--run-id", type=str, default="phase19-benchmark-2026-11-04",
                        help="Benchmark run id (results dedupe on it).")
    args = parser.parse_args()
    if not (args.index or args.query or args.benchmark or args.access_audit):
        parser.error("Choose at least one of --index, --query, --benchmark, --access-audit.")
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
        report: dict = {"commit": bool(args.commit)}
        if args.index:
            report["index"] = runner.index_documents(session, commit=bool(args.commit))
        if args.query:
            report["answer"] = runner.answer_query(
                session, args.query, caller_role=args.role,
                top_k=args.top_k, commit=bool(args.commit),
            )
        if args.benchmark:
            report["benchmark"] = runner.run_benchmark(
                session, run_id=args.run_id, top_k=args.top_k,
                caller_role=args.role, commit=bool(args.commit),
            )
        if args.access_audit:
            report["access_audit"] = runner.run_access_audit(
                session, commit=bool(args.commit)
            )
    except Exception as exc:  # noqa: BLE001 - CLI reports and exits 1
        print(f"RAG run failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, default=str))
    print(
        "dry-run complete (nothing written)." if not args.commit else "commit complete.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
