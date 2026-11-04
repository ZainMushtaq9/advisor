# Phase 4 — Re-judgment addendum (2026-11-04, evening)

This addendum updates `phase_04_acceptance_report.md` (gate-time
verdict: PARTIALLY COMPLETE) with evidence obtained after the gate.
It does not rewrite the gate report. Phase 6 was NOT started in
this run (user instruction 2026-11-04 18:47 PKT: complete Phases
4 and 5 only).

## Criterion 11 — now PASS for the scoped view

Gate-time verdict was PARTIALLY COMPLETE because no usable dated
snapshot existed (D-51/D-52/D-53). That blocker is now resolved
for the Main Board / Normal Counter view:

- Dated snapshot: DPS Listing Status, 2026-11-04, Main Board /
  Normal Counter, 470 rows (row_no 1–470 continuous, 470 unique
  symbols, 17 blank Clearing Types listed in the import output).
- Reconciliation: snapshot_tickers 470, registry_tickers 470,
  matched 470, coverage_ratio 1.0, missing 0, extra 0.
- Verified three times: original import 2026-11-04 ~13:39 PKT
  (470 companies / 470 securities / 37 sectors / 940 evidence
  rows, idempotent re-import delta 0, spot-check 24/24); re-import
  after first DB recovery ~17:15 PKT (dry-run then commit,
  identical counts); re-import after second DB recovery ~18:00
  PKT (dry-run then commit, identical counts, direct DB
  verification).
- All 470 records are UNVERIFIED under rule H1 (single DPS
  source); VERIFIED 0. That is correct, not a defect.

Criterion 11 is therefore PASS for the Main Board / Normal
Counter view. All other 16 gate criteria were already PASS.

## Overall verdict — still PARTIALLY COMPLETE (full-market scope)

The engine and the scoped population are complete, but the phase
cannot honestly be called fully COMPLETE, because:

1. GEM (5) and Non-Compliant / Winding-Up (93) are counted, not
   captured. Capturing them needs new DPS view extractions,
   which fall under the same unresolved PSX Terms question as
   the market-data commit (see below) — held, not silently
   skipped.
2. KSE-100 completeness is not established, and no KSE-100 claim
   is made anywhere on the basis of this registry.
3. Identifiers are 0: the snapshot source carries no ISINs.
4. Every record is UNVERIFIED: VERIFIED under H1 needs a second
   distinct agreeing source including one official; no second
   source has been verified.
5. The PSX Terms basis for the populated registry itself is
   unresolved: the permission request was sent 2026-11-04
   16:58:19 PKT (thread 1a1a66ca3ef85eeb) and the mailbox was
   re-checked 2026-11-04 ~18:46 PKT — zero messages from any
   psx.com.pk sender. The user's permission claim remains
   unverified and cannot substitute for PSX's written words.

## Follow-up fixed in this run

- `/registry/quality` interpretation text corrected to rule H1
  (commit ffc9d61 on phase-05-snapshot-import, local only, no
  push): VERIFIED now reads as ≥2 distinct agreeing sources
  including one official; the previous text wrongly allowed a
  single official evidence row to imply VERIFIED. Full backend
  suite re-run: 85 passed, Ruff clean.

## Phase 5 position (for the same "complete 4 and 5" instruction)

Phase 5 acceptance requires: a verified dated price file
ingested through the CLI (dry-run then commit) + written
resolution of the Terms internal-use question (+ a KSE-100 check
only if a KSE-100 claim is ever made — none is made). Status:

- Verified dated price file: YES (Market Summary 2026-11-03;
  real CLI dry-run passed twice on production: would-ingest
  444, rejected 13, all UNVERIFIED, rollback verified,
  market_prices still 0).
- Commit: BLOCKED on the same written-permission evidence as
  item 5 above. Nothing else is open in Phase 5.

## What unblocks full COMPLETE for both phases

Written PSX permission evidence, produced and verified for its
exact terms (internal, non-commercial, private-database use).
The moment it is verified: commit the 444 rows, re-judge Phase
5, and re-judge Phase 4 items 1 and 5. Until then, both phases
stay honestly PARTIALLY COMPLETE, and Phase 6 stays not started.
