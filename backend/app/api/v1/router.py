"""API v1 router: all versioned routes live under ``/api/v1``."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    auth,
    backtesting,
    decisions,
    forecasting,
    fundamentals,
    indicators,
    macro,
    market,
    news,
    orchestration,
    ownership,
    portfolios,
    rag,
    registry,
    reports,
    risk,
    screener,
    system,
    valuations,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(registry.router)
api_router.include_router(market.router)
api_router.include_router(indicators.router)
api_router.include_router(fundamentals.router)
api_router.include_router(valuations.router)
api_router.include_router(macro.router)
api_router.include_router(news.router)
api_router.include_router(ownership.router)
api_router.include_router(forecasting.router)
api_router.include_router(risk.router)
api_router.include_router(decisions.router)
api_router.include_router(portfolios.router)
api_router.include_router(backtesting.router)
api_router.include_router(orchestration.router)
api_router.include_router(rag.router)
api_router.include_router(screener.router)
api_router.include_router(alerts.router)
api_router.include_router(reports.router)
