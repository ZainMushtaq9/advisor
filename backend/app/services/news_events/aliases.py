"""Deterministic company alias generation (Phase 11).

Rules (same discipline as the Phase 4 normalization, extended only by
documented variants):
- normalize: NFKC -> upper -> punctuation to space -> collapse spaces.
- Strip TRAILING legal suffixes repeatedly: LIMITED, LTD, PVT LTD,
  PRIVATE LIMITED, PLC, INC, CORPORATION, COMPANY, CO.
- NO abbreviation expansion: IND stays IND, it is not INDUSTRIES.
- NO token merging: "D G" stays two tokens, it is not DG.
- NO fuzzy matching: an alias matches exactly or not at all.
- Variants generated per company: TICKER, LEGAL (normalized legal
  name), LEGAL_STRIPPED, PAREN_STRIPPED (parenthetical qualifier
  dropped), PAREN_STRIPPED_SUFFIX (both).
- An alias claimed by more than one company is AMBIGUOUS: effective
  confidence is capped at 0.50 and every match goes to review.
"""

from __future__ import annotations

import re
import unicodedata

SUFFIXES = (
    "LIMITED",
    "LTD",
    "PVT LTD",
    "PRIVATE LIMITED",
    "PLC",
    "INC",
    "CORPORATION",
    "COMPANY",
    "CO",
)

# Longest first so "PVT LTD" strips as one suffix, not "LTD" then "PVT".
_SUFFIXES_SORTED = sorted(SUFFIXES, key=len, reverse=True)

CONFIDENCE = {
    "TICKER": 1.0,
    "LEGAL": 0.95,
    "LEGAL_STRIPPED": 0.85,
    "PAREN_STRIPPED": 0.80,
    "PAREN_STRIPPED_SUFFIX": 0.75,
}

AMBIGUOUS_CAP = 0.50

_PAREN_RE = re.compile(r"\([^)]*\)")


def normalize(text: str) -> str:
    """NFKC -> upper -> punctuation to space -> collapse whitespace."""
    out = unicodedata.normalize("NFKC", text).upper()
    out = re.sub(r"[^A-Z0-9]+", " ", out)
    return re.sub(r"\s+", " ", out).strip()


def strip_suffixes(normalized: str) -> str:
    """Strip trailing legal suffixes repeatedly. '' stays ''."""
    out = normalized
    changed = True
    while changed:
        changed = False
        for suffix in _SUFFIXES_SORTED:
            if out == suffix:
                return ""
            if out.endswith(" " + suffix):
                out = out[: -(len(suffix) + 1)]
                changed = True
                break
    return out


def drop_parenthetical(text: str) -> str:
    """Remove '(...)' qualifiers, e.g. '(Pakistan)', '(Pref)'."""
    return _PAREN_RE.sub(" ", text)


def generate_aliases(legal_name: str, ticker: str) -> list[tuple[str, str, float]]:
    """Return [(alias_normalized, alias_type, base_confidence)].

    Duplicates collapse (highest-confidence type wins); empty aliases
    are dropped. The ticker itself is always an alias.
    """
    by_alias: dict[str, tuple[str, float]] = {}

    def _add(alias: str, alias_type: str) -> None:
        if not alias:
            return
        prev = by_alias.get(alias)
        conf = CONFIDENCE[alias_type]
        if prev is None or conf > prev[1]:
            by_alias[alias] = (alias_type, conf)

    _add(normalize(ticker), "TICKER")
    legal = normalize(legal_name)
    _add(legal, "LEGAL")
    _add(strip_suffixes(legal), "LEGAL_STRIPPED")
    paren = normalize(drop_parenthetical(legal_name))
    _add(paren, "PAREN_STRIPPED")
    _add(strip_suffixes(paren), "PAREN_STRIPPED_SUFFIX")
    return [(alias, typ, conf) for alias, (typ, conf) in by_alias.items()]


def build_alias_index(
    companies: list[tuple[int, str, str]],
) -> dict[str, list[tuple[int, str, float, bool]]]:
    """Build alias -> [(company_id, alias_type, confidence, ambiguous)].

    ``companies`` is [(company_id, legal_name, ticker)]. Ambiguity is
    computed across the whole registry before confidences are capped,
    so a shared alias is capped for every claimant.
    """
    claims: dict[str, list[tuple[int, str, float]]] = {}
    for company_id, legal_name, ticker in companies:
        for alias, alias_type, conf in generate_aliases(legal_name, ticker):
            claims.setdefault(alias, []).append((company_id, alias_type, conf))
    index: dict[str, list[tuple[int, str, float, bool]]] = {}
    for alias, rows in claims.items():
        ambiguous = len({row[0] for row in rows}) > 1
        index[alias] = [
            (
                company_id,
                alias_type,
                min(conf, AMBIGUOUS_CAP) if ambiguous else conf,
                ambiguous,
            )
            for company_id, alias_type, conf in rows
        ]
    return index
