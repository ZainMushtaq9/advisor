# Open Blockers and Defects — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit `8937338`.
**Audit date:** 2026-11-05 (Asia/Karachi).
**Sources:** the Phase 29 defect register
(`docs/phase-29/defect_register.md`, re-verified against scratch
where applicable) plus new findings from this audit. Severity
counts below combine both, with the source of each item marked.
No defect was closed by rewording; "accepted" means understood,
documented, with an exact unblocker — not resolved.

## 1. Severity counts

| Severity | Register (Phase 29) | New in this audit | Total open |
|---|---|---|---|
| Critical | 0 | 0 | **0** |
| High | 0 | 0 | **0** |
| Medium | 1 open (D-04) | 1 (A-02) | **2** |
| Low | 1 open (D-12) | 6 (A-01, A-03 – A-07) | **7** |

Register totals (re-verified in scratch acceptance run): 14
defects — 0 critical, 0 high, 6 medium, 8 low; 2 open (D-04, D-12),
2 fixed (D-05, D-13), 10 accepted. Note: one parent-brief line
called D-14 low; the register governs and D-14 is MEDIUM (and
accepted, not open).

## 2. Open defects from the register (re-verified)

**D-04 — Surrogate-id traps in code (MEDIUM, open).**
`backend/app/services/macro_analysis/__init__.py:66-69` hardcodes
sector ids 16/8/36/4; `backend/app/services/news_events/
__init__.py:164,199` keys publication dates and seed summaries by
document ids 13/14/15. On any fresh import with different
sequence state, these ids differ (live 53/45/73/41; recovery #6
7/8/9; recovery #7 and this audit's scratch 4/5/6), so the macro
sector mapping silently mis-assigns and the news seed silently
produces NULL earnings dates (the exact recovery #6 failure mode:
HUBC alert suppressed, 88 alerts not 89). Workaround documented
(temporary remap + revert — used by this audit for Phase 11 and
reverted); fix is ticker/name resolution, not hardcodes.
*Audit note: the trap did NOT trigger in scratch (scratch ids
coincide with the constants), which proves the trap is
sequence-state-dependent, not absent.*

**D-12 — Token-gated report approval (LOW, open).** The report
approval flow (DRAFT → APPROVED/REJECTED) is CLI-only and belongs
to no brief for token-gating; the "token-gated" variant was
never specified. No APPROVED report exists. Unblocker: a brief
naming the token-gating design, or a decision to keep approval
CLI-only (in which case D-12 closes as "not required" by
decision, not by rewording).

**Accepted (not open, listed for completeness):** 10 defects
with exact unblockers, including D-14 (PyMuPDF AGPL review
trigger, MEDIUM, accepted — the trigger is pre-deployment, see
licensing audit) and the HBL-chain items whose unblocker is the
post-handover HBL batch (which has since completed — but the
audit baseline predates it, so the register state stands for
this audit).

**Fixed (verified in scratch where applicable):** D-05 (omission/
staleness — the recomputation exceptions for report_figure_census
and decision_completeness are in the gate code's
KNOWN_RECOMPUTATION_EXCEPTIONS, and the drift exception is the
expected HBL drift), D-13 (fixed per register; not independently
re-traced in this audit beyond the register's own record).

## 3. New findings from this audit

**A-01 — Readiness endpoint stale head constant (LOW for
function, with a trust note).**
`observability.py:51` hardcodes `EXPECTED_MIGRATION_HEAD =
"20261104_0023"` vs correct `20261104_0024`; live-verified:
`migration_matches: false`, `ready: false` on a healthy,
fully migrated database. Pre-existing, explicitly not fixed in
Phase 30. Fix: one-line constant change under its own brief
(the audit does not make it, per read-only rule). Trust note: a
permanently red readiness signal trains operators to ignore it,
so the fix should not linger once a brief exists — but nothing
gates on this endpoint today, hence LOW.

**A-02 — Integration gap: side-branch code absent from the
release tree (MEDIUM).** LEAP loader (`scripts/
load_leap_evidence.py`, `leap_evidence.py`, tests, reports),
universe endpoint (`endpoints/universe.py`), and HBL extraction
code + page maps are absent from `8937338` (verified by
`ls-tree`). Consolidation commit `8937338` touches only 3
documentation files and is not a merge. A checkout of
`phase-30-release` alone cannot reproduce its own database state.
Fix: a real code merge (or cherry-pick) of `eb2e331` and
`42bd8e2` into the release lineage under a new brief, with
regression tests — not a documentation edit.

**A-03 — CI-in-CI unverified (LOW).** No Actions runs; workflow
triggers only on main/development pushes/PRs, none of which
exist. Fix: a main/development push or PR (separate approval) or
a workflow trigger change under its own brief.

**A-04 — Branch protection absent (LOW).** Both `main` and
`phase-30-release` return "Branch not protected" (verified).
Fix: enable protection before any public-release use (as the
Phase 30 checklist itself recommends).

**A-05 — Tag does not cover the tip (LOW).** `v0.2.0-handover`
peels to `6b1ff9f`, not to `8937338`; the consolidation commit
is untagged. Fix: tag the tip (or re-tag under a new name per
the rollback plan) when the release identity is finalised.

**A-06 — Macro VERIFIED caveat not surfaced (LOW).** The 6
VERIFIED macro indicators rest on an SBP/PBS cross-publisher
caveat, not on H1 registry verification. Any display that shows
"VERIFIED" without the caveat over-states the evidence. Fix:
attach the caveat wherever macro status is displayed, or rename
the status.

**A-07 — Scratch-vs-handover divergences requiring no code fix
(LOW, informational).** News events 8 vs 7, event-companies 4 vs
3, evaluation metrics 50 vs 44, SLO 7/6/1 vs 10/4/0, exceptions
8 vs 6, data_sources 20 vs 19, job_runs 0 vs 71, alert_runs 9 vs
18 — all reconciled in the database audit (HBL mechanism,
operational history, LEAP provenance row). No action except
recording: future handover reports must state their measurement
state (pre- vs post-HBL-downstream) so counts are comparable.

## 4. Open blockers (external dependencies, not code defects)

These block COMPLETE verdicts regardless of code quality. Each
names its exact unblocker:

| Blocker | Blocks | Exact unblocker |
|---|---|---|
| Written PSX permission, verified for its exact terms | Phases 5, 6, 12, 13, 14, 16, 17, 20, 21 (all market-data phases) + any live collection | A PSX reply whose wording the user/parent has read and assessed as permitting the intended use; or a documented decision to proceed on a narrower, permitted basis |
| More trading dates (multi-day price series) | Phases 6 (warm-ups), 13 (forecasts), 14 (VaR/ES), 16 (covariance), 17 (runnable backtests) | Either PSX permission + collection, or another lawful multi-day price source, verified for its terms |
| Verified universe (H1) | Phase 4 + every VERIFIED/PARTIALLY_VERIFIED claim | ≥ 2 distinct agreeing sources incl. one official per company, with identifiers recorded; field-scoped LEAP promotion executed (not just documented) |
| KSE-100 statement coverage | Phases 7, 8, 9, 15 (beyond 4 companies) | Issuer-hosted or lawfully obtained statements for the remaining companies, with DPS-download terms resolved |
| Share counts | Phase 9 market-cap / enterprise-value multiples (insufficient_inputs) | A lawful share-count source, verified for its terms |
| Sufficient forecast inputs | Phase 13 computed forecasts | Multi-day returns + the macro/statement coverage above |
| Runnable backtests | Phase 17 | Multi-day price series (same as above) |
| Vector retrieval implemented | Phase 19 (retrieval beyond keyword) | A verified local embedding model + the retrieval implementation + benchmark re-run |
| Production authentication (first live account) | Phase 24 operational + any exposure | A parent/user decision to create the first CLI account, then a live enforced-mode test |
| Automated collection | Phase 25 (scheduler beyond operator-invoked) | Terms clearance for automated polling + a scheduler decision (host cron or daemon) |
| Deployment + sign-off | Phases 28, 29 (G5), 30 (release) | A deployment target + approval, branch protection, CI run, PyMuPDF licence decision, and a human sign-off recorded in the acceptance run |
| HBL downstream recalculations | Phase 29 G1 (HBL chain) — NOTE: post-handover batch work, not audit scope | The HBL re-run batch (reported complete 2026-11-05 on branch `phase-hbl-reruns`; its results are future work for a follow-up audit, not evidence for this baseline) |

## 5. What is NOT a blocker

- The HBL chain scenario (`chain_hbl_partial` blocked) in the
  audit baseline is a consequence of the baseline predating HBL
  downstream rows, not a code failure: the scratch reproduction
  shows the HBL-inclusive state advancing every downstream count
  it touches. A follow-up audit on the post-batch lineage is the
  correct next verification, not a re-run of this baseline.
- D-DB-09 (daily_return(470) phrasing) is a claim correction, not
  a defect: the error model is run-level, and the headline counts
  are exact.
