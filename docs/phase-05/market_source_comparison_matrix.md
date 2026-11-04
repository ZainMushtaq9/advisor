# Phase 5 — Market Source Comparison Matrix (RESEARCH ONLY, NOT COLLECTION)

**Date: 2026-11-04 (Asia/Karachi). Branch: `phase-05-snapshot-import`.
Companion to `market_source_research.md`, which holds the full
15-field record per source. Nothing here is collected data and no
source below is a verified collector.**

Verdict meanings:

- **SELECTED** — may be used in Phase 5, within the stated limit.
- **NOT SELECTED** — not used; reason given. Not the same as
  BLOCKED: a NOT SELECTED source was not shown to be usable, but
  no hard legal/technical bar was the deciding reason.
- **BLOCKED** — must not be used for live collection in this
  project. The deciding reason is stated; a BLOCKED verdict is
  lifted only by the parent confirmation named in the reason,
  recorded in writing.

## Per-source verdicts

| Source | Verdict | Reason (one line; full record in research doc) |
|---|---|---|
| (i) DPS portal (dps.psx.com.pk) | **BLOCKED for live adapters; SELECTED ONLY as dated-file source via an authorised route** | Live adapters barred by PSX Terms automated-navigation rule + D-51/D-52 history; the dated-file route (parent live-browser read saved as a file, as for the registry snapshot) is the only implementable ingestion route. |
| (ii) psx-dps library | **BLOCKED** | Unofficial scraper of undocumented DPS endpoints; automated DPS navigation without prior written PSX permission; README claims only, never live-verified. |
| (iii) psxdata library | **BLOCKED** | Unofficial HTML-scraping library; automated PSX navigation without prior written PSX permission; alpha, README claims only, never live-verified. |
| (iv) PSX homepage (psx.com.pk) | **NOT SELECTED** | Official but only a current-session summary (Phase 4: 26 PARTIAL rows); no price history, no registry list. |
| (v) SECP (secp.gov.pk) | **NOT SELECTED** | No machine-readable PSX registry or price dataset located (Phase 4 + 2026-11-04 search, negative result); UNVERIFIED as a source. |
| (vi) Any other free source | **NOT SELECTED (none qualifies)** | ksestocks.com is an undated third-party table with unexplained totals; Eulerpool has no PSX-specific coverage stated; psx-terminal / pypsx-toolkit / psx-data-reader / dashboards are scrapers or trading SDKs with no verified PSX licence; licensed vendors are not free. |

## Capability matrix

"Claim" = stated in the source's README/docs, NOT verified by a
live call in this research. "UNVERIFIED" = not established by any
evidence in this research. "No" = stated as absent by the source
itself (psxdata intraday) or by the scope rule below.

| Source | Daily OHLCV | Intraday (historical) | Index availability | Legal-accessibility verdict |
|---|---|---|---|---|
| (i) DPS portal | UNVERIFIED (no DPS price file or data route verified; DPS Downloads contents UNVERIFIED) | OUT OF SCOPE (no verified historical intraday archive from any source; see below) | UNVERIFIED as a dataset (index levels appear on DPS pages as session values, but no index dataset/constituent file was verified) | BLOCKED for live/automated access; dated files via an authorised route only, and only once the parent records the internal-use decision (research doc section 3) |
| (ii) psx-dps | Claim only: ~5 years EOD per symbol, one request (README claim, not a verified fact) | Claim only: today's ticks only — NOT a historical archive; OUT OF SCOPE for Phase 5 | Claim only: KSE-100, KSE-30, KMI-30, ALLSHR and more, levels AND constituents with weights (README claim, not a verified fact) | BLOCKED — automated DPS navigation without prior written PSX permission; library MIT licence does not license PSX data |
| (iii) psxdata | Claim only: daily historical OHLCV bars (depth in years UNVERIFIED — no year count stated in README) | No — README states daily bars + live snapshots ONLY; "Intraday historical data ... is not available because PSX does not publicly expose historical intraday data through any official channel" (README statement, recorded as such) | Claim only: KSE-100 constituents via `indices("KSE100")` (README claim, not a verified fact); index levels not claimed as a dataset in the README text re-read | BLOCKED — HTML scraping of PSX without prior written PSX permission; library MIT licence does not license PSX data |
| (iv) PSX homepage | No — current-session summary only | No | Session index levels only (display, not a dataset) | NOT SELECTED — ordinary browser reading is permitted, but the homepage is not a price-history source; automated access still barred by PSX Terms |
| (v) SECP | No dataset located | No dataset located | No dataset located | NOT SELECTED — no dataset, no terms, no licence located; nothing authorised |
| (vi) Other free sources | No verified free dataset located | No verified free dataset located | No verified free dataset located | NOT SELECTED — no source in this group supplies a verified, legally accessible, free dataset with terms on file |

## Scope statements (explicit)

- **Intraday is OUT OF SCOPE** unless legally accessible free
  intraday is verified in writing. **It is not, in this
  research.** psxdata offers no historical intraday (its own
  README says so); psx-dps offers today's ticks only, which is
  not a historical archive and would in any case require the
  blocked live adapter. No intraday requirement may be marked
  satisfied, and no intraday series may be built by polling
  live quotes.
- **Live DPS adapters are BLOCKED** (D-51/D-52 as technical
  history, plus the PSX Terms automated-navigation bar, which
  is the deciding reason). **The only implementable ingestion
  route in Phase 5 is validated dated files supplied through
  an authorised route** (e.g. a parent live-browser read saved
  as a file, as was done for the registry snapshot) — never a
  scraper, never a library call against live DPS/PSX routes,
  never a polling loop.
- **PSX Terms internal-use question: UNRESOLVED in writing
  (parent decision pending).** Before any live collection, the
  parent must confirm in writing: (1) internal-use permission
  basis; (2) automated-access permission if any live adapter is
  ever wanted; (3) the exact authorised file route for prices,
  including inspection of the UNVERIFIED DPS Downloads section
  via live browser; (4) scope confirmation (KSE-100 check
  against the 470-security snapshot; GEM/Non-Compliant still
  out); (5) the no-republication boundary. Full text in
  `market_source_research.md` section 3.
- **Verification rule carried forward:** VERIFIED requires at
  least two distinct agreeing sources including one official;
  a lone official dated file stays UNVERIFIED. A source adapter
  that has never successfully collected real data is NOT a
  verified collector. If no suitable dated file is supplied,
  the affected requirement is BLOCKED — collection evidence
  must never be manufactured.

## Blocker that would stop ingestion

**The ingestion blocker is the combination of (a) no verified
dated price file in hand and (b) the unresolved PSX Terms
internal-use question.** Even with a file supplied, ingestion
must wait for the parent's written internal-use confirmation
(research doc section 3, item 1) and must pass Phase 5
deterministic validation plus the two-source verification rule
before any record is promoted beyond UNVERIFIED. Until then,
`market_prices` stays 0 and no price, index, or intraday claim
may be made. Cost of this research: PKR 0; no account, no
secret, no ToS acceptance, no live data call.
