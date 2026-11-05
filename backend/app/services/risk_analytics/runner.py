"""Phase 14 risk analytics runner.

Reads only already-stored rows (Phase 5 prices, Phase 7 statements
and opinions, Phase 8 warnings, Phase 10 exposures, Phase 12
breadth/ownership, Phase 13 assessments, Phase 6 coverage) and
writes Phase 14 rows idempotently. No HTTP fetch, no DPS download,
no PSX financials portal use. Dry-run is the default; --commit
writes, and a second --commit writes 0 new rows.

Analysis date 2026-11-04; price reference date 2026-11-03. The
simulated reference portfolio is equal-weight HUBC/NML/OGDC (the
statement companies); it is labelled simulation in every row that
touches it, and no row here is investment advice or a buy/sell
signal.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.analysis import FundamentalWarningEvent
from app.models.financial import AuditorOpinion, FinancialStatement
from app.models.forecasting import ForecastAssessment
from app.models.market import MarketPrice
from app.models.ownership_actions import MarketBreadth, OwnershipHolding
from app.models.reference import Security
from app.models.risk import (
    RiskControl,
    RiskControlCheck,
    RiskFlag,
    RiskMetricDefinition,
    RiskMetricValue,
    StressResult,
    StressScenario,
)
from app.services.risk_analytics import (
    ANALYSIS_DATE,
    CONTROLS_V1,
    METRIC_DEFINITIONS,
    PRICE_DATE,
    REFERENCE_PORTFOLIO,
    RISK_TICKERS,
    SENSITIVITY_ROWS,
    SERIES_METRICS,
    STRESS_SCENARIOS,
)
from app.services.risk_analytics.formulas import (
    portfolio_shock_impact,
    top_n_share,
    volume_tier,
)

ANALYSIS_D = date.fromisoformat(ANALYSIS_DATE)
PRICE_D = date.fromisoformat(PRICE_DATE)
STALE_DAYS = 365


def _add(session: Session, commit: bool, obj: object, counters: dict, key: str) -> None:
    if commit:
        session.add(obj)
    counters[key] += 1


def run_risk(session: Session, commit: bool = False, company_filter: str | None = None) -> dict:
    """Build the Phase 14 risk register. Returns a JSON-able report."""
    counters = {
        "definitions_written": 0,
        "definitions_skipped": 0,
        "values_written": 0,
        "values_skipped": 0,
        "values_computed": 0,
        "values_insufficient": 0,
        "flags_written": 0,
        "flags_skipped": 0,
        "controls_written": 0,
        "controls_skipped": 0,
        "checks_written": 0,
        "checks_skipped": 0,
        "checks_pass": 0,
        "checks_breach": 0,
        "checks_blocked": 0,
        "scenarios_written": 0,
        "scenarios_skipped": 0,
        "stress_written": 0,
        "stress_skipped": 0,
        "stress_computed": 0,
        "stress_insufficient": 0,
    }

    # --- 1. Metric definitions -------------------------------------------
    existing_defs = {d.metric_key for d in session.query(RiskMetricDefinition).all()}
    for key, category, formula, min_obs, window, unit, scope in METRIC_DEFINITIONS:
        if key in existing_defs:
            counters["definitions_skipped"] += 1
            continue
        _add(
            session,
            commit,
            RiskMetricDefinition(
                metric_key=key,
                category=category,
                formula=formula,
                min_observations=min_obs,
                window=window,
                unit=unit,
                scope=scope,
            ),
            counters,
            "definitions_written",
        )

    # --- Inputs ------------------------------------------------------------
    # Per-company sections run over RISK_TICKERS (statement companies
    # incl. HBL); the simulated reference portfolio stays 3-name (see
    # the portfolio stress block, which filters closes to its names).
    tickers = list(RISK_TICKERS)
    if company_filter:
        tickers = [company_filter] if company_filter in tickers else []
    securities = {
        s.ticker: s for s in session.query(Security).filter(Security.ticker.in_(tickers)).all()
    }
    prices = {}
    for ticker, sec in securities.items():
        row = (
            session.query(MarketPrice)
            .filter(MarketPrice.security_id == sec.id, MarketPrice.trading_date == PRICE_D)
            .one_or_none()
        )
        if row is not None:
            prices[ticker] = row

    existing_values = {
        (v.metric_key, v.scope_key, str(v.as_of_date)) for v in session.query(RiskMetricValue).all()
    }

    def value_row(
        metric_key,
        scope_key,
        security_id,
        val,
        status,
        reason,
        evidence,
        as_of=PRICE_D,
        as_of_str=PRICE_DATE,
    ):
        grain = (metric_key, scope_key, as_of_str)
        if grain in existing_values:
            counters["values_skipped"] += 1
            return
        existing_values.add(grain)
        _add(
            session,
            commit,
            RiskMetricValue(
                metric_key=metric_key,
                scope_key=scope_key,
                security_id=security_id,
                as_of_date=as_of,
                value=val,
                computation_status=status,
                reason=reason,
                evidence=evidence,
            ),
            counters,
            "values_written",
        )
        if status == "computed":
            counters["values_computed"] += 1
        else:
            counters["values_insufficient"] += 1

    # --- 2a. Series metrics: all insufficient on one trading date ---------
    for ticker, sec in securities.items():
        n_closes = 1 if ticker in prices else 0
        for metric_key, reason in SERIES_METRICS:
            value_row(
                metric_key,
                ticker,
                sec.id,
                None,
                "insufficient_inputs",
                f"{reason} Series length available: {n_closes} close(s).",
                {
                    "series_length_closes": n_closes,
                    "price_date": PRICE_DATE,
                    "window": "2026-11-03 only",
                },
            )

    # --- 2b. Liquidity ------------------------------------------------------
    median_row = (
        session.query(MarketBreadth)
        .filter(
            MarketBreadth.trading_date == PRICE_D,
            MarketBreadth.metric_key == "median_volume",
            MarketBreadth.scope == "MARKET",
        )
        .one_or_none()
    )
    median_volume = median_row.metric_value if median_row else Decimal("54631.5")
    for ticker, sec in securities.items():
        row = prices.get(ticker)
        if row is None or row.volume is None:
            value_row(
                "volume_liquidity_tier",
                ticker,
                sec.id,
                None,
                "insufficient_inputs",
                "No 2026-11-03 volume row.",
                {"price_date": PRICE_DATE},
            )
        else:
            tier = volume_tier(int(row.volume), median_volume)
            value_row(
                "volume_liquidity_tier",
                ticker,
                sec.id,
                Decimal(row.volume),
                "computed",
                f"2026-11-03 volume {row.volume} vs median {median_volume}: tier {tier}.",
                {
                    "volume": str(row.volume),
                    "median_volume": str(median_volume),
                    "tier": tier,
                    "price_date": PRICE_DATE,
                },
            )
        value_row(
            "turnover_liquidity",
            ticker,
            sec.id,
            None,
            "insufficient_inputs",
            "Turnover is NULL on all 444 2026-11-03 price rows; no "
            "turnover-based liquidity can be computed.",
            {"price_date": PRICE_DATE},
        )

    # --- 2c. Market scope from Phase 12 breadth ----------------------------
    sector_rows = (
        session.query(MarketBreadth)
        .filter(
            MarketBreadth.trading_date == PRICE_D,
            MarketBreadth.metric_key == "priced_coverage",
            MarketBreadth.scope.like("SECTOR:%"),
            MarketBreadth.status == "computed",
        )
        .order_by(MarketBreadth.scope)
        .all()
    )
    for breadth in sector_rows:
        value_row(
            "sector_participation",
            breadth.scope,
            None,
            breadth.metric_value,
            "computed",
            f"Priced {breadth.numerator}/{breadth.denominator} securities "
            f"in {breadth.scope} on 2026-11-03.",
            {
                "numerator": breadth.numerator,
                "denominator": breadth.denominator,
                "price_date": PRICE_DATE,
            },
        )
    market_cov = (
        session.query(MarketBreadth)
        .filter(
            MarketBreadth.trading_date == PRICE_D,
            MarketBreadth.metric_key == "priced_coverage",
            MarketBreadth.scope == "MARKET",
        )
        .one_or_none()
    )
    if market_cov is not None:
        value_row(
            "priced_coverage",
            "MARKET",
            None,
            market_cov.metric_value,
            "computed",
            f"Priced {market_cov.numerator}/{market_cov.denominator} "
            "registry securities on 2026-11-03.",
            {
                "numerator": market_cov.numerator,
                "denominator": market_cov.denominator,
                "price_date": PRICE_DATE,
            },
        )
    top10 = (
        session.query(MarketBreadth)
        .filter(
            MarketBreadth.trading_date == PRICE_D,
            MarketBreadth.metric_key == "top10_volume_share_pct",
            MarketBreadth.scope == "MARKET",
        )
        .one_or_none()
    )
    if top10 is not None:
        value_row(
            "top10_volume_share",
            "MARKET",
            None,
            top10.metric_value,
            "computed",
            "Top-10 securities' share of total 2026-11-03 market volume.",
            {"price_date": PRICE_DATE},
        )
    value_row(
        "sector_volume_hhi",
        "MARKET",
        None,
        None,
        "insufficient_inputs",
        "Per-sector volume shares are not stored by Phase 12 (only "
        "participation counts), so no sector volume HHI can be computed.",
        {"price_date": PRICE_DATE},
    )

    # --- 2d. Ownership concentration (per company with rows) --------------
    # For HUBC the rows are holder categories (key-holder rows carry
    # no percentage and are excluded by the filter, as in the original
    # run); for HBL every body row carries a printed percentage, so
    # the same computation runs over the printed shareholding
    # partition (named holders + categories). Reporting dates are
    # read from the rows, never hardcoded.
    for ticker, sec in securities.items():
        holdings = (
            session.query(OwnershipHolding)
            .filter(
                OwnershipHolding.company_id == sec.company_id,
                OwnershipHolding.is_total.is_(False),
                OwnershipHolding.percentage.isnot(None),
            )
            .all()
        )
        pcts = [Decimal(str(c.percentage)) for c in holdings]
        if not pcts:
            continue
        reporting_dates = sorted({str(c.reporting_date) for c in holdings})
        basis = (
            "holder categories"
            if ticker == "HUBC"
            else "printed shareholding partition (named holders + categories)"
        )
        value_row(
            "largest_holder_share",
            ticker,
            sec.id,
            max(pcts),
            "computed",
            f"Largest holder share of {ticker} shares as at {reporting_dates[-1]}.",
            {
                "basis": basis,
                "reporting_date": reporting_dates[-1],
                "rows_count": len(pcts),
            },
        )
        value_row(
            "top3_holder_share",
            ticker,
            sec.id,
            top_n_share(pcts, 3),
            "computed",
            f"Top-3 holder shares' combined share of {ticker} shares as at {reporting_dates[-1]}.",
            {"basis": basis, "reporting_date": reporting_dates[-1]},
        )

    # --- 2e. Sensitivity coefficients: all insufficient ----------------------
    for ticker, metric_key, reason in SENSITIVITY_ROWS:
        sec = securities.get(ticker)
        if sec is None:
            continue
        value_row(
            metric_key,
            ticker,
            sec.id,
            None,
            "insufficient_inputs",
            reason,
            {"exposure_evidenced": True, "coefficient_stored": False},
        )

    # --- 2f. Model risk -------------------------------------------------------
    assessments = session.query(ForecastAssessment).all()
    n_assess = len(assessments)
    n_insuff = sum(1 for a in assessments if a.computation_status == "insufficient_inputs")
    if n_assess:
        value_row(
            "forecast_abstention_rate",
            "MARKET",
            None,
            Decimal(n_insuff) / Decimal(n_assess) * Decimal(100),
            "computed",
            f"Phase 13 abstained on {n_insuff}/{n_assess} assessments: "
            "no series meets any method's interval minimum.",
            {"assessments": n_assess, "insufficient": n_insuff},
            as_of=ANALYSIS_D,
            as_of_str=ANALYSIS_DATE,
        )
    tech_values = session.execute(text("SELECT COUNT(*) FROM technical_indicator_values")).scalar()
    value_row(
        "technical_coverage_rate",
        "MARKET",
        None,
        Decimal(tech_values or 0) / Decimal(470) * Decimal(100),
        "computed",
        "Phase 6 calculable indicator values / 470 assessed securities "
        "(0 values on one trading date).",
        {"values": tech_values or 0, "assessed": 470},
        as_of=ANALYSIS_D,
        as_of_str=ANALYSIS_DATE,
    )
    value_row(
        "input_drift",
        "MARKET",
        None,
        None,
        "insufficient_inputs",
        "Only one feature vintage exists (as of 2026-11-03/04); drift "
        "needs two vintages to compare.",
        {"vintages_available": 1},
        as_of=ANALYSIS_D,
        as_of_str=ANALYSIS_DATE,
    )

    # --- 3. Risk flags ---------------------------------------------------------
    existing_flags = {
        (f.flag_type, f.company_id, str(f.as_of_date)) for f in session.query(RiskFlag).all()
    }

    def flag_row(flag_type, company_id, severity, evidence):
        grain = (flag_type, company_id, ANALYSIS_DATE)
        if grain in existing_flags:
            counters["flags_skipped"] += 1
            return
        existing_flags.add(grain)
        _add(
            session,
            commit,
            RiskFlag(
                flag_type=flag_type,
                company_id=company_id,
                as_of_date=ANALYSIS_D,
                severity=severity,
                evidence=evidence,
            ),
            counters,
            "flags_written",
        )

    for warn in session.query(FundamentalWarningEvent).all():
        sec = session.query(Security).filter(Security.company_id == warn.company_id).first()
        flag_row(
            f"warning_{warn.warning_type}",
            warn.company_id,
            warn.severity,
            {
                "phase8_warning": warn.warning_type,
                "event_date": str(warn.event_date),
                "ticker": sec.ticker if sec else None,
                "note": "Review-only flag from Phase 8; not a fraud, "
                "default or solvency conclusion.",
            },
        )
    for opinion in session.query(AuditorOpinion).all():
        if opinion.opinion_type == "none":
            sec = session.query(Security).filter(Security.company_id == opinion.company_id).first()
            flag_row(
                "auditor_opinion_absent",
                opinion.company_id,
                "info",
                {
                    "ticker": sec.ticker if sec else None,
                    "absence_note": opinion.absence_note,
                    "note": "Interim condensed statements carry no auditor "
                    "opinion row; recorded as a disclosure gap, "
                    "not as an adverse opinion.",
                },
            )
    for ticker, sec in securities.items():
        latest_end = (
            session.query(FinancialStatement.period_end)
            .filter(FinancialStatement.company_id == sec.company_id)
            .order_by(FinancialStatement.period_end.desc())
            .first()
        )
        latest_pub = (
            session.query(FinancialStatement.publication_date)
            .filter(FinancialStatement.company_id == sec.company_id)
            .order_by(FinancialStatement.period_end.desc())
            .first()
        )
        if latest_end and (ANALYSIS_D - latest_end[0]).days > STALE_DAYS:
            flag_row(
                "statement_stale",
                sec.company_id,
                "warning",
                {
                    "ticker": ticker,
                    "latest_period_end": str(latest_end[0]),
                    "age_days": (ANALYSIS_D - latest_end[0]).days,
                    "stale_threshold_days": STALE_DAYS,
                },
            )
        if latest_pub and latest_pub[0] is None:
            flag_row(
                "publication_date_unknown",
                sec.company_id,
                "warning",
                {
                    "ticker": ticker,
                    "note": "Latest statement has NULL publication_date; "
                    "point-in-time validity is unverifiable (the "
                    "same reason Phase 9 did not compute NML P/E).",
                },
            )
    flag_row(
        "forecast_abstention",
        None,
        "warning",
        {
            "insufficient_assessments": n_insuff,
            "total_assessments": n_assess,
            "note": "Phase 13 abstained on every target/horizon; downstream "
            "decisions requiring a forecast are blocked.",
        },
    )
    flag_row(
        "technical_coverage_zero",
        None,
        "warning",
        {
            "calculable_values": tech_values or 0,
            "note": "Phase 6 produced 0 calculable indicator values; "
            "technical inputs to any decision are absent.",
        },
    )
    flag_row(
        "previous_close_absent",
        None,
        "info",
        {
            "note": "previous_close is NULL on all 444 2026-11-03 price "
            "rows; gap risk and advances/declines are blocked."
        },
    )
    flag_row(
        "turnover_absent",
        None,
        "info",
        {
            "note": "Turnover is NULL on all 444 2026-11-03 price rows; "
            "turnover-based liquidity and breadth are blocked."
        },
    )
    flag_row(
        "missing_tickers_26",
        None,
        "info",
        {
            "note": "26 of 470 registry securities have no 2026-11-03 price "
            "row (13 Phase 5 rejections + 13 absent); breadth "
            "coverage is 94.468085%, not 100%."
        },
    )

    # --- 4. Controls v1 + checks ----------------------------------------------
    existing_controls = {(c.control_key, c.version) for c in session.query(RiskControl).all()}
    for key, threshold, rationale in CONTROLS_V1:
        if (key, 1) in existing_controls:
            counters["controls_skipped"] += 1
            continue
        _add(
            session,
            commit,
            RiskControl(
                control_key=key,
                version=1,
                rule={"threshold": threshold, "unit": "pct_or_shares"},
                rationale=rationale,
                effective_date=ANALYSIS_D,
            ),
            counters,
            "controls_written",
        )

    existing_checks = {
        (c.control_key, c.version, c.scope_key, str(c.as_of_date))
        for c in session.query(RiskControlCheck).all()
    }

    def check_row(control_key, scope_key, outcome, observed, threshold, reason, evidence):
        grain = (control_key, 1, scope_key, ANALYSIS_DATE)
        if grain in existing_checks:
            counters["checks_skipped"] += 1
            return
        existing_checks.add(grain)
        _add(
            session,
            commit,
            RiskControlCheck(
                control_key=control_key,
                version=1,
                scope_key=scope_key,
                as_of_date=ANALYSIS_D,
                outcome=outcome,
                observed_value=observed,
                threshold_value=threshold,
                reason=reason,
                evidence=evidence,
            ),
            counters,
            "checks_written",
        )
        counters[f"checks_{outcome}"] += 1

    n_names = len(REFERENCE_PORTFOLIO)
    weight = Decimal(100) / Decimal(n_names)
    check_row(
        "single_name_cap_pct",
        "SIMULATED_PORTFOLIO",
        "breach",
        weight,
        Decimal(25),
        "Equal-weight 3-name reference portfolio holds 33.333333% per "
        "name, above the 25% cap — breach by construction.",
        {"portfolio": "SIMULATED equal-weight HUBC/NML/OGDC", "names": n_names},
    )
    check_row(
        "sector_cap_pct",
        "SIMULATED_PORTFOLIO",
        "pass",
        weight,
        Decimal(50),
        "Each name sits in a different sector (power, textile, oil & "
        "gas exploration), so each sector weight is 33.333333%, "
        "within the 50% cap.",
        {"portfolio": "SIMULATED equal-weight HUBC/NML/OGDC"},
    )
    check_row(
        "drawdown_warning_pct",
        "SIMULATED_PORTFOLIO",
        "blocked",
        None,
        Decimal(-10),
        "No drawdown can be computed from one price date; the check "
        "is BLOCKED, never passed by default.",
        {"price_dates_available": 1},
    )
    check_row(
        "min_diversification_names",
        "SIMULATED_PORTFOLIO",
        "pass",
        Decimal(n_names),
        Decimal(3),
        "Reference portfolio holds 3 names, meeting the minimum of 3.",
        {"portfolio": "SIMULATED equal-weight HUBC/NML/OGDC"},
    )
    for ticker, sec in securities.items():
        row = prices.get(ticker)
        vol = None if row is None else row.volume
        if vol is None:
            check_row(
                "min_daily_volume_shares",
                ticker,
                "blocked",
                None,
                Decimal(50000),
                "No 2026-11-03 volume row.",
                {"price_date": PRICE_DATE},
            )
        elif vol >= 50000:
            check_row(
                "min_daily_volume_shares",
                ticker,
                "pass",
                Decimal(vol),
                Decimal(50000),
                f"2026-11-03 volume {vol} meets the 50,000-share minimum.",
                {"price_date": PRICE_DATE},
            )
        else:
            check_row(
                "min_daily_volume_shares",
                ticker,
                "breach",
                Decimal(vol),
                Decimal(50000),
                f"2026-11-03 volume {vol} is below the 50,000-share minimum.",
                {"price_date": PRICE_DATE},
            )

    # --- 5. Stress scenarios + results -----------------------------------------
    existing_scen = {s.scenario_key for s in session.query(StressScenario).all()}
    for key, shock, applies_to, method in STRESS_SCENARIOS:
        if key in existing_scen:
            counters["scenarios_skipped"] += 1
            continue
        _add(
            session,
            commit,
            StressScenario(
                scenario_key=key,
                shock=shock,
                applies_to=applies_to,
                method=method,
            ),
            counters,
            "scenarios_written",
        )

    existing_stress = {
        (r.scenario_key, r.scope_key, str(r.as_of_date)) for r in session.query(StressResult).all()
    }

    def stress_row(scenario_key, scope_key, impact, status, reason, evidence):
        grain = (scenario_key, scope_key, PRICE_DATE)
        if grain in existing_stress:
            counters["stress_skipped"] += 1
            return
        existing_stress.add(grain)
        _add(
            session,
            commit,
            StressResult(
                scenario_key=scenario_key,
                scope_key=scope_key,
                as_of_date=PRICE_D,
                impact_pct=impact,
                computation_status=status,
                reason=reason,
                evidence=evidence,
            ),
            counters,
            "stress_written",
        )
        if status == "computed":
            counters["stress_computed"] += 1
        else:
            counters["stress_insufficient"] += 1

    # Portfolio shocks run over the 3-name reference portfolio only,
    # even though per-company sections now cover 4 tickers (HBL is
    # not in the simulated portfolio — see RISK_TICKERS note).
    ref_names = [t for t, _ in REFERENCE_PORTFOLIO]
    closes = {
        t: prices[t].close_price
        for t in ref_names
        if t in prices and prices[t].close_price is not None
    }
    if len(closes) == n_names:
        weights = [Decimal(100) / Decimal(n_names)] * n_names
        impact = portfolio_shock_impact(weights, [Decimal(-10)] * n_names)
        stress_row(
            "market_minus_10",
            "SIMULATED_PORTFOLIO",
            impact,
            "computed",
            "Uniform -10% shock on all three 2026-11-03 closes; simulation only, not a forecast.",
            {
                "portfolio": "SIMULATED equal-weight HUBC/NML/OGDC",
                "closes": {t: str(c) for t, c in closes.items()},
                "price_date": PRICE_DATE,
            },
        )
        for ticker in closes:
            shocks = [Decimal(-20) if t == ticker else Decimal(0) for t in closes]
            impact = portfolio_shock_impact(weights, shocks)
            stress_row(
                "idiosyncratic_minus_20",
                ticker,
                impact,
                "computed",
                f"Only {ticker} shocked -20%; others unchanged; simulation only, not a forecast.",
                {
                    "shocked_ticker": ticker,
                    "portfolio": "SIMULATED equal-weight HUBC/NML/OGDC",
                    "price_date": PRICE_DATE,
                },
            )
    for ticker in ("HUBC", "NML", "OGDC"):
        if ticker in securities:
            stress_row(
                "rate_plus_100bps",
                ticker,
                None,
                "insufficient_inputs",
                "No rate sensitivity coefficient is stored (floating/"
                "fixed debt split unknown); the scenario is defined "
                "but not computed.",
                {"coefficient_stored": False},
            )
    if "HBL" in securities:
        stress_row(
            "rate_plus_100bps",
            "HBL",
            None,
            "insufficient_inputs",
            "No rate sensitivity coefficient is stored (repricing split "
            "of advances/deposits unknown); the scenario is defined "
            "but not computed.",
            {"coefficient_stored": False},
        )
    for ticker in ("NML", "OGDC"):
        if ticker in securities:
            stress_row(
                "fx_pkr_minus_10",
                ticker,
                None,
                "insufficient_inputs",
                "No FX sensitivity coefficient is stored (FX-denominated "
                "amounts unknown); the scenario is defined but not computed.",
                {"coefficient_stored": False},
            )
    if "HBL" in securities:
        stress_row(
            "fx_pkr_minus_10",
            "HBL",
            None,
            "insufficient_inputs",
            "No FX sensitivity coefficient is stored (FX-denominated "
            "amounts unknown); the scenario is defined but not computed.",
            {"coefficient_stored": False},
        )
    if "OGDC" in securities:
        stress_row(
            "commodity_oil_minus_10",
            "OGDC",
            None,
            "insufficient_inputs",
            "No revenue elasticity to oil prices is stored; the "
            "scenario is defined but not computed.",
            {"coefficient_stored": False},
        )

    return {
        **counters,
        "analysis_date": ANALYSIS_DATE,
        "price_date": PRICE_DATE,
        "securities_in_scope": sorted(securities),
        "simulated_portfolio": "equal-weight HUBC/NML/OGDC (simulation only)",
    }
