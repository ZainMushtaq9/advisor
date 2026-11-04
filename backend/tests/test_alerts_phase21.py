"""Phase 21 alerts tests — pure, no DB, no network.

Hand-built fixtures only, using real Phase 14/17/20 values for
HUBC, NML, and OGDC where a value is asserted. Every
acceptance item is tested: triggers are reproducible (same
inputs give the same dedup keys and outcomes); no paid or
external delivery exists (only in-app is allowed, everything
else is refused without sending); duplicates are skipped by
dedup key; stale, future, and dateless events are suppressed
with reasons, never silently dropped; every alert carries
evidence and both timestamps; lifecycle transitions are
guarded (RESOLVED is terminal); endpoints are GET-only; and
no execution path exists anywhere.
"""

from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.api.v1.endpoints import alerts as alerts_endpoint
from app.services.alerts import RULE_BY_KEY, SEED_RULES
from app.services.alerts.evaluation import (
    classify_event,
    dedup_key,
    evaluate_candidates,
    in_quiet_window,
    map_flag_severity,
    paginate,
    transition,
)
from app.services.alerts.runner import apply_frequency_limit, deliver_channel

TZ = ZoneInfo("Asia/Karachi")
AS_OF = date(2026, 11, 4)
PROCESSING = datetime(2026, 11, 5, 1, 30, tzinfo=TZ)


def _rule(key: str) -> dict:
    return dict(RULE_BY_KEY[key])


def _candidate(**overrides) -> dict:
    row = {
        "subject_type": "SECURITY",
        "ticker": "HUBC",
        "company_id": 289,
        "sector": None,
        "event_date": date(2026, 11, 3),
        "title": "High volume: HUBC",
        "source_ref": "market_prices:1",
        "evidence": {"source_ref": "market_prices:1", "volume": 3218965},
        "quality_status": "UNVERIFIED",
    }
    row.update(overrides)
    return row


def test_dedup_key_stable_and_distinct():
    # Keyed on the source event, not just subject and date: one
    # company can carry several flags on the same as-of date,
    # and each is its own alert.
    key = dedup_key("risk_flag_raised", "risk_flags:12", date(2026, 11, 4))
    assert key == dedup_key("risk_flag_raised", "risk_flags:12", date(2026, 11, 4))
    assert key != dedup_key("risk_flag_raised", "risk_flags:13", date(2026, 11, 4))
    assert key != dedup_key("risk_flag_raised", "risk_flags:12", date(2026, 11, 3))
    assert key != dedup_key("macro_release", "macro_events:1", date(2026, 11, 4))
    assert dedup_key("macro_release", "macro_events:1", date(2026, 10, 26)) == (
        "macro_release|macro_events:1|2026-10-26"
    )


def test_staleness_boundary():
    rule = _rule("high_volume")  # max age 7 days
    # Exactly 7 days old on the processing date: not stale.
    assert classify_event(rule, date(2026, 10, 29), AS_OF, date(2026, 11, 5)) is None
    # 8 days old: stale.
    assert classify_event(rule, date(2026, 10, 28), AS_OF, date(2026, 11, 5)) == "STALE"


def test_future_and_unknown_dates():
    rule = _rule("macro_release")
    assert classify_event(rule, date(2026, 12, 14), AS_OF, date(2026, 11, 5)) == "FUTURE_SCHEDULED"
    assert classify_event(rule, None, AS_OF, date(2026, 11, 5)) == "UNKNOWN_DATE"
    # A future event is not misclassified as stale.
    assert classify_event(rule, date(2027, 1, 1), AS_OF, date(2026, 11, 5)) != "STALE"


def test_evaluate_candidates_mixed_batch():
    rule = _rule("earnings_disclosure")  # max age 90 days
    alerts, suppressed = evaluate_candidates(
        rule,
        [
            _candidate(
                subject_type="COMPANY",
                ticker="HUBC",
                event_date=date(2026, 9, 21),
                title="Earnings disclosure: HUBCO Integrated Annual Report 2026",
                source_ref="news_events:1",
                evidence={"source_ref": "news_events:1"},
            ),
            _candidate(
                subject_type="COMPANY",
                ticker="OGDC",
                event_date=date(2026, 2, 23),
                title="Earnings disclosure: OGDC interim",
                source_ref="news_events:3",
                evidence={"source_ref": "news_events:3"},
            ),
            _candidate(
                subject_type="COMPANY",
                ticker="NML",
                event_date=None,
                title="Earnings disclosure: NML quarter",
                source_ref="news_events:2",
                evidence={"source_ref": "news_events:2"},
            ),
        ],
        AS_OF,
        PROCESSING,
    )
    assert [a["ticker"] for a in alerts] == ["HUBC"]
    assert suppressed == {"STALE": 1, "UNKNOWN_DATE": 1}
    hubc = alerts[0]
    assert hubc["dedup_key"] == "earnings_disclosure|news_events:1|2026-09-21"
    assert hubc["event_time"].tzinfo is not None
    assert hubc["processing_time"] == PROCESSING
    assert hubc["as_of_date"] == AS_OF
    assert hubc["evidence"]["source_ref"] == "news_events:1"
    assert hubc["quality_status"] == "UNVERIFIED"


def test_flag_severity_mapping():
    assert map_flag_severity("warning") == "WARNING"
    assert map_flag_severity("info") == "INFO"
    with pytest.raises(ValueError):
        map_flag_severity("critical")


def test_quiet_window_plain_and_wrapping():
    # No window: never deferred.
    assert in_quiet_window(PROCESSING, None, None) is False
    # Plain window 02:00-06:00: 01:30 outside, 03:00 inside.
    assert in_quiet_window(PROCESSING, time(2, 0), time(6, 0)) is False
    assert in_quiet_window(datetime(2026, 11, 5, 3, 0, tzinfo=TZ), time(2, 0), time(6, 0)) is True
    # Wrapping window 23:00-07:00: 01:30 inside, 12:00 outside.
    assert in_quiet_window(PROCESSING, time(23, 0), time(7, 0)) is True
    assert (
        in_quiet_window(datetime(2026, 11, 5, 12, 0, tzinfo=TZ), time(23, 0), time(7, 0)) is False
    )


def test_frequency_limit():
    rule = _rule("high_volume")  # daily limit 100
    assert apply_frequency_limit(rule, 0, 68) == (68, 0)
    assert apply_frequency_limit(rule, 95, 10) == (5, 5)
    assert apply_frequency_limit(rule, 100, 10) == (0, 10)
    unlimited = _rule("macro_release")
    assert apply_frequency_limit(unlimited, 999, 4) == (4, 0)


def test_lifecycle_transitions():
    assert transition("NEW", "acknowledge") == "ACKNOWLEDGED"
    assert transition("NEW", "mute") == "MUTED"
    assert transition("NEW", "resolve") == "RESOLVED"
    assert transition("ACKNOWLEDGED", "mute") == "MUTED"
    assert transition("ACKNOWLEDGED", "resolve") == "RESOLVED"
    assert transition("MUTED", "unmute") == "NEW"
    assert transition("MUTED", "resolve") == "RESOLVED"
    for action in ("acknowledge", "mute", "resolve", "unmute"):
        with pytest.raises(ValueError):
            transition("RESOLVED", action)
    with pytest.raises(ValueError):
        transition("ACKNOWLEDGED", "unmute")
    with pytest.raises(ValueError):
        transition("NEW", "unmute")


def test_external_channel_gate():
    assert deliver_channel("in_app") == {
        "channel": "in_app",
        "outcome": "ALLOWED_LOCAL",
    }
    for channel in ("email", "sms", "push"):
        assert deliver_channel(channel) == {
            "channel": channel,
            "outcome": "BLOCKED_NO_CONSENT",
        }


def test_valuation_change_candidates():
    from decimal import Decimal

    from app.services.alerts.evaluation import valuation_change_candidates

    def row(sec, method, day, value, rid):
        return {
            "security_id": sec,
            "method": method,
            "valuation_date": date.fromisoformat(day),
            "estimated_value": value,
            "row_id": rid,
            "quality_status": "UNVERIFIED",
        }

    # No pair with two rows: whole rule is NO_SERIES.
    changed, suppressed = valuation_change_candidates(
        [row(1, "trailing_pe", "2026-11-03", Decimal("5.1553"), 1)]
    )
    assert changed == [] and suppressed == {"NO_SERIES": 1}
    # Changed, unchanged, and no-value pairs.
    changed, suppressed = valuation_change_candidates(
        [
            row(1, "trailing_pe", "2026-06-30", Decimal("5.0"), 1),
            row(1, "trailing_pe", "2026-11-03", Decimal("5.1553"), 2),
            row(2, "book_value", "2026-06-30", Decimal("100"), 3),
            row(2, "book_value", "2026-11-03", Decimal("100"), 4),
            row(3, "trailing_pe", "2026-06-30", None, 5),
            row(3, "trailing_pe", "2026-11-03", Decimal("17.88"), 6),
        ]
    )
    assert len(changed) == 1
    assert changed[0]["old_value"] == Decimal("5.0")
    assert changed[0]["new_value"] == Decimal("5.1553")
    assert changed[0]["event_date"] == date(2026, 11, 3)
    assert suppressed == {"UNCHANGED": 1, "NO_VALUE": 1}


def test_paginate_validation():
    assert paginate([1, 2, 3, 4, 5], 2, 2) == [3, 4]
    assert paginate([1, 2], 100, 0) == [1, 2]
    with pytest.raises(ValueError):
        paginate([1], 0, 0)
    with pytest.raises(ValueError):
        paginate([1], 101, 0)
    with pytest.raises(ValueError):
        paginate([1], 10, -1)


def test_rule_registry_covers_taxonomy():
    categories = {rule["category"] for rule in SEED_RULES}
    for expected in (
        "PRICE_VOLUME_THRESHOLD",
        "TECHNICAL_EVENT",
        "FINANCIAL_DISCLOSURE",
        "DIVIDEND_ACTION",
        "MACRO_RELEASE",
        "VALUATION_CHANGE",
        "RISK_BREACH",
    ):
        assert expected in categories
    assert len(SEED_RULES) == 9
    assert len({rule["rule_key"] for rule in SEED_RULES}) == 9
    for rule in SEED_RULES:
        assert rule["origin"] in ("OFFICIAL", "DERIVED", "MODEL_WARNING")
        assert rule["max_event_age_days"] > 0


def test_alerts_endpoint_get_only():
    source = Path(alerts_endpoint.__file__).read_text()
    decorators = [
        line.strip() for line in source.splitlines() if line.strip().startswith("@router.")
    ]
    assert decorators, "no routes found"
    assert all(d.startswith("@router.get") for d in decorators), decorators


def test_no_execution_path_anywhere():
    root = Path(__file__).resolve().parents[1]
    hits = []
    needles = (
        "place_order",
        "execute_order",
        "submit_order",
        "execute_trade",
        "place_trade",
        "Broker",
        "broker_client",
    )
    for base in (root / "app", root.parent / "scripts"):
        for path in base.rglob("*.py"):
            if "test_" in path.name:
                continue
            text = path.read_text(errors="ignore")
            for needle in needles:
                if needle in text:
                    hits.append(f"{path}:{needle}")
    assert hits == []
