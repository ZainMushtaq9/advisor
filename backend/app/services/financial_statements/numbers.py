"""Pure number parsing for printed financial statements.

Rules (Phase 3 schema + Phase 7 spec):
- Commas are thousand separators and are stripped.
- (1,234) is negative. A trailing ")" without "(" is OCR noise on a
  printed negative; it parses as negative ONLY with the flag
  ``sign_inferred_from_closing_paren`` set, so the caller can lower
  confidence and record it.
- "-", "--", "nil", blank mean MISSING (None), never zero.
- Unicode ligatures (ﬁ, ﬂ) are normalised before matching.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_DASH_TOKENS = {"-", "--", "–", "—", "nil", "nil.", "n/a", ""}
_NOTE_REF_RE = re.compile(r"^\d{1,2}(\.\d){0,3}$")
_NUM_TOKEN_RE = re.compile(r"^\(?[\d,]+(\.\d+)?\)?$")


def normalise_text(text: str) -> str:
    """Normalise ligatures, dashes, hyphen spacing, case and
    whitespace for label matching only (never for number parsing)."""
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def is_note_ref(token: str) -> bool:
    """True for a bare note-reference token such as '14', '25.3' or
    '16.1.1' (multi-segment references, e.g. HUBC note 16.1.1).

    Each dotted segment must be exactly one digit, so genuine
    decimals are never mistaken for references: EPS '38.26' and
    dividend rates '5.00' / '8.50' do NOT match.
    """
    return bool(_NOTE_REF_RE.match(token.strip()))


def parse_number(token: str) -> tuple[Decimal | None, bool, bool]:
    """Parse one displayed token.

    Returns (value, is_missing, sign_inferred). ``value`` is None for
    missing tokens. A token that is not numeric at all also returns
    (None, False, False) so callers can distinguish "not a number"
    from "missing" by checking the token against _DASH_TOKENS first.
    """
    raw = token.strip().strip("_").strip()
    if raw.lower() in _DASH_TOKENS:
        return None, True, False
    cleaned = raw.replace(",", "").replace("_", "")
    sign_inferred = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    elif cleaned.endswith(")") and not cleaned.startswith("("):
        # OCR dropped the opening paren; treat as negative but flag it.
        cleaned = "-" + cleaned[:-1]
        sign_inferred = True
    try:
        return Decimal(cleaned), False, sign_inferred
    except InvalidOperation:
        return None, False, False


def token_is_numeric(token: str) -> bool:
    """True if the token looks like a printed number or a dash."""
    t = token.strip().strip("_")
    if t.lower() in _DASH_TOKENS:
        return True
    return bool(_NUM_TOKEN_RE.match(t.replace(",", "")))


def normalise_value(numeric: Decimal | None, reported_unit: str | None) -> Decimal | None:
    """Scale a reported figure into base PKR units.

    reported_unit 'thousands' (Rs. '000s / Rupees in thousand) means
    multiply by 1,000. 'millions'/'billions' likewise. Any other unit
    (including None) passes the value through unchanged, and the
    caller records the rule string.
    """
    if numeric is None:
        return None
    scale = {"thousands": 1000, "millions": 1_000_000, "billions": 1_000_000_000}
    return numeric * scale.get((reported_unit or "").lower(), 1)
