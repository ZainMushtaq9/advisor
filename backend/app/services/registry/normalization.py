"""Deterministic normalization for the Phase 4 registry.

Rules (documented in docs/phase-04/normalization_and_matching.md):
- Original values are ALWAYS stored untouched alongside normalized values.
- Normalization is pure string manipulation; no LLM, no fuzzy guessing.
- A normalized value is a match key only, never a display value and
  never evidence that two records are the same company.
"""

from __future__ import annotations

import re
import unicodedata

# Suffixes that vary in spelling but do not distinguish a legal issuer.
# They are stripped ONLY for the normalized match key, never from the
# stored legal name.
_SUFFIXES = (
    " LIMITED",
    " LTD",
    " PVT LTD",
    " PRIVATE LIMITED",
    " PLC",
    " INC",
    " CORPORATION",
    " COMPANY",
    " CO",
)


def normalize_ticker(value: str) -> str:
    """Ticker match key: upper-case, no whitespace/punctuation inside.

    PSX tickers are short uppercase codes (e.g. OGDC). A ticker with a
    suffix such as '.KAR' is NOT silently collapsed to the bare code:
    the suffix is kept, because collapsing it could merge two listings.
    """
    if not isinstance(value, str):
        raise TypeError("ticker must be a string")
    cleaned = unicodedata.normalize("NFKC", value).strip().upper()
    cleaned = re.sub(r"\s+", "", cleaned)
    if not cleaned:
        raise ValueError("ticker must not be empty")
    if len(cleaned) > 50:
        raise ValueError("ticker exceeds 50 characters")
    return cleaned


def normalize_name(value: str) -> str:
    """Company-name match key: case-folded, punctuation collapsed,
    common legal suffixes stripped, whitespace collapsed.

    Two names with the same normalized key are CANDIDATES for a match,
    not a confirmed match — the matcher still requires an identifier
    (ticker, ISIN, or identifier row) to agree.
    """
    if not isinstance(value, str):
        raise TypeError("company name must be a string")
    text = unicodedata.normalize("NFKC", value).strip().upper()
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # "&" and "and" are the same conjunction for matching purposes.
    text = re.sub(r"\bAND\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Strip repeatedly: "Engro Corporation Limited" loses LIMITED and
    # then CORPORATION. A single strip would leave a false difference.
    changed = True
    while changed:
        changed = False
        for suffix in _SUFFIXES:
            if text.endswith(suffix):
                text = text[: -len(suffix)].strip()
                changed = True
                break
    if not text:
        raise ValueError("company name must not be empty after normalization")
    return text


def normalize_sector_name(value: str) -> str:
    """Sector match key: case-folded, punctuation collapsed.

    Source sector taxonomies are NOT merged by normalization. A sector
    row keeps its source and source_sector_name; this key is used only
    to find an existing row from the SAME source.
    """
    if not isinstance(value, str):
        raise TypeError("sector name must be a string")
    text = unicodedata.normalize("NFKC", value).strip().upper()
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise ValueError("sector name must not be empty after normalization")
    return text


def normalize_isin(value: str) -> str:
    """ISIN match key: upper-case, no whitespace. Format is validated
    (2 letters + 9 alphanumerics + 1 check digit) but the check digit
    is NOT recomputed here — that is a Phase 5+ validation concern,
    and a failed format check is a rejection, not a correction.
    """
    if not isinstance(value, str):
        raise TypeError("ISIN must be a string")
    cleaned = unicodedata.normalize("NFKC", value).strip().upper()
    cleaned = re.sub(r"\s+", "", cleaned)
    if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", cleaned):
        raise ValueError(f"ISIN does not match the expected format: {value!r}")
    return cleaned
