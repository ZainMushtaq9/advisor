"""Security middleware: headers, rate limiting, enforcement (Phase 24).

Three independent pieces, mounted in ``app.main``:

1. Security headers — every response carries X-Content-Type-Options,
   X-Frame-Options, Referrer-Policy, Permissions-Policy and a
   restrictive Content-Security-Policy (the API serves JSON, so
   ``default-src 'none'; frame-ancestors 'none'`` is correct).
   Auth responses additionally carry ``Cache-Control: no-store``.
2. Rate limiting — in-memory fixed-window counters, keyed by
   client IP + route group. General API limit and a stricter
   limit for ``/api/v1/auth/*``; both from settings. Over-limit
   requests get 429 + ``Retry-After`` and no handler runs. The
   limiter is deliberately simple (single-process, in-memory):
   it bounds abuse on one instance, and is documented as NOT a
   substitute for edge rate limiting in a multi-instance deploy.
3. Enforcement — only when ``AUTH_ENFORCEMENT=on``: every
   ``/api/v1`` request except ``/api/v1/auth/status`` must carry
   a valid Bearer token or it gets 401. Token validation fails
   closed on any error (no engine, bad token, expired, revoked,
   disabled, locked). ``/health`` is exempt (liveness must not
   require credentials).

CSRF: not applicable today. The API is GET-only, uses no
cookies, and has no state-changing route — there is no ambient
credential for a cross-site request to ride on. The rule is
documented: any future POST/PUT/PATCH/DELETE route MUST use
Bearer-token auth (never cookies) and MUST carry a role or
permission dependency, or it fails review.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; sandbox",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach security headers to every response."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers[name] = value
        if request.url.path.startswith("/api/v1/auth/"):
            response.headers["Cache-Control"] = "no-store"
        return response


class RateLimiter:
    """Fixed-window in-memory limiter (single process).

    ``allow(key)`` returns (allowed, retry_after_seconds).
    Windows are per (key, window-start); counters reset when the
    window advances. Time is injectable for tests.
    """

    def __init__(self) -> None:
        self._counts: dict[tuple[str, int], int] = defaultdict(int)

    def allow(
        self, key: str, limit: int, window_seconds: int, now: float | None = None
    ) -> tuple[bool, int]:
        now = time.time() if now is None else now
        window = int(now // window_seconds)
        bucket = (key, window)
        self._counts[bucket] += 1
        if self._counts[bucket] > limit:
            retry_after = int(window_seconds - (now % window_seconds)) + 1
            return False, retry_after
        return True, 0

    def reset(self) -> None:
        self._counts.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-IP rate limits on API routes (not /health)."""

    def __init__(self, app, limiter: RateLimiter | None = None):  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.limiter = limiter or RateLimiter()

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        path = request.url.path
        if not path.startswith("/api/v1"):
            return await call_next(request)
        from app.config import get_settings

        settings = get_settings()
        ip = request.client.host if request.client else "unknown"
        if path.startswith("/api/v1/auth/"):
            limit = settings.AUTH_RATE_LIMIT_AUTH_PER_MINUTE
            group = "auth"
        else:
            limit = settings.AUTH_RATE_LIMIT_PER_MINUTE
            group = "api"
        allowed, retry_after = self.limiter.allow(f"{group}:{ip}", limit, 60)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "detail": "Too many requests; slow down and retry.",
                },
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)


class EnforcementMiddleware(BaseHTTPMiddleware):
    """Fail-closed authentication gate, active only when enforced."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        from app.config import get_settings
        from app.services.auth.dependencies import PUBLIC_PATHS, optional_principal

        settings = get_settings()
        if settings.AUTH_ENFORCEMENT != "on":
            return await call_next(request)
        path = request.url.path
        if path in PUBLIC_PATHS or not path.startswith("/api/v1"):
            return await call_next(request)
        if optional_principal(request) is None:
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "detail": "authentication required"},
            )
        return await call_next(request)
