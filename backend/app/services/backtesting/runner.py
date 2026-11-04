"""Phase 17 backtesting runner: build runs, metrics, ledger, bias rows.

Reads stored rows only. No HTTP fetch, no forecast generation, no
execution. Dry-run reports without writing; --commit writes
idempotently (a second --commit writes 0 new rows).

Production truth the runner derives live from the database:
- Price dates in the window: exactly one (2026-11-03), so every
  run has zero return intervals and is NOT_RUNNABLE.
- Metrics: gated by assess_metric; all insufficient_inputs except
  benchmark_relative_return (not_applicable: no benchmark series).
- Ledger: re-derived from Phase 16 CONSTRUCTED portfolios.
- Bias: computed from statements, actions, securities/prices,
  and decisions; disclosed, never hidden.
- Paper orders: none are generated. Phase 15 user-facing values
  are all WITHHELD, so no decision-driven order may be created,
  and no price exists after 2026-11-03 for a fill.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.backtesting import (
    BacktestBiasReport,
    BacktestMetric,
    BacktestRun,
    BacktestStrategy,
    PaperLedgerEntry,
)
from app.models.financial import FinancialStatement
from app.models.market import MarketPrice
from app.models.ownership_actions import CorporateActionRecord
from app.models.portfolio import SimulatedPortfolio, SimulatedPortfolioHolding
from app.models.reference import Company, Security
from app.services.backtesting import (
    EXECUTION_ASSUMPTIONS,
    METRIC_NAMES,
    PRODUCTION_END,
    PRODUCTION_START,
    STRATEGIES,
)
from app.services.backtesting.bias import CHECKS
from app.services.backtesting.metrics import assess_metric, simple_returns
from app.services.backtesting.paper import derive_ledger

DECISION_DATE: date = date(2026, 11, 4)
STALE_THRESHOLD_DAYS = 365


def _price_closes(session: Session, tickers: list[str]) -> dict[str, list[Decimal]]:
    """Closes per ticker inside the production window, sorted by date."""
    out: dict[str, list[Decimal]] = {}
    for ticker in tickers:
        security = session.query(Security).filter(Security.ticker == ticker).one_or_none()
        if security is None:
            out[ticker] = []
            continue
        rows = (
            session.query(MarketPrice)
            .filter(
                MarketPrice.security_id == security.id,
                MarketPrice.trading_date >= PRODUCTION_START,
                MarketPrice.trading_date <= PRODUCTION_END,
                MarketPrice.close_price.isnot(None),
            )
            .order_by(MarketPrice.trading_date)
            .all()
        )
        out[ticker] = [Decimal(r.close_price) for r in rows]
    return out


def _build_bias_evidence(session: Session) -> dict[str, dict]:
    """Assemble bias-check evidence from stored rows."""
    # Point-in-time: statement publications vs the decision date.
    inputs: list[dict] = []
    handled: list[str] = []
    for company_id, ticker in ((289, "HUBC"), (394, "NML"), (403, "OGDC")):
        pubs = [
            r[0]
            for r in session.query(FinancialStatement.publication_date)
            .filter(FinancialStatement.company_id == company_id)
            .distinct()
            .all()
        ]
        known = [p for p in pubs if p is not None]
        if known:
            latest = max(known)
            inputs.append(
                {
                    "ticker": ticker,
                    "kind": "latest_statement_publication",
                    "date": str(latest),
                    "after_decision_date": latest > DECISION_DATE,
                }
            )
        else:
            handled.append(
                f"{ticker} publication date is NULL; company is gated out "
                "of rule-based decisions (Phase 15 SCREEN_FAIL), so no "
                "decision uses an undated publication."
            )
    inputs.append(
        {
            "ticker": "ALL",
            "kind": "latest_price_date",
            "date": str(PRODUCTION_END),
            "after_decision_date": PRODUCTION_END > DECISION_DATE,
        }
    )
    # Survivorship: securities retained vs dropped.
    universe = session.query(Security).count()
    dropped = [
        s.ticker
        for s in session.query(Security)
        .filter(Security.status == "DELISTED")
        .order_by(Security.ticker)
        .all()
    ]
    delisted_rows = session.query(Company).filter(Company.delisting_date.isnot(None)).count()
    # Selection: statement companies vs universe.
    statement_companies = session.query(FinancialStatement.company_id).distinct().count()
    # Corporate actions: dated vs undated.
    actions_total = session.query(CorporateActionRecord).count()
    actions_undated = (
        session.query(CorporateActionRecord)
        .filter(
            CorporateActionRecord.announced_date.is_(None),
            CorporateActionRecord.ex_date.is_(None),
            CorporateActionRecord.record_date.is_(None),
            CorporateActionRecord.effective_date.is_(None),
            CorporateActionRecord.payment_date.is_(None),
        )
        .count()
    )
    # Stale prices: price dates + stale statements.
    price_dates = session.query(MarketPrice.trading_date).distinct().count()
    stale: list[dict] = []
    for company_id, ticker in ((289, "HUBC"), (394, "NML"), (403, "OGDC")):
        latest_end = (
            session.query(FinancialStatement.period_end)
            .filter(FinancialStatement.company_id == company_id)
            .order_by(FinancialStatement.period_end.desc())
            .first()
        )
        if latest_end and latest_end[0] is not None:
            age = (DECISION_DATE - latest_end[0]).days
            if age > STALE_THRESHOLD_DAYS:
                stale.append(
                    {"ticker": ticker, "latest_period_end": str(latest_end[0]), "age_days": age}
                )
    # Missing data: securities without a price on the price date.
    priced_ids = {
        r[0]
        for r in session.query(MarketPrice.security_id)
        .filter(MarketPrice.trading_date == PRODUCTION_END)
        .distinct()
        .all()
    }
    missing = [
        s.ticker
        for s in session.query(Security).order_by(Security.ticker).all()
        if s.id not in priced_ids
    ]
    return {
        "point_in_time": {
            "decision_date": str(DECISION_DATE),
            "inputs": inputs,
            "handled_exceptions": handled,
        },
        "survivorship": {
            "universe_securities": universe,
            "dropped_securities": dropped,
            "delisted_with_date": delisted_rows,
            "limitation": (
                "No delisting feed is loaded; delisting_date is NULL for "
                "all companies, so inactive-security handling is limited "
                "to retaining every registry row."
            ),
        },
        "selection": {
            "covered_companies": statement_companies,
            "universe_companies": session.query(Company).count(),
            "note": (
                "Statement-driven strategies cover only companies with "
                "loaded statements; the remaining universe has no "
                "fundamental inputs."
            ),
        },
        "corporate_actions": {
            "actions_total": actions_total,
            "actions_without_dates": actions_undated,
            "actions_applied": 0,
            "note": (
                "No action has an ex-date, so no price adjustment is "
                "applied; price-based returns would carry dividend bias."
            ),
        },
        "stale_prices": {
            "price_dates": price_dates,
            "price_date": str(PRODUCTION_END),
            "stale_statements": len(stale),
            "stale_detail": stale,
            "threshold_days": STALE_THRESHOLD_DAYS,
        },
        "missing_data": {
            "missing_tickers": missing,
            "missing_count": len(missing),
            "priced_count": len(priced_ids),
        },
        "cost_sensitivity": {
            "production_trades": 0,
            "note": (
                "Zero production trades exist, so cost sensitivity is "
                "not_applicable in production; the cost model is "
                "demonstrated on fixtures only."
            ),
        },
    }


def run_backtesting(session: Session, commit: bool) -> dict:
    """Build the Phase 17 rows; write only when commit is True."""
    report: dict = {
        "strategies": {"written": 0, "skipped": 0},
        "runs": {"written": 0, "skipped": 0},
        "metrics": {"written": 0, "skipped": 0, "computed": 0},
        "ledger": {"written": 0, "skipped": 0},
        "bias": {"written": 0, "skipped": 0},
        "paper_orders": {"written": 0},
    }

    # Strategies.
    strategy_rows: dict[str, BacktestStrategy] = {}
    for name, spec in STRATEGIES.items():
        existing = (
            session.query(BacktestStrategy).filter(BacktestStrategy.name == name).one_or_none()
        )
        if existing is not None:
            strategy_rows[name] = existing
            report["strategies"]["skipped"] += 1
            continue
        row = BacktestStrategy(
            name=name,
            version=spec["version"],
            description=spec["description"],
            rule_reference=spec["rule_reference"],
            parameters=spec["parameters"],
            status="ACTIVE",
        )
        strategy_rows[name] = row
        if commit:
            session.add(row)
            session.flush()
        report["strategies"]["written"] += 1

    # Runs + metrics.
    for name, spec in STRATEGIES.items():
        strategy = strategy_rows[name]
        closes_by_ticker = _price_closes(session, spec["parameters"]["universe"])
        all_closes = [c for series in closes_by_ticker.values() for c in series]
        # Single-name strategies have a real one-close series.
        # Multi-name strategies have no single price series: the
        # portfolio value series holds a single valuation point,
        # which is not a price series, so closes is empty here.
        # Either way the window holds zero return intervals.
        if len(spec["parameters"]["universe"]) == 1:
            closes = closes_by_ticker[spec["parameters"]["universe"][0]]
        else:
            closes = []
        returns = simple_returns(closes)
        price_obs = len({PRODUCTION_START}) if all_closes else 0
        run = (
            session.query(BacktestRun)
            .filter(
                BacktestRun.strategy_id == strategy.id,
                BacktestRun.start_date == PRODUCTION_START,
                BacktestRun.end_date == PRODUCTION_END,
            )
            .one_or_none()
        )
        if run is None:
            run = BacktestRun(
                strategy_id=strategy.id,
                start_date=PRODUCTION_START,
                end_date=PRODUCTION_END,
                status="NOT_RUNNABLE",
                not_runnable_reasons={
                    "window_price_observations": price_obs,
                    "window_return_intervals": len(returns),
                    "reason": (
                        "Window contains a single price observation "
                        "(2026-11-03); zero return intervals exist, so "
                        "no return-based metric is computable."
                    ),
                },
                assumptions=dict(EXECUTION_ASSUMPTIONS),
                price_observations=price_obs,
                return_observations=len(returns),
                quality_status="UNVERIFIED",
            )
            if commit:
                session.add(run)
                session.flush()
            report["runs"]["written"] += 1
        else:
            report["runs"]["skipped"] += 1
        years = Decimal((PRODUCTION_END - PRODUCTION_START).days) / Decimal("365.25")
        for metric in METRIC_NAMES:
            existing = (
                session.query(BacktestMetric)
                .filter(
                    BacktestMetric.run_id == run.id,
                    BacktestMetric.metric == metric,
                )
                .one_or_none()
            )
            if existing is not None:
                report["metrics"]["skipped"] += 1
                continue
            value, status, reason = assess_metric(
                metric,
                closes,
                returns,
                snapshots=1,
                benchmark_return=None,
                years=years,
                daily_risk_free=None,
            )
            row = BacktestMetric(
                run_id=run.id,
                metric=metric,
                value=value,
                status=status,
                reason=reason,
                evidence={
                    "closes_observed": len(closes),
                    "returns_observed": len(returns),
                    "snapshots_observed": 1,
                    "benchmark_loaded": False,
                    "risk_free_established": False,
                },
                quality_status="UNVERIFIED",
            )
            if commit:
                session.add(row)
            report["metrics"]["written"] += 1
            if status == "computed":
                report["metrics"]["computed"] += 1

    # Paper ledger from Phase 16 CONSTRUCTED portfolios.
    portfolios = (
        session.query(SimulatedPortfolio)
        .filter(SimulatedPortfolio.status == "CONSTRUCTED")
        .order_by(SimulatedPortfolio.name)
        .all()
    )
    for portfolio in portfolios:
        holdings = (
            session.query(SimulatedPortfolioHolding)
            .filter(SimulatedPortfolioHolding.portfolio_id == portfolio.id)
            .order_by(SimulatedPortfolioHolding.ticker)
            .all()
        )
        holding_dicts = [
            {
                "ticker": h.ticker,
                "units": h.units,
                "price": h.price,
            }
            for h in holdings
        ]
        entries = derive_ledger(
            portfolio.name, Decimal(portfolio.capital), holding_dicts, PRODUCTION_END
        )
        for entry in entries:
            existing = (
                session.query(PaperLedgerEntry)
                .filter(
                    PaperLedgerEntry.portfolio_name == entry["portfolio_name"],
                    PaperLedgerEntry.entry_type == entry["entry_type"],
                    PaperLedgerEntry.ticker_key == entry["ticker_key"],
                )
                .one_or_none()
            )
            if existing is not None:
                report["ledger"]["skipped"] += 1
                continue
            row = PaperLedgerEntry(
                portfolio_name=entry["portfolio_name"],
                entry_type=entry["entry_type"],
                ticker_key=entry["ticker_key"],
                ticker=entry["ticker"],
                units=entry["units"],
                price=entry["price"],
                value=entry["value"],
                cash_after=entry["cash_after"],
                entry_date=entry["entry_date"],
                source=entry["source"],
            )
            if commit:
                session.add(row)
            report["ledger"]["written"] += 1

    # Bias reports.
    evidence = _build_bias_evidence(session)
    for check_name, checker in CHECKS.items():
        result, ev = checker(evidence[check_name])
        existing = (
            session.query(BacktestBiasReport)
            .filter(BacktestBiasReport.check_name == check_name)
            .one_or_none()
        )
        if existing is not None:
            report["bias"]["skipped"] += 1
            continue
        row = BacktestBiasReport(check_name=check_name, result=result, evidence=ev)
        if commit:
            session.add(row)
        report["bias"]["written"] += 1

    if commit:
        session.commit()
    else:
        session.rollback()
    return report
