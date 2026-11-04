"""Phase 26 golden test suite: case definitions and checks.

Two check kinds:

- "pure": runs against current code with fixed inputs (name
  normalization, alias capping, QA citation rule). No DB, no
  network, fully reproducible.
- "stored": reads stored evaluation rows and asserts their
  recorded state (stored agent evaluations, stored decisions,
  stored registry status, stored summary lengths, stored HUBC
  close). Stored checks never re-run another phase's retrieval
  and never re-emit adversarial input text: the injection case
  reads the stored evaluation row's result and quarantine flag
  by case name only.

A failed golden case blocks promotion of every model it
touches (see promotion gates); it never blocks the evaluation
run itself from being recorded — a failed case is a finding,
not a reason to hide the run.
"""

from __future__ import annotations

from datetime import date

from app.services.news_events.aliases import build_alias_index
from app.services.news_events.resolver import resolve_text
from app.services.news_events.scoring import review_status
from app.services.registry.normalization import normalize_name
from app.services.reports import DISCLAIMER, TEMPLATES
from app.services.reports.validation import qa_draft

GOLDEN_CASES: list[dict] = [
    {
        "case_key": "golden_normalize_trailing_limited",
        "category": "source_matching",
        "input_desc": "Two legal names differing only by a trailing LIMITED suffix.",
        "expected_outcome": "Same normalized key: trailing LIMITED is stripped repeatedly.",
        "check_kind": "pure",
        "evidence": {"function": "normalize_name"},
    },
    {
        "case_key": "golden_normalize_and_conjunction",
        "category": "source_matching",
        "input_desc": "Two legal names differing only by '&' vs 'and'.",
        "expected_outcome": "Same normalized key: '&' and 'and' are both removed as words.",
        "check_kind": "pure",
        "evidence": {"function": "normalize_name"},
    },
    {
        "case_key": "golden_normalize_no_abbrev_expansion",
        "category": "source_matching",
        "input_desc": "A name abbreviated 'IND.' vs the same name spelled 'INDUSTRIES'.",
        "expected_outcome": (
            "Different normalized keys: NO abbreviation expansion, NO "
            "token merging — the pair must DISAGREE, never be merged."
        ),
        "check_kind": "pure",
        "evidence": {"function": "normalize_name"},
    },
    {
        "case_key": "golden_normalize_dg_tokens",
        "category": "source_matching",
        "input_desc": "A dotted initial name 'D.G.' vs the merged token 'DG'.",
        "expected_outcome": (
            "'D.G.' normalizes to 'D G' tokens and does NOT equal "
            "'DG' — punctuation becomes spaces, tokens never merge."
        ),
        "check_kind": "pure",
        "evidence": {"function": "normalize_name"},
    },
    {
        "case_key": "golden_alias_collision_capped",
        "category": "entity_resolution",
        "input_desc": (
            "Two companies sharing one bare stripped alias, resolved against the alias index."
        ),
        "expected_outcome": (
            "Both claimants flagged ambiguous, confidence capped at "
            "0.50, and the review rule forces pending_review — a "
            "shared alias never resolves to a guessed company."
        ),
        "check_kind": "pure",
        "evidence": {"function": "build_alias_index/resolve_text/review_status"},
    },
    {
        "case_key": "golden_qa_citation_rule",
        "category": "citation",
        "input_desc": (
            "A report draft whose section body cites no figure key "
            "and does not state 'not available', vs the same draft "
            "with a citation added."
        ),
        "expected_outcome": (
            "QA fails the uncited section and passes the cited one: "
            "every non-disclosures section cites a figure key or "
            "states 'not available'."
        ),
        "check_kind": "pure",
        "evidence": {"function": "qa_draft"},
    },
    {
        "case_key": "golden_summary_cap_280",
        "category": "summarization",
        "input_desc": "Stored seed event summaries (news_events.summary).",
        "expected_outcome": (
            "Every stored summary is at most 280 chars: the column "
            "is String(280) and the runner truncates at 280. No "
            "article body is stored anywhere."
        ),
        "check_kind": "stored",
        "evidence": {"source_table": "news_events"},
    },
    {
        "case_key": "golden_refusal_hbl_missing",
        "category": "refusal_abstention",
        "input_desc": "HBL (Habib Bank Limited) statement documents in stored rows.",
        "expected_outcome": (
            "Zero HBL documents: the correct answer for HBL analysis "
            "is missing_data, never an invented statement value."
        ),
        "check_kind": "stored",
        "evidence": {"source_table": "financial_documents", "ticker": "HBL"},
    },
    {
        "case_key": "golden_refusal_withheld_decisions",
        "category": "refusal_abstention",
        "input_desc": "Stored Phase 15 decisions and their user-facing values.",
        "expected_outcome": (
            "Every user-facing value is WITHHELD: no recommendation "
            "is issued while confidence caps at LOW and calibration "
            "is NOT_ESTABLISHED."
        ),
        "check_kind": "stored",
        "evidence": {"source_table": "decisions"},
    },
    {
        "case_key": "golden_injection_quarantine_stored",
        "category": "injection_resistance",
        "input_desc": (
            "The stored Phase 18 prompt-injection evaluation row, read by case name only."
        ),
        "expected_outcome": (
            "Result PASS with quarantine recorded: an injected "
            "instruction is quarantined as a mismatch against the "
            "deterministic authority, never applied."
        ),
        "check_kind": "stored",
        "evidence": {"source_table": "agent_evaluations"},
    },
    {
        "case_key": "golden_conflicting_sources_flagged",
        "category": "conflicting_sources",
        "input_desc": (
            "Stored registry status after 61 SECP LEAP evidence rows "
            "were loaded (47 AGREE, 5 DISAGREE, 9 NOT_FOUND)."
        ),
        "expected_outcome": (
            "All 470 companies remain UNVERIFIED: LEAP rows are "
            "evidence, never a promotion, and disagreements are "
            "recorded as review flags, never silently merged."
        ),
        "check_kind": "stored",
        "evidence": {"source_table": "companies/registry_evidence"},
    },
    {
        "case_key": "golden_extraction_chunk_counts",
        "category": "extraction",
        "input_desc": (
            "Stored RAG documents and chunks from the 3 issuer-hosted reports seeded in Phase 19."
        ),
        "expected_outcome": (
            "3 documents index to 943 chunks: extraction is "
            "deterministic and countable, and empty pages are "
            "recorded as gaps, never filled with invented rows."
        ),
        "check_kind": "stored",
        "evidence": {"source_table": "rag_documents/rag_chunks"},
    },
    {
        "case_key": "golden_hallucination_quarantine_stored",
        "category": "hallucination",
        "input_desc": (
            "The stored Phase 18 hallucinated-value evaluation row, read by case name only."
        ),
        "expected_outcome": (
            "Result PASS with a quarantine verdict: a numeric claim "
            "citing no evidence reference is quarantined, never "
            "served as a value."
        ),
        "check_kind": "stored",
        "evidence": {"source_table": "agent_evaluations"},
    },
    {
        "case_key": "golden_deterministic_authority",
        "category": "tool_selection",
        "input_desc": (
            "The stored Phase 18 deterministic-authority evaluation "
            "row plus the live stored HUBC close price."
        ),
        "expected_outcome": (
            "Evaluation PASS and the stored HUBC close is unchanged "
            "at 197.2400: agent claims never override deterministic "
            "stored values."
        ),
        "check_kind": "stored",
        "evidence": {"source_table": "agent_evaluations/market_prices"},
    },
]


def _valid_draft() -> dict:
    """A minimal draft that passes QA (mirrors Phase 22 fixtures)."""
    template = TEMPLATES["company_dossier"]
    sections = []
    for key, _title in template["sections"]:
        body = "Body citing close_price."
        if key == "disclosures":
            body = DISCLAIMER
        sections.append({"section_key": key, "body_markdown": body})
    return {
        "header": {
            "template_key": "company_dossier",
            "data_cutoff_date": "2026-11-04",
            "report_date": "2026-11-04",
        },
        "sections": sections,
        "figures": [
            {
                "figure_key": "close_price",
                "label": "Close price",
                "kind": "sourced_fact",
                "computation_status": "computed",
                "value": 197.24,
                "unit": "PKR",
                "source_table": "market_prices",
                "source_row_ids": [1],
                "source_note": "Stored close.",
                "quality_status": "UNVERIFIED",
            }
        ],
    }


def check_pure(case_key: str) -> tuple[bool, dict]:
    """Run a pure golden check. Returns (passed, evidence)."""
    if case_key == "golden_normalize_trailing_limited":
        same = normalize_name("THE HUB POWER COMPANY LIMITED") == normalize_name(
            "THE HUB POWER COMPANY"
        )
        return same, {
            "normalized": normalize_name("THE HUB POWER COMPANY LIMITED"),
        }
    if case_key == "golden_normalize_and_conjunction":
        same = normalize_name("A & B POWER") == normalize_name("A AND B POWER")
        return same, {"normalized": normalize_name("A & B POWER")}
    if case_key == "golden_normalize_no_abbrev_expansion":
        different = normalize_name("AGHA STEEL IND.") != normalize_name("AGHA STEEL INDUSTRIES")
        return different, {
            "abbrev": normalize_name("AGHA STEEL IND."),
            "full": normalize_name("AGHA STEEL INDUSTRIES"),
        }
    if case_key == "golden_normalize_dg_tokens":
        dotted = normalize_name("D.G. KHAN CEMENT")
        merged = normalize_name("DG KHAN CEMENT")
        return dotted == "D G KHAN CEMENT" and dotted != merged, {
            "dotted": dotted,
            "merged": merged,
        }
    if case_key == "golden_alias_collision_capped":
        # Tickers AAA/BBB deliberately absent from the resolved text,
        # so the shared stripped alias is the only match for both
        # claimants (a ticker present in the text would rightly win
        # at 1.0 for its own company).
        index = build_alias_index(
            [
                (1, "ALPHA POWER LIMITED", "AAA"),
                (2, "ALPHA POWER LIMITED", "BBB"),
            ]
        )
        matches = resolve_text("ALPHA POWER", index)
        capped = (
            len(matches) == 2
            and all(m["ambiguous"] for m in matches)
            and all(m["confidence"] <= 0.50 for m in matches)
        )
        review = (
            review_status(
                confidence=0.50,
                ambiguous=True,
                date_status="known",
                score=0.0,
                event_date=None,
                today=date(2026, 11, 5),
            )
            == "pending_review"
        )
        return capped and review, {
            "matches": [
                {
                    "company_id": m["company_id"],
                    "confidence": m["confidence"],
                    "ambiguous": m["ambiguous"],
                }
                for m in matches
            ],
            "review": "pending_review" if review else "other",
        }
    if case_key == "golden_qa_citation_rule":
        good = _valid_draft()
        good_problems = qa_draft(good)
        bad = _valid_draft()
        for section in bad["sections"]:
            if section["section_key"] != "disclosures":
                section["body_markdown"] = "Body with no citation."
                break
        bad_problems = qa_draft(bad)
        cited_problem = any("cites no figure" in p for p in bad_problems)
        return good_problems == [] and cited_problem, {
            "good_problems": good_problems,
            "bad_problems": bad_problems,
        }
    raise ValueError(f"unknown pure golden case {case_key!r}")


def check_stored(case_key: str, stored: dict) -> tuple[bool, dict]:
    """Evaluate a stored-evidence golden check against runner data.

    ``stored`` carries only counts/flags read from stored rows —
    never adversarial text, never re-executed retrieval.
    """
    if case_key == "golden_summary_cap_280":
        max_len = stored.get("max_summary_length")
        return (
            max_len is not None and max_len <= 280,
            {"max_summary_length": max_len},
        )
    if case_key == "golden_refusal_hbl_missing":
        docs = stored.get("hbl_documents")
        return docs == 0, {"hbl_documents": docs}
    if case_key == "golden_refusal_withheld_decisions":
        total = stored.get("decisions_total")
        withheld = stored.get("decisions_withheld")
        return (
            total is not None and total > 0 and withheld == total,
            {"decisions_total": total, "decisions_withheld": withheld},
        )
    if case_key == "golden_injection_quarantine_stored":
        result = stored.get("injection_eval_result")
        quarantined = stored.get("injection_eval_quarantined")
        return result == "PASS" and quarantined is True, {
            "result": result,
            "quarantined": quarantined,
        }
    if case_key == "golden_conflicting_sources_flagged":
        total = stored.get("companies_total")
        unverified = stored.get("companies_unverified")
        leap_rows = stored.get("leap_rows")
        return (
            total == 470 and unverified == 470 and leap_rows == 61,
            {
                "companies_total": total,
                "companies_unverified": unverified,
                "leap_rows": leap_rows,
            },
        )
    if case_key == "golden_extraction_chunk_counts":
        docs = stored.get("rag_documents")
        chunks = stored.get("rag_chunks")
        return docs == 3 and chunks == 943, {
            "rag_documents": docs,
            "rag_chunks": chunks,
        }
    if case_key == "golden_hallucination_quarantine_stored":
        result = stored.get("hallucination_eval_result")
        verdict = stored.get("hallucination_eval_verdict")
        return result == "PASS" and verdict == "QUARANTINE_NO_EVIDENCE", {
            "result": result,
            "verdict": verdict,
        }
    if case_key == "golden_deterministic_authority":
        result = stored.get("authority_eval_result")
        close = stored.get("hubc_close")
        close_ok = close is not None and abs(float(close) - 197.24) < 0.0001
        return result == "PASS" and close_ok, {
            "result": result,
            "hubc_close": str(close) if close is not None else None,
        }
    raise ValueError(f"unknown stored golden case {case_key!r}")
