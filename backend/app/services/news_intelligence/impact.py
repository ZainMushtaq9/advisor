"""Explainable news-impact assessment.

Sentiment, importance, source credibility, company relevance,
sector relevance, and market-wide relevance are SEPARATE numbers
with separate reasons. Nothing here is a price prediction: no
percentage impact is ever produced, and no target price exists
anywhere in this module. Where the evidence cannot support an
assessment, the result is INSUFFICIENT_DATA with the reason —
never a fabricated number.

Source credibility classes (prompt section 13):
official_primary 1.00, company_disclosure 0.95, established_press
0.80, secondary_reporting 0.60, unverified 0.30. Quality is
separate from sentiment: a negative story from an official
source is high-credibility AND negative, and both facts are
reported.
"""

from __future__ import annotations

SOURCE_CREDIBILITY = {
    "official_primary": 1.00,
    "company_disclosure": 0.95,
    "established_press": 0.80,
    "secondary_reporting": 0.60,
    "unverified": 0.30,
}

# Event categories that are structurally material for a single
# company (results, payouts, capital actions, distress). Used only
# to rank importance for display; the weight is documented, not
# measured, and importance is labelled as assessed, not observed.
COMPANY_MATERIAL_CATEGORIES = frozenset(
    {
        "earnings",
        "dividends",
        "bonus",
        "rights",
        "buyback",
        "merger_acquisition",
        "company_default",
        "trading_suspension",
        "credit_rating",
    }
)


def assess_impact(
    record: dict,
    source_quality_class: str,
    sector_match: bool = False,
    conflicting_records: list[dict] | None = None,
) -> dict:
    """Assess one validated intelligence record.

    Returns {sentiment, importance_score, credibility_score,
    company_relevance, sector_relevance, market_relevance,
    horizon, supporting_facts, counterarguments, uncertainty,
    confidence, status}. ``status`` is "assessed" or
    "INSUFFICIENT_DATA" (when the record carries no tickers AND
    no sector AND no market scope — there is nothing to assess
    relevance against).
    """
    tickers = record.get("ticker_symbols", [])
    sectors = record.get("sector_names", [])
    category = record.get("event_category", "other")
    if not tickers and not sectors and category == "other":
        return {
            "sentiment": record.get("sentiment", "neutral"),
            "importance_score": None,
            "credibility_score": SOURCE_CREDIBILITY.get(source_quality_class, 0.30),
            "company_relevance": None,
            "sector_relevance": None,
            "market_relevance": None,
            "horizon": record.get("potential_impact_horizon", "unknown"),
            "supporting_facts": list(record.get("extracted_facts", [])),
            "counterarguments": [],
            "uncertainty": ["No company, sector, or material category: nothing to assess relevance against."],
            "confidence": float(record.get("confidence_score", 0.0)),
            "status": "INSUFFICIENT_DATA",
        }

    credibility = SOURCE_CREDIBILITY.get(source_quality_class, 0.30)
    relevance = float(record.get("relevance_score", 0.0))
    impact = float(record.get("impact_score", 0.0))
    if category in COMPANY_MATERIAL_CATEGORIES and tickers:
        importance = round(min(1.0, 0.6 + 0.4 * relevance), 4)
    elif sectors or sector_match:
        importance = round(min(1.0, 0.4 + 0.4 * relevance), 4)
    else:
        importance = round(0.3 + 0.4 * impact, 4)

    counterarguments: list[str] = []
    for other in conflicting_records or []:
        if other.get("sentiment") != record.get("sentiment"):
            counterarguments.append(
                "Conflicting report preserved side-by-side: "
                f"{other.get('source', 'unknown source')} reports "
                f"sentiment {other.get('sentiment')} for the same event "
                f"({other.get('article_id', 'no id')}). Neither version "
                "was silently chosen."
            )

    return {
        "sentiment": record.get("sentiment", "neutral"),
        "importance_score": importance,
        "credibility_score": credibility,
        "company_relevance": round(relevance, 4) if tickers else None,
        "sector_relevance": round(relevance, 4) if (sectors or sector_match) else None,
        "market_relevance": round(impact, 4),
        "horizon": record.get("potential_impact_horizon", "unknown"),
        "supporting_facts": list(record.get("extracted_facts", [])),
        "counterarguments": counterarguments,
        "uncertainty": list(record.get("uncertainty_notes", [])),
        "confidence": float(record.get("confidence_score", 0.0)),
        "status": "assessed",
    }
