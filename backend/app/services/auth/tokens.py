"""Opaque bearer tokens (stdlib only).

A token is ``psx_`` + 32 bytes of ``secrets.token_urlsafe``.
Only its SHA-256 hex is ever stored (see ``app.models.auth``);
the token itself is shown to its owner exactly once, at issue
time, and is never logged, never returned again, and never
stored. The ``prefix`` (first 8 characters) lets an operator
identify a token in listings and audit rows without knowing it.

Expiry is checked against an aware UTC ``now``; an expired or
revoked token is invalid, and a malformed token string fails
closed. No JWT is used on purpose: opaque tokens need no
signing-key management, are revocable by deleting one row, and
carry no claims that could be misread as authorization.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

TOKEN_PREFIX = "psx_"
TOKEN_BYTES = 32
PUBLIC_PREFIX_CHARS = 8


def new_token() -> str:
    """Draw a fresh bearer token (shown once, never stored)."""
    return TOKEN_PREFIX + secrets.token_urlsafe(TOKEN_BYTES)


def token_hash(token: str) -> str:
    """SHA-256 hex of a token — the only form ever stored."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_prefix(token: str) -> str:
    """First 8 characters: enough to identify, never enough to use."""
    return token[:PUBLIC_PREFIX_CHARS]


def expiry_for(token_type: str, now: datetime, user_ttl_hours: int,
               service_ttl_days: int) -> datetime:
    """Expiry for a token type. Unknown types fail closed (past expiry)."""
    if token_type == "user":
        return now + timedelta(hours=user_ttl_hours)
    if token_type == "service":
        return now + timedelta(days=service_ttl_days)
    return now - timedelta(seconds=1)


def is_expired(expires_at: datetime, now: datetime) -> bool:
    """True when ``now`` is at or past expiry. Naive datetimes fail closed."""
    if expires_at.tzinfo is None or now.tzinfo is None:
        return True
    return now >= expires_at


def utcnow() -> datetime:
    """Aware UTC now (single source, so tests can pin time)."""
    return datetime.now(timezone.utc)
