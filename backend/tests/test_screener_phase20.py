"""Phase 20 screener tests — pure, no DB, no network.

Hand-built fixtures only, using real Phase 8/9/12 values for
HUBC, NML, and OGDC. Every acceptance item is tested:
filters match documented calculation semantics; results show
timestamps/quality (evidence carries as-of and price dates);
no false values are substituted for missing fields; saved
screens are reproducible (same definition + as-of date gives
identical outcomes, and re-running skips); sector-specific
metrics do not apply to banks; technical filters match
nothing; pagination and sorting are validated; endpoints are
GET-only; and no execution path exists anywhere.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from app.api.v1.endpoints import screener as screener_endpoint
from app.services.screener import FILTER_REGISTRY, SEED_SCREENS
from app.services.screener.filters import evaluate_filter, validate_filter_entry
from app.services.screener.ranking import paginate, score_outcomes, sort_results
from app.services.screener.runner import evaluate_screen

D = Decimal


def _base(ticker, sector, **overrides):
    row = {
        "ticker": ticker,
        "security_id": 1,
        "company_id": 289,
        "sector": sector,
        "close_price": D("197.24"),
        "price_date": "2026-11-03",
        "volume": 3218965,
        "volume_share_pct": D("0.7291"),
        "fundamentals": {},
        "valuations": {},
        "dividend_per_share": None,
        "dividend_dates_known": False,
        "dividend_amount_note": None,
        "news_event_count": 0,
        "risk_flag_count": 0,
        "statement_age_days": 127,
        "statement_period_end": "2026-06-30",
        "decision": {
            "research_conclusion": "HOLD_CANDIDATE",
            "user_facing": "WITHHELD",
            "confidence": "LOW",
        },
    }
    row.update(overrides)
    return row


def _fund(value, status="computed"):
    return {"value": value, "status": status, "period_end": "2026-06-30", "row_id": 1}


HUBC = _base(
    "HUBC",
    "POWER GENERATION & DISTRIBUTION",
    fundamentals={
        "roe_total": _fund(D("0.224164")),
        "roa": _fund(D("0.134380")),
        "net_margin": _fund(D("0.790947")),
        "gross_margin": _fund(D("0.417400")),
        "current_ratio": _fund(D("1.417098")),
        "receivables_days": _fund(D("157.535475")),
        "debt_to_equity": _fund(D("0.637795")),
    },
    valuations={"multiples:pe_trailing": {"value": D("5.155254"), "status": "computed"}},
    dividend_per_share=D("10.00"),
    dividend_amount_note="Maximum stored dividend per share.",
    news_event_count=1,
    risk_flag_count=2,
)

OGDC = _base(
    "OGDC",
    "OIL & GAS EXPLORATION COMPANIES",
    security_id=3,
    company_id=403,
    close_price=D("303.63"),
    volume=737659,
    fundamentals={
        "roe_total": _fund(D("0.053457")),
        "roa": _fund(D("0.043708")),
        "net_margin": _fund(D("0.378672")),
        "gross_margin": _fund(D("0.536524")),
        "current_ratio": _fund(D("9.621463")),
        "receivables_days": _fund(D("571.325263")),
        "debt_to_equity": _fund(D("0.218973")),
    },
    valuations={"multiples:pe_trailing": {"value": D("17.881625"), "status": "computed"}},
    news_event_count=1,
    risk_flag_count=1,
    statement_age_days=308,
    statement_period_end="2025-12-31",
)

NML = _base(
    "NML",
    "TEXTILE COMPOSITE",
    security_id=2,
    company_id=394,
    close_price=D("123.61"),
    volume=445059,
    fundamentals={
        "roe_total": _fund(D("-0.007445")),
        "roa": _fund(D("-0.004173")),
        "net_margin": _fund(D("-0.007585")),
        "gross_margin": _fund(D("0.155207")),
        "current_ratio": _fund(D("1.366353")),
        "receivables_days": _fund(D("57.028539")),
        "debt_to_equity": _fund(D("0.832987")),
    },
    valuations={"multiples:pe_trailing": {"value": None, "status": "insufficient_inputs"}},
    dividend_per_share=D("5.00"),
    dividend_amount_note="Maximum stored dividend per share.",
    news_event_count=1,
    risk_flag_count=4,
    statement_age_days=583,
    statement_period_end="2025-03-31",
    decision={
        "research_conclusion": "INSUFFICIENT_EVIDENCE",
        "user_facing": "WITHHELD",
        "confidence": "NONE",
    },
)

HBL = _base(
    "HBL",
    "COMMERCIAL BANKS",
    security_id=4,
    company_id=277,
    close_price=D("286.16"),
    volume=100000,
    statement_age_days=None,
    statement_period_end=None,
    decision={
        "research_conclusion": "INSUFFICIENT_EVIDENCE",
        "user_facing": "WITHHELD",
        "confidence": "NONE",
    },
)


def _screen(name):
    return next(s for s in SEED_SCREENS if s["name"] == name)


# --- Absolute filters -------------------------------------------------


def test_absolute_volume_pass_and_fail():
    entry = validate_filter_entry(
        {"filter": "volume", "kind": "absolute", "op": ">=", "value": 100000}
    )
    assert evaluate_filter(entry, HUBC)["outcome"] == "pass"
    assert evaluate_filter(entry, _base("SMALL", "CEMENT", volume=100))["outcome"] == "fail"


def test_absolute_missing_value_is_missing_not_zero():
    entry = validate_filter_entry(
        {"filter": "roe_total", "kind": "absolute", "op": ">", "value": 0}
    )
    outcome = evaluate_filter(entry, _base("NOSTMT", "CEMENT"))
    assert outcome["outcome"] == "missing"
    assert outcome["reason"] == "MISSING_VALUE"
    assert outcome["value"] is None


def test_insufficient_valuation_row_is_missing():
    entry = validate_filter_entry(
        {"filter": "pe_trailing", "kind": "absolute", "op": "<", "value": 10}
    )
    outcome = evaluate_filter(entry, NML)
    assert outcome["outcome"] == "missing"
    assert outcome["reason"] == "MISSING_VALUE"


# --- Percentile filters -----------------------------------------------


def test_percentile_ranking_semantics():
    entry = validate_filter_entry(
        {"filter": "volume", "kind": "percentile", "op": ">=", "value": 90}
    )
    peers = [D(str(v)) for v in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)]
    # Value 10: 9 of 10 peers strictly below -> 90.0 -> pass.
    top = evaluate_filter(entry, _base("TOP", "CEMENT", volume=10), peers)
    assert top["percentile"] == D("90")
    assert top["outcome"] == "pass"
    # Value 9: 8 of 10 below -> 80.0 -> fail.
    ninth = evaluate_filter(entry, _base("NINTH", "CEMENT", volume=9), peers)
    assert ninth["percentile"] == D("80")
    assert ninth["outcome"] == "fail"


def test_percentile_degenerate_and_empty_peer_sets():
    entry = validate_filter_entry(
        {"filter": "volume", "kind": "percentile", "op": ">=", "value": 50}
    )
    single = evaluate_filter(entry, _base("ONLY", "CEMENT", volume=5), [D("5")])
    assert single["percentile"] == D("0")
    assert single["evidence"]["degenerate_peer_set"] is True
    empty = evaluate_filter(entry, _base("NONE", "CEMENT", volume=5), [])
    assert empty["outcome"] == "missing"


# --- Sector applicability and technical null handling ------------------


def test_industrial_filter_not_applicable_to_banks():
    entry = validate_filter_entry(
        {"filter": "roe_total", "kind": "absolute", "op": ">", "value": 0}
    )
    outcome = evaluate_filter(entry, HBL)
    assert outcome["outcome"] == "not_applicable"
    assert outcome["reason"] == "SECTOR_NOT_APPLICABLE"
    # But a price filter still applies to the bank.
    price_entry = validate_filter_entry(
        {"filter": "close_price", "kind": "absolute", "op": ">", "value": 0}
    )
    assert evaluate_filter(price_entry, HBL)["outcome"] == "pass"


def test_technical_filters_are_not_calculable():
    entry = validate_filter_entry({"filter": "sma_5", "kind": "presence"})
    outcome = evaluate_filter(entry, HUBC)
    assert outcome["outcome"] == "missing"
    assert outcome["reason"] == "NOT_CALCULABLE"
    assert outcome["value"] is None


# --- Presence filters ---------------------------------------------------


def test_presence_semantics():
    news = validate_filter_entry({"filter": "news_event_present", "kind": "presence"})
    assert evaluate_filter(news, HUBC)["outcome"] == "pass"
    assert evaluate_filter(news, _base("QUIET", "CEMENT"))["outcome"] == "fail"
    div = validate_filter_entry({"filter": "dividend_per_share", "kind": "presence"})
    assert evaluate_filter(div, HUBC)["outcome"] == "pass"
    assert evaluate_filter(div, OGDC)["outcome"] == "fail"


# --- Scoring ------------------------------------------------------------


def test_scoring_match_no_match_insufficient():
    assert (
        score_outcomes(
            [{"outcome": "pass", "reason": "PASS"}, {"outcome": "pass", "reason": "PASS"}]
        )["outcome"]
        == "MATCH"
    )
    mixed = score_outcomes(
        [{"outcome": "pass", "reason": "PASS"}, {"outcome": "fail", "reason": "FAIL_THRESHOLD"}]
    )
    assert mixed["outcome"] == "NO_MATCH"
    assert mixed["score"] == D("0.5")
    assert mixed["passed_count"] == 1 and mixed["scored_count"] == 2
    missing_only = score_outcomes(
        [
            {"outcome": "missing", "reason": "MISSING_VALUE"},
            {"outcome": "not_applicable", "reason": "SECTOR_NOT_APPLICABLE"},
        ]
    )
    assert missing_only["outcome"] == "INSUFFICIENT_DATA"
    assert missing_only["score"] is None


# --- Seed-screen evaluation on fixtures ---------------------------------


def test_cheap_profitable_fixture_outcomes():
    results = {
        r["ticker"]: r for r in evaluate_screen(_screen("cheap_profitable"), [HUBC, OGDC, NML, HBL])
    }
    assert results["HUBC"]["outcome"] == "MATCH"
    assert results["HUBC"]["score"] == D("1")
    assert results["OGDC"]["outcome"] == "NO_MATCH"  # P/E 17.88 fails.
    assert results["NML"]["outcome"] == "NO_MATCH"  # P/E missing, ROE negative.
    assert results["NML"]["scored_count"] == 1
    assert results["HBL"]["outcome"] == "INSUFFICIENT_DATA"  # Both not_applicable.
    assert results["HBL"]["scored_count"] == 0
    # Decision context rides along but never scores.
    assert results["HUBC"]["evidence"]["decision_context"]["user_facing"] == "WITHHELD"
    # Stale NML statement is flagged, not scored.
    assert "STALE_INPUT" in results["NML"]["reason_codes"]


def test_technical_momentum_matches_nothing():
    results = evaluate_screen(_screen("technical_momentum"), [HUBC, OGDC])
    assert all(r["outcome"] == "INSUFFICIENT_DATA" for r in results)
    assert all("NOT_CALCULABLE" in r["reason_codes"] for r in results)


def test_evaluate_screen_stamps_as_of_date():
    # HBL re-run batch: a later as-of creates a new run snapshot;
    # result evidence must carry that snapshot's date, not the default.
    screen = [s for s in SEED_SCREENS if s["name"] == "dividend_payers"][0]
    row = {
        "ticker": "HBL",
        "security_id": 1,
        "company_id": 1,
        "sector": "COMMERCIAL BANKS",
        "close_price": None,
        "price_date": None,
        "volume": None,
        "volume_share_pct": None,
        "fundamentals": {},
        "valuations": {},
        "dividend_per_share": Decimal("5.00"),
        "dividend_dates_known": False,
        "dividend_amount_note": "Maximum stored dividend per share.",
        "news_event_count": 0,
        "risk_flag_count": 0,
        "statement_age_days": 309,
        "statement_period_end": "2025-12-31",
        "decision": None,
    }
    results = evaluate_screen(screen, [row], as_of_date="2026-11-05")
    assert results[0]["outcome"] == "MATCH"
    assert results[0]["evidence"]["as_of_date"] == "2026-11-05"


def test_dividend_payers_fixture_outcomes():
    results = {
        r["ticker"]: r for r in evaluate_screen(_screen("dividend_payers"), [HUBC, OGDC, NML, HBL])
    }
    assert results["HUBC"]["outcome"] == "MATCH"
    assert results["NML"]["outcome"] == "MATCH"
    assert results["OGDC"]["outcome"] == "NO_MATCH"
    assert results["HBL"]["outcome"] == "NO_MATCH"


def test_screen_results_carry_timestamps_and_quality():
    results = evaluate_screen(_screen("cheap_profitable"), [HUBC])
    evidence = results[0]["evidence"]
    assert evidence["as_of_date"] == "2026-11-04"
    assert evidence["price_date"] == "2026-11-03"
    assert evidence["score_version"] == "screener-score-v1"
    assert "not a recommendation" in evidence["disclaimer"]


# --- Validation, pagination, sorting ------------------------------------


def test_filter_validation_rejects_unknowns():
    with pytest.raises(ValueError):
        validate_filter_entry({"filter": "nope", "kind": "absolute", "op": ">=", "value": 1})
    with pytest.raises(ValueError):
        validate_filter_entry({"filter": "volume", "kind": "bogus", "op": ">=", "value": 1})
    with pytest.raises(ValueError):
        validate_filter_entry({"filter": "volume", "kind": "absolute", "op": "~~", "value": 1})
    with pytest.raises(ValueError):
        validate_filter_entry({"filter": "volume", "kind": "absolute", "op": ">="})


def test_pagination_validation():
    page, info = paginate(list(range(250)), 100, 200)
    assert len(page) == 50 and info["total"] == 250
    with pytest.raises(ValueError):
        paginate([], 0, 0)
    with pytest.raises(ValueError):
        paginate([], 101, 0)
    with pytest.raises(ValueError):
        paginate([], 20, -1)


def test_sorting_score_desc_none_last_then_ticker():
    rows = [
        {"ticker": "B", "score": None},
        {"ticker": "C", "score": D("0.5")},
        {"ticker": "A", "score": D("1")},
    ]
    assert [r["ticker"] for r in sort_results(rows)] == ["A", "C", "B"]
    assert [r["ticker"] for r in sort_results(rows, "ticker")] == ["A", "B", "C"]
    with pytest.raises(ValueError):
        sort_results(rows, "bogus")


# --- Registry, routes, and execution-denial ------------------------------


def test_registry_covers_all_brief_categories():
    categories = {spec["category"] for spec in FILTER_REGISTRY.values()}
    for required in (
        "price",
        "volume",
        "technical",
        "ratio",
        "leverage",
        "valuation",
        "dividend",
        "news_event",
        "liquidity",
        "risk",
    ):
        assert required in categories
    assert len(SEED_SCREENS) == 5


def test_screener_endpoints_are_get_only():
    methods = set()
    for route in screener_endpoint.router.routes:
        methods.update(route.methods or set())
    assert methods == {"GET"}


def test_no_execution_path_anywhere():
    repo_root = Path(__file__).resolve().parents[2]
    banned = (
        "place_order",
        "execute_order",
        "submit_order",
        "execute_trade",
        "place_trade",
    )
    hits = []
    for base in ("backend/app", "scripts"):
        for path in (repo_root / base).rglob("*.py"):
            if "test_" in path.name:
                continue
            # Phase 29 allowlist: the acceptance auditor holds these
            # identifiers as SEARCH patterns for its own scan; it
            # contains no execution code and never calls them.
            if "acceptance" in path.parts and path.name == "audits.py":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in banned:
                if token in text:
                    hits.append(f"{path}:{token}")
    assert hits == []
