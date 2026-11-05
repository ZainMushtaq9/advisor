"""Article -> validated intelligence record pipeline.

Order of operations (each step can reject, none can invent):
1. Resolve entities with the Phase 11 deterministic resolver
   (exact alias/ticker matches only; ambiguous capped + review).
2. Classify + sentiment: LLM adapter if one is configured and
   reachable, else the deterministic fallback (labelled
   RULE_BASED). An LLM reply is validated with the strict schema;
   a malformed reply is rejected, never repaired.
3. Grounding check: every extracted fact must share vocabulary
   with the input text, or it is listed ungrounded and the record
   is forced to review.
4. Confidence capping (guards): ambiguous or unvalidated input
   caps confidence at 0.50; below 0.80 forces review.

The pipeline never writes to the database itself; the runner
decides persistence. Processing status values: PROCESSED,
REVIEW (processed but flagged), REJECTED (schema/grounding
failure), UNPROCESSED (no model available).
"""

from __future__ import annotations

from app.services.news_intelligence import guards
from app.services.news_intelligence.llm_adapter import (
    DeterministicFallback,
    ModelUnavailable,
)
from app.services.news_intelligence.schema import validate_llm_output


def process_article(
    article: dict,
    alias_index: dict,
    known_tickers: set[str],
    sector_by_ticker: dict[str, str],
    ticker_by_company_id: dict[int, str] | None = None,
    name_by_company_id: dict[int, str] | None = None,
    adapter=None,
) -> dict:
    """Process one article dict into a pipeline result.

    Returns {status, record | None, errors, ungrounded,
    force_review}. ``article`` shape is documented on
    DeterministicFallback.process_record. When ``adapter`` is None
    or raises ModelUnavailable, the deterministic fallback runs
    and the result is labelled RULE_BASED (status PROCESSED or
    REVIEW, never a fake LLM status). When an LLM adapter is
    supplied, its raw JSON is parsed and schema-validated; a
    parse or validation failure yields REJECTED with the errors.
    """
    errors: list[str] = []
    fallback = DeterministicFallback()
    base = fallback.process_record(
        article,
        alias_index,
        known_tickers,
        sector_by_ticker,
        ticker_by_company_id,
        name_by_company_id,
    )
    text = f"{article.get('title', '')} {article.get('text', '')}"

    if adapter is None:
        record = base
        processor = "RULE_BASED"
    else:
        try:
            import json as _json

            raw = adapter.process(text, "Extract the news intelligence record as JSON.")
            parsed = _json.loads(raw)
            ok, validation_errors, cleaned = validate_llm_output(parsed, known_tickers)
            if not ok:
                return {
                    "status": "REJECTED",
                    "record": None,
                    "errors": validation_errors,
                    "ungrounded": [],
                    "force_review": True,
                }
            record = cleaned
            record["processor"] = "LLM"
            processor = "LLM"
        except ModelUnavailable as exc:
            record = base
            processor = "RULE_BASED"
            errors.append(f"LLM unavailable, fallback used: {exc}")
        except (ValueError, TypeError) as exc:
            return {
                "status": "REJECTED",
                "record": None,
                "errors": [f"LLM output unparseable: {exc}"],
                "ungrounded": [],
                "force_review": True,
            }

    # Grounding + confidence, applied to either processor path.
    ungrounded = guards.check_record_grounding(record, text)
    ambiguous = bool(base.get("ambiguous_entity"))
    capped, force_review = guards.cap_confidence(
        float(record.get("confidence_score", 0.0)),
        ambiguous=ambiguous,
        validation_passed=True,
    )
    record["confidence_score"] = round(capped, 4)
    if ungrounded:
        force_review = True
    status = "REVIEW" if force_review else "PROCESSED"
    return {
        "status": status,
        "record": record,
        "errors": errors,
        "ungrounded": ungrounded,
        "force_review": force_review,
        "processor": processor,
    }
