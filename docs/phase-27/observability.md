# Phase 27 — Observability: Logs, Correlation IDs, Metrics, Health

## Structured logs

- Format: one JSON object per record on stdout/stderr
  (`backend/app/services/observability/logging_config.py`).
- Every record carries `level`, `logger`, `message`, and
  `correlation_id`. Job run ids and agent run ids are logged as
  separate fields, never folded into message text.
- Values are rendered on one line: an injected newline in a
  value cannot forge a second record.
- No log text is stored in the database. The database holds
  measurements (`observability_*` tables), not messages.

## Correlation IDs

- Middleware (`CorrelationIdMiddleware`, wired in `app/main.py`)
  takes an incoming `X-Correlation-ID` header when present,
  otherwise generates a 16-hex id per request, and echoes it
  back as an `X-Correlation-ID` response header.
- Verified live: `/api/v1/health` returns the header, and a
  client-supplied id is echoed unchanged.
- A user reporting a failure can quote one id; the operator
  finds every record for that request by it.

## Redaction (brief: "Avoid logging secrets or unnecessary personal data")

Keys matched case-insensitively by substring: password, passwd,
pwd, token, secret, api_key, apikey, authorization, auth, cookie,
session, dsn, database_url, private_key, bearer. Matched values
become `[REDACTED]`. A string shaped like a database URL
(`scheme://...@...`) is redacted in full, never partially masked.
Tested: formatter output contains no secret value, keeps
operational fields (ticker, counts), and stays single-line.

No email address, personal identifier, or full row content is
ever logged. Tickers, counts, dates, and run ids are operational
data, not personal data.

## Health and readiness

- `GET /api/v1/health` — liveness only (Phase 2, unchanged).
- `GET /api/v1/system/status` — real versions + live DB probe
  (Phase 2, unchanged).
- `GET /api/v1/observability/readiness` (new) — database probe,
  migration head vs expected `20261104_0023`, latest
  observability run, auth mode, and a boolean `ready` that is
  true only when the database is reachable AND the migration
  head matches. When no database exists at all, it reports
  `reachable: false, ready: false` instead of crashing — a
  readiness endpoint that 500s when the database is down is
  worse than useless (bug caught in tests, fixed before commit).
- Verified live: readiness reports `ready: true`,
  `migration_matches: true`, latest run
  `phase27-observability-2026-11-05`, auth enforcement `off`.

## Metrics and error tracking

- API metrics: latency is recorded as single samples, never as
  percentiles (see `performance_baseline.md`).
- Error tracking: failures surface as SLO measurements
  (unmet), exception-queue rows (open), and incident reports
  (resolved with evidence) — all queryable via the GET-only
  observability API and visible on `/admin/observability`.
- Job/agent run IDs: every job run, orchestration run,
  evaluation run, and observability run carries its own id;
  the dashboard joins them by run id, never by row position.
