"""Phase 19 research knowledge base and evidence retrieval (RAG).

Registries, seed documents, and benchmark cases.

- Retrieval methods: full_text (token search over chunk text),
  metadata (company / document-type / publication-date / access
  filters), exact_identifier (ticker / company-name tokens).
  vector is REGISTERED but NOT IMPLEMENTED: no local embedding
  model has been verified on this host (Phase 18 established
  LLM-backed execution as unavailable), so no embedding is
  computed, stored, or claimed. Its unblocker is a verified
  local/open-weight embedding model plus licence and quality
  checks.
- Seed documents: exactly the three issuer reports already held
  for internal analysis, keyed to their financial_documents rows
  (HUBC 13, NML 14, OGDC 15). DPS-hosted filings are NOT seeded
  (discovery only; filing-download terms not established).
  Publication dates: HUBC uses the auditor-report date
  2026-09-21 as a labelled PROXY (the report itself carries no
  separate publication-date field in the loaded data); NML is
  UNKNOWN (its Phase 7 record carries publication date NULL —
  never guessed); OGDC uses the RNS date 2026-02-23 as a
  labelled PROXY (Phase 11 seed event). A proxy date is never
  presented as a verified publication date.
- Access levels: official_public (SBP/PBS-type public releases),
  issuer_internal (issuer reports held for internal analysis),
  platform_internal (platform-derived reports). Roles: internal
  sees all levels; external sees official_public only;
  auditor sees official_public + platform_internal (never
  issuer_internal). Every decision is auditable in
  rag_access_audits.
- Benchmark cases: each names the expected passage (ticker +
  page + fragment) or the expected missing-data outcome. A case
  passes only when the expected passage is retrieved within
  top_k AND the answer cites it (citation precision = cited
  passages that match the expectation / all cited passages).
"""

from __future__ import annotations

from datetime import date

# Retrieval methods: name -> (version, implemented, description).
RETRIEVAL_METHODS: dict[str, dict] = {
    "full_text": {
        "version": "rag-v1",
        "implemented": True,
        "description": (
            "Deterministic token search over chunk text: token "
            "overlap plus exact-phrase bonus, scored in Python "
            "over stored chunks (no external search dependency)."
        ),
    },
    "metadata": {
        "version": "rag-v1",
        "implemented": True,
        "description": (
            "Filters on company, document type, publication date "
            "(as-of), and caller access level; combined with "
            "full-text scoring, never as a substitute for it."
        ),
    },
    "exact_identifier": {
        "version": "rag-v1",
        "implemented": True,
        "description": (
            "Ticker and normalised company-name tokens indexed "
            "with every chunk; a ticker query resolves to that "
            "company's documents deterministically."
        ),
    },
    "vector": {
        "version": "rag-v1",
        "implemented": False,
        "description": (
            "NOT IMPLEMENTED: no local embedding model has been "
            "verified on this host, so no embedding is computed "
            "or stored. Unblocker: a verified local/open-weight "
            "embedding model plus licence and quality checks."
        ),
    },
}

# Access model: role -> allowed access levels.
ROLE_ACCESS: dict[str, tuple[str, ...]] = {
    "internal": ("official_public", "issuer_internal", "platform_internal"),
    "external": ("official_public",),
    "auditor": ("official_public", "platform_internal"),
}

# Answer kinds, in the brief's vocabulary.
ANSWER_KINDS: tuple[str, ...] = (
    "direct_evidence",
    "derived_calculation",
    "inference",
    "uncertainty",
    "missing_data",
)

# Snippet cap: retrieval never serves more than this many
# characters per passage, so no document body is redistributed.
SNIPPET_MAX_CHARS = 500

# Chunk cap: a chunk never exceeds this many characters; long
# pages split at paragraph boundaries.
CHUNK_MAX_CHARS = 1500

# Seed documents: (ticker, title, document_type, storage_location,
# page_count, publication_date, publication_date_kind, access_level).
# Seeds are keyed by ticker and storage path, never by surrogate
# financial-document or company ids: both shift across fresh imports
# (the original import used document ids 13/14/15 and company ids
# 289/394/403; the post-VM-replacement import uses 4/5/6 and
# 759/864/873). The runner resolves live ids from the database.
SEED_DOCUMENTS: tuple[dict, ...] = (
    {
        "ticker": "HUBC",
        "title": "HUBCO Integrated Annual Report 2026",
        "document_type": "annual_report",
        "storage_location": ("storage/financial_reports/HUBC_Integrated_Annual_Report_2026.pdf"),
        "page_count": 423,
        "publication_date": date(2026, 9, 21),
        "publication_date_kind": "proxy",
        "publication_date_note": (
            "Auditor-report date (A. F. Ferguson & Co., UDIN "
            "AR202610080onH3rpTV1) used as publication proxy; the "
            "loaded document record carries no separate verified "
            "publication date."
        ),
        "access_level": "issuer_internal",
    },
    {
        "ticker": "NML",
        "title": "Nishat Mills 3rd Quarter Report 2025",
        "document_type": "quarterly_report",
        "storage_location": ("storage/financial_reports/NML_3rd_Quarter_Report_2025.pdf"),
        "page_count": 72,
        "publication_date": None,
        "publication_date_kind": "unknown",
        "publication_date_note": (
            "Phase 7 record carries publication date NULL; never "
            "guessed. The document is therefore excluded by any "
            "as-of date filter that requires a known date."
        ),
        "access_level": "issuer_internal",
    },
    {
        "ticker": "OGDC",
        "title": (
            "OGDC Condensed Interim Consolidated Statements - six months ended 31 December 2025"
        ),
        "document_type": "interim_filing",
        "storage_location": ("storage/financial_reports/OGDC_Interim_Dec2025.pdf"),
        "page_count": 12,
        "publication_date": date(2026, 2, 23),
        "publication_date_kind": "proxy",
        "publication_date_note": (
            "RNS date recorded by the Phase 11 seed event, used "
            "as publication proxy; not a verified publication "
            "date from the document record itself."
        ),
        "access_level": "issuer_internal",
    },
    {
        "ticker": "HBL",
        "title": "HBL Annual Report 2025",
        "document_type": "annual_report",
        "storage_location": ("storage/financial_reports/HBL_Annual_Report_2025.pdf"),
        "page_count": 411,
        "publication_date": date(2026, 3, 3),
        "publication_date_kind": "proxy",
        "publication_date_note": (
            "Consolidated auditor-report date (KPMG Taseer Hadi "
            "& Co., UDIN AR202510201HsNS5gUWD) used as "
            "publication proxy; added by the HBL re-run batch "
            "after the Phase 7 HBL extraction."
        ),
        "access_level": "issuer_internal",
    },
)

# Face pages (Phase 7 page maps) used as section labels so a
# retrieved passage keeps its reporting context.
FACE_PAGES: dict[str, dict[int, str]] = {
    "HUBC": {
        275: "profit_and_loss",
        277: "statement_of_financial_position",
        278: "cash_flow",
        279: "changes_in_equity",
        271: "auditor_opinion",
    },
    "NML": {
        37: "profit_and_loss",
        35: "statement_of_financial_position",
        36: "statement_of_financial_position",
    },
    "OGDC": {
        8: "profit_and_loss",
        7: "statement_of_financial_position",
    },
    # HBL face pages from the Phase 7 HBL page maps (PDF pages):
    # auditor report p.74, SFP p.75, P&L p.76, CE p.78, CF p.79.
    "HBL": {
        74: "auditor_opinion",
        75: "statement_of_financial_position",
        76: "profit_and_loss",
        78: "changes_in_equity",
        79: "cash_flow",
    },
}

# Benchmark cases: (case_key, query, expected_ticker,
# expected_page, expected_fragment, expected_kind).
# Fragments are short verified strings from the loaded data:
# HUBC net profit and EPS come from Phase 7/8 records; the
# auditor wording comes from docs/phase-07/auditor_opinions.json;
# NML's loss and OGDC's profit come from Phase 7 records.
BENCHMARK_CASES: tuple[dict, ...] = (
    {
        "case_key": "hubc_net_profit_fy2026",
        "query_text": "What was HUBC net profit for the year ended 30 June 2026?",
        "expected_ticker": "HUBC",
        "expected_page": 275,
        "expected_fragment": "56,257,178",
        "expected_kind": "direct_evidence",
    },
    {
        "case_key": "hubc_auditor_opinion",
        "query_text": "What did HUBC auditor conclude on the consolidated statements?",
        "expected_ticker": "HUBC",
        "expected_page": 271,
        "expected_fragment": "true and fair view",
        "expected_kind": "direct_evidence",
    },
    {
        "case_key": "nml_nine_month_loss",
        "query_text": "What was Nishat Mills profit or loss for nine months ended 31 March 2025?",
        "expected_ticker": "NML",
        "expected_page": 37,
        "expected_fragment": "1,182,815",
        "expected_kind": "direct_evidence",
    },
    {
        "case_key": "ogdc_six_month_profit",
        "query_text": "What was OGDC profit for the six months ended 31 December 2025?",
        "expected_ticker": "OGDC",
        "expected_page": 8,
        "expected_fragment": "73,019,248",
        "expected_kind": "direct_evidence",
    },
    {
        "case_key": "hubc_gross_margin_derived",
        "query_text": "What is HUBC gross margin for FY2026?",
        "expected_ticker": "HUBC",
        "expected_page": None,
        "expected_fragment": "gross_margin",
        "expected_kind": "derived_calculation",
    },
    # HBL re-run batch: the hbl_missing_document case is RETIRED —
    # its premise (no indexed HBL document) no longer holds now
    # that the 411-page report is indexed. It stays in the
    # database as history (its r3 result stands) but is no
    # longer evaluated: run_benchmark evaluates only current
    # code cases and reports retired ones as skipped. The
    # replacement case below uses only stored Phase 7 figures.
    {
        "case_key": "hbl_profit_cy2025",
        "query_text": "What was HBL profit for the year ended 31 December 2025?",
        "expected_ticker": "HBL",
        "expected_page": 76,
        "expected_fragment": "66,763,916",
        "expected_kind": "direct_evidence",
    },
)
