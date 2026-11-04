# Phase 4 — Completion Report (17-point format)

**Status: PARTIALLY COMPLETE** (engine, APIs, frontend, tests,
and audit verified; production population blocked on a usable
dated official registry source).

## 1. What was built

PSX Company & Security Registry engine on the existing Phase 3
schema: deterministic normalization and matching services,
idempotent incremental importer, evidence-driven verification,
dated-snapshot reconciliation, 9 read-only registry APIs, and a
/database-backed /companies frontend page. One new table only:
`registry_evidence`. No scraper was built against psx.com.pk.

## 2. Gate check results

PASSED. Phase 2 acceptance (PARTIALLY COMPLETE, Docker
definition-only, Playwright not run) and Phase 3 completion
(COMPLETE) read before building. At gate time: PostgreSQL
16.15 live on localhost:5432, 56 public tables, Alembic head
20261104_0004, companies/securities/sectors/exchanges all 0.
Branch `phase-04-company-registry` created from Phase 3 tip
b22281a. The unpushed Phase 2/Phase 3 branches did not block
local Phase 4 work.

## 3. Sources researched (with verification timestamps)

All text fetches 2026-11-04 ~12:56 PKT (fetch headers
2026-11-04 07:56 UTC); full detail in source_research.md.

- PSX official homepage (https://www.psx.com.pk/): 26 PARTIAL
  scrip rows only (volume leaders, GEM, highlighted, futures,
  CDEC contracts — contracts counted separately, never merged
  with equities). No company names, sectors, or listing
  statuses. Not a registry.
- PSX official About Us (https://psx.com.pk/psx/exchange/profile/about-us/about-us):
  dated aggregate only — 535 (+5 GEM) companies, 37 sectors,
  as of August 31, 2026. No list on the page.
- PSX Terms of Use (https://www.psx.com.pk/psx/terms-of-use):
  restrictive — no copying/distribution/modification and no
  automated navigation without prior written permission;
  content "As is". Free access is NOT a redistribution licence.
- PSX Data Services / Vending
  (https://www.psx.com.pk/psx/product-and-services/data-services-vending):
  real-time/EOD/historical data are licensed products;
  redistribution subject to prior approval and licence.
- DPS Listing Status (https://dps.psx.com.pk/listings): 0
  company rows via text fetch (JavaScript-driven table, not a
  site finding). Board/category labels and disclaimer only.
- DPS sitemap (https://dps.psx.com.pk/sitemap): structure only
  (Listing Status, Sector Overview, Stock Screener, etc.) — a
  map of where a registry should live, not registry data.
- SECP homepage (https://www.secp.gov.pk/): no PSX
  listed-company/ticker/sector registry seen; only regulations
  and compliance notices. UNVERIFIED as a registry source.
- psx-dps README (https://github.com/umairsandhu/psx-dps, MIT,
  17 commits, 2 stars): claims only, not live-verified —
  ~496 trading symbols, ~1,029 listed instruments (different
  universes per the README itself), 38 sectors, EOD ~5 years,
  today's ticks only, 224k+ announcements. Also states the
  library is unofficial, endpoints undocumented, and free
  access is not a redistribution licence. Direct DPS access
  from this VM FAILS (NoHealthyNode, D-51) — an environment
  blocker, not a DPS outage finding.
- psxdata README (https://github.com/psxdata/psxdata, MIT, 206
  commits, 30 stars, alpha 0.1.0a1): claims only — `tickers()`
  1000+, `screener()` ~729 (inconsistent within the README),
  37 sectors, daily OHLCV + live snapshots only, no historical
  intraday archive.
- DPS market-watch text copy: a STALE cache crawled
  2026-01-25 (283 days old), numeric sector codes with no name
  mapping, no company legal names — EXCLUDED from use (D-53).

## 4. Actual registry counts from the database

Production (live PostgreSQL, verified by direct counts and by
GET /api/v1/registry/statistics, before and after all tests):
**companies 0, securities 0, sectors 0, evidence rows 0,
quality-report rows 0.** Test-run counts are NOT production:
pytest fake-session imports (2+2 per batch, in-memory only)
and the live-PG check (2+2 created in a transaction, then
ROLLED BACK).

By status (production): all statuses 0 — the registry is empty.

## 5. Reconciliation result against the dated snapshot

**BLOCKED — no usable dated snapshot obtained.** `reconcile()`
is implemented and tested (fixture: snapshot 2 tickers,
registry 2 tickers, matched 1, missing 1, extra 1, coverage
0.5 — a fixture calculation, not a market claim). With
snapshot=None it returns coverage None with an explicit
no-claim note, and it never invents a ratio. The unblocker is a
live-browser extraction of the DPS Listing Status table on a
stated date, saved as a dated snapshot file, or a documented
machine-readable official list (parent task; generic subagents
cannot operate a live browser).

## 6. APIs actually working

All 9 read-only endpoints, verified live on the empty database
via TestClient and on uvicorn port 8003 (statistics 200,
companies 200 with total=0, items=[]; server stopped after):
GET /api/v1/companies, /companies/{id},
/companies/{id}/securities, /securities, /securities/{id},
/sectors, /registry/statistics, /registry/quality,
/registry/sources. Pagination default 50, max 200 (outside
1..200 or skip<0 → 422); unknown ids → 404; no DB configured
→ 503 with a truthful reason, never a fake empty registry.
Full contract in api_documentation.md.

## 7. Frontend actually working

/companies page rebuilt as a client component following the
existing ApiStatus pattern: fetches /companies?limit=50 +
/registry/statistics, renders ONLY API rows, Badge states
("Checking registry…", "Registry unavailable", "Registry
connected — N companies, M securities, K sectors"), empty
state "No registry records yet". No fabricated descriptions,
prices, or ratings; the Phase 2 chart container was removed
from this page (it implied a price view the registry does not
provide). `npm run typecheck`, `npm run lint`, `npm run
build` all pass (route /companies builds). Live preview URL:
UNVERIFIED — the supplied github.dev URL returns only a
GitHub sign-in page; no browser screenshot was obtained by a
generic subagent, and none is claimed.

## 8. Tests actually run (counts)

- Backend pytest: **44 passed, 0 failed, 1 warning** (26 Phase
  4 registry tests + 18 Phase 2 suite re-run; warning is the
  Phase 2 Starlette deprecation, non-blocking).
- Ruff: clean on all Phase 4 backend files, tests, and the
  whole backend.
- Live-PostgreSQL check script (scripts/run_phase4_pg_check.py):
  **PHASE4_PG_CHECK_OK** — 2 TEST ONLY records, re-import
  skipped_as_duplicate=2, adversarial paths (conflict →
  CONFLICTED with stored ISIN unchanged; ambiguous →
  PENDING_REVIEW; ambiguous re-import → no duplicate report),
  reconcile coverage=None, API 200s/404s/422 as claimed, all
  rolled back, final live counts 0.
- Frontend: typecheck pass, lint pass, build pass, Vitest
  **3 files, 11 tests, all passed**.
- Migration cycle: downgrade to 20261104_0004 → upgrade →
  head a909e8449cdd works (auditor-verified); 57 public tables
  after upgrade; phase2_probe retained by design.

## 9. Defects found, fixed, remaining

- D-50 Medium RESOLVED (pre-audit): normalization stripped only
  one legal suffix and did not collapse "&" vs "and".
- D-51 High OPEN (environment blocker): direct DPS access from
  this VM fails (NoHealthyNode on 3 nodes, port 443) — same
  family as the Phase 2 Docker registry TLS failure.
- D-52 Medium OPEN (awaiting live-browser extraction): DPS
  Listing Status yields 0 rows via text fetch (JS-driven).
- D-53 Low RESOLVED by exclusion: stale 2026-01-25 market-watch
  cache not used as a snapshot.
- Audit findings (independent_audit.md): 0 CRITICAL, 1 HIGH
  (H1 VERIFIED trust model), 5 MEDIUM (M1–M5), 6 LOW (L1–L6).
  ALL fixed in code/docs except: ISIN check-digit recomputation
  — ACCEPTED as a documented Phase 5 validation concern
  (format-check only, stated in docs); pytest fake-session
  limitation — ACCEPTED with the live-PG adversarial check as
  mitigation. See §10.

## 10. Audit findings (independent audit, PASS WITH LIMITATIONS)

- H1 HIGH (fixed): VERIFIED could be minted by a single
  import labelled psx_official with no corroboration.
  Corrected rule: VERIFIED requires ≥2 distinct agreeing
  sources including one official; a lone official import stays
  UNVERIFIED. Test updated accordingly.
- M1 MEDIUM (fixed): ISIN/identifier match overrode a name
  disagreement with no flag → now PENDING_REVIEW + report,
  and the record never mutates the stored ticker.
- M2 MEDIUM (fixed): conflicting import mutated the ticker and
  wrote symbol history before marking CONFLICTED → conflict
  is now checked FIRST, before any mutation.
- M3 MEDIUM (fixed): ambiguous/conflict re-imports appended
  duplicate quality reports → reports de-duplicated
  (_report_once; a resolved report does not block a genuinely
  recurring issue).
- M4 MEDIUM (fixed, decision recorded): listing_status was
  silently dropped → suspended/delisted/inactive are now
  stored; verification never promotes lifecycle statuses;
  unknown values are recorded as errors and ignored.
- M5 MEDIUM (fixed): identifiers on a matched re-import were
  used for matching but never stored → now stored when new.
- LOW (all addressed): L1 backend alembic.ini cannot locate
  Phase 3/4 revisions → working database/alembic.ini invocation
  documented; L2 empty observed_name counted as agreeing →
  fixed; L3 ISIN check digit not recomputed → documented Phase
  5 concern (accepted); L4 frontend fetched statistics and
  discarded them → now displayed; L5 reconcile() KeyError on
  malformed snapshot → clear ValueError; L6 pytest fake session
  lacks real DB constraints → live-PG adversarial check added
  (accepted as mitigation, not a replacement).

## 11. Cost compliance

**Paid services introduced: ZERO.** Python, Next.js, FastAPI,
PostgreSQL 16.15, Redis (local), Alembic, Pytest, Vitest —
all free/open-source, already present or locally installed.
No paid market-data API, subscription, AI API, hosting, or
storage was used or created. No external account was created
in Phase 4 (ACCOUNT_REGISTER unchanged). Local hardware,
electricity, and internet remain external operating expenses,
disclosed, never represented as free.

## 12. GitHub branch / commit / push

- Branch: `phase-04-company-registry`, created from Phase 3
  tip b22281a.
- Commit: see git log on the branch (Phase 4 work commit,
  verified clean of secrets/.env/credentials/large datasets
  before committing).
- Push: ATTEMPTED after audit (see §13). If blocked, the exact
  error is recorded in docs/development/GITHUB_PUSH_LOG.md as
  BLOCKED; no password/token was asked for in chat and no
  security control was bypassed. No force-push, no push to
  main, no merge to main. Phase 2 branch
  (phase-02-repository-foundation, 016f3c8) and Phase 3 branch
  (phase-03-database-storage, b22281a) remain unpushed from
  earlier phases; main remains untouched at eb6025b.

## 13. Live-test status

- Backend API live on uvicorn port 8003: statistics/companies/
  health all 200 on the empty database; server stopped after
  the check (port 8000 from earlier phase work left untouched).
- Frontend live preview: UNVERIFIED (no browser screenshot
  obtainable by a generic subagent; build evidence only).
- Docker: NOT re-verified in Phase 4 (definition-only from
  Phase 2, registry TLS failure carried forward).
- Playwright: NOT re-verified in Phase 4 (browser download
  failure from Phase 2 carried forward).

## 14. Carried-forward limitations

- Docker definition-only (Phase 2 registry TLS failure);
  Playwright browsers never downloaded (Phase 2).
- Phase 1 gates: G-01 source verification still open for
  SECP/SBP/PBS/Finance Division/World Bank/IMF/FRED and for a
  structured financial-statement source; G-02 licence recording
  (Phase 2 recorded licences for adopted dependencies);
  G-03 count reconciliation unresolved (535+5/37 as of Aug 31,
  2026 vs 522+/37+ as of Dec 31, 2025 vs ~496 vs ~1,029 vs
  1000+ vs ~729 vs 38/37 sectors — never harmonised, different
  dates and universes); G-04 versions pinned in Phase 2 (Ollama
  model unpinned, no benchmark claimed); G-05 SBP/PBS direct
  fetches still UNVERIFIED (parent live-browser retry);
  G-06 FRED gated out of AI training/caching/commercial output
  until full Terms re-read; G-07 MinIO NOT ADOPTED (optional
  only), Redis 8 tri-licence recorded at Phase 2 setup;
  G-08 no measured figures asserted anywhere in Phase 4.
- Phase 5 gate: Phase 5 must NOT treat this registry as a
  population base until a dated official snapshot exists and
  the source_key provenance control is in place; Phase 5 must
  not invent a replacement company list.

## 15. Files changed / added

- backend/app/services/registry/ (normalization, matching,
  importer, verification, reconciliation, sync_config) —
  importer + verification corrected after audit.
- backend/app/models/registry.py + migration
  a909e8449cdd_phase_4_registry_evidence.py.
- backend/app/api/v1/endpoints/registry.py + router wiring.
- backend/tests/test_registry.py (26 tests).
- frontend/app/companies/page.tsx.
- scripts/run_phase4_pg_check.py (with adversarial paths).
- docs/phase-04/ — 14 files: source_research.md,
  registry_architecture.md, normalization_and_matching.md,
  import_pipeline.md, reconciliation_methodology.md,
  data_quality_policies.md, api_documentation.md,
  frontend_documentation.md, sync_configuration.md,
  test_report.md, registry_statistics.md,
  independent_audit.md, phase_04_acceptance_report.md,
  phase_04_completion_report.md (+ source_research_raw/).
- Trackers: PROJECT_STATUS.md, DEVELOPMENT_LOG.md,
  docs/development/DEFECT_REGISTER.md (D-50–D-53 + audit
  findings), MASTER_EXECUTION_LOG.md, GITHUB_PUSH_LOG.md.

## 16. What was NOT done (honest scope boundary)

- No production company/security/sector was populated.
- No scraper was built against psx.com.pk or dps.psx.com.pk.
- No external account was created; no ToS/payment/CAPTCHA
  step was reached or bypassed.
- No broker/order path, no price data, no recommendation, no
  trade — none exists in this phase.
- Phase 5 was NOT started (parent starts it automatically
  after acceptance under the standing phase-to-phase
  authorization).

## 17. Next step

**Phase 5, only after acceptance** — started automatically by
the parent under the user's standing phase-to-phase
authorization (no separate user approval needed inside this
run). Phase 5's gate check must first verify: (a) the Phase 4
registry exists in the actual database (it is currently EMPTY
— population is blocked, see §5), (b) verified company-security
relationships and ticker/security identity mappings (none
exist yet in production), and (c) registry provenance. If the
registry is missing/unreliable/incomplete at that gate, Phase
5 must stop and report the dependency failure and must NOT
invent a replacement company list.
