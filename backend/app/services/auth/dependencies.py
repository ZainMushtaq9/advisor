"""FastAPI authentication dependencies (Phase 24).

Two modes, driven by ``AUTH_ENFORCEMENT``:

- ``off`` (development default): requests are anonymous unless a
  Bearer token is presented, in which case it is validated and
  the principal is attached. Nothing is denied for lacking a
  token — this preserves the Phase 23 dashboard, which calls the
  public GET-only API without credentials.
- ``on`` (required in production — the app refuses to boot in
  production with enforcement off): every ``/api/v1`` request
  without a valid token is 401, and role-gated dependencies
  return 403 for insufficient roles. ``/health`` and
  ``/api/v1/auth/status`` stay public (they disclose mode and
  role names only, never secrets).

Token validation needs a database session; when the app has no
engine (DATABASE_URL unset), enforced mode fails closed with
401 for every API call — an unconfigured database must never
mean an unauthenticated API.

``require_role`` / ``require_permission`` are the enforcement
points for future write routes. No write route exists today
(the API is GET-only), so they are exercised by tests against a
mounted dummy route and documented as the mandatory pattern for
any route added later. A route that performs a state change
without one of these dependencies is a review failure.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_session_factory
from app.services.auth import has_permission
from app.services.auth.service import validate_token

_bearer = HTTPBearer(auto_error=False)

PUBLIC_PATHS = ("/health", "/api/v1/auth/status")


def _engine(request: Request):  # type: ignore[no-untyped-def]
    return getattr(request.app.state, "engine", None)


def _enforcement(request: Request) -> str:
    from app.config import get_settings

    return get_settings().AUTH_ENFORCEMENT


def optional_principal(request: Request) -> dict | None:
    """Validate a presented Bearer token; None when absent or invalid.

    Never raises: in permissive mode an invalid token simply
    means anonymous. Enforcement middleware handles denial.
    """
    engine = _engine(request)
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer ") or engine is None:
        return None
    factory = get_session_factory(engine)
    if factory is None:
        return None
    # Build the plain dict INSIDE the session: reading ORM
    # attributes after close raises DetachedInstanceError
    # (sessions expire attributes on commit by default).
    with factory() as session:
        user, reason = validate_token(session, auth[7:].strip())
        if user is None:
            return None
        return {
            "username": user.username,
            "role": user.role,
            "user_id": user.id,
            "token_reason": reason,
        }


def require_principal(request: Request) -> dict:
    """Require a valid token. 401 when absent, malformed, or invalid."""
    principal = optional_principal(request)
    if principal is None:
        raise HTTPException(status_code=401, detail="authentication required")
    return principal


def require_role(role: str):  # type: ignore[no-untyped-def]
    """Dependency factory: 401 without a token, 403 for a lesser role."""

    def _check(request: Request) -> dict:
        principal = require_principal(request)
        if principal["role"] != role and principal["role"] != "administrator":
            # Administrators pass every role gate (documented in rbac_model).
            raise HTTPException(status_code=403, detail="insufficient role")
        return principal

    return _check


def require_permission(permission: str):  # type: ignore[no-untyped-def]
    """Dependency factory: 401 without a token, 403 without the permission."""

    def _check(request: Request) -> dict:
        principal = require_principal(request)
        if not has_permission(principal["role"], permission):
            raise HTTPException(status_code=403, detail="insufficient permission")
        return principal

    return _check


def bearer_credentials(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> HTTPAuthorizationCredentials | None:
    """Bearer scheme helper for routes that want the raw credential."""
    return credentials
