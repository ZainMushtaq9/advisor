"""Validated dated-file ingestion for daily OHLCV — Phase 5.

Contract:
- Input is a CSV file with exactly the EXPECTED_HEADER (see
  validation.py). A wrong header raises ValueError before any write.
- Rejected rows are never stored as prices: the report preserves their
  raw values and rejection reason, and nothing is written for them.
- Idempotent: re-ingesting the same grain (security_id, trading_date,
  bar_type "daily", data_source_id) SKIPS — no duplicates, no
  overwrites. market_prices is immutable per Phase 3 triggers, so an
  insert that would violate the grain unique constraint is skipped
  and counted as skipped, never updated.
- Quality is assigned at insert time (see quality.py). All stored
  prices have is_adjusted=False (official unadjusted values).
- Missing sessions: for the requested range (explicit --from/--to, or
  otherwise the span of validated trading dates in the file), every
  date with no observation for a security from THIS source is listed
  in the report. Missing dates are never zero-filled and never stored
  as rows.
- This module never commits: the caller (CLI) commits or rolls back.
  Dry-run therefore leaves the database untouched even though rows
  were flushed for counting.
- No network, no live adapter, no scraper. The operator supplies the
  file; this module only validates, matches, and stores it.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.governance import DataSource
from app.models.market import MarketPrice
from app.models.reference import Security
from app.services.market_data import quality, scheduler
from app.services.market_data.validation import (
    EXPECTED_HEADER,
    ValidatedRow,
    karachi_today,
    validate_row,
)

BAR_TYPE = "daily"

SCOPE_NOTE = "470 Main Board / Normal Counter snapshot securities"

FRESHNESS_RULE_NOTE = (
    "V1 freshness rule: an observation collected more than 30 days "
    "after its trading_date is labelled STALE, in addition to its "
    "quality_status. No other freshness rule applies in v1."
)


@dataclass
class IngestionReport:
    source_key: str
    dry_run: bool
    ingested: int = 0
    skipped: int = 0
    rejected: int = 0
    conflicted: int = 0
    stale: int = 0
    quality_breakdown: dict[str, int] = field(default_factory=dict)
    rejected_rows: list[dict] = field(default_factory=list)
    missing_sessions: dict[str, list[str]] = field(default_factory=dict)
    catch_up: bool = False
    catch_up_filtered: int = 0

    def to_dict(self) -> dict:
        return {
            "source_key": self.source_key,
            "bar_type": BAR_TYPE,
            "dry_run": self.dry_run,
            "ingested": self.ingested,
            "skipped": self.skipped,
            "rejected": self.rejected,
            "conflicted": self.conflicted,
            "stale": self.stale,
            "quality_breakdown": dict(self.quality_breakdown),
            "rejected_rows": self.rejected_rows,
            "missing_sessions": self.missing_sessions,
            "catch_up": self.catch_up,
            "catch_up_filtered": self.catch_up_filtered,
            "scope_note": SCOPE_NOTE,
            "freshness_rule_note": FRESHNESS_RULE_NOTE,
            "note": (
                "Missing sessions are dates with no stored observation "
                "for that security from this source. They are reported, "
                "never zero-filled, and no price row is stored for them."
            ),
        }


def load_csv(path: str) -> list[dict]:
    """Load a CSV file, requiring exactly EXPECTED_HEADER.

    Raises ValueError on a wrong header or an empty file, before any
    database work. Raw row dicts are returned unmodified.
    """
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != EXPECTED_HEADER:
            raise ValueError(
                f"CSV header must be exactly {list(EXPECTED_HEADER)}, "
                f"got {reader.fieldnames}"
            )
        rows = list(reader)
    if not rows:
        raise ValueError("CSV contains no data rows")
    return rows


def get_or_create_source(session: Session, source_key: str) -> DataSource:
    """Resolve a DataSource row by source_key, creating an UNVERIFIED
    one when absent (mirrors the Phase 4 registry importer)."""
    source = session.query(DataSource).filter_by(source_key=source_key).first()
    if source is None:
        source = DataSource(
            source_key=source_key,
            display_name=source_key,
            source_type="file_import",
            base_reference="operator-supplied dated CSV file",
        )
        session.add(source)
        session.flush()
    return source


def security_map(session: Session) -> dict[str, Security]:
    """Ticker (upper-cased, stripped) -> Security, for all securities."""
    return {
        security.ticker.strip().upper(): security
        for security in session.query(Security).all()
    }


def validate_all(
    raw_rows: list[dict],
    known_tickers: set[str],
    today: date | None = None,
) -> tuple[list[ValidatedRow], list[dict]]:
    """Pure validation pass over every row.

    Returns (validated_rows, rejected_rows) where each rejected row is
    {"raw": <original row dict>, "reason": <reason code>}. No database
    access, no writes — the CLI runs this before any write so it can
    fail fast on unknown tickers.
    """
    validated: list[ValidatedRow] = []
    rejected: list[dict] = []
    for raw in raw_rows:
        row, reason = validate_row(raw, known_tickers, today=today)
        if row is None:
            rejected.append({"raw": dict(raw), "reason": reason})
        else:
            validated.append(row)
    return validated, rejected


def ingest_rows(
    session: Session,
    raw_rows: list[dict],
    *,
    source_key_override: str | None = None,
    collected_at: datetime | None = None,
    today: date | None = None,
    date_range: tuple[date, date] | None = None,
    dry_run: bool = True,
    report_tickers: list[str] | None = None,
) -> IngestionReport:
    """Validate and ingest raw rows. Flushes but never commits.

    ``source_key_override`` (the CLI --source-key) wins over a row's
    own source_key; when neither is present the row is rejected as a
    missing field. Unknown tickers are rejected per-row here; the CLI
    additionally aborts the whole run before any write when any row
    has an unknown ticker.
    """
    if today is None:
        today = karachi_today()
    if collected_at is None:
        from zoneinfo import ZoneInfo

        collected_at = datetime.now(ZoneInfo("Asia/Karachi"))
    securities = security_map(session)
    validated, rejected = validate_all(raw_rows, set(securities), today=today)

    # Resolve the effective source per row; a row with no source at all
    # cannot satisfy the NOT NULL grain source, so it is rejected.
    effective_rows: list[tuple[ValidatedRow, str]] = []
    for row in validated:
        effective_source = (source_key_override or row.source_key or "").strip()
        if not effective_source:
            rejected.append({"raw": {"ticker": row.ticker}, "reason": "missing_field"})
        else:
            effective_rows.append((row, effective_source))

    # One source per run is the supported shape: the CLI passes a single
    # --source-key, and a file without one must still resolve to exactly
    # one source_key per row. Group by source so a mixed file cannot
    # silently share one report's source_key.
    sources: dict[str, DataSource] = {}
    for _, source_key in effective_rows:
        if source_key not in sources:
            sources[source_key] = get_or_create_source(session, source_key)
    report_source = (
        source_key_override
        if source_key_override
        else (effective_rows[0][1] if effective_rows else "")
    )
    # A fully filtered-out catch-up run has no effective rows, but its
    # source is still known (the CLI flag): resolve it so the missing
    # -session report can still be computed for that source.
    if report_source and report_source not in sources:
        sources[report_source] = get_or_create_source(session, report_source)
    report = IngestionReport(source_key=report_source, dry_run=dry_run)
    report.rejected = len(rejected)
    report.rejected_rows = rejected

    # Stored observations for the affected grains, grouped by
    # (security_id, trading_date): [(source_key, ohlcv), ...].
    grain_keys = {
        (securities[row.ticker].id, row.trading_date) for row, _ in effective_rows
    }
    stored_by_grain: dict[tuple[int, date], list[tuple[str | None, tuple]]] = {}
    if grain_keys:
        security_ids = sorted({security_id for security_id, _ in grain_keys})
        dates = sorted({trading_date for _, trading_date in grain_keys})
        stored = (
            session.query(MarketPrice)
            .filter(
                MarketPrice.bar_type == BAR_TYPE,
                MarketPrice.security_id.in_(security_ids),
                MarketPrice.trading_date.in_(dates),
            )
            .all()
        )
        for price in stored:
            stored_by_grain.setdefault(
                (price.security_id, price.trading_date), []
            ).append(
                (
                    price.source_key,
                    (
                        price.open_price,
                        price.high_price,
                        price.low_price,
                        price.close_price,
                        price.volume,
                    ),
                )
            )

    # Quality is PRECOMPUTED for every candidate before any insert,
    # against stored rows AND every other candidate in this run. That
    # is what makes two disagreeing rows in one file BOTH land as
    # CONFLICTED, instead of the first landing UNVERIFIED merely
    # because it was inserted first (see quality.py's immutability
    # caveat: a stored row cannot be re-flagged later).
    candidates_by_grain: dict[tuple[int, date], dict[str, tuple]] = {}
    for row, source_key in effective_rows:
        grain_key = (securities[row.ticker].id, row.trading_date)
        candidates_by_grain.setdefault(grain_key, {}).setdefault(
            source_key, row.ohlcv()
        )
    precomputed_status: dict[tuple[int, date, str], str] = {}
    for (security_id, trading_date), by_source in candidates_by_grain.items():
        for source_key, ohlcv in by_source.items():
            others = [
                (s, o)
                for (s, o) in stored_by_grain.get((security_id, trading_date), [])
                if s != source_key
            ] + [
                (s, o) for (s, o) in by_source.items() if s != source_key
            ]
            precomputed_status[(security_id, trading_date, source_key)] = (
                quality.assign_quality(source_key, ohlcv, others)
            )

    inserted_grains: set[tuple[int, date, int]] = set()
    for row, source_key in effective_rows:
        security = securities[row.ticker]
        source = sources[source_key]
        grain = (security.id, row.trading_date, source.id)
        if grain in inserted_grains:
            report.skipped += 1
            continue
        # Already stored under this exact grain (e.g. a re-ingest):
        # skip, never overwrite — market_prices is immutable. The
        # stored_by_grain snapshot covers every grain in this file,
        # so this check needs no extra query.
        already_stored = any(
            stored_source == source_key
            for stored_source, _ in stored_by_grain.get(
                (security.id, row.trading_date), []
            )
        )
        if already_stored:
            report.skipped += 1
            inserted_grains.add(grain)
            continue
        status = precomputed_status[(security.id, row.trading_date, source_key)]
        freshness = quality.freshness_label(collected_at, row.trading_date)
        price = MarketPrice(
            security_id=security.id,
            data_source_id=source.id,
            trading_date=row.trading_date,
            bar_type=BAR_TYPE,
            open_price=row.open_price,
            high_price=row.high_price,
            low_price=row.low_price,
            close_price=row.close_price,
            volume=row.volume,
            turnover=row.turnover,
            previous_close=row.previous_close,
            is_adjusted=False,
            source_key=source_key,
            source_timestamp=row.source_timestamp,
            collected_at=collected_at,
            quality_status=status,
        )
        try:
            # Per-row SAVEPOINT: a grain unique-constraint failure
            # rolls back only this row, never the whole run.
            with session.begin_nested():
                session.add(price)
                session.flush()
        except IntegrityError:
            # Duplicate grain that the pre-check could not see (e.g. a
            # concurrent insert): skip, never update.
            report.skipped += 1
            inserted_grains.add(grain)
            continue
        inserted_grains.add(grain)
        report.ingested += 1
        report.quality_breakdown[status] = report.quality_breakdown.get(status, 0) + 1
        if status == "CONFLICTED":
            report.conflicted += 1
        if freshness == quality.FRESHNESS_STALE:
            report.stale += 1

    # Missing sessions for the requested range (or the validated span).
    if date_range is not None:
        start, end = date_range
    elif effective_rows:
        dates = [row.trading_date for row, _ in effective_rows]
        start, end = min(dates), max(dates)
    else:
        start = end = None  # type: ignore[assignment]
    if start is not None and end is not None:
        # Stored-after-ingest view per ticker, for the report's source:
        # a date counts as observed when this source has a row for it.
        # (Just-flushed rows are visible to the session's own queries.)
        # report_tickers (used by --catch-up) keeps tickers whose rows
        # were all filtered out visible in the missing-session report.
        tickers_in_file = [
            ticker
            for ticker in (
                report_tickers or sorted({row.ticker for row, _ in effective_rows})
            )
            if ticker in securities
        ]
        if tickers_in_file and report_source in sources:
            source = sources[report_source]
            stored_for_source = scheduler.stored_dates_for_source(
                session,
                source.id,
                [securities[ticker].id for ticker in tickers_in_file],
            )
            stored_by_ticker = {
                ticker: stored_for_source.get(securities[ticker].id, set())
                for ticker in tickers_in_file
            }
            report.missing_sessions = scheduler.missing_sessions_by_security(
                stored_by_ticker, tickers_in_file, start, end
            )
    return report
