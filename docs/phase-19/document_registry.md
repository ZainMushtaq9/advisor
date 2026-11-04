# Phase 19 — Document Registry

## Indexed documents (3)

All three are issuer-hosted reports already held for internal analysis
under the Phase 7 source matrix. DPS-hosted filings are NOT seeded
(discovery only; filing-download terms not established). No document
body is served by any route; snippets are capped at 500 chars.

| Ticker | Company id | Document | Pages | Publication date | Date kind | Access level |
|---|---|---|---|---|---|---|
| HUBC | 289 | HUBCO Integrated Annual Report 2026 (financial_document_id 13) | 423 | 2026-09-21 | proxy — auditor-report date, labelled as proxy, never presented as verified | issuer_internal |
| NML | 394 | Nishat Mills 3rd Quarter Report 2025 (financial_document_id 14) | 72 | None | unknown — Phase 7 record carries publication date NULL, never guessed | issuer_internal |
| OGDC | 403 | OGDC Condensed Interim Consolidated Statements, six months ended 31 Dec 2025 (financial_document_id 15) | 12 | 2026-02-23 | proxy — RNS date recorded by the Phase 11 seed event, used as publication proxy | issuer_internal |

## Index counts (live DB, after final re-index)

| Document | Pages with text | Chunks | Empty pages (gap) |
|---|---|---|---|
| HUBC | 413 | — | 10 |
| NML | 71 | — | 1 |
| OGDC | 7 | — | 5 |
| **Total** | **491** | **943** | **16** |

Empty pages are mostly cover / blank / graphic pages with no
extractable text. They yield zero chunks and are recorded as gaps,
never filled with invented text. No OCR rows are created (all three
reports carry full embedded text).

## Section labels (face pages)

| Ticker | Page | Section |
|---|---|---|
| HUBC | 271 | auditor_opinion |
| HUBC | 275 | profit_and_loss |
| HUBC | 277 | statement_of_financial_position |
| HUBC | 278 | cash_flow |
| HUBC | 279 | changes_in_equity |
| NML | 35–36 | statement_of_financial_position |
| NML | 37 | profit_and_loss |
| OGDC | 7 | statement_of_financial_position |
| OGDC | 8 | profit_and_loss |

All other pages label `body`.

## Stale-source handling

- As-of date filters (`as_of`) exclude any document whose
  publication date is unknown (NML is excluded by any as-of filter
  requiring a known date) and any document published after the
  as-of date. No look-ahead: a statement published after the
  analysis date is never cited for that date.
- No vintage is overwritten. A revised report would be a NEW
  `rag_documents` row with `supersedes_id` pointing at the old row.
  None exists yet.
- All indexed documents carry status UNVERIFIED (inherited from
  Phase 7). Indexing does not promote status.

## Not indexed

- HBL CY2025 annual report — PDF download pending (parent-owned
  live-browser task; issuer-site bot-management challenge on the VM).
  The `hbl_missing_document` benchmark case proves the assistant
  answers missing_data with zero citations rather than inventing.
- Any DPS-hosted filing, PSX financials-portal document, news article
  body (Phase 11 discipline: no body column, summaries ≤ 280 chars),
  or proprietary corpus. Nothing unlicensed is redistributed.
