"""Phase 25 job handlers for the news jobs.

Handler contract: ``handle_*(ctx)`` takes a JobContext (session,
run, params, checkpoint) and returns a report dict. Handlers never
send email or messages, never trade, never spend money.

- handle_news_collection_daily: enforcement, not collection. For
  every source in the Phase 11 source registry whose policy blocks
  automated fetching, it records a refused collection run with the
  exact policy reason. It performs NO HTTP fetch for any source:
  no automated fetch is approved. A run that refuses everything is
  a successful run (the gate held), not a failure.
- handle_news_reconciliation_post_close: read-only reconciliation
  (stored articles vs Phase 11 events vs evidence links).
- handle_news_digest: read-only digest over stored PROCESSED /
  REVIEW articles. The digest is a run summary; nothing is sent.
"""

from __future__ import annotations

from sqlalchemy import text as _text

from app.services.news_intelligence import runner as news_runner


def _source_policies(session) -> list[tuple[str, str]]:
    rows = session.execute(
        _text("SELECT source_key, collection_policy FROM news_sources")
    ).all()
    return [(r[0], r[1]) for r in rows]


def handle_news_collection_daily(ctx) -> dict:
    """Enforce the collection gate for every registered source."""
    session = ctx.session
    refused: list[dict] = []
    allowed: list[str] = []
    for source_key, policy in _source_policies(session):
        result = news_runner.refuse_collection(session, source_key, policy)
        if result["refused"]:
            refused.append(
                {"source_key": source_key, "reason": result["reason"]}
            )
        else:
            allowed.append(source_key)
    session.commit()
    return {
        "sources_checked": len(refused) + len(allowed),
        "refused": refused,
        "allowed_but_not_fetched_here": allowed,
        "note": (
            "No automated fetch is approved for any source, so no "
            "collection was attempted. Refused runs are recorded in "
            "news_collection_runs as enforcement evidence."
        ),
    }


def handle_news_reconciliation_post_close(ctx) -> dict:
    """Read-only reconciliation of stored news rows."""
    return news_runner.reconcile(ctx.session)


def handle_news_digest(ctx) -> dict:
    """Read-only digest over stored articles. Sends nothing."""
    digest = news_runner.build_digest(ctx.session, limit=20)
    return {
        "digest_count": digest["count"],
        "articles": digest["articles"],
        "note": (
            "In-app digest only: this report is stored as a job run "
            "summary for the dashboard. No email or message is sent."
        ),
    }
