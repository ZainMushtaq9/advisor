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
    "docs/phase-07/page_maps/hubc_cf.json",
    "docs/phase-07/page_maps/hubc_ce.json",
    "docs/phase-07/page_maps/nml_sfp.json",
    "docs/phase-07/page_maps/nml_pl.json",
    "docs/phase-07/page_maps/nml_cf.json",
    "docs/phase-07/page_maps/nml_ce.json",
    "docs/phase-07/page_maps/ogdc_sfp.json",
    "docs/phase-07/page_maps/ogdc_pl.json",
    "docs/phase-07/page_maps/ogdc_cf.json",
    "docs/phase-07/page_maps/ogdc_ce.json",
]

OPINIONS_JSON = "docs/phase-07/auditor_opinions.json"

SOURCE_KEYS = {
    "HUBC": "hubc_ir_annual_report_2026",
    "NML": "nml_ir_quarterly_2025_q3",
    "OGDC": "ogdc_rns_interim_2025_h1",
    "HBL": "hbl_ir_annual_report_2025",
}

TERMS = {
    "HUBC": "Company-published integrated annual report on issuer investor-relations site; sampled only; internal analysis only; no republication.",
    "NML": "Company-published quarterly report on issuer investor-relations site; sampled only; internal analysis only; no republication.",
    "OGDC": "Company-authored filing transmitted via RNS (carrier, not author); sampled only; internal analysis only; no republication.",
    "HBL": "Company-published annual report on issuer investor-relations site; sampled only; internal analysis only; no republication.",
}

# Balance-identity component lists per statement map.
IDENTITY = {
    "hubc_sfp": (
        ["total_equity"],
        ["non_current_liabilities_total", "current_liabilities_total"],
    ),
    "nml_sfp": (["total_equity"], ["total_liabilities"]),
    "ogdc_sfp": (["total_equity"], ["total_liabilities"]),
    "hbl_sfp": (["total_equity"], ["total_liabilities"]),
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
    "hubc_cf": {
        "pbt_total": ["pbt_continuing", "pbt_discontinued"],
        "op_profit_before_wc": [
            "pbt_total",
            "depreciation",
            "amortisation",
            "provision_slow_moving",
            "provision_wppf",
            "trade_debts_written_off",
            "provision_nrv",
            "staff_gratuity",
            "gain_mutual_fund",
            "interest_income",
            "gain_disposal",
            "dividend_income",
            "loss_fx_adjustment",
            "interest_expense",
            "amort_transaction_costs",
            "share_profit_associates",
            "gain_dilution",
            "levy",
            "realised_profit_management",
        ],
        "cash_generated": ["op_profit_before_wc", "wc_changes"],
        "net_operating": [
            "cash_generated",
            "interest_received",
            "interest_paid",
            "gratuity_paid",
            "taxes_paid",
        ],
        "net_investing": [
            "fixed_capex",
            "disposal_proceeds",
            "lt_investments_made",
            "dividend_received",
            "st_investment_made",
            "st_investments_redeemed",
            "loan_mmcpl",
            "cash_acquired_business_comb",
            "cash_transferred_dilution",
            "lt_deposits_net",
        ],
        "net_financing": [
            "div_owners",
            "div_nci",
            "repay_lt_loans",
            "repay_sukuk",
            "st_borrowings_net",
            "repay_lt_lease",
            "share_issuance_cost",
        ],
        "net_change": ["net_operating", "net_investing", "net_financing"],
        "cash_end": ["cash_begin", "net_change", "loss_fx_closing"],
    },
    "hubc_ce": {
        "om_end": ["om_begin", "om_transfers", "om_utilisation"],
        "unapp_end": [
            "unapp_begin",
            "total_comprehensive",
            "transfers_to_om",
            "utilisation_from_om",
            "share_issue_cost_disc",
            "adj_associate",
            "adj_nci_owners",
            "transactions_subtotal",
            "share_issue_cost",
        ],
        "owners_total": [
            "issued_capital_balance",
            "share_premium_balance",
            "om_end",
            "unapp_end",
        ],
        "nci_end": [
            "nci_begin",
            "nci_arising",
            "nci_total_comprehensive",
            "adj_nci_positive",
            "nci_dividends",
        ],
        "total_equity": ["owners_total", "nci_end"],
    },
    "nml_cf": {
        "net_operating": [
            "cash_generated_ops",
            "finance_cost_paid",
            "income_tax_paid",
            "lt_security_deposits",
            "exchange_gain_forward",
            "retirement_benefit",
            "lt_loans_net",
            "lt_deposits_net",
        ],
        "net_investing": [
            "capex",
            "disposal_ppe",
            "dividends_received",
            "loans_associate",
            "repayment_associate",
            "interest_received",
            "sale_investments",
            "sale_subsidiary",
            "investments_made",
        ],
        "net_financing": [
            "lt_financing_proceeds",
            "lt_financing_repayment",
            "lease_repayment",
            "exchange_translation",
            "st_borrowings",
            "dividend_paid",
        ],
        "net_change": ["net_operating", "net_investing", "net_financing"],
        "cash_end": [
            "net_change",
            "fx_difference",
            "disposal_subsidiary_cash",
            "cash_begin",
        ],
    },
    "ogdc_cf": {
        "op_subtotal": [
            "pbt",
            "depreciation",
            "amortisation_dpa",
            "delayed_surcharge",
            "unwinding_tfc",
            "royalty",
            "wppf",
            "provision_deferred_benefits",
            "unwinding_decommissioning",
            "interest_income_investments",
            "interest_income_lease",
            "unwinding_lease",
            "unrealised_gain_fvtpl",
            "realised_gain_fvtpl",
            "exchange_gain_loss",
            "dividend_income_fvtpl",
            "gain_disposal_ppe",
            "share_profit_associates",
            "stores_written_off",
            "dry_wells",
            "reversal_trade_provision",
        ],
        "cash_generated_ops": [
            "op_subtotal",
            "stores",
            "stock",
            "trade_debts",
            "deposits_prepayments",
            "loans_advances_receivables",
            "trade_payables",
        ],
        "deductions_subtotal": [
            "royalty_paid",
            "deferred_benefits_paid",
            "lt_advances_paid",
            "decommissioning_paid",
            "wppf_paid",
            "taxes_paid",
        ],
        "net_operating": ["cash_generated_ops", "deductions_subtotal"],
        "net_investing": [
            "capex",
            "interest_received",
            "lease_received",
            "dividends_received",
            "encashment",
            "fvtpl_net",
            "investment_associates",
            "disposal_ppe_proceeds",
        ],
        "net_financing": ["dividends_paid", "lease_paid"],
        # NOTE: the 2025 column fails this check by exactly 1
        # (thousand) in the source as printed: components sum to
        # 12,517,649 vs the printed net 12,517,648. Recorded, never
        # adjusted; subtotal checks are not load gates.
        "net_change": ["net_operating", "net_investing", "net_financing"],
        "cash_end": ["cash_begin", "net_change", "fx_effect"],
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
    "hbl_sfp": {
        "total_assets": [
            "cash_treasury_banks",
            "balances_other_banks",
            "lendings_financial_institutions",
            "investments",
            "advances",
            "property_equipment",
            "right_of_use_assets",
            "intangible_assets",
            "deferred_tax_assets",
            "other_assets",
        ],
        "total_liabilities": [
            "bills_payable",
            "borrowings",
            "deposits_other_accounts",
            "lease_liabilities",
            "subordinated_debt",
            "deferred_tax_liabilities",
            "other_liabilities",
        ],
        "equity_attributable": [
            "share_capital",
            "reserves",
            "surplus_revaluation_assets",
            "unappropriated_profit",
        ],
        "total_equity": ["equity_attributable", "non_controlling_interest"],
    },
    # NOTE: check_subtotal only sums, so P&L links that need
    # subtraction (net mark-up, profit chain) are NOT listed here;
    # they were hand-verified in the run report instead. Only
    # addition links are checked mechanically.
    "hbl_pl": {
        "total_non_markup_income": [
            "fee_commission_income",
            "dividend_income",
            "share_profit_associates",
            "foreign_exchange_income",
            "income_derivatives",
            "gain_securities_net",
            "other_income",
        ],
        "total_non_markup_expenses": [
            "operating_expenses",
            "workers_welfare_fund",
            "other_charges",
        ],
        "pat_total": ["pat_equity_holders", "pat_nci"],
    },
    "hbl_cf": {
        "cf_operating_subtotal_1": [
            "profit_before_taxation",
            "dividend_income",
            "share_profit_associates",
            "markup_subordinated_debt",
        ],
        "cf_adjustments_total": [
            "depreciation",
            "amortisation",
            "depreciation_rou",
            "markup_lease_rou",
            "reversal_cla_investments",
            "provisions_cla_loans",
            "reversal_cla_lendings",
            "provision_cla_other_assets",
            "reversal_charge_cla_offbs",
            "unrealised_fvtpl",
            "exchange_gain_loss_goodwill",
            "gain_sale_ppe",
            "gain_closure_branches",
            "workers_welfare_fund",
        ],
        "cf_operating_subtotal_2": [
            "cf_operating_subtotal_1",
            "cf_adjustments_total",
        ],
        "cf_operating_assets_total": [
            "lendings_fi_change",
            "fvtpl_investment_change",
            "advances_change",
            "other_assets_change",
        ],
        "cf_operating_liabilities_total": [
            "bills_payable_change",
            "borrowings_fi_change",
            "deposits_change",
            "other_liabilities_change",
        ],
        "cf_operating_before_tax": [
            "cf_operating_subtotal_2",
            "cf_operating_assets_total",
            "cf_operating_liabilities_total",
        ],
        "cf_net_operating": ["cf_operating_before_tax", "income_tax_paid"],
        "cf_net_investing": [
            "fvcoci_investment_change",
            "amortised_cost_investment_change",
            "associates_investment_change",
            "dividend_received",
            "ppe_investment",
            "intangible_investment",
            "ppe_sale_proceeds",
            "translation_effect_investing",
        ],
        "cf_net_financing": [
            "subordinated_debt_proceeds",
            "subordinated_markup_paid",
            "lease_liability_paid",
            "dividend_paid",
        ],
        "cf_cash_before_increase": ["cf_cash_beginning", "cf_exchange_effect_cash"],
        "cf_cash_end": ["cf_cash_before_increase", "cf_cash_increase"],
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


def drop_lines(lines, patterns):
    """Drop page-furniture lines (headers/footers/titles) before
    extraction. A line is dropped when any pattern appears in it
    (case-insensitive substring). Patterns are map-scoped and must
    never match a row label or a value line."""
    if not patterns:
        return lines
    pats = [p.lower() for p in patterns]
    return [(pno, ln) for (pno, ln) in lines if not any(p in ln.lower() for p in pats)]


def extract_matrix(page_map, repo_root):
    """Extract a changes-in-equity matrix face.

    Returns (blocks, method, match) where blocks is a list of
    {"block": block, "rows": rows} and match maps
    (block_idx, key, comp_idx) -> bool for the second-method
    re-read. The primary method comes from the map ('layout_text'
    = pdftotext -layout, 'embedded_text' = PyMuPDF); the second
    read is always the other method, so the two reads genuinely
    differ (grid order vs content-stream order). Movement blocks
    share one page and resolve via the advancing cursor, so
    repeated labels match their next occurrence per block.
    """
    from app.services.financial_statements.extract import extract_face_from

    pdf = os.path.join(repo_root, page_map["pdf"])
    patterns = page_map.get("drop_lines_matching", [])
    n_comp = len(page_map["components"])
    if page_map["method"] == "layout_text":
        primary = drop_lines(pdftotext_lines(pdf, page_map["pages"]), patterns)
        second = drop_lines(embedded_lines(pdf, page_map["pages"]), patterns)
        method = "pdftotext_layout_text"
    elif page_map["method"] == "embedded_text":
        primary = drop_lines(embedded_lines(pdf, page_map["pages"]), patterns)
        second = drop_lines(pdftotext_lines(pdf, page_map["pages"]), patterns)
        method = "pymupdf_embedded_text"
    else:
        raise ValueError(f"unknown matrix method: {page_map['method']}")
    blocks = []
    cursor = 0
    for block in page_map["blocks"]:
        rows, cursor = extract_face_from(
            primary, block["specs"], n_comp, cursor, scan_cap=40
        )
        blocks.append({"block": block, "rows": rows})
    second_blocks = []
    cursor = 0
    for block in page_map["blocks"]:
        rows, cursor = extract_face_from(
            second, block["specs"], n_comp, cursor, scan_cap=40
        )
        second_blocks.append(rows)
    match = {}
    for bi, (item, srows) in enumerate(zip(blocks, second_blocks)):
        by_key = {r["key"]: r for r in srows}
        for row in item["rows"]:
            other = by_key.get(row["key"])
            for ci in range(n_comp):
                mine = row["values"][ci] if ci < len(row["values"]) else None
                theirs = (
                    other["values"][ci]
                    if other and ci < len(other["values"])
                    else "ABSENT"
                )
                match[(bi, row["key"], ci)] = mine == theirs
    return blocks, method, match


def validate_matrix(item):
    """Roll-forward + balance checks for one matrix map.

    Returns per-block dicts: {block, rows, flagged_rows,
    rollforward, balance, page_match_mismatches, gate_ok}.
    Opening values for a block come from its own opening row, or
    from the previous block's closing row when the block declares
    opening_from_previous_close. A block gates OUT (its component
    statements are skipped) when any check fails OR any row is
    flagged: a flagged row means the extraction itself failed, and
    missing-as-zero must never hide it.
    """
    from app.services.financial_statements.validate import (
        check_cross_component,
        check_subtotal,
    )

    page_map = item["map"]
    comp_keys = [c["key"] for c in page_map["components"]]
    comp_index = {k: i for i, k in enumerate(comp_keys)}
    results = []
    prev_close_values = None
    for bi, entry in enumerate(item["blocks"]):
        block, rows = entry["block"], entry["rows"]
        by_key = {r["key"]: r for r in rows}
        if block.get("opening_from_previous_close"):
            opening_values = prev_close_values
            opening_key = None
        else:
            opening_key = block["opening_key"]
            opening_row = by_key.get(opening_key)
            opening_values = opening_row["values"] if opening_row is not None else None
        closing_row = by_key.get(block["closing_key"])
        # Subtotal rows (total comprehensive income, total
        # distributions) are NOT movements: summing them alongside
        # their components double-counts (OGDC block 1 overstates
        # unappropriated profit by exactly profit + distributions).
        movement_keys = [
            s["key"]
            for s in block["specs"]
            if s["key"] not in (block.get("opening_key"), block["closing_key"])
            and not s.get("subtotal")
        ]
        if opening_values is not None and block.get("opening_from_previous_close"):
            check_rows = [
                {
                    "key": "__block_opening__",
                    "values": opening_values,
                    "displayed": [None] * len(comp_keys),
                }
            ] + rows
            rf_components = ["__block_opening__"] + movement_keys
        else:
            check_rows = rows
            rf_components = [block.get("opening_key")] + movement_keys
        rollforward = {}
        for ci, comp in enumerate(comp_keys):
            if closing_row is None or opening_values is None:
                rollforward[comp] = {
                    "passed": False,
                    "detail": {"reason": "missing opening or closing row"},
                }
                continue
            closing_val = (
                closing_row["values"][ci] if ci < len(closing_row["values"]) else None
            )
            if closing_val is None:
                # A printed dash in the closing row means nil for
                # that component: the roll-forward passes iff the
                # movements compute to zero. Evaluate against a
                # copy of the closing row with 0 substituted, and
                # record the substitution in the detail.
                fixed_rows = []
                for r in check_rows:
                    if r["key"] == block["closing_key"]:
                        vals = list(r["values"])
                        while len(vals) <= ci:
                            vals.append(None)
                        vals[ci] = Decimal(0)
                        fixed_rows.append({**r, "values": vals})
                    else:
                        fixed_rows.append(r)
                ok, detail = check_subtotal(
                    fixed_rows,
                    block["closing_key"],
                    rf_components,
                    ci,
                    missing="zero",
                )
                detail = {**detail, "closing_dash_as_zero": True}
            else:
                ok, detail = check_subtotal(
                    check_rows, block["closing_key"], rf_components, ci, missing="zero"
                )
            rollforward[comp] = {"passed": ok, "detail": detail}
        balance = []
        balance_rows = []
        if block.get("opening_key"):
            balance_rows.append(
                (block["opening_key"], by_key.get(block["opening_key"]))
            )
        elif prev_close_values is not None:
            balance_rows.append(
                (
                    "__previous_close__",
                    {"key": "__previous_close__", "values": prev_close_values},
                )
            )
        balance_rows.append((block["closing_key"], closing_row))
        for row_key, row in balance_rows:
            if row is None:
                balance.append(
                    {
                        "row": row_key,
                        "passed": False,
                        "detail": {"reason": "missing row"},
                    }
                )
                continue
            for check in page_map.get("balance_checks", []):
                total_idx = comp_index[check["total"]]
                comp_indices = [comp_index[c] for c in check["components"]]
                ok, detail = check_cross_component(
                    [row], row_key, total_idx, comp_indices, missing="zero"
                )
                balance.append(
                    {
                        "row": row_key,
                        "total": check["total"],
                        "passed": ok,
                        "detail": detail,
                    }
                )
        flagged = [
            r["key"]
            for r in rows
            if "label_not_found" in r["flags"] or "incomplete_values" in r["flags"]
        ]
        mismatches = sorted(
            f"block{bi}:{key}:{ci}"
            for (b, key, ci), ok in item["match"].items()
            if b == bi and not ok
        )
        gate_ok = (
            not flagged
            and all(v["passed"] for v in rollforward.values())
            and all(b["passed"] for b in balance)
        )
        results.append(
            {
                "block": block,
                "rows": len(rows),
                "flagged_rows": flagged,
                "rollforward": rollforward,
                "balance": balance,
                "page_match_mismatches": mismatches,
                "gate_ok": gate_ok,
            }
        )
        prev_close_values = closing_row["values"] if closing_row is not None else None
    return results


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

    # Fail-fast 1b: opinions file, when present, must validate.
    opinions_records = None
    opinions_path = os.path.join(repo_root, OPINIONS_JSON)
    if os.path.exists(opinions_path):
        from app.services.financial_statements.opinions import (
            validate_opinion_record,
        )

        with open(opinions_path) as f:
            opinions_doc = json.load(f)
        opinions_records = opinions_doc["records"]
        for record in opinions_records:
            errors = validate_opinion_record(record)
            if errors:
                return _fail(
                    f"invalid opinion record for "
                    f"{record.get('company_symbol')}: {errors}"
                )

    # Extraction (no DB yet). A missing extraction tool is a clean
    # exit-2 abort, never a traceback.
    from app.services.financial_statements.validate import (
        check_balance_identity,
        check_subtotal,
    )

    extracted = []
    try:
        for name, page_map in maps:
            if page_map.get("matrix"):
                blocks, method, match = extract_matrix(page_map, repo_root)
                extracted.append(
                    {
                        "name": name,
                        "map": page_map,
                        "kind": "matrix",
                        "blocks": blocks,
                        "method": method,
                        "match": match,
                    }
                )
                continue
            rows, method, _lines = extract_map(page_map, repo_root)
            match = None
            if page_map["method"] == "embedded_text":
                match = page_match_embedded(page_map, repo_root, rows)
            extracted.append(
                {
                    "name": name,
                    "map": page_map,
                    "kind": "standard",
                    "rows": rows,
                    "method": method,
                    "match": match,
                }
            )
    except ValueError as exc:
        return _fail(str(exc))

    # Validation per statement column (standard) or per movement
    # block (matrix).
    report_maps = []
    for item in extracted:
        page_map, name = item["map"], item["name"]
        if item["kind"] == "matrix":
            block_results = validate_matrix(item)
            item["block_results"] = block_results
            report_maps.append(
                {
                    "map": name,
                    "company": page_map["company_symbol"],
                    "statement_type": page_map["statement_type"],
                    "method": item["method"],
                    "kind": "matrix",
                    "blocks": [
                        {
                            "period_start": b["block"]["period_start"],
                            "period_end": b["block"]["period_end"],
                            "rows": b["rows"],
                            "flagged_rows": b["flagged_rows"],
                            "gate_ok": b["gate_ok"],
                            "rollforward": b["rollforward"],
                            "balance": b["balance"],
                            "page_match_mismatches": b["page_match_mismatches"],
                        }
                        for b in block_results
                    ],
                }
            )
            continue
        rows = item["rows"]
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
                "kind": "standard",
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
        docs_by_symbol = {}
        ds_by_symbol = {}
        for item in extracted:
            page_map, name = item["map"], item["name"]
            symbol = page_map["company_symbol"]
            company = companies[symbol]
            ds = get_or_create_data_source(
                session,
                SOURCE_KEYS[symbol],
                f"{symbol} sampled financial statements",
                page_map.get("source_url", ""),
                TERMS[symbol],
            )
            ds_by_symbol[symbol] = ds
            pdf = os.path.join(repo_root, page_map["pdf"])
            content_hash = sha256_file(pdf)
            import pymupdf

            doc = pymupdf.open(pdf)
            page_count = len(doc)
            doc.close()
            document, doc_created = get_or_create_document(
                session, company.id, page_map, content_hash, page_count
            )
            docs_by_symbol[symbol] = document
            if doc_created:
                written["documents"] += 1
            if item["kind"] == "matrix":
                # One statement per equity component per movement
                # block; a gated-out block skips all its component
                # statements (counted as such).
                n_comp = len(page_map["components"])
                for bi, bres in enumerate(item["block_results"]):
                    if not bres["gate_ok"]:
                        written["skipped_validation"] += n_comp
                        continue
                    block = bres["block"]
                    brow = item["blocks"][bi]["rows"]
                    col = {
                        "period_start": block["period_start"],
                        "period_end": block["period_end"],
                        "reporting_frequency": block.get("reporting_frequency"),
                    }
                    for ci, comp in enumerate(page_map["components"]):
                        conf_map = {
                            row["key"]: (
                                Decimal("1.0000")
                                if item["match"].get((bi, row["key"], ci), False)
                                else None
                            )
                            for row in brow
                        }
                        _stmt, n_items, skipped = load_statement(
                            session,
                            company_id=company.id,
                            data_source=ds,
                            document_id=document.id,
                            page_map=page_map,
                            column=col,
                            rows=brow,
                            col_index=ci,
                            method=item["method"],
                            confidence=Decimal("1.0000"),
                            confidence_map=conf_map,
                            scope=comp["key"],
                        )
                        if skipped:
                            written["skipped_existing"] += 1
                        else:
                            written["statements"] += 1
                            written["line_items"] += n_items
                continue
            rows = item["rows"]
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
        # Auditor opinions (same transaction; dry-run rolls back).
        opinions_report = {
            "written": 0,
            "skipped_existing": 0,
            "records": [],
            "skipped_no_document": [],
        }
        if opinions_records is not None:
            from app.services.financial_statements.opinions import load_opinion

            for record in opinions_records:
                symbol = record["company_symbol"]
                if symbol not in docs_by_symbol or symbol not in companies:
                    opinions_report["skipped_no_document"].append(symbol)
                    continue
                _row, created = load_opinion(
                    session,
                    company_id=companies[symbol].id,
                    data_source=ds_by_symbol[symbol],
                    document_id=docs_by_symbol[symbol].id,
                    record=record,
                )
                opinions_report["records"].append(
                    {
                        "company": symbol,
                        "scope": record["opinion_scope"],
                        "type": record["opinion_type"],
                        "created": created,
                    }
                )
                if created:
                    opinions_report["written"] += 1
                else:
                    opinions_report["skipped_existing"] += 1
        if commit:
            session.commit()
        else:
            session.rollback()
        report = {
            "status": "committed" if commit else "dry-run",
            "written": written,
            "opinions": opinions_report,
            "maps": report_maps,
        }
        print(json.dumps(report, indent=2, default=str))
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
