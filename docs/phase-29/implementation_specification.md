# Phase 29 Implementation Specification — End-to-End Integration, System Acceptance and Independent Audit

## 1. What this phase is

Phase 29 is an **audit phase, not an analysis phase**. It produces no new
financial output, collects no new market data, promotes no quality
status, and executes nothing. It proves — with independent recomputation
from raw stored rows, with scenario tests against the live database,
and with source/license/privacy scans of the worktree — that the
platform built in Phases 1–28 behaves as specified, and it records every
gap it finds in a severity-ranked defect register instead of hiding it.

Two rules govern the whole phase:

1. **The auditor does not rewrite the books.** When the audit finds a
   stale stored artifact, it records the defect with its exact fix; it
   does not hand-edit the stored row. In-place correction would destroy
   the evidence the audit exists to check, and versioned artifacts
   (reports, decisions) are corrected by supersession, never by edit.
2. **A failed check is a stored fact, never averaged away.** A
   recomputation that does not match, a scenario that does not pass,
   and a gate item that is not met are all recorded with their
   evidence, and the verdict follows from them — never the reverse.

## 2. Design

### 2.1 Tables (migration 20261104_0024, four new tables)

Precedent (Phases 11–28): this phase stores its own tables rather than
retrofitting Phase 3 tables. These tables carry no `quality_status`:
they are audit records, not business data, and no quality-status
promotion ever applies to them. No order, execution, external-send, or
publication concept exists in these tables. No credentials are stored
anywhere here. Integer primary keys (not `IdMixin` `Identity`): see
`backend/app/models/acceptance.py` for the SQLite portability reason
(same as Phases 24–28).

- `acceptance_runs`: one row per acceptance invocation, keyed by a
  unique `run_id` (idempotency key: a second `--commit` with the same
  `run_id` writes nothing). Carries the run date, the overall verdict,
  and the gate evaluation JSON.
- `acceptance_scenarios`: one row per (run, scenario): the outcome
  (`pass` / `fail` / `blocked` / `not_evaluable`), the evidence JSON,
  and the reason. A `blocked` scenario is not a failure of the system:
  it means the chain cannot complete for a stated external reason
  (Terms gate, pending re-runs). A `not_evaluable` scenario means the
  system has no test data for that case in scope; it is recorded, not
  passed by default.
- `acceptance_recomputations`: one row per (run, check): the claimed
  value (from the stored artifact or the earlier phase report), the
  independently recomputed value (from raw stored rows via direct
  queries, never by re-running the phase service code), whether they
  match within the stated tolerance, and the method. A mismatch row is
  kept, not deleted: it is the audit finding.
- `acceptance_defects`: one row per (run, defect key): severity
  (`critical` / `high` / `medium` / `low`), lifecycle status (`open` /
  `fixed` / `accepted`), impact, and the exact unblocker or fix.
  `accepted` means documented and consciously deferred with a stated
  trigger — it is not a silent pass.

### 2.2 Services (`backend/app/services/acceptance/`)

- `scenarios.py`: 15 end-to-end scenarios (see §3). Each scenario is a
  pure function of the session returning (outcome, evidence, reason).
  Company identity is resolved by ticker everywhere (surrogate ids
  shift across fresh imports — see the Phase 23 repair).
- `recompute.py`: 15 independent recomputations (see §4). All values
  are recomputed from raw stored rows with direct queries and Decimal
  arithmetic, never by calling the phase service that produced them.
  Tolerances: exact for counts and integer money values; 1e-6 for
  ratios and multiples stored at 6 decimal places.
- `audits.py`: security, licensing, and privacy scans (see §5). Scans
  run against the worktree checkout and the live database. A scan hit
  is reported with its file and line, never summarized away.
- `defects.py`: the severity-ranked defect register (see §6).
- `gate.py`: the five acceptance-gate items, each evaluated to
  `met` / `not_met` / `partial` with evidence.
- `runner.py`: `accept(run_id, commit)` — dry-run default (computes
  everything, writes nothing); `--commit` inserts the run, scenarios,
  recomputations, and defects in one transaction and rolls back on
  failure instead of storing a partial run. A second `--commit` with
  the same `run_id` writes nothing (idempotency: the run row is the
  guard). The runner never writes a business row, never promotes a
  status, never collects new data, and never executes anything.

### 2.3 CLI, API, dashboard

- CLI `scripts/run_acceptance.py`: `--run-id` (default
  `phase29-acceptance-2026-11-05`), `--commit`. Dry-run default.
- API `backend/app/api/v1/endpoints/acceptance.py`: GET-only, six
  routes — `/summary`, `/runs`, `/scenarios`, `/recomputations`,
  `/defects`, `/gate`. Everything is read from stored rows or
  explained as absent with a reason.
- Dashboard `frontend/app/admin/acceptance/page.tsx` (nav entry in
  `frontend/lib/nav.ts`): summary, gate table, scenario table,
  recomputation table, defect table. Read-only; runs execute through
  the CLI.

## 3. End-to-end scenarios

| Key | Case | Expected behaviour |
|---|---|---|
| `chain_hubc_full` | HUBC discovery → price → statement → fundamentals → valuation → macro → forecast assessment → risk → decision → portfolio → alert → report | Every link present; insufficiencies honestly recorded, none fabricated |
| `chain_ogdc_full` | Same chain for OGDC | Same |
| `chain_nml_full` | Same chain for NML | Same; NML decision is SCREEN_FAIL / INSUFFICIENT_EVIDENCE by gate, not by error |
| `chain_hbl_partial` | Same chain for HBL | BLOCKED: statements loaded (30), analysis links pending the post-Phase-30 re-runs |
| `missing_source` | A company with no analysis (HBL) | Endpoints and reports show pending states, never errors or fabricated values |
| `delayed_data` | Prices stop at 2026-11-03 | Source health flags market_prices stale; session-gap SLO unmet and recorded |
| `ticker_rename` | ENGRO / ICI / CNERGYICO | Absent from the registry; ENGROH / LCI / CNERGY present; no silent rename or merge |
| `corporate_action` | Dividend actions | 5 actions, dates NULL, no adjusted series stored (rules defined_not_applied) |
| `restatement` | Statement revisions | NOT_EVALUABLE: 0 document versions; versioning discipline documented but unexercised |
| `suspended_security` | Suspended securities | NOT_EVALUABLE: the registry carries no suspended/delisted flag in scope; the 26 priceless tickers are named in the Phase 12 run report, not hidden |
| `no_quote` | AGLNCPS | In universe, no price row; eligibility evidence records IN_UNIVERSE_NO_QUOTE, never a zero price |
| `model_failure` | Forecasts, decisions, backtests with no data | Abstention, not fabrication: 120/120 assessments insufficient, 4/4 user-facing WITHHELD, 5/5 backtests NOT_RUNNABLE |
| `process_restart` | Start/stop/restart | ops/start.sh (exec fix) + fresh-environment test + post-report re-test + twice-proven VM-replacement recovery |
| `provenance_warnings` | User-visible provenance and quality warnings | 22 reports DRAFT, 0 published externally; QA gate; dashboard honesty layer |
| `point_in_time` | No look-ahead | Decision price_date (2026-11-03) ≤ decision_date (2026-11-04); P/E publication (2026-09-21) ≤ price date; Phase 3 forecasts table 0 rows; backtest metrics 0 computed; report dates ≤ cut-off 2026-11-04 |

## 4. Independent recomputations

| Check | Claimed (stored / reported) | Recomputed from |
|---|---|---|
| `hubc_gross_margin` | 0.417400 | HUBC income line items: gross_profit / revenue |
| `hubc_trailing_pe` | 5.155254 | HUBC close 197.24 / EPS 38.26 |
| `ogdc_trailing_pe` | 17.881625 | OGDC close 303.63 / EPS 16.98 |
| `portfolio_reconciliation` | invested + cash = 1,000,000 (×3) | Holdings value sums + capital |
| `breadth_coverage` | 444/470 = 0.944681 | Distinct price tickers / companies |
| `volume_median` | 54,631.5 | Median of 444 volumes |
| `top10_volume_share` | 49.249694% | Top-10 volume sum / total volume |
| `hbl_sfp_identity_2025` | assets = liabilities + equity | HBL balance-sheet total lines, 2025 |
| `hbl_sfp_identity_2024` | assets = liabilities + equity | HBL balance-sheet total lines, 2024 |
| `hbl_pat_eps_2025` | PAT 66,763,916; EPS 45.48 | HBL income line items |
| `screen_matched_counts` | 194 / 44 / 1 / 2 / 0 | screen_runs matched_count recount from screen_results |
| `alert_totals` | 89 = 82 INFO + 6 WARNING + 1 CRITICAL | alerts by severity |
| `report_figure_census` | 541 = 335 + 199 + 7 (Phase 22 claim) | report_figures by status — EXPECTED MISMATCH (see §7) |
| `decision_completeness` | HUBC/OGDC scored 6/7 (original Phase 15 report) | decisions.scored_dimensions — EXPECTED MISMATCH (see §7) |
| `drift_vs_phase24_baseline` | Phase 24 baseline counts | Current counts — EXPECTED DIFFERENCE equals exactly the HBL additions |

## 5. Security, licensing, and privacy audits

- Execution identifiers (`place_order`, `execute_order`, `submit_order`,
  `execute_trade`, `place_trade`, Broker classes, `/orders` routes):
  expected 0.
- Dangerous constructs (`eval`, `exec`, `pickle.load`, `os.system`,
  `shell=True`): expected 0 except the allowlisted tesseract OCR call
  (fixed argv list, no shell) in `financial_statements/extract.py`.
- Secret scan over tracked files: expected no credential literals; the
  only `passwd` hits are redaction-substring keys and traversal-probe
  test strings, both benign by design.
- Tracked datasets: expected 0 `.csv` / `.pdf` files at the Phase 28
  tip and at every remote branch tip (37 tips scanned).
- Tracked environment files: expected 0 real `.env` (only `.env.example`).
- Write routes: expected 0. Upload endpoints: expected 0. Docker
  invocations in code/ops scripts: expected 0 (test-file mentions of
  the ban only).
- PII columns: expected none except auth hashes (`password_hash`,
  `password_salt`, `token_hash`) and the `token_use` count; auth tables
  are empty by decision (0/0/0).
- Licensing: direct backend dependencies recorded in
  `backend/LICENCES.md` with versions and licences. Gap found and
  fixed in this run: PyMuPDF and pdfplumber were used by Phase 7
  extraction but were absent from `backend/requirements.txt` (unpinned)
  and from `backend/LICENCES.md` (Phase 1 gate G-02/G-04 requires
  recording before use). Fix: pin the installed versions and record
  the licences (PyMuPDF AGPL-3.0-or-commercial, pdfplumber MIT).
  PyMuPDF's AGPL status is recorded as a review item before any
  public hosted deployment or redistribution — not as a current
  violation claim: this project is local research, not a distributed
  network service.
- Public-repo boundary, stated honestly: the dataset/secret scans
  cover branch tips, not every historical commit. The `.gitignore`
  rules (financial reports, Phase 5 CSVs, `.env`) plus the tip scans
  are the evidence; a full-history scan is not claimed.

## 6. Defect register (severity-ranked)

Severity rules: `critical` = data corruption, security breach, or
execution risk; `high` = a wrong financial output or a broken critical
workflow; `medium` = a misstated metric, a blocked workflow with a
documented workaround, or a pre-distribution review item; `low` = an
accepted limitation with no wrong output. `open` defects have an exact
fix; `accepted` defects are documented and deferred with a stated
trigger; `fixed` defects were fixed in this run with regression tests.

| Key | Severity | Status | Defect |
|---|---|---|---|
| D-01 | medium | accepted | Terms gate: collection jobs paused, GEM/Non-Compliant missing, full-470 verification blocked. Unblocker: written PSX permission evidence (user-owned). |
| D-02 | medium | accepted | Single trading day (2026-11-03): technical values, forecasts, backtests, series risk blocked. Unblocker: more trading days (Terms-gated). |
| D-03 | medium | accepted | HBL Phases 8+ re-runs pending: statements loaded, analysis links missing. Unblocker: post-Phase-30 re-run batch (banking rule: Phase 9 uses the bank residual-income model for HBL). |
| D-04 | medium | open | Surrogate-id traps: macro sector ids and news publication-date maps still keyed by pre-replacement surrogate ids. Workaround documented (temporary patch + revert + re-run). Fix: permanent name-based sector resolution and ticker-based news mapping, with fixture tests. |
| D-05 | medium | open | Stale downstream artifacts from recovery #6 intermediate news state (see §7). Fix: re-run the decision engine and regenerate the one event brief as part of the post-Phase-30 HBL re-run batch. |
| D-06 | low | accepted | Vector retrieval registered but not implemented (no verified local embedding model). |
| D-07 | low | accepted | No live auth accounts; enforced mode fail-closed (401) until an admin account is created (parent/user decision). |
| D-08 | low | accepted | 4 of 14 SLOs unmet (price coverage, session gap, previous-close completeness, news coverage) — data limitations, Terms-gated. |
| D-09 | low | accepted | No persistent backup-encryption key; no system-wide service install; no host cron (Phase 28). |
| D-10 | low | accepted | No frontend token support for enforced mode (dashboard calls public GET APIs; needed only if enforced mode is ever required for the dashboard). |
| D-11 | low | accepted | RAG benchmark history partial: 6 rows (r3 only); r1/r2 runs of superseded code not reproduced and not fabricated (VM replacement #6 divergence). |
| D-12 | low | open | Token-gated report approval (Phase 24 candidate; belongs to no phase brief so far). |
| D-13 | low | fixed | PyMuPDF/pdfplumber unpinned and unrecorded (see §5). Fixed in this run: pins + LICENCES rows + regression test. |
| D-14 | medium | accepted | PyMuPDF AGPL-3.0-or-commercial: review before any public hosted deployment or redistribution (see §5). |

No critical or high defects were found. The two medium open defects
(D-04, D-05) are documented with exact fixes; neither changes any
decision conclusion, total, confidence, or user-facing value, and
neither blocks the Phase 30 handover.

## 7. The headline audit finding (recovery #6 intermediate state)

During VM replacement #6 recovery, the Phase 11 news seed first ran
with publication dates keyed by pre-replacement document ids
(13/14/15 vs live 7/8/9), seeding NULL earnings dates. Two downstream
artifacts were built from that intermediate state and never refreshed
after the news fix (which deleted the wrong events and re-ran with the
correct dates: HUBC 2026-09-21 known, NML unknown, OGDC 2026-02-23
known):

1. **One stale report figure.** `event_brief` for `news:HUBC:earning`,
   figure `event_date`: the database holds `insufficient_inputs`
   ("Event date is NULL in the stored row"), while the committed
   Markdown export shows `2026-09-21 | computed` and a fresh rebuild
   computes it. The stored figure is absent, not wrong — but it
   disagrees with its own export, so the figure census is 334
   computed / 200 insufficient instead of the Phase 22 claim of
   335 / 199 (total unchanged at 541).
2. **Two stale decision rows.** The decision engine ran at 23:37, four
   minutes before the corrected news links landed at 23:41, so HUBC
   and OGDC snapshots record `news_event` row ids 1/2/3 with NULL
   dates and `unknown` status. Their `news_event` dimension is
   therefore ABSENT instead of 0 (neutral): `scored_dimensions` 5
   instead of the original Phase 15 run's 6, completeness 0.7143
   instead of 0.8571. Totals (+2 HUBC, 0 OGDC), conclusions
   (HOLD_CANDIDATE), confidence (LOW), and user-facing values
   (WITHHELD) are all unaffected, because the news dimension is
   neutral (0) in rules v1. NML (genuinely unknown date) and HBL
   (no statements at decision time) are unaffected.

Both artifacts are recorded as defect D-05. They are not fixed in this
phase, for two reasons: the auditor does not rewrite the books it
audits, and the decision re-run would also pick up HBL's newly loaded
statements, which belongs to the sequenced post-Phase-30 HBL re-run
batch — not to this audit. The Phase 30 handover must carry D-05
forward with that exact fix.

## 8. Acceptance gate evaluation

| Gate item | Result | Evidence |
|---|---|---|
| All critical workflows pass | NOT_MET | HUBC/OGDC/NML chains pass honestly; the HBL chain is BLOCKED at statements (D-03). |
| Critical/high defects resolved | MET | 0 critical, 0 high in the register. |
| No look-ahead or fabricated financial data | MET | Point-in-time checks pass; forecasts table 0 rows; backtest metrics 0 computed; abstentions honest. The §7 staleness is omission, not fabrication, and is recorded, not hidden. |
| Public repo contains no restricted dataset or secret | MET | 0 tracked `.csv`/`.pdf` at the Phase 28 tip and across all 37 remote branch tips; 0 real tracked `.env`; secret scan clean (benign hits only). Boundary: tips scanned, not every historical commit. |
| Independent auditor signs off with evidence | PARTIAL | This independent recomputation, scenario, and scan evidence is complete; human sign-off belongs to the user/parent and is pending. |

## 9. Verdict

**PARTIALLY COMPLETE.** The acceptance gate's testable items hold
except the two stated gaps: the HBL chain cannot complete until the
post-Phase-30 re-runs, and human sign-off is pending. Forcing COMPLETE
would misrepresent both. Phase 30 (release + handover) follows; the
handover must carry forward defects D-01–D-14 (especially D-03, D-04,
D-05), the lineage note that HBL extraction code lives on the side
branch `phase-07-hbl-extraction` (not on the phase lineage), and the
recovery recipe extended with the HBL extraction commit and the
Phase 29 commit.
