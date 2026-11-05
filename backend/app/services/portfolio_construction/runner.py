"""Phase 16 portfolio construction runner (DB orchestration).

Reads only already-stored rows: securities, companies, sectors,
2026-11-03 market prices, and Phase 15 decisions dated
2026-11-04. Builds, in --commit mode, three constructed simulated
portfolios (equal-weight baseline over the statement companies;
rule-based SCREEN_PASS portfolios under the balanced and
conservative profiles) plus one NOT_CALCULABLE mean-variance
comparison row, sector allocations, exclusions, and baseline
comparisons. Dry-run (default) writes nothing.

Idempotency: portfolios are skipped by unique name, holdings /
sectors / exclusions / comparisons by their unique grains, so a
second --commit writes 0 new rows.

No HTTP fetch happens here; no forecast is generated; no live
execution exists anywhere in this project. Capital is hypothetical
simulation capital, never real funds.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.decision import Decision
from app.models.forecasting import ForecastAssessment
from app.models.market import MarketPrice
from app.models.portfolio import (
    PortfolioComparison,
    PortfolioExclusion,
    PortfolioSectorAllocation,
    SimulatedPortfolio,
    SimulatedPortfolioHolding,
)
from app.models.reference import Company, Sector, Security
from app.services.portfolio_construction import (
    ASSUMPTIONS_TEMPLATE,
    BASE_CURRENCY,
    PRICE_DATE,
    RISK_PROFILES,
    SIMULATION_CAPITAL,
    validate_eligibility,
)
from app.services.portfolio_construction.formulas import (
    actual_weights,
    build_equal_weight_positions,
    check_caps,
    mean_variance_gate,
    sector_allocations,
)

PRICE_DAY = date(2026, 11, 3)
DECISION_DAY = date(2026, 11, 4)

# Analysis universe for this run: the statement companies plus
# HBL, which since the re-run batch has statements loaded and a
# current Phase 15 decision (2026-11-05 SCREEN_PASS). HBL is
# eligibility-checked (it has a valid quote) but remains outside
# the portfolio universes below: the baseline is defined over the
# 3 original statement companies (methods.md), and the rule
# portfolios take SCREEN_PASS companies among those three only.
# Expanding either universe to a 4th name is a new portfolio
# design (new portfolio names + Phase 17 ledger re-derivation),
# not a re-run, and needs its own brief.
STATEMENT_TICKERS = ["HUBC", "NML", "OGDC"]
ANALYSIS_TICKERS = ["HUBC", "NML", "OGDC", "HBL"]

# Eligibility probes: tickers validated in the run report to prove
# the four-way distinction (not stored as portfolios).
PROBE_TICKERS = ["ZZZZ", "AGLNCPS"]


def _load_quote(session: Session, ticker: str) -> dict:
    """Eligibility + quote evidence for one ticker on PRICE_DAY."""
    security = session.query(Security).filter(Security.ticker == ticker).one_or_none()
    if security is None:
        status, detail = validate_eligibility(False, None)
        return {
            "ticker": ticker,
            "status": status,
            "detail": detail,
            "security": None,
            "price_row": None,
            "sector": None,
        }
    company = session.query(Company).filter(Company.id == security.company_id).one_or_none()
    sector_name = None
    if company is not None and company.sector_id is not None:
        sector = session.query(Sector).filter(Sector.id == company.sector_id).one_or_none()
        sector_name = sector.name if sector is not None else None
    price_row = (
        session.query(MarketPrice)
        .filter(
            MarketPrice.security_id == security.id,
            MarketPrice.trading_date == PRICE_DAY,
        )
        .one_or_none()
    )
    price = price_row.close_price if price_row is not None else None
    status, detail = validate_eligibility(True, price)
    return {
        "ticker": ticker,
        "status": status,
        "detail": detail,
        "security": security,
        "price_row": price_row,
        "sector": sector_name,
    }


def _load_decisions(session: Session) -> dict[str, Decision]:
    rows = session.query(Decision).filter(Decision.decision_date == DECISION_DAY).all()
    by_ticker: dict[str, Decision] = {}
    for row in rows:
        security = session.query(Security).filter(Security.id == row.security_id).one_or_none()
        if security is not None:
            by_ticker[security.ticker] = row
    return by_ticker


def _binding_constraints(
    profile_name: str, checks: dict, target_weights: list[Decimal]
) -> list[str]:
    """Which constraints actually bound the construction."""
    bound: list[str] = []
    profile = RISK_PROFILES[profile_name]
    if profile["cash_floor"] > 0:
        bound.append(
            "cash_floor: invested amount capped at "
            f"{(Decimal('1') - profile['cash_floor']) * 100}% of capital; "
            "actual cash sits at or just above the floor (excess is "
            "whole-share rounding only)"
        )
    if target_weights and max(target_weights) >= profile["max_single_weight"]:
        bound.append(
            "max_single_weight: target weight sat exactly at the cap; "
            "actual weight sits just under it after whole-share rounding"
        )
    if checks["max_sector_weight"]["pass"] is False:
        bound.append("max_sector_weight: violated (construction rejected)")
    return bound


def _store_portfolio(
    session: Session,
    name: str,
    method: str,
    risk_profile: str,
    positions: list[dict],
    cash: Decimal,
    exclusions: list[dict],
    commit: bool,
    report: dict,
) -> SimulatedPortfolio | None:
    existing = (
        session.query(SimulatedPortfolio).filter(SimulatedPortfolio.name == name).one_or_none()
    )
    if existing is not None:
        report["portfolios_skipped"] += 1
        return existing
    checks = check_caps(
        positions,
        SIMULATION_CAPITAL,
        RISK_PROFILES[risk_profile]["max_single_weight"]
        if risk_profile in RISK_PROFILES
        else Decimal("1"),
        RISK_PROFILES[risk_profile]["max_sector_weight"]
        if risk_profile in RISK_PROFILES
        else Decimal("1"),
        RISK_PROFILES[risk_profile]["cash_floor"]
        if risk_profile in RISK_PROFILES
        else Decimal("0"),
        cash,
    )
    if not checks["max_single_weight"]["pass"] or not checks["max_sector_weight"]["pass"]:
        raise ValueError(f"Portfolio {name} violates a weight cap: {checks}")
    if not checks["cash_floor"]["pass"]:
        raise ValueError(f"Portfolio {name} violates its cash floor: {checks}")
    target_weights = [p["target_weight"] for p in positions]
    portfolio = SimulatedPortfolio(
        name=name,
        method=method,
        capital=SIMULATION_CAPITAL,
        base_currency=BASE_CURRENCY,
        horizon="not_specified",
        risk_profile=risk_profile,
        price_date=PRICE_DAY,
        generated_date=DECISION_DAY,
        constraints={
            "capital": str(SIMULATION_CAPITAL),
            "base_currency": BASE_CURRENCY,
            "horizon": "not_specified",
            "risk_profile": risk_profile,
            "cash_floor": str(
                RISK_PROFILES[risk_profile]["cash_floor"] if risk_profile in RISK_PROFILES else "0"
            ),
            "max_single_weight": str(
                RISK_PROFILES[risk_profile]["max_single_weight"]
                if risk_profile in RISK_PROFILES
                else "1"
            ),
            "max_sector_weight": str(
                RISK_PROFILES[risk_profile]["max_sector_weight"]
                if risk_profile in RISK_PROFILES
                else "1"
            ),
            "eligible_tickers": [p["ticker"] for p in positions],
            "price_date": PRICE_DATE,
            "cash_value": str(cash),
            "cash_weight": str(cash / SIMULATION_CAPITAL),
            "cap_checks": checks,
        },
        assumptions=dict(ASSUMPTIONS_TEMPLATE),
        binding_constraints=_binding_constraints(risk_profile, checks, target_weights)
        if risk_profile in RISK_PROFILES
        else [],
        status="CONSTRUCTED",
        not_calculable_reasons=[],
        source_key="phase16_simulated_construction",
        quality_status="UNVERIFIED",
    )
    if commit:
        session.add(portfolio)
        session.flush()
    else:
        report["portfolios_written"] += 0
        _dry_run_record(report, name, positions, cash, exclusions)
        return None
    report["portfolios_written"] += 1
    actual_weights(positions, SIMULATION_CAPITAL)
    for position in positions:
        _store_holding(session, portfolio, position, report, commit)
    for sector_row in sector_allocations(positions, SIMULATION_CAPITAL):
        _store_sector(session, portfolio, sector_row, report, commit)
    for exclusion in exclusions:
        _store_exclusion(session, portfolio, exclusion, report, commit)
    report["portfolios"][name] = {
        "holdings": len(positions),
        "invested": str(SIMULATION_CAPITAL - cash),
        "cash": str(cash),
        "cash_weight": str(cash / SIMULATION_CAPITAL),
        "exclusions": [e["ticker"] for e in exclusions],
    }
    return portfolio


def _dry_run_record(
    report: dict, name: str, positions: list[dict], cash: Decimal, exclusions: list[dict]
) -> None:
    actual_weights(positions, SIMULATION_CAPITAL)
    report["portfolios"][name] = {
        "holdings": len(positions),
        "invested": str(SIMULATION_CAPITAL - cash),
        "cash": str(cash),
        "cash_weight": str(cash / SIMULATION_CAPITAL),
        "exclusions": [e["ticker"] for e in exclusions],
        "positions": [
            {
                "ticker": p["ticker"],
                "units": str(p["units"]),
                "value": str(p["value"]),
                "actual_weight": str(p["actual_weight"]),
            }
            for p in positions
        ],
    }


def _store_holding(
    session: Session, portfolio: SimulatedPortfolio, position: dict, report: dict, commit: bool
) -> None:
    quote = position["_quote"]
    existing = (
        session.query(SimulatedPortfolioHolding)
        .filter(
            SimulatedPortfolioHolding.portfolio_id == portfolio.id,
            SimulatedPortfolioHolding.security_id == quote["security"].id,
        )
        .one_or_none()
    )
    if existing is not None:
        report["holdings_skipped"] += 1
        return
    session.add(
        SimulatedPortfolioHolding(
            portfolio_id=portfolio.id,
            security_id=quote["security"].id,
            company_id=quote["security"].company_id,
            ticker=position["ticker"],
            sector=position["sector"],
            target_weight=position["target_weight"],
            actual_weight=position["actual_weight"],
            units=position["units"],
            value=position["value"],
            price=position["price"],
            price_id=quote["price_row"].id if quote["price_row"] is not None else None,
            price_date=PRICE_DAY,
            eligibility_status="ELIGIBLE",
            source_key="phase16_simulated_construction",
            quality_status="UNVERIFIED",
        )
    )
    report["holdings_written"] += 1


def _store_sector(
    session: Session, portfolio: SimulatedPortfolio, sector_row: dict, report: dict, commit: bool
) -> None:
    existing = (
        session.query(PortfolioSectorAllocation)
        .filter(
            PortfolioSectorAllocation.portfolio_id == portfolio.id,
            PortfolioSectorAllocation.sector == sector_row["sector"],
        )
        .one_or_none()
    )
    if existing is not None:
        report["sectors_skipped"] += 1
        return
    session.add(
        PortfolioSectorAllocation(
            portfolio_id=portfolio.id,
            sector=sector_row["sector"],
            invested_value=sector_row["invested_value"],
            invested_weight=sector_row["invested_weight"],
            capital_weight=sector_row["capital_weight"],
        )
    )
    report["sectors_written"] += 1


def _store_exclusion(
    session: Session, portfolio: SimulatedPortfolio, exclusion: dict, report: dict, commit: bool
) -> None:
    existing = (
        session.query(PortfolioExclusion)
        .filter(
            PortfolioExclusion.portfolio_id == portfolio.id,
            PortfolioExclusion.ticker == exclusion["ticker"],
        )
        .one_or_none()
    )
    if existing is not None:
        report["exclusions_skipped"] += 1
        return
    session.add(
        PortfolioExclusion(
            portfolio_id=portfolio.id,
            ticker=exclusion["ticker"],
            reason_code=exclusion["reason_code"],
            reason_detail=exclusion["reason_detail"],
        )
    )
    report["exclusions_written"] += 1


def _store_comparison(
    session: Session,
    subject_name: str,
    baseline_name: str | None,
    method_compared: str,
    status: str,
    metrics: dict,
    reasons: list[str],
    report: dict,
    commit: bool,
) -> None:
    existing = (
        session.query(PortfolioComparison)
        .filter(
            PortfolioComparison.subject_name == subject_name,
            PortfolioComparison.method_compared == method_compared,
        )
        .one_or_none()
    )
    if existing is not None:
        report["comparisons_skipped"] += 1
        return
    if not commit:
        # Dry-run: counted nowhere as written; the report carries
        # the comparison content itself (see comparisons_dry_run).
        return
    session.add(
        PortfolioComparison(
            subject_name=subject_name,
            baseline_name=baseline_name,
            method_compared=method_compared,
            status=status,
            metrics=metrics,
            reasons=reasons,
        )
    )
    report["comparisons_written"] += 1


def _comparison_metrics(session: Session, portfolio_name: str, baseline_name: str) -> dict:
    def summary(name: str) -> dict:
        portfolio = (
            session.query(SimulatedPortfolio).filter(SimulatedPortfolio.name == name).one_or_none()
        )
        if portfolio is None:
            return {}
        holdings = (
            session.query(SimulatedPortfolioHolding)
            .filter(SimulatedPortfolioHolding.portfolio_id == portfolio.id)
            .all()
        )
        sectors = (
            session.query(PortfolioSectorAllocation)
            .filter(PortfolioSectorAllocation.portfolio_id == portfolio.id)
            .all()
        )
        invested = sum((h.value for h in holdings), Decimal("0"))
        return {
            "holdings_count": len(holdings),
            "invested": str(invested),
            "cash": str(portfolio.capital - invested),
            "cash_weight": str((portfolio.capital - invested) / portfolio.capital),
            "largest_single_weight": str(
                max((h.actual_weight for h in holdings), default=Decimal("0"))
            ),
            "largest_sector_capital_weight": str(
                max((s.capital_weight for s in sectors), default=Decimal("0"))
            ),
        }

    return {"subject": summary(portfolio_name), "baseline": summary(baseline_name)}


def run_portfolios(
    session: Session, commit: bool = False, profile_filter: str | None = None
) -> dict:
    """Build the Phase 16 simulated portfolios (or dry-run them)."""
    report: dict = {
        "portfolios": {},
        "portfolios_written": 0,
        "portfolios_skipped": 0,
        "holdings_written": 0,
        "holdings_skipped": 0,
        "sectors_written": 0,
        "sectors_skipped": 0,
        "exclusions_written": 0,
        "exclusions_skipped": 0,
        "comparisons_written": 0,
        "comparisons_skipped": 0,
        "eligibility_probes": {},
        "mean_variance": {},
    }

    # Eligibility probes (validation evidence, not portfolios).
    for ticker in PROBE_TICKERS:
        probe = _load_quote(session, ticker)
        report["eligibility_probes"][ticker] = {
            "status": probe["status"],
            "detail": probe["detail"],
        }

    quotes = {ticker: _load_quote(session, ticker) for ticker in ANALYSIS_TICKERS}
    for ticker, quote in quotes.items():
        if quote["status"] != "ELIGIBLE":
            raise ValueError(f"Analysis ticker {ticker} is not eligible: {quote['status']}")
    decisions = _load_decisions(session)

    # 1. Equal-weight baseline over the statement companies.
    baseline_prices = [
        (ticker, quotes[ticker]["price_row"].close_price, quotes[ticker]["sector"])
        for ticker in STATEMENT_TICKERS
    ]
    baseline_positions, baseline_cash = build_equal_weight_positions(
        baseline_prices, SIMULATION_CAPITAL, Decimal("0")
    )
    for position in baseline_positions:
        position["_quote"] = quotes[position["ticker"]]
    _store_portfolio(
        session,
        name="ew_statements_3_balanced",
        method="equal_weight_baseline",
        risk_profile="balanced",
        positions=baseline_positions,
        cash=baseline_cash,
        exclusions=[
            {
                "ticker": "HBL",
                "reason_code": "SCREEN_NOT_RUNNABLE",
                "reason_detail": (
                    "Baseline scope is the 3 original statement companies "
                    "(HUBC, NML, OGDC); HBL has statements loaded since "
                    "the re-run batch and a current Phase 15 decision "
                    "(2026-11-05 SCREEN_PASS), but it is still out of "
                    "baseline scope by definition, not out of the "
                    "universe. HBL's quote itself is ELIGIBLE. Expanding "
                    "the baseline universe needs a new portfolio brief."
                ),
            }
        ],
        commit=commit,
        report=report,
    )

    # 2. Rule-based SCREEN_PASS portfolios under each requested profile.
    screen_pass = [
        ticker
        for ticker in STATEMENT_TICKERS
        if decisions.get(ticker) is not None
        and decisions[ticker].screening_outcome == "SCREEN_PASS"
    ]
    rule_exclusions: list[dict] = []
    for ticker in ANALYSIS_TICKERS:
        decision = decisions.get(ticker)
        if ticker in screen_pass:
            continue
        if decision is None:
            rule_exclusions.append(
                {
                    "ticker": ticker,
                    "reason_code": "SCREEN_NOT_RUNNABLE",
                    "reason_detail": "No Phase 15 decision row for this ticker.",
                }
            )
        elif decision.screening_outcome == "SCREEN_FAIL":
            rule_exclusions.append(
                {
                    "ticker": ticker,
                    "reason_code": "SCREEN_FAIL",
                    "reason_detail": (
                        f"Phase 15 screening failed; gate reasons: {decision.gate_reasons}."
                    ),
                }
            )
        else:
            rule_exclusions.append(
                {
                    "ticker": ticker,
                    "reason_code": decision.screening_outcome,
                    "reason_detail": (
                        "Phase 15 screening is not SCREEN_PASS; gate "
                        f"reasons: {decision.gate_reasons}."
                    ),
                }
            )
    profiles = [profile_filter] if profile_filter is not None else ["balanced", "conservative"]
    for profile_name in profiles:
        if profile_name not in RISK_PROFILES:
            raise ValueError(f"Unknown risk profile: {profile_name}")
        profile = RISK_PROFILES[profile_name]
        rule_prices = [
            (ticker, quotes[ticker]["price_row"].close_price, quotes[ticker]["sector"])
            for ticker in screen_pass
        ]
        rule_positions, rule_cash = build_equal_weight_positions(
            rule_prices, SIMULATION_CAPITAL, profile["cash_floor"]
        )
        for position in rule_positions:
            position["_quote"] = quotes[position["ticker"]]
        _store_portfolio(
            session,
            name=f"rule_screen_pass_{profile_name}",
            method="rule_based_screen_pass",
            risk_profile=profile_name,
            positions=rule_positions,
            cash=rule_cash,
            exclusions=rule_exclusions,
            commit=commit,
            report=report,
        )

    # 3. Baseline comparisons (only meaningful on committed rows;
    # in dry-run mode the metrics are computed from the dry-run
    # positions instead, so the report still shows the comparison).
    if commit:
        for profile_name in profiles:
            subject = f"rule_screen_pass_{profile_name}"
            _store_comparison(
                session,
                subject_name=subject,
                baseline_name="ew_statements_3_balanced",
                method_compared="rule_based_screen_pass",
                status="COMPUTED",
                metrics=_comparison_metrics(session, subject, "ew_statements_3_balanced"),
                reasons=[],
                report=report,
                commit=True,
            )
    else:
        for profile_name in profiles:
            subject = f"rule_screen_pass_{profile_name}"
            subject_summary = report["portfolios"].get(subject, {})
            baseline_summary = report["portfolios"].get("ew_statements_3_balanced", {})
            report.setdefault("comparisons_dry_run", {})[subject] = {
                "subject": subject_summary,
                "baseline": baseline_summary,
            }

    # 4. Mean-variance: gated, never constructed.
    computed_forecasts = 0  # Phase 13 computed 0 forecasts.
    return_observations = 0  # 1 price date gives 0 returns.
    assessments_total = session.query(ForecastAssessment).count()
    gate_status, gate_reasons = mean_variance_gate(
        computed_forecasts, return_observations, assessments_total
    )
    report["mean_variance"] = {"status": gate_status, "reasons": gate_reasons}
    _store_comparison(
        session,
        subject_name="mean_variance",
        baseline_name="ew_statements_3_balanced",
        method_compared="mean_variance",
        status=gate_status,
        metrics={},
        reasons=gate_reasons,
        report=report,
        commit=commit,
    )
    return report
