"""Phase 24 authentication, authorization and audit models.

Three tables: ``auth_users``, ``auth_tokens``, ``auth_audit_logs``.

DELIBERATE EXCEPTION to the Phase 3 statement in
``app.models.base`` ("no model stores a password, API key, token or
secret"): that statement covers business-data models. These three
tables are the project's single, documented exception, and they
store HASHES ONLY, never a plaintext secret:

- ``password_hash`` is PBKDF2-HMAC-SHA256 with a per-user salt
  (see ``app.services.auth.passwords``); the plaintext password
  is never persisted, logged, or returned.
- ``token_hash`` is the SHA-256 hex of an opaque bearer token;
  the token itself is shown to its owner exactly once, at issue
  time, and is never stored. ``prefix`` keeps only the first 8
  characters of the token (the ``psx_`` prefix plus 4 characters)
  so an operator can identify a token without knowing it.
- Audit ``detail`` JSON must never contain a password, token,
  token hash, or any other secret (enforced by the audit writer,
  which drops secret-looking keys).

No order, execution, or external-send concept exists in these
tables. Tokens authorize reads of the existing GET-only API and
CLI-administered account management; they never authorize a
trade, a publication, or a quality-status promotion.

ID deviation, deliberate: these tables do NOT use ``IdMixin``.
``IdMixin`` uses ``Identity(always=True)`` (PostgreSQL-only) and
a BigInteger PK is not a rowid alias on SQLite, so inserts fail
NOT NULL there. The auth tables use a plain Integer primary key
with autoincrement — SERIAL on PostgreSQL, INTEGER rowid alias
on SQLite — so the same code runs on both. Account counts will
never approach the 32-bit limit. The migration matches this
exactly.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin

# Phase 24 roles (see app.services.auth.roles for the permission matrix).
AUTH_ROLES = (
    "user",
    "analyst",
    "administrator",
    "read_only_agent",
    "service_process",
)

AUTH_TOKEN_TYPES = ("user", "service")

AUDIT_OUTCOMES = ("success", "failure", "denied")


class AuthUser(CreatedMixin, Base):
    """One local account. Managed by the local CLI only, never over HTTP."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "auth_users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_auth_users_username"),
        CheckConstraint(
            f"role IN ({', '.join(repr(r) for r in AUTH_ROLES)})",
            name="ck_auth_users_role",
        ),
    )

    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    password_salt: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failed_logins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class AuthToken(CreatedMixin, Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """One issued bearer token, stored as its SHA-256 hash only."""

    __tablename__ = "auth_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_auth_tokens_token_hash"),
        CheckConstraint(
            f"token_type IN ({', '.join(repr(t) for t in AUTH_TOKEN_TYPES)})",
            name="ck_auth_tokens_type",
        ),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("auth_users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False)
    prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class AuthAuditLog(CreatedMixin, Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """One audit event. Detail JSON never carries a secret."""

    __tablename__ = "auth_audit_logs"
    __table_args__ = (
        CheckConstraint(
            f"outcome IN ({', '.join(repr(o) for o in AUDIT_OUTCOMES)})",
            name="ck_auth_audit_logs_outcome",
        ),
    )

    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[str | None] = mapped_column(String(200))
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSON)
