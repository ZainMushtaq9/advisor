#!/usr/bin/env python3
"""Database health check — PSX Intelligence AI, Phase 2 (Team D).

Usage:  DATABASE_URL=... python3 database/scripts/health_check.py
        (or: set -a; source database/.env; set +a; then run it)

Exit 0 only when a real query succeeds. Any connection failure exits 2
with the error printed — never a fake "ok".
Checks: SELECT 1, server version, phase2_probe table presence (warning,
not failure, if the probe migration has not run yet — the DB itself is
still healthy in that case; the migration state is reported separately).
"""
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("HEALTH: FAIL — DATABASE_URL is not set", file=sys.stderr)
        return 2
    # Mask credentials in any echoed output.
    safe = url.split("@")[-1] if "@" in url else url
    print(f"HEALTH: connecting to {safe} ...")
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=1800)
    try:
        with engine.connect() as conn:
            one = conn.execute(text("SELECT 1")).scalar()
            version = conn.execute(text("SHOW server_version")).scalar()
            tables = [
                r[0]
                for r in conn.execute(
                    text(
                        "SELECT tablename FROM pg_tables "
                        "WHERE schemaname='public' ORDER BY 1"
                    )
                )
            ]
        assert one == 1
        print(f"HEALTH: OK — SELECT 1 returned 1, server_version={version}")
        print(f"HEALTH: public tables: {tables}")
        if "phase2_probe" not in tables:
            print("HEALTH: NOTE — phase2_probe absent (migration not applied yet)")
        if "alembic_version" in tables:
            print("HEALTH: alembic_version present (migrations tracked)")
        return 0
    except SQLAlchemyError as exc:
        print(f"HEALTH: FAIL — {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
