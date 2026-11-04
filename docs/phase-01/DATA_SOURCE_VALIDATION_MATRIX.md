# PSX Intelligence AI — Phase 1: Data Source Validation Matrix

**Purpose:** One row per claim that Phase 2 might rely on. Each row states the claim,
the evidence/URL behind it, how it was verified, its status, and the exact check that
remains. This is the Phase 2 gate list: a source (or a specific use of a source) is
not wired into any collector until its UNVERIFIED rows for that use are cleared and
re-dated here.
**Method (Phase 1):** Web search + page-text fetch only. No sign-ups, installs,
purchases, credentials, API keys, live polling, trading or posting. No full-scale live
data collection was done in Phase 1 (data inspection, where it happens in Phase 2,
is read-only).
**Budget:** PKR 0 absolute. No row assumes or requires a paid service. Local hardware,
electricity and internet are external operating expenses, never called free.
**No real trades:** Nothing in this matrix authorises trade execution; the system must
NOT execute real trades initially.
**Status key:**
- **VERIFIED** — page/primary document fetched or reused from the scaffold's
  2026-11-04 check and stating the claim. (Reused scaffold rows are marked as such;
  they were not re-run live in this research.)
- **PARTIALLY VERIFIED** — official document or terms page quoted via search snippet,
  or a third-party summary consistent with official material, but no direct full-text
  fetch completed in this session. Needs a direct re-read before reliance.
- **UNVERIFIED** — no page in this research states the claim. The "Check remains"
  column is the exact next step. UNVERIFIED ≠ false; it means not established.

## 1. PSX Data Portal — https://dps.psx.com.pk/

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| P-01 | Portal exists and displays index/market data; free to view. | https://dps.psx.com.pk/ ; scaffold README/registry (2026-11-04 landing page: indices as of 11:09 AM PKT) | Reused scaffold portal check | VERIFIED (reused 2026-11-04) | Re-confirm landing-page behaviour on first Phase 2 read-only inspection (read-only, no collection). |
| P-02 | PSX publishes an official public API / documentation for portal endpoints. | None found; psx-dps FAQ states PSX publishes no official public API/documentation (via scaffold) | Search + scaffold reuse; no official API doc found | UNVERIFIED (as a positive claim; the negative — no official API found — is the working assumption) | Check PSX site / PSX contact for any official API or data-licensing page; record result dated. Do not assume undocumented endpoints are sanctioned. |
| P-03 | Portal rate limits, auth requirements, redistribution/commercial terms. | None found on portal text reviewed | Search; no terms document found | UNVERIFIED | Fetch/obtain PSX terms or written PSX licensing position before any commercial use or republication; log document + date. |
| P-04 | Portal historical coverage / update schedule. | None stated on portal itself | Search; no portal statement found | UNVERIFIED | Do not rely on portal for history; use library claims (§2–§3) with their own gates. |

## 2. psx-dps — https://github.com/umairsandhu/psx-dps

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| D-01 | MIT licence, zero dependencies, no API key; unofficial, unaffiliated, not endorsed by PSX. | https://github.com/umairsandhu/psx-dps (README, via scaffold) | Reused scaffold README check | VERIFIED (reused 2026-11-04) | Pin version on Phase 2 inspection; re-read README at that version. |
| D-02 | Live quotes/OHLC/order book, whole-market snapshot in one request, ~5y EOD, today's intraday ticks, indices+constituents/weights, 38 sectors, 224k+ announcements with PDF URLs. | Same README (via scaffold) | Reused scaffold README check | VERIFIED (reused 2026-11-04, as README claims — not as live-run proof) | Phase 2 read-only inspection: one symbol + one snapshot + one announcement URL; record exact fields returned vs README. |
| D-03 | ~496 trading symbols vs ~1,029 listed instruments. | Same README (via scaffold) | Reused scaffold README check | VERIFIED (reused 2026-11-04, as README claims) | Phase 2: count symbols returned by a read-only snapshot and reconcile against the listed universe; define universe per use. |
| D-04 | Multi-node 404 quirk; node pool / probe / pin / re-probe mitigation. | Same README (via scaffold) | Reused scaffold README check | VERIFIED (reused 2026-11-04, as README behaviour) | Phase 2: observe node behaviour on read-only inspection; record whether 404s occur and how the library handles them. |
| D-05 | Market-aware TTLs (60 s trading, cached off-hours); cross-process 1 req/s; 429 stops + escalating cooldown. | Scaffold README summary | Reused scaffold check | VERIFIED (reused 2026-11-04, as library behaviour — NOT as a PSX-published limit) | Phase 2: confirm throttle/backoff in the pinned version's code/docs; do not present 1 req/s as PSX's limit. |
| D-06 | PSX data obtained via psx-dps may be commercially redistributed / resold / republished as a live feed. | No PSX agreement found; README "not a licence to redistribute" note is not legal advice (scaffold) | Search; no PSX licence found | UNVERIFIED — default: NOT permitted | Obtain PSX licensing position in writing before any commercial redistribution; until then internal analysis only. |
| D-07 | Symbol renames handled (e.g. ENGRO → ENGROH). | Scaffold (rename example) | Reused scaffold check | PARTIALLY VERIFIED (example cited, mapping table not verified) | Phase 2: build/verify alias table from announcement/PSX evidence for any renamed symbol actually used. |

## 3. psxdata — https://github.com/psxdata/psxdata

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| X-01 | MIT, PyPI, Python 3.11+, alpha 0.1.0a1; REST API in separate repo psxdata-api. | https://github.com/psxdata/psxdata (README, via scaffold) | Reused scaffold README check | VERIFIED (reused 2026-11-04) | Pin version on Phase 2 inspection; re-read README/changelog at that version. |
| X-02 | Historical OHLCV, live quotes, KSE-100 constituents, sectors (37), tickers 1000+, screener ~729. | Same README (via scaffold) | Reused scaffold README check | VERIFIED (reused 2026-11-04, as README claims) | Phase 2 read-only inspection: reconcile 1000+ vs 729 vs 496 universes; record which universe each call returns. |
| X-03 | Fundamentals, debt instruments, margin-eligible stocks (depth/format). | Same README claims (via scaffold) | Reused scaffold README check | PARTIALLY VERIFIED (claimed, depth/format not proven) | Phase 2 read-only inspection: one symbol's fundamentals fields + debt/margin lists; record exact fields or mark "not structured". |
| X-04 | NO historical intraday archive (daily OHLCV + live snapshots only, because PSX does not publicly expose a historical intraday archive). | Same README explicit limit (via scaffold) | Reused scaffold README check | VERIFIED (reused 2026-11-04, as an explicit stated limit) | No check needed to accept the limit; do not plan any historical-intraday feature on this source. |
| X-05 | Historical cached forever, live 15 min; exponential backoff, 3 attempts. | Scaffold README summary | Reused scaffold check | VERIFIED (reused 2026-11-04, as library behaviour) | Confirm in pinned version's code/docs on Phase 2 inspection. |
| X-06 | psxdata PSX data may be commercially redistributed. | No PSX agreement found | Search; no licence found | UNVERIFIED — default: NOT permitted | Same PSX gate as D-06. |

## 4. SECP — https://www.secp.gov.pk/

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| S-01 | SECP homepage lists eZfile + eZfile user manuals; Companies Regulations 2024. | https://www.secp.gov.pk/ | Direct page-text fetch, 2026-11-04 | VERIFIED | None for homepage existence; eZfile data-access details remain per S-04. |
| S-02 | Terms of Use: SECP owns site material; residents/citizens may copy/print single pages unmodified for non-commercial sharing with other citizens/residents without cost; third-party material excluded; hyperlinking/framing needs prior SECP permission; access may be denied/restricted without reasons; verify against official SECP record; no accuracy warranty. | https://www.secp.gov.pk/terms-of-use/ | Direct page-text fetch, 2026-11-04 | VERIFIED | Re-fetch before any SECP reproduction; terms may be revised without notice (per the page itself). |
| S-03 | Basic public company-name search is free without an account; detailed info / certified copies need eServices account + request (and may carry a fee). | Third-party guides (sterling.pk, findpk.com) via search | Third-party summaries only | PARTIALLY VERIFIED | Confirm on SECP/eServices/eZfile pages directly: which search is public, what needs an account, and the current fee (do not quote the Rs 600/page third-party figure). |
| S-04 | A documented, stable public SECP API exists for company/filing data. | None found; third-party skill summary: HTML search form, "no documented, stable programmatic endpoint" | Search; no API doc found | UNVERIFIED — working assumption: NO stable API | Check SECP/eZfile documentation and site directly; if no API is documented, plan manual single-company verification only. |
| S-05 | SECP publishes listed-company financial statements in machine-readable form usable for PSX Intelligence AI. | None found | Search; no such publication found | UNVERIFIED | Check SECP publications/licensed-entities pages directly; do not assume registry = financials feed. |
| S-06 | SECP data may be bulk-collected, scraped or commercially redistributed. | S-02 terms (narrow sharing) + 2022 scraping-restriction precedent (Business Recorder) | Direct terms fetch + third-party report | UNVERIFIED — default: NOT permitted (and scraping is affirmatively risky) | Do not scrape; seek SECP permission for any use beyond S-02 before proceeding. |

## 5. SBP — https://www.sbp.org.pk/

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| B-01 | SBP produces Monthly Statistical Bulletin (MSB); much MSB data also on producers' sites (SBP, PBS). | SBP bulletin prefaces via search (https://www.sbp.org.pk/reports/stat_reviews/Bulletin/index.htm as cited) | Official SBP document via search snippet | PARTIALLY VERIFIED | Directly fetch current MSB index + one bulletin table; record edition + format. |
| B-02 | EasyData portal (easydata.sbp.org.pk) provides access/download/plot of time-series data; latest edition returned states 18,000+ variables; dashboards: Remittances, Inflation Snapshot, Financial Statement Analysis, Pakistan's Economic Interaction with Other Countries. | SBP bulletin prefaces via search (latest edition: SB-26-Jul preface; earlier editions: 8k/11k/14k variables) | Official SBP document via search snippet | PARTIALLY VERIFIED | Directly fetch EasyData catalogue; record current variable count + dashboard list with date; do not cite a count without its edition. |
| B-03 | EasyData has "a new API to retrieve a complete dataset" (SBP preface wording). | Same SBP prefaces via search | Official SBP document via search snippet | PARTIALLY VERIFIED (existence stated; interface not stated) | Find EasyData API documentation page; record endpoint, method, format, auth, rate limit — or record "no public documentation found" if absent. Do not invent an endpoint. |
| B-04 | EasyData API endpoint / format / auth / rate limit / Python library. | None found | Search; no interface document found | UNVERIFIED | Same check as B-03, plus: test only the documented route (read-only) in Phase 2; record result. |
| B-05 | SBP terms / licence / cost for reuse (including commercial reuse). | None found | Search; no terms page found | UNVERIFIED | Fetch SBP terms/licence page or obtain SBP position; until then internal analysis only. |
| B-06 | SBP coverage span, update schedule, named policy-rate series identity. | None stated in material found | Search; no statement found | UNVERIFIED | Record per-series span + update timing from EasyData/MSB metadata on Phase 2 inspection; do not hard-code a schedule. |
| B-07 | Direct fetch of https://www.sbp.org.pk/ in this session. | Fetch attempt 2026-11-04 | Page-text fetch | FAILED (fetch error, not a site finding) | Retry via live-browser check by parent agent if needed; do not treat the fetch error as "SBP site down". |

## 6. PBS — https://www.pbs.gov.pk/

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| Q-01 | PBS homepage surfaces Monthly CPI (Oct 2026, 1.1% in snippet) and Weekly SPI headlines. | https://www.pbs.gov.pk/page/8/ via search snippet | Search snippet (homepage) | PARTIALLY VERIFIED | Directly fetch PBS homepage + latest CPI/SPI release pages; record release dates. |
| Q-02 | CPI monthly (national/urban/rural, base 2015-16=100; 68 urban markets/35 cities + 27 rural centres; HIES 2015-16 weights ~26,000 households); SPI weekly (51 items, 50 markets, 17 cities). | https://www.pbs.gov.pk/price-statistics/ via search snippet + third-party explainers | PBS page snippet + consistent third-party explainers | PARTIALLY VERIFIED | Directly fetch PBS price-statistics methodology page + latest Monthly Review on Price Indices; confirm base, coverage and cadence. |
| Q-03 | Data Dissemination Policy: "open by default, confidential by design"; aggregates/publications/anonymised microdata/metadata/non-confidential datasets normally free under an open licence in human- + machine-readable formats; Tier 1 = open aggregates/APIs, Tier 2 = Public Use Files, Tier 3 = licensed files (application/endorsement/NDA), Tier 4 = non-disseminable. | https://www.pbs.gov.pk/data-dissemination/ via search | Official PBS policy document via search snippet | PARTIALLY VERIFIED | Directly fetch the policy + exact licence text; record per-dataset tier for every PBS dataset actually used. |
| Q-04 | Tier 1/2 products + Public Use Files carry a standard open government licence permitting copying/adaptation/commercial + non-commercial reuse WITH attribution; standard products free at point of use; nominal charges only for exceptional custom work. | Same policy document via search | Official PBS policy document via search snippet | PARTIALLY VERIFIED | Same as Q-03; do not quote custom-work prices until directly verified. |
| Q-05 | A usable public PBS API exists (endpoint, docs, auth, rate limit). | Policy scope mentions "APIs" and Tier 1 "non-confidential APIs"; no endpoint/docs found | Search; no interface document found | UNVERIFIED | Find PBS API documentation or record "no public API documentation found"; plan PDF/spreadsheet extraction until then. |
| Q-06 | Complete machine-readable history per PBS series; PBS release calendar (exact CPI/SPI release times). | Historical indices spreadsheet found (pbos.gov.pk, 2016-17 onward in snippet); cadence from explainers only | Search; partial file + third-party cadence | PARTIALLY VERIFIED (one historical file) / UNVERIFIED (per-series history + calendar) | Verify per-series history file + release calendar from current pbs.gov.pk releases; prefer current domain over legacy pbos.gov.pk files. |
| Q-07 | Direct fetch of https://www.pbs.gov.pk/ in this session. | Fetch attempt 2026-11-04 | Page-text fetch | FAILED (fetch error, not a site finding) | Retry via live-browser check by parent agent if needed; do not treat the fetch error as "PBS site down". |

## 7. Finance Division — https://www.finance.gov.pk/

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| F-01 | Homepage lists Monthly Economic Update & Outlook October 2026 (29-10-2026), debt reviews, borrowing plans, SOE reports, fiscal publications. | https://www.finance.gov.pk/ | Direct page-text fetch, 2026-11-04 | VERIFIED | None for homepage existence. |
| F-02 | Pakistan Economic Survey chapters (e.g. Ch. 4 Fiscal Development, Ch. 11 Health/Nutrition; 2024-25 + 2025-26 editions) and Monthly Updates (Mar/May/Oct 2026) exist as PDFs with fiscal/external/CPI summary tables (CPI sourced to PBS, reserves/exchange to SBP in Oct 2026 edition). | https://www.finance.gov.pk/economic/Monthly_Economic_Update_and_Outlook_October_2026.pdf ; https://finance.gov.pk/survey/chapter_26/4_Fiscal Development.pdf (as returned in search) | Publication PDFs via search | PARTIALLY VERIFIED | Directly fetch current Survey + Update PDFs; record edition, vintage flags (P/B.E./revised) and originator per table. |
| F-03 | A Finance Division API / machine-readable series exists. | None found; all material found is PDF | Search; no API found | UNVERIFIED — working assumption: NO API | Check Finance Division site directly for any data portal/API; if none, plan PDF extraction only. |
| F-04 | Finance Division terms / licence / cost for reuse (including commercial). | None found | Search; no terms page found | UNVERIFIED | Fetch terms/licence page or obtain position; until then internal analysis only, with originator attribution. |
| F-05 | Finance Division release calendar / complete machine-readable fiscal history. | Editions found to ≥2017-18; no calendar or series database found | Search; partial | UNVERIFIED | Record per-edition availability; do not present Survey PDFs as a time series without vintage handling. |

## 8. World Bank — https://data.worldbank.org/

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| W-01 | "Free and open access to global development data"; site expanding to Data360. | https://data.worldbank.org/ | Direct page-text fetch, 2026-11-04 | VERIFIED | None for homepage statement; Data360 migration to be watched (W-05). |
| W-02 | Indicators API v2, keyless, no account/signup; default XML, `format=json` for JSON; base `https://api.worldbank.org/v2/country/{code}/indicator/{indicator}`; v1 retired Nov 2018. | Independent API summaries via search (multiple, consistent) | Third-party summaries (not official docs fetch) | PARTIALLY VERIFIED | Directly fetch World Bank Indicators API documentation; confirm v2 base, formats, pagination (`per_page`, `page`, `date`, `mrv`) before Phase 2 use. |
| W-03 | No official World Bank Python library; third-party `wbgapi`, `wbdata`, `world_bank_data` in common use. | Independent API summaries via search | Third-party summaries | PARTIALLY VERIFIED | Confirm against official docs on Phase 2 inspection; pin any third-party client version if used. |
| W-04 | CC BY 4.0 default for WBG-produced open data (commercial reuse WITH attribution); per-dataset tags + third-party exceptions override; some datasets restricted / not WBG-owned. | https://blogs.worldbank.org/en/opendata/5-reasons-check-out-world-bank-s-new-data-catalog ; https://data360.worldbank.org/en/about ; https://datacatalog.worldbank.org/faq (via search) | World Bank sources via search snippet | PARTIALLY VERIFIED | Directly fetch licence page + licence tag for EVERY indicator/database used; record tag per series. Never default to CC BY 4.0 without the tag. |
| W-05 | Rate limit / update cadence / exact indicator count. | No official limit found in summaries; counts vary (14k–16k+ indicators, 200+ vs 217 economies, 29,544 codes/71 databases) | Search; no official statement found | UNVERIFIED | Do not cite a count or a limit; throttle gently, cache, paginate; record revision behaviour per pull (full-refresh caution). |
| W-06 | Many series back to 1960; patchy pre-1990 / low-income coverage; many values are World Bank estimates, not nationally reported figures. | Independent summaries via search | Third-party caveats | PARTIALLY VERIFIED | Confirm estimate-vs-reported status from API metadata per series used; never present modelled values as nationally reported. |

## 9. IMF — https://www.imf.org/en/Data

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| I-01 | IMF Data covers WEO, IFS, BOP, DOT, GFS, commodity prices and other published statistics. | https://www.imf.org/en/About/copyright-and-terms (Data definition) via search; https://www.imf.org/en/Data | IMF terms page via search snippet | PARTIALLY VERIFIED | Directly fetch terms page + Data portal catalogue; record databases actually available. |
| I-02 | Data terms: download/extract/derivative/publish/distribute permitted WITH attribution "Source: International Monetary Fund, Database Name, <link>"; integrity + transformation-note + downstream-communication + standalone-sale free-availability conditions; "as is" without warranty; no right to confidential/unpublished data. | Same terms page via search (effective 2024-10-11 per excerpts) | IMF terms page via search snippet + consistent third-party excerpts | PARTIALLY VERIFIED | Directly fetch current terms text in full; file excerpt + date before any IMF distribution. |
| I-03 | "For any potential commercial reuse of IMF Data, email copyright@imf.org to request permission." General Content: free non-systematic personal/noncommercial use only; systematic/substantial reuse needs written permission. | Same terms page via search | IMF terms page via search snippet | PARTIALLY VERIFIED | Directly confirm this condition; email copyright@imf.org BEFORE any potential commercial reuse and log the reply. |
| I-04 | DataMapper API (WEO, JSON, `https://www.imf.org/external/datamapper/api/v1/…`) and SDMX API (`api.imf.org/external/sdmx/…`, SDMX 2.1/3.0) exist. | Third-party API evaluations/guides via search | Third-party evaluations (not IMF docs fetch) | PARTIALLY VERIFIED | Directly fetch IMF DataMapper + SDMX documentation; record the exact route, version and dataflows for the intended use. |
| I-05 | Authentication for DataMapper / SDMX (keyless vs subscription key via portal.api.imf.org). | Third-party sources conflict (keyless claims vs key-required claims; portal terms behind sign-in) | Search; conflict unresolved | UNVERIFIED | Test/document the exact route intended (read-only) in Phase 2; record auth result per route; do not state blanket "no auth" for IMF. |
| I-06 | Rate limits (including the 50 req/s `imfp` package claim), indicator/dataflow counts (190+ economies, 222 dataflows), WEO twice-yearly cadence, per-indicator spans. | Third-party evaluations/package pages via search | Third-party only; no IMF document found | UNVERIFIED | Do not adopt any of these as IMF facts; verify counts/cadence/limits against IMF documentation or record as third-party figures. |
| I-07 | Third-party Python libraries `imfpy`, `imfdatapy`, `imfp` exist and are suitable. | PyPI / project pages via search | Third-party project pages | PARTIALLY VERIFIED (existence) / UNVERIFIED (suitability, maintenance, version) | Evaluate pinned versions on Phase 2 inspection; prefer documented IMF routes over an unmaintained wrapper. |

## 10. FRED — https://fred.stlouisfed.org/

| # | Claim | Evidence / URL | Verification method | Status | Check remains |
|---|---|---|---|---|---|
| R-01 | FRED API exists (REST, `https://api.stlouisfed.org/fred/`; `series`, `series/observations`, `series/search`, `category`, `releases`, `sources`); default XML, `file_type=json` for JSON; missing values as `"."` string (per summary). | Independent API summaries via search | Third-party summaries (not official docs fetch) | PARTIALLY VERIFIED | Directly fetch FRED API documentation; confirm endpoints + formats before any use. |
| R-02 | Free API key required via free FRED account, passed as `api_key` parameter; distinct key per application advised. | https://fred.stlouisfed.org/docs/api/terms_of_use.html via search ("you must have register[ed] for an API Key") + summaries | FRED API Terms via search snippet + summaries | PARTIALLY VERIFIED | Directly fetch API Terms + key page; Phase 2 key decision needed before any FRED call (no key obtained in Phase 1). |
| R-03 | Rate limit 120 requests/minute, 429 on excess, possible temporary block. | Independent summaries via search (noting the figure "appears nowhere in the Terms of Use") | Third-party summaries | PARTIALLY VERIFIED as a reported current setting / UNVERIFIED as a contractual limit | Directly check FRED error/terms documentation; throttle well below 120/min and treat 429 as a hard stop regardless. |
| R-04 | Mandatory notice: "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis." Services framed as non-commercial/educational/personal; no endorsement, no replication/replacement of FRED experience, no passing FRED off as your own. | https://fred.stlouisfed.org/legal/ ; https://fred.stlouisfed.org/docs/api/terms_of_use.html via search | FRED legal/API-terms pages via search snippet | PARTIALLY VERIFIED | Directly fetch full current Terms; file excerpt + date before any FRED use. |
| R-05 | Series with a copyright notice are third-party owned; use beyond personal use requires the data owner's permission (St. Louis Fed cannot grant it). | Same FRED legal pages via search | FRED legal pages via search snippet | PARTIALLY VERIFIED | Directly fetch full Terms; check copyright note on EVERY series before any non-personal use. |
| R-06 | **AI/caching prohibitions:** Terms update (June 2024, via FRED news page) prohibits using FRED Services/Content in connection with development/training of AI/ML systems (including LLMs, deep learning, generative AI), and prohibits storing/caching/archiving FRED content, providing stored/cached/archived content to third parties, incorporating it in a database/compilation/archive/cache, and wholesale downloading in violation of Terms. | https://fred.stlouisfed.org/news/2024/06/weve-updated-our-terms-of-use-action-requested via search | FRED news page via search snippet | PARTIALLY VERIFIED — treated as a BLOCKER until directly re-read | **Gate (must clear before ANY FRED AI use):** directly fetch the FULL current FRED Services Terms of Use, confirm whether these prohibitions are current and their exact scope, and obtain a written legal/permission clearance for the specific intended use. Until then: FRED = ON HOLD for PSX Intelligence AI. Do not train on, cache, redistribute or commercially output FRED series. |
| R-07 | No official St. Louis Fed Python library; third-party `fredapi`, `pandas-datareader` in common use; no-key CSV fallback exists. | Independent summaries via search | Third-party summaries | PARTIALLY VERIFIED (no official client) / NOT ADOPTED (CSV fallback as an evasion route) | Confirm official-client position from FRED docs; do NOT use the no-key CSV route to evade key/terms requirements. |
| R-08 | FRED series counts (~800k–851k, 100+ sources) and per-series history (e.g. S&P 500 price-only, ~10y). | Independent summaries via search (counts vary) | Third-party summaries | UNVERIFIED (exact counts + per-series history) | Do not cite a count; read series metadata per series used; record vintage (latest vs ALFRED) per pull. |

## Summary counts (Phase 1)

- **VERIFIED (including reused scaffold):** 13 rows — PSX portal existence, psx-dps/psxdata
  README claims and stated limits, SECP homepage + Terms, Finance Division homepage,
  World Bank homepage statement.
- **PARTIALLY VERIFIED:** 30 rows — mostly official documents quoted via search
  snippets (SBP prefaces, PBS policy, IMF terms, FRED terms, World Bank blog/Data360)
  and consistent third-party API summaries. Every one needs a direct re-read before
  reliance.
- **UNVERIFIED:** 22 rows — concentrated in: PSX/SBP/PBS/Finance API endpoints,
  auth, rate limits and commercial terms; SECP API/financials; IMF auth/rate limits;
  FRED contractual limits/counts; and all commercial-redistribution permissions.
- **Fetch failures (not findings):** SBP homepage and PBS homepage page-text fetches
  failed in this session (fetch error). They are recorded in B-07 and Q-07 and must
  not be reported as "site down" or "no data".

## Phase 2 gate rule (from this matrix)

A Phase 2 collector step may use a source for a purpose only when every matrix row
covering that purpose is VERIFIED (direct fetch, dated, filed) or the purpose is
explicitly internal-analysis-only under the Licensing Policy. Any row still
PARTIALLY VERIFIED or UNVERIFIED at Phase 2 start keeps its gate closed for the
gated use (commercial use, redistribution, AI training, bulk collection) until cleared.
