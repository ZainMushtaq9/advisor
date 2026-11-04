# Phase 5 — Market Source Research (RESEARCH ONLY, NOT COLLECTION)

**Status: research only. Date: 2026-11-04 (Asia/Karachi). Branch:
`phase-05-snapshot-import`. No market data was collected, no adapter
was built, no download of market data was performed, and no source
below is presented as a verified collector.**

This document completes the 15-field template from
`source_research_preparation.md` section 1 for each candidate source.
No field is left as "assumed": where a fact could not be verified in
this research, the field says **UNVERIFIED** and states why. Every
README statement is labelled **(README claim, not a verified fact)**.
README claims are never a population base, a price, or a coverage
claim.

## 0. Standing context (carried forward, not re-assumed)

- Production PostgreSQL 16.15 database `psx_intelligence` holds the
  Phase 4 registry from a single dated DPS snapshot file
  (`docs/phase-04/source_research_raw/dps_listing_status_2026-11-04_main_board_normal_counter.csv`,
  Main Board / Normal Counter only, DPS
  https://dps.psx.com.pk/listings, page header Nov 4, 2026 1:17 PM
  Asia/Karachi): companies 470, securities 470, sectors 37,
  registry_evidence 940, **all UNVERIFIED**. GEM (5) and
  Non-Compliant (93) are NOT in the registry. KSE-100 completeness
  is NOT established. `market_prices` is 0.
- Prior defects, still open at the start of this research: D-51
  (direct DPS access from this VM fails, `NoHealthyNode`); D-52
  (DPS Listing Status returns 0 rows via text fetch,
  JavaScript-driven); D-53 (stale 2026-01-25 cache, excluded).
- PSX Terms of Use (re-read 2026-11-04, see section 1(i) field 12)
  restrict copying/distribution/modification and automated
  navigation (spiders/robots/agents) without prior written
  permission, and PSX Data Services/Vending treats real-time/EOD/
  historical data as licensed products. **The internal-use
  question (internal use, not republication) remains UNRESOLVED
  in writing. Parent decision pending.** See section 3 for exactly
  what the parent must confirm before any live collection.
- Scope rule for this phase: PKR 0 / free only; no fabricated
  prices, coverage, or verification claims; no external accounts;
  no secrets; no sign-up, payment, or ToS acceptance was performed
  in this research.

## 1. Candidate sources — 15 fields each

### (i) PSX Data Portal (DPS)

1. **Official source name:** Pakistan Stock Exchange (PSX) Data
   Portal (DPS).
2. **Exact URL:** https://dps.psx.com.pk/ — Listing Status page
   https://dps.psx.com.pk/listings (the page the Phase 4
   registry snapshot was read from via live browser).
3. **Source authority:** Official — operated by Pakistan Stock
   Exchange Limited. (Authority is official; individual page
   contents still require the dated-file verification in
   section 3.)
4. **Available document/data types:** Listing Status table
   (symbol, company name, sector, clearing type / board
   segment, per the 2026-11-04 snapshot); market-watch / live
   quotes; index levels; eligible-scrips lists. The DPS
   sitemap (search-crawl text, not verified by a direct fetch
   in this research) also lists Reports, Downloads, Daily
   Downloads and Other Downloads. **The contents, columns, and
   date coverage of any DPS download file are UNVERIFIED** —
   no DPS data route was fetched in this research, by design.
5. **Historical coverage:** UNVERIFIED for market prices. No
   DPS price-history range was verified in this research. The
   only verified DPS artefact is the single dated Listing
   Status snapshot of 2026-11-04 (registry, not prices).
6. **Available reporting periods:** UNVERIFIED for prices.
   Listing Status is a point-in-time view (the snapshot's
   header datetime is its period). Daily/EOD periods are
   claimed only via third-party libraries (sections 1(ii)-(iii)),
   not verified against DPS itself.
7. **Publication frequency:** UNVERIFIED for prices. Listing
   Status changes as listings change; no publication schedule
   was verified. Live market data is session-driven by
   definition, but no DPS schedule statement was verified.
8. **Download or access method:** Live browser (generally
   available third-party browser) reading the JavaScript-driven
   pages, with the resulting row tables saved as a dated file
   — the route already used for the registry snapshot. No
   automated download method is authorised by this research
   (see fields 10 and 12).
9. **Direct links available?:** Listing Status and other DPS
   pages have stable page URLs (e.g. `/listings`), but the
   tables themselves are JavaScript-driven: a text fetch of
   `/listings` returns 0 rows (D-52). A direct
   machine-readable data link (CSV/API) from DPS was NOT
   located or verified in this research. **UNVERIFIED.**
10. **Automatic download permitted?:** NO — not without prior
    written permission from PSX. PSX Terms of Use prohibit
    use of browsers other than generally available third-party
    browsers, engines, software, spiders, robots, avatars,
    agents, tools or other mechanisms to navigate, search or
    determine the PSX Website, except with prior written
    permission (quoted in field 12). A scraper or adapter
    hitting DPS data routes is therefore **BLOCKED**, not
    merely unselected.
11. **Access restrictions:** No account, API key, or paywall
    was encountered for the public DPS pages in prior work
    (live-browser reads). Whether any DPS data route requires
    authentication is UNVERIFIED — no data route was probed.
    The binding restriction is legal (field 12), not a login.
12. **Terms of use:** PSX Terms of Use,
    https://www.psx.com.pk/psx/terms-of-use (page text re-read
    2026-11-04): Content is PSX-owned/licensed; "except if we
    give you prior written permission, you will not sell,
    license, rent, modify, print, copy, reproduce, download,
    upload, transmit, distribute, disseminate, publicly
    display, publicly perform, publish, edit, adapt, compile
    or create derivative works from any Content or materials
    (including, without limitation, through framing or
    systematic retrieval to create collections, compilations,
    databases or directories) or otherwise transfer any of the
    Content to any third person"; "Except if we give you prior
    written permission, use of any Web browsers (other than
    generally available third-party browsers), engines,
    software, spiders, robots, avatars, agents, tools or other
    devices or mechanisms to navigate, search or determine the
    PSX Website is strictly prohibited." A single unaltered
    copy for personal, non-commercial use is permitted with
    notices intact. PSX Data Services/Vending
    (https://www.psx.com.pk/psx/product-and-services/data-services-vending,
    search-crawl text 2026-11-04) lists real-time, Level 1+,
    Level 2 (tick-by-tick), corporate announcements and general
    data services as licensed products, with redistribution
    subject to PSX prior approval and licence. **Whether
    internal, non-republication use of a dated DPS file inside
    this project's database is permitted is UNRESOLVED in
    writing** — the Terms text above does not grant it
    expressly, and no written PSX permission is on file.
13. **Redistribution limitations:** Redistribution requires
    PSX prior approval/licence (Data Services/Vending page).
    Nothing in this research authorises republication of DPS
    data, in whole or in part, in any public artefact, API
    response, or dataset.
14. **Known data-quality issues:** D-51 (direct DPS access
    from this VM previously failed, `NoHealthyNode`); D-52
    (JavaScript-driven tables, 0 rows via text fetch); DPS
    pages carry a disclaimer (search-crawl text of
    `/listings`) that PSX and CS Solutions do not guarantee
    timeliness, accuracy, or completeness of website data.
    Symbol universes differ by view: the registry snapshot
    covers Main Board / Normal Counter only, while DPS market
    views cover a different, trading-symbol subset — the two
    must never be conflated (see section 1(ii) field 14).
15. **Last successful verification (date, method, result):**
    2026-11-04, single HEAD request to the site root only
    (bounded probe authorised for this research; NOT a data
    route, NOT a scraper): `curl -I https://dps.psx.com.pk/`
    returned HTTP 200 OK (Server: nginx/1.20.2, 08:42 UTC).
    **This root response does NOT close D-51 or D-52:**
    D-51 concerned direct data-route access and D-52 concerned
    the JavaScript listings table, neither of which was
    re-tested, because this research was forbidden from
    fetching DPS data routes. The registry snapshot itself was
    verified earlier (2026-11-04, live-browser page-by-page
    read, 470 rows, header Nov 4, 2026 1:17 PM Asia/Karachi)
    and is the only verified DPS artefact in this project.

### (ii) psx-dps library (umairsandhu/psx-dps)

1. **Official source name:** psx-dps — "Pakistan Stock Exchange
   (PSX) market data in Python". Unofficial; its own README
   states "Unofficial and unaffiliated. Not endorsed by the
   Pakistan Stock Exchange."
2. **Exact URL:** https://github.com/umairsandhu/psx-dps
   (README page text re-read 2026-11-04; repository created
   2026-09-29, 17 commits, 2 stars, 1 fork, 0 releases, MIT
   licence, default branch main, current commit
   02001d8b744aeabe284513cd6a9898d7f7189561 as crawled).
3. **Source authority:** Unofficial third-party library. Its
   underlying data source is DPS itself (README: data "from
   the official PSX data portal"), so its authority is
   derivative of DPS and inherits DPS's Terms (see field 12).
4. **Available document/data types (README claims, not
   verified facts):** live quotes (OHLC, LDCP, volume, full
   order book); whole-market snapshot; end-of-day history;
   intraday ticks (today only); indices and constituents with
   weights; sector data; 224k+ announcements each with a PDF
   URL; historical tables (every symbol on a trading day, or
   one symbol's month with high/low); market breadth.
5. **Historical coverage (README claim, not a verified fact):**
   "~5 years of daily bars per symbol" via `eod()`, in a single
   request. Not live-verified from this VM; no date range was
   confirmed by an actual call in this research (no call was
   made, by design).
6. **Available reporting periods (README claim, not a verified
   fact):** daily (EOD) bars; today's intraday tick series;
   monthly high/low tables; single-trading-day whole-market
   tables. Historical intraday bars (past days) are NOT
   claimed: the README's intraday feature is "Today's full
   tick series" only.
7. **Publication frequency (README claim, not a verified
   fact):** live during the trading session; the README
   describes market-aware caching (60s while trading, cached
   until next open once shut) and a 1 req/s cross-process rate
   limit. No PSX publication schedule was verified.
8. **Download or access method:** Python library installed
   from git (`pip install git+https://github.com/umairsandhu/psx-dps`),
   plus a CLI (`psx-dps quote / market / eod / announcements /
   movers / diagnose / nodes`) with `--json`/`--csv` output.
   No API key or account is required per the README.
   **No installation, import, or call was performed in this
   research** — method is as documented in the README only.
9. **Direct links available?:** UNVERIFIED. The README points
   to internal docs (API.md, ENDPOINTS.md, DISCOVERY.md) for
   endpoint details, but the DPS endpoints themselves are
   undocumented PSX front-end JSON endpoints (README FAQ:
   "PSX publishes no public API and no documentation for
   one"). No DPS data-route URL was verified in this research.
10. **Automatic download permitted?:** NO for this project.
    The library automates navigation of DPS data routes and
    probes/pins DPS nodes — exactly the automated-navigation
    category PSX Terms restrict without prior written
    permission. The README's own FAQ argues no login/paywall/
    click-through terms exist and that DPS serves no
    `robots.txt`, and states "That is not a licence to
    redistribute". That argument does NOT override the PSX
    Terms of Use text quoted in section 1(i) field 12, and it
    is not legal advice (README's own words). **Live use of
    psx-dps is therefore BLOCKED in this project unless and
    until PSX written permission is obtained and recorded.**
11. **Access restrictions:** Per README, none technical (no
    key, no account, zero dependencies, Python 3.8+). The
    binding restriction is legal (field 10/12), plus the
    operational fragility in field 14.
12. **Terms of use:** Library licence MIT (repository
    metadata). The library licence does NOT license the
    underlying PSX data. Underlying data remains subject to
    PSX Terms of Use and Data Services/Vending licensing
    (section 1(i) field 12-13). The README disclaimer adds:
    endpoints are undocumented and can change without notice;
    no warranty of accuracy or timeliness; nothing is
    investment advice.
13. **Redistribution limitations:** Same as DPS (section 1(i)
    field 13). The README itself warns market data is PSX's to
    license and reselling or republishing a live feed requires
    a conversation with PSX. No redistribution is authorised
    by this research.
14. **Known data-quality issues (README claims, not verified
    facts):** multi-node 404 quirk — DPS is served by several
    nodes, some returning HTTP 404 for every data route while
    serving the ordinary website with 200, with a single
    rotating A record (README cites 52.128.23.6 returning 404
    on `/data/symbol-position` vs 52.128.23.16 returning 200);
    the library therefore keeps a pool of candidate nodes and
    probes for one that serves data. Universe mismatch:
    ~496 trading symbols in market watch vs ~1,029 listed
    instruments (README) — a live-quote universe is NOT the
    registry universe (470 snapshot securities) and must not
    be used as one. Sector count in the README is 38, vs 37
    sectors in the Phase 4 registry snapshot — an unresolved
    discrepancy, recorded not reconciled. Corporate-action
    renames are silent (README example: ENGRO became ENGROH in
    2024). Endpoints can change without notice. The library
    has only 2 stars and 17 commits (created 2026-09-29):
    thin adoption history, recorded as a risk signal, not a
    quality verdict.
15. **Last successful verification (date, method, result):**
    2026-11-04, README page text re-read (crawled 08:42 UTC).
    Result: README claims above confirmed as *claims* (they
    appear in the README text). **No live verification:**
    no install, no import, no data call, no DPS data-route
    fetch was performed. The library is therefore NOT a
    verified collector, and none of its figures may be cited
    as observed data.

### (iii) psxdata library (psxdata/psxdata)

1. **Official source name:** psxdata — "Python Library for
   Pakistan Stock Exchange (PSX) Data". Unofficial; a
   community library, not a PSX publication.
2. **Exact URL:** https://github.com/psxdata/psxdata
   (README page text re-read 2026-11-04; repository created
   2026-04-05, 206 commits, 30 stars, 9 forks, 5 releases,
   MIT licence, default branch main, current commit
   170b1247b22bc1644186144990316ec1d4e5ce2d as crawled).
   Full documentation claimed at psxdata.mintlify.app;
   PyPI distribution: https://pypi.org/project/psxdata/
   (release files 1.1.0 / 1.2.0 seen in search results; the
   README's own alpha note says 0.1.0a1 — version
   discrepancy noted, not resolved).
3. **Source authority:** Unofficial third-party library.
   Its README describes "Core scraping" as complete, and its
   repository topics include "web-scraping"; its underlying
   data source is PSX/DPS, so it inherits DPS's Terms (see
   field 12). It is not an official PSX source.
4. **Available document/data types (README claims, not
   verified facts):** historical OHLCV prices; real-time
   quotes; all listed tickers (1000+); symbol/sector/name
   metadata; full unfiltered screener table (~729 symbols);
   KSE-100 index constituents; sector aggregates (37
   sectors); fundamentals (financial reports); debt market
   instruments (TFCs, Sukuks); margin-eligible scrips.
   A FastAPI REST wrapper lives separately at
   psxdata/psxdata-api (README claim).
5. **Historical coverage (README claim, not a verified fact):**
   daily historical OHLCV bars; no start date, depth in
   years, or per-symbol coverage was stated in the README
   text re-read. **Depth is therefore UNVERIFIED** — do not
   quote a year count for psxdata (the ~5-year figure belongs
   to psx-dps, section 1(ii), and is itself only a claim).
6. **Available reporting periods (README claim, not a verified
   fact):** daily bars only, plus live quote snapshots. The
   README's "Data Availability" section is explicit:
   "psxdata supports daily historical OHLCV bars and live
   quote snapshots only."
7. **Publication frequency:** UNVERIFIED. The README states
   disk caching (historical cached forever, live data 15 min)
   and exponential-backoff retries, but no PSX publication
   schedule was verified.
8. **Download or access method:** Python library via pip
   (`pip install psxdata`, Python 3.11+; optional
   `psxdata[socks]` for SOCKS proxy support; proxy
   configuration including `X-Req-Id` token fetch is
   documented in the README). Functions include
   `stocks(symbol, start, end)`, `tickers()`, `symbols()`,
   `quote(symbol)`, `screener()`, `indices(name)`,
   `sectors()`, `fundamentals(symbol)`, `debt_market()`,
   `eligible_scrips()`. **No installation, import, or call
   was performed in this research** — method is as documented
   in the README only.
9. **Direct links available?:** UNVERIFIED. No PSX/DPS
   data-route URL was verified in this research; the README
   describes dynamic column extraction from HTML `<th>`
   tags, i.e. HTML scraping, not a documented API.
10. **Automatic download permitted?:** NO for this project.
    The library's core function is scraping PSX pages —
    automated navigation of the PSX Website without prior
    written PSX permission, which PSX Terms prohibit (section
    1(i) field 12). **Live use of psxdata is therefore BLOCKED
    in this project unless and until PSX written permission
    is obtained and recorded.** Its MIT licence covers the
    library code, not the PSX data it scrapes.
11. **Access restrictions:** Per README, none technical stated
    (free, open-source; no key/account mentioned). The binding
    restriction is legal (field 10/12), plus alpha status
    (field 14).
12. **Terms of use:** Library licence MIT (repository
    metadata). Underlying PSX data remains subject to PSX
    Terms of Use and Data Services/Vending licensing (section
    1(i) field 12-13). No PSX permission for scraping is
    stated anywhere in the README text re-read.
13. **Redistribution limitations:** Same as DPS (section 1(i)
    field 13). Nothing in the README grants redistribution
    rights over PSX data, and this research authorises none.
14. **Known data-quality issues:** Alpha status — README
    alpha note: 0.1.0a1, "APIs may change before 1.0";
    PyPI shows later 1.1.0/1.2.0 release files, so the README
    alpha note may be stale — **version status is
    UNVERIFIED, not resolved**. Universe figures conflict
    across README functions and with other sources: tickers
    1000+, screener ~729 symbols, sectors 37 (matching the
    registry snapshot's 37, but that match alone proves
    nothing about membership). README's own validation
    (OHLC constraint checks, duplicate/future-date detection)
    is a claim, not an observed result. HTML scraping is
    fragile by the README's own framing (it contrasts itself
    with solutions that "break silently when PSX changes its
    HTML"). No live call was made, so no quality result was
    observed.
15. **Last successful verification (date, method, result):**
    2026-11-04, README page text re-read (crawled 08:42 UTC).
    Result: README claims above confirmed as *claims*, and
    the intraday limitation confirmed as a README statement
    (see section 2). **No live verification:** no install,
    no import, no data call was performed. The library is
    therefore NOT a verified collector.

### (iv) PSX homepage (psx.com.pk)

1. **Official source name:** Pakistan Stock Exchange Limited
   (PSX) official website.
2. **Exact URL:** https://www.psx.com.pk/
3. **Source authority:** Official — PSX itself. Authority
   does not make a partial page a price-history source.
4. **Available document/data types:** Homepage market summary
   (index levels, selected scrip codes and prices); About Us
   aggregates; Terms of Use; Data Services/Vending product
   descriptions; regulations and investor resources. No
   security-level price history is published on the homepage.
5. **Historical coverage:** UNVERIFIED / none observed. The
   homepage is a current-session view, not an archive.
6. **Available reporting periods:** Current session only, as
   observed in Phase 4. No historical reporting periods are
   offered on the homepage.
7. **Publication frequency:** UNVERIFIED. Presumably updated
   during trading sessions; no schedule statement was verified.
8. **Download or access method:** Ordinary browser reading of
   the public homepage. No download file is offered for
   market prices on the homepage.
9. **Direct links available?:** The homepage URL is stable,
   but it does not link to a machine-readable price dataset.
   **No direct price-data link verified.**
10. **Automatic download permitted?:** NO without prior written
    PSX permission, per the same Terms quoted in section 1(i)
    field 12 (automated navigation ban). Ordinary browser
    reading by a person is the permitted route.
11. **Access restrictions:** None observed for the public
    homepage (no login/paywall encountered in Phase 4 text
    fetch). The binding restriction is legal (field 10/12).
12. **Terms of use:** PSX Terms of Use (section 1(i) field 12),
    including the personal, non-commercial single-copy
    allowance and the automated-navigation prohibition.
13. **Redistribution limitations:** Same as DPS (section 1(i)
    field 13): redistribution requires PSX prior approval/
    licence. None is authorised by this research.
14. **Known data-quality issues:** Phase 4 text fetch gave
    only 26 PARTIAL scrip rows (codes/prices only, no legal
    names, sectors, or statuses) — market context only, not a
    registry or price-history source. PSX About Us gives a
    dated aggregate only (535 + 5 GEM companies, 37 sectors,
    as of August 31, 2026 — no list). Homepage figures are
    session snapshots and go stale immediately.
15. **Last successful verification (date, method, result):**
    2026-11-04, two checks: (a) single HEAD request to the
    site root only: `curl -I https://www.psx.com.pk/`
    returned HTTP 200 OK (Server: DOSarrest, 08:42 UTC) —
    root reachability only, not a data verification; (b)
    Phase 4 text fetch (26 PARTIAL rows, carried forward).
    No homepage price was collected or relied on in this
    research.

### (v) SECP (secp.gov.pk)

1. **Official source name:** Securities and Exchange
   Commission of Pakistan (SECP).
2. **Exact URL:** https://www.secp.gov.pk/ (no specific
   PSX registry or price page was located — see field 9).
3. **Source authority:** Official — Pakistan's capital-market
   regulator. Regulatory authority does not imply that SECP
   publishes a PSX price or registry dataset.
4. **Available document/data types:** Circulars, regulations,
   press releases, licensing lists (e.g. active insurers /
   insurance brokers, per third-party reporting of SECP data
   pages). **No PSX company/ticker/sector registry and no
   PSX price dataset was located.**
5. **Historical coverage:** UNVERIFIED for any PSX market
   data — none was located, so no coverage exists to state.
6. **Available reporting periods:** UNVERIFIED — none
   located for PSX market data.
7. **Publication frequency:** UNVERIFIED for PSX market data
   — none located.
8. **Download or access method:** UNVERIFIED for PSX market
   data — no SECP download file for PSX prices or registry
   was located. SECP's known downloads are regulatory
   documents, not market data.
9. **Direct links available?:** NO — no specific SECP list
   page for PSX companies or prices was located in Phase 4
   text fetches or in this research's search (search results
   returned SECP circulars and an insurance-licensing page,
   not a PSX list). A specific SECP list page, if ever
   located, must be fetched and recorded before it is relied
   on.
10. **Automatic download permitted?:** UNVERIFIED — no SECP
    terms statement for PSX market data was located, because
    no such dataset was located. This field cannot be
    answered "yes" on the basis of SECP being a public
    regulator website. **Do not treat SECP as an authorised
    automated source.**
11. **Access restrictions:** UNVERIFIED for PSX market data —
    none located. SECP's public regulatory pages are
    publicly readable; that says nothing about a market-data
    dataset that was not found.
12. **Terms of use:** UNVERIFIED for PSX market data — no
    SECP terms page governing PSX prices/registry was located.
    SECP's general website terms were not relied on, because
    they do not create a market-data source.
13. **Redistribution limitations:** UNVERIFIED — no dataset,
    no terms, no licence located. Nothing is authorised.
14. **Known data-quality issues:** Absence is the issue: SECP
    was not verified as a machine-readable registry source in
    Phase 4, and this research's search found no SECP PSX
    list either. Using SECP press-release aggregates (e.g.
    "535 listed securities" in a March 2026 release) as a
    registry would be an aggregate, not a list, and is
    expressly not done here.
15. **Last successful verification (date, method, result):**
    2026-11-04, web search for an SECP PSX listed-companies /
    price list. Result: **negative** — no SECP PSX registry
    or price page was returned. SECP is therefore recorded
    as UNVERIFIED and NOT SELECTED, not as a confirmed
    absence from the whole web (a negative search result is
    not proof of non-existence, and is not presented as one).

### (vi) Any other free source — none qualifies; examined and rejected

**Finding: no additional free source qualifies for selection in
Phase 5.** The candidates below were examined from search
evidence only (no sign-up, no download, no data call) and are
recorded so they are not re-proposed without new evidence. The
full 15-field treatment is given for the closest candidate
(ksestocks.com); the remainder are summarised with the reason
each fails, which is sufficient to reject them without inventing
a source.

#### (vi-a) ksestocks.com — Listed Companies page (NOT SELECTED)

1. Official source name: ksestocks.com (third-party site, not
   PSX, not SECP).
2. Exact URL: https://www.ksestocks.com/ListedCompanies/SortByName
   (search-result URL, verbatim).
3. Source authority: Unofficial third-party. No affiliation
   with PSX is stated in the search evidence.
4. Available document/data types (search evidence only):
   listed-companies table by sector (symbol, company name,
   face value, year end, outstanding shares, registrar).
   No price history is shown in the search evidence.
5. Historical coverage: UNVERIFIED — no price data shown, no
   date stated in the search evidence.
6. Available reporting periods: UNVERIFIED — none stated.
7. Publication frequency: UNVERIFIED — no schedule stated;
   the page text gives no "as of" date in the search evidence.
8. Download or access method: UNVERIFIED — a web table; no
   download file was verified.
9. Direct links available?: The page URL itself is a direct
   link to a table, but no machine-readable dataset link was
   verified. **UNVERIFIED as a dataset source.**
10. Automatic download permitted?: UNVERIFIED — no terms page
    was read for this site, and its underlying data is PSX
    data, so PSX Terms (section 1(i) field 12) would still
    apply to the underlying content. **Not authorised.**
11. Access restrictions: UNVERIFIED — none stated in the
    search evidence.
12. Terms of use: UNVERIFIED — not read. No licence is stated
    in the search evidence.
13. Redistribution limitations: UNVERIFIED, and in any case
    PSX's redistribution rule (section 1(i) field 13) applies
    to the underlying PSX data. Nothing is authorised.
14. Known data-quality issues: undated page (no "as of" date
    in evidence); totals in evidence (544 companies, 36
    sectors) match neither the registry snapshot (470
    securities, 37 sectors) nor PSX's own aggregate (535 + 5
    GEM, 37 sectors) — an unexplained discrepancy, recorded
    not reconciled; registrar-table evidence elsewhere on the
    site still shows delisted-era symbols (e.g. PIAA/PIAB),
    suggesting staleness, which is a warning flag, not a
    proven error rate. A third-party undated table cannot
    serve as the second agreeing source for VERIFIED status.
15. Last successful verification (date, method, result):
    2026-11-04, search-result text only. Result: page exists
    as a web table; **no field, row, or price was verified
    against it, and no data was taken from it.**

#### (vi-b) Other examined, rejected without full 15-field treatment

- **Eulerpool:** evaluated in earlier project research as a
  vendor page with no PSX-specific coverage stated. NOT a
  PSX source; do not present it as one. No sign-up or key
  was taken.
- **psx-terminal (PyPI, mumtazkahn/psx-terminal):** a
  read-only terminal dashboard for PSX realtime feeds (L1,
  MBP, MBO), requiring network access to the PSX feed host.
  Rejected: realtime-feed tool, not a verified daily-OHLCV
  history source; same PSX Terms automated-access problem as
  sections 1(ii)-(iii); no terms/licence for the underlying
  data verified.
- **pypsx-toolkit (PyPI):** claims real-time and historical
  PSX data with "no authentication required". Rejected: no
  README-level evidence was examined beyond the PyPI
  summary, no terms/licence for underlying PSX data verified,
  and it would face the same PSX Terms bar. Naming it here
  is not a selection and not an endorsement.
- **psx-data-reader (PyPI):** self-described scraper of PSX
  data returning DataFrames. Rejected: explicitly a scraper,
  so it is blocked by the same PSX Terms automated-navigation
  rule; no coverage or terms evidence verified.
- **psx-dashboard-MWBK, pypsx / pytrader-sdk, PSX Expert,
  PSX Invest, ksestocks-adjacent dashboards:** either
  scraping dashboards, API-key trading SDKs (paper/live
  trading, outside this project's PKR 0 / no-trade scope),
  or third-party publishers whose methodology pages claim
  DPS-derived EOD data without a PSX licence on file.
  Rejected: none supplies a verified, legally accessible,
  free daily-OHLCV dataset with terms on file. PSX Expert's
  methodology claim (DPS EOD, ~5 years) is noted as a
  third-party claim only and is NOT adopted as evidence,
  because the publisher is not PSX and no PSX licence is
  shown.
- **PSX licensed vendors (Data Services/Vending authorised
  clients, e.g. Capital Stake, investify.pk, FIS):** these
  are licensed redistribution channels, not free sources.
  Rejected for Phase 5 under the PKR 0 rule: any use would
  require a licence/fee arrangement, which is a parent
  commercial decision, not a research assumption. They are
  named here only as the route the parent could explore if
  it ever seeks a licensed feed.

## 2. Intraday — explicitly OUT OF SCOPE

- **psxdata:** README "Data Availability" section (re-read
  2026-11-04): "psxdata supports daily historical OHLCV bars
  and live quote snapshots only. Intraday historical data
  (1-minute, 5-minute, 15-minute bars, etc.) is not available
  because PSX does not publicly expose historical intraday
  data through any official channel — the DPS/KATS feeds only
  provide real-time data, not a historical intraday archive."
  This is a README statement, recorded as such. It is NOT
  upgraded to a verified fact about PSX's internal systems,
  but it is sufficient to keep historical intraday OUT OF
  SCOPE: no source in this research offers a verified
  historical intraday archive.
- **psx-dps:** README claims "Today's full tick series" only
  (section 1(ii) field 6). Today's ticks are not a historical
  intraday archive, and collecting them would require the
  blocked live adapter (section 1(ii) field 10). Today's
  ticks are therefore also OUT OF SCOPE for Phase 5.
- **Conclusion:** intraday is OUT OF SCOPE unless legally
  accessible free intraday is verified in writing. **It is
  not, in this research.** No intraday requirement may be
  marked satisfied, and no intraday series may be
  constructed by polling live quotes (that would be the
  blocked live adapter, and a self-built series is not an
  official intraday archive).

## 3. What the parent must confirm before ANY live collection

The PSX Terms internal-use question remains **UNRESOLVED in
writing**. Before any live collection (as opposed to research
and to ingestion of an already-supplied dated file through an
authorised route), the parent must confirm and record, in
writing, each of the following — a "yes" to one item does not
imply the others:

1. **Internal-use permission:** whether internal use (database
   storage and internal analysis, NOT republication) of DPS
   snapshot/file contents is permitted under PSX Terms of Use
   / Data Vending, and on what basis (PSX written permission,
   a licence, or a documented reading of the Terms). The
   Terms text quoted in section 1(i) field 12 does not
   expressly grant database ingestion, and the single-copy
   personal-use allowance does not, on its face, cover a
   470-security database import. Until this is recorded, every
   registry record stays UNVERIFIED and no new ingestion
   should be presented as licensed.
2. **Automated-access permission (if any live adapter is ever
   wanted):** prior written PSX permission for automated
   navigation / data-route access, naming the method (DPS
   routes, psx-dps, psxdata, or other). Without it, live DPS
   adapters stay BLOCKED (section 4) and must not be built,
   tested against live DPS routes, or run on a schedule.
3. **Authorised file route for prices:** the exact authorised
   route by which dated price files will be supplied (e.g.
   parent live-browser read saved as a dated file, as was
   done for the registry snapshot; or an official DPS
   Downloads file obtained through a generally available
   browser and saved with its date, source URL, and method).
   The DPS Downloads section (sitemap mention, section 1(i)
   field 4) is UNVERIFIED as a price source: its contents
   must be inspected via the live browser and recorded
   (columns, date coverage, board coverage, adjustment
   status) before any file from it is ingested. No file may
   be ingested on the strength of a sitemap mention alone.
4. **Scope confirmation:** KSE-100 membership check against
   the 470-security snapshot before any "KSE-100 first" claim
   is made; GEM (5) and Non-Compliant (93) remain out of the
   registry until their own dated snapshots are supplied
   through the same authorised route; and the price-file
   scope is the 470 snapshot securities only, unless the
   parent extends it in writing.
5. **No-republication boundary:** confirmation that no DPS /
   PSX data ingested under (1)-(3) will be republished,
   exposed via a public API, or distributed to third parties
   without a separate PSX licence — the project's internal
   APIs and frontend are not a republication licence.

## 4. Ingestion-route conclusion (the only implementable route)

**Live DPS adapters are BLOCKED** (D-51/D-52 as technical
history, plus the PSX Terms automated-navigation bar, which is
the deciding reason: even if the technical defects were fixed,
an adapter would still need prior written PSX permission).
**The only implementable ingestion route in Phase 5 is
validated dated files supplied through an authorised route**
(e.g. a parent live-browser read saved as a file, as was done
for the registry snapshot) — never a scraper, never a library
call against live DPS/PSX routes, never a polling loop that
builds its own series. Each such file must carry its date,
source URL, extraction method, board coverage, and column
contract, and must pass the Phase 5 deterministic validation
(OHLC consistency, positive prices, volume/turnover units,
missing never zero, PKT timezone, duplicate/future/session
checks, cross-source comparison with conflicts preserved) and
the Phase 4 verification rule (VERIFIED requires at least two
distinct agreeing sources including one official; a lone
official file stays UNVERIFIED) before any record is promoted
beyond UNVERIFIED. If no suitable dated file is supplied, the
affected requirement is BLOCKED — collection evidence must
never be manufactured.

## 5. Research method and limits

- Bounded method, 2026-11-04: public README/docs page text
  re-reads (psx-dps, psxdata, PSX Terms of Use), web searches
  (SECP list, PSX Terms/Data Vending, other free sources),
  Phase 4 documents re-read, and ONE lightweight reachability
  probe per DPS/PSX host (single HEAD request to the site
  root only — see section 1(i) field 15 and 1(iv) field 15).
- NOT done, by design: no DPS/PSX data route was fetched, no
  scraper was run, no library was installed or called, no
  control was bypassed, no sign-up, payment, or ToS
  acceptance occurred, no external account was created, no
  secret was used or recorded.
- A failed probe would have been recorded as a finding, not
  as a licence to try another route. In the event, both root
  probes returned 200 (section 1(i) field 15, 1(iv) field 15);
  neither closes D-51 or D-52, for the reasons stated there.
- Cost: PKR 0. Paid services introduced: zero.
