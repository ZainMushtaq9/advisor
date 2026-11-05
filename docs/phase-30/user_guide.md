# PSX Intelligence AI — User Guide (Phase 30)

## What this system is — and is not

An intelligence platform for Pakistan Stock Exchange data: registry,
market prices, financial statements, ratios, valuations, macro context,
news events, ownership/breadth, forecasting research, risk, decisions,
simulated portfolios, backtests, orchestration, knowledge retrieval,
screening, alerts, and reports — all computed deterministically from
stored, provenance-tagged data. **An LLM never invents a numerical
financial result.** Every number shown comes from a deterministic
function run over stored data.

It is NOT: a trading terminal, a broker, a tip service, or a publisher.
There is no broker connection and no order-placement path. Portfolios
are SIMULATED with hypothetical capital. Decisions are research
opinions only, and every user-facing decision value is currently
WITHHELD (see "Reading the badges"). Reports are DRAFT only — none is
approved, none is published externally. Alerts are in-app only; no
email, SMS, or push notification exists.

## Starting, stopping, checking

From the repository root (see `ops/README.md` for the full reference):

```bash
bash ops/start.sh       # postgres if down + backend + frontend (production build only; jobs are NOT started)
bash ops/healthcheck.sh # postgres, backend /health, frontend /, migration match — all must be OK
bash ops/status.sh      # read-only status
bash ops/stop.sh        # backend + frontend only; postgres is never touched
```

- Backend: http://localhost:8000 (`/health`, `/api/v1/...`).
- Frontend: http://localhost:3000. The backend accepts only port-3000
  origins (CORS); serving the frontend on any other port blocks API calls.
- After a VM reboot, run `pg_ctlcluster 16 main start` before DB work
  (policy-rc.d denies auto-start).
- Jobs are operator-invoked, not automatic: there is no daemon and no
  host cron. Run due jobs explicitly (see "Jobs" below).

## Dashboard tour (18 sections, all from the real GET-only APIs)

Home, Dashboard, Companies, Market, Securities, News, Fundamentals,
Valuation, Macro, Technical, Forecasts, Risk, Portfolio, Screener,
Alerts, Reports, Research, Admin. Company detail (`/companies/[key]`,
by registry id or ticker) has seven tabs: Overview, Fundamentals,
Valuation, Macro, Ownership & actions, Risk, News & reports. Report
detail (`/reports/[id]`) shows sections in template order plus the
figure table. Admin pages: `/admin/jobs`, `/admin/evaluation`,
`/admin/observability`, `/admin/acceptance`.

The watchlist is localStorage-only ("this browser only") — no account
system exists, and no live auth accounts exist (auth tables are empty
by decision; enforced mode is fail-closed until an admin account is
created with the CLI-only tool — an operator decision, not a user
action in the dashboard).

## Reading the badges (do not skip this)

- **Quality UNVERIFIED** — the row comes from a single source. VERIFIED
  would require ≥2 distinct agreeing sources including one official
  source; that bar is not met for registry, prices, statements, ratios,
  or valuations. The 6 VERIFIED macro rows are the exception, and they
  rest on documented SBP/PBS cross-publisher agreement, not on second
  evidence rows in the database.
- **Computation status** — `computed` (a value exists),
  `insufficient_inputs` (the inputs do not exist — no value is shown,
  never zero-filled), `not_applicable` (the method does not apply to
  this company, e.g. the bank model for industrials).
- **DRAFT** — every report is a draft. DRAFT means "not internally
  reviewed"; it does not mean "ready to share".
- **WITHHELD** — every user-facing decision value. Issuance requires a
  research conclusion AND confidence ≥ MEDIUM; confidence caps at LOW
  because all inputs are UNVERIFIED, calibration is NOT_ESTABLISHED
  (forecasting abstained), and technical evidence is absent.
- **SIMULATED** — every portfolio and every paper-ledger entry. The
  capital (PKR 1,000,000) is hypothetical; holdings reconcile exactly,
  but nothing was bought or sold.
- **NOT_RUNNABLE** — every backtest. The window holds a single price
  observation and zero return intervals; no series was invented to make
  a backtest "work".
- **Abstained** — all 120 forecast assessments. No forecast figure
  appears anywhere; a point-only value that cannot carry an interval is
  recorded as abstained, never stored as a forecast.
- **HBL pending (historical note)** — HBL statements are now loaded
  (30 statements, 800 line items, consolidated audited FY ended
  31 Dec 2025), but HBL ratios, valuations, decisions-with-evidence,
  positions, backtests, RAG answers, and statement-derived alerts do
  NOT exist yet: the Phases 8+ HBL re-runs are sequenced after
  Phase 30. Until they land, HBL appears only in market-wide figures
  (price/volume screens, breadth/liquidity, one high-volume alert).

## Jobs (operator-invoked)

```bash
python3 scripts/run_jobs.py register   # seed the 8-job registry
python3 scripts/run_jobs.py run-due    # run due jobs, one pass
python3 scripts/run_jobs.py status     # counts: runs, stuck, dead letters
```

The 3 collection jobs (`market_post_close`, `filing_check`,
`macro_release_check`) are PAUSED with exact reasons (Terms gate / no
automated fetch approved); the runner refuses paused jobs, and their
handlers are stubs that dead-letter if ever dispatched. Do not unpause
them without written PSX permission evidence (see handover report).
The retention purge job is manual-only (dry-run default; `--confirm`
deletes only auth audit rows older than 12 months; job tables are
never purged).

## Reports

Reports are generated by `scripts/run_reports.py` (dry-run default,
`--commit`). Approval is a CLI transition only
(DRAFT → APPROVED/REJECTED); APPROVED means "internally reviewed
only". There is no publish step and no external publication path.
Approval is NOT token-gated (defect D-12, open) — treat the CLI
transition as a procedural control, not a security control, until a
phase brief covers token-gating.

## Backup and restore (operator)

```bash
set -a; source database/.env; set +a
bash database/backup.sh                                  # → storage/backups/<ts>-PKT/ (dump + files + manifest)
bash database/restore.sh <backup-dir> <scratch-db>       # default target is the restore-test DB, never live
bash database/verify_restore.sh <backup-dir> <scratch-db> # three-axis gate: hashes, row counts, alembic revision
```

Restoring over the live database is REFUSED unless
`ALLOW_LIVE_RESTORE=1` is set explicitly, and only after a verified
backup of live exists. Backup retention: 30 valid backups, never the
newest, never invalid-manifest directories (`ops/prune_backups.sh`,
dry-run default). Encryption is optional (`BACKUP_GPG_RECIPIENT`);
unset means plaintext, the unchanged default — there is no persistent
backup-encryption key (defect D-09, operator decision).

## Limitations you must know before using any number

- Registry: Main Board / Normal Counter only (470 companies). GEM and
  Non-Compliant/Winding-Up counters are NOT captured (Terms-gated).
- Prices: ONE trading date (2026-11-03), 444 rows, previous_close NULL
  on all rows. No returns, no technical values, no advances/declines.
- Statements: 4 companies (HUBC, NML, OGDC, HBL at statement level
  only). Everything else has no statement-derived analysis.
- No share-count data: no P/B, P/S, market cap, EV multiples, or
  dividend yield. No DCF/DDM/peer medians (no source-backed WACC,
  growth, forecasts, or share counts).
- No verified local LLM or embedding model: orchestration is
  rule-based fallback only; vector retrieval is registered, not
  implemented.
- No live accounts, no enforced-mode production proof, no host cron,
  no multi-instance rate limiting, no CI-in-CI.
- If a number's provenance is unclear, treat it as UNVERIFIED and do
  not act on it. Nothing here is investment advice.

## Support

There is no external support contact and no incident hotline: the
operator is the user. Procedures live in `docs/phase-27/` (incident
playbooks) and `ops/README.md`. When reporting a problem, include the
correlation ID from the response header (`X-Correlation-ID`), the
run id, and the exact command — never a secret.
