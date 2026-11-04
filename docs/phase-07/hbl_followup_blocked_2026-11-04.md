# Phase 7 follow-up — HBL CY2025: BLOCKED at download (2026-11-04)

Branch: `phase-07-hbl-followup` (from `59834f1`). Verdict: **BLOCKED**.
No extraction, no page maps, no database writes, no test changes in
this run. Nothing is claimed as done that is not evidenced below.

## Step 1 — HBL resolved in the registry (done)

- Company id 277, legal name "Habib Bank Limited", security id 277,
  ticker `HBL`, in the 470-company Main Board / Normal Counter
  registry. No registry row was created or edited.

## Step 2 — PDF download (BLOCKED, three curl attempts from the VM)

Target (issuer URL only, per brief):
`https://www.hbl.com/assets/documents/HBL_Annual_Report_2025.pdf`
Expected local path (gitignored, never committed):
`storage/financial_reports/HBL_Annual_Report_2025.pdf`

Evidence the link exists (no PDF fetched):

- The HBL Financial Reports page
  (`https://www.hbl.com/investor-relations/investor-relations/financial-reports`)
  loads over curl: HTTP 200, 339,319 bytes, and contains the string
  `HBL_Annual_Report_2025.pdf`. The parent-verified provenance
  (Annual Accounts, heading "2025", link text "HBL Annual Report
  2025") is consistent with that page. No separate publication date
  was shown beside the link; page footer "Last Updated: 04 Nov,
  2026". Terms note on the page: "© 2026 HBL All Rights Reserved",
  no separate download-terms statement shown.

Download attempts (all against the issuer URL only; no other host,
no mirror, no DPS, no challenge bypass, no cookie forging):

1. `curl -sSL` following redirects: **failed, exit 47, "Maximum
   (50) redirects followed"**. The server answers HTTP 302 with
   `Location:` pointing at the SAME URL, body `<HTML>...<TITLE>
   Loading</TITLE>...`, and sets Imperva-style session cookies
   (`visid_incap_*`, `incap_ses_*`) — a bot-management challenge
   page, not the PDF.
2. Page-visit session cookies + browser user-agent + referer
   (financial-reports page): the request **stalled for ~10 minutes**
   with no HTTP response and no file written.
3. Bounded retry (`--max-time 60`, same cookies/headers):
   **code 000, 0 bytes, 60 s timeout** — no HTTP response at all.

Conclusion: from this VM, non-browser HTTP cannot fetch this PDF
asset. The gate is on the PDF asset itself (the HTML page loads
fine). This is NOT a terms refusal: the issuer page carries no
download prohibition, and the source-matrix verdict for issuer IR
pages (ALLOWED, sampled only, internal analysis only, no
republication) still covers this download once it is obtainable.

## What was NOT done (explicitly)

- No PDF downloaded, stored, hashed, or committed.
- No HBL page maps, no SFP / P&L / cash-flow / changes-in-equity
  extraction, no auditor-opinion record (presence or absence not
  established — the report contents are unknown).
- No database writes: live counts verified unchanged after the
  attempts — documents 3, statements 88, line items 1,316,
  opinion rows 3, all UNVERIFIED.
- No LUCK work: the DPS-hosted Lucky Cement FY2026 PDF
  (`https://dps.psx.com.pk/download/document/282262.pdf`) was NOT
  touched, per the brief (DPS filing-download terms not
  established).
- No PSX market-data collection, no email to PSX, no VERIFIED
  promotion, no Docker, no merge to main, no branch tip moved.

## Exact unblocker (parent browser task, not a bypass)

A normal live-browser visit, as any visitor would make: open the
HBL Financial Reports page above, follow the "HBL Annual Report
2025" link under Annual Accounts / 2025, let the browser complete
the site's own challenge page, and save the resulting PDF as
`storage/financial_reports/HBL_Annual_Report_2025.pdf` in the repo
working tree. Then a follow-up coordinator resumes this brief from
step 3 (SHA-256, source-matrix entry, four-face page maps, opinion
record, independent audit, dry-run, commit, idempotency check,
push). Do NOT substitute a mirror, a search-cache copy, or a DPS
copy, and do NOT forge or replay challenge cookies.

## Remaining blockers (unchanged)

1. **HBL PDF download** — unblocker above. Without it, HBL cannot
   be added to the Phase 7 sample.
2. **KSE-100 expansion** — still the Phase 7 COMPLETE blocker even
   after HBL: needs per-company verified source access under the
   same sampled-only discipline (issuer IR page or regulatory
   filing link verified per company; no DPS filing downloads and
   no PSX financials portal downloads without separately
   established download terms).
3. **DPS filing-download terms** — not separately established; DPS
   remains discovery-only for filings.
4. **CI-in-CI** — unchanged (needs a main/development push or PR;
   separate approval; not done).
