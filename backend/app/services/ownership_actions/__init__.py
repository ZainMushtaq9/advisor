"""Phase 12 seed data: HUBC ownership, dividend actions, adjustment rules.

Every number below was extracted from the already-downloaded HUBC
Integrated Annual Report 2026 (storage/financial_reports/, gitignored)
with TWO independent extractors (PyMuPDF and pdfplumber) that agreed
on all values, and cross-checked: category shareholders sum to 80,377,
category shares sum to 1,297,154,387, category percentages sum to
99.99 (100.00 printed; 0.01 rounding), associated-company named
holdings sum to 264,146,002 (the category total), director named
holdings sum to 1,006,244 (the category total).

Reporting date 2026-06-30 ("As on June 30, 2026"). Publication date
2026-09-21 is the auditor-report date used as publication proxy, the
same convention Phase 11 used for HUBC earnings. Printed pages 383-384
(PDF pages 384-385). Source key: hubc_annual_report_2026.

NOT stored, deliberately:
- Free float: no free-float figure is published in this document, and
  PSX free-float data is Terms-gated. No free-float-adjusted market
  measure is computed in this phase.
- The "OTHERS" line is a section header, not a category; only its six
  sub-rows are stored.
- NIT & ICP is printed as "-" for holders, shares and percentage: it
  is stored with 0 holders, 0 shares and NULL percentage (a printed
  dash is absence, not zero percent asserted — hence NULL).
"""

from __future__ import annotations

from datetime import date

REPORTING_DATE = date(2026, 6, 30)
PUBLICATION_DATE = date(2026, 9, 21)
PUBLICATION_NOTE = (
    "Auditor-report date used as publication proxy (same convention as "
    "Phase 11 HUBC earnings); the document itself prints no separate "
    "publication date beside the shareholding tables."
)
SOURCE_KEY = "hubc_ir_annual_report_2026"  # existing Phase 7 data source row
SOURCE_EVIDENCE = {
    "document": "HUBC Integrated Annual Report 2026",
    "printed_pages": "383-384",
    "pdf_pages": "384-385",
    "extractors": ["pymupdf", "pdfplumber"],
    "extractors_agree": True,
    "reconciliation": {
        "shareholders_sum": 80377,
        "shares_sum": 1297154387,
        "percentages_sum": 99.99,
        "percentages_printed_total": 100.00,
        "percentages_note": "0.01 rounding difference; printed total is 100.00",
        "cdc_note": "76,194 shareholders holding 1,293,129,998 shares via CDC; "
        "remainder 4,183 holders / 4,024,389 shares held outside CDC",
    },
}

# (category, holders, shares, percentage) — percentage None = printed "-".
CATEGORY_ROWS = [
    ("INDIVIDUAL_LOCAL", 79262, 496387210, "38.27"),
    ("INDIVIDUAL_FOREIGN", 320, 300283, "0.02"),
    ("JOINT_STOCK_COMPANY", 310, 40466679, "3.11"),
    ("FINANCIAL_INSTITUTION", 45, 72134823, "5.56"),
    ("INVESTMENT_COMPANY", 32, 26577092, "2.05"),
    ("INSURANCE_COMPANY", 28, 77235790, "5.95"),
    ("ASSOCIATED_COMPANY", 7, 264146002, "20.36"),
    ("DIRECTOR", 9, 1006244, "0.08"),
    ("EXECUTIVE", 5, 14400, "0.00"),
    ("NIT_ICP", 0, 0, None),
    ("MODARABA_MUTUAL_FUND_LEASING", 115, 140321749, "10.82"),
    ("OTHERS_GOVT_BALOCHISTAN", 1, 358607, "0.03"),
    ("OTHERS_GDR_DEPOSITORY", 1, 650, "0.00"),
    ("OTHERS_CHARITABLE_TRUST", 49, 122848220, "9.47"),
    ("OTHERS_COOPERATIVE_SOCIETY", 8, 1085522, "0.08"),
    ("OTHERS_PROVIDENT_PENSION_GRATUITY", 184, 48996921, "3.78"),
    ("EMPLOYEES_OLD_AGE_BENEFITS_INSTITUTION", 1, 5274195, "0.41"),
]

# (category, name, folio, shares). Two folios each for MEGA CONGLOMERATE
# and MUHAMMAD KAMRAN KAMAL are stored as separate rows, never merged.
KEY_HOLDERS = [
    (
        "ASSOCIATED_COMPANY",
        "IMPERIAL DEVELOPERS AND BUILDER (PRIVATE) LIMITED",
        "02832-2798",
        235967,
    ),
    ("ASSOCIATED_COMPANY", "MEGA CONGLOMERATE (PVT.) LIMITED", "02832-2921", 28213975),
    ("ASSOCIATED_COMPANY", "FORBES SHIPPING COMPANY (PRIVATE) LIMITED", "03277-100759", 2871885),
    ("ASSOCIATED_COMPANY", "INSERVEY PAKISTAN (PVT) LTD.", "03277-28342", 216910),
    ("ASSOCIATED_COMPANY", "INSHIPPING (PRIVATE) LIMITED.", "03277-38034", 3310721),
    ("ASSOCIATED_COMPANY", "MEGA CONGLOMERATE (PVT.) LIMITED", "03277-99174", 224428064),
    ("ASSOCIATED_COMPANY", "ASKARI BANK LIMITED", "05132-26", 4868480),
    ("DIRECTOR", "MUHAMMAD HABIB ULLAH KHAN", "01826-108001", 560),
    ("DIRECTOR", "ALY KHAN", "01826-108019", 560),
    ("DIRECTOR", "ALEEYA KHAN", "01826-108043", 560),
    ("DIRECTOR", "SHAFIUDDIN GHANI KHAN", "01826-69757", 203000),
    ("DIRECTOR", "SAAD IQBAL", "03277-94315", 613870),
    ("DIRECTOR", "SYED BAKHTIYAR KAZMI", "06122-191858", 50),
    ("DIRECTOR", "MANZOOR AHMED", "06452-56706", 5),
    ("DIRECTOR", "MUHAMMAD KAMRAN KAMAL", "10629-402670", 87639),
    ("DIRECTOR", "MUHAMMAD KAMRAN KAMAL", "12732-9520", 100000),
]

DATE_EVIDENCE = (
    "Announced, ex, record, effective and payment dates are NOT "
    "published in the loaded statements: the changes-in-equity faces "
    "record appropriations by fiscal year and per-share amount only. "
    "All five date columns are NULL for this reason; the statement "
    "period is the only date evidence and is recorded in "
    "source_evidence. No date is inferred."
)

# (ticker, action_type, fiscal_year_label, dps, total_note, evidence)
DIVIDEND_ACTIONS = [
    (
        "HUBC",
        "DIVIDEND_CASH",
        "FY2024-25 final",
        "10.00",
        "Two statement faces report different appropriation totals "
        "(Rs 12,971,544,000 in the FY2025-26 statement; Rs 11,025,812,000 "
        "in the FY2024-25 statement). No single total is asserted.",
        {
            "statement_label": "Final dividend for the fiscal year 2024-25 @ Rs. 10 "
            "(2023-24 @ Rs. 8.50) per share",
            "statement_type": "changes_in_equity",
            "periods": ["2025-07-01 to 2026-06-30", "2024-07-01 to 2025-06-30"],
        },
    ),
    (
        "HUBC",
        "DIVIDEND_CASH",
        "FY2025-26 first interim",
        "5.00",
        "Appropriation total Rs 6,485,772,000 per statement face; "
        "recorded as evidence only, not as an asserted action total.",
        {
            "statement_label": "First interim dividend for the fiscal year 2025-26 @ Rs. 5 "
            "(2024-25 @ Rs. 5) per share",
            "statement_type": "changes_in_equity",
            "periods": ["2025-07-01 to 2026-06-30"],
        },
    ),
    (
        "HUBC",
        "DIVIDEND_CASH",
        "FY2025-26 second interim",
        "5.00",
        "Appropriation total Rs 6,485,772,000 per statement face; "
        "recorded as evidence only, not as an asserted action total.",
        {
            "statement_label": "Second interim dividend for the fiscal year 2025-26 @ Rs. 5 "
            "(2024-25 @ Rs. Nil) per share",
            "statement_type": "changes_in_equity",
            "periods": ["2025-07-01 to 2026-06-30"],
        },
    ),
    (
        "HUBC",
        "DIVIDEND_CASH",
        "FY2025-26 third interim",
        "5.00",
        "Appropriation total Rs 6,485,772,000 per statement face; "
        "recorded as evidence only, not as an asserted action total.",
        {
            "statement_label": "Third interim dividend for the fiscal year 2025-26 @ Rs. 5 "
            "(2024-25 @ Rs. Nil) per share",
            "statement_type": "changes_in_equity",
            "periods": ["2025-07-01 to 2026-06-30"],
        },
    ),
    (
        "NML",
        "DIVIDEND_CASH",
        "FY2023 final",
        "5.00",
        "Appropriation total Rs 1,757,999,000 repeated across statement "
        "components; recorded as evidence only, not as an asserted "
        "action total, because component rows cannot be distinguished "
        "from a total-column row in the loaded data.",
        {
            "statement_label": "Final dividend for the year ended 30 June 2023 @ Rupees 5.00 "
            "per share",
            "statement_type": "changes_in_equity",
            "periods": ["nine months ended 31 March 2025 statement"],
        },
    ),
]

ADJUSTMENT_RULES = [
    {
        "rule_key": "DIVIDEND_CASH",
        "action_type": "DIVIDEND_CASH",
        "formula": "adjusted_close = raw_close - dividend_per_share, applied to "
        "prices on or after the ex-date. Raw rows are never modified; "
        "the adjusted value is a derived view only.",
        "requires": {"ex_date": "date", "dividend_per_share": "PKR"},
        "description": "Cash dividend adjustment. Needs an ex-date; with no "
        "ex-date on any stored action, this rule is defined but not "
        "applied to any series in this run.",
        "application_status": "defined_not_applied",
    },
    {
        "rule_key": "BONUS_ISSUE",
        "action_type": "BONUS_ISSUE",
        "formula": "factor = (existing_shares + bonus_shares) / existing_shares; "
        "adjusted_close = raw_close / factor; adjusted_volume = "
        "raw_volume * factor. Raw rows are never modified.",
        "requires": {"bonus_ratio": "new shares per existing share", "ex_date": "date"},
        "description": "Bonus issue adjustment. No bonus action is stored in "
        "this run, so the rule is defined but not applied.",
        "application_status": "defined_not_applied",
    },
    {
        "rule_key": "SPLIT",
        "action_type": "SPLIT",
        "formula": "factor = new_shares / old_shares for the same holding; "
        "adjusted_close = raw_close / factor; adjusted_volume = "
        "raw_volume * factor. Raw rows are never modified.",
        "requires": {"split_ratio": "new per old", "ex_date": "date"},
        "description": "Stock split adjustment. No split action is stored in "
        "this run, so the rule is defined but not applied.",
        "application_status": "defined_not_applied",
    },
    {
        "rule_key": "RIGHTS_ISSUE",
        "action_type": "RIGHTS_ISSUE",
        "formula": "theoretical_ex_rights_price = (market_cap_before + "
        "new_shares * subscription_price) / (old_shares + new_shares); "
        "adjustment factor = theoretical_ex_rights_price / "
        "cum_rights_price. Requires subscription price, ratio and "
        "ex-date; none is stored in this run.",
        "requires": {"subscription_price": "PKR", "rights_ratio": "new per old", "ex_date": "date"},
        "description": "Rights issue adjustment (TERP method). No rights action "
        "is stored in this run, so the rule is defined but not applied.",
        "application_status": "defined_not_applied",
    },
]
