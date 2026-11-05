"""News Intelligence Engine tests (prompt section 15).

Pure unit tests + SQLite in-memory model tests only. No real
PostgreSQL, no network, no local model server. A passing suite here
proves the pipeline logic; it does NOT prove production data access
or live collection (those stay PAUSED/BLOCKED and are reported as
such in the run reports).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.news_intelligence import (
    NewsArticle,
    NewsArticleEntity,
    NewsSentimentAssessment,
)
from app.services.news_events.collectors import PolicyBlocked
from app.services.news_intelligence import (
    assistant as assistant_mod,
)
from app.services.news_intelligence import (
    collection as collection_mod,
)
from app.services.news_intelligence import (
    guards as guards_mod,
)
from app.services.news_intelligence import (
    impact as impact_mod,
)
from app.services.news_intelligence import (
    leakage as leakage_mod,
)
from app.services.news_intelligence import (
    market_reaction as reaction_mod,
)
from app.services.news_intelligence import (
    processing as processing_mod,
)
from app.services.news_intelligence import (
    rag_news as rag_news_mod,
)
from app.services.news_intelligence import (
    schema as schema_mod,
)
from app.services.news_intelligence import (
    taxonomy as taxonomy_mod,
)

KNOWN = {"HUBC", "NML", "OGDC", "HBL"}
# Alias index keys are NORMALIZED (Phase 11 aliases.normalize uppercases),
# exactly as the runner builds them from stored company_aliases rows.
ALIAS_INDEX = {
    "HUBC": [(1, "TICKER", 1.0, False)],
    "NML": [(2, "TICKER", 1.0, False)],
    "HBL": [(4, "TICKER", 1.0, False)],
}
SECTOR_BY_TICKER = {"HUBC": "Power Generation & Distribution"}
TICKER_BY_ID = {1: "HUBC", 2: "NML", 4: "HBL"}
NAME_BY_ID = {1: "Hub Power Company Limited", 2: "Nishat Mills Limited"}


def _article(**overrides):
    base = {
        "article_id": "test-1",
        "title": "HUBC announces record profit growth",
        "source": "Test Source",
        "canonical_url": "https://example.invalid/hubc-profit",
        "published_at": "2026-11-04T10:00:00+05:00",
        "retrieved_at": "2026-11-04T11:00:00+05:00",
        "language": "en",
        "text": "HUBC announces record profit growth for the year.",
    }
    base.update(overrides)
    return base


def _valid_record(**overrides):
    base = {
        "article_id": "test-1",
        "title": "HUBC announces record profit growth",
        "source": "Test Source",
        "canonical_url": "https://example.invalid/hubc-profit",
        "published_at": "2026-11-04T10:00:00+05:00",
        "retrieved_at": "2026-11-04T11:00:00+05:00",
        "language": "en",
        "company_names": ["Hub Power Company Limited"],
        "ticker_symbols": ["HUBC"],
        "sector_names": ["Power Generation & Distribution"],
        "event_category": "earnings",
        "sentiment": "positive",
        "relevance_score": 0.6,
        "impact_score": 0.7,
        "confidence_score": 0.7,
        "potential_impact_horizon": "short_term",
        "extracted_facts": ["HUBC announces record profit growth"],
        "supporting_evidence": ["rule_based:keyword"],
        "uncertainty_notes": ["rule-based output"],
        "risk_factors": [],
        "summary": "HUBC announces record profit growth",
        "model_name": "deterministic-fallback-v1",
        "model_version": "rule-based-1.0",
        "processing_timestamp": "2026-11-04T11:00:00+05:00",
    }
    base.update(overrides)
    return base


# --- taxonomy / classification ---------------------------------------


def test_taxonomy_earnings_keyword_wins():
    category, confidence, _basis = taxonomy_mod.classify_deterministic(
        "HUBC announces quarterly earnings and profit"
    )
    assert category == "earnings"
    assert confidence == 0.70


def test_taxonomy_urdu_script_forces_review_category():
    category, confidence, _basis = taxonomy_mod.classify_deterministic(
        "منافع میں اضافہ ہوا ہے"
    )
    assert category == "other"
    assert confidence == 0.50


def test_taxonomy_empty_text_zero_confidence():
    category, confidence, _basis = taxonomy_mod.classify_deterministic("")
    assert confidence == 0.0
    assert category == "other"


def test_taxonomy_invalid_category_rejected():
    assert not taxonomy_mod.is_valid_category("moon_landing")
    assert taxonomy_mod.is_valid_category("dividends")


def test_taxonomy_specific_rule_beats_generic_rule():
    # "quarterly dividend": DIVIDEND must win over QUARTERLY.
    category, _conf, _basis = taxonomy_mod.classify_deterministic(
        "HUBC announces quarterly dividend"
    )
    assert category == "dividends"
    # "contract dispute" in court: COURT must win over CONTRACT.
    category, _conf, _basis = taxonomy_mod.classify_deterministic(
        "OGDC faces court penalty over contract dispute"
    )
    assert category == "court_decision"


def test_lexicon_sentiment_fires_on_normalized_text():
    # Regression: lexicon words must be uppercase because
    # normalize() uppercases; lowercase sets forced neutral always.
    from app.services.news_intelligence.llm_adapter import lexicon_sentiment

    assert lexicon_sentiment("HBL reports loss after tax") == "negative"
    assert lexicon_sentiment("HUBC announces dividend") == "positive"
    assert lexicon_sentiment("Markets steady today") == "neutral"
    assert lexicon_sentiment("Profit rises but penalty imposed") == "mixed"


# --- schema validation ------------------------------------------------


def test_schema_valid_record_passes():
    ok, errors, cleaned = schema_mod.validate_llm_output(_valid_record(), KNOWN)
    assert ok and errors == []
    assert cleaned["ticker_symbols"] == ["HUBC"]


def test_schema_unknown_ticker_rejected():
    ok, errors, _cleaned = schema_mod.validate_llm_output(
        _valid_record(ticker_symbols=["FAKE"]), KNOWN
    )
    assert not ok
    assert any("FAKE" in e for e in errors)


def test_schema_score_out_of_range_rejected():
    ok, errors, _cleaned = schema_mod.validate_llm_output(
        _valid_record(relevance_score=1.5), KNOWN
    )
    assert not ok


def test_schema_missing_field_rejected():
    record = _valid_record()
    del record["summary"]
    ok, errors, _cleaned = schema_mod.validate_llm_output(record, KNOWN)
    assert not ok
    assert any("summary" in e for e in errors)


def test_schema_summary_over_cap_rejected_not_trimmed():
    ok, errors, _cleaned = schema_mod.validate_llm_output(
        _valid_record(summary="x" * 281), KNOWN
    )
    assert not ok


def test_schema_bad_sentiment_and_horizon_rejected():
    ok, errors, _cleaned = schema_mod.validate_llm_output(
        _valid_record(sentiment="ecstatic", potential_impact_horizon="forever"),
        KNOWN,
    )
    assert not ok
    assert len(errors) >= 2


# --- guards ------------------------------------------------------------


def test_grounding_check_shared_token_grounds():
    assert guards_mod.grounding_check(
        "HUBC announces record profit",
        "HUBC announces record profit growth for the year.",
    )
    assert not guards_mod.grounding_check(
        "OGDC discovers oil reserves",
        "HUBC announces record profit growth for the year.",
    )


def test_grounding_numbers_alone_do_not_ground():
    assert not guards_mod.grounding_check(
        "1234 5678",
        "HUBC announces record profit growth for the year.",
    )


def test_cap_confidence_ambiguous_caps_at_half_and_forces_review():
    capped, force_review = guards_mod.cap_confidence(0.95, True, True)
    assert capped == 0.50
    assert force_review is True


def test_cap_confidence_below_threshold_forces_review():
    _capped, force_review = guards_mod.cap_confidence(0.70, False, True)
    assert force_review is True
    _capped, force_review = guards_mod.cap_confidence(0.90, False, True)
    assert force_review is False


def test_check_tickers_flags_unknown():
    assert guards_mod.check_tickers(["HUBC", "FAKE"], KNOWN) == ["FAKE"]
    assert guards_mod.check_tickers(["HUBC"], KNOWN) == []


# --- collection / permission enforcement --------------------------------


def test_collection_blocked_source_refused():
    with pytest.raises(PolicyBlocked):
        collection_mod.collection_allowed("dps_announcements", "TERMS_GATED", True)


def test_collection_permitted_but_unapproved_automation_refused():
    with pytest.raises(PolicyBlocked):
        collection_mod.collection_allowed("sbp", "COLLECTABLE", False)


def test_collection_permitted_and_approved_passes():
    collection_mod.collection_allowed("sbp", "COLLECTABLE", True)


def test_backoff_doubles_to_cap():
    assert collection_mod.backoff_delay_seconds(0) == 60
    assert collection_mod.backoff_delay_seconds(1) == 120
    assert collection_mod.backoff_delay_seconds(10) == 3600
    assert collection_mod.backoff_delay_seconds(-3) == 60


def test_normalize_naive_timestamp_is_karachi_not_utc():
    parsed = collection_mod.normalize_published_at("2026-11-04T10:00:00")
    assert parsed is not None and parsed.tzinfo is not None
    assert "Asia/Karachi" in str(parsed.tzinfo)
    assert collection_mod.normalize_published_at("not a date") is None
    assert collection_mod.normalize_published_at(None) is None


def test_freshness_status_rules():
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    assert (
        collection_mod.freshness_status(
            datetime(2026, 11, 5, 11, 0, tzinfo=timezone.utc), now
        )
        == "current"
    )
    assert (
        collection_mod.freshness_status(
            datetime(2026, 10, 20, 11, 0, tzinfo=timezone.utc), now
        )
        == "stale"
    )
    assert collection_mod.freshness_status(None, now) == "unknown"
    assert (
        collection_mod.freshness_status(
            datetime(2026, 11, 6, 11, 0, tzinfo=timezone.utc), now
        )
        == "unknown"
    )


def test_trading_weekday_rule():
    assert collection_mod.is_trading_weekday(datetime(2026, 11, 5))  # Thursday
    assert not collection_mod.is_trading_weekday(datetime(2026, 11, 7))  # Saturday
    assert not collection_mod.is_trading_weekday(None)


def test_rss_parse_caps_summary_and_rejects_malformed():
    feed = (
        "<rss><channel>"
        "<item><title>HUBC profit</title>"
        "<link>https://example.invalid/1</link>"
        "<description>" + "x" * 500 + "</description></item>"
        "</channel></rss>"
    )
    items = collection_mod.parse_rss_items(feed)
    assert len(items) == 1
    assert len(items[0]["summary"]) == 280
    with pytest.raises(ValueError):
        collection_mod.parse_rss_items("<rss><broken")


def test_content_hash_dedup_grain_stable():
    h1 = collection_mod.article_content_hash("HUBC profit", "https://example.invalid/1")
    h2 = collection_mod.article_content_hash("HUBC profit", "https://example.invalid/1")
    h3 = collection_mod.article_content_hash("HUBC loss", "https://example.invalid/1")
    assert h1 == h2 and h1 != h3


# --- processing pipeline -------------------------------------------------


def test_processing_fallback_is_labelled_and_review_forced():
    result = processing_mod.process_article(
        _article(),
        ALIAS_INDEX,
        KNOWN,
        SECTOR_BY_TICKER,
        TICKER_BY_ID,
        NAME_BY_ID,
        adapter=None,
    )
    assert result["record"]["processor"] == "RULE_BASED"
    assert result["record"]["ticker_symbols"] == ["HUBC"]
    assert result["record"]["event_category"] == "earnings"
    # Fallback confidence caps at 0.70, below the 0.80 review line.
    assert result["status"] == "REVIEW"
    assert result["force_review"] is True


def test_processing_unknown_ticker_text_yields_no_tickers():
    result = processing_mod.process_article(
        _article(
            title="Markets rally on strong sentiment",
            text="Markets rally on strong sentiment today.",
        ),
        ALIAS_INDEX,
        KNOWN,
        SECTOR_BY_TICKER,
        TICKER_BY_ID,
        NAME_BY_ID,
        adapter=None,
    )
    assert result["record"]["ticker_symbols"] == []


def test_processing_malformed_llm_output_rejected():
    class BadAdapter:
        def process(self, _text, _instruction):
            return "{not json"

    result = processing_mod.process_article(
        _article(),
        ALIAS_INDEX,
        KNOWN,
        SECTOR_BY_TICKER,
        TICKER_BY_ID,
        NAME_BY_ID,
        adapter=BadAdapter(),
    )
    assert result["status"] == "REJECTED"
    assert result["record"] is None
    assert result["errors"]


def test_processing_llm_output_with_unknown_ticker_rejected():
    import json as _json

    class FakeAdapter:
        def process(self, _text, _instruction):
            return _json.dumps(_valid_record(ticker_symbols=["FAKE"]))

    result = processing_mod.process_article(
        _article(),
        ALIAS_INDEX,
        KNOWN,
        SECTOR_BY_TICKER,
        TICKER_BY_ID,
        NAME_BY_ID,
        adapter=FakeAdapter(),
    )
    assert result["status"] == "REJECTED"


# --- impact ---------------------------------------------------------------


def test_impact_company_material_category_scores_high():
    assessed = impact_mod.assess_impact(
        _valid_record(), "official_primary", sector_match=True
    )
    assert assessed["status"] == "assessed"
    assert assessed["importance_score"] >= 0.6
    assert assessed["credibility_score"] == 1.00


def test_impact_no_scope_is_insufficient_data():
    assessed = impact_mod.assess_impact(
        _valid_record(ticker_symbols=[], sector_names=[], event_category="other"),
        "unverified",
    )
    assert assessed["status"] == "INSUFFICIENT_DATA"


def test_impact_conflicts_preserved_side_by_side():
    assessed = impact_mod.assess_impact(
        _valid_record(),
        "established_press",
        conflicting_records=[{"summary": "contradicting version"}],
    )
    assert assessed["counterarguments"]


# --- market reaction / event study ------------------------------------------


def test_reaction_single_price_date_is_insufficient():
    result = reaction_mod.compute_reaction(
        date(2026, 11, 4),
        [{"trading_date": date(2026, 11, 3), "close": Decimal("100"), "volume": 1000}],
    )
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["missing"]  # every window names its missing piece


def test_reaction_partial_series_keeps_computed_windows():
    # Windows anchor on the POST session (first obs after the event
    # date). With only one session after post, the 1-day window
    # computes but 5/10/20-day windows are missing, so the study
    # status is INSUFFICIENT_DATA while the computed window is kept
    # (not zeroed, not dropped).
    prices = [
        {"trading_date": date(2026, 11, 2), "close": Decimal("100"), "volume": 1000},
        {"trading_date": date(2026, 11, 3), "close": Decimal("110"), "volume": 1200},
        {"trading_date": date(2026, 11, 4), "close": Decimal("121"), "volume": 900},
        {"trading_date": date(2026, 11, 5), "close": Decimal("133.1"), "volume": 800},
    ]
    result = reaction_mod.compute_reaction(date(2026, 11, 3), prices)
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["company_returns"]["return_1d"] == "0.1"
    assert result["company_returns"]["return_5d"] is None
    assert any("5-day window" in m for m in result["missing"])
    assert "No causality is claimed" in result["note"]


def test_reaction_full_series_computes_all_windows():
    from datetime import timedelta

    base = date(2026, 10, 1)
    prices = [
        {
            "trading_date": base + timedelta(days=k),
            "close": Decimal("100") * (Decimal("1.01") ** k),
            "volume": 1000,
        }
        for k in range(26)
    ]
    result = reaction_mod.compute_reaction(base + timedelta(days=4), prices)
    assert result["status"] == "computed"
    assert result["company_returns"]["return_1d"] == "0.01"
    assert all(
        result["company_returns"][f"return_{w}d"] is not None
        for w in (1, 5, 10, 20)
    )


# --- leakage guards ------------------------------------------------------------


def test_leakage_future_news_excluded():
    aware = datetime(2026, 11, 5, 10, 0, tzinfo=timezone.utc)
    usable, _reason = leakage_mod.usable_for_forecast(
        datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc), aware
    )
    assert usable is False
    usable, _reason = leakage_mod.usable_for_forecast(
        datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc), aware
    )
    assert usable is True


def test_leakage_naive_timestamps_rejected():
    usable, _reason = leakage_mod.usable_for_forecast(
        datetime(2026, 11, 4, 10, 0),
        datetime(2026, 11, 5, 10, 0, tzinfo=timezone.utc),
    )
    assert usable is False
    usable, _reason = leakage_mod.usable_for_forecast(
        None, datetime(2026, 11, 5, 10, 0, tzinfo=timezone.utc)
    )
    assert usable is False


# --- RAG news ------------------------------------------------------------


def _docs():
    return [
        {
            "id": 1,
            "title": "HUBC announces dividend",
            "summary": "HUBC board approves dividend payout.",
            "source": "Test",
            "canonical_url": "https://example.invalid/1",
            "published_at": "2026-11-04",
            "tickers": ["HUBC"],
            "sectors": ["Power Generation & Distribution"],
            "event_category": "dividends",
        },
        {
            "id": 2,
            "title": "OGDC gas discovery",
            "summary": "OGDC reports a new gas discovery.",
            "source": "Test",
            "canonical_url": "https://example.invalid/2",
            "published_at": "2026-11-03",
            "tickers": ["OGDC"],
            "sectors": ["Oil & Gas Exploration"],
            "event_category": "oil_gas",
        },
    ]


def test_rag_token_scoring_and_ticker_bonus():
    result = rag_news_mod.search_news(_docs(), "HUBC dividend")
    assert result["results"][0]["id"] == 1
    assert result["results"][0]["score"] > 0


def test_rag_zero_score_never_returned():
    result = rag_news_mod.search_news(_docs(), "zebra quantum")
    assert result["results"] == []


def test_rag_metadata_filter_applies_before_scoring():
    # OGDC survives the ticker filter but has zero token overlap
    # with "dividend", and the ticker bonus requires overlap, so
    # nothing is returned (a ticker match alone never returns a
    # document that says nothing about the query).
    result = rag_news_mod.search_news(_docs(), "dividend", ticker="OGDC")
    assert result["results"] == []


def test_rag_ticker_bonus_applies_with_overlap():
    result = rag_news_mod.search_news(_docs(), "gas", ticker="OGDC")
    assert result["results"][0]["id"] == 2
    assert result["results"][0]["score"] >= 5.0  # token + phrase + ticker bonus


def test_rag_snippet_capped():
    result = rag_news_mod.search_news(_docs(), "dividend")
    for r in result["results"]:
        assert len(r["snippet"]) <= 500


# --- assistant --------------------------------------------------------------


def test_assistant_recommendation_is_uncertainty():
    answer = assistant_mod.answer_question("Should I buy HUBC?", _docs())
    assert answer["answer_kind"] == "uncertainty"


def test_assistant_dividend_question_cites_source():
    answer = assistant_mod.answer_question("Show me HUBC dividends", _docs())
    assert answer["answer_kind"] == "direct_evidence"
    assert answer["citations"]
    assert all(c["canonical_url"] for c in answer["citations"])


def test_assistant_missing_data_carries_no_citation():
    # LUCK is named (all-caps) but has no stored documents, so the
    # dividends shape must NOT answer with HUBC's dividends.
    answer = assistant_mod.answer_question("Show me LUCK dividends", _docs())
    assert answer["answer_kind"] == "missing_data"
    assert answer["citations"] == []


def test_assistant_named_ticker_scopes_dividends():
    answer = assistant_mod.answer_question("Show me HUBC dividends", _docs())
    assert answer["answer_kind"] == "direct_evidence"
    assert len(answer["citations"]) == 1
    assert "HUBC" in answer["citations"][0]["title"]


# --- jobs spec ------------------------------------------------------------


def test_jobs_spec_two_paused_one_active():
    from app.services.news_intelligence.jobs_spec import NEWS_JOB_DEFINITIONS
    from app.services.jobs.handlers import HANDLERS

    assert len(NEWS_JOB_DEFINITIONS) == 3
    by_key = {d["job_key"]: d for d in NEWS_JOB_DEFINITIONS}
    assert by_key["news_collection_daily"]["status"] == "paused"
    assert by_key["news_reconciliation_post_close"]["status"] == "paused"
    assert by_key["news_digest"]["status"] == "active"
    for d in NEWS_JOB_DEFINITIONS:
        assert d["handler_key"] in HANDLERS


def test_registry_includes_news_jobs():
    from app.services.jobs.registry import JOB_DEFINITIONS

    keys = {d["job_key"] for d in JOB_DEFINITIONS}
    assert "news_collection_daily" in keys
    assert "news_digest" in keys


# --- API smoke tests (TestClient + SQLite, established jobs-test pattern) ---

API_TABLES = (
    "news_sources",
    "news_articles",
    "news_article_entities",
    "news_sentiment_assessments",
    "news_impact_assessments",
    "news_market_reactions",
    "news_collection_runs",
    "news_events",
    "news_event_companies",
    "companies",
    "securities",
    "sectors",
)


def _api_client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import create_app
    from app.models.news_events import NewsSource
    from app.models.reference import Company, Security

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/news_api.db")
    get_settings.cache_clear()
    app = create_app()
    engine = app.state.engine
    assert engine is not None
    tables = [t for n, t in Base.metadata.tables.items() if n in API_TABLES]
    Base.metadata.create_all(engine, tables=tables)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        # Explicit ids: reference models use IdMixin Identity, which
        # does not auto-generate on SQLite (pre-existing design).
        session.add(
            Company(id=10, legal_name="Hub Power Company Limited")
        )
        session.add(Security(id=100, company_id=10, ticker="HUBC"))
        session.add(
            NewsSource(
                id=1,
                source_key="psx_announcements",
                name="PSX Announcements",
                source_type="official",
                collection_policy="TERMS_GATED",
                terms_note="Written permission required.",
            )
        )
        article = NewsArticle(
            article_id="api-1",
            title="HUBC announces dividend",
            source="Test",
            canonical_url="https://example.invalid/1",
            summary="HUBC announces dividend",
            content_hash="api-hash-1",
            processor="RULE_BASED",
            status="REVIEW",
            quality_status="UNVERIFIED",
        )
        session.add(article)
        session.flush()
        session.add(
            NewsArticleEntity(
                article_id=article.id,
                company_id=10,
                ticker="HUBC",
                match_type="TICKER",
                match_confidence=1.0,
                needs_review=False,
            )
        )
        session.add(
            NewsSentimentAssessment(
                article_id=article.id,
                sentiment="positive",
                event_category="dividends",
                relevance_score=0.6,
                impact_score=0.7,
                confidence_score=0.7,
                potential_impact_horizon="short_term",
                extracted_facts=["HUBC announces dividend"],
                supporting_evidence=[],
                uncertainty_notes=[],
                risk_factors=[],
                processor="RULE_BASED",
            )
        )
        session.commit()
    return TestClient(app, raise_server_exceptions=False)


def test_api_feed_and_company_news(tmp_path, monkeypatch):
    client = _api_client(tmp_path, monkeypatch)
    feed = client.get("/api/v1/news-intelligence/feed")
    assert feed.status_code == 200
    assert len(feed.json()["articles"]) == 1
    assert feed.json()["articles"][0]["tickers"] == ["HUBC"]
    filtered = client.get("/api/v1/news-intelligence/feed?ticker=OGDC")
    assert filtered.json()["articles"] == []
    company = client.get("/api/v1/news-intelligence/companies/HUBC/news")
    assert company.status_code == 200
    assert len(company.json()["articles"]) == 1
    unknown = client.get("/api/v1/news-intelligence/companies/FAKE/news")
    assert unknown.status_code == 404


def test_api_impact_sources_quality(tmp_path, monkeypatch):
    client = _api_client(tmp_path, monkeypatch)
    assert client.get("/api/v1/news-intelligence/impact").status_code == 200
    sources = client.get("/api/v1/news-intelligence/sources")
    assert sources.status_code == 200
    assert sources.json()["sources"][0]["collection_policy"] == "TERMS_GATED"
    quality = client.get("/api/v1/news-intelligence/quality")
    assert quality.status_code == 200
    assert quality.json()["articles_by_status"] == {"REVIEW": 1}


def test_api_assistant_shapes(tmp_path, monkeypatch):
    client = _api_client(tmp_path, monkeypatch)
    dividends = client.get(
        "/api/v1/news-intelligence/assistant",
        params={"q": "Show me HUBC dividends"},
    )
    assert dividends.status_code == 200
    assert dividends.json()["answer_kind"] == "direct_evidence"
    assert len(dividends.json()["citations"]) == 1
    assert dividends.json()["retrieval"] == "FULL_TEXT_FALLBACK"
    rec = client.get(
        "/api/v1/news-intelligence/assistant",
        params={"q": "Should I buy HUBC?"},
    )
    assert rec.json()["answer_kind"] == "uncertainty"
    assert rec.json()["citations"] == []
    missing = client.get(
        "/api/v1/news-intelligence/assistant",
        params={"q": "Show me LUCK dividends"},
    )
    assert missing.json()["answer_kind"] == "missing_data"
    assert missing.json()["citations"] == []


# --- SQLite model tests ------------------------------------------------------


@pytest.fixture()
def sqlite_session():
    engine = create_engine("sqlite:///:memory:")
    tables = [
        Base.metadata.tables[name]
        for name in (
            "news_articles",
            "news_sentiment_assessments",
            "news_summaries",
            "news_article_entities",
            "news_impact_assessments",
            "news_market_reactions",
            "news_collection_runs",
            "news_model_evaluations",
            "news_event_evidence",
        )
    ]
    Base.metadata.create_all(engine, tables=tables)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    yield session
    session.close()


def test_model_article_roundtrip(sqlite_session):
    row = NewsArticle(
        article_id="fp-test-1",
        title="HUBC announces dividend",
        source="Test",
        canonical_url="https://example.invalid/1",
        summary="HUBC announces dividend",
        content_hash="hash-test-1",
        processor="RULE_BASED",
        status="REVIEW",
        quality_status="UNVERIFIED",
    )
    sqlite_session.add(row)
    sqlite_session.flush()
    sqlite_session.add(
        NewsSentimentAssessment(
            article_id=row.id,
            sentiment="positive",
            event_category="dividends",
            relevance_score=0.6,
            impact_score=0.7,
            confidence_score=0.7,
            potential_impact_horizon="short_term",
            extracted_facts=["HUBC announces dividend"],
            supporting_evidence=[],
            uncertainty_notes=[],
            risk_factors=[],
            processor="RULE_BASED",
        )
    )
    sqlite_session.commit()
    found = sqlite_session.query(NewsArticle).filter_by(article_id="fp-test-1").one()
    assert found.status == "REVIEW"
    assert found.quality_status == "UNVERIFIED"
    assert (
        sqlite_session.query(NewsSentimentAssessment)
        .filter_by(article_id=found.id)
        .one()
        .sentiment
        == "positive"
    )


def test_model_content_hash_unique(sqlite_session):
    def _row(article_id, content_hash):
        return NewsArticle(
            article_id=article_id,
            title="t",
            source="s",
            canonical_url="https://example.invalid/x",
            summary="s",
            content_hash=content_hash,
            processor="RULE_BASED",
            status="REVIEW",
        )

    sqlite_session.add(_row("a1", "same-hash"))
    sqlite_session.commit()
    sqlite_session.add(_row("a2", "same-hash"))
    with pytest.raises(IntegrityError):
        sqlite_session.commit()
    sqlite_session.rollback()


def test_runner_persist_and_duplicate_skip(sqlite_session):
    from app.services.news_intelligence import runner as runner_mod

    # process_article needs a resolver index; the runner's persist
    # path takes the pipeline result directly.
    result = {
        "status": "REVIEW",
        "record": _valid_record(),
        "errors": [],
        "ungrounded": [],
        "force_review": True,
        "processor": "RULE_BASED",
    }
    item = _article()
    item["_ticker_by_company_id"] = {}
    item["_sector_by_ticker"] = {}
    item["_resolver_matches"] = []
    first = runner_mod.persist_result(sqlite_session, result, item)
    assert first["action"] == "stored"
    second = runner_mod.persist_result(sqlite_session, result, item)
    assert second["action"] == "skipped_duplicate"
    sqlite_session.rollback()


def test_runner_ticker_maps_use_real_schema_columns():
    """Regression: build_ticker_maps must query legal_name / sectors.name
    (the real column names), not company_name / sector_name. Builds a
    minimal registry in SQLite and checks the maps resolve by ticker."""
    from app.models.reference import Company, Sector, Security
    from app.services.news_intelligence import runner as runner_mod

    engine = create_engine("sqlite:///:memory:")
    tables = [
        Base.metadata.tables[name]
        for name in ("companies", "securities", "sectors")
    ]
    Base.metadata.create_all(engine, tables=tables)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    # Explicit ids: the reference models use IdMixin BigInteger
    # Identity, which does not auto-generate on SQLite (pre-existing
    # Phase 3/4 design; this test only exercises the ticker maps).
    sector = Sector(
        id=1,
        name="Power Generation & Distribution",
        source_sector_name="Power Generation & Distribution",
        source="test",
    )
    session.add(sector)
    session.flush()
    company = Company(
        id=10, legal_name="Hub Power Company Limited", sector_id=sector.id
    )
    session.add(company)
    session.flush()
    session.add(Security(id=100, company_id=company.id, ticker="HUBC"))
    session.commit()
    known, sector_by_ticker, ticker_by_id, name_by_id = (
        runner_mod.build_ticker_maps(session)
    )
    assert "HUBC" in known
    assert ticker_by_id[company.id] == "HUBC"
    assert name_by_id[company.id] == "Hub Power Company Limited"
    assert sector_by_ticker["HUBC"] == "Power Generation & Distribution"
    session.close()


def test_runner_persist_reaction_insufficient_data(sqlite_session):
    from app.models.news_intelligence import NewsMarketReaction
    from app.services.news_intelligence import runner as runner_mod

    reaction = {
        "status": "INSUFFICIENT_DATA",
        "pre_price": None,
        "event_day_price": None,
        "post_price": None,
        "company_returns": {"return_1d": None},
        "volume_change": None,
        "benchmark_returns": {},
        "sector_returns": {},
        "excess_vs_benchmark": {},
        "missing": ["no price observation after the event date"],
        "note": "Returns are simple returns on actual closes. No causality is claimed.",
    }
    out = runner_mod.persist_reaction(
        sqlite_session, reaction, event_id=1, event_date=date(2026, 11, 4)
    )
    assert out["action"] == "stored"
    row = sqlite_session.query(NewsMarketReaction).one()
    assert row.status == "INSUFFICIENT_DATA"
    assert row.event_id == 1
    assert row.returns == {"return_1d": None}
    sqlite_session.rollback()


def test_runner_rejected_not_persisted(sqlite_session):
    from app.services.news_intelligence import runner as runner_mod

    result = {
        "status": "REJECTED",
        "record": None,
        "errors": ["not json"],
        "ungrounded": [],
        "force_review": True,
    }
    out = runner_mod.persist_result(sqlite_session, result, _article())
    assert out["action"] == "not_persisted"
    assert sqlite_session.query(NewsArticle).count() == 0
