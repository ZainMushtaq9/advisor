"""Database connection interface (SQLAlchemy engine / session factory).

Phase 2 foundation only: no Phase 3 schema, no models, no tables are
defined here. The database team owns the actual PostgreSQL installation;
this module must work from a ``DATABASE_URL`` env var and report the
real connection state without faking one.

Behaviour:
- ``DATABASE_URL`` unset  -> engine is ``None``; ``check_database()``
  reports ``unavailable`` with reason ``database_url_not_set``.
- ``DATABASE_URL`` set but unreachable -> ``check_database()`` reports
  ``unavailable`` with the exception class name only. The URL (which may
  contain credentials) is never returned, logged or echoed.
- ``DATABASE_URL`` set and reachable -> ``available``. A ``SELECT 1``
  probe is used; no tables are created or assumed.
"""

from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

logger = logging.getLogger("psx_intelligence_ai.database")

# Declarative base for future (Phase 3+) models. Intentionally no models
# are registered on it in Phase 2.
Base = declarative_base()


def build_engine(database_url: str | None) -> Engine | None:
    """Create an engine from a URL, or ``None`` when no URL is configured."""
    if not database_url:
        return None
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        # SQLite (dev-only per Phase 1) needs this for the default pool.
        connect_args = {"check_same_thread": False}
    engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
    return engine


def get_session_factory(engine: Engine | None) -> sessionmaker[Session] | None:
    """Session factory bound to ``engine``, or ``None`` without an engine."""
    if engine is None:
        return None
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def dialect_of(database_url: str | None) -> str | None:
    """Driver/dialect name only (e.g. ``postgresql+psycopg``) — never the URL."""
    if not database_url:
        return None
    try:
        return make_url(database_url).drivername
    except Exception:
        return "unknown"


def check_database(engine: Engine | None, database_url: str | None) -> dict[str, object]:
    """Probe the database and report its ACTUAL state truthfully."""
    if engine is None or not database_url:
        return {
            "status": "unavailable",
            "reachable": False,
            "dialect": None,
            "reason": "database_url_not_set",
        }
    dialect = dialect_of(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "available", "reachable": True, "dialect": dialect, "reason": None}
    except SQLAlchemyError as exc:
        # Exception class name only — no message text that could carry a DSN.
        logger.warning("database probe failed", extra={"dialect": dialect})
        return {
            "status": "unavailable",
            "reachable": False,
            "dialect": dialect,
            "reason": f"connection_failed:{type(exc).__name__}",
        }
    except Exception as exc:  # defensive: never leak internals to callers
        logger.warning("database probe failed unexpectedly")
        return {
            "status": "unavailable",
            "reachable": False,
            "dialect": dialect,
            "reason": f"connection_failed:{type(exc).__name__}",
        }


def get_db(engine: Engine | None) -> Generator[Session, None, None]:
    """Yield a session, or raise a clear error when no database is configured."""
    factory = get_session_factory(engine)
    if factory is None:
        raise RuntimeError("DATABASE_URL is not set; no database is configured")
    session = factory()
    try:
        yield session
    finally:
        session.close()
