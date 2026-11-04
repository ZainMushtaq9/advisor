"""Phase 5 market-data services: validation, quality, ingestion, catch-up.

Daily OHLCV only; intraday is out of scope. No live adapter, no scraper,
no network collection of any kind: the only input is a dated CSV file
supplied by the operator (see scripts/run_market_ingestion.py).

Scope note (carried into every report and API response): the securities
table in production holds the 470 Main Board / Normal Counter snapshot
securities. This package NEVER describes that scope as "KSE-100" or as
full-market coverage, and it never treats a missing session as a zero
price: a missing date is reported, never filled.
"""

from app.services.market_data import ingestion, quality, scheduler, validation

__all__ = ["ingestion", "quality", "scheduler", "validation"]
