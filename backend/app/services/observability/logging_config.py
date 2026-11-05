"""Phase 27 structured logging: correlation IDs, JSON-ish records,
and secret redaction.

Rules (brief: "Avoid logging secrets or unnecessary personal
data"):

- Every record carries a correlation id. The id is taken from an
  incoming ``X-Correlation-ID`` header when present, otherwise
  generated per request. Job and agent run ids are logged as
  separate fields, never folded into the message text.
- Values under a redacted key are replaced with "[REDACTED]",
  never emitted. Keys are matched case-insensitively and by
  substring: ``password``, ``token``, ``secret``, ``api_key``,
  ``apikey``, ``authorization``, ``cookie``, ``dsn``,
  ``database_url``, ``private``. A database URL is redacted in
  full (it carries credentials), never partially masked — a
  partial mask still leaks the host and username shape.
- No message text is ever built from untrusted input: log calls
  take structured fields, and the formatter renders fields, so
  an injected newline or format string in a value cannot forge
  a second record. Values are rendered on one line.
- This module never logs a row's full content, an email
  address, or a personal identifier. Tickers, counts, dates,
  and run ids are operational data, not personal data.

The middleware lives here too (Starlette pure ASGI, no new
dependency): it sets the correlation id for the request scope
and echoes it back as an ``X-Correlation-ID`` response header,
so a client can quote one id when reporting a failure and the
operator can find every record for that request.
"""

from __future__ import annotations

import contextvars
import json
import logging
import re
import uuid

_CORRELATION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "psx_correlation_id", default=None
)

REDACTED = "[REDACTED]"

# Substring match, case-insensitive. Deliberately broad: a missed
# secret in a log is worse than an over-redacted debug field.
_REDACT_KEY_PARTS = (
    "password",
    "passwd",
    "pwd",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "cookie",
    "session",
    "dsn",
    "database_url",
    "private_key",
    "bearer",
)


def _key_is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in _REDACT_KEY_PARTS)


def redact_value(value: object) -> object:
    """Recursively replace sensitive values with [REDACTED].

    Dict keys are matched by substring (see _REDACT_KEY_PARTS).
    Strings that look like a database URL (scheme://...@...) are
    redacted in full. Anything else passes through unchanged.
    """
    if isinstance(value, dict):
        return {
            key: REDACTED if _key_is_sensitive(str(key)) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_value(item) for item in value]
    if isinstance(value, str) and re.match(r"^[a-z][a-z0-9+.-]*://[^/]*@", value):
        return REDACTED
    return value


def set_correlation_id(correlation_id: str | None) -> None:
    _CORRELATION_ID.set(correlation_id)


def get_correlation_id() -> str | None:
    return _CORRELATION_ID.get()


def new_correlation_id() -> str:
    return uuid.uuid4().hex[:16]


class StructuredFormatter(logging.Formatter):
    """One JSON object per record, secrets redacted, single line."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        fields = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        extra = getattr(record, "fields", None)
        if isinstance(extra, dict):
            fields.update(redact_value(extra))  # type: ignore[arg-type]
        if record.exc_info:
            fields["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        line = json.dumps(fields, default=str)
        return line.replace("\n", " ")


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the structured formatter attached once."""
    logger = logging.getLogger(name)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log_event(logger: logging.Logger, level: int, message: str, **fields: object) -> None:
    """Log one structured event. Fields are redacted by the formatter."""
    logger.log(level, message, extra={"fields": fields})


class CorrelationIdMiddleware:
    """Starlette middleware: set/echo X-Correlation-ID per request."""

    def __init__(self, app):  # type: ignore[no-untyped-def]
        self.app = app

    async def __call__(self, scope, receive, send):  # type: ignore[no-untyped-def]
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        correlation_id = headers.get("x-correlation-id") or new_correlation_id()
        set_correlation_id(correlation_id)

        async def send_with_id(message):  # type: ignore[no-untyped-def]
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"x-correlation-id", correlation_id.encode())
                ]
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            set_correlation_id(None)
