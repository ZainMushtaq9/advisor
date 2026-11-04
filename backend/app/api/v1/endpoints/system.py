"""Foundation endpoints reporting ACTUAL system state.

- GET /api/v1/health          — liveness only; does not claim DB health.
- GET /api/v1/system/status   — real Python/platform/package versions
  plus a live database probe (``unavailable`` when PostgreSQL is not
  yet running — never a hardcoded ``ok``).
- GET /api/v1/system/version  — app + API versions.
- GET /api/v1/config/status   — setting names with SET/MISSING flags
  only. Values — and therefore secrets — are never returned.

No endpoint here returns market data, forecasts or recommendations.
"""

from __future__ import annotations

import platform
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from fastapi import APIRouter, Request

from app import __api_version__, __version__
from app.config import get_settings
from app.database import check_database
from app.schemas import (
    ConfigEntry,
    ConfigStatusResponse,
    DatabaseStatus,
    HealthResponse,
    SystemStatusResponse,
    VersionResponse,
)

router = APIRouter(tags=["system"])

# Packages whose installed versions are reported truthfully. If a package
# is somehow absent, its version is reported as "not-installed", never guessed.
_REPORTED_PACKAGES = ("fastapi", "uvicorn", "pydantic", "sqlalchemy", "alembic")


def _package_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for name in _REPORTED_PACKAGES:
        try:
            out[name] = package_version(name)
        except PackageNotFoundError:
            out[name] = "not-installed"
    return out


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.APP_NAME, api_version=__api_version__)


@router.get("/system/status", response_model=SystemStatusResponse)
def system_status(request: Request) -> SystemStatusResponse:
    settings = get_settings()
    db_state = check_database(request.app.state.engine, settings.DATABASE_URL)
    return SystemStatusResponse(
        service=settings.APP_NAME,
        api_version=__api_version__,
        environment=settings.ENVIRONMENT,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        packages=_package_versions(),
        database=DatabaseStatus(**db_state),
    )


@router.get("/system/version", response_model=VersionResponse)
def system_version() -> VersionResponse:
    settings = get_settings()
    return VersionResponse(
        service=settings.APP_NAME,
        app_version=__version__,
        api_version=__api_version__,
        python_version=sys.version.split()[0],
    )


@router.get("/config/status", response_model=ConfigStatusResponse)
def config_status() -> ConfigStatusResponse:
    settings = get_settings()
    return ConfigStatusResponse(
        settings=[ConfigEntry(**entry) for entry in settings.config_status()]
    )
