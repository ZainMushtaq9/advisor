# Phase 25 — Operations dashboard

## API (GET-only, `/api/v1/jobs/*`)

| Endpoint | Returns |
|---|---|
| `GET /jobs/definitions` | 8 definitions with schedules, priorities, pause reasons |
| `GET /jobs/runs?limit&offset&job_key&status` | Paginated runs (limit 1..100) |
| `GET /jobs/runs/{id}` | One run with summary and error |
| `GET /jobs/checkpoints` | Last successful watermarks per job |
| `GET /jobs/dead-letters` | Terminally failed runs awaiting retry |
| `GET /jobs/status` | Run counts, stuck runs, paused definitions, unresolved dead letters, watermarks |

Bad pagination → 400; unknown run → 404. No endpoint
writes anything; no endpoint exposes credentials, DSNs,
or internal paths.

## Frontend (`/admin/jobs`)

- Operations status card: totals by status, stuck-run
  count, unresolved dead letters, paused definitions.
- Definitions table with human-readable schedules and
  exact pause reasons.
- Recent runs table (20) with status badges and
  error/blocked reasons.
- Dead letters table (explicit empty state when none).
- Checkpoints table (watermark key → value).
- Header states the limits on every view: read-only,
  CLI-only actions, paused collection jobs never run,
  no daemon, no paid scheduler.
- Linked from the Admin page ("Jobs / automation" row)
  and the primary nav ("Jobs").

## CLI (the only write path)

`scripts/run_jobs.py`: register, list, due, run-due,
run-one (with `--date` / `--run-tag`), cancel,
retry-dead, status, purge (`--confirm` deletes only
auth audit logs older than 12 months; dry-run default).
JSON on stdout, summary on stderr, exit 0/1/2.

## Health checks

- `status` / dashboard: stuck runs must be 0 in steady
  state; unresolved dead letters must be 0; paused
  definitions must be exactly the 3 collection jobs.
- `drift_check` summaries must show `drift_count` 0
  unless a later phase legitimately changed a count
  (then that phase updates EXPECTED_COUNTS with its
  evidence — drift is a finding, not an error to hide).
- `report_qa_audit` must show 22 reports, 541 figures,
  `published_externally` 0, no publish columns.
