# Phase 7 — HBL Run Report (2026-11-05)

Follow-up extraction adding Habib Bank Limited (HBL) to the Phase 7
sample. Branch: `phase-07-hbl-extraction`, from `phase-26-evaluation`
tip `b6f007cefc3e0d8fc0def986823293c703805070`. No register file was
edited here (the parent consolidates registers).

## Source

| Item | Value |
|---|---|
| Document | HBL Annual Report 2025 |
| Retrieved | 2026-11-05, normal browser visit to the issuer's Financial Reports page (no account, sign-in, payment, mirror, cache, or DPS copy; no bot challenge in the browser visit) |
| Link followed | https://www.hbl.com/investor-relations/investor-relations/financial-reports → "Annual Accounts" / "2025" → "HBL Annual Report 2025" → https://www.hbl.com/assets/documents/HBL_Annual_Report_2025.pdf |
| File | `storage/financial_reports/HBL_Annual_Report_2025.pdf` (gitignored, never committed) |
| SHA-256 | `6cde814285561cfb28596ead2ae5d4dc897ec71c77b4e5271bae626474d75ccd` |
| Pages | 411, embedded text |
| Terms verdict | Issuer IR ALLOWED, sampled only, internal analysis only, no republication (see `source_matrix.md` addendum) |

## Scope as found in the document (not assumed)

| Item | Value |
|---|---|
| Company | Habib Bank Limited, ticker HBL, sector COMMERCIAL BANKS |
| Scope | Consolidated faces only (the unconsolidated opinion and faces in the same report are NOT recorded, matching the HUBC precedent) |
| Period | Year ended 31 December 2025, with 2024 comparative column (annual, both columns) |
| Audit status | Audited |
| Publication date | 2026-03-03 — the consolidated auditor report date (PDF p.74, printed p.72) |
| Auditor | KPMG Taseer Hadi & Co., Chartered Accountants, Karachi; engagement partner Amyn Pirani |
| Opinion | Unmodified, dated 03 March 2026; UDIN `AR202510201HsNS5gUWD`; opinion text on PDF p.70 (printed p.68), signature p.74 (printed p.72) |
| Going concern | No material uncertainty conclusion stated; standard conditional responsibility language only (`going_concern_material_uncertainty=false`) |
| Faces extracted | SFP PDF p.75 (printed 73); P&L p.76 (printed 74); CE p.78 (printed 76); CF p.79 (printed 77) |
| Not a separate face | Statement of comprehensive income, PDF p.77 (printed 75) — outside the Phase 7 four-face scope |
| Units | PKR thousands (Rs '000); SFP/P&L/CF also carry USD ('000) columns. EPS is Rupees per share, NOT thousands |

Banking rule applied: HBL's banking faces were extracted as presented
(including bank-specific lines). No ratios or valuations were computed
here — those belong to the later Phase 8/9 re-runs, where Phase 9 must
use the bank residual-income model for HBL, not the industrial models.

## Counts (before → after)

| Table | Before | After | HBL added |
|---|---|---|---|
| financial_documents | 3 | 4 | 1 |
| financial_statements | 88 | 118 | 30 |
| financial_statement_line_items | 1,316 | 2,116 | 800 |
| auditor_opinions | 3 | 4 | 1 |

All HBL rows are UNVERIFIED (single source, rule H1; terms gate not
cleared, so no promotion in this run).

### HBL breakdown

| Face | Statements | Line items |
|---|---|---|
| Statement of financial position (27 specs × 2 columns) | 2 | 54 |
| Profit and loss (25 × 2) | 2 | 50 |
| Cash flow (54 × 2) | 2 | 108 |
| Changes in equity, block 2024 (25 rows × 12 components) | 12 | 300 |
| Changes in equity, block 2025 (24 rows × 12 components) | 12 | 288 |
| **Total** | **30** | **800** |

```
Statements by company after this run (total 118):
HBL  ▓▓▓▓▓▓▓▓▓▓ 30   (new)
HUBC ▓▓▓ 8            (unchanged)
NML  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 56 (unchanged)
OGDC ▓▓▓▓▓▓▓▓ 24      (unchanged)
```

## Audit: first FAIL → fix → PASS (the Phase 7 pattern)

First dry run: SFP and P&L clean, but two rows failed:

1. `hbl_cf.translation_effect_investing` — label_not_found.
2. `hbl_ce.oci_equity_investments_2024` — incomplete_values, which
   also broke the 2024 block's NCI and total rollforwards.

Root causes (both verified in the source, neither a validation
weakening):

- **CF translation label split with interleaved values.** In
  content-stream order the label prints as two halves with the USD
  value pair between them ("Effect of translation … subsidiaries"
  / 17,119 / (9,818) / "and associates - net of tax" / PKR values).
  The two-consecutive-line join cannot match this. Fix: a new
  `label_parts` map option — each half matched in order, values
  collected after the last half. The full label stays in the map.
- **CE 2024 equity row: blank NCI cell.** All three extractors return
  only 11 tokens for this 12-column row. Word x-positions prove the
  NCI column (~x478–498) is empty — no dash printed — while the
  last 3,278,951 sits at x511.6, aligned with the Total column
  (header x513.5). Fix: a new `blank_columns` map option
  (`[10]` = NCI) that records None for the blank cell exactly as a
  printed dash records None. It applies only on an exact token fit
  (tokens == n_cols − blanks); otherwise the row still gates out.
  The block's rollforward/balance gates then verify the declared
  position — and they pass.

Also from earlier in this run: dual-currency faces print USD ('000)
columns before PKR ('000) in content-stream order, so bare rows use
`skip_values: 2` to collect PKR (labeled rows anchor on the label).

Final dry run: **zero flagged rows, zero page-match mismatches on all
four maps, both CE blocks gate_ok, all rollforwards and balance
checks pass, all subtotal checks pass** (SFP balance identity exact
both years; P&L addition links; CF signed sums).

### Independent cross-read

- pdfplumber confirms exactly: P&L PAT 66,763,916 / 57,804,659;
  equity holders 66,716,190 / 58,457,771; EPS 45.48 / 39.85; CF end
  cash 618,728,825 / 511,519,528; CE 2025 closing balances
  (attributable 486,943,716; NCI 1,670,989; total 488,614,705).
- SFP confirmed by component-sum recomputation from the extracted
  rows: assets 7,708,144,220 / 6,055,112,877; liabilities
  7,219,529,515 / 5,644,314,783; equity 488,614,705 / 410,798,094;
  identity holds exactly both years. (pdfplumber garbles SFP p.75's
  overlapping text layer — split digits, duplicated glyphs — so it
  cannot serve as the SFP cross-reader; that is a pdfplumber
  limitation on this page, not an extraction disagreement: the
  script's two methods agree with zero mismatches.)

### Tests

`backend/tests/test_financial_statements_phase07.py`: **30 passed**
(27 pre-existing + 3 new: `blank_columns` exact fit,
`blank_columns` wrong-count stays incomplete, `label_parts`
value-interleaved split label).

## Idempotency proof

- First `--commit`: documents 1, statements 30, line items 800,
  opinion 1 created.
- Second `--commit`: documents 0, statements 0, line items 0,
  `skipped_existing` 30, opinion `created: false`.
- Final DB totals are exactly the pre-existing counts plus the HBL
  amounts; HUBC 8 / NML 56 / OGDC 24 statements unchanged.

## Source defects recorded, never adjusted

1. **CF unlabeled movement row.** One row between the subordinated-debt
   mark-up row and the first operating subtotal has NO printed label
   in the source (verified visually in a 200 DPI render of PDF p.79
   and in the text spans). Values: PKR (7,528,688) / (3,749,239);
   USD (26,877) / (13,384). Arithmetic proves it is excluded from
   ALL subtotals on the page (the first subtotal equals profit +
   dividend + share + subordinated mark-up exactly, without it).
   Loaded as bare spec `cf_unlabeled_row` with original label
   "(label not printed in source)" and no invented label. Its
   `subtotal_position_inferred` flag means "position inferred", not
   "subtotal".
2. **CE 2024 equity row blank NCI cell** (see Audit above). Recorded
   via `blank_columns: [10]` in the map; value None, not zero.
3. **CF translation label split with interleaved USD values** (see
   Audit above). Recorded via `label_parts` in the map.
4. No printed-total-vs-components defect was found in HBL (unlike the
   OGDC 1-thousand case): every checked total matches its components
   exactly.

## Files changed on this branch

- `docs/phase-07/page_maps/hbl_sfp.json` (new)
- `docs/phase-07/page_maps/hbl_pl.json` (new)
- `docs/phase-07/page_maps/hbl_cf.json` (new)
- `docs/phase-07/page_maps/hbl_ce.json` (new)
- `docs/phase-07/auditor_opinions.json` (HBL record appended)
- `docs/phase-07/source_matrix.md` (HBL follow-up addendum)
- `docs/phase-07/run_report_hbl_2026-11-05.md` (this file)
- `scripts/run_financial_extraction.py` (SOURCE_KEYS / TERMS /
  IDENTITY / SUBTOTALS entries for HBL)
- `backend/app/services/financial_statements/extract.py`
  (`skip_values` for bare rows, `blank_columns`, `label_parts`)
- `backend/tests/test_financial_statements_phase07.py` (4 new tests)

NOT committed: the PDF (gitignored), any CSV, any credential.

## Remaining work (NOT done here)

- Phases 8+ re-runs adding HBL — separate work, sequenced by the
  parent. Phase 9 must use the bank residual-income model for HBL.
- The Phase 27/28 coordinator runs in parallel on the same live DB;
  this run touched only the four Phase 7 tables and modified no
  existing row.
