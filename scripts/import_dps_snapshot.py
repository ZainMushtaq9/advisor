"""Import a DPS Listing Status snapshot CSV through the Phase 4 registry engine.

Snapshot CSV contract (see docs/phase-04/source_research_raw/
dps_listing_status_2026-11-04_main_board_normal_counter.README.md):
  columns: row_no,symbol,name,sector,clearing_type
  - row_no: 1..N continuous, in the order the browser read the pages.
  - symbol: DPS symbol exactly as displayed (ticker). No duplicates.
  - name: company name EXACTLY as displayed, including any apparent
    abbreviation or typo. Never completed or corrected by guessing.
  - sector: sector EXACTLY as displayed. No canonical mapping is applied
    here; the importer stores the source sector verbatim.
  - clearing_type: "NC" or blank. Blank is stored as-is (no value
    invented); it is NOT mapped to a listing status.

Verification rule (Phase 4 audit H1, applied honestly):
  This snapshot is a SINGLE source (DPS). VERIFIED requires >=2 distinct
  agreeing sources including one official, so records imported from
  this file alone MUST stay UNVERIFIED. The importer never sets
  VERIFIED; verification.py promotes only from evidence, and a lone
  source cannot promote. Clearing Type is NOT a verification status
  and is NOT a listing status; it is recorded in the import log only.

Scope limitation: the snapshot covers Main Board / Normal Counter
ONLY. GEM Board and Non-Compliant/Winding-Up rows were counted but
not fully captured, so this import is NOT the full PSX registry and
must never be cited as full-market completeness.

Usage (from repo root, with database/.env present):
  DATABASE_URL=<from database/.env> backend/.venv/bin/python \\
      scripts/import_dps_snapshot.py --csv <path> --dry-run
  DATABASE_URL=<from database/.env> backend/.venv/bin/python \\
      scripts/import_dps_snapshot.py --csv <path> --commit

--dry-run imports inside a transaction that is ALWAYS rolled back
and prints the result + reconciliation. --commit commits the import.
Without --commit, --dry-run is the default (safe). The script never
prints DATABASE_URL. It never fetches from any website.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Backend imports are deliberately deferred into main(), AFTER the CSV
# is validated: importing app.main builds the database engine from
# settings at import time, and a malformed CSV must fail on validation
# alone, never on a database URL error. Do not move these to top level.

SOURCE_KEY = "dps_listing_status_2026-11-04_main_board_normal_counter"
SOURCE_DISPLAY = (
    "DPS Listing Status, Main Board / Normal Counter, "
    "page header Nov 4, 2026 1:17 PM (live browser page-by-page)"
)
# Page header time on the DPS portal during the parent browser read.
COLLECTED_AT = datetime(2026, 11, 4, 13, 17, tzinfo=timezone.utc).astimezone(
    timezone.utc
)


def load_snapshot_csv(path: str) -> list[dict]:
    """Load and strictly validate the snapshot CSV. Any structural
    problem raises ValueError with the exact problem — rows are never
    repaired by guessing."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        expected = ["row_no", "symbol", "name", "sector", "clearing_type"]
        if reader.fieldnames != expected:
            raise ValueError(
                f"CSV header must be exactly {expected}, got {reader.fieldnames}"
            )
        rows = list(reader)
    if not rows:
        raise ValueError("CSV contains no data rows")
    seen_symbols: set[str] = set()
    for i, row in enumerate(rows, start=1):
        try:
            row_no = int(row["row_no"])
        except (TypeError, ValueError):
            raise ValueError(f"Row {i}: row_no {row['row_no']!r} is not an integer")
        if row_no != i:
            raise ValueError(
                f"Row {i}: row_no is {row_no}, expected continuous {i}"
            )
        symbol = (row["symbol"] or "").strip()
        name = (row["name"] or "").strip()
        sector = (row["sector"] or "").strip()
        if not symbol:
            raise ValueError(f"Row {i}: empty symbol")
        if not name:
            raise ValueError(f"Row {i}: empty name for symbol {symbol}")
        if not sector:
            raise ValueError(f"Row {i}: empty sector for symbol {symbol}")
        if symbol in seen_symbols:
            raise ValueError(f"Row {i}: duplicate symbol {symbol!r}")
        seen_symbols.add(symbol)
        ct = (row["clearing_type"] or "").strip()
        if ct not in ("", "NC"):
            raise ValueError(
                f"Row {i} ({symbol}): clearing_type {ct!r} is not '' or 'NC'"
            )
    return rows


def db_counts(session, Company, Sector, Security, RegistryEvidence,  # noqa: N803
              CompanyIdentifier, SymbolHistory, DataQualityReport) -> dict:
    from sqlalchemy import func

    def by_status(model):
        return dict(
            session.query(model.status, func.count())
            .group_by(model.status)
            .all()
        )

    return {
        "companies": session.query(Company).count(),
        "securities": session.query(Security).count(),
        "sectors": session.query(Sector).count(),
        "registry_evidence": session.query(RegistryEvidence).count(),
        "company_identifiers": session.query(CompanyIdentifier).count(),
        "symbol_history": session.query(SymbolHistory).count(),
        "quality_reports": session.query(DataQualityReport).count(),
        "companies_by_status": by_status(Company),
        "securities_by_status": by_status(Security),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="Snapshot CSV path")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Rollback (default)")
    mode.add_argument("--commit", action="store_true", help="Commit the import")
    args = parser.parse_args()
    rows = load_snapshot_csv(args.csv)
    print(f"Snapshot CSV validated: {len(rows)} rows, "
          f"row_no 1..{len(rows)} continuous, no duplicate symbols")
    blank_ct = [r["symbol"] for r in rows if not (r["clearing_type"] or "").strip()]
    print(f"Blank Clearing Type rows in file: {len(blank_ct)}: {blank_ct}")

    assert os.environ.get("DATABASE_URL"), "DATABASE_URL must be set"
    from app.database import get_session_factory
    from app.main import create_app
    from app.models.governance import DataQualityReport
    from app.models.reference import (
        Company, CompanyIdentifier, Sector, Security, SymbolHistory,
    )
    from app.models.registry import RegistryEvidence
    from app.services.registry.importer import SourceRecord, import_records
    from app.services.registry.reconciliation import reconcile

    app = create_app()
    factory = get_session_factory(app.state.engine)
    assert factory is not None
    session = factory()
    try:
        before = db_counts(session, Company, Sector, Security, RegistryEvidence, CompanyIdentifier, SymbolHistory, DataQualityReport)
        print(f"DB before: {before}")
        records = [
            SourceRecord(
                ticker=r["symbol"],
                legal_name=r["name"],
                sector_name=r["sector"],
            )
            for r in rows
        ]
        result = import_records(
            session,
            records,
            source_key=SOURCE_KEY,
            source_display_name=SOURCE_DISPLAY,
            collected_at=COLLECTED_AT,
        )
        print(f"Import result: seen={result.records_seen} "
              f"companies_created={result.companies_created} "
              f"securities_created={result.securities_created} "
              f"sectors_created={result.sectors_created} "
              f"evidence_created={result.evidence_created} "
              f"skipped_as_duplicate={result.skipped_as_duplicate} "
              f"pending_review={result.pending_review} "
              f"conflicts={result.conflicts} rejected={result.rejected}")
        for err in result.errors:
            print(f"  import error: {err}")
        # Idempotency proof inside the same transaction: a second
        # import of the same batch must create nothing.
        again = import_records(
            session,
            records,
            source_key=SOURCE_KEY,
            source_display_name=SOURCE_DISPLAY,
            collected_at=COLLECTED_AT,
        )
        print(f"Re-import (idempotency): skipped_as_duplicate="
              f"{again.skipped_as_duplicate} companies_created="
              f"{again.companies_created} securities_created="
              f"{again.securities_created}")
        if again.skipped_as_duplicate != len(rows):
            print("WARNING: re-import did not skip every row; "
                  "check the import log before committing")
        snap = {
            "source": SOURCE_KEY,
            "snapshot_date": "2026-11-04",
            "tickers": [r["symbol"] for r in rows],
            "dropped": 0,
        }
        report = reconcile(session, snap)
        print(f"Reconciliation: snapshot_tickers={report.snapshot_tickers} "
              f"registry_tickers={report.registry_tickers} "
              f"matched={report.matched} coverage_ratio={report.coverage_ratio}")
        print(f"  missing_from_registry ({len(report.missing_from_registry)}): "
              f"{report.missing_from_registry[:50]}")
        print(f"  extra_in_registry ({len(report.extra_in_registry)}): "
              f"{report.extra_in_registry[:50]}")
        after = db_counts(session, Company, Sector, Security, RegistryEvidence, CompanyIdentifier, SymbolHistory, DataQualityReport)
        print(f"DB after import (pre-commit decision): {after}")
        verified = after["securities_by_status"].get("VERIFIED", 0)
        print(f"VERIFIED securities after single-source import: {verified} "
              f"(must be 0; a lone DPS source cannot verify)")
        if args.commit:
            session.commit()
            print("COMMITTED.")
        else:
            session.rollback()
            print("DRY RUN: rolled back, live database unchanged.")
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
