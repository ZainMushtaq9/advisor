# Phase 11 Taxonomy, Dedup and Scoring

## Taxonomy (brief list, verbatim)

earnings, dividends, rights, bonus, buyback, board_changes, litigation,
regulatory_notice, plant_outage, contract, merger, rating,
policy_change, macro_release.

Seed mappings (documented, not invented):
- Phase 7 `annual_report` / `quarterly_report` / `interim_filing` /
  `half_yearly` → `earnings` (results publication).
- Phase 7 `disclosure` → `regulatory_notice`.
- Phase 10 macro event types (`mpc_meeting`, `mpc_minutes`,
  `cpi_release`, `gdp_release`, `budget`) → `macro_release`.

Official disclosures and third-party commentary are separated by
`source_type` (official / official_filing / regulator / secondary),
never by headline wording.

## Dedup

- `content_hash` = SHA-256(normalized headline + "|" + canonical URL).
  The unique partial index enforces one row per hash.
- `canonical_key` = (primary company or "macro") | event type | date
  or "unknown" | headline core (normalized, suffix-stripped, first 80
  chars). Two items sharing a key are the same underlying event; the
  second becomes a syndicated/coverage link (`news_event_links`), never
  a second event row. Links never merge rows.

## Scoring (documented weights, no sentiment)

score = 0.4·reliability + 0.3·relevance + 0.2·novelty + 0.1·transmission.

| Input | Values |
|---|---|
| reliability | official 1.0, official_filing 0.95, regulator 0.9, secondary 0.6 |
| relevance | company 1.0, macro 0.5 |
| novelty | first 1.0, repeat 0.2 |
| transmission | direct 1.0, macro 0.5 |

A score means review-worthiness and breadth of relevance. It is never
a price signal and never a buy/sell signal (Phase 15 owns proposals).

## Review rules

- Future-dated macro calendar items → `scheduled`.
- Date unknown → `pending_review` (a date is never guessed).
- Ambiguous match, or confidence < 0.8 → `pending_review`.
- Score ≥ 0.8 (high-impact) → `pending_review`.
- Otherwise → `ok`.

Seed run review outcome: 5 pending_review (3 earnings + 2 past macro
events at the 0.8 boundary) and 2 scheduled (future macro events).
No seed event reached `ok`, because every earnings event scores ≥ 0.98
and every past macro event scores exactly 0.8 — the rules working as
designed, not a defect.
