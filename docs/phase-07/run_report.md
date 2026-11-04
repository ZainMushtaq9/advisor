# Phase 7 run report — sampled financial-statement extraction

Date: 2026-11-04 (run during the Phase 7 coordinator session).
Branch: `phase-07-financial-statements` (from `6efede9`).
CLI: `scripts/run_financial_extraction.py` (`--dry-run` default /
`--commit`; exit 2 on fail-fast abort).

## Result (dry-run, final)

- Documents: 3 (HUBC annual report, NML quarterly report, OGDC
  interim filing).
- Statements: 16 (HUBC SFP 2 columns + P&L 2; NML SFP 2 + P&L
  2 statements × 2 columns; OGDC SFP 2 + P&L 2 statements × 2 columns).
- Line items: 316. Skipped (existing): 0. Skipped (validation): 0.
- Flagged rows: NONE. All balance identities and all section
  subtotals pass on every column (see below).
- No new tables. All rows load into the Phase 3 tables
  (`financial_documents`, `financial_statements`,
  `financial_statement_line_items`) with `quality_status =
  UNVERIFIED` (single source, rule H1). No row is promoted to
  VERIFIED or PARTIALLY_VERIFIED in this phase.

## Per-statement validation

Balance identity = total_assets == total_equity + liability totals
(Decimal arithmetic, never adjusted on failure).

| Statement | Columns | Identity | Subtotals |
|---|---|---|---|
| HUBC SFP (annual, FY2026 + FY2025) | 2026, 2025 | PASS both (258,007,509 + 97,833,209 + 66,722,726 = 422,563,444; 243,921,905 + 107,689,918 + 63,110,364 = 414,722,187) | PASS (non-current + current asset sections) |
| HUBC P&L | 2026, 2025 | n/a (income statement) | n/a |
| NML SFP (nine months to 31 Mar 2025 + 30 Jun 2024) | both | PASS both (159,920,849 + 133,212,040 = 293,132,889; 157,847,811 + 115,858,545 = 273,706,356) | PASS (all four sections) |
| NML P&L | nine-month + quarter, both years | n/a | n/a |
| OGDC SFP (half-year to 31 Dec 2025 + 30 Jun 2025) | both | PASS both (1,383,637,471 + 302,979,745 = 1,686,617,216; 1,348,236,596 + 306,369,374 = 1,654,605,970) | PASS (all four sections) |
| OGDC P&L | quarter + half-year, both years | n/a | n/a |

Subtotal checks treat a printed dash as contributing nothing to
the section sum (the face total equals the sum of the printed
components on that basis); the dash itself is stored as NULL,
never zero.

## Independent page-match (gate criterion)

- Embedded-text faces (HUBC, NML): every extracted field was
  re-read with a second extractor (`pdftotext -layout`) and
  re-parsed with the same page maps. Result: ZERO mismatches
  across all four maps (36 + 15 + 38 + 9 rows × their columns).
  Rows whose re-read mismatches would load with
  `extraction_confidence = NULL`; none occurred, so embedded
  rows load at confidence 1.0.
- OGDC faces (CORRECTED — see audit section): the OGDC PDFs
  carry embedded text (PyMuPDF: 2,917 chars on SFP p.7, 2,067 on
  P&L p.8), so extraction uses embedded text, not OCR. The
  second-method match is pdftotext: single-panel re-parse for
  the P&L, and the joint two-panel parser on pdftotext layout
  lines for the SFP (the two methods genuinely differ: sequential
  interleaved lines vs merged two-panel lines). Result: ZERO
  mismatches on all 39 SFP rows and all 6 P&L rows. OGDC rows
  therefore load at confidence 1.0, not 0.85. The coordinator
  additionally read the rendered SFP/P&L pages visually; every
  headline row and total matches. The OCR parser is retained
  and tested as fallback machinery only; no current sample map
  uses it.
- A second extraction of the same source is NOT a second source:
  the page-match satisfies the gate's "match source pages
  independently" criterion; it does NOT promote any row to
  H1-VERIFIED.

## Parser bugs found by the dry-runs and fixed

All were caught by the validation gate before any commit, never
by adjusting values:

1. Case-sensitive label matching missed HUBC
   "NON-CONTROLLING INTERESTS" (all caps). `normalise_text`
   now lowercases.
2. Hyphen-spacing variants ("financing- secured" vs
   "financing - secured", "loans- secured") missed labels.
   `normalise_text` now collapses spaces around hyphens.
3. Two-panel OCR: note references counted as value tokens
   corrupted leftover-token accounting, and bare subtotals
   sharing a line with the other panel's row were skipped.
   Rewrote the joint parser with consumed-span tracking and
   explicit leftover rules (own-side / cross-side / grand-total
   split).
4. OCR artifacts glued to numbers ("—«-110,865,473") were
   dropped. `_token_value` now takes the numeric core of a
   letter-free token.
5. A label wholly on the next line false-matched via the
   two-line join and stole the next row's values. Join matches
   now require the label to be genuinely split across the
   boundary.
6. Wrapped labels (NML EPS) lost the second line's values.
   Joined matches now take the remainder after the label's
   last word on the second line.
7. The 6-token junk-skip cap was too small for long labels
   ("Revenue from contracts with customers - net" needs 7
   skips before its note reference). Cap raised to 20, and a
   punctuation dash before a junk word is skipped while a
   dash before a number is kept as a missing value.
8. Bare specs never flagged incompleteness. They now carry
   `incomplete_values` when fewer than the column count is
   found.
9. The Phase 6 immutability trigger blocks UPDATEs on
   versioned tables: the loader sets per-row confidence at
   INSERT (via `confidence_map`), never by post-load UPDATE.

## Column discipline (cumulative vs standalone)

- NML P&L: the printed nine-month columns and the printed
  quarter columns are stored as SEPARATE statement rows
  (nine_month period 2024-07-01→2025-03-31 and quarterly period
  2025-01-01→2025-03-31, plus comparatives). No derived
  standalone quarter is computed in this run.
- OGDC P&L: the printed six-month columns and three-month
  columns are stored as separate statement rows (half_yearly
  2025-07-01→2025-12-31 and quarterly 2025-10-01→2025-12-31,
  plus comparatives). No derived quarter is computed.
- HUBC: annual statements only; no interim columns exist.
- NML nine-month 2025 consolidated PAT is a LOSS of
  1,182,815 thousand as printed; it is NOT the full-year
  FY2025 PAT (6,013,519 thousand in DPS annual summaries).
  The two must never be conflated.

## Publication dates (never invented)

- HUBC: 2026-09-21 — consolidated auditor report date (PDF
  p.274, printed p.273; A. F. Ferguson & Co., UDIN
  AR202610080onH3rpTV1). Auditor opinion: unmodified
  ("true and fair view … in accordance with the accounting
  and reporting standards as applicable in Pakistan").
  Going concern: standard responsibility language only, no
  material uncertainty reported.
- NML: NULL — no publication/transmission date found in the
  report's front pages; recorded as missing, not estimated.
  CORRECTED: no review report is included in the document
  (verified by full-text scan of all 72 pages); the faces are
  marked Un-audited, so `audited_status` is `unaudited`, not
  `reviewed`. Auditors Riaz Ahmad & Company are named on p.3
  as company auditors, not as reviewers of these statements.
- OGDC: 2026-02-23 — RNS transmission date (annexure
  CS-04-08, 23 Feb 2026). Unaudited condensed interim
  statements.

## What was NOT done (gaps, with unblockers)

- LUCK annual report FY2026: transmission recorded on the DPS
  company page (4 Sep 2026) but no exact issuer-IR or DPS PDF
  link established via search. Unblocker: a parent browser
  task on the DPS company page or the issuer IR page to
  capture the exact PDF link.
- HBL CY2025 annual report: PDF not located via search (only
  news summaries, not loaded). Bank statement formats are
  Phase 8-relevant anyway; the sample already covers three
  sectors without it.
- KSE-100 expansion: needs verified source access per company;
  not started (sample-first rule).
- Cash-flow statements and statements of changes in equity:
  not extracted in this run (face maps cover SFP + P&L
  headlines only). Phase 7's brief includes full statement
  extraction; these faces remain for a follow-up pass.
- Auditor-opinion module: opinion wording + UDIN + firm are
  recorded above for HUBC only; a structured
  auditor-opinion table (per the brief) is not yet built.
  No opinion wording is paraphrased into a stronger claim.
- No new PSX market data was collected; no DPS PDF was
  downloaded (DPS used for discovery only). The PSX Market
  Data Terms question gating Phases 4–6 is untouched by
  this run and remains open, owned by the user.


## Independent audit (FAIL) and fixes — 2026-11-04

A depth-2 independent audit re-ran the suite and dry-run,
verified headline totals against the PDFs, and returned FAIL
before any commit, citing two wrong values hidden by the
"0 flagged" gate, one wrong method claim, and doc/code issues.
All items below were fixed and re-verified; nothing was merely
accepted.

- C1 (CRITICAL, fixed): HUBC `eps_total` loaded note-ref 43 as
  EPS ([43, 38.26]) because the bare-subtotal path took the next
  numeric tokens with no note-ref skip. Fix: `eps_total` is now
  a labeled wrapped spec (its header IS printed on P&L p.275),
  AND the bare path skips lone note-ref lines. Verified:
  eps_total = [38.26, 35.56], eps_continuing = [38.26, 35.44],
  eps_discontinued = [NULL, 0.12]. Regression tests added
  (labeled + bare variants).
- C2 (CRITICAL, fixed): NML `share_capital` loaded the share
  COUNT ([351,599,848, NULL]). Two defects: (a) the
  "ordinary shares" skip only fired same-line, but NML splits
  count and unit across lines; (b) `_token_value` returned
  is_value=True for the unparseable fragment "(30", occupying
  column 2 with NULL. Fixes: share-context stripping (keep
  tokens after "each" on the unit line; skip the preceding
  count line via lookahead) and parse-failure tokens are no
  longer value tokens. Verified on BOTH extractor layouts
  (PyMuPDF separate-lines and pdftotext values-on-unit-line):
  share_capital = [3,515,999, 3,515,999]. Regression tests
  added for both layouts. Note: the balance identity still
  passed with the wrong component because `total_equity` is a
  printed bare subtotal, not a sum of components — component
  rows are now additionally covered by the two-extractor match.
- H1 (HIGH, fixed): the "OGDC image-only → OCR" claim was
  false; embedded text exists (see page-match section above).
  OGDC maps reclassified to embedded text; SFP uses
  interleaved document order; page-match uses the joint
  two-panel parser on pdftotext lines. Method/confidence now
  recorded honestly (`pymupdf_embedded_text`, 1.0 on match).
- H2 (HIGH, fixed): a missing `tesseract` (or `pdftotext`)
  executable now fails fast with a clean exit-2 abort instead
  of a traceback (`shutil.which` guard + ValueError → _fail).
- H3 (HIGH, fixed): the implementation spec contradicted the
  CLI gate (it said failing statements still load; the CLI
  skips them) and overstated the report shape. Spec corrected
  to the CLI's skip behavior; the CLI report now additionally
  includes per-map `page_match_mismatches` summaries.
- M1 (fixed): subtotal checks unified in `validate.py`
  (`check_subtotal` with explicit `missing="fail"|"zero"`);
  the CLI's local duplicate is removed. Missing-as-zero keys
  are listed in the check detail (in this run: only HUBC
  `short_term_investments` 2025, a genuine printed dash).
- M2 (fixed): the loader no longer fabricates an HTTP 200
  download event; the download row records http_status NULL
  with a truthful local-file note.
- M3 (fixed): the unknown-company abort path now calls
  `session.rollback()` explicitly; the CLI documents that
  data-source/document rows commit even when a statement is
  gate-skipped (they describe a real sampled document).
- M4 (fixed): regression tests added for the real NML layout,
  the bare note-ref case, the parse-failure token, and
  subtotal missing semantics (suite now 18 Phase 7 tests).
- L1 (noted): balance-sheet `period_start` carries the fiscal
  period start (e.g. NML SFP 2024-07-01→2025-03-31), not a
  point-in-time date. Consistent across all maps; adopted as
  the Phase 3 convention for this phase. Phase 8 may revisit
  whether SFPs should instead carry period_start == period_end.
- L2 (process): the commit must use explicit `git add` paths
  for Phase 7 only, never `git add -A` (unrelated untracked
  files from earlier phases exist in the tree).
- L3 (fixed): OGDC units confirmed as Rupees '000 from the
  page footers; NML review wording resolved as non-existent
  (see publication dates above).
- L4 (fixed by C1): `eps_total` is no longer mislabeled as
  bare in the page map.

Re-verification after fixes: full backend suite green (see
below); all six maps extract with zero flagged rows under BOTH
PyMuPDF and pdftotext, with zero cross-extractor mismatches;
the two corrected rows (HUBC eps_total, NML share_capital)
match the printed faces.


## Focused re-audit (PASS) — 2026-11-04

A second depth-2 independent audit re-verified every fix item
(C1, C2, H1, H2, H3, M1–M4, L1–L4) plus full regression and
returned PASS with no CRITICAL or HIGH finding. Re-run
evidence: full backend suite 132 passed (114 + 18 Phase 7);
ruff check and format clean; CLI dry-run documents 3,
statements 16, line_items 316, skipped_existing 0,
skipped_validation 0, zero flagged rows, zero
page_match_mismatches, all column checks passing; financial
tables still 0/0/0 after the dry-run (rollback proven);
independent PDF spot-checks all match (HUBC totals, NML
totals and nine-month LOSS, OGDC grand total / six-month PAT
/ EPS); forbidden-content scan clean; fail-fast verified live
for a missing pdftotext (exit 2, clean JSON, no traceback).
Three LOW wording items (stale "OCR" in two code comments,
summary-level spec report wording, "fallback machinery"
phrasing) were polished after the audit without changing any
values or behavior; Phase 7 tests and ruff were re-run after
the polish.
