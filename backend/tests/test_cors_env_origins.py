"""Regression tests: CORS_ORIGINS from the environment.

Backend-correction finding (2026-11-05): the documented env format is
comma-separated (see backend/.env.example), but pydantic-settings
JSON-decodes complex fields from env before validators run, so a plain
origin string crashed boot with SettingsError. The host path sets the
deployed Netlify origin via this env var, so the crash blocked a clean
hosted start. Settings.CORS_ORIGINS is annotated NoDecode and the
before-validator splits comma-separated strings (and accepts a JSON
list). These tests pin the env path, which no earlier test covered:
existing config tests only passed tuples at init time.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import DEFAULT_CORS_ORIGINS, Settings, get_settings
from app.main import create_app

NETLIFY_ORIGIN = "https://gentle-sopapillas-f33c78.netlify.app"


def _client_with_env(monkeypatch: pytest.MonkeyPatch, **env: str) -> TestClient:
    for key in ("ENVIRONMENT", "AUTH_ENFORCEMENT", "CORS_ORIGINS", "DEBUG"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def test_env_single_origin_parses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", NETLIFY_ORIGIN)
    get_settings.cache_clear()
    try:
        assert Settings().CORS_ORIGINS == (NETLIFY_ORIGIN,)
    finally:
        get_settings.cache_clear()


def test_env_comma_separated_parses_and_strips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS", "http://localhost:3000, https://example.com ,"
    )
    get_settings.cache_clear()
    try:
        assert Settings().CORS_ORIGINS == (
            "http://localhost:3000",
            "https://example.com",
        )
    finally:
        get_settings.cache_clear()


def test_env_json_list_parses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["https://a.example.com", "https://b.example.com"]')
    get_settings.cache_clear()
    try:
        assert Settings().CORS_ORIGINS == (
            "https://a.example.com",
            "https://b.example.com",
        )
    finally:
        get_settings.cache_clear()


def test_env_wildcard_still_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_ENFORCEMENT", "on")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="must not contain"):
            Settings()
    finally:
        get_settings.cache_clear()


def test_defaults_unchanged_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    get_settings.cache_clear()
    try:
        assert Settings().CORS_ORIGINS == DEFAULT_CORS_ORIGINS
    finally:
        get_settings.cache_clear()


def test_client_allows_configured_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = _client_with_env(
        monkeypatch,
        ENVIRONMENT="development",
        AUTH_ENFORCEMENT="off",
        CORS_ORIGINS=NETLIFY_ORIGIN,
    )
    with client:
        response = client.get("/api/v1/health", headers={"Origin": NETLIFY_ORIGIN})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == NETLIFY_ORIGIN
        preflight = client.options(
            "/api/v1/health",
            headers={
                "Origin": NETLIFY_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers.get("access-control-allow-origin") == NETLIFY_ORIGIN
    get_settings.cache_clear()


def test_client_does_not_allow_unconfigured_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = _client_with_env(
        monkeypatch, ENVIRONMENT="development", AUTH_ENFORCEMENT="off"
    )
    with client:
        response = client.get("/api/v1/health", headers={"Origin": NETLIFY_ORIGIN})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") is None
    get_settings.cache_clear()
