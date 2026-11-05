"""Phase 15 decision scoring tests — pure, no DB, no network.

Hand-calculated cases only. Every gating rule is tested: a gated
company maps to INSUFFICIENT_EVIDENCE regardless of scores, a
missing input yields ABSENT (never zero-filled), and confidence
can never exceed LOW on UNVERIFIED inputs or uncalibrated models.
The final test proves the acceptance item "no brokerage order
path is present" by scanning the application source (excluding
tests) for execution identifiers and for non-GET routes on the
decisions endpoint.
"""

from decimal import Decimal
from pathlib import Path

from app.services.decision_engine import GATES_V1, RULES_VERSION
from app.services.decision_engine.scoring import (
    ABSENT,
    aggregate,
    agreement,
    completeness,
    confidence,
    fundamentals_score,
    liquidity_score,
    macro_score,
    map_conclusion,
    news_score,
    risk_score,
    user_facing,
    valuation_score,
)

D = Decimal

HUBC_SCORES = {
    "fundamentals": 1,
    "valuation": 1,
    "technical": ABSENT,
    "news_event": 0,
    "macro": -1,
    "liquidity": 1,
    "risk": 0,
}

OGDC_SCORES = {
    "fundamentals": 1,
    "valuation": 0,
    "technical": ABSENT,
    "news_event": 0,
    "macro": -1,
    "liquidity": 0,
    "risk": 0,
}


def test_fundamentals_score_cases():
    assert fundamentals_score(D(100), D(100), False) == 1
    assert fundamentals_score(D("73.3333"), D(100), False) == 1
    assert fundamentals_score(D(0), D("73.3333"), True) == -1
    assert fundamentals_score(D(60), D(60), False) == 0
    assert fundamentals_score(None, D(100), False) is ABSENT
    assert fundamentals_score(D(100), None, False) is ABSENT


def test_valuation_score_cases():
    assert valuation_score(D("5.1553")) == 1
    assert valuation_score(D("17.8816")) == 0
    assert valuation_score(D(10)) == 0
    assert valuation_score(D(25)) == 0
    assert valuation_score(D("25.0001")) == -1
    assert valuation_score(None) is ABSENT


def test_other_dimension_scores():
    assert news_score(True) == 0
    assert news_score(False) is ABSENT
    assert macro_score("tightening") == -1
    assert macro_score("neutral") == 0
    assert macro_score(None) is ABSENT
    assert liquidity_score("HIGH") == 1
    assert liquidity_score("MEDIUM") == 0
    assert liquidity_score("LOW") == -1
    assert liquidity_score(None) is ABSENT
    assert risk_score(True) == -1
    assert risk_score(False) == 0


def test_aggregate_excludes_absent():
    total, scored = aggregate(HUBC_SCORES)
    assert total == 2
    assert scored == 6
    total, scored = aggregate(OGDC_SCORES)
    assert total == 0
    assert scored == 6


def test_map_conclusion_production_cases():
    assert map_conclusion(HUBC_SCORES, []) == "HOLD_CANDIDATE"
    assert map_conclusion(OGDC_SCORES, []) == "HOLD_CANDIDATE"


def test_map_conclusion_gates_override_scores():
    # Even a perfect scorecard is abstained when gated.
    buy_scores = {
        "fundamentals": 1,
        "valuation": 1,
        "technical": ABSENT,
        "news_event": 0,
        "macro": 1,
        "liquidity": 1,
        "risk": 0,
    }
    assert map_conclusion(buy_scores, []) == "BUY_CANDIDATE"
    assert map_conclusion(buy_scores, ["stale_latest_statement"]) == "INSUFFICIENT_EVIDENCE"
    assert map_conclusion(buy_scores, ["publication_date_unknown"]) == "INSUFFICIENT_EVIDENCE"


def test_map_conclusion_sell_and_watchlist():
    sell_scores = {
        "fundamentals": -1,
        "valuation": -1,
        "technical": ABSENT,
        "news_event": 0,
        "macro": -1,
        "liquidity": -1,
        "risk": -1,
    }
    assert map_conclusion(sell_scores, []) == "SELL_CANDIDATE"
    watch_scores = {
        "fundamentals": 1,
        "valuation": ABSENT,
        "technical": ABSENT,
        "news_event": 0,
        "macro": -1,
        "liquidity": 0,
        "risk": ABSENT,
    }
    assert map_conclusion(watch_scores, []) == "WATCHLIST"
    thin_scores = {
        "fundamentals": 1,
        "valuation": ABSENT,
        "technical": ABSENT,
        "news_event": ABSENT,
        "macro": ABSENT,
        "liquidity": ABSENT,
        "risk": ABSENT,
    }
    assert map_conclusion(thin_scores, []) == "INSUFFICIENT_EVIDENCE"


def test_completeness_and_agreement():
    assert completeness(6) == D(6) / D(7)
    assert completeness(0) == D(0)
    # HOLD is neutral: agreement is the share of zero-scored dims.
    assert agreement(HUBC_SCORES, "HOLD_CANDIDATE") == D(2) / D(6)
    assert agreement(OGDC_SCORES, "HOLD_CANDIDATE") == D(4) / D(6)
    assert agreement(HUBC_SCORES, "INSUFFICIENT_EVIDENCE") is None


def test_confidence_caps():
    # Production case: UNVERIFIED + uncalibrated -> LOW, always.
    assert (
        confidence(
            "HOLD_CANDIDATE",
            D(6) / D(7),
            D(2) / D(6),
            "UNVERIFIED",
            False,
            3,
        )
        == "LOW"
    )
    assert confidence("INSUFFICIENT_EVIDENCE", D(0), None, "UNVERIFIED", False, 0) == "NONE"
    # MEDIUM is reachable only with better inputs + calibration.
    assert (
        confidence(
            "HOLD_CANDIDATE",
            D(6) / D(7),
            D(4) / D(6),
            "PARTIALLY_VERIFIED",
            True,
            1,
        )
        == "MEDIUM"
    )
    # HIGH needs everything: verified, calibrated, complete, agreed.
    assert confidence("BUY_CANDIDATE", D(1), D(1), "VERIFIED", True, 0) == "HIGH"


def test_user_facing_withheld_below_medium():
    assert user_facing("HOLD_CANDIDATE", "LOW")[0] == "WITHHELD"
    assert user_facing("INSUFFICIENT_EVIDENCE", "NONE")[0] == "WITHHELD"
    assert user_facing("HOLD_CANDIDATE", "MEDIUM")[0] == "HOLD_CANDIDATE"


def test_rules_version_and_gates_documented():
    assert RULES_VERSION == "decision-rules-v1"
    for gate in (
        "no_statements",
        "stale_latest_statement",
        "publication_date_unknown",
        "valuation_publication_unknown",
        "too_few_dimensions",
    ):
        assert gate in GATES_V1


def test_no_execution_path_in_codebase():
    """Acceptance item: no brokerage order path is present.

    Scans application source (excluding tests) for execution
    identifiers and for write routes on the decisions endpoint.
    Prose mentions of "buy/sell" as research-candidate labels are
    not execution paths and are not matched; only code identifiers
    and route decorators are.
    """
    app_root = Path(__file__).resolve().parent.parent / "app"
    forbidden = (
        "place_order",
        "execute_order",
        "submit_order",
        "execute_trade",
        "place_trade",
        "class Broker",
        "BrokerClient",
        "broker_client",
        "broker_api",
        "/orders",
        "orders_router",
    )
    hits = []
    for path in app_root.rglob("*.py"):
        # Phase 29 allowlist: the acceptance auditor holds these
        # identifiers as SEARCH patterns for its own scan; it
        # contains no execution code and never calls them.
        if "acceptance" in path.parts and path.name == "audits.py":
            continue
        text = path.read_text()
        for token in forbidden:
            if token in text:
                hits.append(f"{path}:{token}")
    assert hits == [], f"Execution path tokens found: {hits}"
    decisions_source = (app_root / "api" / "v1" / "endpoints" / "decisions.py").read_text()
    assert "@router.get" in decisions_source
    for decorator in ("@router.post", "@router.put", "@router.patch", "@router.delete"):
        assert decorator not in decisions_source
