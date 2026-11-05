"""Provider-independent LLM adapter.

The pipeline talks to ``LLMAdapter`` only. Swapping the local model
means swapping the adapter, never redesigning the pipeline.

Adapters:
- ``OllamaAdapter``: stdlib HTTP to a local Ollama server
  (http://localhost:11434, no keys, no paid API). It is
  UNVERIFIED until a model is actually measured on this hardware
  (see docs/news-intelligence/model_selection_report.md): the
  class existing does not prove a model runs.
- ``DeterministicFallback``: rule-based processing (Phase 11
  resolver + taxonomy keywords + a small sentiment lexicon).
  Its output is labelled ``processor="RULE_BASED"`` and
  ``model_name="deterministic-fallback-v1"`` everywhere, so it
  can never be mistaken for LLM output.
- ``NullAdapter``: raises ``ModelUnavailable``. Used when no
  model is configured: the pipeline then records the article as
  UNPROCESSED with the exact reason, instead of faking output.

No adapter ever calls a paid API. There is no OpenAI/Gemini/Groq
code path anywhere in this package, by design.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Protocol

from app.services.news_events.aliases import normalize
from app.services.news_events.resolver import resolve_text
from app.services.news_intelligence.taxonomy import (
    classify_deterministic,
    detect_language,
)


class ModelUnavailable(Exception):
    """No local model is configured or reachable."""


class LLMAdapter(Protocol):
    """process(prompt_text, article) -> raw model JSON string."""

    model_name: str
    model_version: str

    def process(self, article_text: str, instruction: str) -> str:
        ...


class NullAdapter:
    """Always unavailable. Forces the honest UNPROCESSED path."""

    model_name = "none"
    model_version = "none"

    def process(self, article_text: str, instruction: str) -> str:
        raise ModelUnavailable(
            "No local LLM is configured or reachable. Unblocker: "
            "install Ollama, pull a small open-weight instruction "
            "model, and measure latency/memory on this hardware."
        )


class OllamaAdapter:
    """Local Ollama adapter (stdlib only, no API keys).

    Posts to /api/generate with format=json. The caller validates
    the returned JSON with schema.validate_llm_output; this class
    performs no validation itself, so a malformed model reply is
    caught downstream, never trusted here.
    """

    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 120,
    ) -> None:
        self.model_name = "ollama"
        self.model_version = model
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def process(self, article_text: str, instruction: str) -> str:
        payload = json.dumps(
            {
                "model": self._model,
                "prompt": f"{instruction}\n\nARTICLE:\n{article_text}",
                "format": "json",
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self._base_url + "/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except OSError as exc:
            raise ModelUnavailable(f"Ollama server unreachable: {exc}") from exc
        if "response" not in body:
            raise ModelUnavailable("Ollama reply carried no 'response' field")
        return str(body["response"])


# Small auditable sentiment lexicon for the deterministic fallback.
# This is a word-count heuristic, documented as such: it measures
# wording, not market truth, and its output is labelled RULE_BASED.
# Words are UPPERCASE: lexicon_sentiment compares against
# normalize() output, which uppercases. Lowercase sets here made
# every comparison miss and forced every sentiment to neutral
# (found by the N=20 evaluation run, 2026-11-05; fixed the same day).
_POSITIVE_WORDS = frozenset(
    {
        "PROFIT", "GROWTH", "INCREASE", "INCREASED", "GAIN", "GAINS",
        "RISE", "RECORD", "STRONG", "POSITIVE", "SURGE", "UP", "HIGHER",
        "DIVIDEND", "EXPANSION", "APPROVAL", "AWARD", "CONTRACT",
    }
)
_NEGATIVE_WORDS = frozenset(
    {
        "LOSS", "DECLINE", "DECLINED", "FALL", "FELL", "DROP", "DROPPED",
        "DECREASE", "DECREASED", "NEGATIVE", "WEAK", "DEFAULT", "FINE",
        "PENALTY", "SUSPENSION", "LAWSUIT", "FRAUD", "DOWNGRADE",
    }
)


def lexicon_sentiment(text: str) -> str:
    """Word-count sentiment heuristic. 'mixed' on a tie with both
    sides present, 'neutral' when neither side appears."""
    tokens = set(normalize(text).split())
    pos = len(tokens & _POSITIVE_WORDS)
    neg = len(tokens & _NEGATIVE_WORDS)
    if pos > 0 and neg == 0:
        return "positive"
    if neg > 0 and pos == 0:
        return "negative"
    if pos > 0 and neg > 0:
        return "mixed"
    return "neutral"


class DeterministicFallback:
    """Rule-based processor. Output is labelled RULE_BASED.

    Uses the Phase 11 resolver for tickers (exact alias/ticker
    matches only, ambiguous capped at 0.50), the taxonomy keyword
    classifier, and the lexicon sentiment heuristic. It never
    invents a fact: extracted_facts are the headline itself plus
    the matched alias evidence strings, both grounded in the
    input by construction.
    """

    model_name = "deterministic-fallback-v1"
    model_version = "rule-based-1.0"

    def process_record(
        self,
        article: dict,
        alias_index: dict,
        known_tickers: set[str],
        sector_by_ticker: dict[str, str],
        ticker_by_company_id: dict[int, str] | None = None,
        name_by_company_id: dict[int, str] | None = None,
    ) -> dict:
        """Build a validated-shape record from rules.

        ``article``: {article_id, title, source, canonical_url,
        published_at, retrieved_at, language?, text}. ``text`` is
        headline + excerpt (never a full article body: the schema
        stores no body). ``ticker_by_company_id`` /
        ``name_by_company_id`` map resolver company ids to registry
        tickers/names: a legal-name match resolves to its ticker
        through the company id, never by guessing from the alias
        text. Returns a dict in the prompt section 4 shape; the
        caller still runs schema validation on it.
        """
        text = f"{article.get('title', '')} {article.get('text', '')}"
        language = article.get("language") or detect_language(text)
        matches = resolve_text(text, alias_index)
        ticker_by_company_id = ticker_by_company_id or {}
        name_by_company_id = name_by_company_id or {}
        tickers: list[str] = []
        company_names: list[str] = []
        ambiguous = False
        for match in matches:
            ticker = ticker_by_company_id.get(match["company_id"])
            if ticker and ticker in known_tickers:
                tickers.append(ticker)
            name = name_by_company_id.get(match["company_id"])
            if name:
                company_names.append(name)
            if match["ambiguous"]:
                ambiguous = True
        tickers = sorted(set(tickers))
        company_names = sorted(set(company_names))
        category, cat_confidence, cat_basis = classify_deterministic(text)
        sentiment = lexicon_sentiment(text)
        confidence = min(cat_confidence, 0.50 if ambiguous else 0.70)
        sectors = sorted({sector_by_ticker[t] for t in tickers if t in sector_by_ticker})
        summary = (article.get("title", "") or "")[:280]
        return {
            "article_id": article.get("article_id", ""),
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "canonical_url": article.get("canonical_url", ""),
            "published_at": article.get("published_at", ""),
            "retrieved_at": article.get("retrieved_at", ""),
            "language": language if language in ("en", "ur", "mixed", "other") else "other",
            "company_names": company_names,
            "ticker_symbols": tickers,
            "sector_names": sectors,
            "event_category": category,
            "sentiment": sentiment,
            "relevance_score": round(min(1.0, 0.5 + 0.1 * len(tickers)), 4),
            "impact_score": round(cat_confidence, 4),
            "confidence_score": round(confidence, 4),
            "potential_impact_horizon": "unknown",
            "extracted_facts": [article.get("title", "")] if article.get("title") else [],
            "supporting_evidence": [
                f"rule_based:{cat_basis}",
                f"resolver_matches:{len(matches)}",
            ],
            "uncertainty_notes": [
                "Deterministic fallback output: rule-based, not LLM output. "
                "Treat sentiment and category as heuristics, not measurements."
            ],
            "risk_factors": [],
            "summary": summary,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "processing_timestamp": article.get("retrieved_at", ""),
            "processor": "RULE_BASED",
            "ambiguous_entity": ambiguous,
        }
