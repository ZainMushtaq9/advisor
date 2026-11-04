"""Phase 11 news / event intelligence: source registry, taxonomy, seed
definitions, scoring rules.

Read the brief first: playbook lines 964-1023 (Phase 11 of 30).

What this run does NOT do, by policy:
- No live PSX announcement collection. The Phase 5 Terms gate (systematic
  retrieval needs prior written PSX permission) covers PSX announcements
  exactly, and no permission evidence exists. The PSX collector exists
  only as a gated stub that refuses to run.
- No live news-site collection. Per-outlet terms are unreviewed, so
  reputable news is registry-only in this run.
- No full article text, ever: the schema has no body column, summaries
  are capped at 280 chars, and no sentiment is stored (the brief forbids
  treating sentiment as a factual event).

What this run DOES do, from already-stored rows only:
- A source registry with a per-source collection policy.
- A deterministic alias map generated from the 470-company registry
  (no abbreviation expansion, no token merging, no fuzzy matching).
- A resolver, a taxonomy, dedup rules and scoring rules, all tested.
- Seed events derived ONLY from Phase 7 financial documents (3) and
  Phase 10 macro events (4) already in the database. No HTTP fetch.

Coverage honesty: seed events cover 3 of 470 companies plus 4
universe-wide macro events. The brief's acceptance item "news matches
coverage across the verified security universe" therefore FAILS in this
run, and the Phase 11 verdict is PARTIALLY COMPLETE, not COMPLETE.
"""

from __future__ import annotations

# ---------------------------------------------------------------- sources
# key: (name, publisher, source_type, collection_policy, base_url,
#       terms_note, collection_status)
SOURCES = {
    "psx_announcements": (
        "PSX Announcements (DPS)",
        "Pakistan Stock Exchange",
        "official",
        "TERMS_GATED",
        "https://dps.psx.com.pk/",
        "Systematic retrieval to create collections/databases needs prior "
        "written PSX permission (PSX Terms of Use / Data Legal Notice; "
        "Phase 5 gate). DPS is discovery-only until that evidence exists. "
        "Collector refuses to run without it.",
        "not_collected",
    ),
    "issuer_ir": (
        "Issuer Investor-Relations Pages",
        "issuers",
        "official",
        "ALLOWED_SAMPLED",
        None,
        "Phase 7 source matrix: issuer IR pages ALLOWED sampled, internal "
        "analysis only, no republication. Seed source for Phase 7 document "
        "events.",
        "collected_seed",
    ),
    "rns_filing": (
        "London Stock Exchange RNS Filings",
        "London Stock Exchange",
        "official_filing",
        "ALLOWED_SAMPLED",
        "https://www.londonstockexchange.com/",
        "Phase 7 source matrix: RNS filing ALLOWED (carrier, not author). "
        "Seed source for the OGDC interim filing event.",
        "collected_seed",
    ),
    "secp": (
        "SECP Public Pages",
        "Securities and Exchange Commission of Pakistan",
        "regulator",
        "ALLOWED_SAMPLED",
        "https://www.secp.gov.pk/",
        "Public pages only, no bulk route, no paid eServices account. "
        "Registry-only in this run; no seed events from SECP.",
        "not_collected",
    ),
    "sbp": (
        "State Bank of Pakistan",
        "State Bank of Pakistan",
        "official",
        "ALLOWED",
        "https://www.sbp.org.pk/",
        "Phase 10 direct reads established. Seed source for MPC events.",
        "collected_seed",
    ),
    "pbs": (
        "Pakistan Bureau of Statistics",
        "Pakistan Bureau of Statistics",
        "official",
        "ALLOWED",
        "https://www.pbs.gov.pk/",
        "Phase 10 direct reads established. Seed source for CPI events.",
        "collected_seed",
    ),
    "reputable_news": (
        "Reputable News Outlets (per-outlet terms pending)",
        "various",
        "secondary",
        "NOT_COLLECTED",
        None,
        "Brief excerpt policy would allow headline + URL + short summary "
        "only, but no outlet's terms have been reviewed in this run, so "
        "nothing is collected from news outlets here.",
        "not_collected",
    ),
    "social_rumour": (
        "Social Media / Rumour Channels",
        "various",
        "secondary",
        "NOT_COLLECTED",
        None,
        "Excluded by the brief: rumours and third-party commentary are never stored as events.",
        "not_collected",
    ),
}

# ---------------------------------------------------------------- taxonomy
# Brief taxonomy, plus two seed-only mappings:
# - financial_report publication -> "earnings" (results publication).
# - Phase 10 macro event types -> "macro_release".
EVENT_TYPES = (
    "earnings",
    "dividends",
    "rights",
    "bonus",
    "buyback",
    "board_changes",
    "litigation",
    "regulatory_notice",
    "plant_outage",
    "contract",
    "merger",
    "rating",
    "policy_change",
    "macro_release",
)

DOCUMENT_TYPE_TO_EVENT_TYPE = {
    "annual_report": "earnings",
    "quarterly_report": "earnings",
    "interim_filing": "earnings",
    "half_yearly": "earnings",
    "disclosure": "regulatory_notice",
}

MACRO_EVENT_SOURCE = {
    # Phase 10 macro event_type -> news source key.
    "mpc_meeting": "sbp",
    "mpc_minutes": "sbp",
    "cpi_release": "pbs",
    "gdp_release": "pbs",
    "budget": "pbs",
}

# Publication dates for the three Phase 7 documents, with evidence.
# HUBC: auditor report dated 21 Sep 2026 (Phase 7 run-1 report) — used
# as the publication proxy and labelled as such in the event note.
# OGDC: RNS publication date 2026-02-23 (Phase 9 report).
# NML: publication date NULL in the Phase 7 record — date unknown, and
# the event is forced to review rather than guessed.
PUBLICATION_DATES = {
    13: ("2026-09-21", "auditor report dated 21 Sep 2026 (publication proxy)"),
    14: (None, "publication date NULL in Phase 7 record; date unknown"),
    15: ("2026-02-23", "RNS publication date 2026-02-23"),
}

# ---------------------------------------------------------------- scoring
# Documented rule weights. score = 0.4*reliability + 0.3*relevance +
# 0.2*novelty + 0.1*transmission, all in [0, 1].
RELIABILITY = {
    "official": 1.0,
    "official_filing": 0.95,
    "regulator": 0.9,
    "secondary": 0.6,
}
RELEVANCE = {"company": 1.0, "macro": 0.5}
NOVELTY = {"first": 1.0, "repeat": 0.2}
TRANSMISSION = {"direct": 1.0, "macro": 0.5}

REVIEW_SCORE_THRESHOLD = 0.8  # high-impact events go to review
REVIEW_CONFIDENCE_THRESHOLD = 0.8  # low-confidence matches go to review

# What was NOT collected in this run, with the exact unblocker each.
NOT_COLLECTED = {
    "psx_announcements": "written PSX permission evidence, verified for its exact terms",
    "reputable_news": "per-outlet terms review for at least one outlet",
    "secp_announcements": "a documented SECP announcements route (public pages only)",
    "wider_company_coverage": "Phase 7 expansion beyond the 3-company sample",
    "hbl_events": "HBL CY2025 statements (live-browser PDF download, then Phase 7 load)",
}

# Seed summaries for the three Phase 7 documents, keyed by document id.
# Every figure below is already stored in Phase 7 (statements / line
# items); nothing here is new research. All summaries are <= 280 chars
# (the schema cap) and carry no sentiment and no recommendation.
SEED_SUMMARIES = {
    13: (
        "FY2026 consolidated audited results: net profit Rs 56,257,178 "
        "thousand; EPS Rs 38.26 basic / 35.56 diluted; auditor "
        "A. F. Ferguson & Co., unmodified opinion."
    ),
    14: (
        "Nine months ended 31 Mar 2025, consolidated condensed interim, "
        "unaudited: loss after tax Rs 1,182,815 thousand."
    ),
    15: (
        "Six months ended 31 Dec 2025, condensed interim consolidated, "
        "unaudited: profit after tax Rs 73,019,248 thousand; EPS Rs 16.98."
    ),
}

# HBL (Habib Bank Limited, company 277, COMMERCIAL BANKS) is PENDING.
HBL = 277
PENDING_COMPANIES = {
    HBL: "statements not yet loaded (HBL CY2025 PDF blocked at download)",
}
