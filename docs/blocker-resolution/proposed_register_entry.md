# Proposed Register Entry — Blocker Resolution (D-05 / Readiness / G5)

**PROPOSED TEXT ONLY — for parent consolidation. Do NOT paste into
`docs/development/PHASE_COMPLETION_REGISTER.md`,
`PROJECT_EXECUTION_STATE.md`, or `MASTER_EXECUTION_LOG.md` directly;
the parent consolidates registers.**

---

## Blocker-resolution run (2026-11-05) — branch `d05-readiness-g5`

**Base:** `phase-hbl-reruns` `c71469a` (unmoved). **This branch tip:**
[COMMIT SHA — fill after push; remote SHA verified equal to local
tip]. **Main:** `eb6025b` untouched. No merge to main.

### D-05 — FIXED (measured)

- Clean news-first re-derivation executed: news (Phase 11) → decisions
  (Phase 15) → reports (Phase 22). Finding: no live stale figure
  existed at batch end — the stale item was the measurement (pinned
  541 claim + recovery #6 method text), not a stored figure.
  Report 14 (`event_brief news:HUBC:earning`) deleted with dependents
  only (figures 339/340, sections 111–118, exports 40/41/42),
  snapshotted first (`~/workspace/d05-snapshots/pre_d05_snapshot.sql`,
  SHA-256 `8285fed82a14739e95387753de234ea2484ac2c8f95f86c63d8aa7524bb42f50`),
  and recreated as report 26 with identical figures and byte-identical
  md/html export hashes.
- Measurement updated to the measured post-re-derivation census:
  649 = 389 computed + 244 insufficient_inputs + 16 not_applicable
  (`defects.py`, `recompute.py`); drift claim updated to the
  Phase 25-rule approved baseline (documents 4, statements 118,
  line items 2,116); `KNOWN_RECOMPUTATION_EXCEPTIONS` emptied (all
  three former exceptions resolved — any future mismatch now fails
  G3 by design); G3 met-evidence wording corrected (no more
  "D-05 omissions / HBL drift" text).
- MARKET `forecast_abstention_rate` evidence staleness resolved by a
  versioned runner fix: `run_risk(..., model_as_of)` +
  `--as-of-date` CLI option; 2026-11-05 row written with 156/156
  (100%), 2026-11-04 row (120/120) preserved; risk values 95 → 98;
  repeat run writes 0. Regression tests added (5 tests).
- Acceptance run `phase29-acceptance-2026-11-05-blockers`: verdict
  PARTIALLY COMPLETE; G1/G2/G3/G4 MET, G5 PARTIAL; 14 scenarios
  (12 pass, 2 not_evaluable, 0 fail); 15/15 recomputations match;
  D-05 fixed.

### Readiness endpoint — FIXED, retargeted to live head 0025

- `EXPECTED_MIGRATION_HEAD`: 2023-hardcoded `20261104_0023` (Phase 27
  artifact) → `20261104_0025` (live head after the news-intelligence
  migration 0025; this branch's chain head is 0024 — see the run
  report for the distinction). Regression tests: matches/ready true
  at 0025, stale-head (0024) detected as not ready; unavailable-DB
  truthful behavior preserved. Live smoke (GET-only): head 0025,
  expected 0025, matches true, ready true.
- Only other `0023` mention found: a comment example in
  `ops/healthcheck.sh:44` (logic parses the head dynamically — no
  change needed). Note: `ops/healthcheck.sh` on this branch reports
  a migration mismatch (live 0025 ≠ branch head 0024) until the news
  migration is merged into the branch's chain.

### D-12 — BRIEF DELIVERED (preparation only, still OPEN)

- Covering brief at `docs/blocker-resolution/d12_token_gated_approval_brief.md`:
  scope, threat model, design (reuse existing Bearer mechanism,
  `report_approver` role, CLI + optional API routes, same-transaction
  audit rows, backward compatibility), D-10 interaction, tests,
  acceptance criteria, risks, rollout. No implementation in this task.
  Unblocker for closing D-12: the brief's approval + the §5 decisions
  (route scope, gating mode, token bootstrap, D-10 sequencing).

### G5 — EVIDENCE PACKAGE DELIVERED (still PARTIAL, UNSIGNED)

- Package at `docs/blocker-resolution/g5_signoff_evidence_package.md`:
  gate table (G1–G4 MET, G5 PARTIAL), run history (4 runs incl. the
  FAILED mid-batch run), new-run detail, defect status, test evidence,
  known limitations, sign-off block left UNSIGNED. No signature claimed.

### Portfolio — BRIEF DELIVERED (preparation only, NOT executed)

- Brief at `docs/blocker-resolution/hbl_portfolio_expansion_brief.md`:
  three new portfolio versions proposed (ew_statements_4_balanced,
  rule_screen_pass_balanced_v2, rule_screen_pass_conservative_v2),
  Phase 17 ledger re-derivation plan, eligibility evidence (HBL quote
  ELIGIBLE at 286.16, 2026-11-05 SCREEN_PASS decision 6/7), cash
  reconciliation method, comparison methodology, tests, acceptance
  criteria, risks. Stale HBL SCREEN_NOT_RUNNABLE exclusion rows are
  to be superseded by versioning, never overwritten.

### Terms gate — BLOCKED (no change)

- No written permission evidence; no PSX email, no DPS systematic
  collection, no VERIFIED promotion in this task. Unblocker: written
  permission evidence (user-owned); reply-watch cron
  `psx-permission-reply-watch` still active every 6h.

### Regression (this branch)

- Backend pytest: 477 passed (baseline 468 + 9 new/changed tests).
- Frontend vitest: 11 passed. Webpack build: exit 0, 27/27 pages,
  27 routes. (Turbopack build fails in this worktree only: the
  symlinked node_modules falls outside Turbopack's workspace root —
  environment artifact, not a code failure; see run report.)
- Playwright: phase23 22 passed; phase29 6 passed (specs updated to
  the measured post-resolution state: 15 matched / 0 mismatched,
  chain_hbl_full passing — see run report §7c).
- Frontend copy fix (authorized one-line scope, extended to the same
  page's banner): news page now says "four company earnings events
  and four macro events" and "Coverage is 4 of 470 companies"
  (verified: earnings 4, macro_release 4, distinct companies 4).
  Remaining stale copy on other pages noted in the run report.

### Concurrency notes

- Live head moved 0024 → 0025 during this task via the
  news-intelligence coordinator's gated Phase B migration (branch
  news-intelligence, 9 tables, job_definitions 8 → 11, 8 refused
  collection runs, news_articles 0 by design). All D-05-table counts
  (news_events 8, decisions 5, reports 25, figures 649) unchanged;
  this task's deletion touched only report 14 + dependents and no
  news-engine rows.
- Independent 30-phase audit is COMPLETE (verdict C, predates the HBL
  batch); it recommends a fresh audit of the post-batch lineage (D1)
  — not part of this task.
