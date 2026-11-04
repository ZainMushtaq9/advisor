# Phase 4 — Acceptance Report

Date: 2026-11-04. Status: **PARTIALLY COMPLETE**.

## Acceptance criteria — verdict per criterion

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Gate check on Phases 1–3 passed before building | PASS | Phase 2 acceptance (PARTIALLY COMPLETE) + Phase 3 completion (COMPLETE) read; PostgreSQL 16.15 live; 56 public tables at gate; Alembic head 20261104_0004 at gate; branch from b22281a |
| 2 | Source research first, with fields/frequency/history/access/terms/reliability/last-verified per source | PASS | source_research.md + source_research_raw/ snapshots; 2026-11-04 fetch timestamps; PSX Terms of Use + Data Vending licensing recorded; redistribution NOT cleared by free access |
| 3 | No API assumed; no bypass of authentication/paywalls/CAPTCHAs/access controls | PASS | No scraper built against psx.com.pk; direct DPS access failed on this VM (D-51) and was reported, not worked around |
| 4 | Company/security masters on existing Phase 3 tables; no duplicate tables except registry_evidence | PASS | Only new table is registry_evidence (migration a909e8449cdd); 57 public tables after upgrade |
| 5 | Previous names/tickers preserved with effective dates + source evidence | PASS | symbol_history on ticker change; PG check + tests cover it |
| 6 | Source classification kept separate from normalized classification; no sector by guesswork | PASS | Per-source sector rows, canonical_sector_id NULL; auditor check (e) PASS |
| 7 | Deterministic normalization/matching only; no LLM as authority | PASS | normalization.py + matching.py; ticker-only and name-only never merge (auditor check (b) PASS) |
| 8 | Ambiguous records kept original, PENDING_REVIEW, never auto-merged | PASS | Importer + tests + auditor check; reports de-duplicated (M3 fix) |
| 9 | Idempotent incremental import with the 8 statuses | PASS | Re-import delta 0 (auditor check (c) PASS for core entities/evidence); lifecycle statuses stored (M4 fix) |
| 10 | Never mark the whole registry verified on import success | PASS after audit fix | Original VERIFIED rule was unsafe (audit H1) and was corrected: VERIFIED now requires ≥2 distinct agreeing sources including one official; a lone official import stays UNVERIFIED |
| 11 | Reconciliation against a DATED official snapshot; no invented totals | PARTIALLY COMPLETE | reconcile() implemented and tested; NO usable dated snapshot obtained (DPS Listing Status 0 rows via text fetch, D-52; direct DPS access fails, D-51; market-watch copy is a stale 2026-01-25 cache, D-53, excluded). Coverage is None with an explicit no-claim note. This is the population blocker |
| 12 | Read-only APIs (9 endpoints) with pagination/search/filters | PASS | registry.py endpoints; live API smoke test: all 9 return 200 on empty DB, 404 for unknown ids, 422 for limit out of range |
| 13 | Registry frontend with "unavailable" labels, no fabricated data | PASS | /companies page; build/typecheck/lint pass; live preview UNVERIFIED (no browser screenshot obtainable by a generic subagent) |
| 14 | Configurable sync researched, not assumed; no scheduler started | PASS | sync_configuration.md: manual-only, all sources disabled, no scheduler |
| 15 | Synthetic test records kept separate from production | PASS | Live DB counts 0/0/0/0 before and after all test runs; all test imports rolled back |
| 16 | Tests actually executed and reported | PASS | Backend 44 passed (26 Phase 4 + 18 Phase 2 re-run); Ruff clean; frontend typecheck/lint/build pass; Vitest 11 passed; PG check PHASE4_PG_CHECK_OK including adversarial paths |
| 17 | Independent audit completed; findings fixed or accepted in writing | PASS | independent_audit.md: PASS WITH LIMITATIONS, 0 CRITICAL, 1 HIGH, 5 MEDIUM, 6 LOW. All 12 findings fixed in code/docs except the ISIN check-digit recomputation, which is ACCEPTED as a documented Phase 5 validation concern (format-check only, stated in docs), and the pytest fake-session limitation, which is ACCEPTED with the live-PG adversarial check as mitigation. The source_key provenance control is carried forward as a Phase 5 pre-population requirement (see completion report) |

## Overall verdict

**PARTIALLY COMPLETE.** The registry engine, APIs, frontend,
tests, and audit are verified. Production population is blocked
on a usable dated official snapshot (criterion 11), which is an
external-source blocker, not a code defect. The phase is NOT
COMPLETE because a mandatory criterion (population +
reconciliation against a dated snapshot) cannot be satisfied
with the sources obtainable in this environment.

## Carried forward to Phase 5 (must be resolved before any population run)

1. Obtain a dated official registry snapshot (live-browser
   extraction of the DPS Listing Status table, or a documented
   machine-readable official list) — parent task.
2. Add a source_key provenance control (trusted-collector
   registry) before treating any VERIFIED status as
   independently confirmed.
3. Resolve the PSX redistribution/licensing question for
   internal registry use (PSX Terms of Use restrict copying,
   distribution, and automated navigation without prior written
   permission; Data Vending makes redistribution licensed).
4. Phase 1 gates G-01 (source verification) and G-03 (count
   reconciliation) remain open; G-03 in particular cannot close
   without the dated snapshot.
