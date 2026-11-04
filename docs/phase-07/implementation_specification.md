# Phase 7 — Implementation Specification (sample run, 2026-11-04)

## Design: reuse, do not duplicate

Phase 3 already built the schema (`financial_documents`,
`financial_document_downloads`, `financial_document_versions`,
`financial_statements`, `financial_statement_line_items`) and the ORM
(`backend/app/models/financial.py`). This phase adds NO new tables.
It adds a pipeline package and a CLI loader that write into those
tables, plus docs. The Phase 6 indicator runner pattern
(deterministic Python, `--dry-run` default / `--commit`, JSON report,
idempotent writes) is reused.

## Pipeline: `backend/app/services/financial_statements/`

| Module | Job |
|---|---|
| `numbers.py` | Pure parsing. Commas stripped; `(1,234)` → negative; `-`, `--`, `nil`, blank → NULL (never zero); `Rs. '000s` / `Rupees in thousand` → reported_unit `thousands`, normalized_value = numeric × 1000 in PKR. No LLM arithmetic. |
| `extract.py` | Page-map driven text extraction. The method is FIXED per page map (no runtime fallback): `embedded_text` (PyMuPDF lines, sequential face parser; OGDC SFP uses interleaved document order) or `ocr_single_panel` / `ocr_two_panel` (Tesseract `--psm 6`, 200 DPI render; retained and tested code for image-only pages, unused by the current sample (it is not a runtime fallback: the method is fixed per page map)). Page maps are declarative JSON in `docs/phase-07/page_maps/` (statement → PDF pages, columns, units). |
| `validate.py` | Pure checks. Balance-sheet identity: total_assets == total_equity + total_liabilities (+ non-controlling interest is INSIDE total equity where the statement presents it that way — see mapping register). Subtotal checks where the face prints them. Any failure → statement SKIPPED (not loaded; counted as skipped_validation) with the failure recorded (never silently adjusted, never loaded despite the failure). The CLI gate is authoritative; data-source/document rows for a gated-out document are still committed because they describe a real sampled document (see the CLI's NOTE comment). |
| `load.py` | Idempotent loader. Creates `data_sources` rows (one per source), `financial_documents` rows (hash-deduped per the Phase 3 unique index), download rows, statement rows (version 1, is_current) and line-item rows. Re-run with the same document hash writes nothing new. `--dry-run` rolls back. |

## Page maps (this run)

| Company | Statement | PDF pages | Columns | Units |
|---|---|---|---|---|
| HUBC | Consolidated SFP, as at 30 Jun 2026 + 30 Jun 2025 | p.277 | 2026, 2025 | Rs. '000s |
| HUBC | Consolidated P&L, year ended 30 Jun 2026 + 2025 | p.275 | 2026, 2025 | Rs. '000s |
| NML | Consolidated condensed interim SFP, 31 Mar 2025 + 30 Jun 2024 | pp.35–36 | 31 Mar 2025 (un-audited), 30 Jun 2024 (audited) | Rupees in thousand |
| NML | Consolidated condensed interim P&L, nine months + quarter ended 31 Mar 2025/2024 | p.37 | nine months 2025/2024, quarter 2025/2024 | Rupees in thousand |
| OGDC | Condensed interim consolidated SFP, 31 Dec 2025 + 30 Jun 2025 | Embedded-text p.7 (interleaved panel order) + pdftotext two-panel match | 31 Dec 2025 (unaudited), 30 Jun 2025 (audited) | Rupees '000 (confirmed from the p.7 footer) |
| OGDC | Condensed interim consolidated P&L, six months + quarter ended 31 Dec 2025/2024 | Embedded-text p.8 + pdftotext match | six months 2025/2024, quarter 2025/2024 | Rupees '000 (confirmed from the p.8 footer) |

Column discipline: a column is stored under its OWN period
(period_start/period_end), never merged into another period. NML and
OGDC interim reports print BOTH cumulative and quarter columns; both
are stored as-reported, as separate statement rows with different
`reporting_frequency` (nine_month / half_yearly vs quarterly). NO
derived standalone quarter is computed in this run (nothing to derive:
the quarter columns are printed).

## Auditor opinions (exact traceability only)

| Company | Opinion | Firm / date / pages | Going concern |
|---|---|---|---|
| HUBC (consolidated) | Unmodified — "true and fair view … in accordance with the accounting and reporting standards as applicable in Pakistan" | A. F. Ferguson & Co., Chartered Accountants; UDIN AR202610080onH3rpTV1; opinion PDF p.271, signature PDF p.274 | Standard responsibility language only (PDF p.273); NO material uncertainty reported |
| NML (interim) | NO review report is included in the document (verified by full-text scan of all 72 pages); faces are marked Un-audited; auditors Riaz Ahmad & Company are named on p.3 as company auditors | None — no review wording exists to record | Statements recorded as unaudited |
| OGDC (interim) | Unaudited condensed interim statements (no audit opinion; review status to be recorded from the filing) | Transmission CS-04-08, 23 Feb 2026 | As stated in the filing, if anything |

No opinion wording is paraphrased into a stronger claim. If a page
cannot be read, the opinion field stays NULL with a note, never
guessed.

## Quality rules for loaded rows

- Every line item: `quality_status = UNVERIFIED` (single source;
  H1 discipline). No VERIFIED promotion in this phase.
- `extraction_confidence`: 1.0 for embedded-text rows that pass the
  independent page-match (second-method re-read: pdftotext for all
  four embedded maps; OGDC SFP uses the joint two-panel parser on
  the pdftotext layout lines, so the two methods genuinely differ);
  0.85 for OCR rows that pass the visual page-match (no current
  sample map uses OCR); NULL where a figure could not be matched
  (row still loaded, flagged in the run report).
- `extraction_method`: `pymupdf_embedded_text` or
  `ocr_tesseract_5_200dpi`.
- Dash/blank → `numeric_value = NULL`, `original_displayed_value`
  preserved (`-`).
- Restatements: a revised filing would be a NEW statement version
  (version_number + 1, supersedes_id set). None in this run.

## CLI

`scripts/run_financial_extraction.py --dry-run` (default) /
`--commit`, JSON report to stdout: `written` (documents, statements,
line items, skipped_existing, skipped_validation) plus per-map
entries with `flagged_rows`, per-column `columns[].checks`
(balance identity and subtotals), and `page_match_mismatches`
(key:col pairs where the pdftotext re-read disagrees; mismatched
rows load at confidence NULL). Exit 2 on bad args;
any unknown company/period aborts before any write (same fail-fast
discipline as the market ingestion CLI).

---

## Addendum — remainders 2026-11-04 (matrix path, opinion module, 0006)

Matrix extraction (`extract_matrix` in the CLI): the primary method
comes from the map (`layout_text` = pdftotext -layout, `embedded_text`
= PyMuPDF); the second read is always the other method, with the same
`drop_lines_matching` furniture drops. Blocks resolve via the
advancing cursor from `extract_face_from` (new in this branch:
`extract_face` is now a wrapper over `extract_face_from(..., start,
scan_cap=12)`; matrix blocks pass `scan_cap=40` because one row's
values may occupy 16 separate lines in content-stream order). The
page-match dict is keyed (block_idx, key, comp_idx); mismatched
cells load at confidence NULL.

Matrix validation (`validate_matrix` in the CLI): per block,
per-component roll-forward via `check_subtotal` (synthetic opening
row for previous-close blocks), balance checks via the new
`check_cross_component` (validate.py), flagged rows, and page-match
mismatches. A block gates OUT when any check fails OR any row is
flagged — a flagged row means the extraction itself failed, and
missing-as-zero must never hide it. A printed dash in a closing row
means nil: the check substitutes 0 and records
`closing_dash_as_zero: True`.

Extractor fixes in this branch (numbers.py, extract.py): the
last-word remainder search uses the raw label's last word (a label
ending `2023- (Audited)` normalises to one word and otherwise leaks
the year in as a value); the two-line join acceptance splits tokens
on non-alphanumerics (dash columns glue onto the second line's last
word); `is_note_ref` accepts multi-segment references (`16.1.1`)
while each segment must be exactly one digit, so EPS `38.26` and
rates `5.00`/`8.50` never match.

Opinion module (`opinions.py`): `validate_opinion_record` is pure
(present opinions require firm + date + text and must not carry an
absence note; absence records must not carry firm/partner/UDIN/text
and require an absence note); `load_opinion` is idempotent (existing
→ return without update; new → UNVERIFIED row, version 1,
is_current). Unknown JSON fields are ignored.

Migration `20261104_0006` (down_revision `20261104_0005`): adds
nullable `financial_statements.statement_scope` and recreates the
grain unique constraint and partial current index with the scope
column (Postgres treats NULLs as distinct, so existing rows are
unaffected); creates `auditor_opinions` with the shared
quality_status CHECK vocabulary, grain UQ, company index, partial
current index, and the versioned trigger reusing
`psx_allow_only_current_flag()` from migration 0003 (so the table
is VERSIONED like financial_statements/line_items, not immutable).
The CLI loads opinions in the same transaction as the maps (a
partial --maps run skips companies lacking a document, reported as
`skipped_no_document`); the opinions JSON is validated upfront as
fail-fast before any DB work.
