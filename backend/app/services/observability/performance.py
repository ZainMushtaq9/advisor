"""Phase 27 performance baselines: measured probes, not estimates.

Probes (all read-only, all timed with a monotonic clock):

- Database query timings: COUNT(*) on the five largest business
  tables (market_prices, financial_statement_line_items,
  rag_chunks, screen_results, registry_evidence) plus the
  ticker-keyed company lookup the dashboard uses most.
- Database storage: total database size and per-table sizes via
  pg_total_relation_size on PostgreSQL. On SQLite (tests) these
  probes return NULL with a reason — a storage number is never
  invented for a dialect that cannot produce it.
- API latency: measured by the caller (TestClient in tests, the
  Playwright suite in the browser) and recorded here through
  record_api_latency(); this module never claims a percentile
  from a single sample — each probe row is one sample.

Optimization rule (brief: "where justified"): an index, batch,
cache, or partition is added only when a probe shows a measured
bottleneck. At current scale (largest table 1,418 rows) every
probe completes in milliseconds, so the Phase 27 optimization
report records the measurements and adds no index — adding one
would be decoration, not optimization. The check itself (which
indexes already exist on the hot paths) is recorded in the run
report.
"""

from __future__ import annotations

import time
from decimal import Decimal

from sqlalchemy import text

from app.models.reference import Security

# Fixed internal probe list — never user input.
COUNT_TABLES = (
    "market_prices",
    "financial_statement_line_items",
    "rag_chunks",
    "screen_results",
    "registry_evidence",
)

SIZE_TABLES = (
    "market_prices",
    "financial_statement_line_items",
    "rag_chunks",
    "screen_results",
    "report_figures",
    "registry_evidence",
)


def _timed(session, work):  # type: ignore[no-untyped-def]
    start = time.monotonic()
    result = work()
    elapsed_ms = (time.monotonic() - start) * 1000.0
    return result, elapsed_ms


def measure_performance(session) -> list[dict]:
    """Run every baseline probe. Pure reads, no writes."""
    probes: list[dict] = []

    for table in COUNT_TABLES:
        _, elapsed = _timed(
            session,
            lambda table=table: session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar(),
        )
        probes.append(
            {
                "probe_key": f"db_count_{table}",
                "metric_key": "query_latency_ms",
                "value": Decimal(str(round(elapsed, 3))),
                "unit": "ms",
                "notes": "Single COUNT(*) sample; not a percentile.",
            }
        )

    _, elapsed = _timed(
        session,
        lambda: session.query(Security.company_id).filter(Security.ticker == "HUBC").first(),
    )
    probes.append(
        {
            "probe_key": "db_lookup_company_by_ticker",
            "metric_key": "query_latency_ms",
            "value": Decimal(str(round(elapsed, 3))),
            "unit": "ms",
            "notes": "Ticker-keyed lookup (the Phase 23 repair's hot path).",
        }
    )

    dialect = session.bind.dialect.name if session.bind is not None else "unknown"
    if dialect == "postgresql":
        total_bytes, _ = _timed(
            session,
            lambda: session.execute(text("SELECT pg_database_size(current_database())")).scalar(),
        )
        probes.append(
            {
                "probe_key": "db_total_size",
                "metric_key": "bytes",
                "value": Decimal(str(total_bytes)) if total_bytes is not None else None,
                "unit": "bytes",
                "notes": "pg_database_size(current_database()).",
            }
        )
        for table in SIZE_TABLES:
            size_bytes, _ = _timed(
                session,
                lambda table=table: session.execute(
                    text(f"SELECT pg_total_relation_size('{table}')")
                ).scalar(),
            )
            probes.append(
                {
                    "probe_key": f"db_size_{table}",
                    "metric_key": "bytes",
                    "value": Decimal(str(size_bytes)) if size_bytes is not None else None,
                    "unit": "bytes",
                    "notes": "pg_total_relation_size (table + indexes + TOAST).",
                }
            )
    else:
        probes.append(
            {
                "probe_key": "db_total_size",
                "metric_key": "bytes",
                "value": None,
                "unit": "bytes",
                "notes": (f"Storage probe not available on dialect {dialect}; never invented."),
            }
        )

    return probes


def record_api_latency(probes: list[dict], route: str, elapsed_ms: float) -> None:
    """Append one API latency sample (single sample, not a percentile)."""
    probes.append(
        {
            "probe_key": f"api_latency_{route.strip('/').replace('/', '_')}",
            "metric_key": "latency_ms",
            "value": Decimal(str(round(elapsed_ms, 3))),
            "unit": "ms",
            "notes": "Single TestClient sample; not a percentile.",
        }
    )
