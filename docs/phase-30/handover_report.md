# PSX Intelligence AI — Final System Acceptance and Handover Report

**Phase 30 of 30. Date: 2026-11-05 (Asia/Karachi).**

**System verdict: PARTIALLY COMPLETE.** Phases 1–3 are COMPLETE; Phases
4–29 are PARTIALLY COMPLETE; Phase 30 is PARTIALLY COMPLETE (its
release gate does not fully pass — see "Phase 30 gate judgement").
COMPLETE is claimed only for features that passed, per the playbook
rule. No verdict from any earlier phase is upgraded in this report, and
**no human sign-off is claimed** (Phase 29 gate G5 is PARTIAL for
exactly that reason).

## Release identity

- Branch: `phase-30-release`, from `phase-29-acceptance` `858e914`.
- Tag: `v0.2.0-handover` (annotated; first tag on this repository —
  no prior tags existed). A handover snapshot, NOT a production
  release.
- Base unmoved: `phase-29-acceptance` `858e914`. Main untouched:
  remote `main` `eb6025b` (README-only, created 2026-11-04, unrelated
  history); local `main` `214a701` never pushed. No PR exists.
- Migration head: `20261104_0024` (unchanged by this phase; no new
  migration, no new tables, no business rows written by this phase).
- Repository: `ZainMushtaq9/advisor` (PUBLIC, default branch `main`,
  no description). `main` branch is UNPROTECTED (GitHub API returns
  404 "Branch not protected") — enabling protection is a recommended
  owner action before any public-release use; this phase does not
  change repo settings.
- This report: `docs/phase-30/handover_report.md`. Companion docs:
  `implementation_specification.md`, `release_checklist.md`,
  `licence_and_source_inventory.md`, `documentation_index.md`,
  `user_guide.md`, `developer_guide.md`, `run_report.md`.

## What this snapshot is — and is not

It IS: a versioned, documented, auditable snapshot of 30 phases of
work, with every claim traceable to a branch, a commit, a test run, or
a live database count; a working local system (backend + dashboard)
that serves only stored, provenance-tagged data through GET-only APIs;
and a complete, honest record of what is missing and what unblocks it.

It is NOT: a production release, a deployment, a merge to `main`, an
approved or published report set, a live-data service, a trading
system, or investment advice. Nothing here executes a trade, sends an
external message, or publishes anything externally — no such path
exists in the code, and no permission name exists that could grant one.

## Six-way separation

### IMPLEMENTED

Everything below exists as code, tests, and docs on the phase branches
listed in the phase table. "Implemented" means built and tested — it
does not mean the underlying data is complete or verified (see
PARTIALLY VERIFIED).

- Company/sector registry engine + API (470 companies, 37 sectors,
  Main Board / Normal Counter only) with evidence rows and LEAP
  sampled verification procedure.
- Market-data engine + API (444 price rows, one trading date),
  validation (10 rejection codes), quality checks, fail-fast ingestion
  (any unknown ticker aborts before any write).
- Technical-indicator framework (62-indicator registry v1.0, pure
  Decimal, coverage with reasons) — 0 calculable values on current data.
- Financial-statement extraction (two independent extractors, page
  maps, auditor-opinion records) for 4 companies, 118 statements,
  2,116 line items.
- Fundamental analysis (36 metric definitions, health layer v1 —
  descriptive only, NOT a credit rating, NOT advice, NOT a signal).
- Valuation (17-method registry; trailing P/E, book values computed
  where inputs allow; DCF/DDM/peer/share-count methods implemented
  and hand-tested on fixtures, NOT_CALCULABLE in production).
- Macro/sector analysis (12 indicators, exposures, regime, events).
- News/events (alias map, dedup, review-worthiness scoring; live
  collection Terms-gated; PSX collector is a gated stub).
- Ownership/actions/breadth/liquidity (HUBC ownership, 5 dividend
  actions with dates NULL, adjustment rules defined_not_applied).
- Forecasting targets, baselines, walk-forward validation (live
  forecasting ABSTAINED on every target at every horizon).
- Risk analytics (22-metric library, controls v1, stress scenarios).
- Decision engine (rules v1; proposals only; execution denied by
  source scan).
- Simulated portfolio construction (3 portfolios, exact reconciliation).
- Backtesting + paper ledger (strategies, metrics, lifecycle engine;
  all production runs NOT_RUNNABLE).
- Agent orchestration (16-agent registry, permissions, untrusted-input
  quarantine, evaluation; LLM-backed execution unavailable).
- RAG knowledge base (3 documents → 943 chunks; deterministic
  full-text retrieval; vector retrieval REGISTERED, NOT IMPLEMENTED).
- Screener (18-filter registry, screener-score-v1, 5 seed screens).
- Alerts (9-rule registry, gating/dedup/quiet/frequency/lifecycle;
  in-app delivery only).
- Reports (8 templates, QA gate, Markdown + HTML + PDF via fpdf2;
  approval is a CLI transition only; NO publish step).
- Dashboard (18 sections, company/report detail, honesty layer:
  quality + computation-status badges, source/date/unit/quality lines).
- Auth + RBAC (5 roles, closed 5-permission list, CLI-only account
  management, security headers, rate limits, append-only audit logs).
- Automation (DB-backed, operator-invoked job framework; NO daemon,
  NO paid scheduler, NO Celery/Redis; 8 jobs, 3 collection jobs
  PAUSED).
- Evaluation (8 datasets, 9 model cards, 5 promotion gates, drift
  policy, golden suite).
- Observability (structured logging + correlation IDs + redaction,
  14 SLOs, 9 source-health rows, exception queue, incident reports,
  performance baselines, playbooks).
- Deployment + operations (ops scripts, systemd units, backup manifest
  with 40 counts + optional GPG encryption, restore drill,
  fresh-environment test, verify_restore.sh three-axis gate).
- Acceptance (15 scenarios, 15 recomputations, 14 defects, 9
  security/licensing/privacy audits, GET-only API + dashboard).
- Release + handover (this phase: handover report, release checklist
  + rollback plan, licence + source inventory, documentation index,
  user guide, developer guide, changelog entry, tag).

### VERIFIED

"Verified" here is used in two strictly separated senses. Do not
conflate them.

**H1-verified (≥2 distinct agreeing sources including one official
source, per rule H1):**

- 6 macro observations, via SBP/PBS cross-publisher agreement
  documented in `docs/phase-10` — with the standing caveat: they rest
  on that documented agreement, NOT on second evidence rows in the
  database, so they must not be treated as H1-verified in the registry
  sense. Everything else in the database is UNVERIFIED or
  PARTIALLY_VERIFIED at best; no registry, price, statement, ratio, or
  valuation row is H1-verified.

**Independently recomputed and matched (recomputation-verified, NOT
H1-verified — the underlying rows stay UNVERIFIED):**

- HUBC gross margin 29,688,160 / 71,126,352 = 0.41740029… vs stored
  0.417400; HUBC trailing P/E 197.24 / 38.26 = 5.1552535… vs 5.155254;
  OGDC trailing P/E 303.63 / 16.98 = 17.88162544… vs 17.881625 (Phase 29
  recomputations, 14 of 15 matched; the 1 mismatch is the expected HBL
  drift, see below).
- All 3 simulated portfolios reconcile exactly to PKR 1,000,000
  capital; paper ledger reconciles exactly.
- Breadth coverage 444/470 = 0.944681; volume median 54,631.5; top-10
  share 49.249694%.
- HBL SFP identity exact both years (2025: 7,219,529,515 +
  488,614,705 = 7,708,144,220; 2024: 5,644,314,783 + 410,798,094 =
  6,055,112,877).
- Screen counts 194/44/1/2/0; alerts 82/6/1 = 89; report census
  541 = 335/199/7; decision completeness HUBC 6/7, OGDC 6/7.
- HUBC close 197.2400 re-read unchanged after every phase run that
  touched it (including after the Phase 18 injection probe, which was
  QUARANTINED).
- System mechanics verified end to end: fresh-clone reproducibility,
  backup/restore drill (three-axis gate), start/stop/healthcheck cycle
  (Phase 28 post-report re-test: 7 s start, pids verified as the real
  uvicorn/next-server, smoke, healthcheck, stop freeing ports).
- Security posture verified by scan (Phase 29, re-verified Phase 30):
  execution identifiers 0, dangerous constructs 0, write routes 0,
  upload endpoints 0, docker invocations 0, tracked datasets 0,
  tracked secrets 0, PII columns 0 (branch-tip boundary, not every
  historical commit).
- The 61-company LEAP sample: every id/ticker/legal-name check passed
  against the live DB (fail-fast mismatches: NONE). This verifies the
  sample's internal consistency, NOT registry-wide verification.

### PARTIALLY VERIFIED

- Registry: 470 companies with evidence (940 DPS + 61 secp_leap rows),
  but all UNVERIFIED; identifiers 0. The derived summary "47/61
  LEAP-NAME-AGREED (77.0%)" is a sample statistic, NOT a status and NOT
  a registry-wide claim. LEAP verifies legal name only (AGREE/DISAGREE/
  NOT_FOUND); CUIN is RECORDED ONLY, never promoted; the INCORPORATED
  badge is OBSERVED ONLY, not DPS "Normal Counter" status.
- Prices: 444 rows on 2026-11-03 from a single dated source (DPS
  Market Summary Closing). A second agreeing source does not exist, so
  no price row can be promoted even if written PSX permission arrives.
- Statements: 4 companies, 118 statements, 2,116 line items, all
  UNVERIFIED (single issuer source each; two-extractor agreement is a
  transcription check, not a second source).
- Ratios, valuations, macro (6 UNVERIFIED rows), news, ownership,
  breadth, risk, decisions, portfolios, screens, alerts, reports: all
  derived from UNVERIFIED inputs, so all carry UNVERIFIED status, never
  higher. Their arithmetic is verified (see VERIFIED); their inputs
  are not.
- Phase 29 acceptance: 12 of 15 scenarios PASS, 14 of 15
  recomputations matched. The 1 mismatched recomputation
  (drift_vs_phase24_baseline: live 4 documents / 118 statements /
  2,116 items vs baseline 3/88/1,316) is exactly the HBL additions —
  the drift SLO working as designed. The baseline update must be
  recorded with this evidence per the Phase 25 rule, not hidden.
- RAG benchmark: r3 6/6 at page level, recall@5 1.0. The r1/r2 history
  (1/6, 2/6) was runs of superseded retrieval code and was NOT
  reproduced after VM replacement #6; the 12 historical rows were NOT
  fabricated. Live count is 6 (r3 only).

### UNAVAILABLE

Capabilities the system does not offer at all (by design or by missing
inputs — never faked, never zero-filled):

- Live PSX collection (adapters BLOCKED or Terms-gated; collection
  jobs PAUSED; handlers are stubs that dead-letter if dispatched).
- Any forecast value (120/120 assessments abstained; point-only values
  without intervals are never stored as forecasts).
- Any user-facing decision value (4/4 WITHHELD).
- Any backtest metric (5/5 runs NOT_RUNNABLE; 0 return intervals).
- Any technical-indicator value (0 calculable; warm-ups unmet).
- Any share-count-derived value (P/B, P/S, market cap, EV multiples,
  dividend yield — no authoritative shares outstanding or par value).
- DCF/DDM/peer-median valuations (no source-backed WACC, growth,
  forecasts, or share counts).
- Mean-variance portfolios (no validated expected returns, no
  covariance matrix — 0 return observations).
- Series risk metrics (volatility, beta, drawdown, VaR95/ES95 — warm-ups
  unmet; SBP policy rate 12.00% is a policy rate, NEVER used as a
  T-bill rate).
- Advances/declines/unchanged, new highs/lows, turnover distribution
  (previous_close NULL, 1 date, turnover NULL).
- Investor flows (no verified series), free-float measures
  (Terms-gated), adjusted price series (no ex-dates).
- Vector retrieval (registered, not implemented — no verified local
  embedding model).
- LLM-backed orchestration (no verified local/open-weight LLM;
  rule-based fallback only).
- External publication, external notifications, report approval via
  web, token-gated approval (CLI transition only, procedural).
- Live auth accounts (tables empty by decision); enforced-mode
  production proof; multi-instance rate limiting; CI-in-CI.
- A single consolidated API reference document and a single
  consolidated post-Phase-2 architecture diagram (endpoint files +
  per-phase docs are the reference — gap stated plainly).
- Any HBL-derived analysis beyond statements and market-wide figures
  (ratios, valuations, decisions-with-evidence, positions, backtests,
  RAG answers, statement-derived alerts, HBL dossier/earnings/valuation
  reports) — pending the Phases 8+ HBL re-runs.

### BLOCKED

Capabilities with a named blocker and an exact unblocker. Nothing here
is "in progress" in a way that implies it will resolve itself.

| Blocked item | Exact unblocker |
|---|---|
| GEM (5) + Non-Compliant/Winding-Up (93) capture | Written PSX permission evidence (user-owned) |
| Full-470 VERIFIED promotion | Full manual LEAP run (~16–40h) or approved SECP bulk route + field-scoped promotion model in code + separate approval |
| More trading days (Phases 5/6/13/14/17) | Written PSX permission evidence (user-owned) — Terms gate, not a technical limit |
| PSX announcement collection (Phases 11/12/21) | Written PSX permission evidence (user-owned) |
| Free-float data | Written PSX permission evidence (user-owned) |
| HBL chain (fundamentals → valuations → decisions → reports) | Phases 8+ HBL re-runs, sequenced after Phase 30, parent-approved branch strategy (merge or cherry-pick of `phase-07-hbl-extraction` code) |
| Price-coverage, session-gap, previous-close SLOs (3 of the 4 unmet SLOs) | Written PSX permission evidence + more trading days |
| News-coverage SLO (3/470 vs 0.10 threshold) | Written PSX permission evidence + announcement collection |
| Vector retrieval (RAG card, vector metric evaluable) | Verified local embedding model |
| LLM-backed orchestration | Verified local/open-weight LLM |
| First APPROVED report | Internal review decision (CLI transition only, no web approval by design) |
| First live auth account (enforced mode currently fail-closed, 401) | Parent/user decision to create it with the CLI-only tool |
| Enforced-mode production proof, backup-encryption key, service install, host cron, dependency audit with network, frontend token support, multi-instance rate limiting | Real deployment decision (operator) |
| Token-gated report approval (D-12) | A phase brief that covers it (belongs to no brief so far) |
| Permanent surrogate-id fixes (D-04) | A phase brief that covers it (name-based sector resolution + ticker-based news publication-date mapping with fixture tests) |
| Merge to main | Separate user approval + unrelated-histories decision; no PR exists |
| CI-in-CI | Main/development push or PR (separate approval) |
| KSE-100 completeness claim | Verified membership list (only if a claim is ever made; none is made) |
| LUCK FY2026 extraction | DPS filing-download terms (written evidence) or an issuer-hosted URL |
| October CPI YoY official read | Live-browser fetch of the PBS monthly review PDF |

**The single largest blocker is the Terms gate.** The permission email
was sent 2026-11-04 from 5439 to marketdatarequest@psx.com.pk (message
`1a1a66ca3ef85eeb`); a reply arrived but was permanently deleted by
the user including from trash, so its wording is unverifiable and does
NOT clear the gate; no resend was sent (user decision 2026-11-04
18:58 PKT, when the user declined the resend, ordered the price commit,
and took the permission side onto themselves). **Do NOT claim
clearance. Do NOT send PSX any email without a new user instruction.**
A 6-hourly reply-watch cron (`psx-permission-reply-watch`) checks 5439
for any `from:psx.com.pk` message and stays silent unless one arrives.

### PLANNED (not started, not promised a date)

- HBL Phases 8+ re-runs (fundamentals, valuation with the bank
  residual-income model, macro, news, ownership, forecasts, risk,
  decisions, portfolios, backtests, RAG indexing of the 411-page HBL
  report, screener, alerts, reports) + observability baseline update
  for the new HBL documents/statements, recorded with evidence.
- Permanent surrogate-id fixes (D-04) and token-gated report approval
  (D-12), if a future brief covers them.
- Register consolidation #2 (parent task): append the LEAP load
  outcome, HBL blocked report, Phases 8–30 outcomes, recoveries #5–#7,
  D-05/D-13 fixes, and the Phase 28 post-report follow-up to
  `PHASE_COMPLETION_REGISTER.md`, `PROJECT_EXECUTION_STATE.md`, and
  `MASTER_EXECUTION_LOG.md` (last consolidated at `59834f1`).
  `GITHUB_PUSH_LOG.md` intentionally not updated (gap noted since
  Phase 4).
- Wider-company / KSE-100 expansion (per-company source verification
  pass) if the user orders it.
- PyMuPDF AGPL review (D-14) before any public hosted distribution or
  redistribution (trigger-based; no current violation).
- Dependency audit with network (pip-audit/safety) before any
  production deployment.
- Any future execution proposal: a new design decision requiring
  separate approval (never an extension of this system by default).

## Phase-by-phase status (all evidence-based)

Verdicts use only COMPLETE / PARTIALLY COMPLETE / BLOCKED / FAILED.
"Branch tip" is the parent-verified remote SHA. Main is untouched
throughout (`eb6025b`).

| Phase | Verdict | Branch tip | Headline evidence |
|---|---|---|---|
| 1 Specification | COMPLETE (as checkpoint) | (67 files; 8 root trackers + 47 in `docs/phase-01/`) | 21 modules, 18 agents + orchestrator, 33 entities, 30 phases. Gates G-01–G-08 remain open. |
| 2 Repository foundation | COMPLETE (amended criteria) | `phase-02-repository-foundation` `016f3c8` | Next.js 16.4.5 + React 19.3.0; FastAPI; PostgreSQL probe; Redis 7.0.15 + Celery live proof; backup/restore verified. Docker gap closed by user decision (NOT verified). Playwright smoke 2/2 (specs untracked, NOT committed). CI-in-CI unverified. |
| 3 Database + storage | COMPLETE | `phase-03-database-storage` `b22281a` | 54 model tables; manifests/SHA-256/quarantine. Audit PASS WITH LIMITATIONS (0 CRITICAL, 3 HIGH, 9 MEDIUM, 10 LOW). PyArrow NOT installed — no Parquet dataset claimed. |
| 4 Company registry | PARTIALLY COMPLETE | `phase-04-company-registry` `0f4342f`; `phase-04-completion` `c078c0b`; `phase-04-sampled-verification` `9204632`; `phase-04-leap-load` `eb2e331` | 470 companies / 470 securities / 37 sectors / 1,001 evidence rows (940 DPS + 61 secp_leap), all UNVERIFIED, identifiers 0. Main Board/Normal only. LEAP sample 61: AGREE 47 / DISAGREE 5 / NOT_FOUND 9 / BLOCKED 0. |
| 5 Market data | PARTIALLY COMPLETE | `phase-05-snapshot-import` `ffc9d61`; `phase-05-completion` `f4b703d`; `phase-05-revisit` `e281c73` | 444 rows, one date 2026-11-03, all UNVERIFIED, previous_close/turnover/source_timestamp NULL all. 13 rejected + 13 absent, never zero-filled. Sole blocker: written PSX Terms resolution (and even that would NOT promote any row — H1 needs a second agreeing source). |
| 6 Technical analytics | PARTIALLY COMPLETE | `phase-06-technical-analytics` `6efede9`; `phase-06-completion` `e556806`; `phase-06-revisit` `85f4a72` | 62-indicator registry v1.0; 470 assessed; 124 error rows (insufficient_warmup 61 + missing_data 63); 0 values, 0 signals. daily_return missing_data(470) — blank previous_close; more trading days alone do NOT unblock it. |
| 7 Financial statements | PARTIALLY COMPLETE | `phase-07-financial-statements` `366ed32`; `phase-07-remainders` `59834f1`; `phase-07-hbl-followup` `f53cde8` (blocked-at-download report, superseded) | Before HBL: 3 companies, 88 statements, 1,316 items, 3 opinions, all UNVERIFIED. Two independent extractors, zero mismatches, all 6 maps; first audit FAIL → fixed → re-audit PASS. |
| 7b HBL extraction (follow-up) | COMPLETE | `phase-07-hbl-extraction` `42bd8e2` | Consolidated audited FY ended 31 Dec 2025, publication 2026-03-03, KPMG Taseer Hadi & Co. unmodified, UDIN AR202510201HsNS5gUWD. Documents 4, statements 118 (+30), items 2,116 (+800), opinions 4. HBL PAT 66,763,916 / 57,804,659 (Rs '000s), EPS 45.48 / 39.85. All HBL rows UNVERIFIED. Source defects recorded, never adjusted. |
| 8 Fundamental analysis | PARTIALLY COMPLETE | `phase-08-fundamental-analysis` `9969f5a` | 36 definitions, 108 values, 24 health rows, 8 warnings, 108 sector profiles, all UNVERIFIED. Health-v1 descriptive only. |
| 9 Valuation | PARTIALLY COMPLETE | `phase-09-valuation` `f9de2cc` | 51 rows (7 computed, 41 insufficient, 3 not_applicable), all UNVERIFIED. HUBC trailing P/E 5.1553x; OGDC interim-period multiple 17.8816x; book-value totals (not per-share, not market fair value). |
| 10 Macro / sector | PARTIALLY COMPLETE | `phase-10-macro-sector` `9df2266` | 12 indicators (6 VERIFIED via documented SBP/PBS agreement — see caveat — 6 UNVERIFIED), 6 exposures, 12 macro sector profiles, 1 regime (tightening), 4 events. |
| 11 News / events | PARTIALLY COMPLETE | `phase-11-news-events` `b6c6026` | 8 sources, 1,376 aliases, 7 events, 3 event-companies. Coverage 3/470. Live collection Terms-gated. |
| 12 Ownership / actions / breadth | PARTIALLY COMPLETE | `phase-12-ownership-actions-breadth` `a58a104` | 34 ownership rows (HUBC), 5 dividend actions (dates NULL), 4 adjustment rules (defined_not_applied), 50 breadth rows, 889 liquidity rows, 0 investor flows. |
| 13 Forecasting | PARTIALLY COMPLETE | `phase-13-forecasting` `9eb2f41` | 48 targets, 116 snapshots, 120 assessments — ALL insufficient_inputs, 0 computed. Live forecasting ABSTAINED. |
| 14 Risk management | PARTIALLY COMPLETE | `phase-14-risk-management` `04ad858` | 22 definitions, 81 values (46 computed + 35 insufficient), 17 flags, 5 controls/7 checks (single-name cap BREACH on the SIMULATED portfolio only), 5 stress scenarios/10 results. |
| 15 Decision engine | PARTIALLY COMPLETE | `phase-15-decision-engine` `9f78fb4` | 1 rule, 4 decisions, 0 outcomes, ALL user-facing WITHHELD, confidence caps at LOW. Execution denied (source scan 0 hits). |
| 16 Portfolio construction | PARTIALLY COMPLETE | `phase-16-portfolio-construction` `cb2a70c` | 3 SIMULATED portfolios (hypothetical PKR 1,000,000, all reconcile), 7 holdings, 5 exclusions, 7 sector allocations, 3 comparisons. Mean-variance NOT_CALCULABLE. |
| 17 Backtesting | PARTIALLY COMPLETE | `phase-17-backtesting` `5bea951` | 5 strategies, 5 runs ALL NOT_RUNNABLE, 55 metrics (0 computed), 13 ledger entries (PKR 1,000,000.00, SIMULATION), 7 bias rows, 0 paper orders. |
| 18 Orchestration | PARTIALLY COMPLETE | `phase-18-orchestration` `6b8ba4d` | 16 agents, 1 demo run COMPLETED, injection probe QUARANTINED, HUBC close 197.2400 verified unchanged, 6 tasks, 6 audit logs, 6 evaluations 6/6 PASS. LLM-backed execution unavailable. |
| 19 RAG knowledge base | PARTIALLY COMPLETE | `phase-19-rag-knowledge-base` `3cd98e7` | 3 documents, 943 chunks, benchmark r3 6/6 at page level (r1/r2 not reproduced after replacement #6; live count 6), access audits 9. Vector retrieval REGISTERED, NOT IMPLEMENTED. |
| 20 Screener | PARTIALLY COMPLETE | `phase-20-screener` `c91acb1` | 5 screens, 1,418 results (241 MATCH). Technical screen 0 MATCH. Matches are filter results, not opportunities. |
| 21 Alerts | PARTIALLY COMPLETE | `phase-21-alerts` `dbeee4a` | 9 rules, 1 preference (in-app only, external consent False), 89 alerts (82/6/1), 89 deliveries, 18 runs. False-positive rate NOT_MEASURABLE (all NEW). |
| 22 Reports | PARTIALLY COMPLETE | `phase-22-reports` `45d08ec` | 8 templates, 22 DRAFT reports (541 figures: 335 computed, 199 insufficient, 7 not_applicable), QA gate, no publish step. |
| 23 Dashboard | PARTIALLY COMPLETE | `phase-23-dashboard` `6662d34` (repair `a5077e0`) | Full product IA (18 sections), company/report detail, honesty layer. Backend 348 + vitest 11 + Playwright 22 passed. Repair: Phase 8/9/10 APIs ticker-keyed after the surrogate-id shift broke them. |
| 24 Security | PARTIALLY COMPLETE | `phase-24-security` `f648bd5` (migration 0020) | Auth + RBAC (5 roles), CLI-only account management, no login over HTTP, append-only audit logs. Backend 368 passed. Auth tables empty by decision. |
| 25 Automation | PARTIALLY COMPLETE | `phase-25-automation` `a129614` (migration 0021) | DB-backed job framework, no daemon, 8 jobs (3 collection jobs PAUSED), 71 runs, drift 0. Backend 394 passed. |
| 26 Evaluation | PARTIALLY COMPLETE | `phase-26-evaluation` `b6f007c` (migration 0022) | 8 datasets, 9 model cards all NOT_PROMOTED, 5 gates all NOT_MET, 44 metrics (32 computed), golden suite 14/14. 0 predictions, 0 matured labels, 0 outcomes. Backend 408 passed. |
| 27 Observability | PARTIALLY COMPLETE | `phase-27-observability` `544fecc` (migration 0023) | Structured logging + correlation IDs + redaction, 14 SLOs (10 met, 4 unmet), 9 source health (market_prices stale), 6 exceptions open, 3 incidents resolved, performance baselines. Backend 419 passed. |
| 28 Deployment | PARTIALLY COMPLETE | `phase-28-deployment` `b791b7d` (no migration, head 0023) | Ops scripts, systemd units, backup manifest 40 counts + optional GPG encryption, restore drill, fresh-environment test, `.env.example` secured to CHANGEME. Backend 426 passed. Post-report follow-up: backgrounded pre-fix-era start/smoke/stop run (219 s, frontend HTTP 000, servers already gone) matched the pre-fix subshell-without-exec bug and/or concurrent worktree cleanup; a re-test of the committed fixed script reproduced the clean cycle (7 s start, pids verified, smoke, healthcheck, stop) — verdict unchanged. |
| 29 Acceptance | PARTIALLY COMPLETE | `phase-29-acceptance` `858e914` (migration 0024) | 15 scenarios (12 PASS / 0 FAIL / 1 BLOCKED / 2 NOT_EVALUABLE), 15 recomputations (14 matched / 1 expected HBL drift), 14 defects (0 critical, 0 high), 9 security/licensing/privacy audits all PASS. Backend 448 passed. VM replacement #7 recovered before this phase (see below). |
| 30 Release + handover | PARTIALLY COMPLETE | `phase-30-release` (this branch; tag `v0.2.0-handover`) | This report + release checklist + rollback plan + licence/source inventory + documentation index + user/developer guides + changelog entry + tag. Fresh-clone reproducibility, backup/restore drill, final audit scans, independent recomputations, live API smoke — see `run_report.md`. |

## Acceptance gates

### Phase 29 gate (carried verbatim — no upgrade, no rewording)

Gate summary: G1 NOT_MET, G2 MET, G3 MET, G4 MET, G5 PARTIAL.

| Gate | Judgement | Meaning |
|---|---|---|
| G1 | NOT_MET | HBL chain blocked (statements loaded; 0 fundamentals, 0 valuations, decision predates statements, 0 reports). |
| G2 | MET | 0 critical / 0 high defects. |
| G3 | MET | No look-ahead or fabrication. |
| G4 | MET | Repo clean. |
| G5 | PARTIAL | Independent evidence complete; human sign-off pending — no human sign-off is claimed. |

No gate item was reworded to force a pass.

### Phase 30 gate (playbook's five mandatory items, judged honestly)

| Gate item | Judgement | Evidence / limitation |
|---|---|---|
| Release is reproducible from the standalone repository | PARTIALLY MET | Proven from the `phase-30-release` branch via fresh clone (see `run_report.md`). NOT proven from `main` — `main` is README-only with unrelated history and was never merged to. The "standalone repository" release is therefore the branch snapshot, not `main`. |
| All phase statuses are evidence-based | MET | Every phase above carries an exact branch + commit + counts; every count in this report was re-read from the live DB or the branch tip during Phase 30. |
| Security, data licensing and backups are reviewed | MET | Phase 24/28/29 audits + Phase 30 re-verification (scans, licence inventory, backup/restore drill). Open review item D-14 (PyMuPDF AGPL) is a trigger-based review, not a violation. |
| No paid dependency or hidden cost is introduced | MET | All software free/open-source (see licence inventory). Hardware, electricity, and internet are external operating expenses, disclosed, never called free. |
| Final report distinguishes implemented, tested, unavailable and planned features | MET | This report's six-way separation + phase table + defect register. |

Because one gate item is partial, the Phase 30 gate does NOT fully
pass. Phase 30 verdict: PARTIALLY COMPLETE. This is consistent with
the playbook rule: mark COMPLETE only for features that passed.

## Final acceptance workflows (playbook's ten, mapped to evidence)

1. **Company and security** — PASS (within scope): discover from the
   registry (470, Main Board/Normal), verify identity via evidence
   rows + LEAP sample, preserve aliases (1,376), prove the
   data-quality trail (evidence rows carry source + timestamps).
   Limitation: identity is UNVERIFIED registry-wide; LEAP covers a
   61-company sample only.
2. **Market data** — BLOCKED as a live workflow: no genuine allowed
   observation can be collected today (live adapters BLOCKED,
   collection jobs PAUSED, Terms gate). What exists is the dated-file
   route (444 rows, 2026-11-03) with raw source preserved (gitignored
   mapped CSV), OHLCV validated, idempotent storage, timestamps and
   quality shown. Do not present the dated snapshot as live collection.
3. **Financial disclosure** — PASS (within scope): discover a real
   issuer report (HBL CY2025 via the issuer IR page as a normal
   browser visitor), extract statement values, link each to its exact
   page (page maps), verify via two extractors + independent audit,
   store with units (PKR thousands; EPS in Rupees) and publication
   date (2026-03-03). Limitation: 4 companies only; DPS filings are
   discovery-only.
4. **Fundamentals** — PARTIALLY (recompute-verified, inputs
   UNVERIFIED): ratios calculated from stored records, independently
   recomputed (HUBC gross margin, P/E — see VERIFIED), source line
   items and formula shown. Limitation: inputs are UNVERIFIED, so no
   ratio is H1-verified.
5. **Valuation** — PARTIALLY: appropriate models calculated with dated
   assumptions (trailing P/E with publication-date discipline;
   sensitivity at ∓10% for HUBC), limits shown; invalid/inapplicable
   models rejected (share-count, DCF/DDM/peer methods
   NOT_CALCULABLE with reasons). Bank residual-income model exists
   for HBL but has NOT been run (HBL re-runs pending).
6. **Macro/news** — PARTIALLY: allowed official observations preserved
   with publication time and revision handling (SBP/PBS reads; macro
   events with VERIFIED/PARTIALLY_VERIFIED/UNVERIFIED marks);
   exposures mapped only where evidence-backed (6 exposures).
   Limitation: no live collection; news coverage 3/470.
7. **Forecasting** — NOT AVAILABLE as generation: no point-in-time
   forecast can be generated today (all 120 assessments abstained for
   lack of series length). The policy is implemented and tested:
   evaluate only after the outcome horizon matures (matured labels 0
   because the latest price date equals the origin). A forecast
   feature that cannot show uncertainty is refused, not shipped.
8. **Decision/risk** — PARTIALLY: explainable research conclusions
   exist (HUBC/OGDC HOLD_CANDIDATE, NML/HBL INSUFFICIENT_EVIDENCE)
   with supporting and contrary evidence preserved as conflicts (6
   total, never averaged), confidence limitations stated (caps at
   LOW), risk constraints applied (controls, stress). Limitation:
   user-facing values are WITHHELD; outcomes 0.
9. **Portfolio** — PASS (as simulation): simulated portfolios with
   valid universe/quotes (eligibility probes: ZZZZ NOT_IN_UNIVERSE,
   AGLNCPS IN_UNIVERSE_NO_QUOTE), reconciled weights (exact to
   PKR 1,000,000), no real trade execution (execution scan 0 hits).
10. **Operations** — PASS: stop/restart via ops scripts (re-proven
    Phase 28 follow-up), jobs recovered via operator-invoked run-due
    (bounded catch-up, checkpoints), backup restored via the
    three-axis gate (re-proven Phase 30 drill), logs inspected via
    structured logging + correlation IDs, application and data
    integrity verified (counts + recomputations, Phase 30).

## Live data census (re-read 2026-11-05; Phase 30 writes no business rows)

| Table group | Count | Quality / note |
|---|---|---|
| companies / securities / sectors | 470 / 470 / 37 | All UNVERIFIED; Main Board / Normal only |
| registry_evidence | 1,001 | 940 DPS + 61 secp_leap |
| company_identifiers | 0 | CUINs recorded only, never promoted |
| market_prices | 444 | One date 2026-11-03, all UNVERIFIED, previous_close NULL all |
| trading_sessions / index_prices | 0 / 0 | No sessions stored (Terms-gated) |
| financial_documents / statements / line items / opinions | 4 / 118 / 2,116 / 4 | All UNVERIFIED; HUBC 8 / NML 56 / OGDC 24 / HBL 30 statements |
| technical runs / errors / values | 1 / 124 / 0 | 0 calculable values |
| fundamental definitions / values / health / warnings / sector profiles | 36 / 108 / 24 / 8 / 108 (+12 macro) | All UNVERIFIED |
| valuations | 51 | 7 computed, 41 insufficient, 3 not_applicable; all UNVERIFIED |
| economic_indicators / exposures / regimes / events | 12 / 6 / 1 / 4 | 6 VERIFIED (caveat above), 6 UNVERIFIED |
| news_sources / aliases / events / event-companies | 8 / 1,376 / 7 / 3 | Coverage 3/470 |
| ownership / corporate actions / adjustment rules / breadth / liquidity / investor flows | 34 / 5 / 4 / 50 / 889 / 0 | HUBC ownership; dividend dates NULL |
| forecast targets / snapshots / assessments | 48 / 116 / 120 | ALL insufficient_inputs, 0 computed |
| risk definitions / values / flags / controls / checks / stress scenarios / results | 22 / 81 / 17 / 5 / 7 / 5 / 10 | 46 computed + 35 insufficient values |
| decision rules / decisions / outcomes | 1 / 4 / 0 | All user-facing WITHHELD |
| simulated portfolios / holdings / exclusions / sector allocations / comparisons | 3 / 7 / 5 / 7 / 3 | All SIMULATED, reconciled |
| backtest strategies / runs / metrics / ledger / bias / paper orders | 5 / 5 / 55 / 13 / 7 / 0 | All runs NOT_RUNNABLE |
| agent definitions / orchestration runs / tasks / audit logs / evaluations | 16 / 1 / 6 / 6 / 6 | 6/6 PASS; LLM fallback only |
| rag documents / chunks / benchmark cases / benchmark results / access audits | 3 / 943 / 6 / 6 / 9 | r3 only; vector retrieval not implemented |
| screen definitions / runs / results | 5 / 5 / 1,418 | 241 MATCH |
| alert rules / preferences / alerts / deliveries / runs | 9 / 1 / 89 / 89 / 18 | In-app only; false-positive rate NOT_MEASURABLE |
| report templates / reports / figures / sections / exports | 8 / 22 / 541 / 188 / 66 | All DRAFT; 0 approved, 0 published externally |
| job definitions / runs | 8 / 71 | 3 collection jobs PAUSED; 0 stuck, 0 dead letters |
| model cards / evaluation metrics | 9 / 44 | All cards NOT_PROMOTED; 32 computed metrics |
| SLO definitions / measurements / source health / exceptions / incidents / performance probes | 14 / 14 / 9 / 6 / 3 / 13 | SLOs 10 met, 4 unmet; 1 stale source (market_prices) |
| auth users / tokens / audit logs | 0 / 0 / 0 | Empty by decision; enforced mode fail-closed |
| acceptance runs / scenarios / recomputations / defects | 1 / 15 / 15 / 14 | 12 PASS / 1 BLOCKED / 2 NOT_EVALUABLE; 14 matched / 1 expected drift; 0 critical, 0 high |
| data_sources | 19 | Provenance rows (incl. secp_leap, not official secp) |
| migration head | `20261104_0024` | Phase 29 acceptance tables are the latest |

## Quality, provenance, and governance rules (binding on all future work)

- Rule H1: VERIFIED requires ≥2 distinct agreeing sources including
  one official source (`psx_official`, `secp`); PARTIALLY_VERIFIED is
  ≥2 agreeing without official; single source is UNVERIFIED.
  Same-publisher pages (e.g. DPS + PSX homepage) are NOT distinct
  sources. `secp_leap` rows are deliberately NOT the official `secp`
  key, so promotion code can never promote from LEAP rows alone.
- Every record carries source, source timestamp, collected-at, and
  freshness; market timestamps are Asia/Karachi; fetch time is never a
  source timestamp; stale is flagged, never presented as live; missing
  sessions are recorded, never estimated or zeroed; conflicts are kept
  side-by-side, never silently merged; raw is separate from processed;
  previous observations and published statements are never overwritten
  (revisions are new versions).
- Synthetic/test data is always labelled and separate.
- Forecasts are probabilistic only (1d/1w/1m/3/6/12m horizons) with
  uncertainty; BUY/HOLD/SELL/WATCHLIST are probabilistic proposals
  only; no guaranteed returns; no fabricated prices, statements, or
  history; deterministic Python computes all financial numbers.
- No real trades, no broker/order path. No Docker. PKR 0 / free and
  open-source only for software; local hardware, electricity, and
  internet are external operating expenses, disclosed, never called
  free.
- Git: one branch per phase; base tips never moved; no merge to main
  without separate approval; no force-push, no history rewrite; push
  only verified content and verify the remote SHA; gitignored CSVs
  and downloaded PDFs are NEVER committed.
- Surrogate-id rule: resolve identity by ticker, never by hardcoded
  company id (current HUBC 759, NML 864, OGDC 873, HBL 747).

## Security, licensing, and backup review (Phase 30 re-verification)

- Security: Phase 24 RBAC + Phase 29 audits + Phase 30 scans (see
  `run_report.md`). No execution identifiers, no write routes, no
  upload endpoints, no tracked secrets, no PII columns at branch tips.
  Auth tables empty by decision; enforced mode fail-closed. Open
  items: D-07 (no live accounts), D-10 (frontend token support),
  D-12 (token-gated approval), D-14 (PyMuPDF AGPL review trigger).
- Licensing: all software free/open-source (see
  `licence_and_source_inventory.md`). No paid dependency, no hidden
  cost. Data licensing is the binding constraint: the Terms gate is
  NOT cleared, and that single fact gates GEM/Non-Compliant capture,
  announcement collection, free-float data, more trading days, and
  any VERIFIED promotion.
- Backups: manifest-based backups (40 key-table counts since Phase
  28) with optional GPG encryption (no persistent key — operator
  decision, D-09); restore refused over live without
  `ALLOW_LIVE_RESTORE=1` and a verified backup; three-axis restore
  gate re-proven in the Phase 30 drill. Retention: 30 valid backups,
  never the newest, never invalid-manifest directories. Latest
  pre-Phase-30 backup: `2026-11-04T1230-PKT` (manifest SHA verified;
  all 7 VM-replacement recoveries started from it).

## Known limitations (honest list — if it is not here, check the phase docs)

1. Terms gate not cleared (single largest blocker).
2. One trading date; no returns, technicals, advances/declines.
3. Four statement companies (three with analysis, HBL statements only).
4. No share counts → no P/B, P/S, market cap, EV, dividend yield.
5. No DCF/DDM/peer valuations; no mean-variance portfolios.
6. Forecasts abstained; decisions WITHHELD; backtests NOT_RUNNABLE.
7. News coverage 3/470; no live collection; no investor flows.
8. No verified local LLM or embedding model.
9. No live accounts; no enforced-mode production proof; no host cron;
   no multi-instance rate limiting; no CI-in-CI.
10. Registers stale since `59834f1` (consolidation #2 owed by parent).
11. No consolidated API reference or post-Phase-2 architecture diagram.
12. RAG benchmark history partial (r3 only; r1/r2 never re-fabricated).
13. `main` unprotected; no merge to main; no PR.
14. Surrogate-id traps remain (D-04); temporary-patch + revert is the
    documented workaround until a brief covers permanent fixes.
15. Statement freshness 128 days (within the 180-day SLO, but the
    newest statement period ends 2025-12-31 for HBL and 2026-06-30 for
    HUBC; NML's latest period end is 2025-03-31 and is flagged stale
    by the risk layer).

## Next-version roadmap (PLANNED, no dates promised)

1. HBL Phases 8+ re-runs (see batch spec below) + observability
   baseline update with evidence.
2. Written PSX permission evidence → unpause collection jobs, capture
   GEM/Non-Compliant, collect announcements, obtain free-float data,
   add trading days (which then unlock returns, SMA(5), forecast
   intervals, volatility/beta/Sharpe/AR(1), VaR/ES at 2/5/11/30/251
   observations respectively).
3. Share-count data → P/B, P/S, market cap, EV multiples, dividend
   yield, mean-variance.
4. Permanent surrogate-id fixes (D-04) + token-gated approval (D-12).
5. Verified local embedding model → vector retrieval; verified
   local/open-weight LLM → LLM-backed orchestration.
6. KSE-100 / wider-company expansion (per-company source verification).
7. First live admin account + internal review for the first APPROVED
   report (decisions, then code only if a brief covers token-gating).
8. Real deployment decision (enforced-mode proof, backup-encryption
   key, dependency audit with network, frontend token support,
   multi-instance limiting, branch protection, CI-in-CI) + merge to
   main (separate approval + unrelated-histories decision).
9. Register consolidation #2 (parent task, immediately after Phase 30).

## Pending decisions (nothing here is decided by this report)

- First live auth account (CLI-only creation, parent/user decision).
- Internal review decision for the first APPROVED report.
- Real deployment decision (see roadmap item 8).
- Merge to main (separate approval + unrelated-histories decision).
- HBL re-run batch strategy (merge or cherry-pick of
  `phase-07-hbl-extraction` code into the phase lineage, parent
  approval of strategy).
- Any future execution proposal (new design decision, separate
  approval — never an extension of this system by default).
- Any PSX email (no email without a new user instruction; the
  reply-watch cron handles an incoming reply only).

## Operations summary (what the operator does)

Start/stop/healthcheck/status via `ops/` (jobs are NOT started by
`start.sh`); jobs via `scripts/run_jobs.py` (operator-invoked,
bounded catch-up, checkpoints); reports via `scripts/run_reports.py`
(dry-run default); approval via the report CLI only (procedural, not
token-gated); backup via `database/backup.sh`; restore into a scratch
database via `database/restore.sh` + `database/verify_restore.sh`
(never over live without `ALLOW_LIVE_RESTORE=1` and a verified
backup); incidents via `docs/phase-27/incident_playbooks.md` +
`ops/README.md` (no external contact; operator is the user; include
the `X-Correlation-ID` header, run id, and exact command — never a
secret). VM-replacement recovery recipe: see `release_checklist.md`
(rollback plan, item 4) and `developer_guide.md`.

## What is NOT claimed (explicit)

- No COMPLETE system verdict. No production release. No deployment.
- No human sign-off (G5 PARTIAL). No approved or published reports.
- No VERIFIED registry, price, statement, ratio, or valuation row
  (except the 6 macro rows under their documented caveat).
- No live data, no live collection, no real-time anything: the newest
  price date is 2026-11-03 and market_prices is STALE by its own
  1-day threshold.
- No accuracy guarantee, no return promise, no investment advice.
- No CI-in-CI, no branch protection, no hosted demo.
- No claim that the 470-row snapshot, the price CSV, or any issuer
  PDF is in the repository — all are gitignored and absent from every
  branch tip (verified by scan).
- No claim that r1/r2 RAG history, GEM/Non-Compliant data,
  free-float data, share counts, or KSE-100 membership exist — they do
  not.

## HBL Phases 8+ re-run batch (spec for the post-Phase-30 work)

Goal: give HBL the same per-phase treatment the other three companies
have, under the banking rule. Branch strategy needs parent approval
(merge or cherry-pick of `phase-07-hbl-extraction` code into the phase
lineage — the extraction commit `42bd8e2` sits on a branch from
`b6f007c`, not on the phase lineage tip).

1. Phase 8 re-run: banking-appropriate ratios only (no industrial
   ratios blindly applied to a bank); health layer descriptive only.
2. Phase 9 re-run: BANK residual-income model for HBL (mandatory);
   industrial models NOT applied to HBL. Trailing P/E only if a
   valid, dated EPS exists (HBL EPS 45.48 for FY2025, published
   2026-03-03, price date 2026-11-03 — publication-date discipline
   applies).
3. Phase 10 re-run: HBL macro exposures (commercial-banks sector).
4. Phase 11 re-run: HBL news events from stored rows only (earnings
   2026-03-03 publication; no live collection).
5. Phase 12 re-run: HBL ownership/actions/breadth from the annual
   report (dividends with dates only if printed, else NULL).
6. Phase 13 re-run: HBL forecast targets + assessments (expect
   abstention on the same series-length grounds unless new price
   days exist).
7. Phase 14 re-run: HBL risk values, flags, controls, stress.
8. Phase 15 re-run: HBL decision (replacing the predating
   SCREEN_NOT_RUNNABLE/no_statements decision); user-facing stays
   WITHHELD unless the rules + confidence allow otherwise — do not
   force issuance.
9. Phase 16 re-run: HBL eligibility in portfolios (quote 286.16 on
   2026-11-03 is ELIGIBLE evidence; inclusion follows the rules, not
   availability).
10. Phase 17 re-run: HBL backtest (expect NOT_RUNNABLE on one price
    observation; do not invent a series).
11. Phase 18 re-run: orchestration evidence for HBL (no new agents
    unless a brief requires them).
12. Phase 19 re-run: index the 411-page HBL report (943 chunks become
    943 + HBL chunks); benchmark honesty preserved (new cases only
    from stored rows).
13. Phase 20 re-run: screener (HBL in the cheap_profitable /
    dividend_payers logic only where its filters genuinely apply;
    technical screen stays 0 MATCH while values are 0).
14. Phase 21 re-run: HBL statement-derived alerts (earnings
    disclosure 2026-03-03, subject to the 90-day staleness window and
    review outcome — do not force an alert for a stale event).
15. Phase 22 re-run: HBL dossier, earnings update, valuation report
    (banking faces; QA gate; all DRAFT; no publish step).
16. Phase 26/27 follow-ups: evaluation metrics + observability run
    showing the drift vs the Phase 24 baseline WITH the baseline
    update recorded with evidence (per the Phase 25 rule).
17. Acceptance: a Phase 29-style re-run of the HBL chain scenario
    (expect it to flip from BLOCKED only if every link genuinely
    computes — do not force it).

Each re-run follows the phase pattern: dry-run, `--commit`,
second `--commit` (0 new rows), independent audit, no status
promotion, no new PSX collection, identity by ticker.

---

*End of handover report. The pipeline Phases 1–30 is closed with this
report. Further work is the PLANNED batch above and the pending
decisions — each needs its own instruction.*
