"""Phase 6 technical indicators package.

Deterministic, reproducible Python calculations only. No LLM ever
calculates an indicator value, and no function here touches the
network, the filesystem, or any external service. Every function
takes an explicit list of bars and returns a Decimal (or a dict of
Decimals for multi-output indicators), or raises InsufficientData
when warm-up, inputs, or degeneracy rules are not met. Nothing is
ever fabricated to fill a gap: a missing bar is absent, never zero.
"""

from __future__ import annotations

from app.services.technical_indicators import (
    aggregation,
    conventions,
    coverage,
    formulas,
    signals,
)

__all__ = ["aggregation", "conventions", "coverage", "formulas", "signals"]
