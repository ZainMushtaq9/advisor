# Phase 3 — Provenance and Data Quality

## Provenance block (required, not optional)

Every market / financial / news / analysis row carries, where
meaningful: data_source_id, source_key, source_timestamp,
collected_at, quality_status. Rules:

- source_timestamp = when the source says the observation is for.
- collected_at = when WE fetched it (Asia/Karachi, tz-aware).
- A fetch time is never a source timestamp. A source timestamp is
  never a fetch time. Code that conflates them is a defect.
- Freshness is computed from source_timestamp + the source's
  freshness threshold (data_sources.freshness_threshold_seconds),
  never from collected_at alone.

## Quality vocabulary (CHECK-enforced, 22 tables)

Audit H1 fix: migration 20261104_0004 added the missing
`ck_financial_statements_quality_status`, so all 22 tables with a
quality_status column are now CHECK-enforced (21 in migration
20261104_0003 + financial_statements in 20261104_0004). The dead
`QUALITY_CHECK` definition that used to sit in models/base.py was
deleted, so no code looks like enforcement without enforcing.

VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, CONFLICTED, MISSING,
REJECTED, STALE, PENDING_REVIEW.

- UNVERIFIED is the default. Nothing arrives VERIFIED.
- Upgrading UNVERIFIED -> VERIFIED/PARTIALLY_VERIFIED requires
  evidence (a source-check reference). The helper
  `backend/app/services/data_quality.py::upgrade_quality_status`
  raises ValueError without it, and this is tested.
- Downgrades (to CONFLICTED, STALE, REJECTED) are always allowed:
  new information must never be blocked from worsening a status.
- CONFLICTED means two sources disagree and both rows are kept.
  The system never picks a winner silently.
- MISSING means the observation does not exist. It is never stored
  as zero, and a missing session is a data_quality_reports row, not
  a fabricated price.

## Quality registry

data_quality_reports: issue_type (missing_session, stale,
conflict, schema_mismatch, failed_validation), severity
(CRITICAL/HIGH/MEDIUM/LOW), affected entity + row, detail,
resolution_status. Resolution (audit H2 fix) is a status change
on the SAME row (resolution_status + resolved_at are the only
mutable columns, trigger-enforced) plus a new row where
underlying data changed — the original report is never deleted
and its detail is never edited.

## Provenance scope, qualified (audit M7)

The architecture principle reads 'every market/financial/news/
analysis record' with the qualifier 'where meaningful, else via
the parent row'. Tables that rely on parent provenance, not their
own block: financial_statement_line_items (via their statement),
forecast_evaluations (via their forecast), fundamental_analysis_
runs and technical_calculation_runs/errors (operational rows, not
data records), portfolio tables (user-owned state, not sourced
observations), and financial_documents (company + source_url +
content_hash, no separate source block). Everything else in the
market/financial/news/analysis domains carries the full block.

## Source registry

data_sources is the database twin of the collector registry:
source_key (unique), display name, type, base reference (a URL or
identifier as documented — never an invented endpoint), freshness
threshold, reliability notes, verification_status, terms summary
(redistribution limits in plain words). A source marked
'unverified' may be staged; its rows must not be presented as
verified. Phase 1 gates G-01 (SECP/SBP/PBS/Finance/World Bank/IMF/
FRED machine-use UNVERIFIED) and G-06 (FRED gated out of AI
training/caching/commercial output) are carried forward unchanged.
