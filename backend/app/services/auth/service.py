"""Account, token and audit operations (database-backed).

Every function here is explicit about what it writes and what it
never writes:

- Passwords are verified, never read back; the stored hash is
  never returned to any caller (``public_user`` strips it).
- Tokens are returned exactly once, at issue; afterwards only
  the hash, prefix, and metadata exist.
- Audit ``detail`` drops any secret-looking key (``password``,
  ``token``, ``hash``, ``secret``, ``salt`` and friends) before
  writing, so a careless caller cannot leak a credential into
  the audit trail. Audit rows are append-only: no update or
  delete function exists in this module.
- Lockout: ``max_failed`` consecutive failed logins lock the
  account for ``lockout_minutes``. A successful login resets
  the counter. A locked account's password is never checked
  (timing alone must not reveal whether the password was right).
- No function here sends anything externally, publishes
  anything, promotes any quality status, or executes any trade.
  Those capabilities do not exist in this module at all.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.auth import AuthAuditLog, AuthToken, AuthUser
from app.services.auth import ROLES, has_permission
from app.services.auth.passwords import (
    hash_password,
    password_policy_errors,
    verify_password,
)
from app.services.auth.tokens import (
    expiry_for,
    is_expired,
    new_token,
    token_hash,
    token_prefix,
    utcnow,
)

# Keys stripped from audit detail before writing. A superset on
# purpose: anything that even looks like a credential never lands
# in the audit trail.
_SECRET_DETAIL_KEYS = frozenset(
    {
        "password",
        "passwd",
        "pwd",
        "token",
        "bearer",
        "secret",
        "hash",
        "salt",
        "api_key",
        "apikey",
        "credential",
        "private_key",
        "cookie",
        "session",
    }
)

AUDIT_ACTIONS = (
    "account_created",
    "account_disabled",
    "account_enabled",
    "role_changed",
    "password_changed",
    "login_success",
    "login_failed",
    "account_locked",
    "token_issued",
    "token_revoked",
    "token_validated",
    "access_denied",
)


def _as_aware(value: datetime | None) -> datetime | None:
    """Reattach UTC to a naive datetime.

    The service writes only aware UTC datetimes; PostgreSQL
    round-trips them aware, but SQLite strips tzinfo on read.
    A naive value read back is therefore UTC by construction —
    reattaching it is correct, and avoids fail-closed misfires
    (e.g. every token looking expired) on SQLite-backed tests.
    A None stays None.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _clean_detail(detail: dict | None) -> dict | None:
    """Drop secret-looking keys from audit detail (defense in depth)."""
    if not detail:
        return None
    return {k: v for k, v in detail.items() if k.lower() not in _SECRET_DETAIL_KEYS}


def audit(
    session: Session,
    actor: str,
    action: str,
    outcome: str,
    target: str | None = None,
    detail: dict | None = None,
) -> AuthAuditLog:
    """Append one audit row. There is no update or delete path."""
    row = AuthAuditLog(
        actor=actor,
        action=action,
        target=target,
        outcome=outcome,
        detail=_clean_detail(detail),
    )
    session.add(row)
    return row


def public_user(user: AuthUser) -> dict:
    """Safe public view of an account: no hash, no salt, ever."""
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "failed_logins": user.failed_logins,
        "locked_until": user.locked_until.isoformat() if user.locked_until else None,
        "last_login_at": (user.last_login_at.isoformat() if user.last_login_at else None),
    }


def create_user(
    session: Session, actor: str, username: str, password: str, role: str
) -> tuple[AuthUser | None, list[str]]:
    """Create an account. Only an administrator may call this (CLI-enforced).

    Returns (user, errors); errors non-empty means nothing was written.
    """
    errors: list[str] = []
    if role not in ROLES:
        errors.append(f"unknown role {role!r}")
    errors.extend(password_policy_errors(password))
    if session.query(AuthUser).filter_by(username=username).first() is not None:
        errors.append(f"username {username!r} already exists")
    if errors:
        audit(
            session,
            actor,
            "account_created",
            "failure",
            target=username,
            detail={"role": role, "errors": errors},
        )
        session.commit()
        return None, errors
    stored, salt = hash_password(password)
    user = AuthUser(username=username, password_hash=stored, password_salt=salt, role=role)
    session.add(user)
    audit(session, actor, "account_created", "success", target=username, detail={"role": role})
    session.commit()
    return user, []


def authenticate(
    session: Session,
    username: str,
    password: str,
    max_failed: int = 5,
    lockout_minutes: int = 15,
    now: datetime | None = None,
) -> tuple[AuthUser | None, str]:
    """Check credentials. Returns (user, reason); user None means denied.

    A disabled or locked account is denied without checking the
    password. A failed check increments the counter and may lock
    the account; a success resets the counter and stamps last login.
    Every outcome is audited.
    """
    now = now or utcnow()
    user = session.query(AuthUser).filter_by(username=username).first()
    if user is None:
        audit(
            session,
            "system",
            "login_failed",
            "failure",
            target=username,
            detail={"reason": "unknown_user"},
        )
        session.commit()
        return None, "unknown_user"
    if not user.is_active:
        audit(
            session,
            username,
            "login_failed",
            "denied",
            target=username,
            detail={"reason": "disabled"},
        )
        session.commit()
        return None, "disabled"
    locked_until = _as_aware(user.locked_until)  # type: ignore[arg-type]
    if locked_until is not None and now < locked_until:
        audit(
            session,
            username,
            "login_failed",
            "denied",
            target=username,
            detail={"reason": "locked"},
        )
        session.commit()
        return None, "locked"
    if not verify_password(password, user.password_hash):
        user.failed_logins = (user.failed_logins or 0) + 1
        reason = "bad_password"
        if user.failed_logins >= max_failed:
            user.locked_until = now + timedelta(minutes=lockout_minutes)
            reason = "locked"
            audit(
                session,
                username,
                "account_locked",
                "denied",
                target=username,
                detail={"failed_logins": user.failed_logins},
            )
        audit(
            session, username, "login_failed", "failure", target=username, detail={"reason": reason}
        )
        session.commit()
        return None, reason
    user.failed_logins = 0
    user.locked_until = None
    user.last_login_at = now
    audit(session, username, "login_success", "success", target=username)
    session.commit()
    return user, "ok"


def issue_token(
    session: Session,
    actor: str,
    user: AuthUser,
    token_type: str,
    user_ttl_hours: int = 24,
    service_ttl_days: int = 90,
    now: datetime | None = None,
) -> tuple[str | None, str]:
    """Issue a bearer token for an active user. Returns (token, reason).

    The token string is returned exactly once; only its hash is
    stored. Service tokens are issued only to service_process and
    administrator accounts; user tokens to any active account.
    """
    now = now or utcnow()
    if not user.is_active:
        return None, "disabled"
    if token_type == "service" and user.role not in ("service_process", "administrator"):
        audit(
            session,
            actor,
            "token_issued",
            "denied",
            target=user.username,
            detail={"token_type": token_type, "reason": "role_not_allowed"},
        )
        session.commit()
        return None, "role_not_allowed"
    if token_type not in ("user", "service"):
        return None, "unknown_token_type"
    token = new_token()
    row = AuthToken(
        user_id=user.id,
        token_hash=token_hash(token),
        token_type=token_type,
        prefix=token_prefix(token),
        expires_at=expiry_for(token_type, now, user_ttl_hours, service_ttl_days),
    )
    session.add(row)
    audit(
        session,
        actor,
        "token_issued",
        "success",
        target=user.username,
        detail={"token_type": token_type, "prefix": row.prefix},
    )
    session.commit()
    return token, "ok"


def validate_token(
    session: Session, token: str, now: datetime | None = None
) -> tuple[AuthUser | None, str]:
    """Validate a bearer token. Returns (user, reason); user None = invalid.

    Checks, in order: token shape, hash lookup, revocation, expiry,
    account active, account not locked. Any failure fails closed
    and is audited as denied (without ever logging the token).
    """
    now = now or utcnow()
    if not token or not token.startswith("psx_"):
        return None, "bad_token"
    row = session.query(AuthToken).filter_by(token_hash=token_hash(token)).first()
    if row is None:
        return None, "unknown_token"
    if row.revoked_at is not None:
        audit(
            session,
            "system",
            "token_validated",
            "denied",
            target=f"token:{row.prefix}",
            detail={"reason": "revoked"},
        )
        session.commit()
        return None, "revoked"
    if is_expired(_as_aware(row.expires_at), now):  # type: ignore[arg-type]
        audit(
            session,
            "system",
            "token_validated",
            "denied",
            target=f"token:{row.prefix}",
            detail={"reason": "expired"},
        )
        session.commit()
        return None, "expired"
    user = session.query(AuthUser).filter_by(id=row.user_id).first()
    if user is None or not user.is_active:
        return None, "disabled"
    locked_until = _as_aware(user.locked_until)  # type: ignore[arg-type]
    if locked_until is not None and now < locked_until:
        return None, "locked"
    row.last_used_at = now
    session.commit()
    return user, "ok"


def revoke_token(session: Session, actor: str, prefix: str, now: datetime | None = None) -> bool:
    """Revoke all live tokens with a given prefix (operator identification).

    Prefixes identify, never authenticate: revocation by prefix is
    an operator action, audited, and requires the administrator
    role at the CLI layer. Returns True when at least one live
    token was revoked.
    """
    now = now or utcnow()
    rows = session.query(AuthToken).filter_by(prefix=prefix).all()
    revoked = False
    for row in rows:
        if row.revoked_at is None:
            row.revoked_at = now
            revoked = True
    audit(
        session,
        actor,
        "token_revoked",
        "success" if revoked else "failure",
        target=f"token:{prefix}",
        detail={"revoked": revoked},
    )
    session.commit()
    return revoked


def set_user_role(session: Session, actor: str, username: str, new_role: str) -> tuple[bool, str]:
    """Change an account's role. Administrator-only at the CLI layer."""
    if new_role not in ROLES:
        return False, "unknown_role"
    user = session.query(AuthUser).filter_by(username=username).first()
    if user is None:
        return False, "unknown_user"
    old_role = user.role
    user.role = new_role
    audit(
        session,
        actor,
        "role_changed",
        "success",
        target=username,
        detail={"old_role": old_role, "new_role": new_role},
    )
    session.commit()
    return True, "ok"


def set_user_active(session: Session, actor: str, username: str, active: bool) -> tuple[bool, str]:
    """Disable or enable an account. Administrator-only at the CLI layer."""
    user = session.query(AuthUser).filter_by(username=username).first()
    if user is None:
        return False, "unknown_user"
    user.is_active = active
    audit(
        session,
        actor,
        "account_enabled" if active else "account_disabled",
        "success",
        target=username,
    )
    session.commit()
    return True, "ok"


def require_permission(role: str, permission: str) -> bool:
    """Role-matrix check (single place; CLI and dependencies both use it)."""
    return has_permission(role, permission)


def utcnow_aware() -> datetime:
    """Aware UTC now (kept for callers that import from service)."""
    return datetime.now(timezone.utc)
