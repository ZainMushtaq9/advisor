"""Phase 4 live-PostgreSQL check (NOT a pytest test).

Runs the registry importer inside a transaction that is ALWAYS rolled
back, so the live database keeps 0 business rows. Then smoke-tests
the registry API against the (empty) live database via TestClient.

Usage (from repo root, with database/.env present):
    DATABASE_URL=<from database/.env> backend/.venv/bin/python \\
        scripts/run_phase4_pg_check.py

The script prints counts and exits non-zero on any failed assertion.
It never prints the DATABASE_URL.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import get_session_factory  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.reference import Company, Sector, Security  # noqa: E402
from app.services.registry.importer import SourceRecord, import_records  # noqa: E402
from app.services.registry.reconciliation import reconcile  # noqa: E402


def main() -> int:
    assert os.environ.get("DATABASE_URL"), "DATABASE_URL must be set"
    app = create_app()
    factory = get_session_factory(app.state.engine)
    assert factory is not None
    session = factory()
    try:
        session.begin()
        before = (
            session.query(Company).count(),
            session.query(Security).count(),
            session.query(Sector).count(),
        )
        records = [
            SourceRecord(
                ticker="TESTA", legal_name="Test Alpha Limited",
                sector_name="Test Sector", isin="PK0011111111",
            ),
            SourceRecord(
                ticker="TESTB", legal_name="Test Beta Limited",
                sector_name="Test Sector",
            ),
        ]
        result = import_records(
            session, records, source_key="pg_check",
            source_display_name="Phase 4 PG check (TEST ONLY)",
        )
        assert result.companies_created == 2, result
        assert result.securities_created == 2, result
        again = import_records(
            session, records, source_key="pg_check",
            source_display_name="Phase 4 PG check (TEST ONLY)",
        )
        assert again.skipped_as_duplicate == 2, again
        # Adversarial paths on live PostgreSQL (audit recommendation 4),
        # all inside the same rolled-back transaction:
        conflict = import_records(
            session,
            [SourceRecord(ticker="TESTA", legal_name="Test Alpha Limited",
                          isin="PK0099999999")],
            source_key="pg_check_2",
            source_display_name="Phase 4 PG check (TEST ONLY)",
        )
        assert conflict.conflicts == 1, conflict
        stored = session.query(Security).filter_by(ticker="TESTA").first()
        assert stored is not None and stored.status == "CONFLICTED"
        assert stored.isin == "PK0011111111", "conflicting import must not overwrite ISIN"
        ambiguous = import_records(
            session,
            [SourceRecord(ticker="TESTA", legal_name="Totally Different Name")],
            source_key="pg_check_3",
            source_display_name="Phase 4 PG check (TEST ONLY)",
        )
        assert ambiguous.pending_review == 1, ambiguous
        from app.models.governance import DataQualityReport as _DQR

        dqr_before = session.query(_DQR).count()
        import_records(
            session,
            [SourceRecord(ticker="TESTA", legal_name="Totally Different Name")],
            source_key="pg_check_3",
            source_display_name="Phase 4 PG check (TEST ONLY)",
        )
        assert session.query(_DQR).count() == dqr_before, "ambiguous re-import must not duplicate reports"
        print("PG adversarial check: conflict CONFLICTED + ISIN unchanged, "
              "ambiguous PENDING_REVIEW, re-import reports de-duplicated")
        report = reconcile(session, None)
        assert report.coverage_ratio is None
        print(f"PG import check: before={before} created=2 idempotent_skip=2")
        print(f"PG reconcile check: registry_tickers={report.registry_tickers} "
              f"coverage={report.coverage_ratio} (no snapshot: no claim)")
    finally:
        session.rollback()
        session.close()

    # API smoke test against the rolled-back (empty) database.
    with TestClient(app, raise_server_exceptions=False) as client:
        for path, expect in [
            ("/api/v1/companies", 200),
            ("/api/v1/securities", 200),
            ("/api/v1/sectors", 200),
            ("/api/v1/registry/statistics", 200),
            ("/api/v1/registry/quality", 200),
            ("/api/v1/registry/sources", 200),
            ("/api/v1/companies/999999", 404),
            ("/api/v1/securities/999999", 404),
            ("/api/v1/companies?limit=999", 422),
        ]:
            resp = client.get(path)
            assert resp.status_code == expect, (path, resp.status_code, resp.text[:200])
            print(f"API {path} -> {resp.status_code}")
        stats = client.get("/api/v1/registry/statistics").json()
        assert stats["companies"] == 0 and stats["securities"] == 0, stats
        print(f"API statistics on live DB: companies={stats['companies']} "
              f"securities={stats['securities']} (empty registry, honestly reported)")
    print("PHASE4_PG_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
