# Phase 5 commit readiness — 2026-11-04 (NOT committed)

This note records what is ready for a future controlled ingest and
what still blocks it. Nothing in this note authorises a commit.

## Ready now

- Mapped input file (registry scope only, one day 2026-11-03):
  `docs/phase-05/source_files/mktsum_2026-11-03_registry_mapped.csv`
  — verified gitignored (`.gitignore` line 40, `*.csv`), so it can
  never be committed to a public branch by accident. Source:
  DPS Market Summary (Closing) for 2026-11-03, file closing11.lis
  inside the downloaded ZIP. Mapping: Open/High/Low/Close/Volume
  from the source file; previous_close, turnover and
  source_timestamp left BLANK (the source's extra field is
  unverified and must not be stored). Futures rows excluded;
  registry scope only.
- Dry-run validation through the engine's own pure functions
  (2026-11-04 ~3:55 PM PKT): 457 input, 444 validated, 13
  rejected (12 ohlc_inconsistency, 1 non_positive_price SASML),
  0 unknown tickers, all 444 would be UNVERIFIED, freshness
  CURRENT. Full detail in `dps_downloads_inspection_2026-11-04.md`.
- Branch: `phase-05-snapshot-import` at `94f5822`. No commit of
  this package has been made.

## Still blocking a commit — BOTH must clear

1. **PSX Terms basis in writing.** Re-read 2026-11-04 (DPS footer
   Terms of Use and PSX Data Legal Notice, plus
   psx.com.pk/psx/terms-of-use): systematic retrieval to create
   databases, and any dissemination/transmission/sale/commercial
   use of market data without the respective rights/licence, are
   prohibited without prior written permission. The only allowance
   found is one copy of a single document for personal,
   non-commercial use. A permission request DRAFT is ready at
   `psx_permission_request_DRAFT.md` — it has NOT been sent.
   Sending it is the user's decision.
2. **Production database reachable.** No PostgreSQL server exists
   in this VM session (connection refused on port 5432, no server
   binaries installed), so the real CLI dry-run and count
   verification could not be re-run. Recovery path, pending the
   user's decision: install PostgreSQL 16 via apt and restore
   from `storage/backups/2026-11-04T1154-PKT/` (manifest hash
   verification first; restore script defaults to a separate
   restore-test database and refuses live-target overwrites
   without an explicit flag). Even after a restore, gate 1 still
   blocks any commit.

## What a future commit would store (once both gates clear)

444 UNVERIFIED daily rows for 2026-11-03 under source key
`dps_market_summary_2026-11-03`, is_adjusted=False. The 13 absent
registry symbols and 13 rejected rows must be reported alongside
it, never zero-filled. Phase 5 would still be scoped to this one
day and this registry view — not full-market, not KSE-100, not
VERIFIED.
