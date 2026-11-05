"""Phase 27 source health: one snapshot per source category.

Freshness is judged per source against that source's own
threshold — a daily price feed and an annual statement feed do
not share a clock (same rule as the SLO definitions):

- market_prices: stale after 1 day (a trading weekday without a
  session is already a gap; collection is Terms-gated).
- registry: stale after 30 days (a snapshot, not a feed).
- statements: stale after 180 days (annual/interim clock).
- macro: stale after 45 days (monthly releases).
- news: stale after 30 days without a new event (seed-only feed).
- jobs / evaluation / reports / alerts: operational tables,
  stale after 7 days without a new run (they move only when an
  operator runs them).

A source with no rows at all is "unknown", never "fresh" and
never zero-filled. Coverage is reported beside freshness, never
merged into it: a source can be fresh and narrow (statements:
3 of 470 companies) and the snapshot must say both.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import distinct, func

from app.models.alerts import Alert
from app.models.analysis import EconomicIndicator
from app.models.evaluation import EvaluationRun
from app.models.financial import FinancialStatement
from app.models.jobs import JobRun
from app.models.market import MarketPrice
from app.models.reference import Company, Security
from app.models.registry import RegistryEvidence
from app.models.reports import Report

# source_key -> (category, stale_after_days)
_THRESHOLDS: dict[str, tuple[str, int]] = {
    "market_prices": ("market_prices", 1),
    "registry": ("registry", 30),
    "statements": ("statements", 180),
    "macro": ("macro", 45),
    "news": ("news", 30),
    "jobs": ("jobs", 7),
    "evaluation": ("evaluation", 7),
    "reports": ("reports", 7),
    "alerts": ("alerts", 7),
}


def source_health(session, run_date: date) -> list[dict]:
    """Compute one health snapshot per source. Pure reads, no writes."""
    company_count = session.query(func.count(Company.id)).scalar() or 0
    security_count = session.query(func.count(Security.id)).scalar() or 0
    out: list[dict] = []

    def emit(source_key, latest, num, den, notes):  # type: ignore[no-untyped-def]
        category, threshold = _THRESHOLDS[source_key]
        if latest is None:
            status = "unknown"
            freshness = None
        else:
            freshness = (run_date - latest).days
            status = "fresh" if freshness <= threshold else "stale"
        out.append(
            {
                "source_key": source_key,
                "category": category,
                "latest_observation_date": latest,
                "coverage_numerator": num,
                "coverage_denominator": den,
                "freshness_days": freshness,
                "status": status,
                "notes": notes,
            }
        )

    latest_price = session.query(func.max(MarketPrice.trading_date)).scalar()
    priced = (
        session.query(func.count(distinct(MarketPrice.security_id)))
        .filter(MarketPrice.trading_date == latest_price)
        .scalar()
        if latest_price is not None
        else 0
    ) or 0
    emit(
        "market_prices",
        latest_price,
        priced,
        security_count,
        (
            "Latest stored trading date; later weekdays have no "
            "session (collection Terms-gated, not a holiday claim)."
        ),
    )

    latest_evidence = session.query(func.max(RegistryEvidence.collected_at)).scalar()
    evidence_companies = (
        session.query(func.count(distinct(RegistryEvidence.entity_id)))
        .filter(RegistryEvidence.entity_type == "company")
        .scalar()
        or 0
    )
    emit(
        "registry",
        latest_evidence.date() if latest_evidence is not None else None,
        evidence_companies,
        company_count,
        "DPS snapshot plus SECP LEAP sampled verification (61 companies).",
    )

    latest_period_end = session.query(func.max(FinancialStatement.period_end)).scalar()
    statement_companies = (
        session.query(func.count(distinct(FinancialStatement.company_id))).scalar() or 0
    )
    emit(
        "statements",
        latest_period_end,
        statement_companies,
        company_count,
        "3-company sample only; HBL pending (browser download running).",
    )

    latest_macro = session.query(func.max(EconomicIndicator.observation_date)).scalar()
    macro_count = session.query(func.count(EconomicIndicator.id)).scalar() or 0
    emit(
        "macro",
        latest_macro,
        macro_count,
        None,
        "SBP/PBS official reads; 6 VERIFIED by cross-publisher agreement, 6 UNVERIFIED.",
    )

    from app.models.news_events import NewsEvent

    # Latest OBSERVED event only: scheduled future events (SBP
    # meeting 2026-12-14) are not observations, and using them
    # would report a negative freshness. They are noted, not dated.
    latest_event = (
        session.query(func.max(NewsEvent.event_date))
        .filter(NewsEvent.event_date <= run_date)
        .scalar()
    )
    scheduled_future = (
        session.query(func.count(NewsEvent.id))
        .filter(NewsEvent.event_date > run_date)
        .scalar()
        or 0
    )
    event_companies = (
        session.query(func.count(distinct(NewsEvent.primary_company_id)))
        .filter(NewsEvent.primary_company_id.isnot(None))
        .scalar()
        or 0
    )
    emit(
        "news",
        latest_event,
        event_companies,
        company_count,
        f"Seed events from stored rows only; live collection Terms-gated; "
        f"{scheduled_future} scheduled future event(s) excluded from freshness.",
    )

    latest_job = session.query(func.max(JobRun.created_at)).scalar()
    job_count = session.query(func.count(JobRun.id)).scalar() or 0
    emit(
        "jobs",
        latest_job.date() if latest_job is not None else None,
        job_count,
        None,
        "DB-backed job framework; 3 collection jobs paused (Terms gate).",
    )

    latest_eval = session.query(func.max(EvaluationRun.created_at)).scalar()
    eval_count = session.query(func.count(EvaluationRun.id)).scalar() or 0
    emit(
        "evaluation",
        latest_eval.date() if latest_eval is not None else None,
        eval_count,
        None,
        "All model cards NOT_PROMOTED; all promotion gates NOT_MET.",
    )

    latest_report = session.query(func.max(Report.report_date)).scalar()
    report_count = session.query(func.count(Report.id)).scalar() or 0
    emit(
        "reports",
        latest_report,
        report_count,
        None,
        "All reports DRAFT; no publish step exists.",
    )

    latest_alert = session.query(func.max(Alert.as_of_date)).scalar()
    alert_count = session.query(func.count(Alert.id)).scalar() or 0
    emit(
        "alerts",
        latest_alert,
        alert_count,
        None,
        "In-app delivery only; external consent False.",
    )

    return out
