"""Phase 15 pure decision scoring functions.

No database access here: every function takes plain values and
returns plain values, so the rules are testable without a database
and hand-checkable against the run report. No probabilities are
invented: confidence is categorical and derived only from
measured completeness, calibration status, source quality and
agreement. No score is ever produced from a missing input — a
missing input yields ABSENT (None), never zero-filled.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.decision_engine import THRESHOLDS_V1

# Sentinel: a dimension with no computable evidence. ABSENT
# dimensions are excluded from totals and from completeness
# numerators, never counted as 0.
ABSENT = None


def fundamentals_score(
    profitability: Decimal | None,
    solvency: Decimal | None,
    has_negative_pat_warning: bool,
) -> int | None:
    """Score the fundamentals dimension from Phase 8 health rows."""
    if profitability is None or solvency is None:
        return ABSENT
    if has_negative_pat_warning or profitability == 0:
        return -1
    if (
        profitability >= THRESHOLDS_V1["health_strong_at"]
        and solvency >= THRESHOLDS_V1["health_strong_at"]
    ):
        return 1
    return 0


def valuation_score(pe_trailing: Decimal | None) -> int | None:
    """Score the valuation dimension from the computed trailing P/E."""
    if pe_trailing is None:
        return ABSENT
    if pe_trailing < THRESHOLDS_V1["pe_cheap_below"]:
        return 1
    if pe_trailing > THRESHOLDS_V1["pe_expensive_above"]:
        return -1
    return 0


def news_score(event_date_known: bool) -> int | None:
    """News is informational, never directional, in v1."""
    if not event_date_known:
        return ABSENT
    return 0


def macro_score(regime_label: str | None) -> int | None:
    """Macro is uniform context in v1: tightening is a headwind."""
    if regime_label is None:
        return ABSENT
    if regime_label == "tightening":
        return -1
    return 0


def liquidity_score(tier: str | None) -> int | None:
    """Score the liquidity dimension from the Phase 14 tier."""
    if tier is None:
        return ABSENT
    if tier == "HIGH":
        return 1
    if tier == "LOW":
        return -1
    return 0


def risk_score(has_warning_severity_flag: bool) -> int:
    """Score the risk dimension from flag severity, not count."""
    return -1 if has_warning_severity_flag else 0


def aggregate(scores: dict[str, int | None]) -> tuple[int, int]:
    """Return (total, scored_count), excluding ABSENT dimensions."""
    scored = [value for value in scores.values() if value is not ABSENT]
    return sum(scored), len(scored)


def map_conclusion(scores: dict[str, int | None], gate_reasons: list[str]) -> str:
    """Map dimension scores to a research conclusion.

    Gates are evaluated first: any gate forces
    INSUFFICIENT_EVIDENCE regardless of scores. Otherwise the
    v1 thresholds apply exactly as documented in the rule set.
    """
    if gate_reasons:
        return "INSUFFICIENT_EVIDENCE"
    total, scored = aggregate(scores)
    fundamentals = scores.get("fundamentals")
    valuation = scores.get("valuation")
    if total >= THRESHOLDS_V1["buy_min_total"] and fundamentals == 1 and valuation == 1:
        return "BUY_CANDIDATE"
    if total <= THRESHOLDS_V1["sell_max_total"] and fundamentals == -1:
        return "SELL_CANDIDATE"
    if (
        scored >= THRESHOLDS_V1["hold_min_scored"]
        and THRESHOLDS_V1["hold_total_low"] <= total <= THRESHOLDS_V1["hold_total_high"]
    ):
        return "HOLD_CANDIDATE"
    if THRESHOLDS_V1["watchlist_min_scored"] <= scored <= THRESHOLDS_V1["watchlist_max_scored"]:
        return "WATCHLIST"
    return "INSUFFICIENT_EVIDENCE"


def completeness(scored: int, n_dimensions: int = 7) -> Decimal:
    """Measured completeness: scored dimensions over all dimensions."""
    return Decimal(scored) / Decimal(n_dimensions)


def agreement(scores: dict[str, int | None], conclusion: str) -> Decimal | None:
    """Measured agreement for a conclusion, or None when gated.

    For a directional conclusion, agreement is the share of scored
    dimensions that do not contradict its direction. For a neutral
    conclusion (HOLD/WATCHLIST), no dimension contradicts, so
    agreement is 1 minus the share of non-zero scored dimensions
    that pull in either direction. For INSUFFICIENT_EVIDENCE there
    is no conclusion to agree with, so agreement is None.
    """
    if conclusion == "INSUFFICIENT_EVIDENCE":
        return None
    scored = [value for value in scores.values() if value is not ABSENT]
    if not scored:
        return None
    if conclusion == "BUY_CANDIDATE":
        contradicting = sum(1 for value in scored if value == -1)
        return Decimal(len(scored) - contradicting) / Decimal(len(scored))
    if conclusion == "SELL_CANDIDATE":
        contradicting = sum(1 for value in scored if value == 1)
        return Decimal(len(scored) - contradicting) / Decimal(len(scored))
    nonzero = sum(1 for value in scored if value != 0)
    return Decimal(len(scored) - nonzero) / Decimal(len(scored))


def confidence(
    conclusion: str,
    completeness_value: Decimal,
    agreement_value: Decimal | None,
    inputs_quality: str,
    calibration_established: bool,
    unresolved_conflicts: int,
) -> str:
    """Categorical confidence from measured factors only.

    HIGH and MEDIUM are defined but unreachable in this run:
    every input is UNVERIFIED and calibration is NOT_ESTABLISHED
    (Phase 13 abstained on every target). Any conclusion that
    does not meet MEDIUM is LOW; a gated company has NONE.
    """
    if conclusion == "INSUFFICIENT_EVIDENCE":
        return "NONE"
    if (
        inputs_quality == "VERIFIED"
        and calibration_established
        and completeness_value == 1
        and agreement_value is not None
        and agreement_value >= Decimal("0.80")
        and unresolved_conflicts == 0
    ):
        return "HIGH"
    if (
        inputs_quality in ("VERIFIED", "PARTIALLY_VERIFIED")
        and calibration_established
        and completeness_value >= Decimal(6) / Decimal(7)
        and agreement_value is not None
        and agreement_value >= Decimal("0.66")
    ):
        return "MEDIUM"
    return "LOW"


def user_facing(conclusion: str, confidence_value: str) -> tuple[str, str]:
    """Map a research conclusion to the user-facing value.

    Issued only when a conclusion exists and confidence is at
    least MEDIUM; otherwise WITHHELD with its reason. In this run
    every value is WITHHELD.
    """
    if conclusion == "INSUFFICIENT_EVIDENCE":
        return "WITHHELD", "No research conclusion exists (abstained)."
    if confidence_value in ("MEDIUM", "HIGH"):
        return conclusion, "Research conclusion meets the confidence bar."
    return (
        "WITHHELD",
        f"Research conclusion {conclusion} held back: confidence "
        f"{confidence_value} is below MEDIUM.",
    )
