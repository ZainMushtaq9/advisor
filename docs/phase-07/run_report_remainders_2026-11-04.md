# Phase 7 remainders — run report (2026-11-04)

Branch: `phase-07-remainders` (from `366ed32`). Migration `20261104_0006`
applied to the live DB before the commit run. Verdict: **PARTIALLY
COMPLETE** — cash-flow faces, changes-in-equity faces, and the
structured auditor-opinion module are all complete and verified;
KSE-100 expansion alone blocks COMPLETE (see blockers).

## What was closed

1. **Cash-flow + changes-in-equity faces for the same 3 PDFs.**
   New page maps: `hubc_cf.json` (p.278), `hubc_ce.json` (p.279),
   `nml_cf.json` (p.40), `nml_ce.json` (p.39, matrix), `ogdc_cf.json`
   (p.11), `ogdc_ce.json` (p.10, matrix). Consolidated faces only;
   HUBC unconsolidated faces (pp.224–225) and NML unconsolidated
   faces (pp.15–16) are out of scope, matching run 1.
2. **Structured auditor-opinion module.** New table `auditor_opinions`
   (migration 0006) + `opinions.py` loader + `auditor_opinions.json`
   (3 records). HUBC: unmodified opinion, A. F. Ferguson & Co.,
   partner Osama Kapadia, dated 2026-09-21, UDIN
   AR202610080onH3rpTV1, verbatim opinion sentence, going-concern
   material uncertainty false with the standard conditional
   language noted. NML and OGDC: explicit absence records (type
   `none`) — no opinion, firm, or UDIN invented.
3. **KSE-100 expansion: assessed, NOT bulk-expanded** (see blockers).

## Dry-run evidence (all 12 maps, before commit)

- Zero flagged rows on all 12 maps; zero page-match mismatches.
- All 5 matrix blocks gate True (roll-forwards + balance checks).
- All standard subtotals pass EXCEPT one known source difference:
  OGDC cash-flow `net_change` 2025 column, printed 12,517,648 vs
  components 12,517,649 — a 1 (thousand) rounding difference in the
  source as printed, recorded in the CLI, never adjusted. Subtotal
  failures are reported checks only, never load gates.
- Missing-as-zero keys are genuine printed dashes (each movement
  touches only a few components; share capital is untouched by every
  movement). Closing-dash-as-zero cases: NML overhauling reserve
  (blocks 1–2, nil until block 3 creates 1,732,541), NML maintenance
  reserve (block 3, extinguished to zero), OGDC associate
  capital-redemption reserve (both blocks, extinguished to zero in
  block 1 and nil thereafter).
- Expected commit write: statements +72 (8 standard + 64 matrix),
  line items +1000 (336 standard + 664 matrix), opinion rows +3,
  documents +0 (same 3 PDFs). Run-1 statements all skipped_existing
  (16); skipped_validation 0.

## Fixes found by the dry-run (all in this branch)

- **Extractor, hyphen-paren labels:** a label ending `2023- (Audited)`
  normalises to one word `2023-(audited)`, so the last-word token
  search never matched and the remainder fell back to the full line,
  leaking the year in as a value and shifting the whole balance row.
  Fix: the last word now comes from the raw label.
- **Extractor, joined labels:** pdftotext -layout glues dash columns
  onto the second line's last word (`interest---(954,006)`), so the
  two-line join acceptance failed for every NML dividend/transfer
  row. Fix: the boundary-word check splits tokens on
  non-alphanumerics.
- **Matrix roll-forwards:** subtotal rows (total comprehensive
  income, total distributions) were summed as movements,
  double-counting (OGDC block 1 overstated unappropriated profit by
  exactly profit + distributions). Fix: specs marked
  `"subtotal": true` are excluded from movement keys.
- **Matrix roll-forwards, dash closings:** a printed dash in a
  closing row means nil; the check now substitutes 0 and records
  `closing_dash_as_zero: True` in the detail.

## Column discipline (unchanged from run 1)

Cumulative interim figures are never conflated with standalone
quarters: NML nine-month and quarter columns remain separate
statement rows, OGDC six-month and quarter likewise, no derived
standalone quarter invented. Changes-in-equity movements are stored
as one statement per equity component per movement block, with the
component in the new nullable `financial_statements.statement_scope`
column (NULL for ordinary faces). Every new row is UNVERIFIED.
Restatements would be new versions, never overwrites; none occur in
this run. No OCR was used for any new row (all embedded text).

## Tests

Backend suite: 140 passed (run-1 baseline 132 + 8 new: multi-segment
note refs, hyphen-paren label, dash-glued joined label, cursor
continuation across repeated labels, tall value stacks, two
cross-component checks, opinion-record validation). Ruff check and
format clean on the remainders tree (migration 0006 matches the
existing migration style; the current ruff version flags the same
style findings on migration 0005, so parity — not zero findings on
migrations — is the bar there).

## Blockers (exact unblockers)

1. **KSE-100 expansion** — blocked pending per-company verified
   source access under the same sampled-only discipline (issuer IR
   page or regulatory filing link verified per company; no DPS
   filing downloads and no PSX financials portal downloads without
   separately established download terms). The LUCK Annual Report
   FY2026 and HBL CY2025 PDF links, if they arrive via the parent
   browser task, belong to a follow-up extraction pass, not this run.
2. **DPS filing-download terms** — not separately established; DPS
   remains discovery-only for filings. Unblocker: written Terms
   evidence covering DPS filings (the open PSX market-data Terms
   question does not cover this).
3. **CI-in-CI** — unchanged from run 1 (needs a main/development
   push or PR; separate approval; not done).
