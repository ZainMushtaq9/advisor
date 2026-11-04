"""Bias-audit checks for Phase 17 (pure functions over evidence).

Each check takes an evidence dict assembled by the runner from
stored rows and returns (result, evidence). Result vocabulary:
"no_bias_detected", "bias_disclosed", "not_applicable". A
bias_disclosed row is a finding, not a phase failure: the bias
is documented instead of being silently baked into a result.

Checks:
- point_in_time: every input used by a decision or construction
  must be dated on or before the decision date. Handled
  exceptions (inputs gated out, e.g. NML's unknown publication
  date) are listed in the evidence, not hidden.
- survivorship: the universe must retain all securities,
  including price-missing names; delisting data is a stated
  limitation when absent.
- selection: statement-driven strategies cover only the
  statement companies; the coverage fraction is reported.
- corporate_actions: dividend actions without dates cannot be
  applied, so price-based returns would carry dividend bias;
  the adjustment status is reported.
- stale_prices: single price date and stale statements are
  reported with their ages.
- missing_data: tickers without prices are named, never dropped.
- cost_sensitivity: with zero production trades, cost
  sensitivity is not_applicable in production (fixtures only).
"""

from __future__ import annotations


def check_point_in_time(evidence: dict) -> tuple[str, dict]:
    """No-look-ahead audit over dated inputs."""
    late = [item for item in evidence.get("inputs", []) if item.get("after_decision_date")]
    out = dict(evidence)
    out["late_inputs"] = late
    if late:
        return "bias_disclosed", out
    return "no_bias_detected", out


def check_survivorship(evidence: dict) -> tuple[str, dict]:
    """Universe retention audit."""
    dropped = evidence.get("dropped_securities", [])
    if dropped:
        return "bias_disclosed", evidence
    return "no_bias_detected", evidence


def check_selection(evidence: dict) -> tuple[str, dict]:
    """Coverage audit for statement-driven strategies."""
    covered = evidence.get("covered_companies", 0)
    universe = evidence.get("universe_companies", 0)
    if universe and covered < universe:
        return "bias_disclosed", evidence
    return "no_bias_detected", evidence


def check_corporate_actions(evidence: dict) -> tuple[str, dict]:
    """Dividend-action applicability audit."""
    if evidence.get("actions_without_dates", 0) > 0:
        return "bias_disclosed", evidence
    if evidence.get("actions_applied", 0) == 0 and evidence.get("actions_total", 0) > 0:
        return "bias_disclosed", evidence
    return "no_bias_detected", evidence


def check_stale_prices(evidence: dict) -> tuple[str, dict]:
    """Price-date and statement-freshness audit."""
    if evidence.get("price_dates", 0) <= 1:
        return "bias_disclosed", evidence
    if evidence.get("stale_statements", 0) > 0:
        return "bias_disclosed", evidence
    return "no_bias_detected", evidence


def check_missing_data(evidence: dict) -> tuple[str, dict]:
    """Missing-price audit; names are carried in the evidence."""
    if evidence.get("missing_tickers"):
        return "bias_disclosed", evidence
    return "no_bias_detected", evidence


def check_cost_sensitivity(evidence: dict) -> tuple[str, dict]:
    """Cost-sensitivity applicability audit."""
    if evidence.get("production_trades", 0) == 0:
        return "not_applicable", evidence
    return "no_bias_detected", evidence


CHECKS: dict[str, object] = {
    "point_in_time": check_point_in_time,
    "survivorship": check_survivorship,
    "selection": check_selection,
    "corporate_actions": check_corporate_actions,
    "stale_prices": check_stale_prices,
    "missing_data": check_missing_data,
    "cost_sensitivity": check_cost_sensitivity,
}
