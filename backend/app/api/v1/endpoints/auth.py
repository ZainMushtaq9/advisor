"""Phase 24 auth endpoints (GET-only, like every other endpoint).

- ``GET /api/v1/auth/status`` — public. Reports enforcement mode
  and the role list. No secret, no value, no user data.
- ``GET /api/v1/auth/me`` — returns the validated principal
  (username, role, permissions) for a presented Bearer token,
  or 401. In permissive mode an absent token is also 401 here:
  this endpoint exists to prove a token, not to browse
  anonymously. With no database configured it returns 503
  (authentication is unavailable, not bypassed).

There is deliberately NO login, registration, password-change,
or token-issue route over HTTP. Account management happens
through the local CLI (``scripts/manage_auth.py``) by an
operator with shell access — that is the "protected
administrative endpoint" decision: the admin surface does not
exist on the network at all.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.database import get_session_factory
from app.services.auth import ROLES, permissions_for
from app.services.auth.dependencies import optional_principal
from app.services.auth.service import validate_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status")
def auth_status() -> dict:
    """Public auth posture: mode + roles. No secrets, no user data."""
    settings = get_settings()
    return {
        "enforcement": settings.AUTH_ENFORCEMENT,
        "roles": list(ROLES),
        "admin_over_http": False,
        "login_over_http": False,
        "token_ttl_hours": settings.AUTH_TOKEN_TTL_HOURS,
        "service_token_ttl_days": settings.AUTH_SERVICE_TOKEN_TTL_DAYS,
    }


@router.get("/me")
def auth_me(request: Request) -> dict:
    """Validate the presented Bearer token and return its principal."""
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="authentication unavailable (no database)")
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="authentication required")
    factory = get_session_factory(engine)
    if factory is None:
        raise HTTPException(status_code=503, detail="authentication unavailable (no database)")
    # Build the response INSIDE the session: reading ORM
    # attributes after close raises DetachedInstanceError.
    with factory() as session:
        user, reason = validate_token(session, auth[7:].strip())
        if user is None:
            raise HTTPException(status_code=401, detail=f"invalid token ({reason})")
        return {
            "username": user.username,
            "role": user.role,
            "permissions": list(permissions_for(user.role)),
            "last_login_at": (user.last_login_at.isoformat() if user.last_login_at else None),
        }


@router.get("/principal")
def auth_principal(request: Request) -> dict:
    """Debug-shaped view of the request principal (same rules as /me).

    Kept separate from /me so tests can assert the optional-
    principal path (anonymous in permissive mode) without
    conflating it with the strict /me path.
    """
    principal = optional_principal(request)
    if principal is None:
        return {"authenticated": False, "principal": None}
    return {"authenticated": True, "principal": principal}
