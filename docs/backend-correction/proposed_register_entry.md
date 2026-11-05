# Proposed register entry — backend correction + KPI testing (2026-11-05)

> For parent consolidation only. This file does not edit
> `PHASE_COMPLETION_REGISTER.md`, `PROJECT_EXECUTION_STATE.md`, or
> `MASTER_EXECUTION_LOG.md`.

## Entry

**Backend correction + KPI testing (branch `backend-correction-kpi`,
from `news-intelligence` `57f77ec` + merge of `d05-readiness-g5`
`261eab8`, clean, zero conflicts).** Deploy branch for the hosted
backend: `backend-correction-kpi` — the only line containing the HBL
batch code, the news engine + migration 0025, the blockers fixes, and
the CORS fix below. Chain head 0025; readiness constant 0025 matches
the branch's own chain head (the d05 "tracks live head, not chain
head" caveat is closed by this merge).

**VM-replacement recovery (this session):** fresh PostgreSQL 16
cluster found (no `psx_app`, no `psx_intelligence`); backup
`2026-11-05T0642-PKT` SHA-verified and restored (counts matched the
manifest exactly; ticker map HUBC 759 / NML 864 / OGDC 873 / HBL 747);
deterministic Phases 8–22 re-run reproduced every batch-end count
(fundamentals 144, valuations 68, exposures 9, news 8, ownership 112,
assessments 156, risk 95, decisions 5, chunks 2,020, screens 1,422,
alerts 89, reports 25, figures 649 = 389/244/16 census); migration
0025 applied; news jobs 11, 8 refused collection runs, 8
INSUFFICIENT_DATA reactions, 0 articles; risk as-of 95→98.

**Code correction (1):** `CORS_ORIGINS` from env crashed boot
(`SettingsError`: pydantic-settings JSON-decodes complex env fields
before validators; documented comma-separated format in
`.env.example` never worked via env). Fixed with
`Annotated[tuple[str, ...], NoDecode]` + a validator accepting
comma-separated and JSON-list forms. 7 new regression tests
(`backend/tests/test_cors_env_origins.py`). No CORS behavior change
(env-only origins, no production wildcard, GET-only, no credentials).

**Deploy config (measured):** `ENVIRONMENT=development`,
`AUTH_ENFORCEMENT=off`, `CORS_ORIGINS=<deployed origin>`,
`DATABASE_URL=<hosted>`; `uvicorn app.main:app --host 0.0.0.0
--port $PORT` from `backend/`; `alembic upgrade head` from
`database/` before first boot. Production boot requires auth on and
is fail-closed with 0 accounts (401) — the production flip waits for
first-admin-account creation (separate authorization). Fresh-checkout
boot verified (fresh venv, `pip install -r requirements.txt`).

**KPI evidence (this branch):** SLOs 9/14 met (5 unmet: 4 pre-existing
+ drift 1 = risk 95→98 only); evaluation 45 metrics (33/11/1),
golden 14/14 (batch 61 = 44 base + 17 pre-baseline-update drifts,
not a regression); drift_check run 72 drift 1 (risk only);
acceptance run `phase29-acceptance-2026-11-05-backend-correction`
PARTIALLY COMPLETE, G1–G4 MET, G5 PARTIAL, 14 scenarios (12 pass /
2 not_evaluable), 15/15 recomputations; API smoke 129/130 routes
200 with correct params (only `/auth/me` 401 without a token);
regression: backend pytest 542 passed, vitest 11, webpack build
30/30, Playwright phase23 22/22, phase29 6/6.

**Open (unchanged or new):** host choice; hosted seeding; Netlify
API URL + redeploy; G5 sign-off; D-12; Terms gate BLOCKED; drift
baseline decision (risk 95→98); stale `known_hbl_pending` row;
portfolio expansion (brief only); 2 stale-copy pages; fresh
post-batch audit D1 (recommended).

## Verdict note

No phase verdict changes in this task. The backend line is
deployment-ready except the host-dependent steps above; the system
verdict remains PARTIALLY COMPLETE (G5 pending), as measured by the
new acceptance run.
