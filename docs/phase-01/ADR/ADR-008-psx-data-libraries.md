# ADR-008 — PSX data libraries: psx-dps primary, psxdata backup

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04

## Context

There is no official public PSX API (per the psx-dps FAQ, VERIFIED in outline),
so market data must come from unofficial libraries over the PSX Data Portal,
with a mandatory fallback, at PKR 0, and under the scaffold's provenance rules.
The verified facts below come from the task's starting condition (2026-11-04)
and the scaffold's registry, not from a live run by this team.

## Decision

- **Primary:** `psx-dps` (MIT, zero dependencies, no API key) for live quotes,
  whole-market snapshot, ~5 years EOD per symbol, today's intraday ticks,
  indices + constituents/weights, 38 sectors, and announcements with PDF URLs.
- **Backup:** `psxdata` (MIT, PyPI, alpha 0.1.0a1) for historical daily OHLCV
  and live snapshots when the primary fails or a cross-check is needed.
- **Adapter isolation:** each library is called only behind one adapter module,
  so a breaking change (or an endpoint change) touches one file. The collector
  rules from `~/workspace/psx-data-collection/` (provenance, PKT timestamps,
  stale flagging, missing-session recording, conflict preservation, raw vs
  processed separation) apply unchanged to everything these libraries return.

## Consequences and hard limits (do not soften these in later docs)

- **Multi-node 404 quirk (VERIFIED):** dps.psx.com.pk is served by several nodes
  and some return 404 for data routes while serving the website. psx-dps keeps
  a pool of candidate nodes, probes for one that serves data, pins it, and
  re-probes instead of believing a 404. A 404 from one node is therefore NOT
  "no data", and no code may replace this behaviour with a single hard-coded
  node URL.
- **Coverage gap (VERIFIED):** ~496 trading symbols in market watch vs ~1,029
  listed instruments claimed. Coverage per company is UNKNOWN until Phase 2
  documents it company by company; no doc may claim full PSX coverage.
- **No historical intraday archive (VERIFIED):** psxdata provides daily OHLCV
  and live snapshots ONLY; psx-dps provides today's ticks only. Any feature
  needing historical intraday bars has no source in this stack and must be
  specified as unavailable, not approximated.
- **Unofficial + undocumented (VERIFIED):** both libraries are unofficial and
  unaffiliated with PSX; DPS endpoints can change without notice. The fallback
  is mandatory, not optional, and rate limits / backoff (psx-dps: 1 req/s
  cross-process claimed; psxdata: backoff claimed) must be respected.
- **Licensing:** the libraries are free, but PSX data redistribution /
  commercial-use terms must be verified with PSX before any commercial use or
  republication (scaffold warning, inherited). This ADR grants no such licence.

## Alternatives considered

- A single library with no fallback — rejected: an undocumented endpoint
  changing without notice would take the product down.
- Eulerpool / any vendor API — **excluded**: no PSX coverage stated, vendor
  only, no paid API approved.
- An official PSX API — not available publicly; not a real alternative.
- SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use —
  **UNVERIFIED**: no library or endpoint is invented for them; they enter only
  as future verification tasks, not as stack components.

## Verification / open checks

- [ ] Phase 2: pin psxdata (alpha — expect breaking changes); live-sample-check
  psx-dps claims (snapshot, EOD, announcements/PDF URLs) and psxdata claims
  (fundamentals) before any coverage claim; document coverage company by
  company. **No full-scale live collection is authorised in Phase 1.**
