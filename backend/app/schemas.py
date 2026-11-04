"""Response schemas for the Phase 2 foundation endpoints.

These describe system state only. There are no market-data, financial
or Phase 3 schemas in this module.
"""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    api_version: str


class DatabaseStatus(BaseModel):
    status: str
    reachable: bool
    dialect: str | None
    reason: str | None


class SystemStatusResponse(BaseModel):
    service: str
    api_version: str
    environment: str
    python_version: str
    platform: str
    packages: dict[str, str]
    database: DatabaseStatus


class VersionResponse(BaseModel):
    service: str
    app_version: str
    api_version: str
    python_version: str


class ConfigEntry(BaseModel):
    name: str
    status: str  # SET | MISSING
    source: str  # environment | default | unset


class ConfigStatusResponse(BaseModel):
    # Names and SET/MISSING flags only. Values are never included.
    settings: list[ConfigEntry]
