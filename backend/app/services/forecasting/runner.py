"""Phase 13 runner: registry + feature store + assessments. No HTTP fetch.

Scope decision (documented, not hidden): the analysis universe is
the 4 statement companies (HUBC, NML, OGDC, HBL) — the same scope as
Phases 8–12. HBL joined in the post-Phase-30 HBL re-run batch, once
its CY2025 statements were extracted; before that it had a price row
but no statements, so its assessments were pending. The other 466
registry companies have neither statements nor a price series longer
than one row, and assessing 444 of them would add identical
abstention rows without information. When Phase 7 expands, re-running
this script adds companies without redesign (the grain is per security).

Series lengths are READ from the database, never assumed:
- close_price / volume: count of market_prices rows per security.
- return / direction / volatility: closes - 1 (a return needs a
  consecutive pair; one close yields zero returns).
- earnings: count of distinct income-statement period_ends per
  company (current + prior-year comparative column, both stored as
  rows by Phase 7 — e.g. HUBC FY2025 + FY2026 = 2).
- macro series: count of distinct observation_dates per indicator
  code among current (is_current) rows.

No forecast with a validated interval exists in this run, so the
Phase 3 ``forecasts`` table is deliberately left at 0 rows and no
point estimate is stored anywhere: see models/forecasting.py.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models.analysis import EconomicIndicator, Valuation
from app.models.financial import (
    FinancialStatement,
    FundamentalMetricDefinition,
    FundamentalMetricValue,
)
from app.models.forecasting import (
    ForecastAssessment,
    ForecastFeatureSnapshot,
    ForecastTarget,
)
from app.models.market import MarketPrice
from app.models.reference import Company, Security

from . import HORIZONS, TARGETS, method_requirements
from .coverage import assess

COMPANY_TICKERS = ("HUBC", "NML", "OGDC", "HBL")
COMPANY_TARGETS = ("close_price", "return", "direction", "volatility", "volume", "earnings")
MACRO_TARGETS = {
    "macro_policy_rate": "sbp_policy_rate",
    "macro_cpi_yoy": "cpi_yoy",
}
PRICE_ORIGIN = date(2026, 11, 3)
MACRO_ORIGIN = date(2026, 11, 4)


def _dec(value) -> str | None:
    return None if value is None else str(value)


def _series_lengths(session, security) -> dict:
    """Series lengths per company target, read from stored rows."""
    prices = (
        session.query(MarketPrice)
        .filter(MarketPrice.security_id == security.id)
        .order_by(MarketPrice.trading_date)
        .all()
    )
    closes = len(prices)
    income_periods = (
        session.query(FinancialStatement.period_end)
        .filter(
            FinancialStatement.company_id == security.company_id,
            FinancialStatement.statement_type == "income",
        )
        .distinct()
        .all()
    )
    earnings = len(income_periods)
    latest_price = prices[-1] if prices else None
    return {
        "close_price": closes,
        "return": max(0, closes - 1),
        "direction": max(0, closes - 1),
        "volatility": max(0, closes - 1),
        "volume": closes,
        "earnings": earnings,
        "latest_price": latest_price,
        "income_period_ends": sorted(str(p[0]) for p in income_periods),
    }


def _macro_series_lengths(session) -> dict:
    out = {}
    for target_key, code in MACRO_TARGETS.items():
        dates = (
            session.query(EconomicIndicator.observation_date)
            .filter(
                EconomicIndicator.indicator_code == code,
                EconomicIndicator.is_current.is_(True),
            )
            .distinct()
            .all()
        )
        out[target_key] = {
            "length": len(dates),
            "observation_dates": sorted(str(d[0]) for d in dates),
        }
    return out


def run_forecasting(session, commit: bool = False, company_filter: str | None = None) -> dict:
    """Build the Phase 13 registry, feature store and assessments."""
    report = {
        "targets_written": 0,
        "targets_skipped": 0,
        "snapshots_written": 0,
        "snapshots_skipped": 0,
        "assessments_written": 0,
        "assessments_skipped": 0,
        "assessments_computed": 0,
        "phase3_forecasts_rows": 0,
        "companies": [],
        "hbl_pending": True,
    }

    # --- Target registry: 8 targets x 6 horizons = 48 rows. ---
    requirements = method_requirements()
    for target_key, (target_type, scope, _series_desc) in TARGETS.items():
        for horizon in HORIZONS:
            existing = (
                session.query(ForecastTarget)
                .filter(
                    ForecastTarget.target_key == target_key,
                    ForecastTarget.horizon == horizon,
                )
                .first()
            )
            if existing:
                report["targets_skipped"] += 1
                continue
            session.add(
                ForecastTarget(
                    target_key=target_key,
                    horizon=horizon,
                    target_type=target_type,
                    scope=scope,
                    min_observations=1,
                    method_requirements=requirements,
                    status="defined",
                    source_key="phase13_registry",
                    quality_status="UNVERIFIED",
                )
            )
            report["targets_written"] += 1

    tickers = [company_filter] if company_filter else list(COMPANY_TICKERS)
    report["hbl_pending"] = "HBL" not in tickers
    macro_lengths = _macro_series_lengths(session)

    for ticker in tickers:
        security = session.query(Security).filter(Security.ticker == ticker).first()
        if security is None:
            report["companies"].append({"ticker": ticker, "error": "security not found"})
            continue
        company = session.query(Company).filter(Company.id == security.company_id).first()
        lengths = _series_lengths(session, security)
        company_report = {
            "ticker": ticker,
            "security_id": security.id,
            "series_lengths": {
                k: v for k, v in lengths.items() if k not in ("latest_price", "income_period_ends")
            },
            "income_period_ends": lengths["income_period_ends"],
        }

        # --- Feature snapshots as of the price origin. ---
        snapshot_rows = []
        values = (
            session.query(FundamentalMetricValue, FundamentalMetricDefinition.metric_key)
            .join(
                FundamentalMetricDefinition,
                FundamentalMetricDefinition.id == FundamentalMetricValue.metric_definition_id,
            )
            .filter(
                FundamentalMetricValue.company_id == security.company_id,
                FundamentalMetricValue.value.isnot(None),
            )
            .all()
        )
        for value_row, metric_key in values:
            snapshot_rows.append(
                (
                    f"fundamental:{metric_key}",
                    value_row.value,
                    {
                        "source": "fundamental_metric_values",
                        "metric_definition_id": value_row.metric_definition_id,
                        "period_end": str(value_row.period_end),
                        "calculation_version": value_row.calculation_version,
                        "quality_status": value_row.quality_status,
                    },
                )
            )
        valuations = (
            session.query(Valuation)
            .filter(
                Valuation.security_id == security.id,
                Valuation.estimated_value.isnot(None),
            )
            .all()
        )
        for valuation in valuations:
            if (valuation.assumptions or {}).get("computation_status") != "computed":
                continue
            snapshot_rows.append(
                (
                    f"valuation:{valuation.method}",
                    valuation.estimated_value,
                    {
                        "source": "valuations",
                        "method": valuation.method,
                        "valuation_date": str(valuation.valuation_date),
                        "quality_status": valuation.quality_status,
                    },
                )
            )
        latest = lengths["latest_price"]
        if latest is not None:
            snapshot_rows.append(
                (
                    "price:close",
                    latest.close_price,
                    {
                        "source": "market_prices",
                        "trading_date": str(latest.trading_date),
                        "quality_status": latest.quality_status,
                    },
                )
            )
            snapshot_rows.append(
                (
                    "price:volume",
                    Decimal(latest.volume) if latest.volume is not None else None,
                    {
                        "source": "market_prices",
                        "trading_date": str(latest.trading_date),
                        "quality_status": latest.quality_status,
                    },
                )
            )
        for feature_key, feature_value, evidence in snapshot_rows:
            existing = (
                session.query(ForecastFeatureSnapshot)
                .filter(
                    ForecastFeatureSnapshot.security_id == security.id,
                    ForecastFeatureSnapshot.origin_date == PRICE_ORIGIN,
                    ForecastFeatureSnapshot.feature_key == feature_key,
                )
                .first()
            )
            if existing:
                report["snapshots_skipped"] += 1
                continue
            session.add(
                ForecastFeatureSnapshot(
                    security_id=security.id,
                    origin_date=PRICE_ORIGIN,
                    feature_key=feature_key,
                    feature_value=feature_value,
                    evidence=evidence,
                    source_key="phase13_feature_store",
                    quality_status="UNVERIFIED",
                )
            )
            report["snapshots_written"] += 1
        company_report["snapshots"] = len(snapshot_rows)

        # --- Assessments: 6 targets x 6 horizons per company. ---
        for target_key in COMPANY_TARGETS:
            series_length = lengths[target_key]
            for horizon in HORIZONS:
                result = assess(target_key, horizon, series_length)
                existing = (
                    session.query(ForecastAssessment)
                    .filter(
                        ForecastAssessment.security_id == security.id,
                        ForecastAssessment.target_key == target_key,
                        ForecastAssessment.horizon == horizon,
                        ForecastAssessment.origin_date == PRICE_ORIGIN,
                    )
                    .first()
                )
                if existing:
                    report["assessments_skipped"] += 1
                    continue
                session.add(
                    ForecastAssessment(
                        security_id=security.id,
                        target_key=target_key,
                        horizon=horizon,
                        origin_date=PRICE_ORIGIN,
                        method="baseline_suite",
                        computation_status=result["computation_status"],
                        point_estimate=None,
                        interval_low=None,
                        interval_high=None,
                        reason=result["reason"],
                        evidence={
                            "series_length": series_length,
                            "per_method": result["per_method"],
                            "baseline_comparison": "none_available",
                            "calibration_status": result["calibration_status"],
                            "inputs_as_of": {
                                "price_origin": str(PRICE_ORIGIN),
                                "income_period_ends": lengths["income_period_ends"],
                            },
                            "company_legal_name": company.legal_name if company else None,
                        },
                        source_key="phase13_assessment",
                        quality_status="UNVERIFIED",
                    )
                )
                report["assessments_written"] += 1
                if result["computation_status"] == "computed":
                    report["assessments_computed"] += 1
        report["companies"].append(company_report)

    # --- Macro snapshots + assessments (security NULL). ---
    # Snapshots cover ALL current macro observations (the full Phase 10
    # set), not just the two macro-target indicators: every observation
    # is a usable feature for later phases. Assessments cover only the
    # two macro targets in the registry.
    macro_indicators = (
        session.query(EconomicIndicator).filter(EconomicIndicator.is_current.is_(True)).all()
    )
    for indicator in macro_indicators:
        existing = (
            session.query(ForecastFeatureSnapshot)
            .filter(
                ForecastFeatureSnapshot.security_id.is_(None),
                ForecastFeatureSnapshot.origin_date == MACRO_ORIGIN,
                ForecastFeatureSnapshot.feature_key == f"macro:{indicator.indicator_code}",
            )
            .first()
        )
        if existing:
            report["snapshots_skipped"] += 1
            continue
        session.add(
            ForecastFeatureSnapshot(
                security_id=None,
                origin_date=MACRO_ORIGIN,
                feature_key=f"macro:{indicator.indicator_code}",
                feature_value=indicator.value,
                evidence={
                    "source": "economic_indicators",
                    "indicator_code": indicator.indicator_code,
                    "observation_date": str(indicator.observation_date),
                    "quality_status": indicator.quality_status,
                },
                source_key="phase13_feature_store",
                quality_status="UNVERIFIED",
            )
        )
        report["snapshots_written"] += 1
    for target_key, info in macro_lengths.items():
        for horizon in HORIZONS:
            result = assess(target_key, horizon, info["length"])
            existing = (
                session.query(ForecastAssessment)
                .filter(
                    ForecastAssessment.security_id.is_(None),
                    ForecastAssessment.target_key == target_key,
                    ForecastAssessment.horizon == horizon,
                    ForecastAssessment.origin_date == MACRO_ORIGIN,
                )
                .first()
            )
            if existing:
                report["assessments_skipped"] += 1
                continue
            session.add(
                ForecastAssessment(
                    security_id=None,
                    target_key=target_key,
                    horizon=horizon,
                    origin_date=MACRO_ORIGIN,
                    method="baseline_suite",
                    computation_status=result["computation_status"],
                    point_estimate=None,
                    interval_low=None,
                    interval_high=None,
                    reason=result["reason"],
                    evidence={
                        "series_length": info["length"],
                        "per_method": result["per_method"],
                        "baseline_comparison": "none_available",
                        "calibration_status": result["calibration_status"],
                        "inputs_as_of": {
                            "observation_dates": info["observation_dates"],
                        },
                    },
                    source_key="phase13_assessment",
                    quality_status="UNVERIFIED",
                )
            )
            report["assessments_written"] += 1
            if result["computation_status"] == "computed":
                report["assessments_computed"] += 1

    # Phase 3 forecasts table: intentionally untouched (0 rows).
    from app.models.analysis import Forecast

    report["phase3_forecasts_rows"] = session.query(Forecast).count()

    if commit:
        session.commit()
    else:
        session.rollback()
    return report
