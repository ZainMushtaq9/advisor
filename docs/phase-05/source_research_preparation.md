# Phase 5 — Source Research Preparation (PREPARATION ONLY, NOT COLLECTION)

**Status: preparation only.** This document contains no collected market
data, no adapter code, and no coverage claim. It exists so that, if and
when the Phase 5 gate passes (see `phase_05_gate_report.md`), the
implementation team does not have to re-derive the source template or
re-read Phase 4's findings. Nothing here may be cited as a verified
collector, a collected observation, or a population base.

## 1. The 15-field source template (to be completed per source at implementation)

For each candidate source, record: (1) official source name, (2) exact URL,
(3) source authority, (4) available document/data types, (5) historical
coverage, (6) available reporting periods, (7) publication frequency,
(8) download or access method, (9) whether direct document/data links are
available, (10) whether automatic download is permitted, (11) access
restrictions, (12) terms of use, (13) redistribution limitations,
(14) known data-quality issues, (15) last successful verification
(date, method, result). A source with any field left as "assumed" is not
selected.

## 2. Candidate sources carried forward from Phase 4 research (findings only)

- **PSX official website (psx.com.pk):** homepage text fetch 2026-11-04
  gave 26 PARTIAL scrip rows (codes/prices only, no legal names, sectors,
  or statuses). Market context only; not a registry or price-history
  source.
- **PSX Data Portal (DPS, dps.psx.com.pk):** Listing Status page is
  JavaScript-driven (0 rows via text fetch, D-52); direct access from
  this VM fails (NoHealthyNode, D-51). DPS is the intended snapshot
  source for the registry unblocker, via a live-browser extraction —
  not via a scraper, which PSX Terms of Use restrict without prior
  written permission.
- **PSX Terms of Use / Data Services & Vending:** real-time, end-of-day
  and historical data are licensed products; redistribution requires
  prior approval/licence. Internal-use permission is a parent decision,
  to be recorded in writing before any ingestion.
- **SECP (secp.gov.pk):** no machine-readable PSX company/ticker/sector
  registry was located in Phase 4 text fetches. UNVERIFIED as a registry
  source; a specific SECP list page, if located, must be fetched and
  recorded before it is relied on.
- **psx-dps (MIT, umairsandhu/psx-dps):** README claims only — live
  quotes/OHLC/order book, ~496 trading symbols vs ~1,029 listed
  instruments (different universes per the README), whole-market
  snapshot, ~5 years EOD per symbol, today's intraday ticks only,
  indices + constituents/weights, 38 sectors, 224k+ announcements.
  Unofficial, endpoints undocumented, multi-node 404 quirk noted in
  the README. **Not live-verified from this VM; not a population base.**
- **psxdata (MIT, alpha 0.1.0a1):** README claims only — historical
  OHLCV, live quotes, tickers 1000+, KSE-100 constituents, 37 sectors,
  fundamentals, debt, margin-eligible scrips. Explicit limit in the
  README: **daily OHLCV + live snapshots only; no historical intraday
  archive**, because PSX does not publicly expose one. **Not
  live-verified; not a population base.**
- **Eulerpool:** evaluated in earlier project research as a vendor
  page with no PSX-specific coverage stated. Not a PSX source; do not
  present it as one. No sign-up or key was taken.

## 3. Known Phase 5 data rules (from the user specification, for implementation only)

- Scope = verified-registry securities only, KSE-100 first, then
  expansion only after controlled ingestion tests pass; small
  controlled set before any large backfill; no unrestricted
  large-scale collection.
- Daily OHLCV + turnover/previous close where provided; intraday only
  if legally accessible free intraday is verified (psxdata: none
  historically; psx-dps: today's ticks only).
- Indices (KSE-100/KSE-30/KSE All Share/others) only when source and
  fields are verified; market status never inferred from missing
  prices alone.
- Deterministic validation: OHLC consistency, positive prices,
  volume/turnover units, missing ≠ zero, PKT timezone,
  duplicate/future/session checks, cross-source comparison with
  conflicts preserved (never silently choose a conflicting value).
  Quality statuses: VERIFIED / PARTIALLY_VERIFIED / UNVERIFIED /
  CONFLICTED / MISSING / REJECTED / STALE; raw values preserved even
  when rejected.
- Historical integrity: store official unadjusted prices, labelled as
  such; do not calculate adjusted prices without a validated
  corporate-action methodology; never present unadjusted prices as
  total-return/adjusted.
- Reuse the Phase 3 schema; no duplicate tables. A source adapter that
  has never successfully collected real data is NOT a verified
  collector. If no suitable source can be accessed, the affected
  requirement is BLOCKED or PARTIALLY COMPLETE — collection evidence
  must never be manufactured.

## 4. What must happen before any of §3 is implemented

The gate unblocker in `phase_05_gate_report.md` §6 (dated official
snapshot, imported through the Phase 4 engine with the ≥2-source
VERIFIED rule and source_key provenance control, licensing resolved in
writing, reconciliation re-run with a real coverage result). Until that
is verified in the actual database, this document is preparation only.
