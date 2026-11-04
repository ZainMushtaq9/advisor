# Phase 11 Implementation Specification — News, Corporate Announcements and Event Intelligence

Brief: playbook lines 964–1023. Verdict: **PARTIALLY COMPLETE**.

## Entry dependency, as found

- Phase 4 registry: 470 companies, 470 securities, all UNVERIFIED. The
  brief says "verified registry"; in this codebase that means the Phase 4
  registry as the authority for names/tickers, NOT H1-verified rows.
  Alias and event rows inherit UNVERIFIED status from their inputs.
- Phase 7 disclosures: 3 documents (HUBC annual, NML quarterly, OGDC
  interim). Phase 10 macro event registry: 4 events.
- Phase 5 Terms gate: OPEN. No written PSX permission evidence exists.

## What was built

| Piece | Location |
|---|---|
| Models (5 tables) | `backend/app/models/news_events.py` |
| Migration 0008 (head) | `database/migrations/versions/20261104_0008_phase_11_news_events.py` |
| Service | `backend/app/services/news_events/` (`__init__`, `aliases`, `resolver`, `dedup`, `scoring`, `collectors`, `runner`) |
| CLI | `scripts/run_news_events.py` (--dry-run / --commit) |
| API (GET-only) | `backend/app/api/v1/endpoints/news.py` (`/news`, `/news/sources`, `/news/aliases`, `/news/quality`) |
| Tests | `backend/tests/test_news_events_phase11.py` (10 tests, pure) |

The Phase 3 `news` table is intentionally NOT reused or altered: it has
no company link, taxonomy, source type, summary cap, match evidence or
review status, and holds 0 rows. Phase 11 writes only to its own tables.

## Tables

- `news_sources`: source registry with `collection_policy`
  (ALLOWED / ALLOWED_SAMPLED / TERMS_GATED / NOT_COLLECTED) and
  `collection_status` (collected_seed / not_collected).
- `company_aliases`: (company_id, alias_normalized) unique; confidence;
  `is_ambiguous` flag.
- `news_events`: one row per UNDERLYING event, not per article.
  `event_date` NULL exactly when unknown; `canonical_key` unique;
  `content_hash` unique partial index; `summary` capped at 280 chars;
  NO article-body column exists anywhere (copyright discipline is
  structural); NO sentiment column exists (the brief forbids treating
  sentiment as a factual event).
- `news_event_companies`: event↔company links with match evidence.
- `news_event_links`: syndicated / duplicate / coverage links. Links
  never merge rows.

## Collection policy (the gate that shapes this phase)

- PSX announcements: TERMS_GATED. The collector is a stub that raises
  `PolicyBlocked` on every run. No PSX fetch happens in this phase.
- Issuer IR pages, RNS filings: ALLOWED_SAMPLED (Phase 7 matrix).
- SBP, PBS: ALLOWED (Phase 10 direct reads established).
- SECP public pages: ALLOWED_SAMPLED, registry-only in this run.
- Reputable news: NOT_COLLECTED (per-outlet terms unreviewed).
- Social/rumour: NOT_COLLECTED (excluded by the brief).

## Seed events (the only events in this run)

Derived ONLY from rows already in the database. No HTTP fetch.

| # | Event | Company | Date | Source | Review |
|---|---|---|---|---|---|
| 1 | HUBCO Integrated Annual Report 2026 (earnings) | HUBC 289 | 2026-09-21 (auditor-report date proxy) | issuer_ir | pending_review (score 1.0 ≥ 0.8) |
| 2 | Nishat Mills 3rd Quarter Report 2025 (earnings) | NML 394 | unknown (NULL in Phase 7) | issuer_ir | pending_review (date unknown) |
| 3 | OGDC interim statements, 6M to 31 Dec 2025 (earnings) | OGDC 403 | 2026-02-23 (RNS date) | rns_filing | pending_review (score 0.98 ≥ 0.8) |
| 4 | SBP MPC decision: rate to 12% (macro_release) | — | 2026-10-26 | sbp | pending_review (score 0.8, boundary) |
| 5 | PBS October 2026 inflation report (macro_release) | — | 2026-11-02 | pbs | pending_review (score 0.8, boundary) |
| 6 | SBP MPC minutes due (macro_release) | — | 2026-11-20 | sbp | scheduled (future) |
| 7 | SBP MPC meeting scheduled (macro_release) | — | 2026-12-14 | sbp | scheduled (future) |

Seed event quality carries the input's status: document events
UNVERIFIED; macro events carry their Phase 10 quality (VERIFIED,
PARTIALLY_VERIFIED, UNVERIFIED, PARTIALLY_VERIFIED respectively).

## Audit notes (corrections made during this run)

1. **API session bug (found by the live check, fixed):** the first
   `/news` endpoint version passed the FastAPI `Request` object to
   `get_session_factory()` instead of `request.app.state.engine`,
   producing a 500. Fixed to the Phase 10 pattern; all endpoints then
   returned 200 (404 for an unknown ticker).
2. **Test correction (test was wrong, code was right):** the resolver
   test expected no match for "AGHA STEEL INDUSTRIES LIMITED", but the
   text contains the standalone AGHA ticker token, which legitimately
   matches. The test now asserts the precise property: no NAME-alias
   match (no abbreviation expansion), ticker-token match allowed.
3. **Ambiguity is real, not theoretical:** 10 aliases collide across
   two companies each (see `alias_map_method.md`), mostly ordinary vs
   preference/rights classes of the same issuer. Bare-name matches for
   those aliases are capped at 0.50 and forced to review; only the
   ticker disambiguates them.

## Gate assessment (brief acceptance gate)

- News matches coverage across the verified security universe: FAIL —
  3/470 companies + 4 macro events. Needs PSX announcements
  (TERMS_GATED) and per-outlet terms review.
- False positives and ambiguous aliases tested: PASS (10 resolver
  tests, incl. ticker substrings, generic words, non-expansion,
  ambiguity capping).
- Official and secondary sources distinguished: PASS (source_type on
  every event and source row).
- No copyrighted article corpus redistributed: PASS (no body column,
  280-char summary cap, no full text collected).

Verdict: PARTIALLY COMPLETE. The framework, resolver, taxonomy, dedup,
scoring, APIs and seed feed are complete and verified; universe-wide
live coverage is blocked as stated.
