# PSX Intelligence AI — Phase 1: Data Source Comparison

**Budget:** PKR 0 absolute. No paid source, tier, subscription or hosting is ranked,
recommended or budgeted. "Cost" below means only the source's own access cost; the
user's local hardware, electricity and internet are external operating expenses, never
called free. Where a free source cannot meet a need, the cell says so and no paid
alternative is introduced.
**Scope:** Phase 1 research/specification only. No live collection at scale, no Phase 2
code, no real trades (the system must NOT execute real trades initially).
**Reading note:** "Free" in this file always carries the licensing caveat from
`DATA_SOURCE_RESEARCH.md` and `DATA_LICENSING_POLICY.md` — free viewing/access ≠
redistribution or commercial-use rights, except where a per-dataset licence (World Bank
CC BY 4.0 default, PBS Tier 1 open licence signal) actually states otherwise.

## Side-by-side table (all 10 sources)

| Dimension | 1. PSX Portal | 2. psx-dps | 3. psxdata | 4. SECP | 5. SBP (EasyData/MSB) | 6. PBS | 7. Finance Division | 8. World Bank | 9. IMF | 10. FRED |
|---|---|---|---|---|---|---|---|---|---|---|
| **Coverage (what)** | Indices + market data on landing page | Quotes/OHLC/order book, whole-market snapshot, indices+constituents/weights, 38 sectors, announcements+PDF URLs | Historical OHLCV, live quotes, KSE-100, sectors (37), fundamentals (claimed), debt, margin-eligible | Company registry / regulation; NOT prices or financials feed | Monetary/banking/economic time series; remittances, inflation snapshot, FSA dashboards | CPI/WPI/core (monthly), SPI (weekly), trade, population, surveys | Economic Survey (annual chapters) + Monthly Update (fiscal/external/CPI summary, largely secondary) | Global development indicators (GDP, population, trade, FDI, debt, health, governance) | WEO/IFS/BOP/DOT/GFS, commodity prices; global macro/fiscal/external | US + international macro/financial series; US-centric, many republished series |
| **History** | UNVERIFIED from portal | ~5y EOD claimed; intraday = today only | Daily OHLCV; NO historical intraday archive (README explicit) | UNVERIFIED | UNVERIFIED span; MSB monthly vintages | Historical indices file exists (2016-17 onward in snippet); per-series history UNVERIFIED | Survey editions to ≥2017-18 found; machine-readable history UNVERIFIED | Many series to 1960; patchy pre-1990; modelled values | WEO history + projections; dated vintages via SDMX; span per indicator UNVERIFIED | Per-series; varies widely; ALFRED vintages exist |
| **Freshness** | Live in market hours; some landing values prior-day (scaffold) | 60 s TTL while trading (claimed); cached off-hours | Live snapshots 15-min cache (claimed); history cached forever | Registry: UNVERIFIED schedule; NOT market freshness | UNVERIFIED schedule; monthly bulletin | CPI monthly; SPI weekly (explainer statements, not PBS calendar) | Monthly Update monthly; Survey annual | Annual, lagged; quarterly revision cycle (third-party) | WEO twice-yearly (third-party); per-database UNVERIFIED | Per-series release calendar; revisions routine |
| **Machine-readability** | Landing page only; endpoints undocumented | Python library, JSON via undocumented endpoints | Python library + separate REST repo; JSON (claimed) | HTML search form; NO stable API found | Portal + downloads (Excel for MSB, older edition); API existence stated, endpoint UNVERIFIED | PDF reviews + spreadsheets; API contemplated in policy, endpoint UNVERIFIED | PDF only in all material found | REST API v2, JSON (`format=json`), bulk CSV/Excel | DataMapper JSON + SDMX (2.1/3.0); SDMX discovery required | REST API, JSON (`file_type=json`), XML default |
| **Auth** | UNVERIFIED | None (no key) | None stated | Public search: none described; detail/copies: eServices account + request (third-party) | UNVERIFIED | Publication downloads: none evidenced; microdata tiers 3–4: application/NDA (out of scope) | None evidenced for downloads | None (keyless) | Route-dependent / UNVERIFIED (DataMapper reported keyless; SDMX portal key may apply) | Free account + free API key REQUIRED (`api_key` param); no key obtained in Phase 1 |
| **Cost (source itself)** | Free to view | Free library, no key | Free, PyPI | Public search described free; certified copies fee-bearing (figure UNVERIFIED) | No price stated; do not assert "free" as an SBP term | Standard products free at point of use (policy via search); custom work nominal charges (figures not quoted) | No price stated; do not assert "free" as a term | Free, keyless | Free access presented; commercial reuse needs permission (see Licensing) | Free key/access; use prohibitions apply (see below) |
| **Licensing** | PSX's to license; redistribution UNVERIFIED — assume NOT permitted commercially without PSX agreement | MIT = code only; PSX data NOT licensed by it | MIT = code only; PSX data NOT licensed by it | Narrow: residents/citizens may copy/print single pages unmodified, non-commercial sharing only; hyperlinking needs permission; third-party material excluded | UNVERIFIED — no terms page found | Tier 1/2 open government licence signal: copy/adapt/commercial+non-commercial reuse WITH attribution (policy via search; exact text UNVERIFIED) | UNVERIFIED — no terms page found | CC BY 4.0 DEFAULT for WBG-produced open data (commercial reuse WITH attribution); per-dataset tags + third-party exceptions override | Data: download/extract/derivative/publish/distribute WITH attribution + downstream-communication + standalone-sale disclosure; ANY potential commercial reuse: email copyright@imf.org for permission first | Non-commercial/educational/personal framing; mandatory non-endorsement notice; third-party-copyright series need owner permission; AI/ML-training + caching/archiving/redistribution prohibitions reported in 2024 update — ON HOLD for AI use |
| **Stability** | LOW — undocumented, can change without notice | LOW — wraps undocumented endpoints + multi-node 404 quirk; library mitigates, does not remove risk | LOW-MEDIUM — alpha 0.1.0a1, APIs may change; daily-only scope is stable as a stated limit | LOW for automation — HTML form, eZfile transition, access can be restricted | MEDIUM-LOW — official portal, but API interface undocumented in material found | MEDIUM-LOW — official publisher, but PDF-first; policy framework, not per-dataset guarantee | MEDIUM-LOW — official publisher, PDF-only | MEDIUM-HIGH — documented v2 API, but Data360 migration may move docs/URLs; per-dataset terms vary | MEDIUM — two APIs, portal sign-in wall, SDMX complexity, vintage revisions | MEDIUM as an API, LOW for this project — terms may prohibit the intended AI use outright |
| **Intended Phase 2 use** | **Reference only** (landing-page sanity check) | **PRIMARY (market)** — snapshot/quote/EOD/today ticks/announcements, with psxdata fallback | **BACKUP (market)** — EOD/snapshots, KSE-100, sectors; fundamentals ONLY after live-sample verification | **MACRO-ONLY, manual** — registry verification for a named company, case by case; NO bulk/automated use | **MACRO-ONLY** — monetary/banking context after API endpoint + licence are verified | **MACRO-ONLY** — monthly CPI / weekly SPI context after licence text + per-dataset tier are verified | **MACRO-ONLY** — fiscal narrative/context; originator series preferred over its secondary tables | **MACRO-ONLY** — annual global/Pakistan context, per-dataset licence tag checked | **MACRO-ONLY** — WEO/fiscal/external context, commercial permission sought before any commercial use | **MACRO-ONLY, ON HOLD** — NO training, caching, redistribution or commercial AI output until full current Terms are directly re-read and the specific use is cleared in writing |

## Ranking — free sources first (and why this order)

Free here means zero source cost under PKR 0. It does NOT mean zero effort, zero
licence conditions, or zero risk. The ranking is by fitness for PSX Intelligence AI
Phase 2, not by how "open" a source sounds.

1. **psx-dps — primary market source.** Only free route evidenced for whole-market
   snapshot, today's ticks and announcements. Ranked first despite low stability
   because no other free source provides PSX market data at all. Its rank is
   conditional on the psxdata fallback below.
2. **psxdata — backup market source.** Only free route evidenced for daily EOD history
   and a second live-snapshot path. Ranked second because it cannot back up intraday
   history or (until verified) fundamentals, and because it is alpha.
3. **PSX Portal itself — reference, not a ranked data feed.** Free to view and the
   ground truth for what PSX publishes, but with no official API it cannot be a
   programmatic primary. Used for sanity checks, not for collection.
4. **World Bank — first macro source.** Keyless documented v2 API, CC BY 4.0 default
   for WBG-produced data, annual Pakistan/global context. Ranked above IMF only
   because its commercial-reuse default is clearer (attribution) while IMF requires a
   permission request for potential commercial reuse. Per-dataset licence tags still
   mandatory.
5. **PBS — Pakistan macro source (national originator).** Monthly CPI and weekly SPI
   are the authoritative Pakistani inflation series; the Tier 1 open-licence signal
   is favourable. Ranked below World Bank only because its machine-readable route
   (API endpoint) is unverified and its evidenced route is PDF extraction.
6. **SBP — Pakistan monetary/banking source (national originator).** EasyData/MSB are
   the authoritative monetary/banking series, but API endpoint, licence and schedule
   are all unverified, so it cannot rank above PBS on Phase 1 evidence.
7. **IMF — global macro source.** Rich WEO/fiscal/external data, but two APIs with
   unclear auth, SDMX complexity, and a hard commercial-permission condition keep it
   below World Bank/PBS/SBP for Phase 2 sequencing. Use only after the permission
   question is answered.
8. **Finance Division — fiscal narrative source.** Useful context, but PDF-only and
   largely secondary (SBP/PBS/IMF originators). Never preferred over an originator
   series for the same indicator.
9. **SECP — manual registry source.** No bulk, API or market-data role. Included for
   completeness and for single-company verification; ranked last among usable sources
   because automation is not evidenced and scraping is affirmatively risky.
10. **FRED — on hold, effectively unranked for AI use.** Free key and a documented API
    would normally rank it as a strong US-macro source, but the reported AI/ML-training
    and caching/archiving prohibitions in its current Terms (see Research §10) may
    prohibit exactly what PSX Intelligence AI would do with it. Until the full current
    Terms are directly re-read and the use is cleared, FRED contributes NOTHING to
    Phase 2 planning except a documented gap. Listing it tenth is not a judgement that
    its data are poor; it is a judgement that its terms may forbid the product.

## Why Eulerpool is excluded as a PSX source

Eulerpool is NOT one of the 10 sources above and must not be added to any Phase 2
market-data plan on the basis of this research:

- **No PSX-specific coverage was stated** on the Eulerpool page read in the scaffold
  check (canonical page, ad tracking parameters stripped). A vendor page that does not
  state PSX coverage cannot be treated as covering PSX.
- **It is a vendor/paid-API route, not a free PSX source.** The scaffold records a
  claimed free tier (100,000 calls/month, no credit card) with paid tiers beyond it.
  Under the PKR 0 absolute budget, no paid tier may be assumed, budgeted or fallen back
  to, and a free-tier claim on a vendor page is not a substitute for verified PSX
  coverage, PSX licensing, or a PSX data right.
- **"Vendor to evaluate only" is its correct status** (starting condition). Any future
  Eulerpool evaluation would need, as a separate check: (i) a page/document stating
  PSX coverage symbol by symbol, (ii) its PSX data provenance and licence, (iii) its
  terms for AI use, caching and redistribution, and (iv) a zero-cost-only assessment.
  None of those is established here, so Eulerpool is excluded from the comparison
  table, from the risk register's PSX mitigations, and from Phase 2 use.
- **Do not use Eulerpool as a "backup" for psx-dps/psxdata.** A backup must cover the
  same market (PSX) under terms the project can meet. Eulerpool meets neither test on
  current evidence.

## Cross-source disagreements Phase 2 must not paper over

- **Trading vs listed count:** psx-dps ~496 trading symbols vs ~1,029 listed
  instruments vs psxdata 1000+ tickers vs ~729 screener symbols. Different universes;
  Phase 2 needs one defined universe per use (trading watch vs listed vs screener)
  and must record which universe every coverage row belongs to.
- **Sector counts:** psx-dps 38 vs psxdata 37. Do not merge sector labels across
  libraries without a mapping table.
- **CPI provenance:** PBS (originator) vs SBP MSB (republisher, sourced to PBS) vs
  Finance Division Monthly Update (secondary, sourced to PBS/SBP) vs World Bank/IMF
  (annual, modelled/revised). Same indicator name ≠ same series, vintage or method.
- **"Free" does not mean the same thing twice:** MIT (code), CC BY 4.0 (data, World
  Bank default), SECP single-page sharing permission, IMF permission-gated commercial
  reuse, FRED non-commercial framing, and PSX "free to view" are six different legal
  positions. The licensing policy file governs; this table does not override it.
