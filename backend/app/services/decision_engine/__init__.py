"""Phase 15 decision rules v1 and constants.

Everything here is definition, not data: no row is written from
this module, and no threshold is hidden. Rules v1 is deliberately
conservative because of what the pipeline actually holds:

- Technical evidence is ABSENT for every company (Phase 6: 0
  calculable values, technical coverage 0/470), so the technical
  dimension never scores in this run.
- Forecasts are not a dimension at all: Phase 13 abstained on all
  120 assessments, so forecast evidence contributes nothing, and
  calibration is NOT_ESTABLISHED. A proposal must never be
  generated from an abstained forecast as if it were computed.
- Every company input is UNVERIFIED, which caps confidence at LOW
  in v1. The MEDIUM and HIGH confidence rules are defined but
  unreachable in this run, and the user-facing recommendation is
  therefore WITHHELD for every company. That is the rule working,
  not a failure to decide: screening and research conclusions are
  still recorded with full evidence.
- News events are informational, never directional, in v1: no
  expectations data exists, so an earnings event cannot be scored
  as a surprise. It scores 0 (present, neutral) when its date is
  known, ABSENT when its date is unknown.
- Macro is a uniform context dimension in v1: the tightening
  regime (2026-11-04) scores -1 for every company. It is recorded
  as a headwind, not as company-specific evidence, and it cannot
  by itself flip a conclusion.
- Risk scores from severity, not from count: warning-severity risk
  flags score -1; info-only flags score 0 but are listed as
  evidence. Flags never infer fraud, default or solvency.
- Weights are equal (1 each) in v1. Weighted aggregation is a
  future rule version, not an invented number.

Conclusion mapping (total = sum of scored dimensions, ABSENT
excluded; gates evaluated first):
  BUY_CANDIDATE:  total >= +3 AND fundamentals +1 AND valuation +1
  SELL_CANDIDATE: total <= -3 AND fundamentals -1
  HOLD_CANDIDATE: >= 5 scored dimensions and total in [-2, +2]
  WATCHLIST:      3-4 scored dimensions
  INSUFFICIENT_EVIDENCE: any blocking gate, or < 3 scored dimensions

Blocking gates (any one forces INSUFFICIENT_EVIDENCE):
  no_statements:            no statement rows for the company
  stale_latest_statement:   latest period end > 365 days before the
                            decision date (Phase 14 threshold)
  publication_date_unknown: latest statement publication date NULL
                            (no-look-ahead cannot be verified)
  valuation_publication_unknown: a computed valuation's input
                            statement publication date NULL
  too_few_dimensions:       fewer than 3 scored dimensions

Confidence (categorical, from measured factors only — no invented
probabilities):
  HIGH:   inputs VERIFIED, calibration established, completeness
          7/7, agreement >= 0.80, no unresolved conflicts
  MEDIUM: inputs at least PARTIALLY_VERIFIED, calibration
          established, completeness >= 6/7, agreement >= 0.66
  LOW:    anything else with a conclusion (this run: UNVERIFIED
          inputs + calibration NOT_ESTABLISHED cap every
          conclusion at LOW)
  NONE:   no conclusion (gated)

Agreement for a directional conclusion (BUY/SELL) is the share of
scored dimensions that do not contradict its direction; for a
neutral conclusion (HOLD/WATCHLIST) no dimension contradicts, so
agreement is 1 minus the share of non-zero scored dimensions
that pull in either direction — recorded, not used to upgrade
confidence beyond the caps above.

Evidence precedence (selection precedence for conflicts, not
score overriding — conflicts are preserved as unresolved
disagreements in the decision record):
  1. audited statements over interim statements
  2. newer publication over older publication
  3. official sources (SBP/PBS) over issuer documents over press
  4. domain applicability: banking rules are never applied to
     industrials, nor industrial ratios blindly to a bank
"""

from __future__ import annotations

DECISION_DATE = "2026-11-04"
PRICE_DATE = "2026-11-03"
RULES_VERSION = "decision-rules-v1"
STALE_DAYS = 365
N_DIMENSIONS = 7

DIMENSIONS = (
    "fundamentals",
    "valuation",
    "technical",
    "news_event",
    "macro",
    "liquidity",
    "risk",
)

# Dimension scoring rules, as stored in decision_rules.dimensions.
DIMENSION_RULES = {
    "fundamentals": (
        "+1 when profitability >= 70 and solvency >= 70 and no "
        "negative-profit-after-tax warning; -1 when a "
        "negative-profit-after-tax warning exists or profitability "
        "is 0; else 0. Health scores come from Phase 8 rows."
    ),
    "valuation": (
        "+1 when trailing P/E is computed and < 10; 0 when computed "
        "and in [10, 25]; -1 when computed and > 25; ABSENT when "
        "trailing P/E is not computed. Book values are evidence, "
        "not a scored input, in v1."
    ),
    "technical": (
        "ABSENT whenever technical coverage is 0 (Phase 6: 0 "
        "calculable values). No technical score exists in this run."
    ),
    "news_event": (
        "0 (present, neutral, informational) when an earnings event "
        "with a known date exists; ABSENT when the event date is "
        "unknown or no event exists. Never directional in v1: no "
        "expectations data exists, so no surprise can be scored."
    ),
    "macro": (
        "-1 under the tightening regime (2026-11-04, regime-v1), "
        "uniform for every company; 0 otherwise; ABSENT when no "
        "regime row exists."
    ),
    "liquidity": (
        "+1 when the Phase 14 volume liquidity tier is HIGH; 0 "
        "when MEDIUM; -1 when LOW; ABSENT when no tier row exists."
    ),
    "risk": (
        "-1 when any warning-severity risk flag exists for the "
        "company; 0 when only info-severity flags exist or no "
        "flags exist. Flags are review-only, never fraud, default "
        "or solvency conclusions."
    ),
}

WEIGHTS_V1 = {dimension: 1 for dimension in DIMENSIONS}

THRESHOLDS_V1 = {
    "buy_min_total": 3,
    "sell_max_total": -3,
    "hold_min_scored": 5,
    "hold_total_low": -2,
    "hold_total_high": 2,
    "watchlist_min_scored": 3,
    "watchlist_max_scored": 4,
    "pe_cheap_below": 10,
    "pe_expensive_above": 25,
    "health_strong_at": 70,
}

GATES_V1 = {
    "no_statements": "No statement rows for the company.",
    "stale_latest_statement": (
        "Latest statement period end is more than 365 days before the decision date."
    ),
    "publication_date_unknown": (
        "Latest statement publication date is NULL, so the no-look-ahead check cannot be verified."
    ),
    "valuation_publication_unknown": (
        "A computed valuation's input statement publication date "
        "is NULL, so the valuation cannot be placed in time."
    ),
    "too_few_dimensions": "Fewer than 3 scored dimensions.",
}

PRECEDENCE_V1 = {
    "audit_status": "Audited statements take precedence over interim statements.",
    "recency": "Newer publication takes precedence over older publication.",
    "source_reliability": (
        "Official sources (SBP/PBS) take precedence over issuer "
        "documents, which take precedence over press."
    ),
    "domain_applicability": (
        "Banking rules are never applied to industrials, nor industrial ratios blindly to a bank."
    ),
    "conflict_handling": (
        "Precedence selects which evidence is used; it never "
        "overrides a score. Remaining disagreements are preserved "
        "as unresolved conflicts in the decision record."
    ),
}

CONFIDENCE_RULES_V1 = {
    "high_requires": (
        "Inputs VERIFIED, calibration established, completeness "
        "7/7, agreement >= 0.80, no unresolved conflicts."
    ),
    "medium_requires": (
        "Inputs at least PARTIALLY_VERIFIED, calibration "
        "established, completeness >= 6/7, agreement >= 0.66."
    ),
    "low_rule": (
        "Any conclusion not meeting MEDIUM: in this run every "
        "conclusion is LOW because all inputs are UNVERIFIED and "
        "calibration is NOT_ESTABLISHED (Phase 13 abstained)."
    ),
    "user_facing_requires": (
        "A research conclusion AND confidence at least MEDIUM; otherwise WITHHELD with its reason."
    ),
}

# Companies in the analysis universe for this run: the three
# statement companies plus HBL (pending its Phase 7 load, recorded
# as an explicit abstention, not as missing output).
UNIVERSE_TICKERS = ("HUBC", "NML", "OGDC", "HBL")
