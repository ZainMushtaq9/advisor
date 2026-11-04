"""Phase 6 indicator API tests.

With DATABASE_URL unset (the shared ``client`` fixture), every
indicator endpoint must answer 503 truthfully — never a fake
empty market. Route registration is checked without a database.
Live-database behaviour is covered by the coordinator's live run
and the API documentation, not by faked sessions.
"""

from __future__ import annotations

from app.main import create_app


def test_indicator_routes_registered():
    app = create_app()
    paths = set(app.openapi()["paths"])
    assert "/api/v1/indicators/coverage" in paths
    assert "/api/v1/indicators/coverage/{ticker}" in paths
    assert "/api/v1/indicators/values" in paths
    assert "/api/v1/indicators/signals" in paths


def test_indicator_endpoints_503_without_db(client):
    for path in (
        "/api/v1/indicators/coverage",
        "/api/v1/indicators/coverage/OGDC",
        "/api/v1/indicators/values",
        "/api/v1/indicators/signals",
    ):
        response = client.get(path)
        assert response.status_code == 503, path
        assert "DATABASE_URL" in response.json()["detail"]


def test_indicator_values_bad_pagination_still_503_without_db(client):
    # Pagination validation happens after the session dependency,
    # so without a database the truthful 503 wins over a 422.
    response = client.get("/api/v1/indicators/values?limit=0")
    assert response.status_code == 503
