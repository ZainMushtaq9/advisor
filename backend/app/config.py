"""Configuration management (Pydantic v2 settings).

Rules enforced here:
- Values come from environment variables (and an optional ``.env`` file
  loaded by pydantic-settings); nothing secret is hardcoded in code.
- ``DATABASE_URL`` is optional. When it is unset, the database layer
  reports "unavailable" instead of pretending a connection exists.
  The database team owns the actual PostgreSQL installation.
- CORS origins are restricted and come from the environment. A wildcard
  origin is rejected in production.
- Only setting *names* are ever reported by the config-status endpoint;
  this module never logs or returns a setting value.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Names of settings the /config/status endpoint may report on, by name only.
# Keep this list in sync with the fields on Settings.
REPORTABLE_SETTINGS = (
    "APP_NAME",
    "ENVIRONMENT",
    "DEBUG",
    "HOST",
    "PORT",
    "LOG_LEVEL",
    "DATABASE_URL",
    "CORS_ORIGINS",
)

# Defaults that apply when the corresponding env var is absent. These are
# non-secret operational defaults only; DATABASE_URL has no default.
DEFAULT_CORS_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")


class Settings(BaseSettings):
    """Application settings, read from the environment / ``.env``."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "psx-intelligence-ai"
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    # Optional on purpose: unset means "no database configured yet".
    # Never put a real credential in a default value.
    DATABASE_URL: str | None = None
    CORS_ORIGINS: tuple[str, ...] = DEFAULT_CORS_ORIGINS

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(o.strip() for o in value.split(",") if o.strip())
        return value

    @field_validator("DATABASE_URL")
    @classmethod
    def _reject_blank_database_url(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _reject_wildcard_cors_in_production(self) -> "Settings":
        if self.ENVIRONMENT == "production" and "*" in self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must not contain '*' in production")
        if self.ENVIRONMENT == "production" and self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        return self

    def config_status(self) -> list[dict[str, str]]:
        """SET/MISSING status by setting name only — never values.

        ``source`` is one of ``environment`` (env var present),
        ``default`` (built-in default in use) or ``unset`` (no value).
        """
        out: list[dict[str, str]] = []
        for name in REPORTABLE_SETTINGS:
            value = getattr(self, name)
            # Effective value decides SET vs MISSING: a blank env var
            # (e.g. DATABASE_URL=) counts as unset, not as SET.
            if value not in (None, "", ()):
                source = "environment" if name in os.environ else "default"
                status = "SET"
            else:
                status, source = "MISSING", "unset"
            out.append({"name": name, "status": status, "source": source})
        return out


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance; tests clear this cache after monkeypatching env."""
    return Settings()
