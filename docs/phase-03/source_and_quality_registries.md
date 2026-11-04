# Phase 3 — Source and Quality Registries

## data_sources (registry)

source_key (unique), display_name, source_type, base_reference
(a URL or identifier AS DOCUMENTED in the registry — never a newly
invented endpoint), freshness_threshold_seconds, reliability_notes,
verification_status, terms_summary (redistribution limits in plain
words).

Rules:
- A source marked 'unverified' may be staged; its rows must not be
  presented as verified.
- PSX commercial redistribution requires a written PSX agreement
  (Phase 1 gate). MIT licences on psx-dps/psxdata licence the
  libraries only, not PSX data redistribution. This registry
  records that limit; it does not waive it.
- FRED: gated out of AI training, caching and commercial output
  until its full current Terms are re-read and cleared (G-06).
- Universe/sector counts unresolved (G-03): ~496 trading vs
  ~1,029 listed vs 1000+ tickers; 38 vs 37 sectors. The registry
  and the sectors table keep both taxonomies; Phase 4 must
  reconcile them with dated evidence before any full-market
  completeness claim.

## data_quality_reports (registry of problems)

Append-only: issue_type, severity, affected entity + row, detail,
resolution_status, resolved_at. Resolution never deletes the
original report. See provenance_and_quality.md for the vocabulary.

## raw_payloads (hash-addressed evidence)

content_hash (SHA-256, unique), payload_type, storage_location
(storage-relative path, or 'inline' for small payloads), byte_size,
data_source_id. Processed tables reference raw_payloads; they
never embed a second, divergent copy of 'the raw data' as free
text. For large payloads (PDFs) the file is on disk and this row
is its durable reference + hash + size + location.
