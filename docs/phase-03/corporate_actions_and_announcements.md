# Phase 3 — Corporate Actions and Announcements

## Corporate actions

Table: corporate_actions (append-only, security x event_date) +
dividends (1:1 detail: type cash/stock, amount, currency,
payment date, ex-date, record date on the action row).

- Splits, bonuses, rights, mergers are dated events with
  adjustment factors where the source provides them.
- Adjustment factors are STORED, not applied destructively:
  adjusted price series are derived views; the unadjusted series
  remains intact. This is what makes Phase 5's 'unadjusted unless
  a corporate-action methodology is validated' rule implementable.
- A dividend event gets exactly one dividends row; the 1:1
  unique constraint prevents double-counting across the tables.

## Announcements

Table: announcements (append-only) + raw_payloads (hash-addressed)
+ files on disk.

- Grain is not a single natural key: duplicate detection uses
  content_hash first, source URL second. A record with neither
  cannot be duplicate-checked and must be flagged for review.
- The database row stores title, dates, company/security links,
  document_url, document_hash and raw_payload_id — never PDF bytes.
- Corrections are new rows, never edits (immutability trigger).
- Announcement PDF URLs from psx-dps are claimed in that library's
  README and UNVERIFIED by a live run in this project (Phase 1
  gate). Phase 3 stores the reference fields; it does not verify
  the claim.

## News (for contrast)

Table: news — third-party reporting, distinct from announcements.
Same hash + provenance discipline, different provenance meaning:
an announcement is what the issuer/exchange published; news is
what someone else reported. Conflating them would corrupt both
Phase 9 (announcement-driven) and Phase 10+ (news-driven) analysis.
