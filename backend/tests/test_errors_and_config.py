"""Error-handling and environment-validation tests.

Error responses must be generic JSON: no stack trace, no traceback
module path, no secret. Environment validation is exercised directly
against the Settings model and through the app factory.
"""

from __future__ import annotations

import pytest
from fastapi import Query
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app


def test_unknown_route_returns_json_without_traceback(client: TestClient) -> None:
    resp = client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "not_found"
    assert "traceback" not in resp.text.lower()
    assert 'File "' not in resp.text


def test_wrong_method_returns_json_without_traceback(client: TestClient) -> None:
    resp = client.post("/api/v1/health")
    assert resp.status_code == 405
    assert "traceback" not in resp.text.lower()


def test_validation_error_shape_has_no_traceback_or_body(client: TestClient) -> None:
    """Trigger FastAPI validation via a typed query param on a test-only route."""
    app = create_app()

    @app.get("/_test-validated")
    def _validated(limit: int = Query(ge=1, le=10)) -> dict[str, int]:
        return {"limit": limit}

    with TestClient(app, raise_server_exceptions=False) as test_client:
        resp = test_client.get("/_test-validated?limit=not-a-number")
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"] == "validation_error"
        assert "traceback" not in resp.text.lower()
        resp2 = test_client.get("/_test-validated?limit=999")
        assert resp2.status_code == 422


def test_wildcard_cors_rejected_in_production() -> None:
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", CORS_ORIGINS=("*",))


def test_debug_rejected_in_production() -> None:
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", DEBUG=True)


def test_wildcard_cors_allowed_in_development() -> None:
    settings = Settings(ENVIRONMENT="development", CORS_ORIGINS=("*",))
    assert "*" in settings.CORS_ORIGINS


def test_blank_database_url_becomes_unset() -> None:
    settings = Settings(DATABASE_URL="   ")
    assert settings.DATABASE_URL is None


def test_invalid_environment_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="staging")  # type: ignore[arg-type]
