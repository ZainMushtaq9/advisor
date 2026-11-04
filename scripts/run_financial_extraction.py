"""Extract sampled financial-statement faces and load them (Phase 7).

Usage (from repo root, with DATABASE_URL set):
  DATABASE_URL=... backend/.venv/bin/python scripts/run_financial_extraction.py --dry-run
  DATABASE_URL=... backend/.venv/bin/python scripts/run_financial_extraction.py --commit

--dry-run is the DEFAULT: the report is printed but the transaction
is always rolled back. Pass --commit to actually write. --dry-run and
--commit are mutually exclusive; neither flag means dry-run.

Fail-fast, before any write, in BOTH modes:
  1. A missing PDF or unreadable page map aborts before any work.
  2. Any unknown company symbol aborts the whole run before any write.
  3. A failed balance identity (Assets != Liabilities + Equity) skips
     loading that statement; the failure is reported, never adjusted.
A second-method page-match (pdftotext re-read) runs for embedded-text
faces; mismatched rows load with confidence NULL and a flag. OCR
faces load at confidence 0.85, which the run report documents as
OCR + coordinator visual page-match (rendered PNGs vs extraction).
The script never prints DATABASE_URL, never fetches from any website,
and never performs a real trade.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

DEFAULT_MAPS = [
    "docs/phase-07/page_maps/hubc_sfp.json",
    "docs/phase-07/page_maps/hubc_pl.json",
    "docs/phase-07/page_maps/nml_sfp.json",
    "docs/phase-07/page_maps/nml_pl.json",
    "docs/phase-07/page_maps/ogdc_sfp.json",
    "docs/phase-07/page_maps/ogdc_pl.json",
]

SOURCE_KEYS = {
    "HUBC": "hubc_ir_annual_report_2026",
    "NML": "nml_ir_quarterly_2025_q3",
    "OGDC": "ogdc_rns_interim_2025_h1",
}

TERMS = {
    "HUBC": "Company-published integrated annual report on issuer investor-relations site; sampled only; internal analysis only; no republication.",
    "NML": "Company-published quarterly report on issuer investor-relations site; sampled only; internal analysis only; no republication.",
    "OGDC": "Company-authored filing transmitted via RNS (carrier, not author); sampled only; internal analysis only; no republication.",
}

# Balance-identity component lists per statement map.
IDENTITY = {
    "hubc_sfp": (
        ["total_equity"],
        ["non_current_liabilities_total", "current_liabilities_total"],
    ),
    "nml_sfp": (["total_equity"], ["total_liabilities"]),
    "ogdc_sfp": (["total_equity"], ["total_liabilities"]),
}

SUBTOTALS = {
    "hubc_sfp": {
        "non_current_assets_total": [
            "property_plant_equipment",
            "intangibles",
            "long_term_investments",
            "long_term_deposits",
        ],
        "current_assets_total": [
            "stores_spares_consumables",
            "stock_in_trade",
            "trade_debts",
            "loans_and_advances",
            "deposits_prepayments_other_receivables",
            "short_term_investments",
            "cash_and_bank_balances",
        ],
    },
    "nml_sfp": {
        "non_current_liabilities_total": [
            "long_term_financing",
            "lease_liabilities",
            "security_deposits",
            "retirement_benefit_obligation",
            "deferred_liabilities",
        ],
        "current_liabilities_total": [
            "trade_and_other_payables",
            "accrued_markup",
            "short_term_borrowings",
            "current_portion_non_current_liabilities",
            "unclaimed_dividend",
            "provision_taxation_levy",
        ],
        "non_current_assets_total": [
            "property_plant_equipment",
            "intangible_assets",
            "right_of_use_assets",
            "long_term_investments",
            "long_term_loans_asset",
            "long_term_deposits",
        ],
        "current_assets_total": [
            "stores_spare_parts",
            "stock_in_trade",
            "trade_debts",
            "loans_and_advances",
            "short_term_deposits_prepayments",
            "other_receivables",
            "accrued_interest",
            "short_term_investments",
            "cash_and_bank_balances",
        ],
    },
    "ogdc_sfp": {
        "non_current_assets_total": [
            "operating_non_current_subtotal",
            "long_term_investments_subsidiary_associates",
            "long_term_investments_amortized_cost",
            "long_term_loans_asset",
            "long_term_advances_prepayments",
            "lease_receivables",
        ],
        "current_assets_total": [
            "stores_spare_parts",
            "stock_in_trade",
            "trade_debts",
            "loans_and_advances",
            "deposits_short_term_prepayments",
            "other_receivables",
            "income_tax_advance",
            "current_portion_long_term_investments",
            "current_portion_lease_receivables",
            "other_financial_assets",
            "cash_and_bank_balances",
        ],
        "non_current_liabilities_total": [
            "deferred_taxation",
            "deferred_employee_benefits",
            "provision_decommissioning_cost",
            "long_term_lease_liability",
        ],
        "current_liabilities_total": [
            "short_term_lease_liability",
            "trade_and_other_payables",
            "unpaid_dividend",
            "unclaimed_dividend",
        ],
    },
}


def _fail(message: str, detail: dict | None = None) -> int:
    payload = {"status": "aborted", "error": message}
    if detail:
        payload.update(detail)
    print(json.dumps(payload, indent=2, default=str))
    return 2


def embedded_lines(pdf_path, pages):
    import pymupdf

    doc = pymupdf.open(pdf_path)
    out = []
    for pno in pages:
        text = doc[pno - 1].get_text("text")
        for ln in text.splitlines():
            if ln.strip():
                out.append((pno, ln))
    doc.close()
    return out


def pdftotext_lines(pdf_path, pages):
    import shutil

    if shutil.which("pdftotext") is None:
        raise ValueError("pdftotext executable not found; page-match cannot run")
    out = []
    for pno in pages:
        proc = subprocess.run(
            ["pdftotext", "-layout", "-f", str(pno), "-l", str(pno), pdf_path, "-"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        for ln in proc.stdout.splitlines():
            if ln.strip():
                out.append((pno, ln))
    return out


def extract_map(page_map, repo_root):
    from app.services.financial_statements.extract import (
        extract_face,
        extract_ogdc_face,
        ocr_page_lines,
    )

    pdf = os.path.join(repo_root, page_map["pdf"])
    method = page_map["method"]
    n_cols = len(page_map["columns"])
    if method == "embedded_text":
        lines = embedded_lines(pdf, page_map["pages"])
        rows = extract_face(lines, page_map["specs"], n_cols)
        return rows, "pymupdf_embedded_text", lines
    if method == "ocr_single_panel":
        lines = []
        for pno in page_map["pages"]:
            lines.extend(ocr_page_lines(pdf, pno))
        rows = extract_face(lines, page_map["specs"], n_cols)
        return rows, "ocr_tesseract_5_200dpi", lines
    if method == "ocr_two_panel":
        lines = []
        for pno in page_map["pages"]:
            lines.extend(ocr_page_lines(pdf, pno))
        left, right = extract_ogdc_face(
            lines,
            page_map["left_specs"],
            page_map["right_specs"],
            page_map["right_labels"],
            2,
        )
        return left + right, "ocr_tesseract_5_200dpi", lines
    raise ValueError(f"unknown method: {method}")


def page_match_embedded(page_map, repo_root, rows):
    """Second-method re-read with pdftotext; returns {(key, col): bool}.

    For two-panel faces (OGDC SFP), pdftotext -layout merges the
    panels per line, so the second read uses the joint two-panel
    parser while the primary read uses sequential embedded lines:
    the methods genuinely differ, which is the point.
    """
    from app.services.financial_statements.extract import (
        extract_face,
        extract_ogdc_face,
    )

    pdf = os.path.join(repo_root, page_map["pdf"])
    lines = pdftotext_lines(pdf, page_map["pages"])
    if page_map.get("page_match_method") == "two_panel":
        left, right = extract_ogdc_face(
            lines,
            page_map["left_specs"],
            page_map["right_specs"],
            page_map["right_labels"],
            2,
        )
        second = left + right
    else:
        second = extract_face(lines, page_map["specs"], len(page_map["columns"]))
    by_key = {r["key"]: r for r in second}
    result = {}
    for row in rows:
        other = by_key.get(row["key"])
        for ci in range(len(page_map["columns"])):
            mine = row["values"][ci] if ci < len(row["values"]) else None
            theirs = (
                other["values"][ci] if other and ci < len(other["values"]) else "ABSENT"
            )
            result[(row["key"], ci)] = mine == theirs
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract sampled financial statements (Phase 7)."
    )
    parser.add_argument(
        "--maps", nargs="*", default=DEFAULT_MAPS, help="Page-map JSON files."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Report only; roll back (default)."
    )
    mode.add_argument("--commit", action="store_true", help="Actually write.")
    args = parser.parse_args(argv)
    commit = bool(args.commit)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Fail-fast 1: maps + PDFs exist.
    maps = []
    for path in args.maps:
        full = path if os.path.isabs(path) else os.path.join(repo_root, path)
        if not os.path.exists(full):
            return _fail(f"page map not found: {path}")
        with open(full) as f:
            page_map = json.load(f)
        pdf = os.path.join(repo_root, page_map["pdf"])
        if not os.path.exists(pdf):
            return _fail(
                f"PDF not found for {page_map['company_symbol']}: {page_map['pdf']}"
            )
        maps.append((os.path.basename(path).replace(".json", ""), page_map))

    # Extraction (no DB yet). A missing extraction tool is a clean
    # exit-2 abort, never a traceback.
    from app.services.financial_statements.validate import (
        check_balance_identity,
        check_subtotal,
    )

    extracted = []
    try:
        for name, page_map in maps:
            rows, method, _lines = extract_map(page_map, repo_root)
            match = None
            if page_map["method"] == "embedded_text":
                match = page_match_embedded(page_map, repo_root, rows)
            extracted.append(
                {
                    "name": name,
                    "map": page_map,
                    "rows": rows,
                    "method": method,
                    "match": match,
                }
            )
    except ValueError as exc:
        return _fail(str(exc))

    # Validation per statement column.
    report_maps = []
    for item in extracted:
        page_map, rows, name = item["map"], item["rows"], item["name"]
        col_results = []
        for ci, col in enumerate(page_map["columns"]):
            checks = {}
            if name in IDENTITY:
                eq, liab = IDENTITY[name]
                ok, detail = check_balance_identity(rows, ci, eq, liab)
                checks["balance_identity"] = {"passed": ok, "detail": detail}
            for total_key, comps in SUBTOTALS.get(name, {}).items():
                ok, detail = check_subtotal(rows, total_key, comps, ci, missing="zero")
                checks[f"subtotal:{total_key}"] = {"passed": ok, "detail": detail}
            col_results.append({"column": col, "checks": checks})
        item["col_results"] = col_results
        flagged = [
            r["key"]
            for r in rows
            if "label_not_found" in r["flags"] or "incomplete_values" in r["flags"]
        ]
        item["flagged_rows"] = flagged
        # Page-match summary: "key:col" pairs where the pdftotext
        # re-read disagrees (embedded maps only; None otherwise).
        # Mismatched rows load with confidence NULL.
        match_mismatches = None
        if item["match"] is not None:
            match_mismatches = sorted(
                f"{key}:{ci}" for (key, ci), ok in item["match"].items() if not ok
            )
        report_maps.append(
            {
                "map": name,
                "company": page_map["company_symbol"],
                "statement_type": page_map["statement_type"],
                "method": item["method"],
                "rows": len(rows),
                "flagged_rows": flagged,
                "page_match_mismatches": match_mismatches,
                "columns": col_results,
            }
        )

    # DB work (fail-fast 2: unknown company aborts before any write).
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return _fail("DATABASE_URL is required")
    from app.services.financial_statements.load import (
        get_company,
        get_or_create_data_source,
        get_or_create_document,
        load_statement,
        sha256_file,
    )
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        companies = {}
        for name, page_map in maps:
            try:
                companies[page_map["company_symbol"]] = get_company(
                    session, page_map["company_symbol"]
                )
            except ValueError as exc:
                # Explicit rollback: never rely on close() to discard
                # a half-built transaction on the abort path.
                session.rollback()
                return _fail(str(exc))
        # NOTE: data-source and document rows are created before the
        # per-statement balance gate, so a gate-skipped statement
        # still leaves its (real, sampled) document row committed.
        # The gate blocks statement + line-item rows only.
        written = {
            "documents": 0,
            "statements": 0,
            "line_items": 0,
            "skipped_existing": 0,
            "skipped_validation": 0,
        }
        for item in extracted:
            page_map, rows, name = item["map"], item["rows"], item["name"]
            symbol = page_map["company_symbol"]
            company = companies[symbol]
            ds = get_or_create_data_source(
                session,
                SOURCE_KEYS[symbol],
                f"{symbol} sampled financial statements",
                page_map.get("source_url", ""),
                TERMS[symbol],
            )
            pdf = os.path.join(repo_root, page_map["pdf"])
            content_hash = sha256_file(pdf)
            import pymupdf

            doc = pymupdf.open(pdf)
            page_count = len(doc)
            doc.close()
            document, doc_created = get_or_create_document(
                session, company.id, page_map, content_hash, page_count
            )
            if doc_created:
                written["documents"] += 1
            # Group columns (grouped P&L maps -> one statement per group).
            groups: dict[str, list[int]] = {}
            for ci, col in enumerate(page_map["columns"]):
                groups.setdefault(col.get("group", f"col{ci}"), []).append(ci)
            for col_indices in groups.values():
                # Balance-identity gate: every column of the group must pass.
                gate_ok = True
                for ci in col_indices:
                    checks = item["col_results"][ci]["checks"]
                    if (
                        "balance_identity" in checks
                        and not checks["balance_identity"]["passed"]
                    ):
                        gate_ok = False
                if not gate_ok:
                    written["skipped_validation"] += 1
                    continue
                for ci in col_indices:
                    col = page_map["columns"][ci]
                    if page_map["method"] == "embedded_text":
                        # Confidence 1.0 where the pdftotext re-read
                        # agrees, NULL where it mismatches (set at
                        # insert: versioned tables forbid UPDATEs).
                        conf_map = {
                            row["key"]: (
                                Decimal("1.0000")
                                if item["match"]
                                and item["match"].get((row["key"], ci), False)
                                else None
                            )
                            for row in rows
                        }
                        _stmt, n_items, skipped = load_statement(
                            session,
                            company_id=company.id,
                            data_source=ds,
                            document_id=document.id,
                            page_map=page_map,
                            column=col,
                            rows=rows,
                            col_index=ci,
                            method=item["method"],
                            confidence=Decimal("1.0000"),
                            confidence_map=conf_map,
                        )
                    else:
                        _stmt, n_items, skipped = load_statement(
                            session,
                            company_id=company.id,
                            data_source=ds,
                            document_id=document.id,
                            page_map=page_map,
                            column=col,
                            rows=rows,
                            col_index=ci,
                            method=item["method"],
                            confidence=Decimal("0.8500"),
                        )
                    if skipped:
                        written["skipped_existing"] += 1
                    else:
                        written["statements"] += 1
                        written["line_items"] += n_items
        if commit:
            session.commit()
        else:
            session.rollback()
        report = {
            "status": "committed" if commit else "dry-run",
            "written": written,
            "maps": report_maps,
        }
        print(json.dumps(report, indent=2, default=str))
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
