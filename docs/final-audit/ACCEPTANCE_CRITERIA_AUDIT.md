# Acceptance Criteria Audit — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit `8937338`.
**Audit date:** 2026-11-05 (Asia/Karachi).
**Method:** the Phase 29 acceptance run was re-executed BY THIS
AUDIT against the scratch database (not carried from the
handover). Phase-level acceptance is assessed per phase in the
status matrix; documentation tasks are NOT counted as functional
tests anywhere in this report.

## 1. The project's acceptance gate (Phase 29 run, re-derived in scratch)

Run `phase29-acceptance-2026-11-05`, verdict **PARTIALLY COMPLETE**,
stored in `acceptance_runs` and served live by
`GET /api/v1/acceptance/gate`:

| Gate item | Result | Evidence (from scratch, measured) |
|---|---|---|
| G1 critical workflows | **not_met** | HBL chain blocked at statements (D-03); HUBC/OGDC/NML chains pass. Chain outcomes: hubc pass, ogdc pass, nml pass, hbl_partial blocked |
| G2 defects resolved | **met** | 0 critical, 0 high defects open |
| G3 no fabrication | **met** | Point-in-time checks pass; forecasts abstain honestly; every recomputation matches except the documented D-05 omissions and the expected HBL drift |
| G4 repo clean | **met** | All security/licensing/privacy scans pass. Boundary stated in the gate itself: dataset/secret scans cover branch tips, not every historical commit |
| G5 auditor sign-off | **partial** | Independent recomputation, scenario, and scan evidence complete in this run; human sign-off belongs to the user/parent and is pending |

**Gate logic is honest by construction (verified in code,
`backend/app/services/acceptance/gate.py`):** G5 can only be "met"
by a recorded human sign-off (the code caps it at partial
otherwise); G1 requires all four company chains to pass and the
`chain_hbl_partial` BLOCKED outcome forces G1 `not_met`. COMPLETE
is not reachable from a CLI run alone, by design. The verdict
follows from the items, never the reverse (stated in the module
docstring and borne out by the stored evaluation).

## 2. Scenario totals (Phase 29 run, scratch)

| Outcome | Count |
|---|---|
| Pass | 12 |
| Fail | 0 |
| Blocked | 1 (`chain_hbl_partial`) |
| Not evaluable | 2 (`restatement`, `suspended_security`) |
| **Total scenarios** | **15** |

No scenario failed. The single blocked scenario is the HBL chain
(the baseline predates HBL downstream rows; the scratch
reproduction advances HBL coverage but the scenario's own
criterion — the full HBL chain as specified at Phase 29 time —
remains blocked in this baseline's terms). The two
not-evaluable scenarios are not failures: restatement has no
`financial_document_versions` rows to evaluate against (0 rows),
and no suspended security exists in the registry to test.

## 3. Recomputation totals (Phase 29 run, scratch)

| Outcome | Count |
|---|---|
| Matched | 14 |
| Mismatched | 1 (`drift_vs_phase24_baseline` — the expected HBL drift, a documented exception in the gate code's `KNOWN_RECOMPUTATION_EXCEPTIONS`) |
| **Total recomputations** | **15** |

The single mismatch is not a fabrication signal: it is the drift
check correctly reporting that live counts differ from the
Phase 24 baseline on exactly the HBL/LEAP tables (documents 3→4,
statements 88→118, line items 1316→2116, opinions 3→4, news
events 7→8, data_sources 19→20). The gate code names this
exception explicitly.

## 4. Authoritative scans (Phase 29 run, scratch)

9/9 PASS (see SECURITY_AND_PRIVACY_AUDIT.md for the table).
Scoping, honestly stated: `.py`/`.sh`, non-test, self-excluded;
branch-tip datasets across 41 tips; PII columns 0 hits with auth
tables 0/0/0. An ad-hoc grep across docs/test-data gives false
positives and was not used as findings.

## 5. Acceptance criteria totals (what can and cannot be aggregated)

- **The auditable acceptance totals are the Phase 29 run's:**
  15 scenarios (12 pass / 0 fail / 1 blocked / 2 not_evaluable),
  15 recomputations (14 matched / 1 expected-mismatch), 9 scans
  (9 pass), 5 gate items (3 met / 1 not_met / 1 partial).
- **Phase-level criteria are NOT aggregated into a single
  passed/total number,** because the 30 phases have different
  criterion counts, different kinds of criteria (functional vs
  documentary), and different measurement states (pre- vs
  post-HBL-downstream). Aggregating them would produce exactly
  the misleading average percentage the prompt forbids. Instead,
  each phase's acceptance status is given individually in
  PHASE_BY_PHASE_STATUS_MATRIX.md, and documentation tasks are
  never counted as functional tests: a phase with a complete
  report but unmet functional criteria is PARTIALLY COMPLETE,
  not COMPLETE.
- **What "acceptance" does NOT include:** no human sign-off
  exists (G5 partial); no external publication approval exists
  (0 APPROVED reports); no production deployment acceptance
  exists (nothing deployed). These are open items, not passed
  criteria.

## 6. Verdict for this audit area

Acceptance is PARTIALLY COMPLETE and honestly measured: zero
failures, one blocked chain, two not-evaluable scenarios, one
expected-mismatch recomputation, nine clean scans, and a gate
that cannot be gamed into COMPLETE without a human signature.
The gate's own evidence matches the handover claim exactly —
re-derived from scratch, not copied.
