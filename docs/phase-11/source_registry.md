# Phase 11 Source Registry

One row per candidate source in `news_sources`. `collection_policy` is
the gate; `collection_status` records what actually happened in this run.

| Key | Type | Policy | Status | Terms / access note |
|---|---|---|---|---|
| psx_announcements | official | TERMS_GATED | not_collected | Systematic retrieval needs prior written PSX permission (PSX Terms of Use / Data Legal Notice; Phase 5 gate). DPS is discovery-only until that evidence exists. Collector refuses to run. |
| issuer_ir | official | ALLOWED_SAMPLED | collected_seed | Phase 7 matrix: sampled, internal analysis only, no republication. |
| rns_filing | official_filing | ALLOWED_SAMPLED | collected_seed | Phase 7 matrix: carrier, not author. |
| secp | regulator | ALLOWED_SAMPLED | not_collected | Public pages only, no bulk route, no paid eServices account. No seed events from SECP in this run. |
| sbp | official | ALLOWED | collected_seed | Phase 10 direct reads established. |
| pbs | official | ALLOWED | collected_seed | Phase 10 direct reads established. |
| reputable_news | secondary | NOT_COLLECTED | not_collected | Excerpt policy would allow headline + URL + short summary only, but no outlet's terms have been reviewed in this run. |
| social_rumour | secondary | NOT_COLLECTED | not_collected | Excluded by the brief: rumours and commentary are never events. |

## Excerpt limits (enforced by schema)

- Headline: max 500 chars. Summary: max 280 chars. Canonical URL and
  publisher stored. Content hash (SHA-256 of normalized headline + URL)
  is the duplicate key. There is no article-body column, so full
  copyrighted text cannot be stored even by accident.

## What was NOT collected, with exact unblockers

- PSX announcements: written PSX permission evidence, verified for its
  exact terms.
- Reputable news: per-outlet terms review for at least one outlet.
- SECP announcements: a documented SECP announcements route (public
  pages only).
- Wider company coverage: Phase 7 expansion beyond the 3-company sample.
- HBL events: HBL CY2025 statements (live-browser PDF download, then a
  Phase 7 load, then a Phase 11 re-run).
