"""FastAPI application factory.

Run (from ``backend/`` with the venv active)::

    uvicorn app.main:app --host 127.0.0.1 --port 8000

OpenAPI docs are served by FastAPI itself at ``/docs`` (Swagger UI) and
``/openapi.json``. Error responses are generic JSON: no stack traces and
no secrets are ever returned to clients.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1.router import api_router
from app.config import get_settings
from app.database import build_engine
from app.logging_config import configure_logging

logger = logging.getLogger("psx_intelligence_ai")


def create_app() -> FastAPI:
    """Build a fresh app instance (fresh settings + engine per instance)."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    app = FastAPI(
        title="PSX Intelligence AI",
        description=(
            "Phase 2 backend foundation: health, system status, version and "
            "configuration-status endpoints. No market data, forecasting or "
            "AI-agent functionality is provided at this stage."
        ),
        version=__version__,
    )
    # Database engine is built once per app instance from DATABASE_URL.
    # None when unset: endpoints then truthfully report "unavailable".
    app.state.engine = build_engine(settings.DATABASE_URL)

    # CORS: restricted origins from the environment only. Wildcard is
    # rejected in production by Settings validation (see config.py).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.CORS_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = str(uuid.uuid4())
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):  # type: ignore[no-untyped-def]
        # Field names and messages only — no request body, no traceback.
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": [
                    {"field": ".".join(str(p) for p in err["loc"]), "message": err["msg"]}
                    for err in exc.errors()
                ],
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):  # type: ignore[no-untyped-def]
        # Log the exception server-side; clients get a generic message only.
        logger.exception("unhandled error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "detail": "An unexpected error occurred."},
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):  # type: ignore[no-untyped-def]
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "detail": f"No route matches {request.url.path}."},
        )

    app.include_router(api_router)

    @app.get("/health", include_in_schema=False)
    def top_level_health() -> dict[str, str]:
        """Unversioned liveness alias for the Phase 1 ``/health`` monitor."""
        return {"status": "ok", "service": settings.APP_NAME}

    return app


app = create_app()
