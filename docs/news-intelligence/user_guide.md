# User Guide (Deliverable 11)

## What the News Intelligence Engine is

A news layer over the PSX Intelligence project that collects
article metadata (never full article bodies), classifies it,
scores sentiment and impact separately, and answers questions
about stored news with source links. It does NOT give buy/sell
advice, price targets, or percentage impact estimates, and it
does NOT collect PSX announcements (permission pending) or live
news (outlet terms unreviewed).

## Pages

- **News Intelligence** (`/news-intelligence`): the article feed
  with filters (ticker, sentiment, category, source). Start here.
- **News impact** (`/news-intelligence/impact`): impact
  assessments, highest importance first. Importance is not a
  price prediction; a blank company relevance means "not
  applicable" (macro news), not zero.
- **News assistant** (`/news-intelligence/assistant`): ask a
  question. Examples that work: "Show me HUBC dividends",
  "Compare HUBC news with price movement", "What happened in
  Nishat Mills". A question like "Should I buy HUBC?" is always
  answered with uncertainty — the assistant never issues advice.

## Reading the results honestly

- **REVIEW status** on an article means it needs human review
  (ambiguous company match, ungrounded fact, or confidence below
  0.80). All rule-based fallback articles are REVIEW by design
  (fallback confidence caps at 0.70).
- **RULE_BASED** means the result came from deterministic rules,
  not from an AI model. No model has run yet (hardware unblocker
  pending); nothing here is presented as model output.
- **INSUFFICIENT_DATA** on a market reaction means the price
  history cannot support that window yet (only one trading date
  is stored). It is not a bug to fix by guessing prices.
- **Empty results** mean no stored rows match — not that nothing
  happened in the world. Coverage today is the stored seed set
  plus any processed articles, not universe-wide live news.
- **UNVERIFIED** quality status means the row has one source or
  no second agreeing source. Nothing here is VERIFIED, and no
  row claims otherwise.
