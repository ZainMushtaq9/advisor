"""Alembic environment — PSX Intelligence AI, Phase 2 (Team D).

Connection string comes ONLY from the DATABASE_URL environment variable.
If DATABASE_URL is unset, this fails loudly instead of silently falling
back to a guessed database. The backend team owns backend/ model code;
until it wires its Base.metadata in here, target_metadata stays an empty
MetaData and migrations are explicit op.* operations (see versions/).
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import MetaData, engine_from_config, pool

# env.py lives at <repo>/database/migrations/env.py, so the repo root is
# three levels up (migrations -> database -> repo).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Phase 3: backend models now exist. Importing app.models registers all
# Phase 3 tables on app.database.Base; autogenerate uses that metadata.
from app.models import Base  # noqa: E402

target_metadata = Base.metadata

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Set it (or source database/.env, "
            "which is gitignored) before running alembic. Refusing to "
            "migrate against an unknown database."
        )
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = DATABASE_URL
    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
