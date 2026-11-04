# Phase 4 — API Documentation

Base: `/api/v1`. All endpoints are read-only (GET). No endpoint
writes, and no endpoint returns data that is not in the database.
When no database is configured, endpoints answer 503 with a
truthful reason, never a fake empty registry.

## Endpoints

| Method & path | Purpose | Query params |
|---|---|---|
| GET /companies | List companies | search (legal-name substring), status, sector_id, sort=id\|legal_name, skip, limit |
| GET /companies/{id} | One company + securities count | — |
| GET /companies/{id}/securities | Securities of one company | skip, limit |
| GET /securities | List securities | ticker (substring), status, company_id, sort=id\|ticker, skip, limit |
| GET /securities/{id} | One security + company name | — |
| GET /sectors | List sectors (source taxonomies kept separate) | source, skip, limit |
| GET /registry/statistics | Live totals + by-status counts + evidence rows | — |
| GET /registry/quality | By-status counts, pending/conflicted/verified counts, interpretation note | — |
| GET /registry/sources | data_sources rows + sync configs (manual-only note) | — |
| GET /data/universe | Central-universe summary: counts, provenance, freshness, validation counts, scope limitations — never a ticker list, never a CSV dump | — |

## Pagination and validation

- Default limit 50, maximum 200. limit outside 1..200 or
  skip < 0 returns 422. Unknown company/security ids return 404.
- Status filters are upper-cased before comparison, matching
  the stored vocabulary.

## Response notes

- Every list returns `total`, `skip`, `limit`, `items`.
- Sector rows carry `source` and `source_sector_name` verbatim
  and `canonical_sector_id` (null unless a verified mapping
  exists), with a note explaining that taxonomies are separate.
- Statistics carries the note: "Counts are live database counts.
  Zero means the registry is empty, not that the market is empty."
- Quality carries the interpretation of VERIFIED /
  PARTIALLY_VERIFIED in full, so a consumer cannot mistake an
  import success for verification.

## Verified behaviour (live-PostgreSQL check, 2026-11-04)

All 9 endpoints returned 200 on the live (empty) database;
unknown ids returned 404; limit=999 returned 422; statistics
returned companies=0, securities=0. See test_report.md.

## Completion addendum (2026-11-04, phase-04-completion branch)

GET /data/universe was added on the completion branch and
live-verified against the populated registry: 200 with
companies=470, securities=470, sectors=37, evidence_rows=940,
sources=[dps_listing_status_2026-11-04_main_board_normal_counter],
companies_by_status={UNVERIFIED: 470}, no ticker list in the
response. See phase_04_completion_2026-11-04.md.
