# Phase 3 — Financial Statements Schema

## Tables

financial_statements, financial_statement_line_items,
financial_documents, financial_document_versions,
financial_document_downloads.

## Accounting context (mandatory per row, Phase 7 spec carried in)

company_id, document_id, period_start, period_end,
publication_date, financial_year, fiscal_quarter,
reporting_frequency (annual/quarterly/half_yearly/nine_month),
audited_status (audited/reviewed/unaudited),
consolidated_status (consolidated/unconsolidated), currency,
unit_scale, accounting_standard, page_number (line items),
extraction_method, extraction_confidence, quality_status.

## Rules that matter for Phase 7/8 (the consumers)

1. **Cumulative vs standalone quarters.** A six-month cumulative
   figure is NOT second-quarter revenue. Standalone quarters
   derived by subtracting cumulative periods are stored separately,
   marked is_derived, with the derivation formula and input
   periods recorded. Original cumulative values are never replaced
   by derived ones.
2. **Original labels preserved.** Every line item keeps
   original_label + original_displayed_value alongside the
   canonical key and the normalized value. A company-specific item
   is never forced into an incorrect standardized category; unknown
   items stay preserved and pending mapping.
3. **Blank/dash is not zero.** A blank, dash or nil amount is
   stored as NULL unless the document explicitly supports zero.
4. **Units are data.** Rupees vs thousands vs millions vs
   billions, and foreign currencies, are stored per row with the
   normalization rule. Never assume all companies report in PKR
   at the same scale.
5. **Restatements are versions.** A revised statement is a new
   financial_statements row (version_number + supersedes_id) and
   new line-item rows. The old version stays queryable for
   point-in-time analysis.
6. **Documents are files, not blobs.** The database row stores
   reference + SHA-256 + MIME + page count; the PDF lives on disk
   under raw/pdf or financial_reports. Download attempts (success,
   failure, retry, HTTP status) are logged in
   financial_document_downloads; a failed extraction never erases
   the downloaded document.
7. **OCR is not verification.** Extraction confidence is stored
   per line item; OCR output is never treated as verified
   financial information without a validation pass (balance-sheet
   identity, cash-flow identity — see validation helpers).
