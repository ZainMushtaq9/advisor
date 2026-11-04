"""Earnings-quality and review flags for Phase 8.

A warning is a FLAG FOR REVIEW, never proof of fraud, insolvency,
or distress. Every warning carries its evidence values and this
disclaimer in the stored evidence JSON. Severities are "warning"
(negative earnings or cash flow) and "info" (structural or
interpretive notes). No warning ever changes a ratio value.
"""

from __future__ import annotations

from decimal import Decimal

D = Decimal

FLAG_NOTE = (
    "Flag for review only — not proof of fraud, insolvency, or "
    "distress. See the run report for the full evidence."
)


def build_warnings(values: dict, results: list[dict]) -> list[dict]:
    """Derive warning events from computed values + coverage results.

    ``values`` maps metric_key -> Decimal or None; ``results`` is the
    coverage list (for flags such as sign_change).
    """
    flags_by_key = {r["metric_key"]: r.get("flags", []) for r in results}
    v = values.get
    warnings: list[dict] = []

    def add(warning_type: str, severity: str, evidence: dict) -> None:
        evidence["note"] = FLAG_NOTE
        warnings.append({"warning_type": warning_type, "severity": severity, "evidence": evidence})

    # PAT and OCF are levels, not ratio metrics: the runner passes
    # them through as _pat_cur / _ocf_cur for flag rules.
    pat = values.get("_pat_cur")
    ocf = values.get("_ocf_cur")
    if pat is not None and pat < 0:
        add("negative_profit_after_tax", "warning", {"pat": str(pat)})
    if ocf is not None and ocf < 0:
        add("negative_operating_cash_flow", "warning", {"ocf": str(ocf)})
    if "sign_change" in flags_by_key.get("pat_growth", []):
        add(
            "pat_growth_sign_change",
            "info",
            {"pat_growth": str(v("pat_growth"))},
        )
    if "sign_change" in flags_by_key.get("eps_growth", []):
        add(
            "eps_growth_sign_change",
            "info",
            {"eps_growth": str(v("eps_growth"))},
        )
    if "both_negative_do_not_interpret_as_strength" in flags_by_key.get("cash_conversion", []):
        add(
            "cash_conversion_both_negative",
            "info",
            {
                "cash_conversion": str(v("cash_conversion")),
                "explanation": "OCF and PAT are both negative, so the ratio is "
                "arithmetically positive but economically meaningless.",
            },
        )
    conv = v("cash_conversion")
    if (
        conv is not None
        and ocf is not None
        and pat is not None
        and ocf > 0
        and pat > 0
        and conv < D("0.5")
    ):
        add(
            "low_cash_conversion",
            "info",
            {
                "cash_conversion": str(conv),
                "accruals": str(v("accruals")),
                "explanation": "Operating cash covers less than half of profit; "
                "the gap is accruals and non-cash earnings, not an error.",
            },
        )
    recv_days = v("receivables_days")
    if recv_days is not None and recv_days > 365:
        add(
            "receivables_days_over_one_year",
            "info",
            {
                "receivables_days": str(recv_days),
                "explanation": "Average receivables exceed a full year of revenue; "
                "in regulated energy this typically reflects settlement "
                "receivables, but the pattern is flagged for review.",
            },
        )
    div_pp = v("receivables_divergence_pp")
    if div_pp is not None and div_pp > D(10):
        add(
            "receivables_growing_faster_than_revenue",
            "info",
            {
                "receivables_divergence_pp": str(div_pp),
                "explanation": "Trade debts grew faster than revenue by more than "
                "10 percentage points; flagged for review.",
            },
        )
    cov = v("interest_coverage")
    if cov is not None and cov < D("1.5"):
        add(
            "interest_coverage_below_1_5x",
            "warning",
            {"interest_coverage": str(cov)},
        )
    return warnings
