"""API v1 router: all versioned routes live under ``/api/v1``."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import system

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
