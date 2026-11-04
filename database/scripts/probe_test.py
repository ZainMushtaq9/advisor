#!/usr/bin/env python3
"""Phase 2 probe test — insert/retrieve + connection-failure handling.

Usage:  DATABASE_URL=... python3 database/scripts/probe_test.py
Requires migration 20261104_0001 applied (phase2_probe exists).

Subtests:
  1. INSERT a clearly-labelled TEST record (NOT PSX data) and SELECT it
     back; fail loudly if the retrieved values differ.
  2. Connection failure: connect to a wrong port and to a nonexistent
     database; both MUST raise OperationalError. If either "succeeds",
     that is a failure of this test, not a pass.
  3. Cleanup: delete the probe row it inserted, so repeated runs are
     idempotent (the row label is fixed, so a stale row is also deleted
     first if a previous run was interrupted).
Exit 0 only if all subtests pass.
"""
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

LABEL = "phase2-probe-001"
NOTE = "TEST RECORD — NOT PSX DATA — Phase 2 infrastructure probe only"


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("PROBE: FAIL — DATABASE_URL is not set", file=sys.stderr)
        return 2
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM phase2_probe WHERE probe_label = :label"),
                {"label": LABEL},
            )
            row_id = conn.execute(
                text(
                    "INSERT INTO phase2_probe (probe_label, note) "
                    "VALUES (:label, :note) RETURNING id, created_at"
                ),
                {"label": LABEL, "note": NOTE},
            ).one()
            print(f"PROBE: inserted id={row_id[0]} created_at={row_id[1]}")
            got = conn.execute(
                text(
                    "SELECT probe_label, note FROM phase2_probe "
                    "WHERE id = :id"
                ),
                {"id": row_id[0]},
            ).one()
            assert got[0] == LABEL and got[1] == NOTE, f"mismatch: {got!r}"
            print(f"PROBE: retrieved label={got[0]!r} note={got[1]!r} — MATCH")
            conn.execute(
                text("DELETE FROM phase2_probe WHERE id = :id"),
                {"id": row_id[0]},
            )
            remaining = conn.execute(
                text("SELECT count(*) FROM phase2_probe WHERE probe_label = :label"),
                {"label": LABEL},
            ).scalar()
            assert remaining == 0
            print("PROBE: cleanup ok, probe row removed (count=0)")
    except (SQLAlchemyError, AssertionError) as exc:
        print(f"PROBE: FAIL — {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    # Subtest 2: connection failures must fail clearly, not fake-ok.
    bad_urls = [
        url.replace(":5432/", ":59999/"),  # wrong port
        url.rsplit("/", 1)[0] + "/psx_no_such_database",  # wrong database
    ]
    for i, bad in enumerate(bad_urls, start=1):
        try:
            bad_engine = create_engine(bad, pool_pre_ping=True)
            with bad_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"PROBE: FAIL — bad connection {i} unexpectedly succeeded",
                  file=sys.stderr)
            return 2
        except OperationalError as exc:
            # Print only the first line: full tracebacks may echo the URL.
            first = str(exc).splitlines()[0] if str(exc) else "OperationalError"
            print(f"PROBE: bad connection {i} correctly raised "
                  f"OperationalError: {first[:160]}")
    print("PROBE: ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
