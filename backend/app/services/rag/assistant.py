"""Phase 19 grounded research assistant.

Answer synthesis distinguishes, in the brief's vocabulary:

- direct_evidence: the answer is a passage retrieved from an
  indexed document, cited to ticker + title + page + section
  with a capped snippet. The answer text quotes only the
  retrieved passage (plus its citation); nothing is added
  from outside the passage.
- derived_calculation: the answer is a platform calculation
  row (a Phase 8 ratio, a Phase 9 valuation, a Phase 15
  decision), cited to that row's identity and its inputs. It
  is labelled DERIVED, never presented as document text.
- inference: the answer combines retrieved passages with
  stated reasoning; every factual element still carries a
  citation, and the inference step is labelled as inference.
- uncertainty: retrieved evidence is partial or conflicting;
  the answer states what is known, what is missing, and why
  no firmer answer is given.
- missing_data: nothing relevant was retrieved (or the
  company has no indexed document). The answer states that
  plainly and carries NO citation — inventing a citation is
  a failure mode, not a fallback.

No answer is ever a buy/sell signal, a forecast, or investment
advice: Phase 15 user-facing values are WITHHELD, Phase 13
forecasts are abstained, and this assistant does not reintroduce
either. A question asking for a recommendation receives an
uncertainty answer explaining that no issuable recommendation
exists on the current evidence.
"""

from __future__ import annotations

from app.services.rag.retrieval import ScoredChunk

# Question patterns that ask for an executable recommendation.
# These never receive a direct answer: the pipeline holds no
# issuable recommendation (Phase 15 WITHHELD), so the honest
# answer is uncertainty, not a signal.
RECOMMENDATION_PATTERNS = (
    "should i buy",
    "should i sell",
    "should i hold",
    "buy or sell",
    "is it a buy",
    "is it a sell",
    "recommend",
)


def is_recommendation_question(query: str) -> bool:
    lowered = query.lower()
    return any(pattern in lowered for pattern in RECOMMENDATION_PATTERNS)


def answer_from_chunks(
    query: str,
    retrieved: list[ScoredChunk],
    ticker: str | None = None,
) -> dict:
    """Build a direct-evidence / missing-data answer from
    retrieved chunks. Never invents a citation: with no
    retrieved chunk the answer is missing_data with an empty
    citation list."""
    if is_recommendation_question(query):
        return {
            "answer_kind": "uncertainty",
            "answer_text": (
                "No issuable recommendation exists on the current "
                "evidence: Phase 15 user-facing values are WITHHELD "
                "(confidence caps at LOW while inputs stay "
                "UNVERIFIED and Phase 13 forecasting is abstained), "
                "and this assistant does not generate buy/sell "
                "signals. The retrieved evidence below is "
                "descriptive only."
            ),
            "citations": [c.citation() for c in retrieved],
            "retrieved_chunk_ids": [c.chunk_id for c in retrieved],
        }
    if not retrieved:
        if ticker:
            detail = (
                f"No indexed document exists for {ticker} in the "
                "knowledge base (its statements are not loaded), "
                "and no relevant passage was retrieved."
            )
        else:
            detail = "No relevant passage was retrieved from the knowledge base."
        return {
            "answer_kind": "missing_data",
            "answer_text": (
                "Not found in the indexed evidence. " + detail + " "
                "No citation is given because no passage supports "
                "an answer; the question is recorded as missing "
                "data rather than answered from outside sources."
            ),
            "citations": [],
            "retrieved_chunk_ids": [],
        }
    top = retrieved[0]
    return {
        "answer_kind": "direct_evidence",
        "answer_text": (
            "Direct evidence located at "
            f"{top.ticker} p.{top.page_number} ({top.section_label}); "
            "passage preview (capped at 500 chars; the full cited "
            f"passage is chunk {top.chunk_id}): {top.snippet()}"
        ),
        "citations": [c.citation() for c in retrieved],
        "retrieved_chunk_ids": [c.chunk_id for c in retrieved],
    }


def answer_from_calculation(
    query: str,
    metric_key: str,
    company_ticker: str,
    value: object,
    unit: str,
    source_row: dict,
) -> dict:
    """Build a derived-calculation answer. The citation names
    the calculation row (table + id + metric + inputs), never a
    document page the value did not come from."""
    return {
        "answer_kind": "derived_calculation",
        "answer_text": (
            f"Derived calculation (not document text): {company_ticker} "
            f"{metric_key} = {value} {unit}. This value is computed "
            "by the platform's deterministic engine from stored "
            "statement rows; it is not a quotation from a filing."
        ),
        "citations": [
            {
                "kind": "derived_calculation",
                "ticker": company_ticker,
                "metric": metric_key,
                "value": str(value),
                "unit": unit,
                "source_row": source_row,
            }
        ],
        "retrieved_chunk_ids": [],
    }
