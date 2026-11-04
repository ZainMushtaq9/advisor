"""Phase 8 fundamental-analysis tests (pure: no real database, no network).

Fixtures use the real Phase 7 statement values (thousands scale;
units cancel in ratios). Expected values were computed independently
from the same inputs and are asserted within a small tolerance for
averaging rounding. NOT_CALCULABLE is asserted as status + reason,
never as a zero value.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.fundamental_analysis import coverage, formulas, health, warnings

D = Decimal
TOL = D("0.0001")
DAYS_TOL = D("0.05")


def _close(actual, expected, tol=TOL) -> bool:
    return actual is not None and abs(actual - D(str(expected))) <= tol


def _by_key(results: list[dict]) -> dict[str, dict]:
    return {r["metric_key"]: r for r in results}


# ---------------------------------------------------------------------------
# Fixtures (canonical inputs, stored signs: costs/finance/capex/dividends
# negative as printed).
# ---------------------------------------------------------------------------

HUBC_INPUTS = {
    "revenue_cur": D(71126352),
    "revenue_prior": D(83351492),
    "cost_cur": D(-41438192),
    "gross_cur": D(29688160),
    "gross_prior": D(39823888),
    "op_cur": D(34067964),
    "fin_cur": D(-9135708),
    "pat_cur": D(56257178),
    "pat_prior": D(51774561),
    "owners_profit_cur": D(49630724),
    "eps_cur": D("38.26"),
    "eps_prior": D("35.56"),
    "ocf_cur": D(11428574),
    "capex_cur": D(-935016),
    "div_cur": D(-40790850),
    "ca_cur": D(94552627),
    "cl_cur": D(66722726),
    "cash_cur": D(25823657),
    "inv_cur": D(8635912),
    "inv_prior": D(6182121),
    "td_cur": D(32430708),
    "td_prior": D(28966134),
    "pay_cur": D(31675404),
    "pay_prior": D(34677770),
    "ta_cur": D(422563444),
    "ta_prior": D(414722187),
    "te_cur": D(258007509),
    "te_prior": D(243921905),
    "oe_cur": D(235381655),
    "oe_prior": D(219708081),
    "ib_cur": D(72557148),
    "ib_prior": D(84298688),
    "tl_cur": D(164555935),
    "period_days": 365,
}

NML_INPUTS = {
    "revenue_cur": D(155948666),
    "revenue_prior": D(159350195),
    "cost_cur": D(-131744417),
    "gross_cur": D(24204249),
    "gross_prior": D(24794147),
    "op_cur": D(10537986),
    "fin_cur": D(-6893009),
    "pat_cur": D(-1182815),
    "pat_prior": D(7993455),
    "eps_cur": D("-0.42"),
    "eps_prior": D("17.36"),
    "ocf_cur": D(-5371036),
    "capex_cur": D(-8189954),
    "div_cur": D(-2607008),
    "ca_cur": D(138022156),
    "cl_cur": D(101014972),
    "cash_cur": D(11572794),
    "inv_cur": D(81386854),
    "inv_prior": D(58728562),
    "td_cur": D(26540042),
    "td_prior": D(38376196),
    "pay_cur": D(20868132),
    "pay_prior": D(19827841),
    "ta_cur": D(293132889),
    "ta_prior": D(273706356),
    "te_cur": D(159920849),
    "te_prior": D(157847811),
    "oe_cur": D(146538114),
    "oe_prior": D(141869200),
    "ib_cur": D(98375990),
    "ib_prior": D(84342331),
    "tl_cur": D(133212040),
    "period_days": 274,
}

OGDC_INPUTS = {
    "revenue_cur": D(192829894),
    "revenue_prior": D(206423219),
    "cost_cur": D(89372173),
    "cost_derived": True,
    "gross_cur": D(103457821),
    "gross_prior": D(127413076),
    "op_cur": None,
    "fin_cur": None,
    "pat_cur": D(73019248),
    "pat_prior": D(82456666),
    "eps_cur": D("16.98"),
    "eps_prior": D("19.17"),
    "ocf_cur": D(50012941),
    "capex_cur": D(-53939528),
    "div_cur": D(-36562090),
    "ca_cur": D(1113550304),
    "cl_cur": D(115736065),
    "cash_cur": D(11442518),
    "inv_cur": D(30646771),
    "inv_prior": D(30636306),
    "td_cur": D(583823689),
    "td_prior": D(613660983),
    "pay_cur": D(114121985),
    "pay_prior": D(123761613),
    "ta_cur": D(1686617216),
    "ta_prior": D(1654605970),
    "te_cur": D(1383637471),
    "te_prior": D(1348236596),
    "ib_cur": D(2537103),
    "ib_prior": D(3039610),
    "tl_cur": D(302979745),
    "period_days": 184,
}


def test_formulas_never_return_zero_substitutes() -> None:
    assert formulas.div(10, 0) is None
    assert formulas.div(None, 5) is None
    assert formulas.div(10, None) is None
    assert formulas.growth(10, 0) is None
    assert formulas.avg(10, None) is None
    assert (
        formulas.period_days(
            __import__("datetime").date(2025, 7, 1), __import__("datetime").date(2026, 6, 30)
        )
        == 365
    )
    assert formulas.sign_changed(D(-1), D(5)) is True
    assert formulas.sign_changed(D(1), D(5)) is False


def test_hubc_fy2026_ratios_reconcile() -> None:
    r = _by_key(coverage.assess(289, HUBC_INPUTS))
    assert _close(r["gross_margin"]["value"], "0.417400")
    assert _close(r["operating_margin"]["value"], "0.478978")
    assert _close(r["net_margin"]["value"], "0.790947")
    assert _close(r["roa"]["value"], "0.134380")
    assert _close(r["roe_total"]["value"], "0.224164")
    assert _close(r["roe_owners"]["value"], "0.218114")
    assert _close(r["roce"]["value"], "0.103427")
    assert _close(r["current_ratio"]["value"], "1.417098")
    assert _close(r["quick_ratio"]["value"], "1.287668")
    assert _close(r["cash_ratio"]["value"], "0.387029")
    assert _close(r["debt_to_assets"]["value"], "0.389423")
    assert _close(r["debt_to_equity"]["value"], "0.637795")
    assert _close(r["ib_debt_to_equity"]["value"], "0.281221")
    assert _close(r["interest_coverage"]["value"], "3.729099")
    assert _close(r["receivables_days"]["value"], "157.535460", DAYS_TOL)
    assert _close(r["receivables_turnover"]["value"], "2.316938")
    assert _close(r["revenue_growth"]["value"], "-0.146670")
    assert _close(r["pat_growth"]["value"], "0.086580")
    assert _close(r["eps_growth"]["value"], "0.075928")
    assert r["fcf"]["value"] == D(10493558)
    assert _close(r["cash_conversion"]["value"], "0.203149")
    assert _close(r["dividend_cash_coverage"]["value"], "0.280175")
    assert r["accruals"]["value"] == D(44828604)
    assert r["roic"]["status"] == "insufficient_inputs"
    assert r["pe_ratio"]["status"] == "insufficient_inputs"
    assert r["pb_ratio"]["status"] == "insufficient_inputs"
    assert r["dividend_yield"]["status"] == "insufficient_inputs"


def test_nml_negative_earnings_reported_not_hidden() -> None:
    r = _by_key(coverage.assess(394, NML_INPUTS))
    assert r["net_margin"]["status"] == "computed"
    assert _close(r["net_margin"]["value"], "-0.007585")
    assert r["roa"]["value"] < 0
    assert _close(r["gross_margin"]["value"], "0.155207")
    assert _close(r["interest_coverage"]["value"], "1.528793")
    assert _close(r["cash_conversion"]["value"], "4.540893")
    assert "both_negative_do_not_interpret_as_strength" in r["cash_conversion"]["flags"]
    assert "sign_change" in r["pat_growth"]["flags"]
    assert "sign_change" in r["eps_growth"]["flags"]
    assert r["fcf"]["value"] == D(-13560990)


def test_ogdc_structural_gaps_are_not_applicable_or_insufficient() -> None:
    r = _by_key(coverage.assess(403, OGDC_INPUTS))
    assert r["operating_margin"]["status"] == "insufficient_inputs"
    assert "no operating-profit line" in r["operating_margin"]["reason"]
    assert r["interest_coverage"]["status"] == "not_applicable"
    assert r["roce"]["status"] == "insufficient_inputs"
    assert r["roe_owners"]["status"] == "insufficient_inputs"
    assert _close(r["gross_margin"]["value"], "0.536524")
    assert _close(r["net_margin"]["value"], "0.378672")
    assert _close(r["current_ratio"]["value"], "9.621463")
    assert _close(r["receivables_days"]["value"], "571.325336", DAYS_TOL)
    assert _close(r["cash_conversion"]["value"], "0.684928")
    assert "cost_derived_from_sales_minus_gross_profit" in r["inventory_days"]["flags"]


def test_health_bands_and_hubc_dimensions() -> None:
    assert health.band_score("net_margin", D("0.20")) == 100
    assert health.band_score("net_margin", D("0.05")) == 60
    assert health.band_score("net_margin", D("-0.01")) == 0
    assert health.band_score("current_ratio", D("0.9")) == 20
    assert health.band_score("debt_to_assets", D("0.7")) == 20
    assert health.band_score("cash_conversion", D("1.0")) == 100
    assert health.band_score("cash_conversion", D("0.3")) == 20
    results = coverage.assess(289, HUBC_INPUTS)
    values = {x["metric_key"]: x["value"] for x in results}
    flags = {x["metric_key"]: x.get("flags", []) for x in results}
    dims = health.score_dimensions(values, flags)
    assert dims["profitability"]["score"] == D("100.0000")
    assert dims["liquidity"]["score"] == D("73.3333")
    assert dims["solvency"]["score"] == D("100.0000")
    assert dims["efficiency"]["score"] == D("60.0000")
    assert dims["cash_flow"]["score"] == D("46.6667")
    assert dims["growth"]["score"] == D("40.0000")
    assert dims["earnings_quality"]["score"] == D("20.0000")
    assert dims["sector"]["score"] is None
    assert "NOT a credit rating" in dims["profitability"]["evidence"]["disclaimer"]


def test_warnings_flag_review_only() -> None:
    nml = coverage.assess(394, NML_INPUTS)
    vals = {x["metric_key"]: x["value"] for x in nml}
    vals["_pat_cur"] = NML_INPUTS["pat_cur"]
    vals["_ocf_cur"] = NML_INPUTS["ocf_cur"]
    types = {w["warning_type"] for w in warnings.build_warnings(vals, nml)}
    assert "negative_profit_after_tax" in types
    assert "negative_operating_cash_flow" in types
    assert "pat_growth_sign_change" in types
    assert "cash_conversion_both_negative" in types
    ogdc = coverage.assess(403, OGDC_INPUTS)
    ovals = {x["metric_key"]: x["value"] for x in ogdc}
    ovals["_pat_cur"] = OGDC_INPUTS["pat_cur"]
    ovals["_ocf_cur"] = OGDC_INPUTS["ocf_cur"]
    otypes = {w["warning_type"] for w in warnings.build_warnings(ovals, ogdc)}
    assert "receivables_days_over_one_year" in otypes
    for w in warnings.build_warnings(vals, nml):
        assert "not proof of fraud" in w["evidence"]["note"]


def test_fundamentals_endpoints_answer_503_without_db(client) -> None:
    resp = client.get("/api/v1/fundamentals/ratios", params={"ticker": "HUBC"})
    assert resp.status_code == 503
    resp = client.get("/api/v1/fundamentals/health", params={"ticker": "HUBC"})
    assert resp.status_code == 503
