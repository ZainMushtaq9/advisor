# PSX Intelligence AI — Phase 1: Data Source Research

**Project:** PSX Intelligence AI, Phase 1 of 30 — Team 2 (Free Data Source Research + Licensing)
**Date of this research:** 2026-11-04
**Scope rule:** Phase 1 is research, validation and specification ONLY. No full-scale live
data collection, no application code beyond tiny illustrative snippets, no Phase 2 work,
no real trades. The system must NOT execute real trades initially; this document is about
data sources for analysis/intelligence, not about order execution.
**Budget rule (revised brief, PKR 0 absolute):** No paid market-data API, financial
subscription, AI/LLM API, database, hosting, storage or monitoring service is assumed,
recommended or budgeted anywhere in this file. Where a free source cannot satisfy a
requirement, the gap is recorded as a limitation — no paid alternative is introduced.
Local hardware, electricity and internet access are EXTERNAL operating expenses of the
user's own environment; they are disclosed here and are never described as "free".
No permanent free hosting is assumed to exist.
**Reference scaffold (never overwritten or touched):**
`~/workspace/psx-data-collection/` — README, DATA_SOURCE_REGISTRY, `psx_collector.py`
(provenance / PKT timestamps / stale / conflict rules), offline tests, `coverage.json`
template. This file is consistent with that scaffold; it does not duplicate its collector code.
**Method:** Web search and page-text fetch ONLY. No sign-ups, installs, purchases,
credentials, API keys, live polling, trading or posting. A text fetch is not a live-browser
visit and does not prove live availability, price or account state.

## How to read the verification column

- **VERIFIED-from-README/portal (reused 2026-11-04, not a new live run here):** the
  starting condition for this task, taken from the scaffold's 2026-11-04 README/portal
  check. Reused verbatim; this team did not re-run it as a new live claim.
- **VERIFIED-by-direct-page-fetch (2026-11-04):** this team fetched the page text itself
  on 2026-11-04 and the page states the fact quoted.
- **PARTIALLY VERIFIED — official document via search snippet:** an official-domain
  document (e.g. an SBP bulletin preface, an IMF terms page, a FRED terms page) was
  returned in search results quoting the fact, but this team did not complete a direct
  full-text fetch of that page in this session. Treat as a lead that still needs a direct
  read before Phase 2 relies on it.
- **PARTIALLY VERIFIED — third-party summary:** a non-official page summarises an
  official API/terms position. Useful for scoping, never sufficient for a licensing or
  rate-limit commitment.
- **UNVERIFIED:** no page fetched or returned in this research states the fact. The
  exact check still needed is written out. Never read UNVERIFIED as "does not exist" —
  it means "not established by this research".

> **Global rule for every source below:** free public viewing, a free tier, an open
> licence, or a free API key is NOT, by itself, a right to resell, republish a live feed,
> or redistribute raw data commercially. See `DATA_LICENSING_POLICY.md`. Never assume
> an undocumented endpoint is stable. Never claim real-time data without verification.

---

## 1. PSX Data Portal — https://dps.psx.com.pk/

| Field | Finding |
|---|---|
| What data it provides | Index levels and market data shown on the portal landing page. Via the libraries below it is the underlying source for quotes, whole-market snapshots, EOD, today's intraday ticks, indices + constituents/weights, sectors and announcements with PDF URLs (those detailed claims belong to the library READMEs, not to a portal API document). |
| Free? | Free to view (scaffold, 2026-11-04 portal landing page). No price was stated on the landing page text reviewed. |
| Official public API? | **No.** PSX publishes no official public API/documentation for these endpoints (per psx-dps FAQ, reused from scaffold). Any JSON endpoint reached through a library is undocumented. |
| Python library? | No official PSX Python library is identified in this research. Access in Phase 2 planning is via the unofficial libraries in §2–§3 only. |
| Authentication | UNVERIFIED for direct portal use. No API key is stated for the portal itself; do not assume keyless programmatic access is permitted — see licensing. |
| Data coverage | Portal landing page showed indices as of 2026-11-04 11:09 AM PKT in the scaffold check (e.g. first index 169,819.93, +1,801.07 / +1.07%); some indices were shown with prior-day timestamps (e.g. one index as of 2026-11-02 6:30 PM). That is a landing-page snapshot, not a coverage census. |
| Historical coverage | UNVERIFIED from the portal itself. Historical EOD/intraday claims are library claims (§2–§3), not portal documentation. |
| Update frequency | Live during market hours per scaffold; off-hours values may be prior-day. Do not call any fetched value "real-time" — record its source timestamp (scaffold rule). |
| Rate limits if documented | UNVERIFIED. No portal rate-limit document was found in this research. Do not invent one. |
| Licensing / commercial-use restrictions | Free to view ≠ redistribution. Redistribution/licensing must be verified with PSX before any commercial use (scaffold). PSX data is PSX's to license. No reselling or republishing a live feed without a PSX agreement. |
| Known limitations | Undocumented endpoints can change without notice; no official documentation to pin behaviour to; landing-page timestamps can lag. |
| Backup alternatives | psxdata (§3) for EOD/live snapshots; SBP/PBS/Finance/World Bank/IMF/FRED (§5–§10) for macro context only — none of them is a PSX market-data backup. |
| Verification status | **VERIFIED-from-README/portal (reused 2026-11-04):** portal exists, shows indices, free to view. **UNVERIFIED:** official API, rate limits, redistribution terms, full coverage. |
| Source URLs | https://dps.psx.com.pk/ ; scaffold `~/workspace/psx-data-collection/DATA_SOURCE_REGISTRY.md` |

## 2. psx-dps (unofficial PSX library) — https://github.com/umairsandhu/psx-dps

| Field | Finding |
|---|---|
| What data it provides | Per its README (reused): live quotes / OHLC / order book, whole-market snapshot in one request, ~5 years EOD per symbol, intraday ticks for today only, indices + constituents with weights, 38 sectors, 224k+ announcements with PDF URLs. |
| Free? | Yes — free library, no API key (README, reused). Cost here means the library/API-key cost, not the user's hardware/electricity/internet, which are external operating expenses. |
| Official public API? | No — it wraps PSX's undocumented portal endpoints. Unofficial and unaffiliated; not endorsed by PSX. |
| Python library? | Yes — `psx-dps` itself. Zero dependencies, MIT licence (README, reused). |
| Authentication | No API key (README, reused). |
| Data coverage | ~496 trading symbols in market watch vs ~1,029 listed instruments claimed (README/scaffold). The gap is a real coverage fact to carry into Phase 2, not a rounding error to ignore. |
| Historical coverage | ~5 years EOD per symbol (claimed); intraday ticks for today only — no historical intraday archive is claimed. |
| Update frequency | Market-aware TTLs claimed: 60 s while trading, cached until next open off-hours (scaffold). Cross-process 1 req/s limit claimed; 429 stops + escalating cooldown (scaffold). These are library-implemented behaviours, not PSX-published limits. |
| Rate limits if documented | No PSX-published limit found. The 1 req/s figure is the library's own throttle, not a PSX document. Do not present it as PSX's limit. |
| Licensing / commercial-use restrictions | Library licence is MIT; that licences the code, NOT the PSX data. The README's "not a licence to redistribute" note is not legal advice (scaffold). PSX data remains PSX's to license. |
| Known limitations | Multi-node 404 quirk: dps.psx.com.pk is served by several nodes and some return 404 for data routes while serving the website; psx-dps keeps a pool of candidate nodes, probes for one that serves data, pins it, and re-probes instead of believing a 404 (README/scaffold). Symbol renames need handling, e.g. ENGRO → ENGROH (scaffold). Endpoints can change without notice, so a fallback is mandatory. |
| Backup alternatives | psxdata (§3) for EOD/snapshots; no backup exists in this research for today's intraday ticks or for the full announcement PDF set. |
| Verification status | **VERIFIED-from-README/portal (reused 2026-11-04).** No new live run was made in this Phase 1 research. |
| Source URLs | https://github.com/umairsandhu/psx-dps ; scaffold README/registry |

## 3. psxdata (unofficial PSX library + separate REST API repo)

| Field | Finding |
|---|---|
| What data it provides | Per its README (reused): historical OHLCV, live quotes, KSE-100 constituents, sector summaries, fundamentals, debt instruments, margin-eligible stocks; all listed tickers (1000+), screener ~729 symbols, 37 sectors. Fundamentals/announcement depth is CLAIMED, not yet proven by a live sample in either scaffold or this research. |
| Free? | Yes — free, PyPI, MIT (README, reused). No paid API is involved. The separate REST API lives in a separate repo, `psxdata-api` (reused). |
| Official public API? | No — unofficial, wrapping PSX portal data. Its own REST API repo is a wrapper, not a PSX official API. |
| Python library? | Yes — `psxdata`, PyPI, Python 3.11+ (README, reused). Alpha 0.1.0a1 — APIs may change before 1.0. |
| Authentication | No API key stated (README, reused). |
| Data coverage | Tickers 1000+ claimed; screener ~729 symbols; 37 sectors (README, reused). The 1000+ vs 729 vs psx-dps ~496 figures measure different universes (listed vs screener vs trading watch) — do not merge them into one "coverage" number. |
| Historical coverage | Daily historical OHLCV only. **Explicit README limit: historical intraday bars are NOT available because PSX does not publicly expose a historical intraday archive.** |
| Update frequency | Historical cached forever, live 15 min (claimed); exponential backoff, 3 attempts (scaffold). |
| Rate limits if documented | UNVERIFIED as a PSX-published limit. Backoff behaviour is library behaviour. |
| Licensing / commercial-use restrictions | Library licence MIT; PSX data itself is PSX's to license. Same redistribution bar as §1–§2. |
| Known limitations | Alpha status; daily-only history; fundamentals format/depth unverified; sector count (37) differs from psx-dps (38) — the two libraries do not agree on sector taxonomy, so Phase 2 must not silently merge sector labels. |
| Backup alternatives | psx-dps (§2) is the primary-market counterpart; each library backs up the other for EOD/snapshots only. Neither backs up historical intraday. |
| Verification status | **VERIFIED-from-README/portal (reused 2026-11-04).** Fundamentals depth, debt/margin coverage and live behaviour remain UNVERIFIED by a live sample. |
| Source URLs | https://github.com/psxdata/psxdata ; separate REST API repo `psxdata-api` (name as given in scaffold; its URL was not re-fetched here) |

## 4. SECP — Securities and Exchange Commission of Pakistan — https://www.secp.gov.pk/

| Field | Finding |
|---|---|
| What data it provides | Corporate regulator: company registration/incorporation, compliance, licensed entities, regulations. This research establishes a company-registry / regulatory-information role, NOT a PSX price, fundamentals-feed or filings-API role. No page found here states that SECP publishes listed-company financial statements in machine-readable form for PSX Intelligence AI. |
| Free? | Basic public company-name search is described in third-party guides as free without an account; certified true copies carry a fee (third-party guides; see below). SECP's own Terms page (direct fetch, § Licensing) does not state a price list. Do not quote a fee figure from this research — the Rs 600/page figure in one third-party article is NOT adopted here because it was not confirmed on an SECP page. |
| Official public API? | **No documented, stable public API found.** A third-party skill summary states the eServices company search is "an HTML web search form, not a formal published API" with "no documented, stable programmatic endpoint". That is a third-party characterisation, but it is consistent with the absence of any API document found on secp.gov.pk in this research. Status: UNVERIFIED as an official statement; no API is to be assumed. |
| Python library? | None identified (official or established third-party) in this research. UNVERIFIED / none found — do not invent one. |
| Authentication | Public name search: no account described as needed (third-party guides). Detailed company information / certified copies: eServices account and a document request are described as needed (third-party guides). The current filing system is eZfile, replacing eServices for filings (SECP homepage fetch 2026-11-04 lists "eZfile" and eZfile user manuals; a 2025 third-party article describes eZfile as the replacement system). Whether eZfile exposes any public search, and on what terms, is UNVERIFIED — the homepage fetch returned only link labels, not a data-access statement. |
| Data coverage | Company registry scope (all registered company types) per third-party guides; listed-company-specific coverage, PSX-ticker mapping and filing-type coverage are UNVERIFIED. SECP data is NOT a substitute for PSX announcements/financials. |
| Historical coverage | UNVERIFIED. No retention/history statement was found on an SECP page in this research. |
| Update frequency | UNVERIFIED from an SECP page. A third-party claim of "real-time" registry updates is NOT adopted — do not repeat it as verified. |
| Rate limits if documented | UNVERIFIED. None found. A 2022 Business Recorder item records SECP restricting XML tags after unauthorised scraping and pursuing legal recourse — a warning against scraping, not a rate-limit document. Do not scrape SECP. |
| Licensing / commercial-use restrictions | **Direct page fetch, 2026-11-04, https://www.secp.gov.pk/terms-of-use/:** website material is SECP property, protected by IP law; permission is granted to residents/citizens of Pakistan to copy electronically and print single pages of SECP copyright material without deletion/addition/modification "for the sole purpose of sharing information with other citizens and residents without cost to them"; that permission does NOT extend to material copyrighted by another party; hyperlinking/framing SECP contents requires prior SECP permission; SECP reserves the right to deny/restrict access without reasons; site information is "for general information only" and users are advised to verify contents independently against the official record at SECP offices; no warranty of accuracy/completeness. That is a narrow, non-commercial, unmodified single-page sharing permission — it is NOT a redistribution, resale or bulk-reuse licence, and it does NOT cover company filings owned by the companies themselves. |
| Known limitations | Registry ≠ market data; detailed filings behind account/fee/request; eZfile transition means older eServices guidance may be stale; scraping history shows access can be restricted; per-company filing formats (if any are public) are UNVERIFIED. |
| Backup alternatives | PSX announcements (via §2) for listed-company disclosures; listed-company investor-relations sites (per-company, UNVERIFIED in this research). Neither is an SECP backup in the API sense. |
| Verification status | **VERIFIED-by-direct-page-fetch:** homepage shows eZfile; Terms of Use as quoted above. **PARTIALLY VERIFIED — third-party:** free public name search, eServices account for detail, eZfile replacing eServices, no stable API. **UNVERIFIED:** any SECP API endpoint, rate limit, fee schedule, filing-format/API coverage, PSX-ticker mapping, history/retention, commercial redistribution terms. |
| Source URLs | https://www.secp.gov.pk/ ; https://www.secp.gov.pk/terms-of-use/ ; https://eservices.secp.gov.pk (as cited in third-party guides; not fetched as a data source here) |

## 5. SBP — State Bank of Pakistan — https://www.sbp.org.pk/

| Field | Finding |
|---|---|
| What data it provides | Central-bank statistics: Monthly Statistical Bulletin (MSB), monetary/banking/economic time series, and the EasyData portal (easydata.sbp.org.pk) with dashboards including workers' remittances, Inflation Snapshot, Financial Statement Analysis and Pakistan's Economic Interaction with Other Countries (SBP bulletin preface, official SBP document via search). Policy rates / monetary-policy decisions are the expected use, but no single "policy rate series" was verified as a named, machine-readable series in this research. |
| Free? | No price or paywall was stated in the SBP material returned. "Free to access" is NOT asserted as a verified SBP statement — access cost is UNVERIFIED as a formal term; the portal is publicly presented, which is weaker than a stated free licence. Do not quote SBP as "free" without that caveat in Phase 2. |
| Official public API? | **Partially established, endpoint UNVERIFIED.** SBP's own bulletin preface (multiple editions via search) states: "Recently, we have upgraded the EasyData and introduced new features including … a new API to retrieve a complete dataset." No endpoint URL, method, format, auth or documentation page was returned in this research. Do NOT invent an EasyData endpoint. |
| Python library? | None identified (official or established third-party) in this research. UNVERIFIED / none found. |
| Authentication | UNVERIFIED. No auth statement for EasyData or its API was found. |
| Data coverage | Variable counts in successive SBP prefaces grow over time (8,000+ → 11,000+ → 14,000+ → 18,000+ variables in the editions returned). The latest edition returned states "more than eighteen thousand variables". Do not cite a single count without its edition date; the count is edition-dependent and this research did not fetch the current live EasyData catalogue. Dashboards named above are the only dashboard list verified from a preface. |
| Historical coverage | UNVERIFIED as a stated span. The MSB is a monthly bulletin; EasyData is a time-series portal — neither yielded a verified start-date or revision policy in this research. |
| Update frequency | UNVERIFIED as a stated schedule. Monthly bulletin cadence is implied by its name, not verified as a machine-readable update guarantee. EasyData update timing is UNVERIFIED. |
| Rate limits if documented | UNVERIFIED. None found for SBP/EasyData. Third-party rate figures found for unrelated APIs in the same searches are NOT SBP limits and are deliberately not reproduced here. |
| Licensing / commercial-use restrictions | UNVERIFIED. No SBP terms/licence page was fetched or returned in this research. Do not assume public statistics = commercial redistribution rights. Attribution to SBP is good practice but is NOT stated here as a verified SBP licence term. |
| Known limitations | API existence is stated but its interface is not documented in the material found; MSB tables are also published in MS Excel format (older preface) — format per dataset is UNVERIFIED for the current edition; SBP series are macro/banking context only, never PSX prices; SBP republishes some PBS data (its preface says much MSB data is also on producers' sites) — provenance must record SBP vs PBS as the originator per series. |
| Backup alternatives | PBS (§6) for CPI; World Bank/IMF (§8–§9) for annual macro series; Finance Division (§7) for fiscal context. None backs up SBP banking/monetary series specifically. |
| Verification status | **PARTIALLY VERIFIED — official SBP preface via search snippet:** EasyData exists, 18,000+ variables (latest edition returned), dashboards named, new API to retrieve a complete dataset, MSB in Excel (older edition). **UNVERIFIED:** EasyData API endpoint/format/auth/rate limit, cost/licence terms, coverage span, update schedule, policy-rate series identity. A direct fetch of https://www.sbp.org.pk/ and https://www.pbs.gov.pk/ failed in this session with a fetch error (not a finding about those sites); that failure is recorded, not treated as proof the sites are down. |
| Source URLs | https://www.sbp.org.pk/ ; https://easydata.sbp.org.pk (as cited in SBP prefaces; interface not verified) ; SBP Monthly Statistical Bulletin prefaces via https://www.sbp.org.pk/reports/stat_reviews/Bulletin/index.htm (as cited in prefaces) |

## 6. PBS — Pakistan Bureau of Statistics — https://www.pbs.gov.pk/

| Field | Finding |
|---|---|
| What data it provides | National statistics: monthly CPI (national/urban/rural), WPI, core inflation, weekly SPI, trade, population and other surveys/indices. CPI is the headline monthly inflation figure (third-party explainers consistent with PBS releases). The PBS homepage snippet returned in search shows "Monthly Consumer Price Index — For the Month Ended on Oct 2026, 1.1%" and "Weekly Sensitive Price Index (SPI) … -0.35%", confirming the homepage surfaces current CPI/SPI headlines, but headline text is not a dataset. |
| Free? | Standard products: a PBS Data Dissemination Policy document (via pbs.gov.pk in search) states Tier 1/2 products, Public Use Files and ordinary downloads "stay free at point of use", with nominal charges only for exceptional customised tabulations / resource-intensive processing / physical or secure-environment services. That is a policy-document statement via search snippet, not a direct fetch — PARTIALLY VERIFIED. Customised data prices quoted in that policy (e.g. per-dataset rupee figures) are deliberately NOT reproduced here because they were not directly verified and are not needed for Phase 1 macro use. |
| Official public API? | **UNVERIFIED as a usable endpoint.** The same policy document's scope says it "applies to PBS-produced censuses, surveys, indices, dashboards, APIs, metadata and microdata services" and Tier 1 includes "non-confidential APIs" — i.e. PBS contemplates APIs — but no PBS API endpoint, documentation URL, format or key was found in this research. Do NOT invent a PBS API. The practical Phase 1 route evidenced is publication download (Monthly Review on Price Indices PDF; historical indices spreadsheet found on the older pbos.gov.pk domain), not an API. |
| Python library? | None identified. UNVERIFIED / none found. |
| Authentication | UNVERIFIED. No PBS API auth statement found. Publication downloads are presented publicly; microdata tiers 3–4 require application/endorsement/NDA or are non-disseminable (policy document) — those tiers are out of scope for this project and must not be pursued. |
| Data coverage | CPI: monthly, national + urban + rural, base 2015-16 = 100 (third-party explainers + PBS price-statistics page snippet: monthly prices from 68 urban markets of 35 cities and 27 rural centres; HIES 2015-16 weights, ~26,000 households). SPI: weekly, 51 essential items, 50 markets, 17 cities (third-party explainer). These collection details are third-party/PBS-page snippets, not a directly fetched PBS methodology page — PARTIALLY VERIFIED. Full PBS catalogue (trade, labour, census, LSM, etc.) is UNVERIFIED per dataset. |
| Historical coverage | A historical indices spreadsheet was found (pbos.gov.pk, base 2015-16 and old base 2007-08, monthly rows from 2016-17 onward in the snippet). That proves at least one historical file exists; it does NOT prove a complete, current, machine-readable history for every PBS series. Per-series history is UNVERIFIED. |
| Update frequency | CPI monthly (usually first working day of next month, per third-party explainer); SPI weekly (usually Friday for week ending Thursday, per third-party explainer). Both are explainer statements, not PBS release-calendar statements fetched directly — PARTIALLY VERIFIED. Do not hard-code a release time. |
| Rate limits if documented | UNVERIFIED. None found. |
| Licensing / commercial-use restrictions | **PARTIALLY VERIFIED — PBS policy document via search:** policy adopts "open by default, confidential by design and equal access"; "Aggregate statistics, publications, anonymized microdata … metadata and non-confidential datasets shall normally be released free of charge under an open license, in accessible human-readable and machine-readable formats"; "Tier 1/2 products and Public Use Files carry a standard open government licence permitting copying, adaptation and commercial/non-commercial reuse with attribution." That is the most permissive macro-source licence signal in this research — but it is a policy document via snippet, the exact licence text was not directly fetched, and microdata tiers 3–4 are restricted. Phase 2 must fetch the licence text and record the per-dataset tier before any reuse, and must attribute PBS on every reuse. It does NOT license PSX data and does NOT license identifiable microdata. |
| Known limitations | Publication-first, not API-first: CPI/SPI arrive as monthly/weekly PDF reviews (table extraction + vintage control needed); policy is a framework document, not a per-dataset licence; PBS homepage fetch failed in this session (fetch error, not a site finding); older pbos.gov.pk files may be superseded — always prefer the current pbs.gov.pk release. |
| Backup alternatives | SBP EasyData/MSB republishes PBS CPI (SBP preface + SBP bulletin CPI tables sourced to PBS); World Bank/IMF for annual CPI (lagged, modelled). Neither is a same-week SPI backup. |
| Verification status | **PARTIALLY VERIFIED — PBS policy/homepage/price-statistics snippets via search:** CPI/SPI existence and cadence, open-by-default policy, Tier 1 open-licence-with-attribution signal, standard products free at point of use. **UNVERIFIED:** any PBS API endpoint/docs/auth/rate limit, exact licence text, per-dataset tier, complete historical coverage, release calendar. |
| Source URLs | https://www.pbs.gov.pk/ ; https://www.pbs.gov.pk/price-statistics/ ; https://www.pbs.gov.pk/data-dissemination/ (policy document, via search) ; https://www.pbs.gov.pk/page/8/ (homepage snippet via search) |

## 7. Finance Division, Government of Pakistan — https://www.finance.gov.pk/

| Field | Finding |
|---|---|
| What data it provides | Fiscal/economic publications: Pakistan Economic Survey (annual, chapter PDFs — e.g. Chapter 4 Fiscal Development, Chapter 11 Health and Nutrition, for 2024-25 and 2025-26 editions found via search), Monthly Economic Update & Outlook (Economic Adviser's Wing, e.g. March, May and October 2026 editions found via search, with an Economic Indicators table dated to the month-end). Also budget/fiscal operations, debt reviews, borrowing plans and SOE reports are listed on the homepage news list (direct fetch 2026-11-04). This is fiscal narrative + summary tables, not a series database. |
| Free? | No price/paywall stated on the homepage text fetched. Formal cost/licence terms are UNVERIFIED — do not assert "free" as a Finance Division term. |
| Official public API? | **None found. UNVERIFIED / no API evidenced.** All material found is PDF publication. Do not assume an API exists. |
| Python library? | None identified. UNVERIFIED / none found. |
| Authentication | No login is evidenced for publication downloads. Formal access terms are UNVERIFIED. |
| Data coverage | Survey chapters cover fiscal, agriculture, industry, trade, health, education and other sectors per edition; the Monthly Update covers remittances, exports/imports, current account, FDI, reserves, exchange rate (sourced to SBP in the October 2026 edition snippet), fiscal operations and CPI (sourced to PBS in the same snippet). Coverage is therefore largely SECONDARY for macro indicators — provenance must cite SBP/PBS/IMF as originators where the Update itself does, not Finance Division as the originator. |
| Historical coverage | Survey editions back to at least 2017-18 were found in search (chapter PDFs). A complete, machine-readable fiscal history is UNVERIFIED; chapter PDFs are annual vintages with provisional (P) / budget-estimate (B.E.) flags that Phase 2 must preserve, not overwrite. |
| Update frequency | Monthly Update is monthly by name and by editions found (March/May/October 2026); Survey is annual by name. Exact release dates are UNVERIFIED. |
| Rate limits if documented | UNVERIFIED. None found. |
| Licensing / commercial-use restrictions | UNVERIFIED. No Finance Division terms/licence page was fetched or returned. Government publication ≠ commercial redistribution right. Attribute Finance Division + the originator series source on any reuse, and verify terms before any commercial use. |
| Known limitations | PDF-only in all material found: table extraction, vintage (P/B.E./revised) handling and secondary-source provenance are mandatory work; no API; no stated licence; monthly indicators duplicate SBP/PBS/IMF series with a lag and possible revision differences — never silently merge Finance Division figures with originator figures. |
| Backup alternatives | SBP (§5) and PBS (§6) as originators for the same indicators; IMF/World Bank (§8–§9) for cross-checked annual fiscal/external series. |
| Verification status | **VERIFIED-by-direct-page-fetch (2026-11-04):** homepage exists, lists Monthly Economic Update & Outlook October 2026 (29-10-2026) and other fiscal publications. **PARTIALLY VERIFIED — publication PDFs via search:** Survey chapters and Monthly Updates with the indicator coverage above. **UNVERIFIED:** any API, licence/cost terms, release calendar, machine-readable series. |
| Source URLs | https://www.finance.gov.pk/ ; https://www.finance.gov.pk/economic/Monthly_Economic_Update_and_Outlook_October_2026.pdf ; https://finance.gov.pk/survey/chapter_26/4_Fiscal Development.pdf (as returned in search; case-sensitive path as returned) |

## 8. World Bank — Open Data / World Development Indicators — https://data.worldbank.org/

| Field | Finding |
|---|---|
| What data it provides | Global development indicators: GDP, population, trade, FDI, debt, education, health, gender, governance and more, for 200+ economies. Pakistan series are annual macro context (e.g. GDP, CPI inflation FP.CPI.TOTL.ZG, population SP.POP.TOTL in third-party examples) — NOT PSX prices, NOT Pakistani monthly CPI, NOT a substitute for SBP/PBS. |
| Free? | Yes — homepage fetched 2026-11-04 states "Free and open access to global development data". No key, no tier, no price is stated for the Indicators API in the material reviewed. |
| Official public API? | Yes — World Bank Indicators API v2 (e.g. `https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json` as cited in multiple independent summaries; default format is XML, `format=json` is required for JSON). Version 1 was retired November 2018 per a third-party summary — do not use v1. A separate Data360 API also exists (data360.worldbank.org) with its own terms; it is NOT the same as the Indicators API and is not adopted here. |
| Python library? | No official World Bank Python library is named in the API documentation summaries reviewed. Third-party libraries in common use: `wbgapi`, `wbdata`, `world_bank_data` (third-party summaries). Any of them is a third-party dependency, not a World Bank product — Phase 2 must pin a version and record that fact. Tiny illustrative use (not application code): `wbgapi`'s `wb.data.DataFrame('NY.GDP.MKTP.CD', …)` pattern is cited in third-party summaries only. |
| Authentication | None required — no key, no account, no signup for the Indicators API (multiple independent summaries + homepage "free and open"). No documented rate limit was found in the documentation summaries; "no limit" is NOT claimed — treat as UNVERIFIED / unstated, be gentle with concurrency, cache, and paginate (`per_page`, `page`, `date`, `mrv` parameters are cited in third-party summaries, not verified against official docs here). |
| Data coverage | ~16,000 indicators (documentation summaries vary: 14,000–16,000+ indicators, 200+ economies, 217 economies in some summaries, 29,544 indicator codes across 71 databases in one summary counting all databases). Do NOT cite a single indicator count as verified — counts depend on whether WDI alone or all databases are counted. Pakistan coverage is annual for most macro series. |
| Historical coverage | Many series back to 1960 (summaries); pre-1990 and low-income-country coverage is patchy and many values are World Bank estimates/modelled rather than nationally reported (third-party caveats). Record estimate-vs-reported status per series where the API metadata states it; never present a modelled value as a PBS/SBP reported value. |
| Update frequency | Quarterly release cycle for revisions is cited in one third-party summary (full-refresh behaviour); official update cadence is UNVERIFIED in this research. Annual series are lagged by construction — never present World Bank annual CPI/GDP as current-month Pakistani inflation or growth. |
| Rate limits if documented | UNVERIFIED / none stated in the documentation summaries reviewed. Do not invent a limit and do not claim "unlimited". |
| Licensing / commercial-use restrictions | **PARTIALLY VERIFIED — World Bank sources via search:** World Bank blog (2018, updated 2024) states open datasets use CC BY 4.0 — "anybody is free to share and use our open datasets, as long as they credit it appropriately"; Data360 About page states datasets are "unless specifically labeled otherwise" under CC BY 4.0 with additional terms, and that some third-party datasets "may not be redistributed or reused without the consent of the original data provider, or may be subject to terms … different from those described above"; Data Catalog FAQ states each dataset is tagged with its terms, not all datasets are WBG-owned, and some have restricted access. So: CC BY 4.0 is the DEFAULT for World Bank-produced open data (including commercial reuse with attribution), but per-dataset licence tags override the default. Phase 2 must check the licence tag of every indicator/database used, attribute World Bank + data provider, and never imply World Bank endorsement. |
| Known limitations | Annual/lagged; modelled/estimated values; per-dataset licence exceptions; Data360 migration (open-data site "expanding to Data360" per homepage fetch) means URLs/docs may move — pin the Indicators API v2 actually used. |
| Backup alternatives | IMF (§9) for WEO growth/inflation/fiscal (different vintage/method — never merge silently); SBP/PBS (§5–§6) as national originators (preferred for Pakistan-specific values). |
| Verification status | **VERIFIED-by-direct-page-fetch:** homepage "Free and open access to global development data", Data360 expansion note. **PARTIALLY VERIFIED — World Bank blog/Data360/FAQ + independent summaries via search:** Indicators API v2, keyless, JSON via `format=json`, CC BY 4.0 default with third-party exceptions, annual back-to-1960 coverage. **UNVERIFIED:** official API documentation text itself, any rate limit, exact indicator count, update cadence, per-indicator licence tags. |
| Source URLs | https://data.worldbank.org/ ; https://api.worldbank.org/v2/ (base as cited in summaries) ; https://blogs.worldbank.org/en/opendata/5-reasons-check-out-world-bank-s-new-data-catalog ; https://data360.worldbank.org/en/about ; https://datacatalog.worldbank.org/faq |

## 9. IMF — International Monetary Fund — https://www.imf.org/en/Data

| Field | Finding |
|---|---|
| What data it provides | Global macro/fiscal/external statistics: World Economic Outlook (WEO — growth, inflation, fiscal balance, current account, government debt, projections), International Financial Statistics (IFS), Balance of Payments (BOP), Direction of Trade (DOT), Government Finance Statistics (GFS), commodity prices and others (IMF terms page + third-party API evaluations via search). Pakistan values are annual/semi-annual macro context — NOT PSX prices, NOT monthly Pakistani CPI. |
| Free? | Data access is presented as free/public in third-party evaluations; the IMF terms page itself (via search) frames a "policy of free access and free reuse of IMF Data". No price is stated. Formal "free" as a commercial-use term is NOT established — see Licensing, which requires permission for commercial reuse. |
| Official public API? | Yes, in two forms whose auth differs — do not conflate them: (a) IMF DataMapper API (WEO indicators, JSON, e.g. `https://www.imf.org/external/datamapper/api/v1/…` as cited in third-party guides); (b) IMF SDMX API (`api.imf.org/external/sdmx/…`, SDMX 2.1/3.0, and the Azure API Management developer portal `portal.api.imf.org` for browsing/managing subscription keys, per a third-party evaluation). Whether a subscription key is required for a given SDMX route, and the portal terms behind its sign-in wall, are UNVERIFIED in this research. Secondary sources conflict (some say DataMapper needs no auth, some say an IMF API key is required in general) — Phase 2 must test the exact route it intends to use and record the result. |
| Python library? | No official IMF Python library is established in this research. Third-party libraries cited: `imfpy` (MIT, Direction of Trade focus in its own description), `imfdatapy` (Apache-2.0), `imfp` (older, SDMX/JSON). All are third-party; none is adopted here as verified. One third-party `imfp` page claims an application-based limit of 50 requests/second identified by user-agent — that is a third-party package claim, NOT an IMF-published limit, and is deliberately NOT adopted as an IMF rate limit. |
| Authentication | UNVERIFIED / route-dependent (see above). Do not state "no auth" as a blanket IMF fact. |
| Data coverage | WEO: 190+ economies (third-party evaluations); SDMX dataflows: 222 dataflows claimed in one third-party evaluation (anonymous). Neither count was verified against an IMF catalogue in this research — record as third-party counts, not IMF-verified counts. |
| Historical coverage | WEO history + projections (projections to ~2029 in one evaluation); dated WEO vintages exist via SDMX (third-party evaluation). Exact span per indicator is UNVERIFIED. WEO is published twice a year (April/October per one evaluation) — that cadence is third-party, not verified against an IMF release calendar here. |
| Update frequency | UNVERIFIED as an IMF-stated schedule in this research. Twice-yearly WEO cadence is third-party only. |
| Rate limits if documented | UNVERIFIED as an IMF-published limit. No IMF rate-limit document was found. The 50 req/s figure above is NOT an IMF limit. |
| Licensing / commercial-use restrictions | **PARTIALLY VERIFIED — IMF Copyright and Usage page via search (https://www.imf.org/en/About/copyright-and-terms, effective 2024-10-11 per third-party excerpts):** for statistical "Data" (IFS, BOP, DOT, GFS and other IMF-produced/curated published statistics), users "may download, extract, copy, create derivative works, publish, distribute, and use Data obtained from IMF Sites" subject to conditions including: accurate reproduction with attribution in the form "Source: International Monetary Fund, Database Name, <link>"; no act altering data integrity, with material transformation stated explicitly; users who make IMF Data available to others through any distribution/download environment must take reasonable efforts to communicate/promote compliance by their users; if IMF Data is sold as a standalone product, sellers must inform purchasers it is available free from the IMF; data is "as is" without warranty; free access/reuse does NOT imply a right to confidential/unpublished data. **Critical commercial-use condition:** "For any potential commercial reuse of IMF Data, please email copyright@imf.org to request permission." The 2020 terms' "and sell" wording is reported as dropped in current terms — do NOT claim a general right to sell IMF data. General (non-Data) IMF Content is stricter: free non-systematic downloading/printing for personal, noncommercial use only, without resale/redistribution/derivative rights; systematic copying or substantial reuse beyond fair use needs written permission (via Copyright Clearance Center or copyright@imf.org). Phase 2 must therefore (i) confirm the current terms text by direct fetch, (ii) seek IMF permission before ANY commercial reuse, and (iii) treat IMF data as macro-only, attributed, non-standalone-sale data until that permission is in hand. |
| Known limitations | Two APIs with different auth/docs; portal terms behind sign-in; SDMX complexity (dataflow/dimension discovery required); WEO vintages revise — record vintage/edition per pull; one third-party evaluation reports the DataMapper country path filter being silently ignored in its test (full country matrix returned regardless) — a parsing/validation warning, not an IMF admission. |
| Backup alternatives | World Bank (§8) for annual macro (different method/vintage); SBP/PBS (§5–§6) as national originators. |
| Verification status | **PARTIALLY VERIFIED — IMF terms page + third-party API evaluations via search:** DataMapper + SDMX existence, Data-use permissions/attribution/commercial-permission condition as quoted above. **UNVERIFIED:** direct full-text fetch of current terms, SDMX/DataMapper auth per route, rate limits, indicator/dataflow counts, release cadence, per-database coverage. |
| Source URLs | https://www.imf.org/en/Data ; https://www.imf.org/en/About/copyright-and-terms ; https://www.imf.org/external/datamapper/api/v1 (as cited in third-party guides) ; https://data.imf.org |

## 10. FRED — Federal Reserve Economic Data, Federal Reserve Bank of St. Louis — https://fred.stlouisfed.org/

| Field | Finding |
|---|---|
| What data it provides | US and international macro/financial time series (output, prices, rates, spreads, Treasury yields, employment, recession indicators, etc.). For PSX Intelligence AI the only defensible use is US/global macro context (e.g. US rates, US CPI, oil/commodity-adjacent series where FRED is the republisher) — FRED is NOT a Pakistan source and NOT a PSX source, and it republishes many series it does not own. |
| Free? | API access is free (no paid subscription stated); a free account + free API key are required (see Authentication). "Free" does NOT override the use prohibitions below. |
| Official public API? | Yes — FRED API, REST, at `https://api.stlouisfed.org/fred/` (third-party API summaries; endpoints cited: `series`, `series/observations`, `series/search`, `category`, `releases`, `sources`). Default format XML; `file_type=json` required for JSON; missing observations return the literal `"."` string in one summary — parse explicitly, do not assume null. |
| Python library? | No official (St. Louis Fed) Python library is identified in the summaries reviewed. Third-party libraries in common use: `fredapi` (PyPI), `pandas-datareader` (third-party summaries). Both are third-party, not Fed products. A no-key CSV fallback (`fredgraph.csv?id=…`) is described in one third-party guide — that fallback is NOT adopted here as a sanctioned route, because it bypasses the API-key terms; Phase 2 must not use it to evade key/terms requirements. |
| Authentication | Free API key required, passed as the `api_key` URL parameter; key obtained via a free FRED account (multiple summaries + FRED API Terms page via search: "In order to use the FRED® API, you must have register[ed] for an API Key"). A distinct key per application is advised in one summary. No API key has been obtained in Phase 1 (no sign-up permitted by the task method) — Phase 2 needs a key decision before any FRED call. |
| Data coverage | ~800,000–851,100 series from 100+ sources (third-party summaries vary; do not cite a single count as verified). Coverage is overwhelmingly US; Pakistan-specific series, if any, are republished/secondary and must be traced to their originator. |
| Historical coverage | Per-series; varies widely (one summary warns a popular S&P 500 series is price-only and only ~10 years deep). Per-series history is UNVERIFIED until the series metadata is read. ALFRED vintages exist for point-in-time values — latest-vintage vs vintage choice must be recorded per use. |
| Update frequency | Per-series release calendar (releases/dates endpoints cited). No single FRED freshness guarantee exists. Revisions are routine — record vintage. |
| Rate limits if documented | **Reported, not in Terms:** multiple independent summaries state 120 requests/minute with HTTP 429 on excess and possible temporary block for non-compliance, while noting the figure "appears nowhere in the Terms of Use, which reserve the right to impose or adjust limits at any time". Status: PARTIALLY VERIFIED as a reported current setting, UNVERIFIED as a contractual limit. Phase 2 must throttle well below 120/min, cache, and treat 429 as a hard stop (per project rules). |
| Licensing / commercial-use restrictions | **PARTIALLY VERIFIED — FRED Services Terms of Use + API Terms + 2024 Terms update notice via search (https://fred.stlouisfed.org/legal/ , https://fred.stlouisfed.org/docs/api/terms_of_use.html):** (1) FRED services are provided "for non-commercial, educational, and personal uses subject to a few prohibitions" (summarised Terms). (2) API applications MUST prominently display: "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis." (3) Must NOT suggest Fed/FRED endorsement, replicate/replace the essential FRED/ALFRED user experience, or pass FRED off as your own product/service. (4) Series with a copyright notice are owned by third parties: "Before using data with a copyright notice for anything other than your own personal use, you must contact the data owner to obtain permission" — the St. Louis Fed cannot grant that permission. (5) **AI blocker — read before ANY Phase 2 FRED use:** the June 2024 Terms update notice (via search) lists prohibitions on using FRED Services/Content "in connection with the development or training of any software program or system or machine learning, including … large language models, deep learning, generative artificial intelligence", and on "storing, caching, or archiving" FRED content or providing stored/cached/archived content to a third party, or incorporating it in a database/compilation/archive/cache, and on wholesale downloading in violation of the Terms. If that update text is current, it is architecturally incompatible with an AI product that trains on, caches, or redistributes FRED series. **Therefore FRED is classified in this Phase 1 as MACRO-ONLY, ON-HOLD for any AI use — no FRED series is approved for model training, cached redistribution, or commercial PSX Intelligence AI output until the full current Terms are fetched directly and a written legal/permission check clears the specific use.** This is the single most important FRED finding in this file; do not soften it. |
| Known limitations | US-centric; third-party copyright per series; AI/ML + caching prohibitions (above); key required (Phase 1 has none); no official Python client; revision/vintage complexity; XML default. |
| Backup alternatives | World Bank/IMF (§8–§9) for annual global macro (with their own licence checks); SBP/PBS for Pakistan macro. None is a like-for-like FRED replacement for daily US series, and that gap is recorded as a limitation under the PKR 0 rule — no paid substitute is introduced. |
| Verification status | **PARTIALLY VERIFIED — FRED legal/API-terms pages + independent API summaries via search:** free key, `api_key` parameter, JSON via `file_type=json`, 120/min reported setting, mandatory non-endorsement notice, third-party-copyright rule, non-commercial framing, AI/caching prohibitions in the 2024 update notice. **UNVERIFIED:** direct full-text fetch of current Terms, any contractual rate limit, per-series copyright status, Pakistan-series availability, current AI-prohibition scope (needs direct re-read before any use). |
| Source URLs | https://fred.stlouisfed.org/ ; https://fred.stlouisfed.org/docs/api/ ; https://fred.stlouisfed.org/legal/ ; https://fred.stlouisfed.org/docs/api/terms_of_use.html |

---

## What was deliberately NOT claimed

- No PSX, SECP, SBP, PBS or Finance Division API endpoint, rate limit, price or licence
  is stated where this research did not find it on a page. "UNVERIFIED" above is the claim.
- No FRED, World Bank or IMF indicator count is presented as exact — counts vary by
  counting method across sources and none was verified against a live catalogue here.
- No fee figure (SECP certified copies, PBS custom tabulations, SBP services) is quoted,
  because no fee schedule was directly verified on an official page in this research.
- No real-time, live, intraday-history, fundamentals-depth or full-market-coverage claim
  is made beyond the README/portal statements reused from the scaffold.
- Eulerpool is not treated as a PSX source anywhere in this file (see Comparison file).
- No paid alternative is offered for any gap. Gaps stay gaps under PKR 0.
- No trade execution is in scope. Nothing in this file authorises, describes or assumes
  real order placement, broker connectivity or live trading.

## Phase 2 hand-off (specification only, not execution)

Phase 2 must, per source, complete the UNVERIFIED checks listed in
`DATA_SOURCE_VALIDATION_MATRIX.md` before relying on that source, record the result
with a dated evidence URL, and only then wire the source into any collector. Until then,
the only sources with a documented machine-readable route are psx-dps/psxdata (PSX),
World Bank Indicators API v2 (macro, per-dataset licence check) and IMF DataMapper/SDMX
(macro, commercial-permission check) — and FRED remains on hold for AI use.
