"""Phase 20 screener: filter registry and seed screens.

Filter semantics (the brief's "documented calculation
semantics"):

- An ABSOLUTE filter compares a stored value against a
  threshold with one operator (>=, <=, >, <, ==). The value is
  read from stored rows only; a NULL value never becomes a
  number — it becomes a MISSING_VALUE (or NOT_CALCULABLE for
  technical indicators, which have zero calculable rows)
  outcome that is excluded from scoring.
- A PERCENTILE filter ranks a security's stored value among
  its peer set: percentile = (peers with a strictly smaller
  present value) / (peers with any present value). The peer
  set is always named in the outcome evidence: price/volume
  percentiles rank among the 444 priced securities; ratio
  percentiles rank among the statement companies with a
  computed value (at most 3). A percentile over a peer set of
  one is 0.0 by definition and is flagged as a degenerate
  peer set, never hidden.
- A PRESENCE filter passes when at least one linked row
  exists (a dividend action, a news event, a risk flag).
- SECTOR APPLICABILITY: filters marked "industrial_only"
  (ratios, margins, valuation multiples) return
  NOT_APPLICABLE for COMMERCIAL BANKS securities: industrial
  ratio semantics must not be applied blindly to a bank
  (Phase 8 banking rule). A non-bank company without a
  computed value returns MISSING_VALUE, not NOT_APPLICABLE —
  absence of data and inapplicability are different reasons
  and are never conflated.
- STALENESS is an evidence flag, never a silent adjustment:
  a statement older than 365 days at the screen as-of date
  carries STALE_INPUT in the result's reason codes.

Ranking (score version "screener-score-v1"): score =
passed / scored, where scored counts only filters with a
pass or fail outcome. A security MATCHES when every scored
filter passes and at least one filter was scored; a security
with zero scored filters is INSUFFICIENT_DATA, never a
match. Scores are explainable: every result carries its
per-filter outcomes, values, source row references, and
quality. A screen match is NOT an investment opportunity,
NOT a recommendation, and NOT a forecast — the response
disclaimer says so on every surface, and Phase 15 decision
context (research conclusion, WITHHELD user-facing value)
rides along as evidence only, never as a score input.

Universes: "priced" = all 470 registry securities (444 with
a 2026-11-03 price, 26 without — the missing 26 are results
too, with MISSING_VALUE reasons); "decision_companies" =
the 4 securities with a Phase 15 decision (HUBC, NML, OGDC,
HBL), which is the only universe where fundamental,
valuation, dividend, and decision-context filters have any
coverage.
"""

from __future__ import annotations

SCORE_VERSION = "screener-score-v1"
SCREEN_AS_OF = "2026-11-04"
PRICE_DATE = "2026-11-03"

# filter_key -> spec. "source" names the stored table the value
# is read from; "unit" is the documented unit; "kinds" lists
# the threshold kinds the filter supports.
FILTER_REGISTRY: dict[str, dict] = {
    # Price / volume (source: market_prices, 2026-11-03).
    "close_price": {
        "category": "price",
        "unit": "PKR",
        "source": "market_prices",
        "sector_applicability": "all",
        "kinds": ("absolute", "percentile"),
        "description": "Official close on 2026-11-03 (unadjusted).",
    },
    "volume": {
        "category": "volume",
        "unit": "shares",
        "source": "market_prices",
        "sector_applicability": "all",
        "kinds": ("absolute", "percentile"),
        "description": "Traded volume on 2026-11-03.",
    },
    "price_present": {
        "category": "price",
        "unit": "boolean",
        "source": "market_prices",
        "sector_applicability": "all",
        "kinds": ("presence",),
        "description": "A 2026-11-03 price row exists for the security.",
    },
    "volume_share_pct": {
        "category": "liquidity",
        "unit": "pct",
        "source": "liquidity_observations",
        "sector_applicability": "all",
        "kinds": ("absolute", "percentile"),
        "description": "Share of total 2026-11-03 market volume (Phase 12).",
    },
    # Fundamentals (source: fundamental_metric_values, latest
    # computed row per company). Industrial only.
    "roe_total": {
        "category": "ratio",
        "unit": "ratio",
        "source": "fundamental_metric_values",
        "sector_applicability": "industrial_only",
        "kinds": ("absolute", "percentile"),
        "description": "Return on equity (total), latest computed period.",
    },
    "roa": {
        "category": "ratio",
        "unit": "ratio",
        "source": "fundamental_metric_values",
        "sector_applicability": "industrial_only",
        "kinds": ("absolute", "percentile"),
        "description": "Return on assets, latest computed period.",
    },
    "net_margin": {
        "category": "ratio",
        "unit": "ratio",
        "source": "fundamental_metric_values",
        "sector_applicability": "industrial_only",
        "kinds": ("absolute", "percentile"),
        "description": "Net margin, latest computed period.",
    },
    "gross_margin": {
        "category": "ratio",
        "unit": "ratio",
        "source": "fundamental_metric_values",
        "sector_applicability": "industrial_only",
        "kinds": ("absolute", "percentile"),
        "description": "Gross margin, latest computed period.",
    },
    "current_ratio": {
        "category": "ratio",
        "unit": "x",
        "source": "fundamental_metric_values",
        "sector_applicability": "industrial_only",
        "kinds": ("absolute", "percentile"),
        "description": "Current ratio, latest computed period.",
    },
    "receivables_days": {
        "category": "ratio",
        "unit": "days",
        "source": "fundamental_metric_values",
        "sector_applicability": "industrial_only",
        "kinds": ("absolute", "percentile"),
        "description": "Receivables days, latest computed period.",
    },
    "debt_to_equity": {
        "category": "leverage",
        "unit": "ratio",
        "source": "fundamental_metric_values",
        "sector_applicability": "industrial_only",
        "kinds": ("absolute", "percentile"),
        "description": "Debt to equity, latest computed period.",
    },
    # Valuation (source: valuations, method key as filter key).
    "pe_trailing": {
        "category": "valuation",
        "unit": "x",
        "source": "valuations",
        "sector_applicability": "industrial_only",
        "kinds": ("absolute", "percentile"),
        "description": "Trailing P/E (Phase 9 multiples:pe_trailing).",
    },
    # Dividend (source: corporate_action_records).
    "dividend_per_share": {
        "category": "dividend",
        "unit": "PKR",
        "source": "corporate_action_records",
        "sector_applicability": "all",
        "kinds": ("presence", "absolute"),
        "description": "Latest stored dividend per share; all stored "
        "actions carry NULL dates — dates_unknown is flagged "
        "in evidence, never invented.",
    },
    # News / event (source: news_events via news_event_companies
    # and primary_company_id).
    "news_event_present": {
        "category": "news_event",
        "unit": "boolean",
        "source": "news_events",
        "sector_applicability": "all",
        "kinds": ("presence",),
        "description": "At least one company-linked news event exists.",
    },
    # Risk (source: risk_flags).
    "risk_flag_present": {
        "category": "risk",
        "unit": "boolean",
        "source": "risk_flags",
        "sector_applicability": "all",
        "kinds": ("presence",),
        "description": "At least one review-only risk flag exists. "
        "Flags are never fraud, default, or solvency findings.",
    },
    # Staleness (derived from statement period ends).
    "statement_age_days": {
        "category": "freshness",
        "unit": "days",
        "source": "financial_statements",
        "sector_applicability": "all",
        "kinds": ("absolute",),
        "description": "Days from latest statement period end to the "
        "screen as-of date. Over 365 days also raises the "
        "STALE_INPUT reason code.",
    },
    # Technical (source: technical_indicator_values). Zero
    # calculable rows exist (Phase 6), so every evaluation is
    # NOT_CALCULABLE with its reason — registered to prove
    # null handling, never to fabricate a value.
    "sma_5": {
        "category": "technical",
        "unit": "PKR",
        "source": "technical_indicator_values",
        "sector_applicability": "all",
        "kinds": ("absolute", "percentile", "presence"),
        "description": "5-day simple moving average. NOT_CALCULABLE: "
        "0 calculable values; 5 closes are needed and only "
        "1 trading date exists.",
    },
    "rsi_14": {
        "category": "technical",
        "unit": "points",
        "source": "technical_indicator_values",
        "sector_applicability": "all",
        "kinds": ("absolute", "percentile", "presence"),
        "description": "14-period RSI. NOT_CALCULABLE: 0 calculable "
        "values; 15 observations are needed and only 1 "
        "trading date exists.",
    },
}

# Seed screens, version v1. Each filter entry: {"filter": key,
# "kind": "absolute"|"percentile"|"presence", "op": ..., "value": ...}.
# Presence filters take no op/value.
SEED_SCREENS: tuple[dict, ...] = (
    {
        "name": "liquid_leaders",
        "version": "v1",
        "description": "Priced securities with a 2026-11-03 close and "
        "volume of at least 100,000 shares.",
        "universe": "priced",
        "filters": [
            {"filter": "price_present", "kind": "presence"},
            {"filter": "volume", "kind": "absolute", "op": ">=", "value": 100000},
        ],
    },
    {
        "name": "volume_top_decile",
        "version": "v1",
        "description": "Securities in the top volume decile among the "
        "444 priced securities (percentile >= 90).",
        "universe": "priced",
        "filters": [
            {"filter": "volume", "kind": "percentile", "op": ">=", "value": 90},
        ],
    },
    {
        "name": "cheap_profitable",
        "version": "v1",
        "description": "Statement companies with trailing P/E below 10 "
        "and positive total ROE. OGDC's P/E is a 6-month "
        "interim-period multiple, labelled as such in "
        "evidence; NML's P/E is missing (negative EPS and "
        "unknown publication date), so NML cannot match.",
        "universe": "decision_companies",
        "filters": [
            {"filter": "pe_trailing", "kind": "absolute", "op": "<", "value": 10},
            {"filter": "roe_total", "kind": "absolute", "op": ">", "value": 0},
        ],
    },
    {
        "name": "dividend_payers",
        "version": "v1",
        "description": "Companies with at least one stored dividend "
        "action. All stored actions carry NULL dates, so "
        "every match carries the dates_unknown quality flag.",
        "universe": "decision_companies",
        "filters": [
            {"filter": "dividend_per_share", "kind": "presence"},
        ],
    },
    {
        "name": "technical_momentum",
        "version": "v1",
        "description": "Securities with a computed 5-day moving average. "
        "Expected result: zero matches — Phase 6 holds 0 "
        "calculable technical values, so every outcome is "
        "NOT_CALCULABLE. This screen exists to prove null "
        "handling, not to find momentum.",
        "universe": "priced",
        "filters": [
            {"filter": "sma_5", "kind": "presence"},
        ],
    },
)

DISCLAIMER = (
    "Screen matches are filter results over stored rows, not "
    "investment opportunities, not recommendations, and not "
    "forecasts. Nothing here is investment advice, a buy/sell "
    "signal, or a guaranteed outcome. Phase 15 user-facing "
    "values are WITHHELD and Phase 13 forecasts are abstained; "
    "this screener does not reintroduce either. No order path "
    "exists anywhere in this project."
)
