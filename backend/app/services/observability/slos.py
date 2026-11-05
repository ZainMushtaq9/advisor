"""Phase 27 data-quality SLOs: definitions per source category and
their measurement against stored rows.

Brief requirement: "Define measurable freshness and completeness
targets by source category, not one universal threshold." Every
SLO below therefore carries its own target and its own rationale
— a price-feed SLO and a statement SLO do not share a threshold,
because a daily price feed and an annual report do not go stale
on the same clock.

Measurement discipline (same as Phases 13/26): a value is a
Decimal or None. None means not_evaluable, never zero. An unmet
SLO is a stored fact with its exact reason, never averaged away.
Company identity is resolved by ticker everywhere (surrogate
ids shift across fresh imports — see Phase 23 repair).

Trading weekdays are Monday–Friday (Phase 25 job calendar).
No holiday calendar is claimed: a weekday with no session is
reported as a missing session, not assumed a holiday.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import distinct, func

from app.models.alerts import Alert, AlertDelivery
from app.models.evaluation import GoldenTestResult
from app.models.financial import FinancialStatement
from app.models.jobs import JobRun
from app.models.market import MarketPrice
from app.models.news_events import NewsEvent
from app.models.reference import Company, Security
from app.models.registry import RegistryEvidence
from app.models.reports import Report
from app.services.data_quality import validate_ohlc
from app.services.jobs.registry import EXPECTED_COUNTS
from app.services.market_data.validation import karachi_today

# One entry per SLO: key, category, metric, target, comparison,
# unit, rationale. Targets are deliberate, not aspirational:
# price coverage 0.95 (not 1.0) because 26 tickers had no usable
# 2026-11-03 quote in the recorded source; news coverage 0.10
# because the seed is 3 companies by design, not a universe feed.
SLO_DEFINITIONS: list[dict] = [
    {
        "slo_key": "registry_evidence_coverage",
        "category": "registry",
        "metric_key": "companies_with_evidence_ratio",
        "target_value": Decimal("1"),
        "comparison": "ge",
        "unit": "ratio",
        "rationale": (
            "Every registry company must carry at least one evidence "
            "row; a company with none is unaccounted for, not merely "
            "unverified."
        ),
    },
    {
        "slo_key": "price_coverage_latest_day",
        "category": "market_prices",
        "metric_key": "priced_securities_ratio",
        "target_value": Decimal("0.95"),
        "comparison": "ge",
        "unit": "ratio",
        "rationale": (
            "On the latest price date, at least 95% of registry "
            "securities should carry a quote. The recorded 2026-11-03 "
            "source left 26 tickers without a usable quote, so 1.0 "
            "would be a false target."
        ),
    },
    {
        "slo_key": "price_session_gap_weekdays",
        "category": "market_prices",
        "metric_key": "missing_trading_weekdays_since_latest_price",
        "target_value": Decimal("0"),
        "comparison": "le",
        "unit": "count",
        "rationale": (
            "No trading weekday between the latest stored price date "
            "and today may lack a session. A gap is a missing "
            "session, never an assumed holiday (no holiday calendar "
            "is claimed)."
        ),
    },
    {
        "slo_key": "previous_close_completeness",
        "category": "market_prices",
        "metric_key": "non_null_previous_close_ratio",
        "target_value": Decimal("1"),
        "comparison": "ge",
        "unit": "ratio",
        "rationale": (
            "Every stored price row should carry its previous close: "
            "without it, daily returns are not calculable at all "
            "(Phase 6 daily_return is missing_data on all 470)."
        ),
    },
    {
        "slo_key": "ohlc_validity_rate",
        "category": "market_prices",
        "metric_key": "stored_prices_passing_ohlc_validity_ratio",
        "target_value": Decimal("1"),
        "comparison": "ge",
        "unit": "ratio",
        "rationale": (
            "Stored prices must all pass OHLC validity (high >= "
            "max(open, close), low <= min(open, close), no negatives). "
            "Ingest rejects invalid rows, so stored rows should be "
            "clean; this SLO proves it rather than assuming it."
        ),
    },
    {
        "slo_key": "duplicate_ticker_rate",
        "category": "registry",
        "metric_key": "securities_beyond_first_per_ticker_ratio",
        "target_value": Decimal("0"),
        "comparison": "le",
        "unit": "ratio",
        "rationale": (
            "One ticker must map to one security. A duplicate ticker "
            "breaks every ticker-keyed resolution in the system."
        ),
    },
    {
        "slo_key": "statement_document_lineage",
        "category": "statements",
        "metric_key": "statements_with_document_ratio",
        "target_value": Decimal("1"),
        "comparison": "ge",
        "unit": "ratio",
        "rationale": (
            "Every statement must trace to its source document: "
            "lineage coverage below 1.0 means figures that cannot "
            "be traced to a page."
        ),
    },
    {
        "slo_key": "statement_freshness_days",
        "category": "statements",
        "metric_key": "days_since_latest_statement_period_end",
        "target_value": Decimal("180"),
        "comparison": "le",
        "unit": "days",
        "rationale": (
            "Annual and interim reports arrive on a months-long "
            "clock, so the freshness target is 180 days, not a "
            "price-feed target. Staleness of any single company "
            "(NML, latest period end 2025-03-31) is flagged "
            "separately by Phase 14, not hidden by this maximum."
        ),
    },
    {
        "slo_key": "news_company_coverage",
        "category": "news",
        "metric_key": "companies_with_events_ratio",
        "target_value": Decimal("0.10"),
        "comparison": "ge",
        "unit": "ratio",
        "rationale": (
            "News coverage is seeded from stored rows for 3 of 470 "
            "companies by design; the target is 10%, an honest "
            "near-term bar, not a claim of universe coverage."
        ),
    },
    {
        "slo_key": "reports_published_externally",
        "category": "reports",
        "metric_key": "reports_published_externally_count",
        "target_value": Decimal("0"),
        "comparison": "le",
        "unit": "count",
        "rationale": (
            "Phase 22 has no publish step, so externally published "
            "reports must be exactly zero. Any other value is a "
            "control failure, not a metric to celebrate."
        ),
    },
    {
        "slo_key": "alert_delivery_rate",
        "category": "alerts",
        "metric_key": "delivered_deliveries_per_alert_ratio",
        "target_value": Decimal("1"),
        "comparison": "ge",
        "unit": "ratio",
        "rationale": (
            "Every alert must have a delivered in-app delivery; "
            "external channels are disabled by consent, so the "
            "denominator is alerts, not attempted sends."
        ),
    },
    {
        "slo_key": "job_success_rate",
        "category": "jobs",
        "metric_key": "succeeded_runs_per_terminal_run_ratio",
        "target_value": Decimal("0.95"),
        "comparison": "ge",
        "unit": "ratio",
        "rationale": (
            "Terminal job runs (succeeded/dead/cancelled) should be "
            "at least 95% succeeded. Queued/running/blocked runs "
            "are not terminal and are excluded, never counted as "
            "failures or successes."
        ),
    },
    {
        "slo_key": "golden_pass_rate",
        "category": "evaluation",
        "metric_key": "golden_cases_passed_ratio_latest_run",
        "target_value": Decimal("1"),
        "comparison": "ge",
        "unit": "ratio",
        "rationale": (
            "The golden suite must pass in full on the latest "
            "evaluation run; a single failure is a regression, "
            "not a rounding error."
        ),
    },
    {
        "slo_key": "drift_difference_count",
        "category": "evaluation",
        "metric_key": "live_counts_differing_from_phase24_baseline",
        "target_value": Decimal("0"),
        "comparison": "le",
        "unit": "count",
        "rationale": (
            "Live business counts must match the Phase 24 baseline "
            "in the Phase 25 job registry. A difference is a "
            "finding to explain, never auto-fixed (Phase 26 drift "
            "policy). New phase tables are not baseline rows, so "
            "they are reported separately, not counted as drift."
        ),
    },
]


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return Decimal(numerator) / Decimal(denominator)


def measure_slos(session, run_date: date | None = None) -> list[dict]:
    """Measure every SLO against stored rows. Pure reads, no writes.

    Returns one dict per SLO: slo_key, value (Decimal or None),
    status (met / unmet / not_evaluable), reason, evidence.
    """
    today = run_date or karachi_today()
    out: list[dict] = []

    def emit(slo_key: str, value: Decimal | None, reason: str, evidence: dict) -> None:
        definition = next(d for d in SLO_DEFINITIONS if d["slo_key"] == slo_key)
        target = definition["target_value"]
        comparison = definition["comparison"]
        if value is None:
            status = "not_evaluable"
        elif comparison == "ge":
            status = "met" if value >= target else "unmet"
        elif comparison == "le":
            status = "met" if value <= target else "unmet"
        else:
            status = "met" if value == target else "unmet"
        out.append(
            {
                "slo_key": slo_key,
                "value": value,
                "status": status,
                "reason": reason,
                "evidence": evidence,
            }
        )

    company_count = session.query(func.count(Company.id)).scalar() or 0
    security_count = session.query(func.count(Security.id)).scalar() or 0
    # RegistryEvidence keys evidence by entity_type/entity_id, not
    # by a company_id column: company evidence is entity_type
    # 'company' with entity_id = the company id.
    evidence_companies = (
        session.query(func.count(distinct(RegistryEvidence.entity_id)))
        .filter(RegistryEvidence.entity_type == "company")
        .scalar()
        or 0
    )
    emit(
        "registry_evidence_coverage",
        _ratio(evidence_companies, company_count),
        f"{evidence_companies} of {company_count} companies carry evidence.",
        {"companies": company_count, "companies_with_evidence": evidence_companies},
    )

    latest_price_date = session.query(func.max(MarketPrice.trading_date)).scalar()
    if latest_price_date is None:
        emit(
            "price_coverage_latest_day",
            None,
            "No price rows exist, so latest-day coverage is not evaluable.",
            {},
        )
        emit(
            "price_session_gap_weekdays",
            None,
            "No price rows exist, so the session gap is not evaluable.",
            {},
        )
    else:
        priced = (
            session.query(func.count(distinct(MarketPrice.security_id)))
            .filter(MarketPrice.trading_date == latest_price_date)
            .scalar()
            or 0
        )
        emit(
            "price_coverage_latest_day",
            _ratio(priced, security_count),
            f"{priced} of {security_count} securities priced on {latest_price_date}.",
            {"latest_price_date": str(latest_price_date), "priced": priced},
        )
        # Weekdays after the latest price date are missing sessions
        # only if no price row exists for them; with a single price
        # date, every later weekday is a gap by that definition.
        stored_dates = {row[0] for row in session.query(MarketPrice.trading_date).distinct().all()}
        missing = 0
        day = latest_price_date + timedelta(days=1)
        while day <= today:
            if day.weekday() < 5 and day not in stored_dates:
                missing += 1
            day += timedelta(days=1)
        emit(
            "price_session_gap_weekdays",
            Decimal(missing),
            (
                f"{missing} trading weekday(s) after {latest_price_date} "
                f"have no stored session (collection Terms-gated)."
            ),
            {"latest_price_date": str(latest_price_date), "run_date": str(today)},
        )

    price_count = session.query(func.count(MarketPrice.id)).scalar() or 0
    prev_close_count = (
        session.query(func.count(MarketPrice.id))
        .filter(MarketPrice.previous_close.isnot(None))
        .scalar()
        or 0
    )
    emit(
        "previous_close_completeness",
        _ratio(prev_close_count, price_count),
        f"{prev_close_count} of {price_count} price rows carry previous_close.",
        {"price_rows": price_count, "with_previous_close": prev_close_count},
    )

    prices = session.query(
        MarketPrice.open_price,
        MarketPrice.high_price,
        MarketPrice.low_price,
        MarketPrice.close_price,
    ).all()
    valid = sum(1 for (o, h, low, c) in prices if validate_ohlc(o, h, low, c) == [])
    emit(
        "ohlc_validity_rate",
        _ratio(valid, len(prices)),
        f"{valid} of {len(prices)} stored price rows pass OHLC validity.",
        {"price_rows": len(prices), "valid": valid},
    )

    tickers = [row[0] for row in session.query(Security.ticker).all()]
    duplicates = len(tickers) - len(set(tickers))
    emit(
        "duplicate_ticker_rate",
        _ratio(duplicates, len(tickers)),
        f"{duplicates} duplicate ticker assignment(s) across {len(tickers)} securities.",
        {"securities": len(tickers), "duplicates": duplicates},
    )

    statement_count = session.query(func.count(FinancialStatement.id)).scalar() or 0
    with_document = (
        session.query(func.count(FinancialStatement.id))
        .filter(FinancialStatement.document_id.isnot(None))
        .scalar()
        or 0
    )
    emit(
        "statement_document_lineage",
        _ratio(with_document, statement_count),
        f"{with_document} of {statement_count} statements trace to a document.",
        {"statements": statement_count, "with_document": with_document},
    )
    latest_period_end = session.query(func.max(FinancialStatement.period_end)).scalar()
    if latest_period_end is None:
        emit(
            "statement_freshness_days",
            None,
            "No statements exist, so statement freshness is not evaluable.",
            {},
        )
    else:
        freshness = (today - latest_period_end).days
        emit(
            "statement_freshness_days",
            Decimal(freshness),
            f"Latest statement period end {latest_period_end} is {freshness} day(s) old.",
            {"latest_period_end": str(latest_period_end)},
        )

    event_companies = (
        session.query(func.count(distinct(NewsEvent.primary_company_id)))
        .filter(NewsEvent.primary_company_id.isnot(None))
        .scalar()
        or 0
    )
    emit(
        "news_company_coverage",
        _ratio(event_companies, company_count),
        f"{event_companies} of {company_count} companies carry news events.",
        {"companies": company_count, "companies_with_events": event_companies},
    )

    published = (
        session.query(func.count(Report.id)).filter(Report.published_externally.is_(True)).scalar()
        if hasattr(Report, "published_externally")
        else None
    )
    if published is None:
        # Reports carry no publication flag in this schema version:
        # Phase 22 has no publish step, so the count is 0 by
        # construction, recorded with that reason, not assumed.
        emit(
            "reports_published_externally",
            Decimal(0),
            "No publish step exists (Phase 22), so externally published reports are 0.",
            {"publish_step": "none"},
        )
    else:
        emit(
            "reports_published_externally",
            Decimal(published),
            f"{published} report(s) externally published.",
            {"published": published},
        )

    alert_count = session.query(func.count(Alert.id)).scalar() or 0
    delivered = (
        session.query(func.count(AlertDelivery.id))
        .filter(AlertDelivery.outcome == "DELIVERED")
        .scalar()
        or 0
    )
    emit(
        "alert_delivery_rate",
        _ratio(delivered, alert_count),
        f"{delivered} delivered deliveries across {alert_count} alerts.",
        {"alerts": alert_count, "delivered": delivered},
    )

    terminal = (
        session.query(func.count(JobRun.id))
        .filter(JobRun.status.in_(("succeeded", "dead", "cancelled")))
        .scalar()
        or 0
    )
    succeeded = (
        session.query(func.count(JobRun.id)).filter(JobRun.status == "succeeded").scalar() or 0
    )
    emit(
        "job_success_rate",
        _ratio(succeeded, terminal),
        f"{succeeded} of {terminal} terminal job runs succeeded.",
        {"terminal_runs": terminal, "succeeded": succeeded},
    )

    latest_eval_run = (
        session.query(GoldenTestResult.run_id).order_by(GoldenTestResult.id.desc()).first()
    )
    if latest_eval_run is None:
        emit(
            "golden_pass_rate",
            None,
            "No golden results exist, so the golden pass rate is not evaluable.",
            {},
        )
    else:
        run_id = latest_eval_run[0]
        total = (
            session.query(func.count(GoldenTestResult.id))
            .filter(GoldenTestResult.run_id == run_id)
            .scalar()
            or 0
        )
        passed = (
            session.query(func.count(GoldenTestResult.id))
            .filter(GoldenTestResult.run_id == run_id, GoldenTestResult.passed.is_(True))
            .scalar()
            or 0
        )
        emit(
            "golden_pass_rate",
            _ratio(passed, total),
            f"{passed} of {total} golden cases passed on run {run_id}.",
            {"run_id": run_id, "passed": passed, "total": total},
        )

    differences = _drift_differences(session)
    emit(
        "drift_difference_count",
        Decimal(len(differences)),
        _drift_reason(differences),
        {"differences": differences},
    )

    return out


def _drift_reason(differences: list[dict]) -> str:
    """Display reason for the drift SLO, capped for VARCHAR(1000).

    The full expected/live pairs live in evidence (JSON, uncapped)
    and in the drift exception's evidence, so capping the display
    reason never hides a difference. (The HBL re-run batch grew
    the list past 1000 chars and the observability commit
    failed on StringDataRightTruncation.)
    """
    if not differences:
        return "Live business counts match the Phase 24 baseline."
    table_list = ", ".join(d["table"] for d in differences)
    reason = (
        f"{len(differences)} count(s) differ from baseline "
        f"({table_list}); full expected/live pairs in evidence."
    )
    if len(reason) > 990:
        reason = reason[:987] + "..."
    return reason


def _drift_differences(session) -> list[dict]:
    """Compare live counts against EXPECTED_COUNTS (Phase 25 baseline).

    Each entry names the table, expected and live counts. An empty
    list means no drift. New phase tables are not baseline rows:
    they are reported by the runner separately, never as drift.
    """
    from app.models.alerts import Alert, AlertDelivery
    from app.models.analysis import EconomicIndicator
    from app.models.backtesting import BacktestRun
    from app.models.decision import Decision
    from app.models.financial import (
        AuditorOpinion,
        FinancialDocument,
        FinancialStatement,
        FinancialStatementLineItem,
        TechnicalCalculationError,
        TechnicalCalculationRun,
    )
    from app.models.forecasting import ForecastAssessment
    from app.models.governance import DataSource
    from app.models.news_events import NewsEvent
    from app.models.orchestration import OrchestrationRun
    from app.models.ownership_actions import OwnershipHolding
    from app.models.portfolio import SimulatedPortfolio
    from app.models.rag import RagChunk
    from app.models.reference import Company, Security
    from app.models.registry import RegistryEvidence
    from app.models.reports import Report, ReportFigure
    from app.models.risk import RiskMetricValue
    from app.models.screener import ScreenResult

    table_models = {
        "companies": Company,
        "securities": Security,
        "registry_evidence": RegistryEvidence,
        "market_prices": MarketPrice,
        "financial_documents": FinancialDocument,
        "financial_statements": FinancialStatement,
        "financial_statement_line_items": FinancialStatementLineItem,
        "auditor_opinions": AuditorOpinion,
        "technical_calculation_runs": TechnicalCalculationRun,
        "technical_calculation_errors": TechnicalCalculationError,
        "technical_indicator_values": None,
        "fundamental_metric_values": None,
        "sector_metric_profiles": None,
        "valuations": None,
        "economic_indicators": EconomicIndicator,
        "news_events": NewsEvent,
        "ownership_holdings": OwnershipHolding,
        "forecast_assessments": ForecastAssessment,
        "risk_metric_values": RiskMetricValue,
        "decisions": Decision,
        "simulated_portfolios": SimulatedPortfolio,
        "backtest_runs": BacktestRun,
        "orchestration_runs": OrchestrationRun,
        "rag_chunks": RagChunk,
        "screen_results": ScreenResult,
        "alerts": Alert,
        "alert_deliveries": AlertDelivery,
        "reports": Report,
        "report_figures": ReportFigure,
        "data_sources": DataSource,
        "auth_users": None,
        "auth_tokens": None,
        "auth_audit_logs": None,
    }
    differences: list[dict] = []
    for table, expected in EXPECTED_COUNTS.items():
        model = table_models.get(table)
        if model is None:
            # Tables whose model lives elsewhere or whose count is
            # asserted by its owning phase's own check: count via
            # raw SQL on the fixed table name (internal, safe).
            from sqlalchemy import text as sql_text

            live = session.execute(sql_text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
        else:
            live = session.query(func.count(model.id)).scalar() or 0
        if live != expected:
            differences.append({"table": table, "expected": expected, "live": live})
    return differences
