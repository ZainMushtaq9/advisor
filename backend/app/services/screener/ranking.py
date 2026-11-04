"""Phase 20 explainable ranking, sorting, and pagination.

Score version "screener-score-v1": score = passed / scored,
where scored counts only pass/fail outcomes. Missing and
not_applicable outcomes are excluded from both numerator and
denominator — they are reported, never scored as zero.

Outcome rule: MATCH when scored >= 1 and passed == scored;
NO_MATCH when scored >= 1 and passed < scored;
INSUFFICIENT_DATA when scored == 0. A screen match is a
filter result, not an opportunity, recommendation, or
forecast — that disclaimer is attached by the API and CLI,
not hidden in a footnote.

Pagination is validated, never silently clamped: limit must
be 1..100 and offset >= 0, else ValueError. Sorting is by
score descending (NULL scores last) then ticker ascending,
or by ticker ascending when requested. No arbitrary sort
keys and no user SQL exist anywhere in this module.
"""

from __future__ import annotations

from decimal import Decimal

MAX_LIMIT = 100


def score_outcomes(filter_outcomes: list[dict]) -> dict:
    """Aggregate per-filter outcomes into a scored result."""
    passed = sum(1 for o in filter_outcomes if o["outcome"] == "pass")
    scored = sum(1 for o in filter_outcomes if o["outcome"] in ("pass", "fail"))
    if scored == 0:
        outcome = "INSUFFICIENT_DATA"
        score = None
    elif passed == scored:
        outcome = "MATCH"
        score = Decimal(passed) / Decimal(scored)
    else:
        outcome = "NO_MATCH"
        score = Decimal(passed) / Decimal(scored)
    reason_codes = sorted({o["reason"] for o in filter_outcomes})
    return {
        "outcome": outcome,
        "score": score,
        "passed_count": passed,
        "scored_count": scored,
        "reason_codes": reason_codes,
    }


def sort_results(results: list[dict], sort: str = "score") -> list[dict]:
    """Sort screen results. "score": score desc (NULL last),
    then ticker asc. "ticker": ticker asc. Anything else
    raises ValueError."""
    if sort == "ticker":
        return sorted(results, key=lambda r: r["ticker"])
    if sort == "score":
        # -score on Decimal works; None scores sort last via
        # the leading 1 in the tuple.
        return sorted(
            results,
            key=lambda r: (
                (1, r["ticker"]) if r.get("score") is None else (0, -r["score"], r["ticker"])
            ),
        )
    raise ValueError(f"Unknown sort: {sort!r}")


def paginate(items: list, limit: int, offset: int) -> tuple[list, dict]:
    """Validate and apply pagination. Raises ValueError on an
    out-of-range limit or a negative offset."""
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit must be an integer in 1..{MAX_LIMIT}")
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    page = items[offset : offset + limit]
    return page, {
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "returned": len(page),
    }
