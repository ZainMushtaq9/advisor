"""Phase 21 alerts and event-driven monitoring: rule registry.

All alerting is derived from already-stored rows. Nothing here
fetches anything, generates a price, ratio, forecast, or
recommendation, or sends anything outside this machine. The
only deliverable channel is the in-app ledger itself.

As-of discipline mirrors the pipeline: the evaluation date is
2026-11-04 (the Phase 15 decision date) and the price date is
2026-11-03 (the single stored trading date). Event times are
the stored event dates at midnight Asia/Karachi; processing
time is the real run time, also Asia/Karachi. Both are stored
on every alert, so a trigger can always be reproduced.

Taxonomy coverage (one rule per category at minimum):
- price/volume thresholds: high_volume, price_move
- technical events: technical_event
- financial disclosures: earnings_disclosure
- dividend/corporate actions: dividend_declared
- news events: earnings_disclosure (seed news events), macro_release
- valuation changes: valuation_change
- macro releases: macro_release
- data failures: risk_flag_raised (its market flags cover
  missing tickers, absent previous close / turnover, and zero
  technical coverage) plus the suppressed-reason counts
- risk breaches: risk_flag_raised, control_breach

Rules that cannot fire on current data are still defined and
evaluated; they produce suppressed counts with reasons, never
invented alerts:
- dividend_declared: all 5 stored dividend actions carry NULL
  announced/ex/record/payment dates, so no event date exists.
- valuation_change: only one valuation run exists, so no
  change over time is computable.
- technical_event: Phase 6 holds 0 calculable values.
- price_move: previous_close is NULL on all 444 price rows.

An alert is a notification about a stored event. It is not an
investment opportunity, not a recommendation, and not a
forecast: Phase 15 user-facing values are WITHHELD and Phase
13 forecasts are abstained, and this phase reintroduces
neither. No order path exists anywhere in this project.
"""

from __future__ import annotations

ALERT_AS_OF = "2026-11-04"
PRICE_DATE = "2026-11-03"
TIMEZONE = "Asia/Karachi"

DISCLAIMER = (
    "Alerts notify about stored events only. They are not investment "
    "opportunities, not recommendations, and not forecasts. Phase 15 "
    "user-facing values are WITHHELD and Phase 13 forecasts are abstained; "
    "this phase reintroduces neither. Delivery is in-app only: no email, "
    "SMS, push, or paid service is used, and no external message is sent."
)

# Severity mapping for Phase 14 risk flags: a flag's own severity
# becomes the alert severity unchanged (info -> INFO,
# warning -> WARNING). No flag is upgraded.
FLAG_SEVERITY_MAP = {"info": "INFO", "warning": "WARNING"}

SEED_RULES = [
    {
        "rule_key": "macro_release",
        "name": "Macro release",
        "version": "v1",
        "category": "MACRO_RELEASE",
        "origin": "OFFICIAL",
        "severity": "INFO",
        "trigger": {"source": "macro_events", "scheduled_included": False},
        "description": (
            "One alert per past macro event (SBP/PBS) on or before the "
            "evaluation date. Future scheduled events do not fire."
        ),
        "max_event_age_days": 30,
        "daily_limit": None,
    },
    {
        "rule_key": "earnings_disclosure",
        "name": "Earnings disclosure",
        "version": "v1",
        "category": "FINANCIAL_DISCLOSURE",
        "origin": "OFFICIAL",
        "severity": "INFO",
        "trigger": {"source": "news_events", "event_type": "earnings"},
        "description": (
            "One alert per earnings news event with a known publication "
            "date inside the age window. Dateless events are suppressed "
            "as UNKNOWN_DATE; over-age events as STALE."
        ),
        "max_event_age_days": 90,
        "daily_limit": None,
    },
    {
        "rule_key": "risk_flag_raised",
        "name": "Risk flag raised",
        "version": "v1",
        "category": "RISK_BREACH",
        "origin": "MODEL_WARNING",
        "severity": "MAPPED",
        "trigger": {"source": "risk_flags"},
        "description": (
            "One alert per stored risk flag, severity mapped from the "
            "flag itself. Flags are review-only: never fraud, default, "
            "or solvency conclusions."
        ),
        "max_event_age_days": 30,
        "daily_limit": None,
    },
    {
        "rule_key": "control_breach",
        "name": "Control breach",
        "version": "v1",
        "category": "RISK_BREACH",
        "origin": "MODEL_WARNING",
        "severity": "CRITICAL",
        "trigger": {"source": "risk_control_checks", "outcome": "breach"},
        "description": (
            "One alert per breached risk control check. The seed breach "
            "is on the SIMULATED reference portfolio only, never a real "
            "holding."
        ),
        "max_event_age_days": 30,
        "daily_limit": None,
    },
    {
        "rule_key": "high_volume",
        "name": "High volume",
        "version": "v1",
        "category": "PRICE_VOLUME_THRESHOLD",
        "origin": "DERIVED",
        "severity": "INFO",
        "trigger": {"source": "market_prices", "volume_at_least": 1000000},
        "description": (
            "One alert per security whose stored 2026-11-03 volume is at "
            "or above 1,000,000 shares. A point-in-time threshold on the "
            "single stored trading date, not a move or a spike."
        ),
        "max_event_age_days": 7,
        "daily_limit": 100,
    },
    {
        "rule_key": "dividend_declared",
        "name": "Dividend declared",
        "version": "v1",
        "category": "DIVIDEND_ACTION",
        "origin": "OFFICIAL",
        "severity": "INFO",
        "trigger": {"source": "corporate_action_records", "family": "DIVIDEND"},
        "description": (
            "One alert per dividend action with a known event date. "
            "The seed run fires none: all 5 stored actions carry NULL "
            "dates, and no date is invented for them."
        ),
        "max_event_age_days": 90,
        "daily_limit": None,
    },
    {
        "rule_key": "valuation_change",
        "name": "Valuation change",
        "version": "v1",
        "category": "VALUATION_CHANGE",
        "origin": "DERIVED",
        "severity": "INFO",
        "trigger": {"source": "valuations", "needs": "two_runs"},
        "description": (
            "One alert per valuation that changed between runs. The "
            "seed run fires none: only one valuation run exists, so "
            "no change over time is computable."
        ),
        "max_event_age_days": 30,
        "daily_limit": None,
    },
    {
        "rule_key": "technical_event",
        "name": "Technical event",
        "version": "v1",
        "category": "TECHNICAL_EVENT",
        "origin": "DERIVED",
        "severity": "INFO",
        "trigger": {"source": "technical_indicator_values", "needs": "calculable_value"},
        "description": (
            "One alert per new calculable technical signal. The seed "
            "run fires none: Phase 6 holds 0 calculable values."
        ),
        "max_event_age_days": 7,
        "daily_limit": None,
    },
    {
        "rule_key": "price_move",
        "name": "Price move",
        "version": "v1",
        "category": "PRICE_VOLUME_THRESHOLD",
        "origin": "DERIVED",
        "severity": "INFO",
        "trigger": {"source": "market_prices", "needs": "previous_close"},
        "description": (
            "One alert per security whose close moved beyond threshold "
            "against its previous close. The seed run fires none: "
            "previous_close is NULL on all 444 price rows."
        ),
        "max_event_age_days": 7,
        "daily_limit": None,
    },
]

RULE_BY_KEY = {rule["rule_key"]: rule for rule in SEED_RULES}

DEFAULT_PREFERENCES = {
    "profile": "local",
    # Only in-app delivery is enabled. External channels are
    # recorded as disabled and external consent is False; the
    # delivery code refuses any other channel outright.
    "channels": {"in_app": True, "email": False, "sms": False, "push": False},
    "external_consent": False,
    # No quiet window in the seed profile, so seed alerts are
    # delivered immediately. Quiet-window handling is implemented
    # and fixture-tested; a window can be set on the profile row.
    "quiet_start": None,
    "quiet_end": None,
    "muted_rule_keys": [],
}
