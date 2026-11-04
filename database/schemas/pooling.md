# Connection pooling — documented settings for the backend team

Team D owns the server, role, database, and Alembic infrastructure.
The backend team owns backend/ code, including the engine it builds.
This note is the pooling CONTRACT so both sides configure the same
values; it is not backend code and does not modify backend/ files.

## Recommended SQLAlchemy engine settings (FastAPI service)

```python
from sqlalchemy import create_engine
import os

engine = create_engine(
    os.environ["DATABASE_URL"],  # never hard-code; never commit a password
    pool_size=5,          # persistent connections in the pool
    max_overflow=10,      # extra connections under burst load (pool total <= 15)
    pool_timeout=30,      # seconds to wait for a connection before erroring
    pool_recycle=1800,    # recycle connections after 30 min (stale-connection guard)
    pool_pre_ping=True,   # test a connection before use; dropped connections
                          # are replaced instead of failing the first query
)
```

## Why these values (single self-hosted instance, 7.7 GiB RAM)

- PostgreSQL default `max_connections = 100` (cluster default, verified
  at initdb). One API process at pool total 15 leaves headroom for
  psql/admin sessions, a Celery worker pool, and Alembic runs without
  approaching the limit. If a second process is added, its pool must
  be sized so the SUM of all pools stays comfortably below 100.
- `pool_pre_ping=True` is the cheap guard against "server closed the
  connection unexpectedly" after idle periods; it costs one round-trip
  per checkout, which is acceptable for this workload.
- `pool_recycle=1800` avoids connections that outlive NAT/firewall
  idle timeouts on a self-hosted box.
- Do NOT use `NullPool` in the application (it opens a connection per
  request). `NullPool` is used only in `migrations/env.py`, where a
  migration run is short-lived and single-connection by design.
- Do NOT raise `pool_size` to "fix" slow queries: slow queries are
  fixed by indexes/query shape (Phase 1 indexing strategy), not by
  more connections. Pool exhaustion must surface as an error in logs,
  not be papered over.

## Failure behaviour (verified by scripts/probe_test.py)

A wrong port, wrong database, or wrong password must raise a clear
`sqlalchemy.exc.OperationalError` (wrapping a psycopg connection
error) and the application must report it, not return a fake "ok".
The health check (`scripts/health_check.py`) exits non-zero on any
connection failure, so a supervisor/CI gate can detect it.
