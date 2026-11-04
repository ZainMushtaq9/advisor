"""Phase 9 valuation tests (pure: no real database, no network).

Expected values were computed independently from the same inputs
and are asserted within a small tolerance. NOT_CALCULABLE is
asserted as status + reason, never as a zero value. Production
figures used in fixtures are the real Phase 7/5 values: HUBC close
197.24 with EPS 38.26, OGDC close 303.63 with EPS 16.98, NML close
123.61 with nine-month EPS -0.42.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.valuation import coverage, formulas, peers

D = Decimal
TOL = D("0.0001")


def _close(actual, expected, tol=TOL) -> bool:
    return actual is not None and abs(actual - D(str(expected))) <= tol


def _by_key(results: list[dict]) -> dict[str, dict]:
    return {r["method_key"]: r for r in results}


def _base_inputs(**overrides) -> dict:
    inputs = {
        "company_id": 289,
        "ticker": "HUBC",
        "sector": "POWER GENERATION & DISTRIBUTION",
        "flow_frequency": "annual",
        "period_end": date(2026, 6, 30),
        "bs_date": date(2026, 6, 30),
        "price": D("197.24"),
        "price_date": date(2026, 11, 3),
        "eps": D("38.26"),
        "eps_period_label": "FY2026 annual (audited, consolidated)",
        "publication_date": date(2026, 9, 21),
        "total_equity": D("258007509000"),
        "owners_equity": D("235381655000"),
        "peers": [],
    }
    inputs.update(overrides)
    return inputs


# ---------------------------------------------------------------------------
# Formulas
# ---------------------------------------------------------------------------


def test_trailing_pe_hubc_hand_calculated():
    # 197.24 / 38.26 = 5.1552535... (independent Decimal computation).
    assert _close(formulas.trailing_pe(D("197.24"), D("38.26")), "5.1552535")


def test_trailing_pe_ogdc_hand_calculated():
    # 303.63 / 16.98 = 17.8816254...
    assert _close(formulas.trailing_pe(D("303.63"), D("16.98")), "17.8816254")


def test_trailing_pe_non_positive_eps_is_none():
    assert formulas.trailing_pe(D("123.61"), D("-0.42")) is None
    assert formulas.trailing_pe(D("123.61"), D("0")) is None
    assert formulas.trailing_pe(D("123.61"), None) is None


def test_price_sensitivity_hand_calculated():
    assert _close(formulas.price_sensitivity(D("197.24"), D("38.26"), D("-0.10")), "4.6397282")
    assert _close(formulas.price_sensitivity(D("197.24"), D("38.26"), D("0.10")), "5.6707789")


def test_dcf_fixture_hand_calculated():
    # Flows 100, 110, 121 at 10%; terminal growth 3% on the last flow:
    # TV = 121 x 1.03 / (0.10 - 0.03) = 1780.428571...;
    # PV = 90.909091 x 3 + 1780.428571 / 1.331 = 1610.389610...
    assert _close(
        formulas.dcf_value([D("100"), D("110"), D("121")], D("0.10"), D("0.03")),
        "1610.3896104",
    )


def test_dcf_terminal_growth_at_or_above_wacc_rejected():
    assert formulas.dcf_value([D("100")], D("0.10"), D("0.10")) is None
    assert formulas.dcf_value([D("100")], D("0.10"), D("0.12")) is None
    assert formulas.dcf_value([], D("0.10"), D("0.03")) is None
    assert formulas.dcf_value([D("100"), None], D("0.10"), D("0.03")) is None


def test_gordon_ddm_fixture():
    # 5 x 1.04 / (0.12 - 0.04) = 65 exactly.
    assert formulas.gordon_ddm(D("5"), D("0.04"), D("0.12")) == D("65")
    assert formulas.gordon_ddm(D("5"), D("0.12"), D("0.12")) is None


def test_residual_income_fixture():
    # 1000 + 50/1.1 + 55/1.21 = 1090.909090...
    assert _close(
        formulas.residual_income_value(D("1000"), [D("50"), D("55")], D("0.10")),
        "1090.9090909",
    )
    assert formulas.residual_income_value(D("1000"), [D("50")], D("0")) is None


def test_peer_median_needs_three_peers():
    assert formulas.peer_median([D("10"), D("12"), D("14")]) == D("12")
    assert formulas.peer_median([D("10"), D("12")]) is None
    assert formulas.peer_median([]) is None


# ---------------------------------------------------------------------------
# Coverage: production-shaped assessments
# ---------------------------------------------------------------------------


def test_hubc_assessment_computed_methods():
    by_key = _by_key(coverage.assess("HUBC", _base_inputs()))
    pe = by_key["multiples:pe_trailing"]
    assert pe["status"] == "computed"
    assert _close(pe["value"], "5.1552535")
    assert _close(pe["sensitivity"]["price_minus_10pct"], "4.6397282")
    assert _close(pe["sensitivity"]["price_plus_10pct"], "5.6707789")
    book = by_key["asset_based:equity_book_value_total"]
    assert book["status"] == "computed" and book["value"] == D("258007509000")
    owners = by_key["asset_based:equity_book_value_owners"]
    assert owners["status"] == "computed" and owners["value"] == D("235381655000")
    # Everything share-count or assumption gated stays NOT_CALCULABLE.
    for key in (
        "multiples:pb",
        "multiples:ps",
        "multiples:market_cap",
        "multiples:enterprise_value",
        "dcf:fcff",
        "dcf:fcfe",
        "dividend:ddm",
        "asset_based:sum_of_parts",
    ):
        assert by_key[key]["status"] == "insufficient_inputs", key
        assert by_key[key]["value"] is None, key
    assert by_key["residual_income:bank"]["status"] == "not_applicable"


def test_ogdc_assessment():
    by_key = _by_key(
        coverage.assess("OGDC",
            _base_inputs(
                ticker="OGDC",
                sector="OIL & GAS EXPLORATION COMPANIES",
                flow_frequency="half_yearly",
                period_end=date(2025, 12, 31),
                bs_date=date(2025, 12, 31),
                price=D("303.63"),
                eps=D("16.98"),
                publication_date=date(2026, 2, 23),
                total_equity=D("1383637471000"),
                owners_equity=None,
            ),
        )
    )
    assert by_key["multiples:pe_trailing"]["status"] == "computed"
    assert _close(by_key["multiples:pe_trailing"]["value"], "17.8816254")
    assert by_key["asset_based:equity_book_value_total"]["value"] == D("1383637471000")
    # No owners split on the extracted OGDC balance sheet.
    assert by_key["asset_based:equity_book_value_owners"]["status"] == "insufficient_inputs"


def test_nml_assessment_two_independent_pe_blocks():
    by_key = _by_key(
        coverage.assess("NML",
            _base_inputs(
                ticker="NML",
                sector="TEXTILE COMPOSITE",
                flow_frequency="nine_month",
                period_end=date(2025, 3, 31),
                bs_date=date(2025, 3, 31),
                price=D("123.61"),
                eps=D("-0.42"),
                publication_date=None,
                total_equity=D("159920849000"),
                owners_equity=D("146538114000"),
            ),
        )
    )
    pe = by_key["multiples:pe_trailing"]
    assert pe["status"] == "insufficient_inputs"
    assert pe["value"] is None
    assert "non-meaningful" in pe["reason"]
    # Book values still compute: they are statement-date values and
    # do not depend on publication dates or EPS.
    assert by_key["asset_based:equity_book_value_total"]["value"] == D("159920849000")


def test_look_ahead_publication_rejected():
    by_key = _by_key(
        coverage.assess("HUBC",
            _base_inputs(publication_date=date(2026, 12, 1)),
        )
    )
    pe = by_key["multiples:pe_trailing"]
    assert pe["status"] == "insufficient_inputs"
    assert "look-ahead" in pe["reason"]


def test_missing_publication_date_rejected_even_with_positive_eps():
    by_key = _by_key(coverage.assess("HUBC", _base_inputs(publication_date=None)))
    pe = by_key["multiples:pe_trailing"]
    assert pe["status"] == "insufficient_inputs"
    assert "point-in-time unverifiable" in pe["reason"]


def test_peer_rules():
    target = {
        "ticker": "HUBC",
        "sector": "POWER GENERATION & DISTRIBUTION",
        "reporting_frequency": "annual",
        "period_end": date(2026, 6, 30),
    }
    same_sector = {
        "ticker": "OTHER",
        "sector": "POWER GENERATION & DISTRIBUTION",
        "reporting_frequency": "annual",
        "period_end": date(2026, 6, 30),
    }
    other_sector = dict(same_sector, sector="TEXTILE COMPOSITE")
    other_freq = dict(same_sector, reporting_frequency="half_yearly")
    stale = dict(same_sector, period_end=date(2025, 6, 30))
    assert peers.select_peers(target, [same_sector]) == [same_sector]
    assert peers.select_peers(target, [other_sector]) == []
    assert peers.select_peers(target, [other_freq]) == []
    assert peers.select_peers(target, [stale]) == []
    assert peers.select_peers(target, [target]) == []
    kept, excluded = peers.apply_outlier_rule([D("10"), D("11"), D("12"), D("13"), D("100")])
    assert D("100") in excluded and len(kept) == 4
    kept, excluded = peers.apply_outlier_rule([D("10"), D("11"), D("100")])
    assert kept == [D("10"), D("11"), D("100")] and excluded == []
