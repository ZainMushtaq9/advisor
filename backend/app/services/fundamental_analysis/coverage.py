"""Calculability assessment for Phase 8 (mirrors Phase 6 coverage.py).

For one company-period, every registered metric gets exactly one
verdict: ``computed`` (a Decimal value), ``insufficient_inputs``
(value None + the exact missing input or methodological reason), or
``not_applicable`` (the metric has no meaning for this company's
structure — currently only OGDC interest coverage). No verdict ever
carries a substituted zero or an estimate.

``inputs`` is the canonical dict built by runner.load_period_inputs:
flow values carry ``_cur``/``_prior`` suffixes, balance-sheet points
likewise, ``period_days`` is the inclusive calendar day count of the
current flow period, and ``flags`` carries derivation notes (OGDC
derived cost, HUBC derived total liabilities). A missing canonical
input is simply absent or None.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.fundamental_analysis import NOT_APPLICABLE, formulas
from app.services.fundamental_analysis.formulas import avg, div, growth

D = Decimal


def _missing(inputs: dict, *names: str) -> list[str]:
    return [n for n in names if inputs.get(n) is None]


def _result(
    metric_key: str,
    value,
    missing: list[str],
    reason: str | None = None,
    flags: list[str] | None = None,
) -> dict:
    if value is None:
        return {
            "metric_key": metric_key,
            "status": "insufficient_inputs",
            "value": None,
            "reason": reason or f"missing inputs: {', '.join(missing)}",
            "flags": flags or [],
        }
    return {
        "metric_key": metric_key,
        "status": "computed",
        "value": value,
        "reason": None,
        "flags": flags or [],
    }


def _na(metric_key: str, reason: str) -> dict:
    return {
        "metric_key": metric_key,
        "status": "not_applicable",
        "value": None,
        "reason": reason,
        "flags": [],
    }


def assess(company_id: int, inputs: dict) -> list[dict]:
    """Assess every registered metric for one company-period."""
    g = inputs.get
    days = inputs.get("period_days") or 0
    derived_cost = bool(inputs.get("cost_derived"))
    cost_flags = ["cost_derived_from_sales_minus_gross_profit"] if derived_cost else []
    out: list[dict] = []

    def missing(*names: str) -> list[str]:
        return _missing(inputs, *names)

    # ---- Profitability ----
    gross_margin = div(g("gross_cur"), g("revenue_cur"))
    out.append(_result("gross_margin", gross_margin, missing("gross_cur", "revenue_cur")))
    if g("op_cur") is None and (("operating_margin", company_id) in NOT_APPLICABLE):
        out.append(_na("operating_margin", NOT_APPLICABLE[("operating_margin", company_id)]))
    else:
        out.append(
            _result(
                "operating_margin",
                div(g("op_cur"), g("revenue_cur")),
                missing("op_cur", "revenue_cur"),
                reason=(
                    "no operating-profit line in the extracted statements"
                    if g("op_cur") is None
                    else None
                ),
            )
        )
    out.append(
        _result(
            "net_margin", div(g("pat_cur"), g("revenue_cur")), missing("pat_cur", "revenue_cur")
        )
    )
    out.append(
        _result(
            "roa",
            div(g("pat_cur"), avg(g("ta_cur"), g("ta_prior"))),
            missing("pat_cur", "ta_cur", "ta_prior"),
        )
    )
    out.append(
        _result(
            "roe_total",
            div(g("pat_cur"), avg(g("te_cur"), g("te_prior"))),
            missing("pat_cur", "te_cur", "te_prior"),
        )
    )
    out.append(
        _result(
            "roe_owners",
            div(g("owners_profit_cur"), avg(g("oe_cur"), g("oe_prior"))),
            missing("owners_profit_cur", "oe_cur", "oe_prior"),
            reason=(
                "no owners-attributable profit line in the extracted statements"
                if g("owners_profit_cur") is None
                else None
            ),
        )
    )
    cap_cur = cap_prior = None
    if g("te_cur") is not None and g("ib_cur") is not None:
        cap_cur = g("te_cur") + g("ib_cur")
    if g("te_prior") is not None and g("ib_prior") is not None:
        cap_prior = g("te_prior") + g("ib_prior")
    if g("op_cur") is None and (("roce", company_id) in NOT_APPLICABLE):
        out.append(_na("roce", NOT_APPLICABLE[("roce", company_id)]))
    else:
        out.append(
            _result(
                "roce",
                div(g("op_cur"), avg(cap_cur, cap_prior)),
                missing("op_cur", "te_cur", "ib_cur", "te_prior", "ib_prior"),
                reason=(
                    "no operating-profit line in the extracted statements"
                    if g("op_cur") is None
                    else None
                ),
            )
        )
    out.append(
        _result(
            "roic",
            None,
            [],
            reason=(
                "NOPAT needs a validated tax allocation; operating profit "
                "includes post-tax associate earnings for HUBC, so a "
                "group-rate NOPAT would misstate. Formula reserved, not estimated."
            ),
        )
    )

    # ---- Liquidity ----
    out.append(_result("current_ratio", div(g("ca_cur"), g("cl_cur")), missing("ca_cur", "cl_cur")))
    inv_cur = g("inv_cur")
    quick = None
    if g("ca_cur") is not None and inv_cur is not None and g("cl_cur") not in (None, 0):
        quick = (g("ca_cur") - inv_cur) / g("cl_cur")
    out.append(_result("quick_ratio", quick, missing("ca_cur", "inv_cur", "cl_cur")))
    out.append(
        _result("cash_ratio", div(g("cash_cur"), g("cl_cur")), missing("cash_cur", "cl_cur"))
    )

    # ---- Leverage ----
    out.append(
        _result("debt_to_assets", div(g("tl_cur"), g("ta_cur")), missing("tl_cur", "ta_cur"))
    )
    out.append(
        _result("debt_to_equity", div(g("tl_cur"), g("te_cur")), missing("tl_cur", "te_cur"))
    )
    out.append(
        _result("ib_debt_to_equity", div(g("ib_cur"), g("te_cur")), missing("ib_cur", "te_cur"))
    )
    if ("interest_coverage", company_id) in NOT_APPLICABLE:
        out.append(_na("interest_coverage", NOT_APPLICABLE[("interest_coverage", company_id)]))
    else:
        fin = g("fin_cur")
        out.append(
            _result(
                "interest_coverage",
                div(g("op_cur"), abs(fin) if fin is not None else None),
                missing("op_cur", "fin_cur"),
                reason=(
                    "no finance-cost line in the extracted statements" if fin is None else None
                ),
            )
        )

    # ---- Efficiency ----
    out.append(
        _result(
            "receivables_days",
            formulas.days_metric(avg(g("td_cur"), g("td_prior")), g("revenue_cur"), days),
            missing("td_cur", "td_prior", "revenue_cur"),
        )
    )
    cost_cur = g("cost_cur")
    cost_abs = abs(cost_cur) if cost_cur is not None else None
    out.append(
        _result(
            "inventory_days",
            formulas.days_metric(avg(g("inv_cur"), g("inv_prior")), cost_abs, days),
            missing("inv_cur", "inv_prior", "cost_cur"),
            flags=cost_flags,
        )
    )
    out.append(
        _result(
            "payables_days",
            formulas.days_metric(avg(g("pay_cur"), g("pay_prior")), cost_abs, days),
            missing("pay_cur", "pay_prior", "cost_cur"),
            flags=cost_flags,
        )
    )
    out.append(
        _result(
            "receivables_turnover",
            div(g("revenue_cur"), avg(g("td_cur"), g("td_prior"))),
            missing("revenue_cur", "td_cur", "td_prior"),
        )
    )

    # ---- Growth (same-length comparison only) ----
    for key, cur, prior in (
        ("revenue_growth", g("revenue_cur"), g("revenue_prior")),
        ("pat_growth", g("pat_cur"), g("pat_prior")),
        ("eps_growth", g("eps_cur"), g("eps_prior")),
        ("assets_growth", g("ta_cur"), g("ta_prior")),
        ("equity_growth", g("te_cur"), g("te_prior")),
    ):
        flags = ["sign_change"] if formulas.sign_changed(cur, prior) else []
        miss = [n for n, v in (("current", cur), ("prior", prior)) if v is None]
        out.append(
            _result(
                key,
                growth(cur, prior),
                miss,
                reason=("zero prior-period denominator" if prior == 0 else None),
                flags=flags,
            )
        )

    # ---- Cash flow ----
    ocf = g("ocf_cur")
    out.append(_result("ocf", ocf, missing("ocf_cur")))
    capex = g("capex_cur")
    fcf = None if ocf is None or capex is None else ocf + capex
    out.append(_result("fcf", fcf, missing("ocf_cur", "capex_cur")))
    conv = div(ocf, g("pat_cur"))
    conv_flags = (
        ["both_negative_do_not_interpret_as_strength"]
        if ocf is not None and g("pat_cur") is not None and ocf < 0 and g("pat_cur") < 0
        else []
    )
    out.append(_result("cash_conversion", conv, missing("ocf_cur", "pat_cur"), flags=conv_flags))
    div_paid = g("div_cur")
    out.append(
        _result(
            "dividend_cash_coverage",
            div(ocf, abs(div_paid) if div_paid is not None else None),
            missing("ocf_cur", "div_cur"),
        )
    )
    accruals = None
    if g("pat_cur") is not None and ocf is not None:
        accruals = g("pat_cur") - ocf
    out.append(_result("accruals", accruals, missing("pat_cur", "ocf_cur")))

    # ---- Earnings quality ----
    out.append(
        _result(
            "accruals_to_pat",
            div(accruals, abs(g("pat_cur")) if g("pat_cur") is not None else None),
            missing("pat_cur", "ocf_cur"),
        )
    )
    gm_prior = div(g("gross_prior"), g("revenue_prior"))
    gm_change = None
    if gross_margin is not None and gm_prior is not None:
        gm_change = (gross_margin - gm_prior) * D(100)
    out.append(
        _result(
            "gross_margin_change_pp",
            gm_change,
            missing("gross_cur", "revenue_cur", "gross_prior", "revenue_prior"),
        )
    )
    td_growth = growth(g("td_cur"), g("td_prior"))
    rev_growth = growth(g("revenue_cur"), g("revenue_prior"))
    divergence = None
    if td_growth is not None and rev_growth is not None:
        divergence = (td_growth - rev_growth) * D(100)
    out.append(
        _result(
            "receivables_divergence_pp",
            divergence,
            missing("td_cur", "td_prior", "revenue_cur", "revenue_prior"),
        )
    )
    out.append(
        _result(
            "inventory_growth_pct",
            growth(g("inv_cur"), g("inv_prior")),
            missing("inv_cur", "inv_prior"),
        )
    )

    # ---- Market multiples: NOT_CALCULABLE in v1.0 (see conventions). ----
    out.append(
        _result(
            "pe_ratio",
            None,
            [],
            reason=(
                "single unadjusted close (2026-11-03); no corporate-action "
                "adjustment methodology; price date not aligned to statement "
                "publication; interim EPS for NML/OGDC"
            ),
        )
    )
    out.append(
        _result(
            "pb_ratio",
            None,
            [],
            reason=(
                "book value per share needs a share count, which no extracted "
                "statement provides; same price limitations as pe_ratio"
            ),
        )
    )
    out.append(
        _result(
            "dividend_yield",
            None,
            [],
            reason=(
                "needs dividends per share (needs a share count) and an "
                "aligned adjusted price; neither is available"
            ),
        )
    )

    return out
