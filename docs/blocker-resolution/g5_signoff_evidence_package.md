# G5 Human Sign-Off — Evidence Package

**Status: PREPARATION ONLY — assembled, NEVER signed.**
This package collects the measured evidence a human sign-off decision
needs. It does not claim a signature, and no code in this project can
grant one: G5 is met only by a recorded human sign-off, never by a
CLI run. The sign-off block at the end is left UNSIGNED for the
user/parent.

**Branch:** `d05-readiness-g5` (from `phase-hbl-reruns` `c71469a`).
**Acceptance run in this package:**
`phase29-acceptance-2026-11-05-blockers`, verdict PARTIALLY COMPLETE,
committed to the live database 2026-11-05.

## 1. Gate table (measured, new run)

| Gate | Result | Evidence (verbatim from the run) |
|---|---|---|
| G1 critical workflows | MET | All four company chains pass. |
| G2 defects resolved | MET | 0 critical, 0 high defects open. |
| G3 no fabrication | MET | Point-in-time checks pass; forecasts abstain honestly; every recomputation matches (15/15). The former D-05 census and HBL-drift exceptions were resolved 2026-11-05 and removed from KNOWN_RECOMPUTATION_EXCEPTIONS, so no exception applies to this run. |
| G4 repo clean | MET | All security/licensing/privacy scans pass. Boundary: dataset/secret scans cover branch tips, not every historical commit. |
| G5 auditor sign-off | PARTIAL | Independent recomputation, scenario, and scan evidence is complete in this run; human sign-off belongs to the user/parent and is pending. |

**Verdict: PARTIALLY COMPLETE.** The only reason the verdict is not
COMPLETE is G5 itself: every other gate is MET on measured evidence.
That is the designed state — a COMPLETE verdict requires the human
signature in §7.

## 2. Acceptance run history (old + new)

| Run id | Date | Verdict | What it shows |
|---|---|---|---|
| phase29-acceptance-2026-11-05 | 2026-11-05 | PARTIALLY COMPLETE | Pre-batch baseline: census matched the Phase 22 claim exactly (541 = 335/199/7). |
| phase29-acceptance-2026-11-05-hbl | 2026-11-05 | FAILED | Mid-batch run: 4 scenarios failed (missing_source, corporate_action, model_failure, provenance_warnings); census and drift mismatched; D-04, D-05, D-12 open. Superseded — do not use as current evidence. |
| phase29-acceptance-2026-11-05-hbl-rerun | 2026-11-05 | PARTIALLY COMPLETE | Batch-end run: G1 flipped to MET (all four chains incl. HBL); census 649 vs claimed 541 and drift vs the Phase 24 baseline mismatched, tolerated via KNOWN_RECOMPUTATION_EXCEPTIONS; G3 MET on that basis. |
| phase29-acceptance-2026-11-05-blockers | 2026-11-05 | PARTIALLY COMPLETE | **This run:** 14 scenarios, 15/15 recomputations match, 14 defects recorded, zero exceptions in force. |

## 3. New-run detail (phase29-acceptance-2026-11-05-blockers)

- **Scenarios (14):** 12 pass (chain_hubc_full, chain_ogdc_full,
  chain_nml_full, chain_hbl_full, delayed_data, ticker_rename,
  corporate_action, no_quote, model_failure, process_restart,
  provenance_warnings, point_in_time); 2 not_evaluable (restatement,
  suspended_security). Zero failures.
- **Recomputations (15/15 match):** hubc_gross_margin, hubc_trailing_pe,
  ogdc_trailing_pe, portfolio_reconciliation, breadth_coverage,
  volume_median, top10_volume_share, hbl_sfp_identity_2025,
  hbl_sfp_identity_2024, hbl_pat_eps_2025, screen_matched_counts,
  alert_totals, report_figure_census (649 = 389 computed + 244
  insufficient_inputs + 16 not_applicable), decision_completeness
  (HUBC 6/7, OGDC 6/7), drift_vs_phase24_baseline (approved baseline:
  documents 4, statements 118, line items 2,116).
- **Defects (14):** D-03 fixed, D-04 fixed, D-05 fixed (this run),
  D-13 fixed; D-01, D-02, D-06, D-07, D-08, D-09, D-10, D-11, D-14
  accepted; **D-12 open (low)** — the only open defect, with its
  covering brief delivered alongside this package (implementation
  not authorized by this task).
- **Repo audits (9/9 pass):** execution_identifiers,
  dangerous_constructs, write_routes, upload_endpoints,
  docker_invocations, tracked_datasets, tracked_secrets (branch tips
  scanned: 43), branch_tip_datasets, pii_columns. Auth tables
  0/0/0 confirmed by the pii_columns audit.

## 4. Defect status (post-fix)

- **D-05 fixed on measured evidence.** The stale measurement (pinned
  541 claim + recovery #6 method text) was replaced by the measured
  post-re-derivation census 649 = 389/244/16; the drift claim was
  updated to the Phase 25-rule approved baseline (4/118/2,116); the
  MARKET `forecast_abstention_rate` evidence staleness (120/120) was
  resolved by a versioned runner fix (`--as-of-date`), writing the
  156/156 row for 2026-11-05 and preserving the 2026-11-04 row.
  The clean re-derivation itself (news → decisions → reports)
  recreated event_brief `news:HUBC:earning` as report 26 with figures
  identical to the deleted report 14 and byte-identical md/html
  export hashes.
- **D-12 open (low).** Brief delivered; implementation needs the
  brief's approval first. It does not block G1–G4, and it is the
  only open defect.
- **Terms gate BLOCKED (unchanged).** No written permission evidence;
  no PSX email, no DPS systematic collection, no VERIFIED promotion
  in this task. See the run report §5 for the exact unblocker.
- **Remainder accepted.** D-01, D-02, D-06, D-07, D-08, D-09, D-10,
  D-11, D-14 are accepted with recorded reasons (see the defect
  register); 0 critical, 0 high open overall.

## 5. Test evidence (this branch)

- Backend pytest (full suite): **477 passed** (batch baseline 468 +
  9 new/changed tests in this task: D-05 census update + old-census
  guard, 2 readiness tests, 5 risk as-of tests, 1 G3-evidence test,
  1 gate-strictness test update).
- Frontend vitest: **11 passed** (unchanged baseline).
- Webpack production build: **exit 0, 27/27 pages, 27 routes**
  (includes the corrected news page copy).
- Playwright: phase23 + phase29 suites — see the run report for
  the recorded result (this package was assembled while they ran;
  the run report carries the counts).
- Live readiness smoke (GET-only, port 8001): migration_head
  20261104_0025, migration_expected 20261104_0025,
  migration_matches true, ready true.

## 6. Known limitations (what this package does NOT claim)

- **HBL rows are UNVERIFIED** (single-source extraction from HBL's
  own investor-relations page; no second agreeing source, no
  official PSX/SECP source). Prices (444, one date 2026-11-03) are
  UNVERIFIED. No VERIFIED promotion is claimed anywhere.
- **Readiness tracks the live head (0025), not this branch's chain
  head (0024).** Migration 0025 belongs to the news-intelligence
  branch (gated Phase B work, applied to the live DB during this
  task). This branch does not carry the 0025 migration file, so a
  checkout of this branch alone truthfully reports not-ready until
  the news migration is merged into its chain. The endpoint logic
  itself is verified by tests at both heads.
- **Parallel news-engine work is outside acceptance coverage.**
  The live DB gained 9 news-intelligence tables and rows
  (news_sources 8, news_collection_runs 8, news_articles 0 by
  design) during this task. No acceptance check reads those tables;
  all D-05-table counts (news_events 8, decisions 5, reports 25,
  figures 649) are unchanged by that work.
- **Frontend copy:** the news page description/banner were corrected
  (4 earnings + 4 macro events; 4 of 470 companies). Two further
  stale-copy strings remain on other pages (company detail page:
  "Seed coverage is 3 of 470 companies"; home page statements line:
  "3 of 470 companies (HUBC, NML, OGDC)") — noted as follow-ups in
  the run report, not fixed here (outside the authorized one-line
  fix).
- **No live auth accounts exist (0/0/0)** by parent/user decision.
  D-12 implementation therefore needs a token-bootstrap decision
  before it can be exercised live.
- **Independent audit note:** the 30-phase audit (branch
  final-30-phase-verification-audit) verdict C predates the HBL
  batch and makes no claim about it; it recommends a fresh audit of
  the post-batch lineage (item D1). That fresh audit is not part of
  this task.

## 7. Sign-off block — UNSIGNED

> I have reviewed the evidence above. I understand that G1–G4 are
> MET on measured evidence, that D-12 remains open with only a brief
> delivered, that the PSX Terms gate remains BLOCKED, and that HBL
> rows and prices remain UNVERIFIED. I sign off / do not sign off
> (delete as applicable) the PSX Intelligence AI project state as
> recorded in acceptance run phase29-acceptance-2026-11-05-blockers.
>
> Signature: ______________________________ (UNSIGNED)
> Name / role: ______________________________
> Date: ____________________________________
>
> This block must remain UNSIGNED until a human completes it. No
> agent, script, or scheduled job may fill it in.
