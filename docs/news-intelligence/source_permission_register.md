# Source Permission and Compliance Register (Deliverable 2)

Status: PARTIALLY COMPLETE — register written and enforced in code;
per-outlet news terms remain unreviewed (see below). Enforcement is
not advisory: `collection_allowed()` in
`backend/app/services/news_intelligence/collection.py` raises
`PolicyBlocked` unless policy == `COLLECTABLE` AND automated
fetching is approved, and the CLI `enforce` command records every
refusal in `news_collection_runs`.

## DPS / PSX announcements — BLOCKED (permission)

Evidence (verified in this project, not assumed):

- PSX Terms of Use + PSX Data Legal Notice (re-read 2026-11-04):
  systematic retrieval to create collections/compilations/databases
  is prohibited except with prior written permission; automated
  access is prohibited except via generally available third-party
  browsers, unless prior written permission; redistribution /
  republication / dissemination / sale / commercial use of Market
  Data without acquiring the respective rights/licence is strictly
  prohibited. Contact: marketdatarequest@psx.com.pk.
- Permission request sent 2026-11-04 16:58:19 PKT from
  zainmushtaq5439@gmail.com to marketdatarequest@psx.com.pk
  (Gmail message/thread `1a1a66ca3ef85eeb`; sending proves
  neither delivery nor reading).
- The user later reported a reply had arrived and that they
  permanently deleted it, including from trash — verified
  unrecoverable; wording unverifiable. The user declined a resend
  (2026-11-04 18:58 PKT) and took the permission side onto
  themselves.
- Current state: Terms gate NOT cleared, owned by the user. No PSX
  email is sent without a new user instruction. A reply-watch cron
  (`psx-permission-reply-watch`, every 6h) checks 5439 for
  `from:psx.com.pk`; only a reply from that sender counts.

Consequence: no live DPS announcement collection is implemented,
and no mirror, cache, or "just a little" collection is used — that
would still be systematic retrieval. The Phase 11 PSX collector
remains a gated stub raising `PolicyBlocked`.

## Other sources

| Source | Position | Exact unblocker |
|---|---|---|
| SBP / PBS press releases | Manual official reads ALLOWED (Phase 10 precedent). Automated collection PAUSED. | A documented approval for automated fetching of those pages. |
| SECP public pages | Sampled manual reads only. No bulk route established; the paid Rs. 100 eServices account is explicitly NOT used. | A documented public announcements route. |
| Finance Division | UNVERIFIED — no prior evidence, no collection. | A terms + publication-route review. |
| Issuer IR pages | ALLOWED sampled, manual only, internal analysis only, no republication (Phase 7 matrix). Automated polling NOT approved. | An approval for automated issuer-page polling. |
| Business Recorder / Dawn Business / Mettis Global / Profit / Reuters | NOT_COLLECTED — terms unreviewed. | Per-outlet terms + robots.txt + RSS-permission verification, recorded here. |
| Social / rumour channels | EXCLUDED by the Phase 11 rule, carried forward. | None — no unblocker is sought. |

## Copyright discipline (structural)

- No article-body column exists anywhere in the engine
  (models, migration 0025, API, CLI). Titles (<=500 chars),
  summaries (<=280 chars), canonical URLs, and content hashes only.
- Summaries are capped excerpts with canonical links, within
  applicable rights; full copyrighted articles are never stored or
  redistributed.
- HTML scraping is NOT implemented: no current register entry
  permits it. Adding it needs its own permission review.

## Scratch enforcement evidence (2026-11-05)

CLI `enforce --commit` on the scratch database checked all 8
registered sources and recorded 8 refused runs (one per source).
Note: no registered source currently holds the `COLLECTABLE`
policy — Phase 11 `ALLOWED` means manual reads, not automated
collection — so automated collection refuses everything by design.
That strictness is intentional: an `ALLOWED` label must never be
misread as an automated-fetch approval.
