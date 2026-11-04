"""Deterministic entity resolution (Phase 11).

Resolution uses ONLY the alias index: exact ticker tokens (word
boundaries) and exact full-alias phrases (word boundaries). There is no
single-token matching, so a generic word like PAKISTAN can never resolve
on its own, and a ticker substring like HBL inside HBLXYZ never matches.
Every match carries its alias, type, confidence, ambiguity flag and a
human-readable evidence string; ambiguous matches are capped at 0.50
and forced to review by the scoring rules.

For one company, only the highest-confidence matching alias is kept.
"""

from __future__ import annotations

import re

from app.services.news_events.aliases import build_alias_index, normalize


def _word_boundary_pattern(phrase: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)")


def resolve_text(
    text: str,
    index: dict[str, list[tuple[int, str, float, bool]]],
) -> list[dict]:
    """Resolve ``text`` against the alias index.

    Returns [{company_id, alias, alias_type, confidence, ambiguous,
    evidence}] sorted by confidence desc, then company_id. Empty text
    and texts with no exact alias/ticker match return [].
    """
    normalized = normalize(text)
    if not normalized:
        return []
    best: dict[int, dict] = {}
    for alias, rows in index.items():
        if not _word_boundary_pattern(alias).search(normalized):
            continue
        for company_id, alias_type, conf, ambiguous in rows:
            prev = best.get(company_id)
            if prev is None or conf > prev["confidence"]:
                best[company_id] = {
                    "company_id": company_id,
                    "alias": alias,
                    "alias_type": alias_type,
                    "confidence": conf,
                    "ambiguous": ambiguous,
                    "evidence": (
                        f"exact {'ticker' if alias_type == 'TICKER' else 'alias'} "
                        f"match '{alias}'" + (" (AMBIGUOUS: shared alias)" if ambiguous else "")
                    ),
                }
    return sorted(best.values(), key=lambda m: (-m["confidence"], m["company_id"]))


def build_index_from_companies(companies: list[tuple[int, str, str]]):
    """Convenience wrapper over aliases.build_alias_index."""
    return build_alias_index(companies)
