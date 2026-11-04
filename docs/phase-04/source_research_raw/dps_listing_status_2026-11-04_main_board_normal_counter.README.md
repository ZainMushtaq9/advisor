# DPS Listing Status snapshot — Main Board / Normal Counter — 2026-11-04

## Snapshot file status: ROW DATA FILE PENDING — DO NOT CITE AS COMPLETE

The canonical snapshot CSV for this snapshot,
`dps_listing_status_2026-11-04_main_board_normal_counter.csv`,
**has not yet been written into this repository**, because the
row-level data from the parent's live-browser read did not reach
this coordinator's session as a file or as row text. The browser
read itself is reported (by the parent) to have returned 470 rows,
but no row table is present in any file accessible to this
coordinator, and the 24 browser screenshots on disk are viewport
images (25 rows shown per view, overlapping scroll positions),
not a row-level record. Transcribing a "snapshot" from those
screenshots would be a reconstruction, not the inherited browser
rows, and would risk misreading names, symbols, and sectors —
which this project forbids ("never fill by guessing"). **No rows
have been fabricated to fill this gap.** This README records the
provenance and the exact gap so the file can be written mechanically
the moment the row data is delivered.

## Provenance (as reported by the parent, to be confirmed against the CSV)

- Source URL: https://dps.psx.com.pk/listings
- View: MAIN BOARD / Normal Counter
- Page header date/time during the read: Nov 4, 2026 1:17 PM
  (Asia/Karachi, as displayed on the portal)
- Extraction method: live browser, page by page (parent session;
  generic subagents cannot operate a live browser)
- Reported row count: 470 data rows (pages 1–100, 101–200, 201–300,
  301–400, 401–470), each with symbol, name exactly as displayed,
  sector exactly as displayed, and Clearing Type (NC or blank)
- Page ranges reported: page 1: 786 through CSIL; page 2: CTM
  (Colony Textile Mills Limited) through HUBC; page 3: HUMNL
  through NETSOL; page 4: NEXT through SNBL; page 5: SNGP through
  ZUMA
- Earlier summarized report's CTM/CWHC entries and its blank-type
  exceptions list are SUPERSEDED by the page-by-page reads and must
  not be used; the blank-Clearing-Type list must be rebuilt from
  the page data itself (blank rows reported across the reads
  include CWHC, GCWLPRS, IDEAL, JSRR, NGLEL, NNAR, PINLR, SELECT,
  SLM, SOYASUP, SPAC2, SPSL, STLR, TISL, WAHDAT, plus BAPLR1 and
  CENIR from page 1 — to be confirmed against the CSV, not assumed)
- Names with apparent abbreviations or typos (e.g. "Ittehad
  Chemicals Limted", "Orient Rental Mod", "PIA Holding Company
  LimitedB") must be kept EXACTLY as displayed, never completed
  or corrected by guessing

## Scope limitation (applies to the CSV once written)

- Main Board / Normal Counter ONLY.
- GEM Board (5 entries) and Main Board Non-Compliant / Winding-Up
  (93 entries) were counted but NOT fully captured in this read.
- This snapshot is therefore NOT the full PSX registry and must
  never be cited as full-market completeness, KSE-100 completeness,
  or a VERIFIED registry (single source — see below).

## CSV contract (enforced by scripts/import_dps_snapshot.py)

Columns, in order: `row_no,symbol,name,sector,clearing_type`

- `row_no`: 1..470 continuous, in browser-read order.
- `symbol`: DPS symbol exactly as displayed; no duplicates within
  the file. Distinct symbols sharing a name (preference/rights
  variants) are distinct rows and must NOT be merged.
- `name`: exactly as displayed, including apparent typos.
- `sector`: exactly as displayed; no canonical mapping applied.
- `clearing_type`: `NC` or blank. Blank means blank — it is not
  mapped to a listing status or a verification status.
- No placeholder, `?`, or guessed values. Any row from the browser
  reports that is missing or unclear when the CSV is written must
  be listed explicitly as a gap in the import report, never filled
  by guessing.

## Verification rule (Phase 4 audit H1)

This snapshot is a SINGLE source (DPS). VERIFIED requires >=2
distinct agreeing sources including one official, so records
imported from this file alone MUST stay UNVERIFIED. The Phase 4
importer never sets VERIFIED, and verification.py cannot promote
from a lone source. Clearing Type is not a verification status.

## What is ready while the CSV is pending

- `scripts/import_dps_snapshot.py`: validates the CSV strictly
  (header, continuous row numbers, no duplicate symbols, no empty
  symbol/name/sector, clearing_type NC-or-blank), imports through
  the Phase 4 engine (idempotent, deterministic matching, no LLM
  as authority), runs `reconcile()` against the snapshot tickers,
  and prints database counts by status. Tested 2026-11-04 in
  --dry-run mode on a 3-row synthetic TEST ONLY CSV (rolled back):
  3 created, re-import skipped 3, reconcile coverage 1.0, all
  UNVERIFIED, VERIFIED = 0, live database still 0 afterwards.
  Validation was also tested: duplicate symbol, non-continuous
  row_no, and invalid clearing_type are all rejected before any
  database access.
- The moment the 470-row CSV is placed at the path above, the
  import is: `DATABASE_URL=<from database/.env> backend/.venv/bin/python
  scripts/import_dps_snapshot.py --csv <path> --dry-run` (verify),
  then the same with `--commit`, then a 20-row spot-check against
  the CSV (including one blank-Clearing-Type row and one
  rights/preference variant) before any Phase 5 gate claim.

## Licensing note (unresolved, recorded not bypassed)

PSX Terms of Use restrict copying, distribution, modification and
automated navigation without prior written permission, and PSX Data
Services/Vending treats data as licensed products. Whether internal
registry use (not republication) of this snapshot is permitted must
be recorded in writing by the parent; it is NOT resolved by this
README. No scraper was built against psx.com.pk or dps.psx.com.pk.
