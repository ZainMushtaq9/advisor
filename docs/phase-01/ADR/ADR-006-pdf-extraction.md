# ADR-006 — PDF extraction: PyMuPDF (primary) + pypdf (fallback only) + Tesseract (scanned only)

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04
- **Supersedes:** The first draft's "pypdf not installed" position — the fixed
  stack lists PyMuPDF and pypdf, so pypdf is retained in a fallback-only role.

## Context

PSX announcements and listed-company reports arrive as PDFs of two kinds:
those with a real text layer, and scanned/image PDFs with none. Extraction
must be traceable (a number must be traceable to its source PDF and page) and
must never let an LLM become the extractor of record for a financial number
(ADR-010).

## Decision

- **Stage 1 — text layer:** PyMuPDF is the primary extractor for every PDF
  with a usable text layer.
- **Stage 2 — fallback:** pypdf runs **only** when PyMuPDF fails on a
  document. The failure, the fallback, and the method used are logged with the
  extracted text. pypdf is never run in parallel with PyMuPDF on the same page
  in the same run — one method of record per page.
- **Stage 3 — scanned pages:** Tesseract OCR runs **only** on pages with no
  usable text layer. OCR is a different role from text extraction, not a
  duplicate extractor.
- **Provenance (mandatory):** extracted text always keeps its source PDF,
  page number, and extraction method, so any number can be traced back to its
  page. Raw PDFs are stored separately from processed records (scaffold rule).

## Consequences

- Positive: one primary path, one defined fallback, one OCR path — no
  ambiguity about which extraction produced a given text; Celery jobs make
  slow OCR non-blocking.
- Negative: three tools to pin; Tesseract needs a binary + language data that
  are not verified present on this machine (UNVERIFIED — setup check).
- Constraint: table extraction (pdfplumber/Camelot/Tabula) is a later,
  per-document problem, not the general extraction job; no such tool is a
  Phase 1 primary.

## Alternatives considered

- pypdf as primary — rejected: PyMuPDF is the fixed-stack primary; pypdf's
  value here is as a fallback, not a parallel primary.
- pdfplumber / Camelot / Tabula as primaries — rejected for Phase 1 (above).
- A paid PDF API — **excluded**: paid, violates PKR 0.
- An LLM "reading the PDF" as extractor of record — **prohibited** (ADR-010).

## Verification / open checks

- [ ] At Phase 2 setup: pin PyMuPDF/pypdf; read their LICENSE files
  (UNVERIFIED in Phase 1 — PyMuPDF's terms in particular must be read, not
  assumed); confirm the Tesseract binary + language data are installed, or
  record OCR as unavailable until they are.
