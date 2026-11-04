"""Explainable financial-health profile, method health-v1.

NOT A CREDIT RATING. NOT INVESTMENT ADVICE. NOT A BUY/SELL SIGNAL.
Each dimension (profitability, liquidity, solvency, efficiency,
cash_flow, growth, earnings_quality) scores 0–100 from the computed
ratios against the published bands below; a dimension with no
computable input scores NULL (INSUFFICIENT_DATA), never zero. No
single aggregate grade is produced — deliberately: a single grade
would masquerade as a rating. The 'sector' category likewise carries
no numeric score, only the sector-profile evidence.

Sub-scores are banded 100 / 60 / 20 / 0 (see BANDS). A dimension
score is the equal-weighted mean of its available sub-scores, with
the inputs, bands, and any flag (e.g. receivables divergence capping
earnings_quality at 60) recorded in the evidence JSON so any reader
can reproduce the score from the ratio values alone.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.fundamental_analysis import HEALTH_METHOD_VERSION

D = Decimal

DISCLAIMER = (
    "Descriptive profile only. NOT a credit rating, NOT investment "
    "advice, and NOT a buy/sell signal. Scores describe the computed "
    "ratios against the published bands in health_method_v1.md; they "
    "do not predict solvency, default, or future performance."
)

# Bands for higher-is-better metrics: list of (lower bound
# inclusive, score), highest first. A value below every bound takes
# 0 for return/growth metrics and 20 otherwise (see band_score).
# Lower-is-better metrics live in INVERTED, not here.
BANDS: dict[str, list[tuple[Decimal, int]]] = {
    "net_margin": [(D("0.10"), 100), (D(0), 60)],
    "roa": [(D("0.10"), 100), (D(0), 60)],
    "roe_total": [(D("0.15"), 100), (D(0), 60)],
    "current_ratio": [(D(2), 100), (D(1), 60)],
    "quick_ratio": [(D(1), 100), (D("0.5"), 60)],
    "cash_ratio": [(D("0.5"), 100), (D("0.2"), 60)],
    "interest_coverage": [(D(3), 100), (D("1.5"), 60)],
    "dividend_cash_coverage": [(D("1.5"), 100), (D(1), 60)],
    "revenue_growth": [(D("0.10"), 100), (D(0), 60)],
    "pat_growth": [(D("0.10"), 100), (D(0), 60)],
    "eps_growth": [(D("0.10"), 100), (D(0), 60)],
}

# Inverted bands: score 100 at or below the first bound, 60 at or
# below the second, 20 above it.
INVERTED: dict[str, list[tuple[Decimal, int]]] = {
    "debt_to_assets": [(D("0.4"), 100), (D("0.6"), 60)],
    "debt_to_equity": [(D(1), 100), (D(2), 60)],
    "receivables_days": [(D(60), 100), (D(120), 60)],
    "inventory_days": [(D(90), 100), (D(180), 60)],
    "accruals_to_pat": [(D("0.25"), 100), (D("0.5"), 60)],
    "gross_margin_change_pp": [(D(2), 100), (D(5), 60)],
}

DIMENSIONS: dict[str, list[str]] = {
    "profitability": ["net_margin", "roa", "roe_total"],
    "liquidity": ["current_ratio", "quick_ratio", "cash_ratio"],
    "solvency": ["debt_to_assets", "debt_to_equity", "interest_coverage"],
    "efficiency": ["receivables_days", "inventory_days"],
    "cash_flow": ["cash_conversion", "dividend_cash_coverage", "fcf_sign"],
    "growth": ["revenue_growth", "pat_growth", "eps_growth"],
    "earnings_quality": ["accruals_to_pat", "gross_margin_change_pp"],
}


def band_score(metric_key: str, value) -> int | None:
    """Band a ratio value to 100/60/20/0. None when value is None."""
    if value is None:
        return None
    v = Decimal(str(value))
    if metric_key in INVERTED:
        bands = INVERTED[metric_key]
        for bound, score in bands:
            if (
                abs(v) <= bound
                if metric_key in ("accruals_to_pat", "gross_margin_change_pp")
                else v <= bound
            ):
                return score
        return 20
    if metric_key == "cash_conversion":
        if D("0.8") <= v <= D("1.2"):
            return 100
        if (D("0.5") <= v < D("0.8")) or (D("1.2") < v <= D("1.5")):
            return 60
        return 20
    bands = BANDS.get(metric_key)
    if bands is None:
        return None
    for bound, score in bands:
        if v >= bound:
            return score
    # Below every bound: 0 for return/growth metrics, 20 otherwise.
    if metric_key in (
        "net_margin",
        "roa",
        "roe_total",
        "revenue_growth",
        "pat_growth",
        "eps_growth",
    ):
        return 0
    return 20


def score_dimensions(values: dict[str, Decimal | None], flags: dict[str, list[str]]) -> dict:
    """Score every dimension from computed metric values.

    ``values`` maps metric_key -> Decimal or None; ``flags`` maps
    metric_key -> flag list (from coverage results). Returns
    {category: {"score": Decimal|None, "evidence": {...}}}.
    """
    results: dict = {}
    for category, keys in DIMENSIONS.items():
        subs: dict[str, int] = {}
        for key in keys:
            if key == "fcf_sign":
                fcf = values.get("fcf")
                if fcf is not None:
                    subs[key] = 100 if fcf > 0 else 20
                continue
            if (
                key == "cash_conversion"
                and "both_negative_do_not_interpret_as_strength" in flags.get("cash_conversion", [])
            ):
                if values.get("cash_conversion") is not None:
                    subs[key] = 20  # both-negative ratio is not strength
                continue
            s = band_score(key, values.get(key))
            if s is not None:
                subs[key] = s
        score = None
        if subs:
            score = (D(sum(subs.values())) / D(len(subs))).quantize(D("0.0001"))
        evidence = {
            "method_version": HEALTH_METHOD_VERSION,
            "sub_scores": subs,
            "disclaimer": DISCLAIMER,
        }
        if category == "earnings_quality":
            div_pp = values.get("receivables_divergence_pp")
            if div_pp is not None and div_pp > D(10) and score is not None and score > 60:
                score = D(60)
                evidence["capped_at_60"] = (
                    "receivables grew faster than revenue by more than 10pp; "
                    "quality dimension capped pending review"
                )
            evidence["receivables_divergence_pp"] = str(div_pp) if div_pp is not None else None
        results[category] = {"score": score, "evidence": evidence}
    # Sector category: never scored; evidence only.
    results["sector"] = {
        "score": None,
        "evidence": {
            "method_version": HEALTH_METHOD_VERSION,
            "note": "Sector applicability is descriptive (see sector_profiles.md); "
            "no numeric sector score is assigned.",
            "disclaimer": DISCLAIMER,
        },
    }
    return results
