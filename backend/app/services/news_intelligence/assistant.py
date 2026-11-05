"""AI news assistant over stored rows (prompt section 11D).

Answers are built ONLY from stored news documents/events and
stored market rows, with a source link on every factual claim.
No answer is ever a buy/sell signal, a forecast, or investment
advice: recommendation questions get an uncertainty answer
(Phase 19 rule), and Phase 15 user-facing values are WITHHELD,
so the assistant never reintroduces them.

Supported question shapes (matched by intent keywords, in
order):
- company + today/recent -> company news timeline
- dividends -> dividend announcements
- sector + negative -> sector negative news
- economic/macro + sector -> macro news relevant to the sector
- compare <ticker> news with price movement -> news + market
  reaction (INSUFFICIENT_DATA when windows are missing)
- evidence behind sentiment -> the record's supporting
  evidence + grounding note
Anything else -> a scoped search over stored news (the RAG
fallback) or missing_data when nothing matches. A missing_data
answer carries NO citation — inventing one is a failure mode.
"""

from __future__ import annotations

import re

from app.services.news_intelligence.rag_news import search_news

RECOMMENDATION_PATTERNS = (
    "should i buy",
    "should i sell",
    "should i hold",
    "buy or sell",
    "is it a buy",
    "is it a sell",
    "recommend",
)


def _normalize(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip().lower())


def _cite(doc: dict) -> dict:
    return {
        "title": doc.get("title"),
        "source": doc.get("source"),
        "canonical_url": doc.get("canonical_url"),
        "published_at": doc.get("published_at"),
    }


# Words that look like tickers when uppercased but are question
# scaffolding or intent keywords, never company tickers. A token in
# the original question that is ALL-CAPS and NOT in this set is
# treated as a named ticker the user asked about.
_GENERIC_WORDS = {
    "SHOW", "ME", "MY", "THE", "A", "AN", "AND", "OR", "FOR", "WITH",
    "OF", "TO", "IN", "ON", "AT", "IS", "ARE", "ABOUT",
    "NEWS", "LATEST", "RECENT", "RECENTLY", "TODAY", "ALL", "ANY",
    "DIVIDEND", "DIVIDENDS", "BONUS", "RIGHTS", "EARNINGS", "PRICE",
    "MARKET", "STOCK", "SHARE", "SHARES", "COMPARE", "COMPARISON",
    "WHAT", "HAPPENED", "NEGATIVE", "POSITIVE", "ECONOMIC", "ECONOMY",
    "MACRO", "SECTOR", "BANK", "ENERGY", "CEMENT", "OIL", "GAS",
    "TEXTILE", "EVIDENCE", "SENTIMENT", "BEHIND", "GIVE", "TELL",
    "FIND", "LIST",
}


def _named_tickers(question: str) -> set[str]:
    """All-caps tokens in the ORIGINAL question that name tickers.

    The normalized (lowercased) question loses the all-caps signal,
    so this runs on the raw question. A question written entirely
    in capitals still scopes correctly: its scaffolding words are
    in _GENERIC_WORDS and drop out, leaving the ticker(s).
    """
    return {
        token
        for token in re.findall(r"\b[A-Z]{2,10}\b", question)
        if token not in _GENERIC_WORDS
    }


def _scope_to_named(docs: list[dict], named: set[str]) -> list[dict]:
    """If the user named tickers, keep only their documents.

    Without this, "Show me LUCK dividends" would answer with
    another company's dividends as if they were LUCK's — a wrong
    answer with a real citation, worse than missing_data.
    """
    if not named:
        return docs
    return [
        d for d in docs if named & {t.upper() for t in d.get("tickers", [])}
    ]


def answer_question(
    question: str,
    documents: list[dict],
    ticker_by_company_name: dict[str, str] | None = None,
    sector_by_ticker: dict[str, str] | None = None,
    market_reaction_for: object = None,
) -> dict:
    """Answer one question from stored rows.

    ``documents`` use the rag_news shape. ``ticker_by_company_name``
    maps normalized company-name fragments to tickers for the
    'what happened in X' shape. ``market_reaction_for`` is an
    optional callable (ticker, event_date) -> market-reaction dict
    for the comparison shape; when absent, comparison answers
    report the reaction as unavailable with the reason.
    Returns {answer_kind, answer_text, citations, note}.
    """
    normalized = _normalize(question)
    ticker_by_company_name = ticker_by_company_name or {}
    sector_by_ticker = sector_by_ticker or {}

    if any(p in normalized for p in RECOMMENDATION_PATTERNS):
        return {
            "answer_kind": "uncertainty",
            "answer_text": (
                "No issuable recommendation exists on the current "
                "evidence: user-facing decisions are WITHHELD and "
                "forecasts are abstained. This assistant does not "
                "produce buy/sell advice."
            ),
            "citations": [],
            "note": "Recommendation questions never receive a signal.",
        }

    # "Compare <TICKER> news with its price movement."
    compare = re.search(r"compare\s+([A-Za-z0-9]{2,10})\b", normalized)
    if compare:
        ticker = compare.group(1).upper()
        docs = [d for d in documents if ticker in [t.upper() for t in d.get("tickers", [])]]
        if not docs:
            return {
                "answer_kind": "missing_data",
                "answer_text": f"No stored news found for {ticker}, so no comparison is possible.",
                "citations": [],
                "note": "An empty result means no stored event, not no news in the world.",
            }
        reaction_note = (
            "Market-reaction windows are INSUFFICIENT_DATA on the "
            "current single price date; no movement comparison is "
            "fabricated."
        )
        if market_reaction_for is not None:
            try:
                reaction = market_reaction_for(ticker, docs[0].get("published_at"))
                reaction_note = f"Market reaction status: {reaction.get('status')}"
            except Exception as exc:  # defensive: never fail the answer
                reaction_note = f"Market reaction unavailable: {exc}"
        return {
            "answer_kind": "comparison",
            "answer_text": (
                f"{len(docs)} stored news item(s) for {ticker}. "
                f"Latest: {docs[0].get('title')}. {reaction_note}"
            ),
            "citations": [_cite(d) for d in docs[:5]],
            "note": "News and price movement are reported separately; correlation is not causality.",
        }

    named = _named_tickers(question)
    if "dividend" in normalized:
        docs = [d for d in documents if d.get("event_category") == "dividends"]
        docs = _scope_to_named(docs, named)
        if not docs:
            return {
                "answer_kind": "missing_data",
                "answer_text": (
                    f"No stored dividend announcements found for "
                    f"{', '.join(sorted(named))}."
                    if named
                    else "No stored dividend announcements found."
                ),
                "citations": [],
                "note": "Coverage is seed-only; absence here is not evidence of no dividends.",
            }
        return {
            "answer_kind": "direct_evidence",
            "answer_text": f"{len(docs)} stored dividend announcement(s).",
            "citations": [_cite(d) for d in docs],
            "note": "Dates are publication dates as stored; dateless actions are never dated by guesswork.",
        }

    if "negative" in normalized:
        sector_hit = None
        for word in ("bank", "energy", "cement", "oil", "gas", "textile"):
            if word in normalized:
                sector_hit = word
                break
        docs = [
            d
            for d in documents
            if d.get("sentiment") == "negative"
            and (sector_hit is None or sector_hit in " ".join(d.get("sectors", [])).lower())
        ]
        docs = _scope_to_named(docs, named)
        if not docs:
            return {
                "answer_kind": "missing_data",
                "answer_text": "No stored negative news found for that scope.",
                "citations": [],
                "note": "Sentiment here is the stored assessment (rule-based fallback unless an LLM record exists).",
            }
        return {
            "answer_kind": "direct_evidence",
            "answer_text": f"{len(docs)} stored negative news item(s).",
            "citations": [_cite(d) for d in docs],
            "note": "Sentiment is not a price prediction.",
        }

    if "economic" in normalized or "economy" in normalized or "macro" in normalized:
        docs = [d for d in documents if d.get("event_category") in ("macro_release", "interest_rate", "inflation", "budget", "exchange_rate")]
        docs = _scope_to_named(docs, named)
        if not docs:
            return {
                "answer_kind": "missing_data",
                "answer_text": "No stored macro/economic news found.",
                "citations": [],
                "note": "",
            }
        return {
            "answer_kind": "direct_evidence",
            "answer_text": f"{len(docs)} stored macro/economic item(s).",
            "citations": [_cite(d) for d in docs],
            "note": "Sector impact is assessed separately from the macro event itself.",
        }

    # "What happened in <COMPANY> today/recently" — company-name match.
    for fragment, ticker in ticker_by_company_name.items():
        if fragment in normalized:
            docs = [d for d in documents if ticker in [t.upper() for t in d.get("tickers", [])]]
            if not docs:
                return {
                    "answer_kind": "missing_data",
                    "answer_text": f"No stored news found for {ticker}.",
                    "citations": [],
                    "note": "An empty result means no stored event, not no news in the world.",
                }
            return {
                "answer_kind": "direct_evidence",
                "answer_text": f"Stored news for {ticker}: {docs[0].get('title')}",
                "citations": [_cite(d) for d in docs[:5]],
                "note": "'Today' means the latest stored items; live intraday collection does not run (jobs paused).",
            }

    if "evidence" in normalized and "sentiment" in normalized:
        docs = [d for d in documents if d.get("sentiment")]
        if not docs:
            return {
                "answer_kind": "missing_data",
                "answer_text": "No stored sentiment assessments found to show evidence for.",
                "citations": [],
                "note": "",
            }
        doc = docs[0]
        return {
            "answer_kind": "direct_evidence",
            "answer_text": (
                f"Sentiment {doc.get('sentiment')} for '{doc.get('title')}' rests on: "
                f"{'; '.join(doc.get('supporting_evidence', []) or ['stored assessment'])}. "
                "Sentiment is an assessment, not a price prediction."
            ),
            "citations": [_cite(doc)],
            "note": "Rule-based fallback assessments are labelled RULE_BASED in their records.",
        }

    # Fallback: scoped full-text search.
    found = search_news(documents, question)
    if not found["results"]:
        return {
            "answer_kind": "missing_data",
            "answer_text": "Nothing relevant found in stored news.",
            "citations": [],
            "note": "Search used deterministic full-text retrieval (FULL_TEXT_FALLBACK).",
        }
    return {
        "answer_kind": "direct_evidence",
        "answer_text": f"Top stored match: {found['results'][0]['title']}",
        "citations": [_cite(r) for r in found["results"][:5]],
        "note": "Retrieval method: FULL_TEXT_FALLBACK (vector retrieval not implemented).",
    }
