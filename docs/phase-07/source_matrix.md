# Phase 7 — Document Source Matrix (2026-11-04 run)

Sources are judged on TERMS FIRST. A source whose download terms are
unclear is recorded as such and is NOT used for downloads in this run,
even if its documents are publicly visible. No copyrighted report is
republished or redistributed. All PDFs live under
`storage/financial_reports/` (gitignored) with SHA-256 recorded here
and in `financial_documents.content_hash`. Internal analysis only.

## Verdicts

| Source | What it is | Terms found | Verdict |
|---|---|---|---|
| Issuer investor-relations pages (hubpower.com, nishatmillsltd.com) | Company-published stakeholder documents (annual / interim reports) | No download prohibition found on the publication pages. Documents are © the issuer and published for stakeholders/shareholders. | ALLOWED, sampled only, internal analysis only, no republication |
| Regulatory filing via RNS (rns-pdf.londonstockexchange.com) | Company-authored filing publicly transmitted to LSE/PSX (OGDC interim statements, transmission CS-04-08, 23 Feb 2026) | Public regulatory disclosure by design; no download prohibition. RNS is a news service, not the author — provenance records the COMPANY as author and RNS as carrier. | ALLOWED, sampled only, internal analysis only, no republication |
| DPS company pages (dps.psx.com.pk/company/…) | PSX-hosted announcement listings (used for DISCOVERY: which reports exist, transmission dates) | The DPS Terms of Use modal addresses the Market Data feed (systematic retrieval / redistribution of market data). It does not clearly cover company filings. Filing-download terms not separately established. | DISCOVERY ONLY in this run — no DPS PDF downloaded |
| PSX financials portal (financials.psx.com.pk) | PSX-hosted company reports | Report-download terms not separately established. | NOT USED in this run |
| SECP (LEAP / eServices) | Company search (Phase 4 route), not a report host in this run | N/A for reports. | N/A |
| News / research sites (mettisglobal, brecorder, craft, pitchbook, etc.) | Secondary summaries, NOT official documents | Not official, not used as statement sources. | EXCLUDED |

## Sample companies and document status

| Ticker | Sector | Document attempted | Source | Status |
|---|---|---|---|---|
| HUBC (id 759) | POWER GENERATION & DISTRIBUTION | Integrated Annual Report 2026, FY ended 30 Jun 2026, consolidated statements, audited | hubpower.com (issuer) | DOWNLOADED, 423 pp, embedded text |
| NML (id 864) | TEXTILE COMPOSITE | 3rd Quarter Report, nine months ended 31 Mar 2025, consolidated condensed interim statements, unaudited (CORRECTED: no review report is included in the document; faces are marked Un-audited; auditors Riaz Ahmad & Company are named on p.3 as company auditors, not as reviewers of these statements) | nishatmillsltd.com (issuer) | DOWNLOADED, 72 pp, embedded text |
| OGDC (id 873) | OIL & GAS EXPLORATION COMPANIES | Condensed interim consolidated statements, six months ended 31 Dec 2025, unaudited | RNS carrier, company-authored filing | DOWNLOADED, 12 pp, EMBEDDED TEXT (CORRECTED: the earlier image-only claim was wrong — PyMuPDF returns 2,917 chars on p.7 and 2,067 on p.8; extraction uses embedded text with a pdftotext second-method match; the OCR parser is retained and tested as fallback machinery only) |
| LUCK (CEMENT) | CEMENT | Annual Report FY ended 30 Jun 2026 (transmitted 4 Sep 2026 per DPS listing) | DPS listing (discovery only); issuer IR PDF not located via search | NOT DOWNLOADED — exact PDF link not established; needs a parent browser task on the DPS company page or the issuer IR page. Recorded as a gap, not filled from news summaries. |
| HBL (COMMERCIAL BANKS) | COMMERCIAL BANKS | Annual report (CY2025) | Not located via search (only news summaries) | NOT DOWNLOADED — recorded as a gap. Bank statement formats are Phase 8-relevant; the sample already covers 3 sectors without it. |

## Downloaded files (SHA-256, storage/financial_reports/)

| File | SHA-256 | Pages | Text |
|---|---|---|---|
| HUBC_Integrated_Annual_Report_2026.pdf | 0b73724fa8361e283ff1e19290e273ce7752718585079be8f9b534da9f2f81ac | 423 | Embedded (some image pages) |
| NML_3rd_Quarter_Report_2025.pdf | dc14d2036633004ab0bd0872aa0234d152d85aa172c59e88e9c5a389607fa4f0 | 72 | Embedded |
| OGDC_Interim_Dec2025.pdf | 7f03c772ed44d479c804cda4225014f0697ca6cf8430c0fabf62e8e3ede53ddb | 12 | Embedded text (PyMuPDF) + pdftotext match |

## PSX Market Data Terms — scope note

The written-permission question gating Phases 4–6 concerns systematic
retrieval/collection of PSX MARKET DATA into a database. It is NOT
assumed to cover or to clear company annual/interim reports, and
nothing in this phase relies on it: report downloads above are
sampled issuer/regulatory documents, stored outside Git, never
republished, and logged with provenance. If PSX later asserts that
its portal terms cover filings, DPS-sourced downloads (none in this
run) would be the first thing re-examined.
