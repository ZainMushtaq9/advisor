# API Documentation (Deliverable 10)

Base: `/api/v1` (same router as the rest of the app). All six
endpoints are GET-only. No endpoint writes anything, and no
endpoint issues a buy/sell signal, a percentage impact, or a
target price. An unknown ticker returns 404; a known ticker with
no rows returns 200 with empty lists and a `no_inputs`-style note.

## GET /news-intelligence/feed

Filters (all optional): `ticker`, `sector`, `source`
(source_key), `sentiment` (positive/negative/neutral/mixed),
`event_category`, `published_after` (ISO-8601; invalid value -> 400),
`min_importance` (float), `limit` (default 50, max 200).
Response: `{scope_note, articles: [...]}`. Each article carries
title, source, canonical_url, published_at, summary (<=280
chars), processor, status, quality_status, sentiment, category,
scores, tickers, sectors, importance and credibility scores.
Filters apply before ordering (newest first, dateless last).

## GET /news-intelligence/companies/{ticker}/news

Response: `{ticker, company_name, articles, phase11_events,
market_reactions, note}`. Market reactions carry status and
returns; on the current single price date they are
INSUFFICIENT_DATA with the reason — the note states correlation
is not causality.

## GET /news-intelligence/impact

Response: `{scope_note, impacts: [...]}` ordered by importance
descending (max 100). Dimensions are separate fields:
importance_score, credibility_score, credibility_class,
company_relevance (null = not applicable), sector_relevance
(null = not applicable), market_relevance, horizon, confidence,
status, counterarguments (conflicting coverage preserved).

## GET /news-intelligence/assistant?q=

Response: `{answer_kind, answer_text, citations, retrieval,
note}`. `retrieval` is always `FULL_TEXT_FALLBACK`.
`answer_kind` is one of direct_evidence / comparison /
uncertainty / missing_data. Recommendation questions return
uncertainty with no signal. missing_data returns NO citations.
Every factual claim in a direct_evidence answer carries a
citation (title, source, canonical_url, published_at); a stored
row with an empty canonical_url renders as "no stored link".

## GET /news-intelligence/sources

Response: `{sources: [...], gate_note}`. Every source with its
collection_policy and terms_note. A listed source is not an
integrated source. DPS is TERMS_GATED with the gate evidence in
the permission register.

## GET /news-intelligence/quality

Response: `{collection_runs_by_source, articles_by_status,
freshness_note}`. Freshness: current <= 1 day, recent <= 7 days,
stale beyond; missing or future-dated publication dates are
"unknown", never "current".
