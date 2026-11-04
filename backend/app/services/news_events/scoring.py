"""Impact scoring and review rules (Phase 11).

score = 0.4*reliability + 0.3*relevance + 0.2*novelty + 0.1*transmission.
All inputs are documented rule lookups, never sentiment and never a
price signal: a high score means "review-worthy and widely relevant",
never "buy". Review rules:
- confidence < 0.8, or the match is ambiguous -> pending_review.
- event date unknown -> pending_review (a date is never guessed).
- score >= 0.8 (high-impact) -> pending_review.
- future-dated macro calendar items -> scheduled (not yet occurred).
- otherwise -> ok.
"""

from __future__ import annotations

from datetime import date

from app.services.news_events import (
    NOVELTY,
    RELEVANCE,
    RELIABILITY,
    REVIEW_CONFIDENCE_THRESHOLD,
    REVIEW_SCORE_THRESHOLD,
    TRANSMISSION,
)


def score_event(
    source_type: str,
    scope: str,
    novelty: str,
    transmission: str,
) -> float:
    """Deterministic impact score in [0, 1]. Unknown keys raise."""
    reliability = RELIABILITY[source_type]
    relevance = RELEVANCE[scope]
    nov = NOVELTY[novelty]
    trans = TRANSMISSION[transmission]
    return round(0.4 * reliability + 0.3 * relevance + 0.2 * nov + 0.1 * trans, 4)


def review_status(
    *,
    confidence: float,
    ambiguous: bool,
    date_status: str,
    score: float,
    event_date: date | None,
    today: date,
) -> str:
    """Apply the review rules. 'scheduled' wins for future macro dates."""
    if event_date is not None and event_date > today:
        return "scheduled"
    if date_status == "unknown":
        return "pending_review"
    if ambiguous or confidence < REVIEW_CONFIDENCE_THRESHOLD:
        return "pending_review"
    if score >= REVIEW_SCORE_THRESHOLD:
        return "pending_review"
    return "ok"
