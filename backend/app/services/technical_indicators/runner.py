"""Production assessment runner (Phase 6).

Reads ONLY already-committed daily market_prices rows (never a new
external fetch), assesses every registered indicator for every
registry security, and — on --commit only — writes:

- one TechnicalCalculationRun row (counts, never values),
- one TechnicalCalculationError row per (indicator_key, reason,
  bars_available) aggregate (security_id NULL: these are coverage
  summaries, not per-security error logs; per-security verdicts
  stay available through the live coverage API, which recomputes
  them deterministically from market_prices),
- one TechnicalIndicatorValue row per CALCULABLE verdict, and
  only when no row already exists for that grain (idempotent).

Correction propagation (implemented, audit finding H3): market_prices
rows are immutable, so an input never changes in place. If a
correction ever arrives for an existing grain, the operator
re-runs with changed parameters and get_active_config()
deactivates the superseded active configuration and creates a
new one with a bumped config_version; corrected values are
stored under it, old rows are retained (and the Phase 6
immutability migration makes UPDATE/DELETE raise). The values
API exposes indicator_key, configuration id, config_version and
parameters per row, so a consumer can ask for a version.
Incremental recalculation: a re-run only writes grains that do
not already exist; existing value rows are never rewritten.
Re-run guard (audit finding H4): a completed run for the same
run_key is never duplicated — a second --commit for the same
as-of reports already_recorded and writes nothing. (Late-arriving
rows for an already-run as-of date need operator handling with
a distinct run_key; that path is not automated here.)

Quality governance: CONFLICTED or REJECTED input rows are
flagged, not silently dropped: load_series() returns the set of
tickers with such rows, and every indicator for those tickers
is NOT_CALCULABLE with reason conflicted_input (audit H2).
Computed values inherit the lowest input quality; with today's
single UNVERIFIED source, any future value would be UNVERIFIED.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.financial import (
    TechnicalCalculationError,
    TechnicalCalculationRun,
    TechnicalIndicatorConfiguration,
    TechnicalIndicatorDefinition,
    TechnicalIndicatorValue,
)
from app.models.market import MarketPrice
from app.models.reference import Security
from app.services.technical_indicators import conventions, coverage

PKT = ZoneInfo("Asia/Karachi")


def seed_definitions(session: Session) -> dict[str, TechnicalIndicatorDefinition]:
    """Insert missing indicator definitions; refresh text on change.

    Definitions are metadata, not history: correcting formula text
    updates the row in place (with its version), while computed
    values keep the calculation_version they were written with.
    """
    by_key: dict[str, TechnicalIndicatorDefinition] = {}
    for spec in conventions.INDICATORS:
        row = (
            session.query(TechnicalIndicatorDefinition)
            .filter_by(indicator_key=spec.key)
            .one_or_none()
        )
        if row is None:
            row = TechnicalIndicatorDefinition(
                indicator_key=spec.key,
                category=spec.category,
                formula_text=spec.formula_text,
                formula_version=spec.formula_version,
                default_parameters=spec.default_parameters(),
                warmup_periods=spec.warmup_bars,
            )
            session.add(row)
            session.flush()
        elif (
            row.formula_text != spec.formula_text
            or row.formula_version != spec.formula_version
            or row.default_parameters != spec.default_parameters()
            or row.warmup_periods != spec.warmup_bars
        ):
            row.formula_text = spec.formula_text
            row.formula_version = spec.formula_version
            row.default_parameters = spec.default_parameters()
            row.warmup_periods = spec.warmup_bars
        by_key[spec.key] = row
    return by_key


def _bump_version(existing: list[str]) -> str:
    """Next config_version: minor bump of the highest existing one."""
    best = (0, 0)
    for version in existing:
        try:
            major, minor = version.split(".", 1)
            best = max(best, (int(major), int(minor)))
        except ValueError:
            continue
    if best == (0, 0):
        return "1.0"
    return f"{best[0]}.{best[1] + 1}"


def get_active_config(
    session: Session, definition: TechnicalIndicatorDefinition, parameters: dict
) -> TechnicalIndicatorConfiguration:
    """Return the active configuration with exactly these parameters.

    If none matches, the superseded active configurations are
    deactivated and a new one is created with a bumped version —
    this is the correction-propagation path: old value rows stay
    under their old configuration, new values go under the new one.
    """
    configs = (
        session.query(TechnicalIndicatorConfiguration)
        .filter_by(indicator_definition_id=definition.id)
        .all()
    )
    for config in configs:
        if config.is_active and (config.parameters or {}) == parameters:
            return config
    for config in configs:
        if config.is_active:
            config.is_active = False
    config = TechnicalIndicatorConfiguration(
        indicator_definition_id=definition.id,
        parameters=parameters,
        config_version=_bump_version([c.config_version for c in configs]),
        is_active=True,
    )
    session.add(config)
    session.flush()
    return config


def load_series(
    session: Session,
) -> tuple[dict[str, list[dict]], dict[str, int], set[str]]:
    """Load daily bars per ticker.

    Returns (series, security_ids, conflicted_tickers). CONFLICTED
    and REJECTED rows are kept OUT of the series but their tickers
    are flagged, so coverage reports conflicted_input instead of
    pretending the security had no data (audit H2).
    """
    rows = (
        session.query(Security.ticker, MarketPrice)
        .join(MarketPrice, MarketPrice.security_id == Security.id)
        .filter(MarketPrice.bar_type == "daily")
        .order_by(Security.ticker, MarketPrice.trading_date)
        .all()
    )
    series: dict[str, list[dict]] = {}
    security_ids: dict[str, int] = {}
    conflicted: set[str] = set()
    for ticker, price in rows:
        if price.quality_status in ("CONFLICTED", "REJECTED"):
            conflicted.add(ticker)
            continue
        series.setdefault(ticker, []).append(
            {
                "date": price.trading_date,
                "open": price.open_price,
                "high": price.high_price,
                "low": price.low_price,
                "close": price.close_price,
                "volume": price.volume,
                "previous_close": price.previous_close,
                "quality_status": price.quality_status,
                "source_key": price.source_key,
            }
        )
    for security in session.query(Security).order_by(Security.ticker).all():
        series.setdefault(security.ticker, [])
        security_ids[security.ticker] = security.id
    return series, security_ids, conflicted


def run_assessment(
    session: Session, as_of: date | None = None, dry_run: bool = True
) -> dict:
    """Assess the market; write run + error + value rows unless dry-run."""
    started = datetime.now(PKT)
    series, security_ids, conflicted = load_series(session)
    if as_of is None:
        all_dates = [b["date"] for bars in series.values() for b in bars]
        as_of = max(all_dates) if all_dates else None
    assessment = coverage.assess_market(series, as_of, conflicted_tickers=conflicted)
    run_key = f"phase06-coverage-{as_of.isoformat() if as_of else 'nodata'}"

    values_written = 0
    error_rows = 0
    already_recorded = False
    if not dry_run:
        existing = (
            session.query(TechnicalCalculationRun)
            .filter_by(run_key=run_key, status="completed")
            .one_or_none()
        )
        if existing is not None:
            already_recorded = True
            return {
                "run_key": run_key,
                "dry_run": dry_run,
                "as_of": as_of.isoformat() if as_of else None,
                "securities_assessed": assessment["securities_assessed"],
                "indicators_registered": assessment["indicators_registered"],
                "securities_with_any_calculable": assessment[
                    "securities_with_any_calculable"
                ],
                "values_written": 0,
                "error_rows_written": 0,
                "already_recorded": True,
                "per_indicator": assessment["per_indicator"],
            }
        definitions = seed_definitions(session)
        configs = {
            key: get_active_config(session, definitions[key], spec.default_parameters())
            for key, spec in ((s.key, s) for s in conventions.INDICATORS)
        }
        run = TechnicalCalculationRun(
            run_key=run_key,
            started_at=started,
            status="running",
            securities_processed=assessment["securities_assessed"],
            records_written=0,
        )
        session.add(run)
        session.flush()
        # Aggregate error rows: (indicator, reason, bars_available).
        aggregates: dict[tuple[str, str, int], list[str]] = {}
        for ticker, detail in assessment["per_ticker"].items():
            for verdict in detail["verdicts"]:
                if verdict["status"] == "CALCULABLE":
                    continue
                bars_n = detail["bars_available"]
                aggregates.setdefault(
                    (verdict["indicator_key"], verdict["reason"] or "unknown", bars_n),
                    [],
                ).append(verdict["detail"] or verdict["reason"] or "")
        for (key, reason, bars_n), details in sorted(aggregates.items()):
            session.add(
                TechnicalCalculationError(
                    run_id=run.id,
                    security_id=None,
                    indicator_key=key,
                    error_type=reason,
                    detail=f"{len(details)} securities with {bars_n} bars: {details[0]}",
                )
            )
            error_rows += 1
        # Value rows, only for CALCULABLE verdicts, only new grains.
        for ticker, detail in assessment["per_ticker"].items():
            security_id = security_ids[ticker]
            input_quality = detail["input_quality"]
            # Source lineage comes from the as-of-sliced bars only,
            # never from bars dated after the assessment date.
            obs_for_source = (
                date.fromisoformat(detail["as_of"]) if detail["as_of"] else None
            )
            sliced = [
                b
                for b in series[ticker]
                if obs_for_source is None or b["date"] <= obs_for_source
            ]
            source_keys = {b.get("source_key") for b in sliced if b.get("source_key")}
            source_key = source_keys.pop() if len(source_keys) == 1 else "multiple"
            for verdict in detail["verdicts"]:
                if verdict["status"] != "CALCULABLE":
                    continue
                config = configs[verdict["indicator_key"]]
                obs_date = date.fromisoformat(detail["as_of"]) if detail["as_of"] else None
                if obs_date is None:
                    continue
                exists = (
                    session.query(TechnicalIndicatorValue)
                    .filter_by(
                        security_id=security_id,
                        indicator_configuration_id=config.id,
                        observation_date=obs_date,
                        timeframe="daily",
                    )
                    .one_or_none()
                )
                if exists is not None:
                    continue
                session.add(
                    TechnicalIndicatorValue(
                        security_id=security_id,
                        indicator_configuration_id=config.id,
                        observation_date=obs_date,
                        timeframe="daily",
                        value=Decimal(verdict["value"]),
                        calculation_version=verdict["formula_version"],
                        last_input_observation_date=date.fromisoformat(detail["last_date"])
                        if detail["last_date"]
                        else None,
                        quality_status=input_quality,
                        source_key=source_key,
                        collected_at=datetime.now(PKT),
                    )
                )
                values_written += 1
        run.status = "completed"
        run.ended_at = datetime.now(PKT)
        run.records_written = values_written
        session.commit()
    return {
        "run_key": run_key,
        "dry_run": dry_run,
        "as_of": as_of.isoformat() if as_of else None,
        "securities_assessed": assessment["securities_assessed"],
        "indicators_registered": assessment["indicators_registered"],
        "securities_with_any_calculable": assessment["securities_with_any_calculable"],
        "values_written": values_written,
        "error_rows_written": error_rows,
        "already_recorded": already_recorded,
        "per_indicator": assessment["per_indicator"],
    }
