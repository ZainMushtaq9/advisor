# Phase 22 Run Report — Research Reports, Investment Memos and Company Dossiers

Verdict: **PARTIALLY COMPLETE** (see §7 for why COMPLETE is not claimed).

Brief source: playbook extract `~/workspace/psx-playbook/psx_playbook.txt`,
lines 1623–1681. Base branch: `phase-21-alerts` (`dbeee4a`).
Migration head before: `20261104_0018`; after: `20261104_0019`.

## 1. What was built

- 8 report templates (company_dossier, earnings_update, valuation_report,
  sector_outlook, event_brief, portfolio_review, risk_report,
  market_overview), each with a fixed section list, audience, methodology
  text, and disclosure text. Report date 2026-11-04; data cut-off 2026-11-04;
  price date 2026-11-03 (the single stored trading date).
- Evidence model: every figure carries one of five kinds (sourced_fact,
  deterministic_calculation, model_output, analyst_inference, assumption)
  and one of three computation statuses (computed, insufficient_inputs,
  not_applicable). A computed figure carries exactly one value form
  (numeric or text); a non-computed figure carries neither — never a
  zero-fill, never an estimate. There is no `price_target` figure kind and
  no section may state one.
- QA gate (runs on every draft before any write): cut-off and report date
  present, section list exactly equals the template list, DISCLAIMER present
  in the body, forbidden wording rejected (target price, BUY/SELL shares,
  place an order, execute a trade, guaranteed return), every figure passes
  validation, at least one figure present, and every non-disclosures section
  cites at least one figure key or states "not available".
- Rendering: Markdown (canonical committed form), standalone HTML, and PDF
  via fpdf2 2.9.0 (free, pure Python; pinned in `backend/requirements.txt`
  with a Phase 22 note). A render that raises is a failure, never a partial
  file. Markdown/HTML exports are committed under `docs/phase-22/reports/`;
  PDFs live under gitignored `storage/research_reports/` with only hash and
  path recorded in `report_exports`.
- Approval is an explicit CLI transition only (DRAFT → APPROVED or
  DRAFT → REJECTED). APPROVED means internally reviewed only. There is no
  publish step and no external publication path anywhere in this phase.
- API: GET-only `/api/v1/reports/*` (templates, list, detail, status),
  registered in the v1 router; generation/approval/rejection run through
  the CLI only.

## 2. Seed run (actual evidence)

Dry-run first: 22 evaluated, 22 would_write, 0 failed.
Commit: 22 created, 0 failed — 541 figures, 46 warnings, 188 sections,
66 exports (22 markdown + 22 HTML + 22 PDF).
Second `--commit`: 22 skipped_existing, 0 created — idempotency proven.

| Report | Sections | Figures | Warnings |
| --- | --- | --- | --- |
| company_dossier HUBC | 10 | 56 | 3 |
| company_dossier NML | 10 | 56 | 11 |
| company_dossier OGDC | 10 | 56 | 3 |
| earnings_update HUBC / NML / OGDC | 8 each | 25 each | 1 / 3 / 1 |
| valuation_report HUBC / NML / OGDC | 8 each | 27 each | 1 / 3 / 1 |
| sector_outlook POWER GENERATION & DISTRIBUTION | 8 | 4 | 1 |
| sector_outlook TEXTILE COMPOSITE | 8 | 4 | 1 |
| sector_outlook OIL & GAS EXPLORATION COMPANIES | 8 | 4 | 1 |
| event_brief macro:2026-10-26:mpc_meeting | 8 | 2 | 0 |
| event_brief news:HUBC:earning | 8 | 2 | 0 |
| portfolio_review ew_statements_3_balanced | 9 | 10 | 1 |
| portfolio_review rule_screen_pass_balanced | 9 | 8 | 0 |
| portfolio_review rule_screen_pass_conservative | 9 | 8 | 0 |
| risk_report HUBC / NML / OGDC | 8 each | 30 / 29 / 30 | 2 / 8 / 2 |
| risk_report MARKET | 8 | 60 | 0 |
| market_overview market | 11 | 26 | 3 |

Figure statuses: computed 335, insufficient_inputs 199, not_applicable 7.
Figure kinds: sourced_fact 85, deterministic_calculation 140,
model_output 313, assumption 3, analyst_inference 0 (no analyst inference
is computed anywhere — by rule, analyst_inference can never be `computed`).
Warning kinds: risk_flag 24, gate 9, coverage 4, stale 3, unknown_date 3,
missing 2, not_calculable 1. All 22 reports are DRAFT; none is APPROVED,
because no report has been internally reviewed yet — approving one only to
exercise the path would misstate its status.

## 3. Independent audit (hand-checked against the live DB)

- HUBC dossier `close_price` = 197.240000 — matches the stored 2026-11-03
  close exactly.
- HUBC dossier `ratio_gross_margin` = 0.417400 — matches the Phase 8
  computed value exactly.
- HUBC dossier `valuation_multiples:pe_trailing` = 5.155254 — matches the
  Phase 9 computed value exactly.
- HUBC close re-read after the whole run: 197.2400 (Phase 22 writes no
  price rows; the deterministic-authority property holds).
- Live API (TestClient): templates 200 (8); reports 200 (total 22); status
  200 (by template 3/3/3/3/2/3/4/1, by status DRAFT 22, published_externally
  0); detail 200 (HUBC dossier: 10 sections, 56 figures, 3 warnings,
  3 exports); unknown report 404; bad pagination 400; unknown-template
  filter 200 with total 0.

## 4. Corrections made during this run (all in Phase 22 code, none hidden)

1. CLI `build_engine()` call passed no argument while `app.database`
   requires the URL — fixed to pass `DATABASE_URL` from the environment.
2. Assembly SQL used pre-Phase-5 column names for prices (`open/high/low/
   close` instead of `open_price/high_price/low_price/close_price`) and
   ordered macro rows by `indicator_key` instead of `indicator_code`;
   ownership rows used `shares`/`as_of_date` instead of
   `shares_held`/`reporting_date` — all corrected to the real schema
   (ownership loader is carried in the bundle but currently feeds no figure;
   noted, not removed, to keep the bundle contract stable).
3. Downstream key uses updated to match (`price["close_price"]`).
4. Runner did not roll back after a failed build, so one SQL failure
   poisoned every later build in the same session — the runner now rolls
   back on a failed build and commits each created report immediately, so a
   later failure cannot discard earlier reports or poison later ones.
5. Persist read `fig["figure_kind"]` while `figure()` emits `"kind"` —
   fixed to `fig["kind"]` (the model column stays `figure_kind`).
6. QA citation failures fixed in builders, never by weakening QA: risk
   sections now cite figure keys that actually exist for that subject
   (market coverage rate for MARKET, volume tier for companies, first
   control/stress figure keys present); market overview screens/decisions/
   alerts sections now name `screen_liquid_leaders`, `decision_HUBC`,
   `alerts_info`; valuation methods/scenarios sections cite
   `valuation_<method>` keys.
7. Forbidden-wording failures fixed by rewording, not by narrowing the
   gate: "no target price is stated" → "no price objective is stated",
   "No scenario states a target price" → "No scenario states a price
   objective". The bare `target price` pattern stays in force.
8. Approval lifecycle test added (in-memory SQLite, no live DB, no
   network): DRAFT → APPROVED, re-approve rejected, reject from APPROVED
   rejected, DRAFT → REJECTED, approve from REJECTED rejected, unknown id
   rejected. The live CLI guard was also checked (`--approve 999999`
   exits 1 with "unknown report id", all 22 reports still DRAFT).

## 5. Tests

- Phase 22 pure suite: 22 passed (21 prior + 1 new lifecycle test).
- Full backend suite: 348 passed, 0 failed.
- Ruff check and format clean on all new/changed Phase 22 files.
- No-execution scan: 0 hits; reports endpoint carries only `@router.get`
  decorators. No broker/order/execution concept exists anywhere.

## 6. What computed vs what is NOT_CALCULABLE (with reasons)

Computed (335 figures): stored closes and volumes, statement counts and
income-line values, Phase 8 ratios and health scores, Phase 9 book values
and trailing P/E where computable, Phase 10 regime label, Phase 12 breadth
and liquidity values, Phase 14 computed risk values, Phase 15 decision
conclusions (as model outputs, user-facing WITHHELD), Phase 16 simulated
holdings and sector weights, Phase 20 screen match counts, Phase 21 alert
totals by severity.

NOT_CALCULABLE (199 insufficient_inputs + 7 not_applicable, never
numbered): every Phase 6 technical value (0 calculable values); Phase 9
share-count methods (no shares-outstanding source), DCF/DDM (no
source-backed discount rates, growth, or DPS series), peer medians (each
company alone in its sector); Phase 13 forecasts (abstained on all 120
assessments — no forecast figure appears in any report); Phase 15
user-facing values (all WITHHELD at LOW confidence); Phase 16 mean-variance
(no validated returns, no covariance); Phase 17 backtest metrics (all 5
runs NOT_RUNNABLE — no backtest result appears in any report); series risk
metrics (one price date); advances/declines/turnover breadth
(previous_close and turnover NULL on all price rows); portfolio return
(zero return observations). Future scheduled events (SBP minutes
2026-11-20, MPC meeting 2026-12-14) appear only in explicitly labelled
scheduled/upcoming sections, never as occurred. No figure in any report
carries a quality status higher than its inputs (all inputs UNVERIFIED
except the 6 Phase 10 macro observations documented as SBP/PBS
cross-publisher agreement, which keep their documented caveats).

## 7. Why PARTIALLY COMPLETE, not COMPLETE

The acceptance gate is met for what this phase controls (every key figure
traceable, cut-off explicit, exports render without layout errors, zero
external publication), but the reports inherit every upstream limitation:
all statement/ratio/valuation inputs UNVERIFIED; 3-company statement
coverage (3/470); one price date; abstained forecasts; WITHHELD decisions;
NOT_RUNNABLE backtests; fallback-only agents; vector retrieval not
implemented; HBL pending. COMPLETE would require those inputs to be
verified and complete, which is not this phase's to claim.

## 8. HBL-pending note

Habib Bank Limited has no dossier, earnings update, or valuation report
(it has no loaded statements); it appears in market-wide figures only
(price/volume screens, breadth/liquidity, one high-volume alert). Design
accepts HBL via a Phase 7 load plus a Phase 22 re-run with no redesign;
the banking rule (no industrial ratios blindly applied) carries forward.

## 9. Remaining blockers (with exact unblockers)

- Wider-company/KSE-100 expansion: Phase 7 expansion beyond the 3-company
  sample, per-company source verification pass; then a Phase 22 re-run.
- HBL coverage: live-browser download of the HBL CY2025 PDF (parent-owned
  task), then Phase 7 load, then Phase 22 re-run.
- VERIFIED promotion: H1 second agreeing source including an official
  source, plus a recorded human approval gate (none granted); everything
  stays UNVERIFIED until then.
- Price-target-free valuation scenarios stay scenario lists, never price
  objectives, until a validated target methodology exists (none defined).
- CI-in-CI: a main/development push or PR (separate approval; remote/local
  main have unrelated histories; no PR exists).
- Vector retrieval in RAG (Phase 19 blocker) does not block these reports
  (they cite stored rows, not retrieved passages), but a future
  passage-cited report variant would need a verified local embedding model.

## 10. VM-replacement recovery note (2026-11-05, before Phase 22 work)

The VM replacement wiped PostgreSQL and the original Phase 22 worktree.
Recovery, in order: PostgreSQL 16 reinstalled (apt lock held by a boot-time
replay was waited out, not broken); role/databases recreated; backup
2026-11-04T1230-PKT restored and manifest-verified; migrations to
`20261104_0018`; registry import, LEAP load, 444-row price commit, and
Phases 6–21 re-run deterministically. Two recovery findings, both disclosed:

- Surrogate-id shift: the fresh registry import assigned company ids
  560–1029 (HUBC 759, NML 864, OGDC 873, HBL 747) versus the original
  90–559 (HUBC 289, NML 394, OGDC 403, HBL 277). Several phase seed files
  hardcode the original ids (fundamental, valuation, macro company and
  sector ids; news publication-date and summary maps keyed by original
  document ids 13/14/15 versus current 4/5/6). The recovery temporarily
  patched those constants in the main worktree to the current ids, ran the
  affected phases, and reverted every patch (main worktree clean afterwards
  except pre-existing untracked files). No committed code changed. A
  Phase 6 nodata run created before the price fix was deleted before the
  correct re-run (124 error rows restored). A Phase 11 earnings-date miss
  (all three events seeded NULL) traced to the document-id map was fixed by
  the same temporary patch plus re-seeding the 3 earnings events; the
  alerts tables were then rebuilt with two clean commits.
- Final verification: all 26 recorded end-of-Phase-21 counts match exactly
  (companies 470, securities 470, registry_evidence 1001, market_prices
  444, documents 3, statements 88, line items 1316, opinions 3, technical
  runs 1, errors 124, indicator values 0, fundamental values 108,
  valuations 51, economic_indicators 12, news_events 7, ownership 34,
  forecast assessments 120, risk values 81, decisions 4, simulated
  portfolios 3, backtest runs 5, orchestration runs 1, rag_chunks 943,
  screen_results 1418, alerts 89, data_sources 19); HUBC close 197.2400.
  The id shift is a surrogate-key difference only: every identity join in
  Phase 22 resolves by ticker, and all values and counts match the recorded
  state. A future full re-import would shift ids again; any seed that
  hardcodes surrogate ids should be resolved by ticker instead.
