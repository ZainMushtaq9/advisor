"""Phase 24 auth/security tests — pure + SQLite-backed + API.

No real PostgreSQL, no network. SQLite strips tzinfo on read;
the service reattaches UTC (see service._as_aware), so token
expiry and lockout behave identically on both backends.

Every acceptance item is tested: least-privilege roles are
enforced (matrix + role/permission dependencies + CLI admin
proof); secrets are never stored or returned (hashes only,
audit detail stripped, public views clean); high-risk
vulnerabilities are blocked (SQLi-shaped input, path
traversal, bad tokens, expired/revoked tokens, lockout);
agent tool boundaries hold (no execution identifiers in new
code); audit trails are append-only and complete.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings, get_settings
from app.main import create_app
from app.models.auth import AuthAuditLog, AuthToken, AuthUser
from app.services.auth import ROLES, has_permission, permissions_for
from app.services.auth.middleware import RateLimiter
from app.services.auth.passwords import (
    hash_password,
    password_policy_errors,
    verify_password,
)
from app.services.auth.service import (
    audit,
    authenticate,
    create_user,
    issue_token,
    public_user,
    revoke_token,
    set_user_active,
    set_user_role,
    validate_token,
)
from app.services.auth.tokens import (
    is_expired,
    new_token,
    token_hash,
    token_prefix,
)

NOW = datetime(2026, 11, 5, 3, 0, tzinfo=timezone.utc)
STRONG = "Correct-Horse-Battery-99!"


# ---------------------------------------------------------------------------
# Pure: passwords
# ---------------------------------------------------------------------------


def test_password_policy() -> None:
    assert password_policy_errors("short")  # too short
    assert password_policy_errors("alllowercasepassword")  # 1 class
    assert password_policy_errors("password1234")  # blocklisted
    assert password_policy_errors(STRONG) == []


def test_password_hash_verify_and_salt_uniqueness() -> None:
    stored1, _ = hash_password(STRONG)
    stored2, _ = hash_password(STRONG)
    assert stored1 != stored2  # fresh salt every call
    assert verify_password(STRONG, stored1)
    assert not verify_password("wrong-password-123!", stored1)
    assert not verify_password(STRONG, "not-a-valid-stored-value")
    assert not verify_password(STRONG, "md5$1$abcd$efgh")  # wrong algo
    assert stored1.startswith("pbkdf2_sha256$600000$")


# ---------------------------------------------------------------------------
# Pure: tokens
# ---------------------------------------------------------------------------


def test_token_shape_hash_prefix_and_expiry() -> None:
    token = new_token()
    assert token.startswith("psx_")
    assert token_hash(token) != token
    assert len(token_hash(token)) == 64
    assert token_prefix(token) == token[:8]
    future = NOW + timedelta(hours=1)
    past = NOW - timedelta(seconds=1)
    assert not is_expired(future, NOW)
    assert is_expired(past, NOW)
    assert is_expired(future, NOW.replace(tzinfo=None))  # naive now: closed
    assert is_expired(future.replace(tzinfo=None), NOW)  # naive expiry: closed


# ---------------------------------------------------------------------------
# Pure: roles / least privilege
# ---------------------------------------------------------------------------


def test_role_matrix_least_privilege() -> None:
    assert set(ROLES) == {
        "user",
        "analyst",
        "administrator",
        "read_only_agent",
        "service_process",
    }
    assert permissions_for("user") == ("read:public",)
    assert permissions_for("read_only_agent") == ("read:public",)
    assert "manage:users" not in permissions_for("analyst")
    assert "manage:tokens" not in permissions_for("analyst")
    assert "read:audit" not in permissions_for("service_process")
    assert "read:audit" not in permissions_for("user")
    assert set(permissions_for("administrator")) == {
        "read:public",
        "read:internal",
        "read:audit",
        "manage:users",
        "manage:tokens",
    }
    assert permissions_for("nobody") == ()  # unknown role: fail closed
    assert not has_permission("user", "manage:users")
    assert has_permission("administrator", "manage:users")


def test_rate_limiter_window() -> None:
    limiter = RateLimiter()
    for _ in range(5):
        allowed, _ = limiter.allow("k", 5, 60, now=1000.0)
        assert allowed
    allowed, retry = limiter.allow("k", 5, 60, now=1001.0)
    assert not allowed and retry > 0
    allowed, _ = limiter.allow("k", 5, 60, now=2000.0)  # new window
    assert allowed


# ---------------------------------------------------------------------------
# SQLite-backed service tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session():  # type: ignore[no-untyped-def]
    engine = create_engine("sqlite:///:memory:")
    from app.database import Base

    wanted = {"auth_users", "auth_tokens", "auth_audit_logs"}
    tables = [t for name, t in Base.metadata.tables.items() if name in wanted]
    Base.metadata.create_all(engine, tables=tables)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def test_create_user_and_public_view(db_session) -> None:  # type: ignore[no-untyped-def]
    user, errors = create_user(db_session, "cli-admin", "alice", STRONG, "analyst")
    assert errors == [] and user is not None
    view = public_user(user)
    assert view["username"] == "alice" and view["role"] == "analyst"
    assert "password_hash" not in view and "password_salt" not in view
    # Duplicate, weak password, unknown role: nothing written for them.
    _, errors = create_user(db_session, "cli-admin", "alice", STRONG, "analyst")
    assert any("already exists" in e for e in errors)
    _, errors = create_user(db_session, "cli-admin", "bob", "short", "analyst")
    assert errors
    _, errors = create_user(db_session, "cli-admin", "carol", STRONG, "superuser")
    assert any("unknown role" in e for e in errors)
    assert db_session.query(AuthUser).count() == 1


def test_authenticate_lockout_and_reset(db_session) -> None:  # type: ignore[no-untyped-def]
    create_user(db_session, "cli-admin", "dave", STRONG, "user")
    user, reason = authenticate(db_session, "dave", STRONG, now=NOW)
    assert user is not None and reason == "ok"
    for _ in range(4):
        user, reason = authenticate(db_session, "dave", "wrong-pass-123!", now=NOW)
        assert user is None and reason == "bad_password"
    user, reason = authenticate(db_session, "dave", "wrong-pass-123!", now=NOW)
    assert user is None and reason == "locked"  # 5th failure locks
    # Locked: even the RIGHT password is denied without checking it.
    user, reason = authenticate(db_session, "dave", STRONG, now=NOW)
    assert user is None and reason == "locked"
    # After the lockout window, the right password works and resets.
    later = NOW + timedelta(minutes=16)
    user, reason = authenticate(db_session, "dave", STRONG, now=later)
    assert user is not None and reason == "ok"
    assert user.failed_logins == 0 and user.locked_until is None


def test_disabled_user_denied(db_session) -> None:  # type: ignore[no-untyped-def]
    create_user(db_session, "cli-admin", "erin", STRONG, "user")
    set_user_active(db_session, "cli-admin", "erin", False)
    user, reason = authenticate(db_session, "erin", STRONG, now=NOW)
    assert user is None and reason == "disabled"


def test_token_issue_validate_revoke_expiry(db_session) -> None:  # type: ignore[no-untyped-def]
    create_user(db_session, "cli-admin", "fran", STRONG, "user")
    user, _ = authenticate(db_session, "fran", STRONG, now=NOW)
    assert user is not None
    # Service tokens are denied to plain users.
    token, reason = issue_token(db_session, "cli-admin", user, "service", now=NOW)
    assert token is None and reason == "role_not_allowed"
    token, reason = issue_token(db_session, "cli-admin", user, "user", now=NOW)
    assert token is not None and reason == "ok"
    # Only the hash is stored; the token itself never appears in rows.
    rows = db_session.query(AuthToken).all()
    assert len(rows) == 1 and rows[0].token_hash != token
    assert rows[0].token_hash == token_hash(token)
    assert rows[0].prefix == token_prefix(token)
    owner, reason = validate_token(db_session, token, now=NOW)
    assert owner is not None and owner.username == "fran"
    assert validate_token(db_session, "psx_bogus", now=NOW)[0] is None
    assert validate_token(db_session, "not-a-token", now=NOW)[0] is None
    # Expiry: move the row's expiry into the past.
    rows[0].expires_at = NOW - timedelta(seconds=1)
    db_session.commit()
    assert validate_token(db_session, token, now=NOW) == (None, "expired")
    # Revocation by prefix.
    token2, _ = issue_token(db_session, "cli-admin", user, "user", now=NOW)
    assert token2 is not None
    assert revoke_token(db_session, "cli-admin", token_prefix(token2), now=NOW)
    assert validate_token(db_session, token2, now=NOW) == (None, "revoked")


def test_audit_detail_never_carries_secrets(db_session) -> None:  # type: ignore[no-untyped-def]
    audit(
        db_session,
        "cli-admin",
        "token_issued",
        "success",
        target="alice",
        detail={"password": "should-be-stripped", "token": "also-stripped", "role": "analyst"},
    )
    db_session.commit()
    row = db_session.query(AuthAuditLog).one()
    assert row.detail == {"role": "analyst"}
    # Audit rows are append-only: this module exposes no update/delete.
    import app.services.auth.service as svc

    assert not hasattr(svc, "delete_audit")
    assert not hasattr(svc, "update_audit")


def test_role_change_requires_known_role(db_session) -> None:  # type: ignore[no-untyped-def]
    create_user(db_session, "cli-admin", "gwen", STRONG, "user")
    done, _ = set_user_role(db_session, "cli-admin", "gwen", "analyst")
    assert done
    done, reason = set_user_role(db_session, "cli-admin", "gwen", "superuser")
    assert not done and reason == "unknown_role"
    done, reason = set_user_role(db_session, "cli-admin", "nobody", "analyst")
    assert not done and reason == "unknown_user"


# ---------------------------------------------------------------------------
# API tests (SQLite-backed app)
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_client(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    """App backed by a temp SQLite DB with seeded auth tables + users.

    Tokens are issued with real time (not the fixed NOW), so they
    are valid for the whole test run. Two companies are seeded so
    the SQL-injection probe can distinguish "parameterized" (0
    rows for an injection string) from "empty database".
    """
    db_path = tmp_path / "auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.delenv("AUTH_ENFORCEMENT", raising=False)
    get_settings.cache_clear()
    from app.database import Base

    app = create_app()
    engine = app.state.engine
    assert engine is not None
    # securities is included because the companies endpoint counts
    # a company's securities in every row it returns.
    wanted = {"auth_users", "auth_tokens", "auth_audit_logs", "companies", "securities"}
    tables = [t for name, t in Base.metadata.tables.items() if name in wanted]
    Base.metadata.create_all(engine, tables=tables)
    # Companies are seeded with explicit ids via raw SQL: the
    # reference Company model uses IdMixin (Identity), which
    # SQLite cannot auto-assign, so ORM inserts fail there.
    # Explicit ids are test setup only, never production code.
    from sqlalchemy import text

    factory = sessionmaker(bind=engine)
    with factory() as session:
        create_user(session, "bootstrap", "admin", STRONG, "administrator")
        create_user(session, "bootstrap", "analyst1", STRONG, "analyst")
        admin = session.query(AuthUser).filter_by(username="admin").one()
        token, _ = issue_token(session, "bootstrap", admin, "user")
        analyst = session.query(AuthUser).filter_by(username="analyst1").one()
        atoken, _ = issue_token(session, "bootstrap", analyst, "user")
        session.execute(
            text(
                "INSERT INTO companies (id, legal_name, status) VALUES "
                "(1, 'THE HUB POWER COMPANY LIMITED', 'UNVERIFIED'), "
                "(2, 'NISHAT MILLS LIMITED', 'UNVERIFIED')"
            )
        )
        session.commit()
    with TestClient(app, raise_server_exceptions=False) as client:
        client.admin_token = token  # type: ignore[attr-defined]
        client.analyst_token = atoken  # type: ignore[attr-defined]
        yield client
    get_settings.cache_clear()


def test_auth_status_public_and_me_flow(api_client) -> None:  # type: ignore[no-untyped-def]
    status = api_client.get("/api/v1/auth/status")
    assert status.status_code == 200
    body = status.json()
    assert body["enforcement"] == "off"
    assert body["admin_over_http"] is False
    assert body["login_over_http"] is False
    assert "administrator" in body["roles"]
    # /me without a token is 401; with a bad token 401; with a real one 200.
    assert api_client.get("/api/v1/auth/me").status_code == 401
    assert (
        api_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer psx_bogus"}).status_code
        == 401
    )
    me = api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {api_client.admin_token}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert "manage:users" in me.json()["permissions"]
    analyst = api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {api_client.analyst_token}"},
    )
    assert analyst.status_code == 200
    assert "manage:users" not in analyst.json()["permissions"]


def test_security_headers_present(api_client) -> None:  # type: ignore[no-untyped-def]
    resp = api_client.get("/api/v1/auth/status")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert resp.headers["Cache-Control"] == "no-store"  # auth routes: no-store


def test_auth_router_is_get_only() -> None:  # type: ignore[no-untyped-def]
    from app.api.v1.endpoints import auth as auth_endpoint

    methods = {tuple(sorted(route.methods)) for route in auth_endpoint.router.routes}
    assert methods == {("GET",)}


def test_enforced_mode_blocks_anonymous_but_not_health(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "enforced.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AUTH_ENFORCEMENT", "on")
    get_settings.cache_clear()
    from app.database import Base

    app = create_app()
    engine = app.state.engine
    assert engine is not None
    wanted = {"auth_users", "auth_tokens", "auth_audit_logs"}
    tables = [t for name, t in Base.metadata.tables.items() if name in wanted]
    Base.metadata.create_all(engine, tables=tables)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        create_user(session, "bootstrap", "admin", STRONG, "administrator")
        admin = session.query(AuthUser).filter_by(username="admin").one()
        token, _ = issue_token(session, "bootstrap", admin, "user")
    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/auth/status").status_code == 200
        assert client.get("/api/v1/system/status").status_code == 401
        assert (
            client.get(
                "/api/v1/system/status", headers={"Authorization": "Bearer bogus"}
            ).status_code
            == 401
        )
        ok = client.get(
            "/api/v1/system/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ok.status_code == 200
    get_settings.cache_clear()


def test_role_dependency_enforces(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """require_role: 401 without token, 403 for lesser role, 200 for admin.

    Standalone app (own SQLite engine) so the test does not depend
    on TestClient internals.
    """
    from fastapi import Depends, FastAPI

    from app.database import Base
    from app.services.auth.dependencies import require_role

    engine = create_engine(f"sqlite:///{tmp_path}/roles.db")
    wanted = {"auth_users", "auth_tokens", "auth_audit_logs"}
    tables = [t for name, t in Base.metadata.tables.items() if name in wanted]
    Base.metadata.create_all(engine, tables=tables)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        create_user(session, "bootstrap", "admin", STRONG, "administrator")
        create_user(session, "bootstrap", "analyst1", STRONG, "analyst")
        admin = session.query(AuthUser).filter_by(username="admin").one()
        admin_token, _ = issue_token(session, "bootstrap", admin, "user")
        analyst = session.query(AuthUser).filter_by(username="analyst1").one()
        analyst_token, _ = issue_token(session, "bootstrap", analyst, "user")

    app = FastAPI()
    app.state.engine = engine

    @app.get("/_test/admin-only")
    def _admin_only(principal: dict = Depends(require_role("administrator"))):  # type: ignore[no-untyped-def]
        return {"ok": True, "user": principal["username"]}

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/_test/admin-only").status_code == 401
        forbidden = client.get(
            "/_test/admin-only",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert forbidden.status_code == 403
        allowed = client.get(
            "/_test/admin-only",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert allowed.status_code == 200


def test_production_requires_enforcement() -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match="AUTH_ENFORCEMENT"):
        Settings(ENVIRONMENT="production")
    ok = Settings(ENVIRONMENT="production", AUTH_ENFORCEMENT="on")
    assert ok.AUTH_ENFORCEMENT == "on"


def test_no_execution_identifiers_in_auth_code() -> None:  # type: ignore[no-untyped-def]
    auth_dir = Path(__file__).resolve().parent.parent / "app" / "services" / "auth"
    endpoint = (
        Path(__file__).resolve().parent.parent / "app" / "api" / "v1" / "endpoints" / "auth.py"
    )
    banned = (
        "place_order",
        "execute_order",
        "submit_order",
        "execute_trade",
        "place_trade",
        "Broker",
        "broker_client",
        "/orders",
    )
    for path in list(auth_dir.rglob("*.py")) + [endpoint]:
        text = path.read_text()
        for token in banned:
            assert token not in text, f"{token} found in {path}"


def test_sqli_shaped_input_returns_no_data(api_client) -> None:  # type: ignore[no-untyped-def]
    """An injection-shaped search must match nothing (ORM parameters).

    A successful injection would return both seeded companies;
    parameterization returns zero, and a plain substring still
    finds its row — proving the filter works and is not bypassed.
    """
    injection = api_client.get("/api/v1/companies", params={"search": "' OR '1'='1"})
    assert injection.status_code == 200
    assert injection.json()["total"] == 0
    plain = api_client.get("/api/v1/companies", params={"search": "HUB"})
    assert plain.status_code == 200
    assert plain.json()["total"] == 1
    leak = api_client.get("/api/v1/companies/' OR '1'='1")
    assert leak.status_code in (404, 422)


def test_path_traversal_rejected(api_client) -> None:  # type: ignore[no-untyped-def]
    resp = api_client.get("/api/v1/reports/../../etc/passwd")
    assert resp.status_code == 404
    resp = api_client.get("/api/v1/companies/..%2F..%2Fetc%2Fpasswd")
    assert resp.status_code in (404, 422)
