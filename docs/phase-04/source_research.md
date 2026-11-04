# Phase 4 — Source Research

Date: 2026-11-04 (Asia/Karachi). Research only; no account created, no
sign-in, no bypass of any access control. All fetches below are text
fetches unless stated otherwise. A text fetch is NOT a live-browser
visit, and a cached page is NOT a current page — both are labelled.

## Sources researched

### 1. PSX official website — https://www.psx.com.pk/
- What was actually seen (text fetch, 2026-11-04 12:56 PKT): homepage
  scrip tables — 26 partial rows across volume leaders (7), GEM board
  (3), highlighted symbols (6), futures contracts (5) and CDEC
  contracts (5). Company full names are NOT shown; only scrip codes.
  No sector, listing-status, or company-to-ticker mapping is given
  for those rows, and the homepage does not state that the tables
  are a complete listed-company registry.
- Fields available on that page: scrip code, price, high, low, change,
  volume. Fields NOT available: legal company name, sector name,
  listing status, ISIN.
- Verdict: usable as market context only. NOT usable as a registry
  snapshot, because a registry row requires a legal name (and,
  ideally, a sector and a status) that this page does not supply.
  Futures/CDEC rows are contracts, not equities, and were counted
  separately, never merged with the underlying equity symbol.
- Raw file: `source_research_raw/snapshot_psx_homepage_2026-11-04.md`
  (marked PARTIAL in the file itself).

### 2. PSX Data Portal (DPS) — https://dps.psx.com.pk/
- Listing Status page, https://dps.psx.com.pk/listings (text fetch,
  2026-11-04 12:56 PKT): title and board/category labels only
  (Main Board, GEM Board, Normal Counter, Non-Compliant Segment or
  Winding-Up Segment). ZERO company/ticker/sector rows appeared in
  the fetched text. The page also carries a disclaimer that PSX and
  CS Solutions do not guarantee timeliness, accurateness, or
  completeness of the data on the website.
- DPS sitemap, https://dps.psx.com.pk/sitemap (same date): lists
  under "Companies" — Listing Status, Circuit Breakers, Margin
  Eligible Securities, Acquisition/Loss of Shares — and under
  "Market" — Today's Summary, Sector Overview, Stock Screener,
  Historical Data, Eligible Scrips. No company rows on the page.
- Why 0 rows is NOT a finding that DPS has no listing data: DPS is a
  JavaScript-driven portal and a text fetch does not execute its
  table rendering. The listing table may render in a live browser
  session. That live-browser check was NOT done by a generic
  subagent (no live browser) and is recorded as a parent task.
- Direct DPS access from this VM (2026-11-04, psx-dps library
  transport): FAILED — `NoHealthyNode: could not connect to any of
  198.18.60.204, 52.128.23.16, 52.128.23.6 on port 443`. This is an
  environment network failure (same family as Phase 2's Docker
  registry TLS failure), not evidence about DPS itself.
- DPS market-watch page via text fetch: the copy returned was
  crawled 2026-01-25 (283 days old) — a STALE cached copy, not a
  current snapshot. It shows SYMBOL, a numeric SECTOR code (e.g.
  0824), LISTED IN indices, and prices. Sector codes have no name
  mapping on that page, and no company legal names are shown.
  Verdict: NOT used as a registry snapshot (stale, no names, codes
  without a mapping). Recorded here so a later reader does not
  mistake the cached table for current registry data.
- Raw file: `source_research_raw/snapshot_dps_listings_2026-11-04.md`
  (0 rows, with the JS-rendering caveat stated in the file).

### 3. PSX official — About Us (dated aggregate, no list)
- https://psx.com.pk/psx/exchange/profile/about-us/about-us
  (text fetch, 2026-11-04 12:56 PKT): aggregate counts only —
  "535 (+5 GEM Board) companies listed… distributed amongst 37
  sectors/groups of industries", market cap Rs 19.83 trillion,
  "18 indices listed". The page itself dates the count: as of
  August 31, 2026 (indices as of June 30, 2026).
- Verdict: a useful DATED anchor for the count debate, but NOT a
  registry: no company, ticker, or sector list is on this page.
  It also shows the count moves with the date (see §5: a
  December 31, 2025 snippet says "more than 522" companies) —
  another reason no single total is treated as fixed.

### 4. PSX official — Terms of Use and Data Vending (licensing)
- Terms of Use, https://www.psx.com.pk/psx/terms-of-use (text
  fetch, 2026-11-04 12:56 PKT): content is protected by IP law;
  no use "except as expressly provided"; no licence "without
  the express written permission of PSX"; users "will not sell,
  license, rent, modify, print, copy, reproduce, download,
  upload, transmit, distribute, disseminate…" except with
  prior written permission, with a narrow exception for a
  single unaltered copy for personal, non-commercial use; use
  of browsers/spiders/robots/agents to navigate/search the
  site is "strictly prohibited" without prior written
  permission; content is "As is" with no warranty of accuracy,
  timeliness, or completeness.
- Data Services / Vending,
  https://www.psx.com.pk/psx/product-and-services/data-services-vending:
  real-time Level 1+/Level 2 feeds, end-of-day summaries, and
  historical data are LICENSED products; authorised clients are
  "permitted to use PSX data", and redistribution is marked as
  subject to "PSX's prior approval and license".
- Consequence for Phase 4: free public access is NOT a
  redistribution licence, and automated navigation itself is
  restricted by the site's terms without permission. Whether
  internal registry use (not republication) is permitted is a
  licensing decision for the parent, not a claim made here.
  No PSX data is redistributed by this phase, and no scraper
  was built against psx.com.pk.

### 5. SECP — https://www.secp.gov.pk/
- Homepage text fetch (2026-11-04 12:56 PKT): NO PSX
  listed-company/ticker/sector registry was seen — only an
  Annual Compliance 2026 notice, a "List of Companies suspected
  to be engaged in Unauthorized Activities" title (no list in
  the fetched text), eZfile, NBFC licensed-entities links, and
  regulations notices. Search results show listed-company
  REGULATIONS (e.g. Code of Corporate Governance, Takeovers
  Regulations), not a company/ticker list.
- Status: UNVERIFIED as a machine-readable registry source, and
  NOT used as one in this phase. SECP remains an OFFICIAL source
  for verification-rule purposes only if/when a specific SECP
  list page is located and fetched — that check is a parent
  follow-up, not a Phase 4 claim.

### 4. Public libraries (README evidence only)
- psx-dps (MIT, umairsandhu/psx-dps): claims live quotes, KSE-100
  constituents with weights, ~496 trading symbols, whole-market
  snapshot in one request, 38 sectors, 224k+ announcements.
  These are README claims, NOT live-verified coverage in this
  phase — the library's own transport could not connect from this
  VM (see §2).
- psxdata (MIT, alpha 0.1.0a1): claims 1000+ tickers, 37 sectors,
  KSE-100 constituents. Also README claims only, not live-verified.
- Neither library is adopted as a Phase 4 data source, and neither
  is installed into the project backend.

## Count discrepancies (Phase 1 gate G-03) — NOT harmonised

| Claim | Source | Status |
|---|---|---|
| ~496 trading symbols | psx-dps README | README claim, not live-verified |
| ~1,029 listed instruments | psx-dps README FAQ ("market watch carries ~496 of ~1,029 listed instruments") | README claim, not live-verified; the library itself presents these as different universes (trading vs all listed, incl. non-trading/contract symbols) — its explanation, not an official reconciliation |
| 1000+ tickers | psxdata README (`tickers()`) | README claim, not live-verified |
| ~729 screener symbols | psxdata README (`screener()`) | README claim, not live-verified; inconsistent with the same README's 1000+ tickers — different functions/universes, not reconciled by the README |
| 38 sectors | psx-dps README | README claim, not live-verified |
| 37 sectors | psxdata README + PSX About Us (as of Aug 31, 2026) | README claim + dated official aggregate; sector count still unresolved as a single figure |
| 535 (+5 GEM) companies, 37 sectors | PSX official About Us | Dated official aggregate, as of Aug 31, 2026; no list on the page |
| More than 522 companies, more than 37 sectors | PSX Margin Trading page (search snippet only) | Snippet, as of Dec 31, 2025; different date, different total — consistent with counts moving over time, not with a fixed total |

No winner was picked. The registry keeps source taxonomies
separate (see registry_architecture.md), and no full-market
completeness claim is made in this phase.

## Redistribution

PSX publishes no official public API. DPS endpoints are
undocumented and can change. Free public access is NOT a licence
to redistribute PSX data: any redistribution of PSX data requires
a written PSX agreement (Phase 1 gate). The DPS disclaimer quoted
above is recorded, and no PSX data is redistributed by this phase.

## What this research does NOT establish

- No complete official listed-company list was obtained.
- No company legal name, sector name, or listing status was
  verified from an official source in this phase.
- No source was verified as machine-readable on this VM.
- Therefore the production registry is EMPTY (0 companies, 0
  securities, 0 sectors) and reconciliation against a complete
  dated official snapshot is BLOCKED — see
  reconciliation_methodology.md and phase_04_completion_report.md.
