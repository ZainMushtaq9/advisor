"""Phase 11 news/event tests (pure: no real database, no network).

Hand-checked expectations:
- Normalization follows the Phase 4 rule exactly: suffixes strip
  repeatedly, abbreviations are NOT expanded, tokens are NOT merged.
- The resolver never matches a ticker substring (HBL inside HBLXYZ),
  never resolves a generic word alone (PAKISTAN), and never matches a
  LEAP-style expanded name (INDUSTRIES) against an IND registry name.
- A shared alias is capped at 0.50 and flagged ambiguous.
- Dedup groups the same underlying event and separates different dates.
- Scoring is a documented weighted sum; review rules force review for
  unknown dates, low confidence, ambiguity and high-impact scores.
- The PSX collector refuses to run (TERMS_GATED), always.
- No article-body column exists anywhere in the Phase 11 schema, and
  every seed summary fits the 280-char cap.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.models.news_events import NewsEvent
from app.services.news_events import SEED_SUMMARIES
from app.services.news_events.aliases import (
    build_alias_index,
    generate_aliases,
    normalize,
    strip_suffixes,
)
from app.services.news_events.collectors import (
    GatedPsxCollector,
    PolicyBlocked,
    build_seed_events,
    source_for_document,
)
from app.services.news_events.dedup import canonical_key, content_hash, headline_core
from app.services.news_events.resolver import resolve_text
from app.services.news_events.scoring import review_status, score_event


def test_normalize_and_suffix_strip():
    assert normalize("Agha Steel Ind.Ltd") == "AGHA STEEL IND LTD"
    assert strip_suffixes("AGHA STEEL IND LTD") == "AGHA STEEL IND"
    assert strip_suffixes("THE HUB POWER COMPANY LIMITED") == "THE HUB POWER"
    # No token merging: D.G. stays two tokens.
    assert normalize("D.G. Khan Cement") == "D G KHAN CEMENT"
    # Parenthetical survives normalization (dropped only as a variant).
    assert normalize("Abbott Laboratories (Pakistan) Limited") == (
        "ABBOTT LABORATORIES PAKISTAN LIMITED"
    )


def test_generate_aliases_hubc_and_agha():
    hubc = dict(
        (a, (t, c)) for a, t, c in generate_aliases("The Hub Power Company Limited", "HUBC")
    )
    assert hubc["HUBC"] == ("TICKER", 1.0)
    assert hubc["THE HUB POWER COMPANY LIMITED"] == ("LEGAL", 0.95)
    assert hubc["THE HUB POWER"] == ("LEGAL_STRIPPED", 0.85)
    agha = dict((a, (t, c)) for a, t, c in generate_aliases("Agha Steel Ind.Ltd", "AGHA"))
    assert agha["AGHA STEEL IND"] == ("LEGAL_STRIPPED", 0.85)
    # No expanded alias is ever generated.
    assert "AGHA STEEL INDUSTRIES" not in agha
    assert "AGHA STEEL INDUSTRIES LIMITED" not in agha


def test_shared_alias_capped_and_flagged():
    index = build_alias_index(
        [
            (1, "ABC Limited", "ABC"),
            (2, "ABC Ltd", "ABC2"),
        ]
    )
    rows = index["ABC"]
    assert len({r[0] for r in rows}) == 2
    assert all(r[2] == 0.50 and r[3] is True for r in rows)


def _sample_index():
    return build_alias_index(
        [
            (289, "The Hub Power Company Limited", "HUBC"),
            (99, "Agha Steel Ind.Ltd", "AGHA"),
            (277, "Habib Bank Limited", "HBL"),
        ]
    )


def test_resolver_exact_matches_only():
    index = _sample_index()
    matches = resolve_text("HUBC results beat estimates", index)
    assert [m["company_id"] for m in matches] == [289]
    assert matches[0]["alias_type"] == "TICKER"
    # Ticker substring must not match.
    assert resolve_text("HBLXYZ announced a deal", index) == []
    # Generic word alone must not resolve.
    assert resolve_text("PAKISTAN", index) == []
    # LEAP expanded name must not match via any NAME alias (no
    # abbreviation expansion). It still matches via the AGHA ticker
    # token, which is a legitimate exact token match, not an expansion.
    expanded = resolve_text("AGHA STEEL INDUSTRIES LIMITED", index)
    assert all(m["alias_type"] == "TICKER" for m in expanded)
    assert resolve_text("STEEL INDUSTRIES LIMITED", index) == []
    # Registry name itself matches.
    matches = resolve_text("Agha Steel Ind.Ltd reports", index)
    assert [m["company_id"] for m in matches] == [99]
    # Empty text matches nothing.
    assert resolve_text("", index) == []


def test_dedup_keys_and_hash():
    base = canonical_key(289, "earnings", "2026-09-21", "HUBCO Integrated Annual Report 2026")
    same = canonical_key(289, "earnings", "2026-09-21", "HUBCO Integrated Annual Report 2026!")
    assert base == same
    assert (
        canonical_key(289, "earnings", "2026-09-22", "HUBCO Integrated Annual Report 2026") != base
    )
    assert (
        canonical_key(403, "earnings", "2026-09-21", "HUBCO Integrated Annual Report 2026") != base
    )
    assert canonical_key(None, "macro_release", "2026-10-26", "SBP decision") != base
    h1 = content_hash("Title", "https://example.com/a")
    assert h1 == content_hash("title", "https://example.com/a")
    assert h1 != content_hash("Title", "https://example.com/b")
    assert headline_core("Agha Steel Ind.Ltd") == "AGHA STEEL IND"


def test_scoring_and_review_rules():
    assert score_event("official", "company", "first", "direct") == 1.0
    assert score_event("secondary", "macro", "first", "macro") == 0.64
    today = date(2026, 11, 4)
    assert (
        review_status(
            confidence=1.0,
            ambiguous=False,
            date_status="known",
            score=0.5,
            event_date=date(2026, 9, 21),
            today=today,
        )
        == "ok"
    )
    assert (
        review_status(
            confidence=1.0,
            ambiguous=False,
            date_status="unknown",
            score=0.5,
            event_date=None,
            today=today,
        )
        == "pending_review"
    )
    assert (
        review_status(
            confidence=0.5,
            ambiguous=False,
            date_status="known",
            score=0.5,
            event_date=date(2026, 9, 21),
            today=today,
        )
        == "pending_review"
    )
    assert (
        review_status(
            confidence=1.0,
            ambiguous=True,
            date_status="known",
            score=0.5,
            event_date=date(2026, 9, 21),
            today=today,
        )
        == "pending_review"
    )
    assert (
        review_status(
            confidence=1.0,
            ambiguous=False,
            date_status="known",
            score=0.9,
            event_date=date(2026, 9, 21),
            today=today,
        )
        == "pending_review"
    )
    assert (
        review_status(
            confidence=1.0,
            ambiguous=False,
            date_status="known",
            score=0.5,
            event_date=date(2026, 12, 14),
            today=today,
        )
        == "scheduled"
    )
    with pytest.raises(KeyError):
        score_event("rumour", "company", "first", "direct")


def test_psx_collector_refuses():
    with pytest.raises(PolicyBlocked, match="TERMS_GATED"):
        GatedPsxCollector().run()


def test_source_for_document():
    assert (
        source_for_document("http://www.rns-pdf.londonstockexchange.com/rns/x.pdf") == "rns_filing"
    )
    assert source_for_document("https://hubpower.com/wp-content/uploads/x.pdf") == "issuer_ir"
    assert source_for_document(None) == "issuer_ir"


def test_seed_builder_shapes_and_skips():
    docs = [
        {
            "id": 13,
            "company_id": 289,
            "ticker": "HUBC",
            "document_type": "annual_report",
            "title": "HUBCO Integrated Annual Report 2026",
            "source_url": "https://hubpower.com/x.pdf",
            "company_name": "The Hub Power Company Limited",
        },
        {
            "id": 14,
            "company_id": 394,
            "ticker": "NML",
            "document_type": "quarterly_report",
            "title": "Nishat Mills 3rd Quarter Report 2025",
            "source_url": "https://nishatmillsltd.com/x.pdf",
            "company_name": "Nishat Mills Limited",
        },
        {
            "id": 8,
            "company_id": 747,
            "ticker": "HBL",
            "document_type": "annual_report",
            "title": "HBL Annual Report 2025",
            "source_url": "https://www.hbl.com/assets/documents/HBL_Annual_Report_2025.pdf",
            "company_name": "Habib Bank Limited",
        },
        {
            "id": 99,
            "company_id": 1,
            "ticker": "XXX",
            "document_type": "mystery_type",
            "title": "Mystery",
            "source_url": None,
            "company_name": "X",
        },
    ]
    macros = [
        {
            "id": 1,
            "event_date": "2026-10-26",
            "event_type": "mpc_meeting",
            "title": "SBP decision",
            "quality_status": "VERIFIED",
        },
        {
            "id": 9,
            "event_date": "2026-11-01",
            "event_type": "alien_type",
            "title": "Alien",
            "quality_status": "UNVERIFIED",
        },
    ]
    events, skipped = build_seed_events(docs, macros)
    assert len(events) == 4  # 3 docs + 1 macro; 2 skipped
    assert len(skipped) == 2
    hubc = next(e for e in events if e["document_id"] == 13)
    assert hubc["event_date"] == "2026-09-21" and hubc["date_status"] == "known"
    assert hubc["source_key"] == "issuer_ir"
    nml = next(e for e in events if e["document_id"] == 14)
    assert nml["event_date"] is None and nml["date_status"] == "unknown"
    # HBL resolves by ticker (never by document id, which shifts).
    hbl = next(e for e in events if e["document_id"] == 8)
    assert hbl["event_date"] == "2026-03-03" and hbl["date_status"] == "known"
    assert hbl["summary"] is not None and "66,763,916" in hbl["summary"]
    macro = next(e for e in events if e["macro_event_id"] == 1)
    assert macro["event_type"] == "macro_release" and macro["primary_company_id"] is None
    assert macro["quality_status"] == "VERIFIED"


def test_no_body_column_and_summary_caps():
    columns = {c.name for c in NewsEvent.__table__.columns}
    assert "body" not in columns
    assert "article_text" not in columns
    assert "content" not in columns
    assert all(len(s) <= 280 for s in SEED_SUMMARIES.values())
