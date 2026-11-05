# Known Limitations and Blockers (Deliverable 14)

## Blockers (with exact unblockers)

| Blocker | Unblocker |
|---|---|
| DPS/PSX systematic collection BLOCKED | Written PSX permission (user-owned gate; reply-watch cron active). No resend without a new user instruction. |
| Live local-model inference UNVERIFIED | Free RAM above ~3 GB (measured), Ollama install, <=1B Q4 open-weight model pull, latency/memory measurement on N=20. |
| Live collection from any source PAUSED | A documented automated-fetch approval per source (SBP/PBS manual precedent is not one). |
| Per-outlet news terms unreviewed | Per-outlet terms + robots.txt + RSS-permission review, recorded in the register. |
| Event-study windows INSUFFICIENT_DATA | More trading days (2 closes -> returns, 5 -> SMA(5), 11 -> forecast intervals, 30 -> volatility/beta/Sharpe/AR(1), 251 -> VaR/ES). |
| VERIFIED promotion unavailable | H1 second agreeing source incl. official + recorded human approval gate (none granted). |
| No VERIFIED local embedding model | A verified local embedding model + vector-retrieval evaluation (Phase 19 gap, unchanged). |

## Limitations (not blockers — design or data facts)

- All fallback articles are REVIEW by design (confidence caps at
  0.70 < 0.80 review line). The review queue is the quality gate
  until a verified model exists.
- Keyword taxonomy gaps (measured): "gas reserves discovery" and
  "expands" wording are not covered; "bonus"/"approves"/"eases"
  are not lexicon words. Coverage was deliberately NOT chased to
  fit the synthetic set — these are documented gaps for a future
  taxonomy review with a larger labelled set.
- Common-word ticker collisions: exact-token matching can match
  ordinary words that are also tickers (measured: "next week" ->
  NEXT). Mitigation is the REVIEW queue, not a fix in this work.
- Title-only seed items classify as "other": document titles are
  not news headlines; their Phase 11 types come from document_type.
- Macro seed documents have empty canonical_url: citations to
  them show "no stored link".
- `news_event_evidence` is empty: no article has been linked to a
  canonical Phase 11 event yet. The table and grain exist; the
  linking run is future work.
- Freshness "current" requires a publication date within 1 day;
  future-dated scheduled events (e.g. the 2026-12-14 MPC meeting)
  report "unknown", never "current".
- The Phase 11 frontend news page still describes "three company
  earnings events" — stale since the batch added HBL (4
  companies, 8 events). Flagged for the parent; not edited here
  because it belongs to Phase 11's page, not this engine.
- The readiness endpoint still hardcodes migration head 0023
  (pre-existing Phase 27 artifact, needs its own brief).
- Defects D-05 (stale event_brief figure) and D-12 (token-gated
  report approval) remain OPEN from the batch; neither is in this
  engine's scope.
