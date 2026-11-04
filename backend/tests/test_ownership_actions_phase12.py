"""Phase 12 pure tests: adjustment formulas, breadth math, seed data.

No database, no network. Hand-calculated expectations throughout.
"""

from decimal import Decimal

from app.services.ownership_actions import CATEGORY_ROWS, KEY_HOLDERS
from app.services.ownership_actions.adjustments import (
    apply_factor,
    bonus_factor,
    can_apply_dividend,
    dividend_adjusted_close,
    split_factor,
    theoretical_ex_rights_price,
)
from app.services.ownership_actions.breadth import compute_breadth, compute_liquidity


def test_dividend_adjustment_actual_examples():
    # Actual examples: NML close 2026-11-03 = 123.61, final DPS 5.00.
    assert dividend_adjusted_close(Decimal("123.61"), Decimal("5.00")) == Decimal("118.61")
    # HUBC close 197.24, final DPS 10.00 and interim DPS 5.00.
    assert dividend_adjusted_close(Decimal("197.24"), Decimal("10.00")) == Decimal("187.24")
    assert dividend_adjusted_close(Decimal("197.24"), Decimal("5.00")) == Decimal("192.24")


def test_bonus_and_split_factors():
    assert bonus_factor(Decimal("4"), Decimal("1")) == Decimal("1.25")
    price, volume = apply_factor(Decimal("100"), 1000, Decimal("1.25"))
    assert price == Decimal("80")
    assert volume == Decimal("1250")
    assert split_factor(Decimal("1"), Decimal("10")) == Decimal("10")
    price, volume = apply_factor(Decimal("50"), 100, Decimal("10"))
    assert price == Decimal("5")
    assert volume == Decimal("1000")


def test_terp_formula():
    # 100 old shares at 50, 25 new at 40: (5000 + 1000) / 125 = 48.
    assert theoretical_ex_rights_price(
        Decimal("100"), Decimal("50"), Decimal("25"), Decimal("40")
    ) == Decimal("48")


def test_dividend_rule_needs_ex_date():
    assert can_apply_dividend(None, Decimal("5.00")) is False
    assert can_apply_dividend("2026-01-01", None) is False
    assert can_apply_dividend("2026-01-01", Decimal("5.00")) is True


def test_category_seed_reconciles_to_totals():
    holders = sum(row[1] for row in CATEGORY_ROWS)
    shares = sum(row[2] for row in CATEGORY_ROWS)
    assert holders == 80377
    assert shares == 1297154387
    pct_sum = sum(Decimal(row[3]) for row in CATEGORY_ROWS if row[3] is not None)
    assert pct_sum == Decimal("99.99")  # printed total 100.00; 0.01 rounding


def test_key_holder_seed_matches_categories():
    assoc = sum(shares for cat, _n, _f, shares in KEY_HOLDERS if cat == "ASSOCIATED_COMPANY")
    directors = sum(shares for cat, _n, _f, shares in KEY_HOLDERS if cat == "DIRECTOR")
    assert assoc == 264146002
    assert directors == 1006244
    # Two folios each for MEGA CONGLOMERATE and MUHAMMAD KAMRAN KAMAL.
    mega = [row for row in KEY_HOLDERS if row[1] == "MEGA CONGLOMERATE (PVT.) LIMITED"]
    assert len(mega) == 2 and mega[0][2] != mega[1][2]
    kamal = [row for row in KEY_HOLDERS if row[1] == "MUHAMMAD KAMRAN KAMAL"]
    assert len(kamal) == 2 and kamal[0][2] != kamal[1][2]


def test_breadth_fixture():
    universe = [
        {"ticker": "A", "sector": "CEMENT"},
        {"ticker": "B", "sector": "CEMENT"},
        {"ticker": "C", "sector": "BANKS"},
    ]
    priced = [
        {"ticker": "A", "sector": "CEMENT", "volume": 100},
        {"ticker": "B", "sector": "CEMENT", "volume": 300},
    ]
    metrics = {(m["scope"], m["metric_key"]): m for m in compute_breadth(priced, universe)}
    assert metrics[("MARKET", "priced_coverage")]["numerator"] == 2
    assert metrics[("MARKET", "priced_coverage")]["denominator"] == 3
    assert metrics[("SECTOR:CEMENT", "priced_coverage")]["numerator"] == 2
    assert metrics[("SECTOR:BANKS", "priced_coverage")]["numerator"] == 0
    assert metrics[("MARKET", "total_volume")]["value"] == Decimal(400)
    assert metrics[("MARKET", "median_volume")]["value"] == Decimal(200)
    assert metrics[("MARKET", "top10_volume_share_pct")]["value"] == Decimal(100)
    for key in (
        "advances",
        "declines",
        "unchanged",
        "new_highs",
        "new_lows",
        "turnover_distribution",
    ):
        metric = metrics[("MARKET", key)]
        assert metric["value"] is None
        assert metric["status"] == "insufficient_inputs"


def test_liquidity_fixture():
    priced = [
        {"ticker": "A", "sector": "CEMENT", "volume": 100},
        {"ticker": "B", "sector": "CEMENT", "volume": 300},
    ]
    obs = {(o["scope_key"], o["metric_key"]): o for o in compute_liquidity(priced)}
    assert obs[("SEC:A", "volume_share_pct")]["value"] == Decimal(25)
    assert obs[("SEC:B", "volume_share_pct")]["value"] == Decimal(75)
    assert obs[("MARKET", "total_volume")]["value"] == Decimal(400)
