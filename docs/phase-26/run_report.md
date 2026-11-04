# Phase 26 — Run Report

**Verdict: PARTIALLY COMPLETE.** The acceptance gate's testable
items hold (reproducible out-of-sample rules, baselines and
negative outcomes included, promotion governed by evidence, no
unsupported accuracy claims), but the underlying data stays
limited exactly as Phases 4–25 recorded it: 0 predictions, 0
matured labels, 0 recommendation outcomes, 3-company coverage,
HBL pending. COMPLETE would misrepresent those limits.

## What changed

- **Branch:** `phase-26-evaluation`, new branch from
  `phase-25-automation` (`a129614`).
- **Migration:** `20261104_0021` → `20261104_0022` (7 evaluation
  tables), applied to the live DB.
- **Seed run:** `phase26-evaluation-2026-11-05` — dry-run first
  (would_write), then --commit (created), then a second --commit
  (skipped_existing, 0 new rows — idempotency proven).
- **No register files edited** (parent consolidates). No merge
  to main, no force-push, no history rewrite, no cross-push, no
  CSVs/PDFs committed, no credentials anywhere, no live auth
  accounts created (auth tables still 0/0/0 by decision).

## Seed run evidence (live, parent-verifiable)

- **Metrics:** 44 total — 32 computed, 11 not_evaluable (NULL
  values, never zero-filled), 1 not_applicable (vector
  retrieval).
- **Forecast:** predictions 0, assessments 120 (0 computed, 120
  insufficient), matured labels 0 (latest price date equals
  origin 2026-11-03). MAE, RMSE, directional accuracy, interval
  coverage, baseline-relative performance: NOT_EVALUABLE.
- **Recommendation:** decisions 4, user-facing abstention rate
  1.0 (WITHHELD 4/4), outcomes 0, adverse observed 0 among 0
  recorded (not a claim that none occurred). Subsequent return,
  benchmark-relative return, precision, recall, calibration:
  NOT_EVALUABLE.
- **Agent:** 6/6 evaluations PASS, pass rate 1.0 (all 6
  categories 1/1).
- **RAG:** 6 cases, recall@5 1.0 (page level), pass rate 6/6,
  mean citation precision 0.4667 (direct-case 0.2000 values
  included, not hidden). Vector retrieval not_applicable.
- **Backtest:** 5 runs, 0 runnable, 0 metrics computed; Sharpe
  NOT_EVALUABLE (no return series, no validated risk-free
  series).
- **Reports QA:** 22 reports, 0 approved, 0 published
  externally, 541 figures (335 computed).
- **Drift:** 0 differences vs the Phase 24 baseline
  (EXPECTED_COUNTS). No business count changed.
- **Golden suite:** 14/14 passed (4 source matching, 1 entity
  resolution, 1 tool selection, 1 citation, 1 extraction, 1
  summarization, 2 refusal/abstention, 1 injection resistance,
  1 hallucination, 1 conflicting sources).
- **Model cards:** 9, all NOT_PROMOTED. **Promotion gates:** 5,
  all NOT_MET, each with its exact missing evidence.
- **Datasets:** 8 versioned, with out-of-sample split policies.

## Independent audit (hand-checked vs live DB)

Stored metrics re-read and recomputed from source tables:
recall 6/6 → 1.0 ✓; abstention 4/4 → 1.0 ✓; mean citation
precision 0.4667 ✓; HUBC close re-read 197.2400 after the run
(unchanged) ✓; HBL documents 0 ✓; max stored summary length
157 ≤ 280 ✓; companies 470/470 UNVERIFIED despite 61 LEAP
rows ✓. Business counts unchanged after the run (companies
470, prices 444, reports 22, alerts 89, job runs 71, auth
users 0).

## Tests

- Backend suite: **408 passed** (394 + 14 new), 0 failed.
  Ruff check + format clean on all new/changed files.
- Frontend vitest: **11 passed**. ESLint clean on new/changed
  files. Prettier clean.
- Production build (`next build --webpack`): **25 routes**
  (24 + /admin/evaluation). Turbopack note from Phase 23
  still applies (symlinked node_modules worktree artifact).
- Playwright phase26 suite: **6 passed, 0 failed** (3 specs ×
  desktop + mobile). One test-only fix during the run: the
  page-heading matcher needed `exact: true` (it also matched
  "Latest evaluation run" as a substring).
- No-execution scan: 0 hits. Evaluation endpoints: GET-only
  (9 routes).

## Corrections made during this run (not hidden)

1. `matured_labels` was first drafted as a hardcoded zero;
   corrected so the runner counts assessments whose horizon
   actually matured (0 in the seed run, for the right reason).
2. The alias-collision golden check first used tickers present
   in the resolved text; the resolver rightly preferred the
   ticker match at 1.0. Corrected to tickers absent from the
   text, so the shared stripped alias is the only match.
3. `predictions_count` was first hardcoded 0; corrected to
   count the Phase 3 forecasts table (0 rows, now read, not
   assumed).
4. A nonsense `rag_chunks` expression in an early runner draft
   was replaced with a real RagChunk count before any run.
5. A test assertion about the adverse-outcome reason
   contradicted its own clarifying wording; corrected to
   assert the clarification is present.

## HBL-pending note (unchanged)

HBL remains pending (CY2025 PDF blocked at the issuer-site
challenge; live-browser download runs separately, no result
yet). Phase 26 touches no company data; a 4th company later
needs no Phase 26 redesign (evaluation resolves by ticker;
the HBL golden case flips from missing_data to evaluated
when its documents land, and the run report must say so).

## Remaining blockers with exact unblockers

- Written PSX permission evidence (user-owned) → collection
  jobs unpause, full-470 verification, new PSX collection,
  and with them the first matured forecast labels and
  recommendation outcomes.
- More trading days (Terms-gated) → technical values,
  forecasts, backtests, series risk, and evaluated predictions.
- HBL PDF via browser download → 4th company everywhere,
  including a 4th decision and a 4th dossier.
- Verified local embedding model → vector retrieval (then the
  RAG card and the vector metric become evaluable).
- Internal review decision → first APPROVED report (CLI
  transition only, no web approval by design).
- Parent/user decision → first live auth account (auth tables
  intentionally 0/0/0).
- Real deployment decision → enforced-mode production proof,
  backup encryption, dependency audit, frontend token
  support, multi-instance rate limiting.
- Follow-ups (not Phase 26 changes, still open from Phase
  25): permanent name-based sector resolution; permanent
  ticker-based news publication-date mapping (the same
  surrogate-id trap will recur on the next recovery
  otherwise).
- Phase 24 candidate (a) token-gated report approval: still
  open (does not belong to the evaluation brief either;
  candidate for a later phase).
