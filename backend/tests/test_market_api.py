"""Phase 5 market API tests — offline, SQLite file DBs in tmp_path.

Prices below are TEST ONLY fixtures. Empty-state tests seed securities
but no market_prices rows, proving the API returns counts of 0 with
the scope note instead of 404s or fabricated rows.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import get_settings
from app.database import Base
from app.main import create_app
from app.models.governance import DataSource
from app.models.market import MarketPrice
from app.models.reference import Company, Security


def _install_sqlite_id_fallback() -> None:
    """TEST ONLY: see test_market_data.py — PostgreSQL Identity ids
    do not auto-generate on SQLite, so assign max(id)+1 on insert."""
    for model in (Company, Security, DataSource, MarketPrice):
        def _assign(mapper, connection, target, _model=model):  # noqa: ANN001, ANN202
            if target.id is None:
                value = connection.execute(
                    select(func.max(_model.__table__.c.id))
                ).scalar()
                target.id = (value or 0) + 1

        event.listen(model, "before_insert", _assign)


_install_sqlite_id_fallback()

KARACHI = ZoneInfo("Asia/Karachi")
SCOPE = "470 Main Board / Normal Counter snapshot securities"


@pytest.fixture()
def seeded_client(tmp_path, monkeypatch):
    """App backed by a SQLite file DB with 2 securities, optional prices."""
    db_path = tmp_path / "api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    app = create_app()
    engine = app.state.engine
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    company = Company(legal_name="Test Company A", status="UNVERIFIED")
    session.add(company)
    session.flush()
    testa = Security(company_id=company.id, ticker="TESTA", status="UNVERIFIED")
    session.add(testa)
    session.flush()
    testb = Security(company_id=company.id, ticker="TESTB", status="UNVERIFIED")
    session.add(testb)
    session.flush()
    source = DataSource(
        source_key="test_source",
        display_name="test_source",
        source_type="file_import",
        base_reference="TEST ONLY fixture",
    )
    session.add(source)
    session.flush()
    session.commit()
    ids = {"testa": testa.id, "testb": testb.id, "source": source.id}
    session.close()
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client, factory, ids
    finally:
        get_settings.cache_clear()
        engine.dispose()


def _add_price(factory, ids, trading_date, close, quality="UNVERIFIED", ticker_id=None):
    session = factory()
    price = MarketPrice(
        security_id=ticker_id or ids["testa"],
        data_source_id=ids["source"],
        trading_date=trading_date,
        bar_type="daily",
        open_price=100,
        high_price=105,
        low_price=99,
        close_price=close,
        volume=1000,
        turnover=100000,
        previous_close=99.5,
        is_adjusted=False,
        source_key="test_source",
        source_timestamp=datetime(2026, 11, 2, 16, 0, tzinfo=KARACHI),
        collected_at=datetime(2026, 11, 2, 17, 0, tzinfo=KARACHI),
        quality_status=quality,
    )
    session.add(price)
    session.commit()
    session.close()


def test_empty_states_return_zero_with_scope_note(seeded_client) -> None:
    client, _, _ = seeded_client
    status = client.get("/api/v1/market/status")
    assert status.status_code == 200
    body = status.json()
    assert body["market_prices_total"] == 0
    assert body["securities_with_observations"] == 0
    assert body["earliest_trading_date"] is None
    assert body["latest_trading_date"] is None
    assert body["counts_by_quality_status"]["UNVERIFIED"] == 0
    assert body["scope_note"] == SCOPE
    assert "KSE-100" not in body["scope_note"]

    prices = client.get("/api/v1/market/prices")
    assert prices.status_code == 200
    assert prices.json()["total"] == 0
    assert prices.json()["items"] == []
    assert prices.json()["scope_note"] == SCOPE

    latest = client.get("/api/v1/market/prices/TESTA/latest")
    assert latest.status_code == 200
    assert latest.json()["observation"] is None
    assert latest.json()["ticker"] == "TESTA"


def test_unknown_ticker_latest_is_404_but_list_is_empty(seeded_client) -> None:
    client, _, _ = seeded_client
    assert client.get("/api/v1/market/prices/NOPE/latest").status_code == 404
    resp = client.get("/api/v1/market/prices?ticker=NOPE")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_prices_list_newest_first_and_filters(seeded_client) -> None:
    from datetime import date

    client, factory, ids = seeded_client
    _add_price(factory, ids, date(2026, 11, 2), 103)
    _add_price(factory, ids, date(2026, 11, 3), 104, quality="PARTIALLY_VERIFIED")
    _add_price(factory, ids, date(2026, 11, 3), 200, ticker_id=ids["testb"])

    resp = client.get("/api/v1/market/prices")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["items"][0]["trading_date"] == "2026-11-03"
    row = body["items"][0]
    assert row["is_adjusted"] is False
    assert row["quality_status"] in ("UNVERIFIED", "PARTIALLY_VERIFIED")
    assert row["source_key"] == "test_source"
    assert row["collected_at"] is not None
    assert row["freshness"] == "CURRENT"

    by_ticker = client.get("/api/v1/market/prices?ticker=TESTB")
    assert by_ticker.json()["total"] == 1
    by_quality = client.get("/api/v1/market/prices?quality_status=PARTIALLY_VERIFIED")
    assert by_quality.json()["total"] == 1
    by_range = client.get("/api/v1/market/prices?from_date=2026-11-03&to_date=2026-11-03")
    assert by_range.json()["total"] == 2
    paged = client.get("/api/v1/market/prices?limit=2")
    assert len(paged.json()["items"]) == 2
    assert paged.json()["total"] == 3

    latest = client.get("/api/v1/market/prices/TESTA/latest")
    assert latest.json()["observation"]["trading_date"] == "2026-11-03"
    assert latest.json()["observation"]["close"] == 104.0

    status = client.get("/api/v1/market/status").json()
    assert status["market_prices_total"] == 3
    assert status["securities_with_observations"] == 2
    assert status["earliest_trading_date"] == "2026-11-02"
    assert status["latest_trading_date"] == "2026-11-03"
    assert status["counts_by_quality_status"]["UNVERIFIED"] == 2
    assert status["counts_by_quality_status"]["PARTIALLY_VERIFIED"] == 1


def test_invalid_params_rejected(seeded_client) -> None:
    client, _, _ = seeded_client
    assert client.get("/api/v1/market/prices?from_date=not-a-date").status_code == 422
    assert (
        client.get("/api/v1/market/prices?from_date=2026-11-03&to_date=2026-11-02").status_code
        == 422
    )
    assert client.get("/api/v1/market/prices?quality_status=BOGUS").status_code == 422
    assert client.get("/api/v1/market/prices?limit=999").status_code == 422


def test_unavailable_state_when_database_url_unset(client) -> None:
    for path in (
        "/api/v1/market/prices",
        "/api/v1/market/prices/TESTA/latest",
        "/api/v1/market/status",
    ):
        resp = client.get(path)
        assert resp.status_code == 503
        assert "DATABASE_URL" in resp.json()["detail"] or "not configured" in resp.json()["detail"]
