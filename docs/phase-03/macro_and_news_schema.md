# Phase 3 — Macro Indicators and News Schema

## Economic indicators

Table: economic_indicators — definition + observation in one
table (Phase 1 design): indicator_code + observation_date +
version_number grain, verification_status default 'unverified'
(via quality_status), revision preserved as new versions.

Indicator codes are data, not schema: CPI, policy rate, reserves,
fiscal balance, industrial production, etc. are rows, so a new
indicator never requires a schema change.

## Hard gate (carried forward, not resolved by Phase 3)

SECP, SBP, PBS, Finance Division, World Bank, IMF and FRED
machine-use is UNVERIFIED (Phase 1 gate G-01). FRED is gated out
of AI training, caching and commercial output until its full
current Terms are re-read and cleared (G-06). Phase 3 therefore
provides the table and the verification-status discipline, and
ZERO macro rows: no macro observation may be presented as
verified until a source check documents it. A Phase 3 table with
no rows is the correct state, not a gap to be filled with
unverified figures.

## News and research files

- news rows: headline, publisher, URL, content_hash,
  raw_payload_id, full provenance block.
- Research reports (agent outputs): files under
  research_reports/, referenced + hashed from agent_outputs —
  never duplicated as database text.
- File-level storage for the same payloads is in
  STORAGE_ARCHITECTURE (Phase 1) and storage_engine.md (Phase 3);
  the database row and the file are two views of one provenance
  record, linked by content hash.
