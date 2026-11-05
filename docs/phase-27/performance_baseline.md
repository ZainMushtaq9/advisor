# Phase 27 — Performance Baseline and Optimization Report

All probes are single samples, labelled as such. No percentile
is claimed from a single sample. Database timings use a
monotonic clock; storage uses `pg_total_relation_size` (table +
indexes + TOAST) and `pg_database_size` on PostgreSQL. On SQLite
the storage probes return NULL with a reason — a storage number
is never invented for a dialect that cannot produce it.

## Seed baseline (run `phase27-observability-2026-11-05`)

### Database query timings

| Probe | Value |
|---|---|
| COUNT(*) market_prices | 0.387 ms |
| COUNT(*) financial_statement_line_items | 0.345 ms |
| COUNT(*) rag_chunks | 0.423 ms |
| COUNT(*) screen_results | 0.337 ms |
| COUNT(*) registry_evidence | 0.266 ms |
| Ticker-keyed company lookup (HUBC) | 1.557 ms |

### Database storage

| Probe | Value |
|---|---|
| Total database size | 25,492,503 bytes (~24.3 MB) |
| screen_results | 1,572,864 bytes |
| rag_chunks | 1,474,560 bytes |
| financial_statement_line_items | 1,196,032 bytes |
| registry_evidence | 720,896 bytes |
| market_prices | 360,448 bytes |
| report_figures | 221,184 bytes |

### API latency (live smoke, uvicorn, TestClient-equivalent curl)

- `/api/v1/health`: 200 with security headers + correlation id.
- `/api/v1/observability/readiness`: 200, `ready: true`,
  migration match true.
- `/api/v1/observability/summary`: 200, full seed counts.
- `/api/v1/observability/slos`: 200, 14 definitions, 4 unmet.
- `/api/v1/observability/incidents`: 200, 3 resolved.
- Unknown route: 404. Bad pagination: 400.

### Frontend rendering (prior measured baseline, Phase 23 UX audit)

DOM ready 28–299 ms; goto-to-networkidle ~1.0–1.6 s (API
round-trips, not rendering). No high-impact perf issue found
then; the Phase 27 page adds one more admin route of the same
shape (tables over GET-only APIs) and the Playwright suite
passes in ~10 s for 6 tests.

### Model runtimes

No local model runtime exists to profile: LLM-backed execution
is unavailable (Phase 18 fallback only) and vector retrieval is
not implemented (Phase 19). Both are recorded as absent, not as
fast. When a verified local model lands, its runtime becomes a
probe before it becomes a dependency.

## Optimization report: no index added, on purpose

The brief says to optimize "measured bottlenecks ... where
justified". The measurements show no bottleneck:

- Every COUNT(*) probe is under 0.5 ms. The largest business
  table has 1,418 rows.
- The ticker lookup (the dashboard's hot path) is 1.557 ms.
- Existing indexes already cover the hot paths:
  `idx_market_prices_security_date`,
  `idx_securities_company`, plus primary-key and grain
  unique constraints.

The one plausible new index, `report_figures.report_id`
(report detail queries filter by it), was evaluated and
REJECTED: the table has 541 rows, the probe shows no
measurable cost, and adding it would be decoration, not
optimization. If the table grows past ~100,000 rows or the
probe exceeds 50 ms on two consecutive runs, that decision
reverses — the trigger is recorded here so it is not a matter
of opinion later.

No batching, caching, or partitioning change was made either,
for the same reason: nothing measured justifies one. Caching
in particular would risk serving stale quality statuses, which
this project treats as a correctness failure, not a speedup.

## Storage growth note

Total database size is ~24.3 MB after 26 phases. Growth is
dominated by screen_results and rag_chunks (both bounded by
seed scope, not by time). The next growth event will be the
HBL load (one more annual report, ~400 pages) and any new
trading day (one more price date) — both bounded and both
visible in the next observability run's storage probes.
