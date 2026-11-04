# DPS Snapshot Import Attempt — 2026-11-04 (Main Board / Normal Counter)

Branch: `phase-05-snapshot-import` (from Phase 5 gate tip `c960937`).
Status of THIS task: **BLOCKED — row data not delivered to this
coordinator's session.** No import was executed against production
data, and no snapshot CSV was written, because writing either
without the inherited browser rows would require inventing rows.

## What the parent reported (not independently re-verified here)

A live-browser read of https://dps.psx.com.pk/listings (Main Board /
Normal Counter, 100 entries per page, page header "Nov 4, 2026 1:17 PM"
throughout) returned all 470 rows, page by page (1–100, 101–200,
201–300, 301–400, 401–470), each with symbol, name exactly as
displayed, sector exactly as displayed, and Clearing Type (NC or
blank). The earlier summarized report's CTM/CWHC entries and its
blank-type exceptions list are superseded by the page-by-page reads.

## What this coordinator actually found in its own session

- No file in the repository (or in any agent tool-output directory
  accessible here) contains the 470 row tables. A full-workspace
  search found only the Phase 4 0-row text-fetch snapshot note
  (`source_research_raw/snapshot_dps_listings_2026-11-04.md`).
- A text fetch of https://dps.psx.com.pk/listings by this
  coordinator returned the same 0-row result as Phase 4 (26 lines:
  index strip, board labels, disclaimer) — the portal is
  JavaScript-driven, as recorded in D-52.
- 24 browser screenshots from the parent's browser task exist on
  disk (`.hatch-browser/snapshots/browser-task:3d48bbb1-.../`), each
  a 1920x999 viewport showing ~25 entries with overlapping scroll
  positions and cut rows at the edges. They are evidence that the
  page rendered, not a row-level record: transcribing 470 exact
  rows (including displayed typos) from them would be a
  reconstruction with unavoidable misreading risk, not the
  inherited browser rows. They were NOT used as a data source.
- No OCR tooling is available on this VM (no tesseract binary, no
  pytesseract), so even a screenshot-OCR recovery path is not
  available here without new tooling whose output would still need
  row-by-row verification against the authoritative report.

## What was verified in the actual database (by this coordinator)

PostgreSQL 16.15, database `psx_intelligence`, 2026-11-04:

| Table | Production rows |
|---|---|
| companies | 0 |
| securities | 0 |
| sectors | 0 |
| registry_evidence | 0 |
| company_identifiers | 0 |
| symbol_history | 0 |
| public tables | 57 |
| alembic_version | 1 row (`a909e8449cdd`, Phase 4 head) |

The Phase 5 gate evidence is therefore unchanged: the registry is
still empty in production.

## What was built and tested (preparation, ready to run)

- `scripts/import_dps_snapshot.py` — strict CSV validation, import
  through the Phase 4 engine, `reconcile()` run, database counts by
  status, `--dry-run` (rollback) default and `--commit` mode.
  Tested 2026-11-04:
  - 3-row synthetic TEST ONLY CSV, dry-run: 3 companies, 3
    securities, 2 sectors, 6 evidence rows created in-transaction;
    re-import skipped 3 (idempotent); reconcile coverage 1.0;
    all records UNVERIFIED; VERIFIED securities = 0; rolled back;
    live database confirmed still 0 afterwards.
  - Validation rejections (before any database access): duplicate
    symbol, non-continuous row_no, invalid clearing_type.
  - A validation-order bug found during testing (backend import
    built the DB engine before CSV validation) was fixed and
    re-tested: malformed CSVs now fail on validation alone.
- Snapshot provenance README:
  `docs/phase-04/source_research_raw/dps_listing_status_2026-11-04_main_board_normal_counter.README.md`
  — header fields, scope limitation, CSV contract, verification
  rule, and the exact gap.
- Phase 5 gate report re-check section (2026-11-04) appended to
  `docs/phase-05/phase_05_gate_report.md` — original BLOCKED record
  preserved, not erased.

## What is still required (single precise action)

The parent must deliver the browser report's row tables as a file
at
`docs/phase-04/source_research_raw/dps_listing_status_2026-11-04_main_board_normal_counter.csv`
(470 rows, `row_no,symbol,name,sector,clearing_type`, names and
sectors exactly as displayed), or re-deliver the row text so this
coordinator can write that file and verify it (470 rows, row_no
1–470 continuous, no duplicate symbols, no placeholders). On
delivery, the run is mechanical: dry-run, verify, commit, 20-row
spot-check (including one blank-Clearing-Type row and one
rights/preference variant), reconcile, then a Phase 5 gate
re-judgement on real evidence.

## Statuses (evidence-based only)

- D-54 (Phase 5 gate failure): stays OPEN — the gate evidence is
  unchanged (registry still 0 in production).
- D-51 (direct DPS access fails from this VM): stays OPEN — not
  re-tested in this run; the parent's browser read is a different
  route, not a fix to VM DPS access.
- D-52 (DPS Listing Status 0 rows via text fetch): stays OPEN as
  a text-fetch limitation — the parent's live-browser read
  overcame the rendering barrier in the parent's session, but the
  row evidence is not in this repository, so D-52 cannot be
  closed on that basis alone.
- Phase 5 gate: still BLOCKED. Phase 5 market-data implementation:
  NOT started. No push, no merge, no VERIFIED claim, no
  full-market claim is made by this document.
