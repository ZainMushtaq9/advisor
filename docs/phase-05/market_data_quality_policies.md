# Phase 5 — Market-Data Quality Policies

## 1. Vocabulary (Phase 3 CHECK constraints + Phase 5 spec)

VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, CONFLICTED, MISSING,
REJECTED, STALE, PENDING_REVIEW. In market data, MISSING and
REJECTED are report states (a missing session, a rejected row),
not stored price rows: a missing observation is absent, never
zero; a rejected row is never stored as a price.

## 2. Promotion rules (never automatic)

- No single-source observation is ever VERIFIED, even from an
  official source. VERIFIED requires an official source AND
  another agreeing source for the same grain.
- No record is promoted by re-ingestion, by age, or by volume
  of evidence from one source. Promotion requires a second
  distinct agreeing source.
- All registry records feeding this phase are UNVERIFIED
  (single DPS snapshot). Market observations inherit that
  caution: scope is labelled, never upgraded, until a second
  source corroborates.

## 3. Conflicts

Conflicting prices/records are kept side-by-side with
provenance (grain includes data_source_id). Nothing silently
merges or chooses a conflicting value. Within one ingestion run
both disagreeing rows are CONFLICTED. Across runs, the later
disagreeing row is CONFLICTED while the earlier row cannot be
re-flagged (Phase 3 immutability) — the conflict remains visible
via differing values plus the CONFLICTED row (audit A3, accepted).

## 4. Staleness

V1 freshness rule only: collected >30 days after trading_date
→ `freshness: STALE` alongside quality_status (see
`market_validation_rules.md` §4). STALE never replaces a
quality status and never, by itself, deletes or corrects a row.

## 5. Raw vs processed

Raw values are preserved: rejected rows keep their raw values
in the ingestion report; stored rows keep official unadjusted
prices (`is_adjusted=False`). Adjusted series, if ever built,
are derived views with a validated corporate-action
methodology — never edits to stored rows, never presented as
official prices.

## 6. Provenance on every observation

source_key, source_timestamp (when the source says the
observation is for), collected_at (when WE received it, PKT,
tz-aware), quality_status, freshness label. Collection time is
never an observation time; a fetch time is never a source
timestamp. A row without a source is not stored (MarketPrice
data_source_id is NOT NULL by Phase 3 audit fix H3).

## 7. Frontend/API honesty

APIs return only rows that exist. Empty market → counts 0 with
the scope note, never 404 for an empty market, never fabricated
rows. The frontend renders only API rows with truthful
empty/unavailable states.
