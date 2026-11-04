"""API v1 router: all versioned routes live under ``/api/v1``."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import fundamentals, indicators, market, registry, system, valuations

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(registry.router)
api_router.include_router(market.router)
api_router.include_router(indicators.router)
api_router.include_router(fundamentals.router)
api_router.include_router(valuations.router)
