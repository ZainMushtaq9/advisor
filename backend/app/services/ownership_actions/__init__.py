"""Phase 12 seed data: HUBC + HBL ownership, dividend actions, adjustment rules.

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

# ---------------------------------------------------------------------------
# HBL seed data (HBL re-run batch). Every number below was extracted
# from the already-downloaded HBL Annual Report 2025
# (storage/financial_reports/, gitignored) with TWO independent
# extractors (PyMuPDF and pdfplumber) that agreed on all values, and
# cross-checked: 77 body rows sum to 91,413 holders and 1,466,852,508
# shares (both exact against the printed totals); printed percentages
# sum to 99.96 against the printed total 100.00 (0.04 rounding across
# 2-decimal rows, same phenomenon as HUBC's 99.99).
#
# Reporting date 2025-12-31 ("AS AT DECEMBER 31, 2025"). Publication
# date 2026-03-03 is the consolidated auditor-report date (the same
# date Phase 9 uses as the HBL income publication date). Printed
# pages 397-398 (PDF pages 399-400). Source key:
# hbl_ir_annual_report_2025 (existing Phase 7 data source row).
#
# Structure note: unlike HUBC's category table, HBL prints named
# rows inside sections (5%+ holders, directors, associated parties,
# modarabas/mutual funds) plus single-row categories. All 77 body
# rows are stored: named rows carry their printed name and printed
# percentage; single-row categories carry holders/shares/percentage.
# No folio numbers are printed in the HBL table, so folio is NULL
# for every HBL row. The printed "five percent or more" heading is
# kept verbatim even though British International Investment PLC is
# printed at 4.99% — the heading is the document's, not a claim.
# ---------------------------------------------------------------------------

HBL_REPORTING_DATE = date(2025, 12, 31)
HBL_PUBLICATION_DATE = date(2026, 3, 3)
HBL_PUBLICATION_NOTE = (
    "Consolidated auditor-report date (KPMG Taseer Hadi & Co., "
    "03 March 2026), the same date Phase 9 uses as the HBL income "
    "publication date; the shareholding tables print no separate "
    "publication date."
)
HBL_SOURCE_KEY = "hbl_ir_annual_report_2025"
HBL_SOURCE_EVIDENCE = {
    "document": "HBL Annual Report 2025",
    "printed_pages": "397-398",
    "pdf_pages": "399-400",
    "extractors": ["pymupdf", "pdfplumber"],
    "extractors_agree": True,
    "reconciliation": {
        "body_rows": 77,
        "shareholders_sum": 91413,
        "shares_sum": 1466852508,
        "percentages_sum": 99.96,
        "percentages_printed_total": 100.00,
        "percentages_note": "0.04 rounding difference across 2-decimal rows; printed total is 100.00",
        "modaraba_mutual_fund_rows": 54,
    },
}

# (category, holders, shares, percentage) — single-row categories only.
HBL_CATEGORY_ROWS = [
    ("EXECUTIVES_EMPLOYEES", 18, 2972376, "0.20"),
    ("NIT_ICP", 1, 1608726, "0.11"),
    ("BANKS_DFI_NBFI", 14, 3346602, "0.23"),
    ("INSURANCE_COMPANY", 12, 11422505, "0.78"),
    ("GENERAL_PUBLIC_LOCAL", 90726, 114729725, "7.82"),
    ("GENERAL_PUBLIC_FOREIGN", 246, 370036, "0.03"),
    ("FOREIGN_COMPANY", 42, 149822537, "10.21"),
    ("OTHERS", 284, 142789782, "9.73"),
]

# (category, name, shares, percentage) — named rows inside sections.
# No folios are printed in the HBL table.
HBL_KEY_HOLDERS = [
    ("FIVE_PCT_PLUS", "AGA KHAN FUND FOR ECONOMIC DEVELOPMENT", 829967872, "56.58"),
    ("FIVE_PCT_PLUS", "BRITISH INTERNATIONAL INVESTMENT PLC", 73342000, "4.99"),
    ("DIRECTOR_CEO_SPOUSE_MINOR", "MS. SABA KAMAL", 12410, "0.00"),
    ("DIRECTOR_CEO_SPOUSE_MINOR", "MR. KHALEEL AHMED", 10, "0.00"),
    ("DIRECTOR_CEO_SPOUSE_MINOR", "SYED SALIM RAZA", 600, "0.00"),
    ("DIRECTOR_CEO_SPOUSE_MINOR", "MR. MUHAMMAD NASSIR SALIM", 265933, "0.02"),
    ("DIRECTOR_CEO_SPOUSE_MINOR", "DR. NAJEEB SAMIE", 50500, "0.00"),
    ("ASSOCIATED_RELATED", "TRUSTEE HBL EMPLOYEES GRATUITY FUND TRUST", 2639039, "0.18"),
    ("ASSOCIATED_RELATED", "TRUSTEE- HBL EMPLOYEES PENSION FUND TRUST", 13238341, "0.90"),
    ("ASSOCIATED_RELATED", "TRUSTEES OF HABIB BANK LTD EMPLOYEES PROVIDENT FUND", 5485962, "0.37"),
    ("ASSOCIATED_RELATED", "JUBILEE GENERAL INSURANCE COMPANY LIMITED", 4270000, "0.29"),
    ("ASSOCIATED_RELATED", "THE AGA KHAN UNIVERSITY FOUNDATION", 17173361, "1.17"),
    ("ASSOCIATED_RELATED", "TRUSTEES OF HBL DEFERRED REMUNERATION TRUST FUND", 8253907, "0.56"),
    ("ASSOCIATED_RELATED", "CDC - TRUSTEE HBL EQUITY FUND", 304000, "0.02"),
    ("ASSOCIATED_RELATED", "JUBILEE LIFE INSURANCE COMPANY LIMITED", 47429121, "3.23"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE MCB PAKISTAN STOCK MARKET FUND", 4237941, "0.29"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE PAKISTAN CAPITAL MARKET FUND", 152000, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE HBL INVESTMENT FUND", 116500, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE JS LARGE CAP. FUND", 226524, "0.02"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE HBL GROWTH FUND", 385700, "0.03"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ATLAS STOCK MARKET FUND", 5430710, "0.37"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE UBL GROWTH AND INCOME FUND", 687000, "0.05"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE FAYSAL STOCK FUND", 29200, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ALFALAH GHP VALUE FUND", 30000, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE UNIT TRUST OF PAKISTAN", 142000, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE AKD INDEX TRACKER FUND", 216604, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE AKD OPPORTUNITY FUND", 250000, "0.02"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE UBL STOCK ADVANTAGE FUND", 4574033, "0.31"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE NBP STOCK FUND", 3651021, "0.25"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE NBP BALANCED FUND", 135680, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ALFALAH GHP INCOME MULTIPLIER FUND", 44000, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE APF-EQUITY SUB FUND", 319000, "0.02"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE JS PENSION SAVINGS FUND - EQUITY ACCOUNT", 19450, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE HBL - STOCK FUND", 426000, "0.03"),
    ("MODARABA_MUTUAL_FUND", "MC FSL - TRUSTEE JS GROWTH FUND", 275000, "0.02"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE HBL MULTI - ASSET FUND", 9800, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ALFALAH GHP STOCK FUND", 1837005, "0.13"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE PAKISTAN INCOME ENHANCEMENT FUND", 150000, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ALFALAH GHP ALPHA FUND", 561727, "0.04"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE NIT-EQUITY MARKET OPPORTUNITY FUND", 2720334, "0.19"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ABL STOCK FUND", 1184331, "0.08"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE AL HABIB STOCK FUND", 1459333, "0.10"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE LAKSON EQUITY FUND", 758064, "0.05"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE NBP SARMAYA IZAFA FUND", 70666, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE HBL PF EQUITY SUB FUND", 29400, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE UBL ASSET ALLOCATION FUND", 420958, "0.03"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE FIRST CAPITAL MUTUAL FUND", 20000, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE UBL RETIREMENT SAVINGS FUND - EQUITY SUB FUND", 895000, "0.06"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ABL PENSION FUND - EQUITY SUB FUND", 36695, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC-TRUSTEE NITPF EQUITY SUB-FUND", 34500, "0.00"),
    ("MODARABA_MUTUAL_FUND", "ABA ALI HABIB SECURITIES (PVT) LIMITED - MF", 100, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ALFALAH MTS FUND - MT", 803114, "0.05"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE LAKSON TACTICAL FUND", 15800, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE AL HABIB ASSET ALLOCATION FUND", 90000, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE NBP FINANCIAL SECTOR FUND", 308675, "0.02"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE UBL FINANCIAL SECTOR FUND", 2976001, "0.20"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ALLIED FINERGY FUND", 20000, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE GOLDEN ARROW STOCK FUND", 540000, "0.04"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE NIT ASSET ALLOCATION FUND", 82823, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE NIT PAKISTAN GATEWAY EXCHANGE TRADED FUND", 34440, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ALFALAH FINANCIAL VALUE FUND-II", 19300, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE UBL PAKISTAN ENTERPRISE EXCHANGE TRADED FUND", 79808, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE NBP PAKISTAN GROWTH EXCHANGE TRADED FUND", 38335, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE NBP FINANCIAL SECTOR INCOME FUND - MT", 49518, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ALFALAH GHP DEDICATED EQUITY FUND", 59000, "0.00"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE HBL FINANCIAL SECTOR INCOME FUND PLAN I - MT", 98248, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE MCB PAKISTAN DIVIDEND YIELD PLAN", 506000, "0.03"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE JS GLOBAL BANKING SECTOR EXCHANGE TRADED FUND", 84825, "0.01"),
    ("MODARABA_MUTUAL_FUND", "CDC - TRUSTEE ABL OPTIMAL ASSET ALLOCATION FUND", 15000, "0.00"),
]

HBL_TOTAL = (91413, 1466852508, "100.00")

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
    # HBL FY2025 actions (HBL re-run batch), from the loaded 2025
    # changes-in-equity face (total scope). Same DATE_EVIDENCE as
    # HUBC/NML: all five date columns NULL (appropriations by fiscal
    # year and per-share amount only). Appropriation totals are
    # evidence only, never asserted action totals — and note the
    # cash-flow statement's dividend_paid for 2025 (Rs 26,610,622,000)
    # differs from the CE appropriation sum (Rs 26,770,058,000) by
    # Rs 159,436,000 (declaration-vs-payment timing: the final
    # dividend is declared subsequent to the year-end), so no single
    # total is asserted. FY2024 actions (final Rs 4.00 + three
    # interims Rs 4.00) exist in the 2024 face but are not separately
    # actioned here, following the HUBC pattern (prior-year interims
    # not separately actioned; only the latest year's set).
    (
        "HBL",
        "DIVIDEND_CASH",
        "FY2025 final",
        "4.25",
        "Appropriation total Rs 6,234,123,000 per CE face (total scope); "
        "recorded as evidence only, not as an asserted action total.",
        {
            "statement_label": "Final cash dividend - Rs 4.25 per share declared subsequent "
            "to the year ended December 31, 2024",
            "statement_type": "changes_in_equity",
            "periods": ["2025-01-01 to 2025-12-31"],
        },
    ),
    (
        "HBL",
        "DIVIDEND_CASH",
        "FY2025 first interim",
        "4.50",
        "Appropriation total Rs 6,600,836,000 per CE face (total scope); "
        "recorded as evidence only, not as an asserted action total.",
        {
            "statement_label": "1st interim cash dividend - Rs 4.50 per share",
            "statement_type": "changes_in_equity",
            "periods": ["2025-01-01 to 2025-12-31"],
        },
    ),
    (
        "HBL",
        "DIVIDEND_CASH",
        "FY2025 second interim",
        "4.50",
        "Appropriation total Rs 6,600,836,000 per CE face (total scope); "
        "recorded as evidence only, not as an asserted action total.",
        {
            "statement_label": "2nd interim cash dividend - Rs 4.50 per share",
            "statement_type": "changes_in_equity",
            "periods": ["2025-01-01 to 2025-12-31"],
        },
    ),
    (
        "HBL",
        "DIVIDEND_CASH",
        "FY2025 third interim",
        "5.00",
        "Appropriation total Rs 7,334,263,000 per CE face (total scope); "
        "recorded as evidence only, not as an asserted action total.",
        {
            "statement_label": "3rd interim cash dividend - Rs 5.00 per share",
            "statement_type": "changes_in_equity",
            "periods": ["2025-01-01 to 2025-12-31"],
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
