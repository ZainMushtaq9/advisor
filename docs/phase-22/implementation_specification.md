# Phase 22 — Implementation Specification

Status: implemented on branch `phase-22-reports` (from
`phase-21-alerts` dbeee4a). Report date 2026-11-04, data
cut-off 2026-11-04, price date 2026-11-03.

## Objective (playbook brief, lines 1623–1681)

Generate consistent, evidence-backed research documents from
validated platform data and analysis: company dossiers,
earnings updates, valuation reports, sector outlooks, event
briefs, portfolio reviews, risk reports, and market
overviews. Every key figure has a traceable source or
calculation; the data cut-off is explicit; reports export
without layout errors; nothing is published externally
without permission (no publish step exists at all).

## What was built

| Piece | Path |
|---|---|
| 6 tables | `database/migrations/versions/20261104_0019_phase_22_reports.py` (head 0019) |
| ORM models | `backend/app/models/reports.py` (registered in `backend/app/models/__init__.py`) |
| Template registry + fixed dates + disclaimer | `backend/app/services/reports/__init__.py` |
| Figure rules (pure) | `backend/app/services/reports/evidence.py` |
| Draft QA (pure) | `backend/app/services/reports/validation.py` |
| Markdown / HTML / PDF renderers | `backend/app/services/reports/render.py` |
| Draft builders (read-only) | `backend/app/services/reports/assembly.py` |
| Runner (writes, lifecycle, exports) | `backend/app/services/reports/runner.py` |
| CLI | `scripts/run_reports.py` |
| GET-only API | `backend/app/api/v1/endpoints/reports.py` (registered in `backend/app/api/v1/router.py`) |
| Pure tests | `backend/tests/test_reports_phase22.py` |
| PDF dependency | `fpdf2==2.9.0` in `backend/requirements.txt` (free, pure Python; verified in the venv) |

No Phase 3 table was reused or altered (Phases 11–21
precedent). No broker, order, or execution concept exists
anywhere in the new code (proven by the no-execution test
scan). No external send exists: APPROVED means internally
reviewed only.

## Design decisions

1. **Drafts are dicts, not rows, until QA passes.** The
   builder produces a dict; `qa_draft` checks it; only then
   does the runner persist it. A QA failure refuses the
   commit and reports the problems.
2. **One value form per computed figure.** Numeric `value`
   for prices, ratios, and counts; `value_text` for dates and
   labels. A non-computed figure carries neither — never a
   zero, never an estimate, never a dash that reads as a
   number. NULL renders as "not available".
3. **No price_target figure kind.** `figure()` rejects any
   key containing `price_target`. Valuation scenarios list
   computed and unavailable methods with reasons; they never
   state a target price.
4. **Cut-off discipline.** REPORT_DATE and DATA_CUTOFF_DATE
   are both 2026-11-04 (the latest date for which any stored
   observation exists; also the Phase 15 decision date and
   the Phase 21 alert as-of date). PRICE_DATE is 2026-11-03
   (the single trading date with stored prices). The only
   stored rows postdating the cut-off are SCHEDULED future
   events (SBP minutes 2026-11-20, MPC meeting 2026-12-14),
   which appear only in explicitly labelled scheduled
   sections, never as occurred. The event-brief builder for a
   future macro event adds a `scheduled` warning.
5. **Quality is inherited, never promoted.** Every figure
   carries its inputs' quality status. All Phase 7–21 inputs
   in this run are UNVERIFIED except the six Phase 10 macro
   observations documented as VERIFIED via SBP/PBS
   cross-publisher agreement (see the Phase 10 run report;
   later phases must not treat those as H1-verified in the
   registry sense).
6. **Exports.** Markdown and HTML are archived under
   `docs/phase-22/reports/` (committed, readable). PDFs go
   to gitignored `storage/research_reports/`; only their
   SHA-256 and path are recorded in `report_exports`. The
   project never commits PDFs or CSVs.
7. **Idempotency.** Templates by (template_key, version);
   reports by (template_key, subject_key, report_date,
   data_cutoff_date, template_version) among current rows. A
   second `--commit` reuses existing reports and writes
   nothing new. Versioning is via supersedes_id/is_current;
   a report is never edited in place (no UNIQUE blocks a
   future superseding version with the same dates).
8. **Approval is a CLI transition only.** DRAFT → APPROVED
   or DRAFT → REJECTED; anything else exits 1. The API is
   GET-only.

## Seed list (22 reports)

Company dossiers, earnings updates, and valuation reports
for HUBC, NML, OGDC; sector outlooks for POWER GENERATION &
DISTRIBUTION, TEXTILE COMPOSITE, OIL & GAS EXPLORATION
COMPANIES; event briefs for macro:2026-10-26:mpc_meeting and
news:HUBC:earning; portfolio reviews for the three Phase 16
SIMULATED portfolios; risk reports for HUBC, NML, OGDC, and
MARKET; one market overview. HBL is deliberately absent: it
has no stored statements, so a dossier would be an empty
shell; the design accepts it later via a Phase 7 load plus a
Phase 22 re-run, with no redesign (see the HBL-pending note
in the run report).

## What is NOT_CALCULABLE (with reasons)

See `evidence_method.md` and the run report. In short:
returns (zero return observations from one price date);
series risk metrics (volatility, beta, drawdown, VaR/ES —
warm-ups unmet, previous_close NULL); share-count valuation
methods (no shares-outstanding source); DCF/DDM (no
source-backed discount rates or DPS series); peer medians
(each company alone in its sector); technical values (0
calculable Phase 6 values); forecasts (Phase 13 abstained on
all 120 assessments); user-facing decisions (all WITHHELD);
backtest results (Phase 17 NOT_RUNNABLE); vector retrieval
(not implemented); universe-wide news coverage (Terms-gated).
Every one of these appears in reports as an
insufficient_inputs figure with its reason, or as an
explicit "not available" statement — never as a number.
