# Application Runtime Audit — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit `8937338`.
**Audit date:** 2026-11-05 (Asia/Karachi).
**Method:** the backend was started by this audit against the
SCRATCH database (never the live database) on `127.0.0.1:8000`,
and the fresh-clone production frontend build was exercised
through the Playwright Phase 29 suite. A successful build alone
was NOT treated as runtime evidence. All routes below were hit
live; all responses quoted are from the scratch backend.

## 1. Startup and health

- Backend (FastAPI/uvicorn from `backend/.venv`, `app.main:app`)
  starts cleanly against scratch PostgreSQL at head `20261104_0024`.
- `GET /health` → 200 `{"status":"ok","service":
  "psx-intelligence-ai"}`.
- Structured request logging works (request id, method, path,
  status, duration_ms per request).
- An early auditor mistake (wrong `--app-dir`) produced a clean
  `ModuleNotFoundError: No module named 'app'` and no partial
  startup — the documented launch form (`cd backend && uvicorn
  app.main:app`) works first time.
- Shutdown is clean (SIGTERM to uvicorn; ports 3000/8000 verified
  clear afterwards). No stray server was left running.

## 2. API surface (live, from `/openapi.json`)

- **123 paths, methods: GET only.** No POST, PUT, PATCH, or DELETE
  route exists anywhere in the API. Static grep confirms the same
  (no `@router.post/put/patch/delete` in any endpoint module).
- **GET-only enforcement, live:** `POST /api/v1/companies` → 405.
- **No execution route:** no `/orders` route, no `place_order` /
  `execute_order` / `submit_order` / `execute_trade` / `place_trade`
  implementation exists outside the acceptance scanner's own
  pattern list. Execution is denied by absence, not by a flag.
- **Unknown identifiers:** ticker route
  `GET /api/v1/market/prices/ZZZZ/latest` → 404 (proper not-found).
  Company route `GET /api/v1/companies/{company_id}` takes an
  INTEGER id: `/companies/XXXX` → 422 validation error,
  `/companies/289` (scratch HUBC id) → 200 with full company record
  (legal name, sector, UNVERIFIED status, securities count).
  API-contract observation (LOW): there is no ticker-keyed company
  route, so callers must resolve ticker → surrogate id first — and
  surrogate ids shift across fresh imports (scratch HUBC 289 vs
  live 759 at handover). A client caching company ids will break
  silently after a re-import; the ticker-keyed market routes do
  not have this problem.

## 3. Live endpoint evidence (scratch backend)

| Endpoint | Result |
|---|---|
| `GET /health` | 200, ok |
| `GET /api/v1/observability/readiness` | 200; see §4 (artifact reproduced) |
| `GET /api/v1/acceptance/gate` | 200; run `phase29-acceptance-2026-11-05`, verdict PARTIALLY COMPLETE, G1 not_met / G2 met / G3 met / G4 met / G5 partial — identical to the stored gate |
| `GET /api/v1/companies/289` | 200; HUBC, POWER GENERATION & DISTRIBUTION, UNVERIFIED |
| `GET /api/v1/market/prices/HUBC/latest` | 200; 2026-11-03, close 197.24, volume 3,218,965, turnover NULL, previous_close NULL, is_adjusted false — honest NULLs, no fabrication |
| `GET /api/v1/market/status` | 200; 444 prices, 444 securities, single date 2026-11-03, all UNVERIFIED, 0 VERIFIED / 0 PARTIALLY_VERIFIED |
| `GET /api/v1/reports` | 200; paginated envelope |
| `POST /api/v1/companies` | 405 (GET-only) |
| `GET /api/v1/companies/XXXX` | 422 (integer id expected) |
| `GET /api/v1/market/prices/ZZZZ/latest` | 404 (unknown ticker) |

No console errors, no 500s, and no stack traces were observed in
any of these calls. No endpoint returned fabricated or
zero-filled data: every gap observed is an explicit NULL, an
insufficient_inputs status, or a 404/422.

## 4. Readiness endpoint artifact (FINDING, pre-existing, LOW)

Live response from the scratch backend:

```json
{
  "migration_head": "20261104_0024",
  "migration_expected": "20261104_0023",
  "migration_matches": false,
  "auth_enforcement": "off",
  "ready": false
}
```

The endpoint hardcodes `EXPECTED_MIGRATION_HEAD = "20261104_0023"`
(`backend/app/api/v1/endpoints/observability.py:51`, a Phase 27
artifact) while the correct head is `20261104_0024`. It therefore
reports `migration_matches: false` and `ready: false` against a
healthy, fully migrated database. This was explicitly NOT fixed in
Phase 30 and is still true on the audit baseline — verified live,
not from a report. Severity LOW (the endpoint is advisory; no
workflow gates on it), but it makes the readiness signal
permanently red and must be fixed by its own brief (the fix is a
one-line constant change; the audit does not make it, per the
read-only rule).

## 5. Authentication posture (live)

- `auth_enforcement: "off"` in the readiness response, consistent
  with zero auth accounts: with no accounts created, the API serves
  data without authentication. This is the documented Phase 24
  posture (CLI-only account creation; enforcement activates on the
  first account and is fail-closed thereafter), but it means the
  current deployment has NO access control — a MEDIUM
  production-readiness finding, not a code defect. Creating the
  first live account is a parent/user decision; this audit created
  none (scratch test accounts were not needed — the audit never
  exercised a write path because none exists).
- No login route over HTTP exists by design; no cookie-based
  session exists; the API is GET-only, so the CSRF analysis
  (not-applicable today, Bearer+dependency rule mandatory for any
  future write route) stands.

## 6. Frontend (production build + live pages)

- Production build (webpack, fresh clone): 27/27 pages, route
  manifest exactly 27 entries including dynamic
  `/companies/[key]/page` and `/reports/[id]/page`.
- 18 navigation sections; company detail and report detail pages
  exist; admin pages (acceptance, evaluation, jobs, observability)
  exist.
- API client prefixes `/api/v1` (`frontend/lib/api.ts`, the Phase
  23 fix); default API URL `http://localhost:8000`.
- Playwright Phase 29 suite against scratch backend + production
  build: **6/6 passed** (desktop + mobile): acceptance page shows
  run/verdict/counts; scenario table shows HBL blocked and no
  failures; defect register shows no critical/high defects. This
  is live UI evidence, not a build log.
- No console errors were reported by the Playwright runs (the
  suite would fail on missing page elements; all assertions
  passed). The Phase 2 smoke specs remain untracked and were not
  re-run (their files are not in the audited tree).

## 7. What the runtime audit does NOT prove

- The backend was exercised on a single trading day of data; no
  multi-day, high-concurrency, or failure-injection behaviour was
  tested (no such tests exist in the suite either).
- No production deployment exists to audit (no hosted frontend,
  no systemd service running in production, no scheduler daemon —
  jobs are operator-invoked by design). The `ops/` scripts were
  statically reviewed (exec-in-subshell, production-build-only
  frontend, postgres left running by `stop.sh`, dirty-tree refusal
  and ff-only pull in `update.sh`) but not executed against a
  production host, because there is none.
- Rate limits (300/min API, 30/min auth) are in-memory and
  single-process; they were not load-tested and would not survive
  a multi-process deployment.

## 8. Verdict for this audit area

The application is OPERATIONAL as a local, read-only, GET-only
analytical system on scratch data: it starts, answers health,
serves all 123 GET routes, enforces GET-only with 405s, handles
unknown tickers with 404s, and renders its admin pages correctly.
It is NOT operational as a production service: no authentication
is enforced (no accounts), no deployment exists, and the readiness
endpoint permanently reports not-ready due to the stale head
constant. Runtime behaviour matches the handover claims in every
case tested, with exactly one live-confirmed artifact (the
readiness constant).
