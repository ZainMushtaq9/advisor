"""Endpoint tests: health, version, system status, config redaction."""

from __future__ import annotations

import sys

from fastapi.testclient import TestClient


def test_health_reports_ok(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["api_version"] == "v1"
    assert body["service"] == "psx-intelligence-ai"


def test_top_level_health_alias(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_system_version(client: TestClient) -> None:
    resp = client.get("/api/v1/system/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["app_version"] == "0.1.0"
    assert body["api_version"] == "v1"
    assert body["python_version"] == sys.version.split()[0]


def test_system_status_reports_real_versions_and_unavailable_db(client: TestClient) -> None:
    """No DATABASE_URL in this fixture, so db must NOT be reported ok."""
    resp = client.get("/api/v1/system/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["python_version"] == sys.version.split()[0]
    assert body["packages"]["fastapi"] != "not-installed"
    assert body["packages"]["sqlalchemy"] != "not-installed"
    assert body["database"]["status"] == "unavailable"
    assert body["database"]["reachable"] is False
    assert body["database"]["reason"] == "database_url_not_set"


def test_system_status_unreachable_db_is_not_ok(client_with_fake_db_url: TestClient) -> None:
    """A DATABASE_URL pointing at a non-running server must be unavailable."""
    resp = client_with_fake_db_url.get("/api/v1/system/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"]["status"] == "unavailable"
    assert body["database"]["reachable"] is False
    # Dialect name only; never the URL, host, user or password.
    assert body["database"]["dialect"] == "postgresql+psycopg"
    assert "fake-secret-123" not in resp.text
    assert "localhost" not in resp.text


def test_system_status_reachable_sqlite_reports_available(tmp_path, monkeypatch) -> None:
    """A reachable dev SQLite file reports available (dev-only path, Phase 1)."""
    from app.config import get_settings
    from app.main import create_app

    db_path = tmp_path / "dev.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    try:
        with TestClient(create_app(), raise_server_exceptions=False) as test_client:
            resp = test_client.get("/api/v1/system/status")
        assert resp.status_code == 200
        assert resp.json()["database"]["status"] == "available"
        assert resp.json()["database"]["reachable"] is True
    finally:
        get_settings.cache_clear()


def test_config_status_lists_names_only_and_redacts_values(
    client_with_fake_db_url: TestClient,
) -> None:
    resp = client_with_fake_db_url.get("/api/v1/config/status")
    assert resp.status_code == 200
    body = resp.json()
    names = {entry["name"]: entry for entry in body["settings"]}
    assert "DATABASE_URL" in names
    assert names["DATABASE_URL"]["status"] == "SET"
    assert names["DATABASE_URL"]["source"] == "environment"
    # Redaction: no value, no secret, no URL fragment anywhere in the body.
    assert "fake-secret-123" not in resp.text
    assert "postgresql" not in resp.text
    assert "psx_test" not in resp.text
    for entry in body["settings"]:
        assert set(entry.keys()) == {"name", "status", "source"}
        assert entry["status"] in ("SET", "MISSING")


def test_config_status_blank_db_url_counts_as_missing(monkeypatch) -> None:
    """DATABASE_URL= (blank) must not be reported as SET."""
    from app.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("DATABASE_URL", "")
    get_settings.cache_clear()
    try:
        with TestClient(create_app(), raise_server_exceptions=False) as test_client:
            resp = test_client.get("/api/v1/config/status")
        assert resp.status_code == 200
        names = {entry["name"]: entry for entry in resp.json()["settings"]}
        assert names["DATABASE_URL"]["status"] == "MISSING"
    finally:
        get_settings.cache_clear()


def test_config_status_missing_db_url(client: TestClient) -> None:
    resp = client.get("/api/v1/config/status")
    assert resp.status_code == 200
    names = {entry["name"]: entry for entry in resp.json()["settings"]}
    assert names["DATABASE_URL"]["status"] == "MISSING"
    assert names["DATABASE_URL"]["source"] == "unset"


def test_openapi_docs_are_served(client: TestClient) -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert "/api/v1/health" in spec["paths"]
    assert "/api/v1/system/status" in spec["paths"]
    assert "/api/v1/system/version" in spec["paths"]
    assert "/api/v1/config/status" in spec["paths"]
