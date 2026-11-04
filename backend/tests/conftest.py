"""Shared test fixtures.

Each test builds a fresh app via ``create_app()`` after clearing the
cached settings, so monkeypatched env vars take effect. No test ever
touches a real PostgreSQL instance or any network service.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Test client with DATABASE_URL unset (DB truthfully unavailable)."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture()
def client_with_fake_db_url(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Client whose env DATABASE_URL contains a fake secret.

    Used only to prove /config/status never echoes values.
    """
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://tester:fake-secret-123@localhost:5432/psx_test"
    )
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    get_settings.cache_clear()


def _clear_settings_cache() -> None:
    get_settings.cache_clear()


def _env_without_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    os.environ.pop("DATABASE_URL", None)
