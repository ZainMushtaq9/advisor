"""Password storage and policy (stdlib only, no new dependency).

Storage: PBKDF2-HMAC-SHA256, 600,000 iterations (OWASP guidance
for PBKDF2-HMAC-SHA256), 32-byte per-user salt from
``secrets``. The stored form is ``pbkdf2_sha256$<iterations>$<salt>$<hash>``
with salt and hash hex-encoded. Verification uses
``hmac.compare_digest`` (constant time). A plaintext password is
never logged, never returned, and never stored anywhere else.

Policy (enforced at account creation and password change):
minimum 12 characters, at least 3 of 4 character classes
(lower, upper, digit, symbol), and not on a small blocklist of
common passwords. The blocklist is a floor, not a guarantee:
a long, unique passphrase beats a short complex password.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

ITERATIONS = 600_000
SALT_BYTES = 32
MIN_LENGTH = 12

# Common passwords refused outright. Deliberately short: this list
# catches the worst choices; length + class rules do the rest.
BLOCKLISTED = frozenset(
    {
        "password",
        "password123",
        "password1234",
        "123456789012",
        "1234567890ab",
        "qwerty123456",
        "letmein12345",
        "admin1234567",
        "psx123456789",
        "changeme1234",
    }
)


def password_policy_errors(password: str) -> list[str]:
    """Return every policy violation; empty means the password is allowed."""
    errors: list[str] = []
    if len(password) < MIN_LENGTH:
        errors.append(f"password must be at least {MIN_LENGTH} characters")
    classes = sum(
        (
            any(c.islower() for c in password),
            any(c.isupper() for c in password),
            any(c.isdigit() for c in password),
            any(not c.isalnum() for c in password),
        )
    )
    if classes < 3:
        errors.append("password must use at least 3 of: lowercase, uppercase, digit, symbol")
    if password.lower() in BLOCKLISTED:
        errors.append("password is on the blocklist of common passwords")
    return errors


def hash_password(password: str) -> tuple[str, str]:
    """Return (stored_hash, salt_hex). A fresh salt is drawn every call."""
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    stored = f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"
    return stored, salt.hex()


def verify_password(password: str, stored: str) -> bool:
    """Constant-time verification. Any malformed stored value fails closed."""
    try:
        algo, iterations, salt_hex, digest_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False
