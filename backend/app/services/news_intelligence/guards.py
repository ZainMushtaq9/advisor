"""Hallucination safeguards.

Validation (schema.py) proves shape. These guards prove grounding:
an extracted fact must share vocabulary with the source text, a
ticker must come from the registry, and a source must come from the
permission register. Anything ungrounded is flagged, never stored
as verified information. Confidence is capped by the weakest
evidence: an ambiguous entity match caps confidence at 0.50 and
forces review, exactly as Phase 11 scoring does.
"""

from __future__ import annotations

import re

STOPWORDS = frozenset(
    {
        "the", "and", "for", "with", "from", "that", "this", "will",
        "has", "have", "been", "were", "are", "was", "its", "per",
        "pakistan", "company", "limited", "ltd",
    }
)

AMBIGUOUS_CONFIDENCE_CAP = 0.50
REVIEW_CONFIDENCE_THRESHOLD = 0.80


def _significant_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9]{4,}", text.lower())
    return {t for t in tokens if t not in STOPWORDS}


def grounding_check(fact: str, source_text: str) -> bool:
    """True if the fact shares at least one significant token with
    the source text. A fact sharing nothing is ungrounded: it may
    be model invention, and must be flagged, never trusted. Numbers
    alone do not ground a fact (a wrong figure can share digits
    with a right one); token overlap is a necessary check, not a
    truth certificate, and the result is labelled as such."""
    fact_tokens = _significant_tokens(fact)
    if not fact_tokens:
        return False
    source_tokens = _significant_tokens(source_text)
    return len(fact_tokens & source_tokens) > 0


def check_record_grounding(record: dict, source_text: str) -> list[str]:
    """Return a list of ungrounded extracted facts (empty = all
    grounded). An empty source text grounds nothing."""
    ungrounded = []
    for fact in record.get("extracted_facts", []):
        if not grounding_check(fact, source_text):
            ungrounded.append(fact)
    return ungrounded


def cap_confidence(
    confidence: float,
    ambiguous: bool,
    validation_passed: bool,
) -> tuple[float, bool]:
    """Apply the confidence caps. Returns (capped, force_review).

    Ambiguous entity matches cap at 0.50 (Phase 11 rule). Failed
    validation caps at 0.50 as well — a record that failed
    validation is never stored anyway; the cap exists so a
    partially-validated pipeline can never present a high
    confidence. Anything below 0.80 forces review.
    """
    capped = float(confidence)
    if ambiguous:
        capped = min(capped, AMBIGUOUS_CONFIDENCE_CAP)
    if not validation_passed:
        capped = min(capped, AMBIGUOUS_CONFIDENCE_CAP)
    force_review = capped < REVIEW_CONFIDENCE_THRESHOLD
    return capped, force_review


def check_tickers(tickers: list[str], known_tickers: set[str]) -> list[str]:
    """Tickers outside the registry set. Empty = all supported."""
    return [t for t in tickers if t.upper() not in known_tickers]


def check_source(source_key: str, permitted_keys: set[str]) -> bool:
    """True if the source key is in the permission register's
    permitted set. An unregistered source is never accepted."""
    return source_key in permitted_keys
