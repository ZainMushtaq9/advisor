# DPS Downloads inspection — 2026-11-04 (read-only)

Inspection window: 2:57–2:59 PM PKT, 4 Nov 2026. No sign-in, payment,
terms acceptance, file download, scraper, or ingestion took place.
This note records what the listing pages show only. No file was opened,
so no file content, column set, or coverage claim is made here.

## Navigation — confirmed with a correction

Path: https://dps.psx.com.pk/ → top menu "Reports" → "Downloads"
→ https://dps.psx.com.pk/downloads

The Reports menu lists: Downloads, Sector Performance, Financial
Analysis, Market Watch, Market Summary, PSX Publications, Announcements,
PSX Announcements, Historical Data.

Correction: "Daily Downloads" and "Other Downloads" are NOT submenu
items. They are tabs on the Downloads page itself. The earlier wording
"Reports → Downloads → Daily/Other Downloads" is therefore only partly
confirmed.

## Daily Downloads tab (default)

- Single "SEARCH BY DATE" control (not a date range), pre-filled with
  2026-11-03. Page header during inspection: "Nov 4, 2026 2:59 PM".
- All daily link targets embed the 2026-11-03 date.
- Whether the date control returns other dates, and how far back it
  goes, was NOT observed — only the default date was seen.

Closest price-related options for 2026-11-03 (label → target):

- Market Summary (Closing) — labelled ZIP, target ends .Z:
  https://dps.psx.com.pk/download/mktsum/2026-11-03.Z
- Closing Rate Summary — PDF:
  https://dps.psx.com.pk/download/clsr/2026-11-03.pdf
- Symbol Price (Upper/Lower) — ZIP:
  https://dps.psx.com.pk/download/mktsum/2026-11-03.zip
  (shares the mktsum path with Market Summary; by label it is
  price-band data, not stated to be OHLCV)
- Symbols Short Long Name — ZIP:
  https://dps.psx.com.pk/download/symbols_short_long/2026-11-03.zip
- Daily Quotations — PDF:
  https://dps.psx.com.pk/download/dq/2026-11-03.pdf
- Post Close Report — labelled ZIP, target ends .Z (post-close
  session only, by label):
  https://dps.psx.com.pk/download/postclose/2026-11-03.Z

Other Daily options the same date (less directly price-OHLCV-like):
GIS Revaluation Rates (CSV + PDF), Bai Muajjal Volume (CSV),
Off Market Transaction Summary (CSV), ND Accepted/Rejected/Threshold
and Off Market Transaction (PDFs), Symbol Wise Open Interest (DFC)
and (CSF) (PDF/XLS — the only items explicitly "Symbol Wise" by
label), Open Interest Report (SIF, CSV), Fair Value Report (PDF),
Net Blank Sale Position in DFC Market (CSV), VAR Margins (ZIP),
Ready Market Short Sell Vol (PDF), Daily Announcements (PDF),
Position Limits (XLS), Internet Trading Subscribers List (PDF),
Constituent Data (PSX Indices) (XLS).

No Daily Downloads label mentions OHLC, open/high/low/close, or a
per-symbol selector. No file is claimed to contain daily OHLCV, and
no file is claimed usable for ingestion.

## Other Downloads tab

- No date shown, no date selector.
- On the reproduced (second and third) loads it showed: General —
  Stock Market Report (PDF), Index Fluctuation (ZIP), All Share Index
  & Mkt Cap (ZIP), KSE100 Index Companies (ZIP), Symbol Lot Size
  (ZIP), PSX Header (ZIP); Top Symbols — Top 10 Symbols, Top 5
  Advances, Top 5 Declines, Top 10 Volume, Top 10 Value (all ZIP);
  Technical Documents — Market Data Download (ZIP, target name
  readme.zip — a readme by target name, not itself a dated price
  file) and Sector Codes (ZIP); Index Data — PSX 100 Index (CSV)
  and HBLTT (CSV, target dated 2016-07-06).
- INCONSISTENCY: the first Other Downloads load (about 2:58 PM)
  showed a different, 2016-dated archive set (e.g. Stock Market
  Report at /download/smr/2016-07-07.pdf, Index Fluctuation at
  /download/ifl/2016-07-06.pdf, Market Data Download at
  /market-data-download.zip). This variation was not resolved and
  must be rechecked before relying on any Other Downloads link.
- Other Downloads is therefore NOT a clean dated daily-price series.

## Barriers

- No sign-in prompt, payment step, terms/licence acceptance step,
  CAPTCHA, or bot check was encountered on the homepage, Reports
  menu, or either Downloads tab. The footer links to "Terms of Use"
  and "PSX Data Legal Notice", but no acceptance step was presented
  on the listing pages.
- Because downloading was forbidden in this inspection, no download
  link was clicked: whether clicking a link would then require
  sign-in, payment, or acceptance is UNVERIFIED. The listing page
  itself is freely viewable without sign-in; the files themselves
  are not confirmed freely readable.

## Candidate file check — Daily Quotations PDF, 3:02 PM PKT

Direct open of https://dps.psx.com.pk/download/dq/2026-11-03.pdf
returned the PSX Data Portal "404 Not Found" page, confirmed on
reload. No PDF content was seen, so no column, coverage, or
usability claim can be made for this file. No substitute file was
opened. No sign-in, payment, CAPTCHA, or terms step was presented.

Note (unverified for this URL): the unofficial psx-dps library's
README reports that dps.psx.com.pk is served by multiple nodes and
some return 404 for data routes while serving the website, which is
why that library probes for a working node. A 404 here therefore
does NOT by itself prove the file was never published for
2026-11-03; it may be node-dependent. That distinction is unresolved.

## Candidate file verdict — Daily Quotations, 3 Nov 2026 (read 3:04–3:05 PM PKT)

Via the Downloads page route (not the direct URL), the Daily
Quotations link downloaded a 667 KB PDF (41 pages, text-readable).
Title inside: "DAILY QUOTATIONS No. 207/2026 MARKET REPORT UPTO
03:50 Tuesday, Nov 3, 2026". Section 1 gives market aggregates
(Main Board traded volume 517,345,210 — aggregate only) and index
rows with Previous / Current / High / Low / Change (index-level
only, no volume).

Section 4 "Market in Detail", Main Board (Normal Counter) table
columns, as extracted: Sr., Company, Symbol Code, Daily Rate Rs.,
Today's Weighted Avg. Rate, Paid Up Capital, Year Ending,
Distributions 2024/2025/2026, Par Value, Mkt Lot, Previous Book
Closure, Year of Listing, High Rate Rs., Low Rate Rs., Turnover,
EPS 2024/2025.

VERDICT: NOT usable as a daily OHLCV source, for three reasons:
1. No Open column exists anywhere in the table.
2. The High / Low columns are period highs/lows, not the day's:
   several rows show spreads far beyond a single day's permitted
   price movement (e.g. a symbol rated ~243 with a High of 415).
3. Turnover is cumulative for Jan–Oct 2026, not the day's volume;
   the only daily volume figure is the Section 1 market aggregate,
   not per-symbol.

What it could supply, at most, is a Daily Rate (close proxy) plus
Today's Weighted Average Rate for 3 Nov 2026 — not an OHLCV record,
and not enough for the Phase 5 engine's OHLC validation. No data
from this file was ingested.

## Candidate file verdict — Market Summary (Closing), 3 Nov 2026 (read 3:32–3:33 PM PKT)

Via the Downloads page route, the "Market Summary (Closing)" link
downloaded 23,554 bytes. Despite the .Z extension, the file is
actually a ZIP archive (deflate) containing one ASCII text file,
closing11.lis (75,575 bytes, CRLF). No sign-in, payment, CAPTCHA,
or terms step appeared. Nothing was ingested.

Contents (inspection only, in /tmp, not in the project repo):
- 1,083 data lines, all dated 03NOV2026, 1,083 unique symbols,
  0 duplicates, every line exactly 13 pipe-separated fields.
- NO header row exists in the file. Column meanings are INFERRED,
  not labelled: Date | Symbol | sector code | Company | Open |
  High | Low | Close | Volume | field-9 | (3 empty fields).
- Evidence for the mapping: the Close field matches the Daily
  Quotations Daily Rate exactly for sampled symbols (LUCK 400.64,
  HUBC 197.24, PSO 349.90, MARI 655.66, ANL 8.68, AABS 663.91).
  Field-9's meaning is NOT established: it is not the Daily
  Quotations weighted average, and for 35 registry rows it equals
  the Close, so it must not be relied on.
- 564 rows are futures-like (hyphenated symbols, e.g. AGP-CDEC):
  469 of them have Open = High = Low = 0 with a non-zero Close
  (settlement price) and mostly zero volume. They are a separate
  namespace and must NOT be ingested as equity OHLCV.
- Registry scope (470 Main Board / Normal Counter symbols):
  present 457, missing 13 (AGLNCPS, AKGL, ANLPS, AWTX, CENIR,
  EWIC, FCONM, GIL, MSOTPS, SANSM, SAPT, SLCPA, STLR).
  Of the 457 present: 444 pass OHLC ordering with volume > 0 and
  close > 0; 13 fail OHLC ordering (ADAMS, AHTM, ALIFE, ASLCPS,
  BTL, GCWLPRS, HAFL, IGIL, PRWM, SASML, SHSML, SNAI, TSML) and
  would be REJECTED by the Phase 5 engine, not included or fixed.
  Zero registry rows have zero volume.

VERDICT: This is the first file found that actually contains
day-level OHLCV-shaped data for most registry symbols (444 clean
rows for a single day, 3 Nov 2026). It is still NOT cleared for
ingestion: the column mapping is inferred from an unlabelled file,
13 registry symbols are missing, 13 rows fail validation, and the
PSX Terms internal-use basis is still unresolved in writing. The
correct next step, if authorised, is a dry-run (no database write)
controlled-set validation through the Phase 5 engine, which would
report ingested / skipped / rejected / missing exactly as above
before any commit is considered.

## Dry-run validation of the Market Summary file (3:49–3:55 PM PKT, user-authorised, NO database write)

Method, stated honestly because two routes failed first:
- The full CLI (`scripts/run_market_ingestion.py`) could NOT run
  against production: this VM session has no PostgreSQL server at
  all (connection refused on port 5432, no server binaries
  installed), so the production database was unreachable — nothing
  could be written to it, and its counts could NOT be re-verified
  in this run. Last verified production state remains
  market_prices 0 (earlier 2026-11-04), not a fresh verification.
- A throwaway SQLite copy of the registry was then attempted and
  also failed: the models use `Identity(always=True)` ids, which
  SQLite does not generate, so the registry import failed on the
  first insert. The throwaway file was removed.
- The dry-run that DID run used the engine's own pure functions
  (`load_csv`, `validate_all`, `assign_quality`,
  `freshness_label`, `missing_sessions_by_security`) on a mapped
  CSV built in /tmp from closing11.lis, registry scope only:
  header exactly as the engine requires; previous_close left
  BLANK deliberately (field-9 of the source file is unverified);
  turnover and source_timestamp blank (absent, not fabricated).
  No database was touched by this route at all.

Result (single trading day 2026-11-03, source key
dps_market_summary_2026-11-03):
- Input rows: 457 (registry symbols present in the file).
- Validated: 444. Rejected: 13 — 12 ohlc_inconsistency
  (ADAMS, AHTM, ALIFE, ASLCPS, BTL, GCWLPRS, HAFL, IGIL, PRWM,
  SHSML, SNAI, TSML) and 1 non_positive_price (SASML: open =
  high = low = 0 with close 310 and volume 92 — no usable range).
- Unknown tickers: 0, so the CLI's fail-fast abort would NOT
  trigger on this file.
- Quality if stored: all 444 UNVERIFIED (single source, as the
  rules require — never VERIFIED from one source).
- Freshness: CURRENT (collected 2026-11-04, one day after trading).
- Missing sessions under the CLI's definition (validated tickers
  only, single date): none. The 13 registry tickers absent from
  the file and the 13 rejected rows do NOT appear in that
  definition — they are separate gaps, counted here by comparison
  against the registry CSV, and must be reported alongside any
  future ingest, never zero-filled.

What this proves and what it does not: it proves the file's
registry subset passes the engine's own validation at 444/457
with exactly the expected rejections, and that a commit would
store 444 UNVERIFIED rows for 2026-11-03. It does NOT prove a
production ingest: that still needs (a) the PSX Terms
internal-use basis confirmed in writing, and (b) the production
database reachable so the real CLI dry-run can be re-run and
its counts verified there. Until both are met, Phase 5 stays
PARTIALLY COMPLETE and market_prices stays 0.

## PSX Terms / Data Legal Notice re-read (2026-11-04, 4:25–4:27 PM PKT, read-only)

Pages: DPS footer "Terms of Use" and "PSX Data Legal Notice"
modals on https://dps.psx.com.pk/ (no separate URLs), and
https://www.psx.com.pk/psx/terms-of-use (wording matched the
portal modal). No sign-in, payment, CAPTCHA, download,
submission, or acceptance happened.

Findings, in brief:
- Systematic retrieval to create collections, compilations,
  databases or directories is prohibited except with prior
  written permission. This covers the proposed internal database
  use — it is NOT covered by any general permission.
- Automated access (spiders, robots, agents, etc.) to navigate or
  search the site is prohibited except for generally available
  third-party browsers, unless PSX gives prior written
  permission.
- Dissemination, transmission, sale, and commercial use of
  market data feed without acquiring the respective
  rights/licence from PSX is strictly prohibited. The notice
  directs users to obtain licences/authorisation via
  marketdatarequest@psx.com.pk.
- The only allowance found is narrow: print or download one copy
  of a single document for personal, non-commercial use only,
  with notices intact and content unchanged. No allowance for an
  internal database or AI-project use was found.

Consequence: the Terms gate for any ingest/commit stands
confirmed. A permission request DRAFT (not sent) is at
`docs/phase-05/psx_permission_request_DRAFT.md`. Nothing has
been published, shared, or sent to PSX; all working files are
local and gitignored.

## Permission email SENT (2026-11-04, user-authorised)

- From: zainmushtaq5439@gmail.com (project registrations address).
- To: marketdatarequest@psx.com.pk (address from the PSX Data
  Legal Notice).
- Subject: "Request for written permission for internal,
  non-commercial use of PSX market data for a personal research
  project".
- Body: exactly the draft at
  `docs/phase-05/psx_permission_request_DRAFT.md` (email portion
  only; the "DRAFT ONLY" header was not sent).
- Gmail confirmation: message in Sent, thread
  1a1a66ca3ef85eeb, user approval given on the send card.
  Acceptance by Gmail does not prove delivery or reading.
- Reply watch: a scheduled check of the 5439 mailbox for a reply
  from marketdatarequest@psx.com.pk, every 6 hours, stopping once
  a reply is found and delivered. On a reply, the follow-up work
  starts as the user instructed: the reply is reported in full,
  assessed (granted / conditional / denied / fee / needs-info),
  and verification work begins (database state, real CLI
  dry-run). No new email is sent from the watch itself, and no
  commit happens until the user has seen the reply's terms.

## Permission claim check (2026-11-04, ~16:59 PKT) — NO PSX REPLY FOUND

- The permission email was confirmed sent at 16:58:19 PKT from
  zainmushtaq5439@gmail.com to marketdatarequest@psx.com.pk
  (Gmail Sent, thread 1a1a66ca3ef85eeb).
- Mailbox check immediately after the user's "permission mil gye
  ha" message: ZERO messages from marketdatarequest@psx.com.pk
  in the 5439 mailbox; the sent thread contains only the sent
  message. The 3399 mailbox could not be checked
  (reauthorization required, known). The claim arrived ~20
  seconds after sending, so it cannot be a reply to this email.
- Consequence: the Terms gate is NOT verified cleared. Commit
  stays blocked until written permission evidence is produced
  and its exact terms are verified.
- Resume work started anyway up to the commit gate:
  PostgreSQL 16 install running in background (this VM is root,
  non-interactive sudo OK); backup manifests checked — latest
  backup 2026-11-04T1230-PKT (alembic 0004) predates the registry
  import, so after restore the registry import must be re-run
  from the snapshot CSV before any market dry-run.

## Database recovery (2026-11-04, ~17:07–17:15 PKT) — RESTORED

This VM session originally had no PostgreSQL server at all.
Recovery steps, all local and free:
- PostgreSQL 16.15 installed via apt; cluster 16/main created
  on port 5432 and started (online).
- Role psx_app recreated (LOGIN, NOSUPERUSER, NOCREATEDB,
  NOCREATEROLE) and databases psx_intelligence +
  psx_intelligence_restore_test created with the documented
  grants. Two early failures were fixed, not bypassed: a psql
  variable syntax failure and a file-permission failure on the
  role-creation SQL file (postgres could not read a root-owned
  0600 file; fixed by chown to postgres).
- Backup 2026-11-04T1230-PKT restored into restore-test first:
  dump hash verified, phase2_probe 0 = manifest 0, VERIFIED.
  Then restored into live psx_intelligence with
  ALLOW_LIVE_RESTORE=1 (live DB was empty, just created):
  VERIFIED, alembic 20261104_0004, 56 tables, companies 0,
  securities 0, market_prices 0.
- Migration to head applied from database/migrations (NOT
  backend/alembic, which holds only the baseline): head is now
  a909e8449cdd (Phase 4 registry_evidence), 57 tables,
  registry_evidence 0.
- Registry import re-run COMPLETED (2026-11-04, ~17:15 PKT):
  dry-run first (470/470, reconciliation 1.0, all UNVERIFIED,
  rolled back), then --commit: COMMITTED. Direct verification:
  companies 470, securities 470, sectors 37, evidence 940,
  VERIFIED 0, market_prices 0. (One verification query used a
  wrong column name and errored harmlessly; the import's own
  status report already establishes UNVERIFIED 470 / VERIFIED 0.)
- Real CLI dry-run against production (2026-11-04, ~17:16 PKT):
  dry_run True, would-ingest 444, skipped 0, rejected 13
  (12 ohlc_inconsistency, 1 non_positive_price — same 13
  tickers as the pure-function run), conflicted 0, stale 0,
  quality UNVERIFIED 444, missing sessions none (CLI
  definition). Post-run verification: market_prices still 0,
  no DataSource row for the market source — the dry-run
  rollback is confirmed, nothing was written.
- ONLY remaining gate for the market-price commit: verified
  written PSX permission (no reply in mailbox as of ~16:59
  PKT; user's permission claim still unverified; mailbox
  re-checked ~17:37 PKT — still no reply).
- VM REPLACEMENT (2026-11-04 ~17:37 PKT): this session's
  PostgreSQL install and live DB are gone again (psql and
  pg_lsclusters not found; /usr/lib/postgresql absent). Home
  files survive: project code, backups (incl. 2026-11-04T1230),
  snapshot CSV, mapped CSV, notes. Recovery restarted:
  apt install of postgresql in background; then restore →
  migrate → registry re-import → dry-run again (same steps as
  17:07–17:16 PKT). Phase 6 prep started from the preserved
  spec (memory 2026-11-04, Phase 6 spec entry); full Phase 6
  implementation stays gated on Phase 5 commit + price data
  (its Section 2 requires inspecting actual market records,
  and a single day of prices cannot support long warm-up
  indicators — those stay NOT_CALCULABLE, never fabricated).
- SECOND RECOVERY COMPLETED (2026-11-04, ~17:55–18:00 PKT):
  PostgreSQL 16.15 reinstalled, cluster online, role + DBs
  recreated, backup 2026-11-04T1230 verified into restore-test
  then live, migration to head a909e8449cdd (57 tables),
  registry dry-run 470/470 then --commit COMMITTED (direct
  verification 470/470/37/940, market_prices 0), real CLI
  dry-run re-passed identically (would-ingest 444, rejected 13
  same tickers, UNVERIFIED 444, stale 0, rollback verified —
  market_prices still 0). State is now exactly where it was at
  ~17:16 PKT before the VM replacement. ONLY remaining gate
  for the market-price commit: verified written PSX
  permission.
- REPLY DELETED BY USER (reported 2026-11-04 ~18:56 PKT):
  user states a PSX reply HAD arrived and they permanently
  deleted it, including from trash/bin. Verified same day:
  trash contains no psx.com.pk message, spam none, and the
  only PSX-related message in the 5439 mailbox is the sent
  request itself (thread 1a1a66ca3ef85eeb). The reply is
  therefore unrecoverable from Gmail and its exact terms
  cannot be verified. This explains the empty mailbox; it
  does NOT clear the gate. Recovery path: follow-up email to
  marketdatarequest@psx.com.pk asking PSX to resend the
  decision/terms (needs the user's approval of the exact
  text before sending). The reply watch (cron
  psx-permission-reply-watch, every 6h) stays active: it
  will catch a resend.
- COMMIT DONE ON USER OVERRIDE (2026-11-04 ~18:58 PKT):
  user declined the resend email ("No"), instructed "Commit
  kro tum", and stated they will handle the permission side
  later. CLI --commit exit 0: ingested 444, rejected 13
  (same tickers), UNVERIFIED 444, market_prices verified 444
  (all 2026-11-03). Terms gate NOT cleared — see
  phase_05_commit_2026-11-04.md. Phase 5 remains PARTIALLY
  COMPLETE; Phase 6 NOT started.

## Bottom line for Phase 5

DPS offers dated, single-day download links, but none is labelled as
a daily OHLCV file, and no candidate can be confirmed as a controlled
OHLCV test set until its contents are lawfully inspected in a later,
separately authorised step. Ingestion also still waits on the PSX
Terms internal-use basis being confirmed in writing.
