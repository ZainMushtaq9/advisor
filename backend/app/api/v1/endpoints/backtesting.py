"""Phase 17 backtesting read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent
with a reason. No value is ever fabricated, and no endpoint writes
anything. An unknown strategy, run, or portfolio returns 404.
Nothing here is investment advice, a buy/sell signal, or a
forecast: every backtest result is a labelled SIMULATION, every
production run is NOT_RUNNABLE (single price observation), the
paper ledger re-derives Phase 16 simulated portfolios only, and
no execution path exists anywhere in this project.

Endpoints:
  GET /api/v1/backtesting/strategies
      Registered strategy versions.
  GET /api/v1/backtesting/runs
      Backtest runs with their NOT_RUNNABLE reasons.
  GET /api/v1/backtesting/metrics?run_id=
      Metric rows for one run (value NULL unless computed).
  GET /api/v1/backtesting/ledger?portfolio=
      Paper ledger entries for one simulated portfolio.
  GET /api/v1/backtesting/bias
      Bias-audit checks with evidence.
  GET /api/v1/backtesting/status
      Coverage counts and the honest Phase 17 summary.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.backtesting import (
    BacktestBiasReport,
    BacktestMetric,
    BacktestRun,
    BacktestStrategy,
    PaperLedgerEntry,
)

router = APIRouter(tags=["backtesting"])

SCOPE_NOTE = (
    "Scope: SIMULATION ONLY. Production backtest runs are "
    "NOT_RUNNABLE: the window holds a single price observation "
    "(2026-11-03), hence zero return intervals, so no return-based "
    "metric is computable and benchmark-relative return is "
    "not_applicable (no benchmark series loaded). The paper ledger "
    "re-derives Phase 16 simulated portfolios (hypothetical capital "
    "PKR 1,000,000) as opening positions, opening cash, and a "
    "valuation snapshot dated 2026-11-03. Zero paper orders exist: "
    "Phase 15 user-facing values are all WITHHELD and no price "
    "exists after 2026-11-03 for a fill. No live execution exists."
)


def _session(request: Request) -> Session:
    factory = get_session_factory(request.app.state.engine)
    return factory()


@router.get("/backtesting/strategies")
def list_strategies(request: Request):
    session = _session(request)
    try:
        rows = session.query(BacktestStrategy).order_by(BacktestStrategy.name).all()
        return {
            "scope_note": SCOPE_NOTE,
            "strategies": [
                {
                    "name": r.name,
                    "version": r.version,
                    "description": r.description,
                    "rule_reference": r.rule_reference,
                    "parameters": r.parameters,
                    "status": r.status,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/backtesting/runs")
def list_runs(request: Request):
    session = _session(request)
    try:
        rows = session.query(BacktestRun).order_by(BacktestRun.id).all()
        strategies = {s.id: s.name for s in session.query(BacktestStrategy).all()}
        return {
            "scope_note": SCOPE_NOTE,
            "runs": [
                {
                    "id": r.id,
                    "strategy": strategies.get(r.strategy_id),
                    "start_date": str(r.start_date),
                    "end_date": str(r.end_date),
                    "status": r.status,
                    "not_runnable_reasons": r.not_runnable_reasons,
                    "assumptions": r.assumptions,
                    "price_observations": r.price_observations,
                    "return_observations": r.return_observations,
                    "quality_status": r.quality_status,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/backtesting/metrics")
def list_metrics(request: Request, run_id: int):
    session = _session(request)
    try:
        run = session.query(BacktestRun).filter(BacktestRun.id == run_id).one_or_none()
        if run is None:
            raise HTTPException(status_code=404, detail="Backtest run not found.")
        rows = (
            session.query(BacktestMetric)
            .filter(BacktestMetric.run_id == run_id)
            .order_by(BacktestMetric.metric)
            .all()
        )
        return {
            "scope_note": SCOPE_NOTE,
            "run_id": run_id,
            "run_status": run.status,
            "metrics": [
                {
                    "metric": r.metric,
                    "value": str(r.value) if r.value is not None else None,
                    "status": r.status,
                    "reason": r.reason,
                    "evidence": r.evidence,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/backtesting/ledger")
def ledger(request: Request, portfolio: str):
    session = _session(request)
    try:
        rows = (
            session.query(PaperLedgerEntry)
            .filter(PaperLedgerEntry.portfolio_name == portfolio)
            .order_by(PaperLedgerEntry.entry_type, PaperLedgerEntry.ticker_key)
            .all()
        )
        if not rows:
            raise HTTPException(
                status_code=404, detail="No paper ledger entries for this portfolio."
            )
        return {
            "scope_note": SCOPE_NOTE,
            "portfolio": portfolio,
            "simulation": True,
            "entries": [
                {
                    "entry_type": r.entry_type,
                    "ticker": r.ticker,
                    "units": str(r.units) if r.units is not None else None,
                    "price": str(r.price) if r.price is not None else None,
                    "value": str(r.value),
                    "cash_after": str(r.cash_after),
                    "entry_date": str(r.entry_date),
                    "source": r.source,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/backtesting/bias")
def bias(request: Request):
    session = _session(request)
    try:
        rows = session.query(BacktestBiasReport).order_by(BacktestBiasReport.check_name).all()
        return {
            "scope_note": SCOPE_NOTE,
            "checks": [
                {"check": r.check_name, "result": r.result, "evidence": r.evidence} for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/backtesting/status")
def status(request: Request):
    session = _session(request)
    try:
        return {
            "scope_note": SCOPE_NOTE,
            "strategies": session.query(BacktestStrategy).count(),
            "runs": session.query(BacktestRun).count(),
            "runs_not_runnable": session.query(BacktestRun)
            .filter(BacktestRun.status == "NOT_RUNNABLE")
            .count(),
            "metrics": session.query(BacktestMetric).count(),
            "metrics_computed": session.query(BacktestMetric)
            .filter(BacktestMetric.status == "computed")
            .count(),
            "ledger_entries": session.query(PaperLedgerEntry).count(),
            "paper_orders": 0,
            "bias_checks": session.query(BacktestBiasReport).count(),
            "verdict": "PARTIALLY COMPLETE",
            "verdict_reason": (
                "Engine, registry, paper ledger, and bias audit are "
                "delivered; no production backtest is runnable because "
                "the window holds a single price observation."
            ),
        }
    finally:
        session.close()
