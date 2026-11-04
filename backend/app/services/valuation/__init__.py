"""Phase 9 company-valuation services.

Pure deterministic computation over already-committed Phase 7
statements, Phase 8 ratios, and Phase 5 prices. Nothing here invents
a value: a method whose inputs are missing, methodologically
unavailable, or point-in-time unverifiable is NOT_CALCULABLE (value
NULL, status recorded in the valuation row's assumptions JSON), never
zero, never an estimate. Computed values inherit the lowest input
quality (all production inputs today are UNVERIFIED, so every output
is UNVERIFIED too — never upgraded by calculation).

Valuation-date discipline (brief: historical validity): a
price-based method is point-in-time valid only when the statement it
uses was published on or before the valuation date. The valuation
date for price-based methods is the price date (2026-11-03, the only
trading date in the price set). Statement-only methods (book value)
carry the balance-sheet date as their valuation date and are labelled
statement-date values, not market fair values at the price date.

Phase 8 refinement, stated explicitly: Phase 8 recorded pe/pb/div_yield
as insufficient_inputs for all three companies for a combined reason
(single unadjusted close, no adjustment methodology, no share-count
data, price/publication misalignment). Phase 9 refines that ruling
per method instead of as a block:
  * trailing P/E needs only price / EPS — no share count — so it
    becomes computable where the EPS is positive AND the statement's
    publication date is known and on/before the valuation date
    (HUBC, OGDC). A single unadjusted official close is a valid
    point-in-time price; adjustment methodology matters for series,
    not for a single-date multiple.
  * P/B, P/S, market cap, enterprise value, EV multiples, cash-flow
    yield and dividend yield still need share counts (and DPS for
    the yield), which do not exist in the data — they stay
    NOT_CALCULABLE. This does not revise any Phase 8 row; Phase 8
    rows stand as Phase 8 scope, and Phase 9 rows carry their own
    method keys and applicability rulings.
  * NML trailing P/E stays NOT_CALCULABLE for two independent
    reasons: its nine-month EPS is negative (-0.42, non-meaningful
    multiple) AND its statements carry no publication date, so
    point-in-time validity cannot be verified.

Financial-company rule (brief): industrial enterprise-value DCF is
never applied to a bank, and residual-income models are bank
models. HBL (Habib Bank Limited) has no statements loaded (pending
PDF download, running separately), so it gets no valuation rows at
all — it is reported as PENDING, never as zero. Every structure
below accepts a 4th company by adding one PERIODS entry (reused from
Phase 8) and one price row; no redesign is needed.
"""

from __future__ import annotations

from datetime import date

VALUATION_VERSION = "1.0"

# The only trading date in the Phase 5 price set; the valuation date
# for every price-based method.
PRICE_DATE = date(2026, 11, 3)

# Company ids in the live registry (post-recovery numbering, as Phase 8).
HUBC = 289  # The Hub Power Company Limited — POWER GENERATION & DISTRIBUTION
NML = 394  # Nishat Mills Limited — TEXTILE COMPOSITE
OGDC = 403  # Oil & Gas Development Company Limited — OIL & GAS EXPLORATION
HBL = 277  # Habib Bank Limited — COMMERCIAL BANKS (PENDING input)

PENDING_COMPANIES = {HBL: "statements not yet loaded (HBL CY2025 PDF blocked at download)"}

# Method registry v1.0: (family, model, formula_text, unit).
# Families match the valuations.method vocabulary (Phase 3 model
# comment): multiples, dcf, dividend, asset_based, residual_income.
METHODS: dict[str, tuple[str, str, str, str]] = {
    # Relative valuation — price-based, valuation_date = PRICE_DATE.
    "multiples:pe_trailing": (
        "multiples",
        "pe_trailing",
        "close_price / EPS (EPS of the statement flow period)",
        "x",
    ),
    "multiples:pb": (
        "multiples",
        "pb",
        "close_price / book_value_per_share; needs shares outstanding",
        "x",
    ),
    "multiples:ps": (
        "multiples",
        "ps",
        "close_price / revenue_per_share; needs shares outstanding",
        "x",
    ),
    "multiples:ev_ebitda": (
        "multiples",
        "ev_ebitda",
        "enterprise_value / EBITDA; needs market cap and EBITDA",
        "x",
    ),
    "multiples:ev_ebit": (
        "multiples",
        "ev_ebit",
        "enterprise_value / EBIT; needs market cap",
        "x",
    ),
    "multiples:div_yield": (
        "multiples",
        "div_yield",
        "dividend_per_share / close_price; needs DPS",
        "ratio",
    ),
    "multiples:market_cap": (
        "multiples",
        "market_cap",
        "close_price x shares outstanding; needs shares outstanding",
        "PKR",
    ),
    "multiples:enterprise_value": (
        "multiples",
        "enterprise_value",
        "market_cap + interest_bearing_debt - cash; needs market cap",
        "PKR",
    ),
    "multiples:cf_yield": (
        "multiples",
        "cf_yield",
        "operating_cash_flow_per_share / close_price; needs shares outstanding",
        "ratio",
    ),
    "multiples:peer_median_pe": (
        "multiples",
        "peer_median_pe",
        "median trailing P/E of genuinely comparable peers (>=3 peers)",
        "x",
    ),
    # Intrinsic models — scenario/assumption-gated, valuation_date = PRICE_DATE.
    "dcf:fcff": (
        "dcf",
        "fcff",
        "PV of forecast FCFF + terminal value; needs WACC, growth, forecasts",
        "PKR",
    ),
    "dcf:fcfe": (
        "dcf",
        "fcfe",
        "PV of forecast FCFE + terminal value; needs cost of equity, growth, forecasts",
        "PKR",
    ),
    "dividend:ddm": (
        "dividend",
        "ddm",
        "Gordon: DPS x (1+g) / (r - g); needs DPS, growth, required return",
        "PKR",
    ),
    # Asset-based — statement-date values, valuation_date = balance-sheet date.
    "asset_based:equity_book_value_total": (
        "asset_based",
        "equity_book_value_total",
        "total_equity as printed on the balance sheet",
        "PKR",
    ),
    "asset_based:equity_book_value_owners": (
        "asset_based",
        "equity_book_value_owners",
        "equity_attributable_to_owners as printed on the balance sheet",
        "PKR",
    ),
    "asset_based:sum_of_parts": (
        "asset_based",
        "sum_of_parts",
        "sum of segment values; needs segment-level statements",
        "PKR",
    ),
    # Bank model — not applicable to industrials; HBL pending.
    "residual_income:bank": (
        "residual_income",
        "bank",
        "book_value + PV of residual income; bank-appropriate only",
        "PKR",
    ),
}

# Methods whose valuation_date is the balance-sheet date, not PRICE_DATE.
STATEMENT_DATE_METHODS = frozenset(
    {
        "asset_based:equity_book_value_total",
        "asset_based:equity_book_value_owners",
        "asset_based:sum_of_parts",
    }
)
