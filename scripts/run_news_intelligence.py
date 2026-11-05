"""News Intelligence Engine CLI (dry-run default, --commit writes).

Usage (DATABASE_URL must be set, e.g. from database/.env):

  # Process article dicts from a JSONL file (one dict per line;
  # shape: {article_id, title, source, canonical_url, published_at,
  # retrieved_at, language?, text, source_key?, _credibility_class?}).
  # "text" is headline + excerpt only: never a full article body.
  python scripts/run_news_intelligence.py process --input items.jsonl
  python scripts/run_news_intelligence.py process --input items.jsonl --commit

  # Record refused collection runs for every registered source whose
  # policy blocks automated fetching (enforcement evidence; no fetch).
  python scripts/run_news_intelligence.py enforce --commit

  # Read-only digest over stored PROCESSED / REVIEW articles.
  python scripts/run_news_intelligence.py digest

  # Read-only reconciliation (articles vs events vs evidence links).
  python scripts/run_news_intelligence.py reconcile

  # Compute + store market reactions for stored Phase 11 events
  # (INSUFFICIENT_DATA rows included: the status is the finding).
  python scripts/run_news_intelligence.py reactions --commit

  # Read-only source quality: registered sources, their policies,
  # and collection-run history.
  python scripts/run_news_intelligence.py quality

The report is JSON on stdout. Nothing is written unless --commit
is passed, except the read-only commands, which never write.
Processing uses the deterministic fallback (RULE_BASED) unless
--ollama-model is given AND a local Ollama server answers; a model
that cannot be reached yields UNPROCESSED/fallback rows, never fake
LLM output. No paid API is ever called by this script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import text as _text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import build_engine  # noqa: E402
from app.services.news_intelligence import runner as news_runner  # noqa: E402


def _session():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set; refusing to run.", file=sys.stderr)
        sys.exit(2)
    engine = build_engine(database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def _cmd_process(args) -> int:
    items = []
    with open(args.input, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    adapter = None
    if args.ollama_model:
        from app.services.news_intelligence.llm_adapter import OllamaAdapter

        adapter = OllamaAdapter(model=args.ollama_model)
    session = _session()
    try:
        report = news_runner.run_processing(
            session, items, adapter=adapter, commit=args.commit
        )
    finally:
        session.close()
    report["mode"] = "commit" if args.commit else "dry-run"
    print(json.dumps(report, indent=2, default=str))
    return 0


def _cmd_enforce(args) -> int:
    session = _session()
    try:
        rows = session.execute(
            _text("SELECT source_key, collection_policy FROM news_sources")
        ).all()
        refused = []
        for source_key, policy in rows:
            result = news_runner.refuse_collection(session, source_key, policy)
            if result["refused"]:
                refused.append(result)
        if args.commit:
            session.commit()
        else:
            session.rollback()
    finally:
        session.close()
    print(
        json.dumps(
            {
                "sources_checked": len(rows),
                "refused": refused,
                "mode": "commit" if args.commit else "dry-run",
                "note": "Refused runs are enforcement evidence. No fetch was attempted.",
            },
            indent=2,
            default=str,
        )
    )
    return 0


def _cmd_digest(_args) -> int:
    session = _session()
    try:
        print(json.dumps(news_runner.build_digest(session), indent=2, default=str))
    finally:
        session.close()
    return 0


def _cmd_reconcile(_args) -> int:
    session = _session()
    try:
        print(json.dumps(news_runner.reconcile(session), indent=2, default=str))
    finally:
        session.close()
    return 0


def _cmd_reactions(args) -> int:
    session = _session()
    try:
        report = news_runner.compute_event_reactions(session, commit=args.commit)
    finally:
        session.close()
    report["mode"] = "commit" if args.commit else "dry-run"
    print(json.dumps(report, indent=2, default=str))
    return 0


def _cmd_quality(_args) -> int:
    session = _session()
    try:
        sources = session.execute(
            _text(
                "SELECT source_key, name, source_type, collection_policy, "
                "collection_status, terms_note FROM news_sources "
                "ORDER BY source_key"
            )
        ).all()
        runs = session.execute(
            _text(
                "SELECT source_key, status, COUNT(*), MAX(created_at) "
                "FROM news_collection_runs GROUP BY source_key, status "
                "ORDER BY source_key, status"
            )
        ).all()
    finally:
        session.close()
    print(
        json.dumps(
            {
                "sources": [
                    {
                        "source_key": r[0],
                        "name": r[1],
                        "source_type": r[2],
                        "collection_policy": r[3],
                        "collection_status": r[4],
                        "terms_note": r[5],
                    }
                    for r in sources
                ],
                "collection_runs": [
                    {
                        "source_key": r[0],
                        "status": r[1],
                        "count": int(r[2]),
                        "last_run": str(r[3]) if r[3] else None,
                    }
                    for r in runs
                ],
            },
            indent=2,
            default=str,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("process", help="Process article dicts from a JSONL file.")
    p.add_argument("--input", required=True, help="JSONL file of article dicts.")
    p.add_argument("--commit", action="store_true", help="Actually write.")
    p.add_argument(
        "--ollama-model",
        default=None,
        help="Local Ollama model to try (unreachable -> fallback, never faked).",
    )
    e = sub.add_parser(
        "enforce", help="Record refused runs for policy-blocked sources."
    )
    e.add_argument("--commit", action="store_true", help="Actually write.")
    sub.add_parser("digest", help="Read-only digest over stored articles.")
    sub.add_parser("reconcile", help="Read-only article/event reconciliation.")
    r = sub.add_parser(
        "reactions", help="Compute + store reactions for Phase 11 events."
    )
    r.add_argument("--commit", action="store_true", help="Actually write.")
    sub.add_parser("quality", help="Read-only source quality + run history.")
    args = parser.parse_args(argv)
    if args.command == "process":
        return _cmd_process(args)
    if args.command == "enforce":
        return _cmd_enforce(args)
    if args.command == "digest":
        return _cmd_digest(args)
    if args.command == "reconcile":
        return _cmd_reconcile(args)
    if args.command == "reactions":
        return _cmd_reactions(args)
    if args.command == "quality":
        return _cmd_quality(args)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
