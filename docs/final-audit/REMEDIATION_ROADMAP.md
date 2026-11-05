# Remediation Roadmap — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit `8937338`.
**Audit date:** 2026-11-05 (Asia/Karachi).
**Rules:** no step below bypasses a restriction, fabricates data,
promotes a quality status without evidence, or invents a human
sign-off. Estimates are realistic, not optimistic: they assume
the stated unblocker arrives; where the unblocker is external
(PSX permission), no date is promised. Order is by dependency,
not by phase number — shared blockers first, because they unlock
many phases at once.

## Phase A — Shared blockers (do these first; they unlock the rest)

**A1. Written PSX permission, verified for its exact terms.**
Missing work: read and assess a PSX reply (or obtain one through
a lawful channel the user directs). Cause: permission requested
but the reply's wording is unverifiable (deleted). Blocker:
external (PSX). Category: legal/permission. Action: user/parent
presents the reply text (or a new reply arrives via the
reply-watch cron); assess its exact terms against the intended
uses (retention, internal analysis, any republication — each
separately); record the assessment; only then unpause collection
jobs. Affected files: job registry (pause reasons), Phase 5/11
collectors, NOT_COLLECTED lists. Tests: paused-job refusal tests
must still pass; a new permission-terms test should assert the
recorded scope. Evidence: the reply text + assessment, stored
outside the public repo if it contains anything non-public.
Estimate: assessment 1 day once the text exists; obtaining the
text is externally timed and not estimated.

**A2. Real code integration of the side branches.**
Missing work: merge `eb2e331` (LEAP loader) and `42bd8e2` (HBL
extraction) into the release lineage. Cause: consolidation #2 was
documentary, not a merge. Blocker: none (internal). Category:
integration. Action: merge or cherry-pick under a new brief, add
the universe endpoint to the release tree, re-run the full
scratch reproduction, and confirm the tree alone reproduces its
database. Affected files: `scripts/load_leap_evidence.py`,
`backend/app/services/registry/leap_evidence.py`,
`backend/app/api/v1/endpoints/universe.py`,
`docs/phase-07/page_maps/hbl_*.json`, HBL extractor options.
Tests: backend pytest (453 + LEAP tests), fresh-clone
reproducibility. Evidence: new branch tip + scratch counts.
Estimate: 1–2 days.

**A3. Surrogate-id fix (D-04).**
Missing work: replace hardcoded sector ids and document ids with
ticker/name resolution. Cause: ids shift on every fresh import.
Blocker: none (internal). Category: code defect. Action: resolve
sectors by name and documents by (ticker, document_type, period)
at runtime; add a regression test that re-runs Phase 10/11
against a deliberately shifted-id database. Affected files:
`backend/app/services/macro_analysis/__init__.py`,
`backend/app/services/news_events/__init__.py`. Tests: new
shifted-id regression tests + existing suites. Evidence: Phase
10/11 reproduce without any remap on a shifted-id scratch DB.
Estimate: 1 day.

**A4. Readiness constant fix (A-01).**
Missing work: `EXPECTED_MIGRATION_HEAD` 0023 → 0024. Cause:
Phase 27 artifact carried forward. Blocker: none (needs its own
brief per audit rules). Category: code defect (LOW). Action:
one-line change + a test asserting the constant equals the
current head. Affected files:
`backend/app/api/v1/endpoints/observability.py`. Tests:
readiness endpoint test. Evidence: live readiness response with
`migration_matches: true`, `ready: true` (once auth posture is
also decided — see A6). Estimate: under 1 hour.

**A5. Branch protection + tag hygiene (A-04, A-05).**
Missing work: protect `main` and the release branch; tag the
release tip. Cause: never enabled. Blocker: repo-admin action
(user/parent). Category: governance. Action: enable protection
via GitHub settings; tag `8937338` (or its successor) with a
release tag. Tests: none (settings verification via API).
Evidence: `gh api` protection responses + tag peel. Estimate:
under 1 hour.

**A6. First live auth account + enforced-mode test.**
Missing work: create the first CLI account, verify enforcement
activates and fail-closed behaviour holds. Cause: parent/user
decision pending. Blocker: decision. Category: security/
operations. Action: create one CLI account on the live database
(never on scratch for production), run the auth test suite
against enforced mode, verify unauthenticated requests fail.
Affected files: none (CLI + tests). Tests: auth suite (24)
under enforced mode. Evidence: readiness
`auth_enforcement: "on"` + failed unauthenticated probe.
Estimate: 1 day including verification.

## Phase B — Data blockers (unlock analysis phases)

**B1. Multi-day price series.**
Missing work: ≥ 251 trading days for VaR/ES warm-ups; at minimum
2+ days to enable returns, covariance, and runnable backtests.
Cause: single-day snapshot + Terms-gated collection. Blocker:
A1 (permission) or another lawful source. Category: data.
Action: once permitted, run the unpaused collection jobs
daily; backfill lawfully if a permitted history source exists.
Affected files: Phase 5/6/12/13/14/16/17 runners (no code change
expected — they already handle multi-day data; they currently
abstain correctly). Tests: Phase 6 warm-up tests, backtest
runnability tests. Evidence: trading_sessions > 0, prices on
multiple dates, VaR/ES computed, backtest runs RUNNABLE.
Estimate: collection time is calendar time (251 trading days
cannot be accelerated by effort); the engineering work is 2–3
days once the source is permitted.

**B2. Verified universe (H1).**
Missing work: second agreeing sources incl. one official per
company; identifiers recorded; field-scoped LEAP promotion
executed. Cause: single-source DPS snapshot; LEAP procedure
documented but not executed as promotions. Blocker: source
access + the promotion decision. Category: data/verification.
Action: execute the field-scoped promotion procedure for the 61
LEAP companies first (evidence already loaded), then expand
coverage; record identifiers. Affected files: registry service,
promotion procedure doc. Tests: H1 rule tests. Evidence:
companies with VERIFIED/PARTIALLY_VERIFIED status + identifier
rows > 0. Estimate: 1 week for the 61-company promotion batch;
full-universe coverage is a longer programme, not estimated
here.

**B3. KSE-100 statement coverage + share counts.**
Missing work: statements beyond 4 companies; share counts for
market-cap multiples. Cause: DPS-download terms unresolved;
no share-count source. Blocker: terms + source. Category: data.
Action: issuer-hosted statements first (lawful, sampled);
resolve DPS-download terms or find an issuer-hosted route for
the rest; adopt a share-count source and verify its terms.
Affected files: Phase 7/9 runners, keymaps. Tests: extraction
tests per new company. Evidence: statements > 4 companies;
market-cap multiples computed. Estimate: per-company effort;
not estimated as a single date.

**B4. Macro VERIFIED caveat surfacing (A-06).**
Missing work: attach the SBP/PBS cross-publisher caveat wherever
macro VERIFIED is displayed. Cause: definitional difference
from H1. Blocker: none. Category: documentation/display.
Action: caveat text in the macro API responses and frontend
displays (or rename the status). Affected files: macro
endpoints, frontend macro pages. Tests: display tests.
Evidence: caveat visible on a macro page. Estimate: under 1 day.

## Phase C — Capability blockers (unlock feature phases)

**C1. Vector retrieval + verified local model (Phase 19).**
Missing work: embedding model (licence-checked) + retrieval
implementation + benchmark re-run. Cause: registered but not
implemented; no model verified. Blocker: model selection +
licence. Category: feature. Action: select an open-weight
embedding model, check its licence, implement retrieval, re-run
the benchmark (new run id — never re-fabricate r1/r2). Affected
files: RAG service, benchmark harness. Tests: RAG benchmark
(6 cases, new run). Evidence: benchmark results from the new
retrieval code. Estimate: 1–2 weeks.

**C2. CI-in-CI (A-03).**
Missing work: an Actions run on the release workflow. Cause:
triggers require main/development activity. Blocker: approval
for a main/development push or PR. Category: governance/CI.
Action: push or PR under separate approval, or retarget the
workflow trigger under its own brief. Tests: the CI run itself.
Evidence: `gh run list` non-empty, green. Estimate: 1 day once
approved.

**C3. Deployment + human sign-off (Phases 28/29/30).**
Missing work: a deployment target, a production run, and a
recorded human sign-off (G5). Cause: no target, no approval.
Blocker: user/parent decisions (target, budget PKR 0 constraint,
PyMuPDF licence decision). Category: operations/governance.
Action: choose a free, lawful host (or stay local by decision);
deploy; run the acceptance gate on the deployed system; record
sign-off in the acceptance run. Affected files: `ops/`
scripts, deployment docs. Tests: deployment suite + Playwright
against the deployed URL. Evidence: deployed URL + gate with
G5 met. Estimate: 1–2 weeks once the target is chosen.

**C4. Token-gated report approval (D-12) — decision, not code.**
Missing work: a brief, or a decision to keep approval CLI-only.
Cause: belongs to no brief. Blocker: decision. Category:
governance. Action: user/parent decides; if CLI-only, close
D-12 as "not required" by that decision (recorded, not
reworded). Estimate: decision only.

## Phase D — Follow-up verification (after the batch lineage lands)

**D1. Follow-up audit on the post-HBL-batch lineage.**
Missing work: verify the `phase-hbl-reruns` lineage (reported
complete 2026-11-05) against its own claims — including whether
G1 flipped to MET on measured evidence, whether D-03/D-04 are
fixed there, and whether the HBL downstream counts match the
batch's reported numbers. Cause: this audit's baseline predates
the batch by design. Blocker: none (the batch branch exists).
Category: verification. Action: a new independent audit scoped
to the batch branch, using the same scratch method. Evidence:
a follow-up audit report. Estimate: 1–2 days (the method is
proven; the scope is a delta, not a full re-run).
*This audit makes no claim about the batch lineage's correctness;
the MEMORY note reporting its completion is parent-side news,
not audit evidence.*

## What "done" looks like (all 30 COMPLETE)

- All shared blockers cleared (A1–A6), data blockers cleared
  (B1–B3), capabilities built (C1–C3), and a follow-up audit
  (D1) confirming the new lineage.
- Every phase's mandatory criteria pass with current
  reproducible evidence: verified universe, multi-day prices,
  computed forecasts, runnable backtests, enforced auth,
  deployed service, CI green, human sign-off recorded, and a
  release tag covering the tip.
- Until then, the honest verdict remains PARTIALLY COMPLETE —
  and any user-facing report must carry the same counts this
  audit carries, not a rounded percentage.
