# News Source Inventory (Deliverable 1)

Status: PARTIALLY COMPLETE — inventory written; integration state per
source is in the permission register (Deliverable 2). A source being
listed here does NOT mean it is integrated.

## Sources in the Phase 11 registry (verified from `news_sources`, 8 rows)

| source_key | type | Phase 11 policy | Engine collection state |
|---|---|---|---|
| psx_announcements | PSX/DPS announcements | TERMS_GATED | BLOCKED — never collected from |
| sbp | SBP press releases | ALLOWED (manual reads) | NOT auto-collected — no automated fetch approved |
| pbs | PBS press releases | ALLOWED (manual reads) | NOT auto-collected — same reason |
| issuer_ir | Company IR pages | ALLOWED_SAMPLED | NOT auto-collected — sampled manual only |
| rns_filing | RNS filings | ALLOWED_SAMPLED | NOT auto-collected — sampled manual only |
| secp | SECP public pages | ALLOWED_SAMPLED | NOT auto-collected — no bulk route, no paid account |
| reputable_news | Business press | NOT_COLLECTED | NOT_COLLECTED — per-outlet terms unreviewed |
| social_rumour | Social / rumour | NOT_COLLECTED | EXCLUDED by brief, permanently |

## Candidate outlets reviewed for future integration (not integrated)

Business Recorder, Dawn Business, Mettis Global, Profit, Reuters.
Third-party reports note free RSS feeds for Business Recorder and
Dawn Business; those reports are NOT direct verification of terms,
robots.txt, or RSS permission, so all five stay NOT_COLLECTED until
a per-outlet review (terms + robots.txt + RSS permission) is
recorded. No feed was fetched, parsed, or stored in this work.

## Competitor platforms reviewed (research only, public features)

PSX Invest, Sarmaaya/Zar, Investify, Zaryaab, PSX Swing, Capitalist.
Feature matrix in the implementation plan. No proprietary code,
branding, protected content, or private data was copied. Deliberate
non-goals (not gaps): executable BUY/SELL signals with targets and
stops, paid tiers, WhatsApp/external delivery, demo trading, live
prices.
