"""News RAG retrieval: deterministic full-text fallback.

Mirrors the Phase 19 retrieval contract (token scoring, phrase
bonus, ticker bonus, metadata filters before scoring, capped
snippets, one result per document) over stored news articles and
events. The capability is labelled FULL_TEXT_FALLBACK everywhere
it is served: vector retrieval is REGISTERED BUT NOT
IMPLEMENTED (no verified local embedding model), and this module
never claims a vector score.

Citations are (title, source, canonical_url, published_at) —
never a full article body, never an invented source.
"""

from __future__ import annotations

import re

from app.services.news_events.aliases import normalize

STOPWORDS = frozenset(
    {
        "a", "an", "the", "and", "or", "of", "to", "in", "on", "for",
        "was", "were", "is", "are", "what", "which", "with", "by",
    }
)

SNIPPET_MAX_CHARS = 500
RETRIEVAL_METHOD = "FULL_TEXT_FALLBACK"


def _tokens(text: str) -> list[str]:
    tokens = re.split(r"[^A-Za-z0-9]+", normalize(text).lower())
    return [t for t in tokens if t and t not in STOPWORDS]


def _snippet(text: str, query_tokens: list[str]) -> str:
    """Snippet centred on the first matched query token, capped
    at 500 chars (same contract as Phase 19)."""
    lowered = text.lower()
    first = len(text)
    for token in query_tokens:
        idx = lowered.find(token)
        if 0 <= idx < first:
            first = idx
    if first == len(text):
        return text[:SNIPPET_MAX_CHARS]
    start = max(0, first - 100)
    return text[start : start + SNIPPET_MAX_CHARS]


def search_news(
    documents: list[dict],
    query: str,
    ticker: str | None = None,
    sector: str | None = None,
    event_category: str | None = None,
    limit: int = 10,
) -> dict:
    """Search stored news documents.

    ``documents``: [{id, title, summary, source, canonical_url,
    published_at (ISO str or None), tickers: [str],
    sectors: [str], event_category: str}]. Metadata filters apply
    BEFORE scoring. Score = 2.0 per distinct query token present
    + 5.0 exact-phrase bonus + 3.0 ticker bonus (a queried ticker
    matching the document's tickers). The ticker bonus applies ONLY
    when the document already has token or phrase overlap: a
    ticker match alone must not return a document that says
    nothing about the query (a ticker-filtered search for
    "dividend" must not return an unrelated gas discovery just
    because its ticker matched). Zero-score documents are never
    returned. One result per document id (documents are already
    unique here; the rule is stated for parity with Phase 19's
    per-page dedup).
    """
    query_tokens = _tokens(query)
    normalized_query = normalize(query).lower()
    results = []
    for doc in documents:
        if ticker and ticker.upper() not in [t.upper() for t in doc.get("tickers", [])]:
            continue
        if sector and sector not in doc.get("sectors", []):
            continue
        if event_category and event_category != doc.get("event_category"):
            continue
        haystack = f"{doc.get('title', '')} {doc.get('summary', '')}"
        hay_tokens = set(_tokens(haystack))
        score = 0.0
        for token in set(query_tokens):
            if token in hay_tokens:
                score += 2.0
        if normalized_query and normalized_query in normalize(haystack).lower():
            score += 5.0
        if (
            score > 0
            and ticker
            and ticker.upper() in [t.upper() for t in doc.get("tickers", [])]
        ):
            score += 3.0
        if score <= 0:
            continue
        results.append(
            {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "source": doc.get("source"),
                "canonical_url": doc.get("canonical_url"),
                "published_at": doc.get("published_at"),
                "tickers": doc.get("tickers", []),
                "event_category": doc.get("event_category"),
                "score": round(score, 4),
                "snippet": _snippet(haystack, query_tokens),
                "retrieval_method": RETRIEVAL_METHOD,
            }
        )
    results.sort(key=lambda r: (-r["score"], str(r["id"])))
    return {
        "retrieval_method": RETRIEVAL_METHOD,
        "results": results[:limit],
        "note": (
            "Deterministic full-text retrieval. Vector retrieval is "
            "registered but not implemented (no verified local "
            "embedding model); no vector score is claimed."
        ),
    }
