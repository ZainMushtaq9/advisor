"""Phase 15 decision engine runner.

Reads only already-stored rows (Phase 7 statements, Phase 8
health/warnings, Phase 9 valuations, Phase 10 macro regime,
Phase 11 news events, Phase 12 breadth, Phase 13 assessments,
Phase 14 risk flags and liquidity tiers, Phase 6 coverage) and
writes Phase 15 rows idempotently. No HTTP fetch, no DPS download,
no PSX financials portal use, no forecast generation, and no
execution of any kind. Dry-run is the default; --commit writes,
and a second --commit writes 0 new rows.

Analysis date 2026-11-04; price reference date 2026-11-03.
Forecasts contribute no evidence in rules v1: Phase 13 abstained
on all 120 assessments, so the forecast block in every snapshot
records abstention, never a number. Technical evidence is absent
for every company (Phase 6: 0 calculable values).

Conflicts are derived by generic rules from stored rows, not
hand-written per company:
  profitability_vs_earnings_quality: profitability >= 70 while
    earnings_quality < 40 (the high margin rests on earnings the
    quality score does not support — HUBC's associate profit).
  cheap_vs_cash_quality: valuation +1 while a cash-conversion or
    receivables warning exists.
  profitability_vs_receivables: profitability >= 70 while a
    receivables-days-over-one-year warning exists.
  profitability_without_growth: profitability >= 70 while
    growth is 0.
  fundamentals_vs_macro_headwind: fundamentals +1 while the
    macro regime is tightening.
These are preserved as unresolved disagreements; precedence
selects evidence, it never overrides a score.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.analysis import FinancialHealthAssessment, FundamentalWarningEvent, Valuation
from app.models.decision import Decision, DecisionOutcome, DecisionRule
from app.models.financial import FinancialStatement
from app.models.forecasting import ForecastAssessment
from app.models.macro import MacroRegime
from app.models.news_events import NewsEvent
from app.models.reference import Company, Security
from app.models.risk import RiskFlag, RiskMetricValue
from app.services.decision_engine import (
    CONFIDENCE_RULES_V1,
    DECISION_DATE,
    DIMENSION_RULES,
    GATES_V1,
    N_DIMENSIONS,
    PRECEDENCE_V1,
    PRICE_DATE,
    RULES_VERSION,
    STALE_DAYS,
    THRESHOLDS_V1,
    UNIVERSE_TICKERS,
    WEIGHTS_V1,
)
from app.services.decision_engine.scoring import (
    ABSENT,
    aggregate,
    agreement,
    completeness,
    confidence,
    fundamentals_score,
    liquidity_score,
    macro_score,
    map_conclusion,
    news_score,
    risk_score,
    user_facing,
    valuation_score,
)

DECISION_D = date.fromisoformat(DECISION_DATE)

RULE_ROW = {
    "version": RULES_VERSION,
    "dimensions": DIMENSION_RULES,
    "weights": WEIGHTS_V1,
    "thresholds": THRESHOLDS_V1,
    "gates": GATES_V1,
    "precedence": PRECEDENCE_V1,
    "confidence_rules": CONFIDENCE_RULES_V1,
}


def _dec(value) -> str | None:
    return None if value is None else str(value)


def _conflicts(
    health: dict[str, Decimal | None],
    fund_score: int | None,
    val_score: int | None,
    warning_types: list[str],
    regime_label: str | None,
) -> list[dict]:
    conflicts = []
    profitability = health.get("profitability")
    earnings_quality = health.get("earnings_quality")
    growth = health.get("growth")
    if (
        profitability is not None
        and earnings_quality is not None
        and profitability >= 70
        and earnings_quality < 40
    ):
        conflicts.append(
            {
                "type": "profitability_vs_earnings_quality",
                "for": f"profitability {profitability}",
                "against": f"earnings_quality {earnings_quality}",
                "resolution": "unresolved",
            }
        )
    if val_score == 1 and any(
        w in ("low_cash_conversion", "receivables_growing_faster_than_revenue")
        for w in warning_types
    ):
        conflicts.append(
            {
                "type": "cheap_vs_cash_quality",
                "for": "trailing P/E below 10",
                "against": "cash-conversion or receivables warning present",
                "resolution": "unresolved",
            }
        )
    if (
        profitability is not None
        and profitability >= 70
        and ("receivables_days_over_one_year" in warning_types)
    ):
        conflicts.append(
            {
                "type": "profitability_vs_receivables",
                "for": f"profitability {profitability}",
                "against": "receivables days over one year",
                "resolution": "unresolved",
            }
        )
    if profitability is not None and profitability >= 70 and growth is not None and growth == 0:
        conflicts.append(
            {
                "type": "profitability_without_growth",
                "for": f"profitability {profitability}",
                "against": "growth score 0",
                "resolution": "unresolved",
            }
        )
    if fund_score == 1 and regime_label == "tightening":
        conflicts.append(
            {
                "type": "fundamentals_vs_macro_headwind",
                "for": "fundamentals +1",
                "against": "macro regime tightening",
                "resolution": "unresolved",
            }
        )
    return conflicts


def _company_decision(session: Session, ticker: str) -> dict:
    """Build (not yet write) one company's decision record."""
    security = session.query(Security).filter(Security.ticker == ticker).one_or_none()
    company = None
    if security is not None:
        company = session.query(Company).filter(Company.id == security.company_id).one_or_none()
    if company is None:
        company = session.query(Company).filter(Company.legal_name.ilike(f"%{ticker}%")).first()

    # --- Gather stored evidence (no look-ahead: nothing here is
    # dated after DECISION_DATE; the runner verifies this below).
    statements = []
    if company is not None:
        statements = (
            session.query(FinancialStatement)
            .filter(FinancialStatement.company_id == company.id)
            .order_by(FinancialStatement.period_end.desc())
            .all()
        )
    latest_period_end = statements[0].period_end if statements else None
    latest_publication = None
    if statements:
        pubs = {s.publication_date for s in statements if s.period_end == latest_period_end}
        latest_publication = sorted(pubs)[0] if pubs else None
        if len(pubs) > 1:
            latest_publication = None
    statement_age_days = (DECISION_D - latest_period_end).days if latest_period_end else None

    health: dict[str, Decimal | None] = {}
    health_rows: dict[str, int] = {}
    if company is not None:
        for row in (
            session.query(FinancialHealthAssessment)
            .filter(FinancialHealthAssessment.company_id == company.id)
            .filter(FinancialHealthAssessment.score.isnot(None))
            .all()
        ):
            health[row.category] = row.score
            health_rows[row.category] = row.id

    valuations: dict[str, dict] = {}
    pe_trailing: Decimal | None = None
    if security is not None:
        for row in session.query(Valuation).filter(Valuation.security_id == security.id).all():
            status = (row.assumptions or {}).get("computation_status")
            valuations[row.method] = {
                "row_id": row.id,
                "value": _dec(row.estimated_value),
                "status": status,
            }
            if row.method == "multiples:pe_trailing" and status == "computed":
                pe_trailing = row.estimated_value

    warning_types: list[str] = []
    warning_rows: list[dict] = []
    if company is not None:
        for row in (
            session.query(FundamentalWarningEvent)
            .filter(FundamentalWarningEvent.company_id == company.id)
            .all()
        ):
            warning_types.append(row.warning_type)
            warning_rows.append(
                {"row_id": row.id, "type": row.warning_type, "severity": row.severity}
            )

    risk_flag_rows: list[dict] = []
    has_warning_flag = False
    if company is not None:
        for row in session.query(RiskFlag).filter(RiskFlag.company_id == company.id).all():
            risk_flag_rows.append(
                {"row_id": row.id, "type": row.flag_type, "severity": row.severity}
            )
            if row.severity == "warning":
                has_warning_flag = True

    tier: str | None = None
    if security is not None:
        tier_row = (
            session.query(RiskMetricValue)
            .filter(RiskMetricValue.security_id == security.id)
            .filter(RiskMetricValue.metric_key == "volume_liquidity_tier")
            .filter(RiskMetricValue.computation_status == "computed")
            .one_or_none()
        )
        if tier_row is not None:
            tier = (tier_row.evidence or {}).get("tier")

    news_row = None
    if company is not None:
        news_row = (
            session.query(NewsEvent)
            .filter(NewsEvent.primary_company_id == company.id)
            .filter(NewsEvent.event_type == "earnings")
            .order_by(NewsEvent.event_date.desc().nullslast())
            .first()
        )

    regime = session.query(MacroRegime).order_by(MacroRegime.observation_date.desc()).first()
    regime_label = regime.regime_label if regime is not None else None

    tech_row = (
        session.query(RiskMetricValue)
        .filter(RiskMetricValue.metric_key == "technical_coverage_rate")
        .filter(RiskMetricValue.scope_key == "MARKET")
        .one_or_none()
    )
    tech_coverage = (
        str(tech_row.value) if tech_row is not None and tech_row.value is not None else "0"
    )

    forecast_total = session.query(ForecastAssessment).count()
    forecast_computed = (
        session.query(ForecastAssessment)
        .filter(ForecastAssessment.computation_status == "computed")
        .count()
    )

    # --- Gates (evaluated before any conclusion).
    gate_reasons: list[str] = []
    if not statements:
        gate_reasons.append("no_statements")
    if statement_age_days is not None and statement_age_days > STALE_DAYS:
        gate_reasons.append("stale_latest_statement")
    if statements and latest_publication is None:
        gate_reasons.append("publication_date_unknown")
    if security is not None and statements:
        for row in session.query(Valuation).filter(Valuation.security_id == security.id).all():
            if (row.assumptions or {}).get("computation_status") != "computed":
                continue
            for statement_id in row.input_statement_ids or []:
                stmt = (
                    session.query(FinancialStatement)
                    .filter(FinancialStatement.id == statement_id)
                    .one_or_none()
                )
                if stmt is not None and stmt.publication_date is None:
                    if "valuation_publication_unknown" not in gate_reasons:
                        gate_reasons.append("valuation_publication_unknown")
                    break

    # --- Dimension scores (computed inputs only; ABSENT excluded).
    scores = {
        "fundamentals": fundamentals_score(
            health.get("profitability"),
            health.get("solvency"),
            "negative_profit_after_tax" in warning_types,
        ),
        "valuation": valuation_score(pe_trailing),
        "technical": ABSENT,
        "news_event": news_score(news_row is not None and news_row.date_status == "known")
        if news_row is not None
        else ABSENT,
        "macro": macro_score(regime_label),
        "liquidity": liquidity_score(tier),
        "risk": risk_score(has_warning_flag),
    }
    total, scored = aggregate(scores)
    if scored < 3 and "too_few_dimensions" not in gate_reasons:
        gate_reasons.append("too_few_dimensions")

    # --- Screening, conclusion, confidence, user-facing value.
    if not statements:
        screening = "SCREEN_NOT_RUNNABLE"
    elif "stale_latest_statement" in gate_reasons or "publication_date_unknown" in gate_reasons:
        screening = "SCREEN_FAIL"
    else:
        screening = "SCREEN_PASS"
    conclusion = map_conclusion(scores, gate_reasons)
    completeness_value = completeness(scored, N_DIMENSIONS)
    agreement_value = agreement(scores, conclusion)
    inputs_quality = "UNVERIFIED"
    calibration_established = False
    conflicts = (
        []
        if conclusion == "INSUFFICIENT_EVIDENCE"
        else _conflicts(
            health,
            scores["fundamentals"],
            scores["valuation"],
            warning_types,
            regime_label,
        )
    )
    confidence_value = confidence(
        conclusion,
        completeness_value,
        agreement_value,
        inputs_quality,
        calibration_established,
        len(conflicts),
    )
    facing, facing_reason = user_facing(conclusion, confidence_value)

    # --- No-look-ahead verification: every dated evidence item
    # must be on or before the decision date.
    look_ahead_violations = []
    if latest_publication is not None and latest_publication > DECISION_D:
        look_ahead_violations.append("statement publication after decision date")
    if (
        news_row is not None
        and news_row.event_date is not None
        and news_row.event_date > DECISION_D
    ):
        look_ahead_violations.append("news event after decision date")
    if regime is not None and regime.observation_date > DECISION_D:
        look_ahead_violations.append("regime observation after decision date")
    assert not look_ahead_violations, f"Look-ahead violation for {ticker}: {look_ahead_violations}"

    snapshot = {
        "decision_date": DECISION_DATE,
        "price_date": PRICE_DATE,
        "rules_version": RULES_VERSION,
        "company_id": company.id if company is not None else None,
        "security_id": security.id if security is not None else None,
        "latest_period_end": str(latest_period_end) if latest_period_end else None,
        "latest_publication_date": str(latest_publication) if latest_publication else None,
        "statement_age_days": statement_age_days,
        "health": {k: {"score": _dec(v), "row_id": health_rows[k]} for k, v in health.items()},
        "valuations": valuations,
        "pe_trailing": _dec(pe_trailing),
        "warnings": warning_rows,
        "risk_flags": risk_flag_rows,
        "liquidity_tier": tier,
        "news_event": (
            {
                "row_id": news_row.id,
                "event_date": str(news_row.event_date) if news_row.event_date else None,
                "date_status": news_row.date_status,
            }
            if news_row is not None
            else None
        ),
        "macro_regime": (
            {
                "row_id": regime.id,
                "label": regime.regime_label,
                "observation_date": str(regime.observation_date),
            }
            if regime is not None
            else None
        ),
        "technical_coverage": tech_coverage,
        "forecast_evidence": {
            "status": "abstained",
            "assessments_total": forecast_total,
            "computed": forecast_computed,
            "note": (
                "Phase 13 abstained on every assessment: no series "
                "meets any method's interval minimum. Forecasts "
                "contribute no evidence to this decision."
            ),
        },
        "inputs_quality": inputs_quality,
        "calibration": "NOT_ESTABLISHED",
        "dimension_scores": {k: v for k, v in scores.items()},
        "dimension_evidence": {
            "fundamentals": "health scores + negative-PAT warning check",
            "valuation": "computed trailing P/E only",
            "technical": "ABSENT: 0 calculable technical values",
            "news_event": "earnings event, informational only",
            "macro": "regime-v1 label",
            "liquidity": "Phase 14 volume liquidity tier",
            "risk": "warning-severity risk flags",
        },
    }

    return {
        "ticker": ticker,
        "company_id": company.id if company is not None else None,
        "security_id": security.id if security is not None else None,
        "screening_outcome": screening,
        "research_conclusion": conclusion,
        "user_facing": facing,
        "user_facing_reason": facing_reason,
        "confidence": confidence_value,
        "total_score": total,
        "scored_dimensions": scored,
        "completeness": str(completeness_value),
        "agreement": str(agreement_value) if agreement_value is not None else None,
        "evidence_snapshot": snapshot,
        "conflicts": conflicts,
        "gate_reasons": gate_reasons,
    }


def run_decisions(
    session: Session, commit: bool = False, company_filter: str | None = None
) -> dict:
    """Build decisions for the universe; write only with --commit."""
    tickers = [company_filter] if company_filter else list(UNIVERSE_TICKERS)
    built = [_company_decision(session, ticker) for ticker in tickers]

    rules_written = 0
    rules_skipped = 0
    existing_rule = (
        session.query(DecisionRule).filter(DecisionRule.version == RULES_VERSION).one_or_none()
    )
    if existing_rule is None:
        if commit:
            session.add(DecisionRule(**RULE_ROW))
        rules_written = 1
    else:
        rules_skipped = 1

    written = 0
    skipped = 0
    for item in built:
        existing = (
            session.query(Decision)
            .filter(Decision.company_id == item["company_id"])
            .filter(Decision.decision_date == DECISION_D)
            .filter(Decision.rules_version == RULES_VERSION)
            .one_or_none()
        )
        if existing is not None:
            skipped += 1
            continue
        if commit:
            session.add(
                Decision(
                    company_id=item["company_id"],
                    security_id=item["security_id"],
                    decision_date=DECISION_D,
                    rules_version=RULES_VERSION,
                    screening_outcome=item["screening_outcome"],
                    research_conclusion=item["research_conclusion"],
                    user_facing=item["user_facing"],
                    confidence=item["confidence"],
                    total_score=item["total_score"],
                    scored_dimensions=item["scored_dimensions"],
                    completeness=Decimal(item["completeness"]),
                    evidence_snapshot=item["evidence_snapshot"],
                    conflicts={"conflicts": item["conflicts"]},
                    gate_reasons={"gates": item["gate_reasons"]},
                    quality_status="UNVERIFIED",
                )
            )
        written += 1

    outcomes = session.query(DecisionOutcome).count()
    return {
        "rules_written": rules_written,
        "rules_skipped": rules_skipped,
        "decisions_written": written,
        "decisions_skipped": skipped,
        "decisions": [
            {
                "ticker": item["ticker"],
                "screening": item["screening_outcome"],
                "conclusion": item["research_conclusion"],
                "user_facing": item["user_facing"],
                "user_facing_reason": item["user_facing_reason"],
                "confidence": item["confidence"],
                "total_score": item["total_score"],
                "scored_dimensions": item["scored_dimensions"],
                "completeness": item["completeness"],
                "agreement": item["agreement"],
                "gates": item["gate_reasons"],
                "conflicts": len(item["conflicts"]),
            }
            for item in built
        ],
        "outcomes_existing": outcomes,
    }
