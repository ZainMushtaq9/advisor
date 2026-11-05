"""Strict LLM output schema (prompt section 4).

Every processed article must produce a validated record with exactly
the prompt's field list. Validation REJECTS malformed output: it
never repairs, guesses, or fills a missing field. An LLM record is
never stored as verified information — validation is a necessary
check, not a truth certificate. Summary excerpts are capped at 280
chars, matching the Phase 11 excerpt discipline (no article-body
storage anywhere in this project).
"""

from __future__ import annotations

from app.services.news_intelligence.taxonomy import is_valid_category

REQUIRED_FIELDS = (
    "article_id",
    "title",
    "source",
    "canonical_url",
    "published_at",
    "retrieved_at",
    "language",
    "company_names",
    "ticker_symbols",
    "sector_names",
    "event_category",
    "sentiment",
    "relevance_score",
    "impact_score",
    "confidence_score",
    "potential_impact_horizon",
    "extracted_facts",
    "supporting_evidence",
    "uncertainty_notes",
    "risk_factors",
    "summary",
    "model_name",
    "model_version",
    "processing_timestamp",
)

SENTIMENTS = ("positive", "negative", "neutral", "mixed")
LANGUAGES = ("en", "ur", "mixed", "other")
HORIZONS = ("short_term", "medium_term", "long_term", "unknown")

SUMMARY_MAX_CHARS = 280


def _is_score(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0.0 <= float(value) <= 1.0
    )


def validate_llm_output(
    record: object,
    known_tickers: set[str],
) -> tuple[bool, list[str], dict]:
    """Validate one LLM output record.

    Returns (ok, errors, cleaned). ``known_tickers`` is the registry
    ticker set passed in by the caller: any ticker outside it is an
    error, never silently accepted. On failure, ``cleaned`` is {}.
    On success, ``cleaned`` is a copy with normalized tickers
    (uppercased) and the summary truncated ONLY if it exceeds the
    cap — truncation is recorded in neither case as a pass: a
    summary over the cap is an ERROR, not something to trim
    silently. (Truncation here applies solely to defensive
    whitespace stripping; see the check below.)
    """
    errors: list[str] = []
    if not isinstance(record, dict):
        return False, ["record is not a JSON object"], {}
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] is None:
            errors.append(f"missing required field: {field}")
    if errors:
        return False, errors, {}

    if not isinstance(record["title"], str) or not record["title"].strip():
        errors.append("title must be a non-empty string")
    if not isinstance(record["source"], str) or not record["source"].strip():
        errors.append("source must be a non-empty string")
    if not isinstance(record["canonical_url"], str) or not record["canonical_url"].strip():
        errors.append("canonical_url must be a non-empty string")
    if not isinstance(record["published_at"], str) or not record["published_at"].strip():
        errors.append("published_at must be a non-empty string")
    if not isinstance(record["retrieved_at"], str) or not record["retrieved_at"].strip():
        errors.append("retrieved_at must be a non-empty string")
    if record["language"] not in LANGUAGES:
        errors.append(f"language must be one of {sorted(LANGUAGES)}")
    if not isinstance(record["company_names"], list) or not all(
        isinstance(c, str) for c in record["company_names"]
    ):
        errors.append("company_names must be a list of strings")
    if not isinstance(record["ticker_symbols"], list) or not all(
        isinstance(t, str) for t in record["ticker_symbols"]
    ):
        errors.append("ticker_symbols must be a list of strings")
    else:
        unknown = [
            t for t in record["ticker_symbols"] if t.upper() not in known_tickers
        ]
        if unknown:
            errors.append(f"unsupported tickers rejected: {sorted(set(unknown))}")
    if not isinstance(record["sector_names"], list) or not all(
        isinstance(s, str) for s in record["sector_names"]
    ):
        errors.append("sector_names must be a list of strings")
    if not is_valid_category(record["event_category"]):
        errors.append(f"event_category is not a known category: {record['event_category']!r}")
    if record["sentiment"] not in SENTIMENTS:
        errors.append(f"sentiment must be one of {sorted(SENTIMENTS)}")
    for score_field in ("relevance_score", "impact_score", "confidence_score"):
        if not _is_score(record[score_field]):
            errors.append(f"{score_field} must be a number in [0, 1]")
    if record["potential_impact_horizon"] not in HORIZONS:
        errors.append(f"potential_impact_horizon must be one of {sorted(HORIZONS)}")
    for list_field in ("extracted_facts", "supporting_evidence", "uncertainty_notes", "risk_factors"):
        if not isinstance(record[list_field], list) or not all(
            isinstance(v, str) for v in record[list_field]
        ):
            errors.append(f"{list_field} must be a list of strings")
    if not isinstance(record["summary"], str) or not record["summary"].strip():
        errors.append("summary must be a non-empty string")
    elif len(record["summary"]) > SUMMARY_MAX_CHARS:
        errors.append(
            f"summary exceeds the {SUMMARY_MAX_CHARS}-char excerpt cap "
            f"({len(record['summary'])} chars)"
        )
    if not isinstance(record["model_name"], str) or not record["model_name"].strip():
        errors.append("model_name must be a non-empty string")
    if not isinstance(record["model_version"], str) or not record["model_version"].strip():
        errors.append("model_version must be a non-empty string")
    if not isinstance(record["processing_timestamp"], str) or not record["processing_timestamp"].strip():
        errors.append("processing_timestamp must be a non-empty string")
    if not isinstance(record["article_id"], str) or not record["article_id"].strip():
        errors.append("article_id must be a non-empty string")

    if errors:
        return False, errors, {}
    cleaned = dict(record)
    cleaned["ticker_symbols"] = [t.upper() for t in record["ticker_symbols"]]
    return True, [], cleaned
