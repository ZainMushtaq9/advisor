# Phase 22 — Rendering and QA

## Renderers

- **Markdown** (`render_markdown`): canonical form. Header
  with report/cut-off/price dates, audience, and DRAFT
  status; sections in template order; a figures table
  (figure, value, status, kind, source); a warnings list.
  Archived under `docs/phase-22/reports/`.
- **HTML** (`render_html`): standalone page with a small
  stdlib converter for the emitted subset (## headings,
  paragraphs, bullet lists, **bold**); figures as an HTML
  table. Archived alongside the Markdown.
- **PDF** (`render_pdf`, fpdf2 2.9.0, free pure Python):
  title, dates line, sections, figures, warnings. Returns
  ("ok", bytes) or ("not_available", None) when fpdf2 is not
  installed; genuine rendering errors propagate. PDFs go to
  gitignored `storage/research_reports/`; only SHA-256 and
  path are recorded in `report_exports`.

## Layout QA rule

A render that raises is a failure, never a partial file.
Callers write files only after the full render succeeds.
The runner renders all three formats before writing any of
them for a report; a failure aborts that report's commit
(the runner reports it as a failure, not a partial write).

## Draft QA (validation.py, pure)

A draft passes only when ALL of these hold:

1. Template is known and the emitted section list exactly
   equals the template's section list (order included).
2. Data cut-off date and report date are present.
3. The full disclaimer appears in the joined bodies.
4. No forbidden wording appears: "target price", BUY/SELL
   … shares, "place an order", "execute a trade",
   "guaranteed return".
5. At least one figure is present, and every figure passes
   `check_figure` (kind/status known, value-form rules,
   source table and note present, no price_target,
   analyst_inference never computed).
6. Every non-disclosures section cites at least one figure
   key or states "not available".

QA failure refuses the commit. The CLI reports the problems
as JSON; nothing is stored or exported for a failed draft.

## Checks performed in this run

- Pure test suite: `backend/tests/test_reports_phase22.py`
  (registry, figure rules, cut-off, stale threshold,
  unknown dates, QA pass/fail, rendering, section-order
  enforcement, no-execution scan, GET-only endpoints).
- Full backend suite plus Ruff check and format on all
  new/changed files (see the run report for counts).
- Live API checks via TestClient after commit: templates,
  reports list, one report detail, status, unknown
  template/report 404s (see the run report).
- Independent audit: one dossier's figures hand-checked
  against DB values (HUBC close 197.24, gross margin
  0.4174, trailing P/E 5.1553) — see the run report.
- Export rendering QA: every committed report produced a
  Markdown file, an HTML file, and a PDF file (or a
  recorded not_available); a render failure would have
  aborted that report instead of writing partial files.
