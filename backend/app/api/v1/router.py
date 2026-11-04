"""API v1 router: all versioned routes live under ``/api/v1``."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import registry, system, universe

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(registry.router)
api_router.include_router(universe.router)
