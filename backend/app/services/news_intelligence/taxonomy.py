"""Event taxonomy for the News Intelligence Engine.

Prompt section 5 categories, as configurable entries. Phase 11 event
types map onto this taxonomy (see PHASE11_TYPE_MAP); the taxonomy is
the wider set, Phase 11's is the seed subset. Keyword rules in
KEYWORD_RULES are the DETERMINISTIC fallback classifier only: they
never claim LLM accuracy, and any text matching no rule is
``other`` with low confidence, forced to review.

Language note: keyword rules cover English text. Text in Arabic
script (Urdu) is detected by script range and classified as
``other`` with language ``ur`` and confidence capped at 0.50, forced
to review — never misclassified by English keywords. Urdu LLM
classification is UNVERIFIED until a local model is measured on
Urdu input (see docs/news-intelligence/model_selection_report.md).
"""

from __future__ import annotations

import re

# Prompt section 5, as stable category keys.
CATEGORIES = (
    "earnings",
    "dividends",
    "bonus",
    "rights",
    "buyback",
    "board_meeting",
    "board_changes",
    "merger_acquisition",
    "new_project",
    "contract_order",
    "expansion",
    "management_change",
    "regulatory_notice",
    "court_decision",
    "banking_policy",
    "interest_rate",
    "inflation",
    "exchange_rate",
    "foreign_reserves",
    "budget",
    "tax_policy",
    "energy_price",
    "oil_gas",
    "commodity_price",
    "political_geopolitical",
    "market_wide",
    "credit_rating",
    "company_default",
    "trading_suspension",
    "corporate_governance",
    "macro_release",
    "other",
)

# Phase 11 seed event types -> taxonomy categories.
PHASE11_TYPE_MAP = {
    "earnings": "earnings",
    "dividends": "dividends",
    "rights": "rights",
    "bonus": "bonus",
    "buyback": "buyback",
    "board_changes": "board_changes",
    "litigation": "court_decision",
    "regulatory_notice": "regulatory_notice",
    "plant_outage": "other",
    "contract": "contract_order",
    "merger": "merger_acquisition",
    "rating": "credit_rating",
    "policy_change": "banking_policy",
    "macro_release": "macro_release",
}

# Deterministic fallback keyword rules: (category, [patterns]).
# Order matters: first match wins; patterns are word-boundary regexes
# over normalized (uppercased) text. Kept deliberately small and
# auditable — a rule list that pretends to understand news would be
# a hallucination source, not a classifier.
# ORDER MATTERS (first match wins): the more specific rule must
# come first. Dividends precedes earnings because "quarterly
# dividend" contains QUARTERLY, which the earnings rule also
# matches; court_decision precedes contract_order because a
# "contract dispute" in court is a court matter first. Both
# orderings were fixed after the N=20 evaluation run showed the
# generic rule winning (2026-11-05).
KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("dividends", [r"\bDIVIDEND\b", r"\bCASH PAYOUT\b", r"\bINTERIM DIVIDEND\b", r"\bFINAL DIVIDEND\b"]),
    ("earnings", [r"\bRESULTS\b", r"\bPROFIT\b", r"\bLOSS AFTER TAX\b", r"\bEPS\b", r"\bEARNINGS\b", r"\bQUARTERLY\b", r"\bANNUAL RESULTS\b"]),
    ("bonus", [r"\bBONUS SHARES\b", r"\bBONUS ISSUE\b"]),
    ("rights", [r"\bRIGHT SHARES\b", r"\bRIGHT ISSUE\b"]),
    ("buyback", [r"\bBUYBACK\b", r"\bSHARE REPURCHASE\b"]),
    ("board_meeting", [r"\bBOARD MEETING\b"]),
    ("board_changes", [r"\bBOARD OF DIRECTORS\b", r"\bDIRECTOR APPOINTED\b", r"\bDIRECTOR RESIGNED\b"]),
    ("merger_acquisition", [r"\bMERGER\b", r"\bACQUISITION\b", r"\bACQUIRED\b", r"\bTAKEOVER\b"]),
    ("court_decision", [r"\bCOURT\b", r"\bSUIT\b", r"\bLITIGATION\b"]),
    ("contract_order", [r"\bCONTRACT\b", r"\bORDER WORTH\b", r"\bAWARDED\b"]),
    ("new_project", [r"\bNEW PROJECT\b", r"\bPROJECT LAUNCH\b"]),
    ("expansion", [r"\bEXPANSION\b", r"\bNEW PLANT\b", r"\bCAPACITY EXPANSION\b"]),
    ("management_change", [r"\bCEO\b.*\b(APPOINTED|RESIGNED|STEPPED DOWN)\b", r"\bCHIEF EXECUTIVE\b"]),
    ("trading_suspension", [r"\bTRADING SUSPEND", r"\bSUSPENDED FROM TRADING\b"]),
    ("company_default", [r"\bDEFAULTED\b", r"\bLOAN DEFAULT\b"]),
    ("credit_rating", [r"\bCREDIT RATING\b", r"\bRATING (UPGRADED|DOWNGRADED)\b"]),
    ("regulatory_notice", [r"\bSECP\b", r"\bREGULATORY\b", r"\bSHOW CAUSE\b", r"\bNOTICE\b"]),
    ("interest_rate", [r"\bPOLICY RATE\b", r"\bINTEREST RATE\b", r"\bMONETARY POLICY\b"]),
    ("inflation", [r"\bINFLATION\b", r"\bCPI\b"]),
    ("exchange_rate", [r"\bRUPEE\b.*\b(DOLLAR|USD)\b", r"\bEXCHANGE RATE\b", r"\bINTERBANK\b"]),
    ("foreign_reserves", [r"\bFOREIGN RESERVES\b", r"\bFOREX RESERVES\b"]),
    ("budget", [r"\bBUDGET\b", r"\bFISCAL\b"]),
    ("tax_policy", [r"\bTAX\b", r"\bSUPER TAX\b", r"\bWITHHOLDING TAX\b"]),
    ("energy_price", [r"\bELECTRICITY TARIFF\b", r"\bPOWER TARIFF\b", r"\bFUEL PRICE\b"]),
    ("oil_gas", [r"\bOIL PRICE\b", r"\bCRUDE\b", r"\bGAS PRICE\b", r"\bOPEC\b"]),
    ("commodity_price", [r"\bCOMMODITY\b", r"\bGOLD PRICE\b", r"\bCOTTON PRICE\b"]),
    ("banking_policy", [r"\bSTATE BANK\b", r"\bSBP\b", r"\bCASH RESERVE\b", r"\bSTATUTORY LIQUIDITY\b"]),
    ("political_geopolitical", [r"\bGOVERNMENT\b", r"\bELECTION\b", r"\bPOLITICAL\b", r"\bGEOPOLITICAL\b"]),
    ("market_wide", [r"\bKSE-100\b", r"\bKSE 100\b", r"\bINDEX\b.*\b(POINTS|CLOSED)\b", r"\bMARKET\b.*\b(RALLY|CRASH|CLOSED)\b"]),
    ("corporate_governance", [r"\bGOVERNANCE\b", r"\bAUDIT COMMITTEE\b", r"\bANNUAL GENERAL MEETING\b", r"\bAGM\b"]),
]

_ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF]")


def detect_language(text: str) -> str:
    """'ur' if Arabic-script characters dominate, else 'en'.

    Mixed-script text returns 'mixed'. Empty text returns 'other'.
    This is script detection, not language identification: Urdu and
    Arabic share the script, so 'ur' here means 'Arabic-script text
    handled as Urdu for this Pakistan-market product', documented
    as a limitation, never as verified language identification.
    """
    if not text or not text.strip():
        return "other"
    arabic = len(_ARABIC_SCRIPT.findall(text))
    total = len([c for c in text if c.isalpha()])
    if total == 0:
        return "other"
    if arabic / total >= 0.5:
        return "ur"
    if arabic > 0:
        return "mixed"
    return "en"


def classify_deterministic(text: str) -> tuple[str, float, str]:
    """Deterministic fallback classification.

    Returns (category, confidence, basis). Arabic-script text is
    never classified by English keywords: it returns ('other',
    0.50, 'urdu_script_review'). Unmatched English text returns
    ('other', 0.50, 'no_keyword_rule'). A keyword match returns
    confidence 0.70 — a rule hit, not a measured accuracy.
    """
    if not text or not text.strip():
        return "other", 0.0, "empty_text"
    if detect_language(text) in ("ur", "mixed"):
        return "other", 0.50, "urdu_script_review"
    normalized = text.upper()
    for category, patterns in KEYWORD_RULES:
        for pattern in patterns:
            if re.search(pattern, normalized):
                return category, 0.70, f"keyword_rule:{category}"
    return "other", 0.50, "no_keyword_rule"


def is_valid_category(category: str) -> bool:
    return category in CATEGORIES
