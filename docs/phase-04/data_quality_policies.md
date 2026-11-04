# Phase 4 — Data Quality Policies

## Statuses (registry lifecycle)

VERIFIED / PARTIALLY_VERIFIED / UNVERIFIED / CONFLICTED /
INACTIVE / SUSPENDED / DELISTED / PENDING_REVIEW. These live on
companies and securities. They are NOT the same as the Phase 5
market-data quality vocabulary, though the words overlap; the
registry statuses describe identity/lifecycle evidence, not price
observations.

## Verification rules (evidence-driven, in verification.py)

- VERIFIED (CORRECTED after the independent audit, finding H1):
  evidence from at least TWO DISTINCT sources agrees on the
  normalized name AND at least one of those sources is OFFICIAL
  — `psx_official` or `secp` (a code-level constant, so a source
  cannot promote itself by editing a database row).
  The ORIGINAL rule — one official evidence row suffices — was
  unsafe and is superseded: the importer writes the evidence row
  from the very record it imports, so a lone official row agrees
  with itself trivially, and source_key is caller-supplied with
  no provenance check. A mislabelled collector could therefore
  mint VERIFIED rows under the old rule. Corroboration is now
  mandatory. Until a source_key provenance control exists (a
  registry of trusted collectors, not just a caller-supplied
  string), VERIFIED must be read as "corroborated including an
  official-labelled source", not as independently confirmed by
  PSX/SECP themselves. That control is a Phase 5
  pre-population requirement.
- PARTIALLY_VERIFIED: evidence from at least two DISTINCT
  sources agrees on the normalized name (no official source
  needed).
- Evidence rows with an empty observed_name never count as
  agreeing: without an observed name there is nothing that
  agrees with the stored name.
- Lifecycle statuses (CONFLICTED, PENDING_REVIEW, SUSPENDED,
  DELISTED, INACTIVE) are never promoted. A lifecycle status is
  not a verification state.
- Otherwise the status is left untouched. The importer sets
  UNVERIFIED (clean new record), PENDING_REVIEW (ambiguous),
  CONFLICTED (identifier disagreement), or a stated lifecycle
  status. Verification never demotes a lifecycle/conflict status.
- One verified company does not verify the registry. A status
  is a presentation of the evidence rows that exist for that
  entity, nothing more.

## Policies

- Missing data: absent, never zero-filled, never estimated.
- Ambiguous records: kept original, PENDING_REVIEW, never
  auto-merged.
- Conflicts: kept side-by-side (existing row + quality report),
  never silently chosen or overwritten.
- Ticker changes: symbol_history row with effective date and
  source evidence; surrogate id unchanged.
- Previous names/tickers/identifiers: preserved with effective
  dates; never overwritten.
- Sector assignment: source taxonomy only; no canonical sector
  by guesswork; no sector assigned from a numeric code without
  a verified name mapping.
- Stale data: a snapshot's date is its date. A cached copy
  crawled 2026-01-25 is reported as 2026-01-25 data, not as
  current data, and is not used for population.
- Synthetic/test records: TEST ONLY, in tests and in the
  rolled-back live check. No test record exists in production
  tables (verified: 0 business rows after rollback).
