"""Phase 22 report template registry and shared constants.

A report is a descriptive/analytical document assembled only
from already-stored rows. It is never investment advice, never
a buy/sell signal presented as executable, never a forecast
presented as fact, and never a price target. There is no
price_target figure kind anywhere in this package: a builder
that tried to emit one is rejected by evidence.figure().

Fixed pipeline dates (see the Phase 22 run report for why
each is what it is):
  REPORT_DATE = 2026-11-04 — the date the reports are
      generated (also the Phase 15 decision date and the
      Phase 21 alert as-of date).
  DATA_CUTOFF_DATE = 2026-11-04 — the latest date for which
      any stored observation exists. No stored row postdates
      it except SCHEDULED future events, which appear only in
      explicitly labelled "scheduled / upcoming" sections,
      never as occurred.
  PRICE_DATE = 2026-11-03 — the single trading date with
      stored prices (444 rows).
Currency is PKR throughout; statement amounts are in
Rs '000s unless a figure note says otherwise.
"""

from __future__ import annotations

from datetime import date

REPORT_DATE = date(2026, 11, 4)
DATA_CUTOFF_DATE = date(2026, 11, 4)
PRICE_DATE = date(2026, 11, 3)

DISCLAIMER = (
    "INTERNAL RESEARCH DOCUMENT — NOT INVESTMENT ADVICE. "
    "This report assembles figures already stored in the PSX "
    "Intelligence platform; it introduces no new market data. "
    "Every figure inherits its inputs' quality status (all "
    "statement, price, ratio, valuation, macro, news, "
    "ownership, forecast, risk, decision, portfolio, backtest, "
    "screen, and alert inputs in this run are UNVERIFIED unless "
    "a figure note says otherwise). Screen matches are filter "
    "results, not investment opportunities. Phase 15 "
    "user-facing values are WITHHELD and Phase 13 forecasts "
    "are abstained; neither is reintroduced here. No price "
    "target is stated anywhere in this report, and no section "
    "recommends a trade. This report is not published "
    "externally; APPROVED means internally reviewed only."
)

FIGURE_KINDS = (
    "sourced_fact",
    "deterministic_calculation",
    "model_output",
    "analyst_inference",
    "assumption",
)

COMPUTATION_STATUSES = (
    "computed",
    "insufficient_inputs",
    "not_applicable",
)

TEMPLATES = {
    "company_dossier": {
        "title": "Company Dossier",
        "audience": "internal_research",
        "sections": [
            ("executive_summary", "Executive summary"),
            ("thesis", "Thesis"),
            ("counter_thesis", "Counter-thesis"),
            ("financial_snapshot", "Financial snapshot"),
            ("valuation", "Valuation"),
            ("risks", "Risks"),
            ("catalysts", "Catalysts"),
            ("uncertainty", "Uncertainty"),
            ("monitoring", "Monitoring items"),
            ("disclosures", "Methodology, sources and disclosures"),
        ],
        "methodology": (
            "Figures are pulled from stored Phase 5 prices, "
            "Phase 7 statements, Phase 8 ratios and health, "
            "Phase 9 valuations, Phase 10 macro context, Phase "
            "11 news events, Phase 12 ownership and actions, "
            "Phase 14 risk flags, Phase 15 decisions, Phase 20 "
            "screen outcomes, and Phase 21 alerts. No figure is "
            "estimated; a missing input yields an "
            "insufficient_inputs figure with its reason."
        ),
    },
    "earnings_update": {
        "title": "Earnings Update",
        "audience": "internal_research",
        "sections": [
            ("executive_summary", "Executive summary"),
            ("results", "Reported results"),
            ("thesis", "Thesis"),
            ("counter_thesis", "Counter-thesis"),
            ("risks", "Risks"),
            ("uncertainty", "Uncertainty"),
            ("monitoring", "Monitoring items"),
            ("disclosures", "Methodology, sources and disclosures"),
        ],
        "methodology": (
            "Income-statement lines are taken from the latest "
            "stored statement period only. Cumulative interim "
            "columns and standalone quarters are never mixed, "
            "no annualisation is applied, and no trailing "
            "twelve-month figure is synthesised. A publication "
            "date of NULL is reported as unknown, never "
            "guessed."
        ),
    },
    "valuation_report": {
        "title": "Valuation Report",
        "audience": "internal_research",
        "sections": [
            ("executive_summary", "Executive summary"),
            ("methods", "Valuation methods"),
            ("scenarios", "Valuation scenarios"),
            ("thesis", "Thesis"),
            ("counter_thesis", "Counter-thesis"),
            ("risks", "Risks"),
            ("uncertainty", "Uncertainty"),
            ("disclosures", "Methodology, sources and disclosures"),
        ],
        "methodology": (
            "Each Phase 9 method stands alone with its own "
            "inputs and reason; incompatible methods are never "
            "averaged. Book values are statement-date, "
            "company-level values, not market fair values and "
            "not per-share values. Scenarios list computed "
            "methods and unavailable methods with reasons; "
            "they never state a target price."
        ),
    },
    "sector_outlook": {
        "title": "Sector Outlook",
        "audience": "internal_research",
        "sections": [
            ("executive_summary", "Executive summary"),
            ("coverage", "Coverage"),
            ("thesis", "Thesis"),
            ("counter_thesis", "Counter-thesis"),
            ("risks", "Risks"),
            ("uncertainty", "Uncertainty"),
            ("monitoring", "Monitoring items"),
            ("disclosures", "Methodology, sources and disclosures"),
        ],
        "methodology": (
            "Sector membership comes from the Phase 4 "
            "registry; breadth comes from Phase 12 market "
            "breadth rows; macro context comes from Phase 10. "
            "A sector with one statement company is described "
            "as such, never as sector-wide evidence."
        ),
    },
    "event_brief": {
        "title": "Event Brief",
        "audience": "internal_research",
        "sections": [
            ("executive_summary", "Executive summary"),
            ("event", "Event"),
            ("thesis", "Thesis"),
            ("counter_thesis", "Counter-thesis"),
            ("risks", "Risks"),
            ("uncertainty", "Uncertainty"),
            ("monitoring", "Monitoring items"),
            ("disclosures", "Methodology, sources and disclosures"),
        ],
        "methodology": (
            "Events are Phase 10 macro events or Phase 11 news "
            "events already stored. Future-dated events appear "
            "only as scheduled items, never as occurred. An "
            "event with an unknown date is labelled unknown, "
            "never dated by guesswork."
        ),
    },
    "portfolio_review": {
        "title": "Portfolio Review",
        "audience": "internal_research",
        "sections": [
            ("executive_summary", "Executive summary"),
            ("holdings", "Holdings"),
            ("exclusions", "Exclusions"),
            ("comparison", "Comparison"),
            ("thesis", "Thesis"),
            ("counter_thesis", "Counter-thesis"),
            ("risks", "Risks"),
            ("uncertainty", "Uncertainty"),
            ("disclosures", "Methodology, sources and disclosures"),
        ],
        "methodology": (
            "Portfolios are Phase 16 SIMULATED portfolios on "
            "hypothetical capital, never real holdings. "
            "Holdings plus cash reconcile to the stated "
            "capital. Returns are insufficient_inputs: one "
            "price date yields zero return observations, and "
            "no return is invented."
        ),
    },
    "risk_report": {
        "title": "Risk Report",
        "audience": "internal_research",
        "sections": [
            ("executive_summary", "Executive summary"),
            ("metrics", "Risk metrics"),
            ("controls", "Controls"),
            ("stress", "Stress scenarios"),
            ("thesis", "Thesis"),
            ("counter_thesis", "Counter-thesis"),
            ("uncertainty", "Uncertainty"),
            ("disclosures", "Methodology, sources and disclosures"),
        ],
        "methodology": (
            "Metrics, flags, controls, and stress results are "
            "Phase 14 rows, reproduced with their computation "
            "statuses. Flags are review-only: they are never "
            "fraud, default, or solvency conclusions. Stress "
            "impacts are simulation arithmetic on stored "
            "closes only, never forecasts."
        ),
    },
    "market_overview": {
        "title": "Market Overview",
        "audience": "internal_research",
        "sections": [
            ("executive_summary", "Executive summary"),
            ("breadth", "Market breadth"),
            ("macro", "Macro context"),
            ("screens", "Screen outcomes"),
            ("decisions", "Decision context"),
            ("alerts", "Alert context"),
            ("thesis", "Thesis"),
            ("counter_thesis", "Counter-thesis"),
            ("risks", "Risks"),
            ("uncertainty", "Uncertainty"),
            ("disclosures", "Methodology, sources and disclosures"),
        ],
        "methodology": (
            "Breadth is Phase 12 market breadth for "
            "2026-11-03; macro is Phase 10; screens are Phase "
            "20; decisions are Phase 15; alerts are Phase 21. "
            "Advances/declines and turnover are absent because "
            "previous_close and turnover are NULL on all "
            "stored price rows; the absence is stated, never "
            "filled."
        ),
    },
}
