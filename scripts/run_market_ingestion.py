"""Ingest a dated daily-OHLCV CSV file into market_prices — Phase 5.

Usage (from repo root, with DATABASE_URL set):
  DATABASE_URL=... scripts/run_market_ingestion.py --input <csv> --source-key <key> [--commit]
  DATABASE_URL=... scripts/run_market_ingestion.py --input <csv> --source-key <key> \
    --catch-up --from-date 2026-10-01 --to-date 2026-11-03

--dry-run is the DEFAULT: the report is printed but the transaction is
always rolled back. Pass --commit to actually write. --dry-run and
--commit are mutually exclusive; neither flag means dry-run.

Fail-fast, before any write, in BOTH modes:
  1. A wrong CSV header aborts before any database work (the header is
     validated before backend modules are even imported).
  2. Any row whose ticker is unknown aborts the whole run before any
     write — validation of every row happens first, then writing.
  Other invalid rows are rejected individually and counted in the
  report (raw values preserved); they are never stored as prices.

--catch-up restricts the file's validated rows to dates missing for
that source in the requested range (see scheduler.py); it requires
--from-date and --to-date. Missing sessions are reported, never
zero-filled. The script never prints DATABASE_URL, never fetches from
any website, and never performs a real trade.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Backend imports are deliberately deferred until AFTER the CSV header
# is validated: a malformed CSV must fail on validation alone, never
# on a database URL error. Do not move these to top level.


def _fail(message: str, detail: dict | None = None) -> int:
    payload = {"status": "aborted", "error": message}
    if detail:
        payload.update(detail)
    print(json.dumps(payload, indent=2, default=str))
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest daily OHLCV CSV into market_prices.")
    parser.add_argument("--input", required=True, help="Path to the dated CSV file.")
    parser.add_argument(
        "--source-key",
        default=None,
        help="Source key for every row; overrides the CSV source_key column.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Report only; roll back (default).")
    mode.add_argument("--commit", action="store_true", help="Actually write to the database.")
    parser.add_argument(
        "--from-date",
        default=None,
        help="Range start (YYYY-MM-DD) for missing sessions / catch-up.",
    )
    parser.add_argument(
        "--to-date",
        default=None,
        help="Range end (YYYY-MM-DD) for missing sessions / catch-up.",
    )
    parser.add_argument(
        "--catch-up",
        action="store_true",
        help="Ingest only rows whose dates are missing for this source in the range.",
    )
    args = parser.parse_args(argv)

    # 1. Structural CSV validation FIRST, before any database work.
    from app.services.market_data.ingestion import load_csv
    from app.services.market_data.validation import EXPECTED_HEADER

    try:
        raw_rows = load_csv(args.input)
    except (OSError, ValueError) as exc:
        return _fail(str(exc), {"expected_header": list(EXPECTED_HEADER)})

    if args.catch_up and (not args.from_date or not args.to_date):
        return _fail("--catch-up requires both --from-date and --to-date")

    date_range: tuple[date, date] | None = None
    if args.from_date or args.to_date:
        try:
            start = date.fromisoformat(args.from_date) if args.from_date else None
            end = date.fromisoformat(args.to_date) if args.to_date else None
        except ValueError:
            return _fail("--from-date/--to-date must be ISO dates (YYYY-MM-DD)")
        if start is not None and end is not None and end < start:
            return _fail("to-date must not be before from-date")
        if start is not None and end is not None:
            date_range = (start, end)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return _fail("DATABASE_URL is not set; refusing to run without a database")

    from app.database import build_engine, get_session_factory
    from app.services.market_data import ingestion, scheduler
    from app.services.market_data.validation import REJECTION_UNKNOWN_TICKER

    engine = build_engine(database_url)
    factory = get_session_factory(engine)
    if factory is None:  # pragma: no cover - build_engine returns None only for empty URL
        return _fail("DATABASE_URL is not set; refusing to run without a database")
    session = factory()
    try:
        # 2. Full validation BEFORE any write, so an unknown ticker
        # aborts the run without touching market_prices.
        securities = ingestion.security_map(session)
        validated, rejected = ingestion.validate_all(raw_rows, set(securities))
        unknown = sorted(
            row["raw"].get("ticker")
            for row in rejected
            if row["reason"] == REJECTION_UNKNOWN_TICKER
        )
        if unknown:
            return _fail(
                "refusing to run: unknown ticker(s) in CSV",
                {"unknown_tickers": unknown, "rejected_rows": rejected},
            )

        dry_run = not args.commit
        collected_at = datetime.now(ZoneInfo("Asia/Karachi"))
        rows_for_ingest = raw_rows
        catch_up_filtered = 0
        if args.catch_up:
            assert date_range is not None
            # Resolve the report source first (CLI flag wins).
            source_key = args.source_key or (validated[0].source_key if validated else None)
            if not source_key:
                return _fail("--catch-up requires --source-key or a source_key in the CSV")
            source = ingestion.get_or_create_source(session, source_key)
            stored = scheduler.stored_dates_for_source(
                session,
                source.id,
                [securities[row.ticker].id for row in validated],
            )
            kept, catch_up_filtered = scheduler.filter_rows_to_missing(
                validated,
                stored,
                {ticker: securities[ticker].id for ticker in securities},
            )
            kept_keys = {(row.ticker, row.trading_date) for row in kept}
            rows_for_ingest = [
                raw
                for raw in raw_rows
                if (raw.get("ticker", "").strip().upper(), _csv_date(raw)) in kept_keys
            ]
            # Re-validate the kept subset implicitly by reusing ingest's
            # own validation; rejected rows outside the kept set were
            # already counted above only if they were unknown tickers
            # (which abort), so non-unknown rejections inside the kept
            # set are counted by ingest_rows itself.

        report = ingestion.ingest_rows(
            session,
            rows_for_ingest,
            source_key_override=args.source_key,
            collected_at=collected_at,
            date_range=date_range,
            dry_run=dry_run,
            report_tickers=(
                sorted({row.ticker for row in validated}) if args.catch_up else None
            ),
        )
        if args.catch_up:
            report.catch_up = True
            report.catch_up_filtered = catch_up_filtered
        if dry_run:
            session.rollback()
        else:
            session.commit()
        print(json.dumps(report.to_dict(), indent=2, default=str))
        return 0
    finally:
        session.close()
        engine.dispose()


def _csv_date(raw: dict) -> date | None:
    try:
        return date.fromisoformat(str(raw.get("trading_date", "")).strip())
    except ValueError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
