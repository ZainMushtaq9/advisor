"""Phase 7 parser, number, and validator tests.

Synthetic faces only; no test ever touches a real database. Expected
values are hand-computed from the documented rules, and the OGDC
fixtures mirror the real two-panel OCR layout (including its traps:
section headers containing a later label, hyphenated labels, and
bare subtotal lines shared with the other panel's row).
"""

from __future__ import annotations

from decimal import Decimal

from app.services.financial_statements import numbers
from app.services.financial_statements.extract import (
    _token_value,
    extract_face,
    extract_face_from,
    extract_ogdc_face,
)
from app.services.financial_statements.opinions import validate_opinion_record
from app.services.financial_statements.validate import (
    check_balance_identity,
    check_cross_component,
    check_subtotal,
)


def test_parse_number_parentheses_negative():
    value, missing, sign_inferred = numbers.parse_number("(41,438,192)")
    assert value == Decimal("-41438192")
    assert missing is False
    assert sign_inferred is False


def test_parse_number_dash_is_missing_not_zero():
    value, missing, sign_inferred = numbers.parse_number("-")
    assert value is None
    assert missing is True


def test_parse_number_trailing_paren_sign_inferred():
    value, missing, sign_inferred = numbers.parse_number("579,205)")
    assert value == Decimal("-579205")
    assert sign_inferred is True


def test_parse_number_decimal_eps():
    value, _, _ = numbers.parse_number("38.26")
    assert value == Decimal("38.26")


def test_normalise_value_scaling():
    assert numbers.normalise_value(Decimal("422563444"), "thousands") == Decimal("422563444000")
    assert numbers.normalise_value(Decimal("5"), "millions") == Decimal("5000000")
    assert numbers.normalise_value(Decimal("5"), "rupees") == Decimal("5")
    assert numbers.normalise_value(None, "thousands") is None


def test_extract_face_note_ref_and_dash():
    lines = [
        (275, "Revenue from contracts with customers - net"),
        (275, "5"),
        (275, "71,126,352"),
        (275, "83,351,492"),
        (275, "Short term investments"),
        (275, "23"),
        (275, "3,993,713"),
        (275, "-"),
    ]
    specs = [
        {"label": "Revenue from contracts with customers - net", "key": "revenue"},
        {"label": "Short term investments", "key": "short_term_investments"},
    ]
    rows = extract_face(lines, specs, 2)
    assert rows[0]["values"] == [Decimal("71126352"), Decimal("83351492")]
    # Dash is NULL, never zero.
    assert rows[1]["values"] == [Decimal("3993713"), None]
    assert rows[1]["displayed"][1] == "-"


def test_extract_face_share_count_line_skipped():
    lines = [
        (35, "Issued, subscribed and paid-up share capital"),
        (35, "351,599,848 (30 June 2024: 351,599,848) ordinary shares of Rupees 10 each"),
        (35, "3,515,999"),
        (35, "3,515,999"),
    ]
    rows = extract_face(
        lines,
        [{"label": "Issued, subscribed and paid-up share capital", "key": "share_capital"}],
        2,
    )
    assert rows[0]["values"] == [Decimal("3515999"), Decimal("3515999")]


def test_extract_face_bare_subtotal_and_wrapped_label():
    lines = [
        (275, "Basic and diluted earnings per share attributable to owners"),
        (275, "of the holding company"),
        (275, "43"),
        (275, "38.26"),
        (275, "35.56"),
    ]
    rows = extract_face(
        lines,
        [
            {
                "label": (
                    "Basic and diluted earnings per share attributable "
                    "to owners of the holding company"
                ),
                "key": "eps_header",
            },
            {"label": None, "key": "eps_total"},
        ],
        2,
    )
    # The header row itself takes the following values in this
    # synthetic layout; the bare spec then finds nothing and flags.
    assert rows[0]["values"] == [Decimal("38.26"), Decimal("35.56")]
    assert "incomplete_values" in rows[1]["flags"]


def test_extract_face_join_does_not_steal_next_row():
    # Regression: a label wholly on the next line must not
    # false-match via the two-line join at the previous line.
    lines = [
        (8, "Income tax 20 (14,165,527) (31,264,908)"),
        (8, "Profit for the period 34,714,402 41,436,755"),
    ]
    rows = extract_face(
        lines,
        [{"label": "Profit for the period", "key": "profit_for_period"}],
        2,
    )
    assert rows[0]["values"] == [Decimal("34714402"), Decimal("41436755")]
    assert rows[0]["page"] == 8


def test_balance_identity_pass_and_fail():
    rows = [
        {"key": "total_assets", "values": [Decimal("100")]},
        {"key": "total_equity", "values": [Decimal("60")]},
        {"key": "non_current_liabilities_total", "values": [Decimal("25")]},
        {"key": "current_liabilities_total", "values": [Decimal("15")]},
    ]
    ok, detail = check_balance_identity(
        rows, 0, ["total_equity"], ["non_current_liabilities_total", "current_liabilities_total"]
    )
    assert ok is True
    assert detail["difference"] == "0"
    rows[3]["values"] = [Decimal("16")]
    ok, detail = check_balance_identity(
        rows, 0, ["total_equity"], ["non_current_liabilities_total", "current_liabilities_total"]
    )
    assert ok is False
    assert detail["difference"] == "-1"


def test_ogdc_two_panel_with_header_guard_and_bare_lines():
    lines = [
        (7, "SHARE CAPITAL AND RESERVES NON CURRENT ASSETS"),
        (
            7,
            "Share capital 43,009,284 43,009,284 "
            "Property, plant and equipment 8 118,479,239 97,861,516",
        ),
        (
            7,
            "Reserves 4 33,573,914 33,909,396 "
            "Exploration and evaluation assets 10 24,787,873 28,939,818",
        ),
        (7, "300,460,611 265,813,084"),
        (7, "Unappropriated profit 1,307,054,273 1,271,317,916"),
        (7, "1,383,637,471 1,348,236,596"),
    ]
    left_specs = [
        {"label": "Share capital", "key": "share_capital"},
        {"label": "Reserves", "key": "reserves"},
        {"label": "Unappropriated profit", "key": "unappropriated_profit"},
        {"label": None, "key": "total_equity"},
    ]
    right_specs = [
        {"label": "Property, plant and equipment", "key": "ppe"},
        {"label": "Exploration and evaluation assets", "key": "exploration"},
        {"label": None, "key": "operating_subtotal"},
    ]
    right_labels = ["Property, plant and equipment", "Exploration and evaluation assets"]
    left, right = extract_ogdc_face(lines, left_specs, right_specs, right_labels, 2)
    by_key = {r["key"]: r for r in left + right}
    # The section header must NOT consume share_capital.
    assert by_key["share_capital"]["values"] == [Decimal("43009284"), Decimal("43009284")]
    assert by_key["reserves"]["values"] == [Decimal("33573914"), Decimal("33909396")]
    assert by_key["exploration"]["values"] == [Decimal("24787873"), Decimal("28939818")]
    # The bare right subtotal takes the numbers-only line, not the
    # previous row's second column.
    assert by_key["operating_subtotal"]["values"] == [Decimal("300460611"), Decimal("265813084")]
    assert by_key["total_equity"]["values"] == [Decimal("1383637471"), Decimal("1348236596")]


def test_token_value_parse_failure_is_not_a_value():
    # Regression (audit C2): the fragment "(30" from "(30 June
    # 2024: ...)" must never occupy a column with NULL.
    value, is_value, _ = _token_value("(30")
    assert is_value is False
    assert value is None


def test_extract_face_share_count_split_lines_real_layout():
    # Regression (audit C2): real NML p.35 layout — the share count
    # and its "ordinary shares" unit are on SEPARATE lines.
    lines = [
        (35, "Issued, subscribed and paid-up share capital"),
        (35, "351,599,848 (30 June 2024: 351,599,848)"),
        (35, "   ordinary shares of Rupees 10 each "),
        (35, "3,515,999 "),
        (35, "3,515,999"),
    ]
    rows = extract_face(
        lines,
        [{"label": "Issued, subscribed and paid-up share capital", "key": "share_capital"}],
        2,
    )
    assert rows[0]["values"] == [Decimal("3515999"), Decimal("3515999")]


def test_extract_face_share_values_on_ordinary_shares_line():
    # pdftotext -layout variant: the true values sit ON the
    # "ordinary shares" line itself, after the unit phrase.
    lines = [
        (35, "Issued, subscribed and paid-up share capital"),
        (35, "351,599,848 (30 June 2024: 351,599,848)"),
        (
            35,
            "  ordinary shares of Rupees 10 each"
            "                                         3,515,999        3,515,999",
        ),
    ]
    rows = extract_face(
        lines,
        [{"label": "Issued, subscribed and paid-up share capital", "key": "share_capital"}],
        2,
    )
    assert rows[0]["values"] == [Decimal("3515999"), Decimal("3515999")]


def test_extract_face_bare_subtotal_skips_note_ref():
    # Regression (audit C1): a bare subtotal preceded by a lone
    # note reference must skip the note, not take it as a value.
    lines = [
        (275, "- Discontinued operations "),
        (275, " -    "),
        (275, " 0.12 "),
        (275, "Basic and diluted earnings per share attributable to owners"),
        (275, "of the holding company"),
        (275, "43  "),
        (275, " 38.26  "),
        (275, " 35.56 "),
    ]
    rows = extract_face(
        lines,
        [
            {"label": "Discontinued operations", "key": "eps_discontinued"},
            {
                "label": (
                    "Basic and diluted earnings per share attributable "
                    "to owners of the holding company"
                ),
                "key": "eps_total",
            },
        ],
        2,
    )
    assert rows[0]["values"] == [None, Decimal("0.12")]
    assert rows[1]["values"] == [Decimal("38.26"), Decimal("35.56")]


def test_extract_face_bare_path_skips_lone_note_ref():
    # Defense in depth for C1: even a genuinely bare total must
    # not take a preceding lone note reference as its first value.
    lines = [
        (275, "- Discontinued operations "),
        (275, " -    "),
        (275, " 0.12 "),
        (275, "Basic and diluted earnings per share attributable to owners"),
        (275, "of the holding company"),
        (275, "43  "),
        (275, " 38.26  "),
        (275, " 35.56 "),
    ]
    rows = extract_face(
        lines,
        [
            {"label": "Discontinued operations", "key": "eps_discontinued"},
            {"label": None, "key": "eps_total"},
        ],
        2,
    )
    assert rows[1]["values"] == [Decimal("38.26"), Decimal("35.56")]


def test_check_subtotal_missing_fail_vs_zero():
    rows = [
        {"key": "total", "values": [Decimal("100")]},
        {"key": "a", "values": [Decimal("60")]},
        {"key": "b", "values": [None]},
    ]
    ok, detail = check_subtotal(rows, "total", ["a", "b"], 0)
    assert ok is False
    assert detail["keys"] == ["b"]
    # Missing-as-zero is explicit: the key is listed in the detail.
    ok, detail = check_subtotal(rows, "total", ["a", "b"], 0, missing="zero")
    assert ok is False  # 60 != 100 even with b as zero
    assert detail["missing_as_zero"] == ["b"]


def test_ogdc_grand_total_four_token_line():
    lines = [
        (7, "TOTAL LIABILITIES 302,979,745 306,369,374 1,113,550,304 1,123,383,935"),
        (7, "1,686,617,216 1,654,605,970 1,686,617,216 1,654,605,970"),
    ]
    left_specs = [
        {"label": "TOTAL LIABILITIES", "key": "total_liabilities"},
        {"label": None, "key": "grand_total"},
    ]
    right_specs = [
        {"label": None, "key": "current_assets_total"},
        {"label": None, "key": "total_assets"},
    ]
    left, right = extract_ogdc_face(lines, left_specs, right_specs, [], 2)
    left_by_key = {r["key"]: r for r in left}
    right_by_key = {r["key"]: r for r in right}
    assert left_by_key["total_liabilities"]["values"] == [
        Decimal("302979745"),
        Decimal("306369374"),
    ]
    # Excess tokens on the TOTAL LIABILITIES line feed the right bare.
    assert right_by_key["current_assets_total"]["values"] == [
        Decimal("1113550304"),
        Decimal("1123383935"),
    ]
    assert left_by_key["grand_total"]["values"] == [Decimal("1686617216"), Decimal("1654605970")]
    assert right_by_key["total_assets"]["values"] == [Decimal("1686617216"), Decimal("1654605970")]


# ---------------------------------------------------------------------------
# Phase 7 remainders: multi-segment note refs, cursor block extraction,
# matrix cross-component checks, and opinion-record validation.
# ---------------------------------------------------------------------------


def test_is_note_ref_multi_segment():
    # HUBC note 16.1.1 is a reference, not a value.
    assert numbers.is_note_ref("16.1.1") is True
    assert numbers.is_note_ref("14.3") is True
    assert numbers.is_note_ref("42") is True
    # Genuine decimals must never be mistaken for references.
    assert numbers.is_note_ref("38.26") is False
    assert numbers.is_note_ref("5.00") is False
    assert numbers.is_note_ref("8.50") is False


def test_extract_face_from_cursor_resolves_repeated_labels():
    lines = [
        (39, "Balance as at 30 June 2023"),
        (39, "3,515,999"),
        (39, "100,000"),
        (39, "Profit for the period"),
        (39, "50,000"),
        (39, "60,000"),
        (39, "Balance as at 31 March 2024"),
        (39, "3,515,999"),
        (39, "160,000"),
        (39, "Profit for the period"),
        (39, "70,000"),
        (39, "80,000"),
    ]
    block1 = [
        {"label": "Balance as at 30 June 2023", "key": "opening"},
        {"label": "Profit for the period", "key": "profit"},
        {"label": "Balance as at 31 March 2024", "key": "closing"},
    ]
    block2 = [{"label": "Profit for the period", "key": "profit"}]
    rows1, cursor = extract_face_from(lines, block1, 2, 0)
    assert [r["key"] for r in rows1] == ["opening", "profit", "closing"]
    assert rows1[0]["values"] == [Decimal("3515999"), Decimal("100000")]
    assert rows1[1]["values"] == [Decimal("50000"), Decimal("60000")]
    # Second block resolves the repeated label to its NEXT occurrence.
    rows2, _ = extract_face_from(lines, block2, 2, cursor)
    assert rows2[0]["values"] == [Decimal("70000"), Decimal("80000")]


def test_extract_face_from_scan_cap_for_tall_value_stacks():
    # 16 values on separate lines (content-stream order) exceed the
    # default 12-line scan cap; matrix extraction passes a larger cap.
    lines = [(39, "Some reserve row")] + [(39, f"{i + 1},000") for i in range(16)]
    specs = [{"label": "Some reserve row", "key": "row"}]
    rows, _ = extract_face_from(lines, specs, 16, 0)
    assert "incomplete_values" in rows[0]["flags"]
    rows, _ = extract_face_from(lines, specs, 16, 0, scan_cap=40)
    assert "incomplete_values" not in rows[0]["flags"]
    assert rows[0]["values"][0] == Decimal("1000")
    assert rows[0]["values"][15] == Decimal("16000")


def test_label_ending_hyphen_paren_does_not_leak_year():
    # NML balance rows end "2023- (Audited)": normalise merges the
    # hyphen spacing into "2023-(audited)", so a last-word search
    # on the normalised label never matches a raw token and the
    # remainder used to fall back to the full line, leaking 2023
    # in as the first value.
    lines = [
        (
            39,
            "Balance as at 30 June 2023- (Audited) 3,515,999 5,499,530",
        )
    ]
    specs = [{"label": "Balance as at 30 June 2023- (Audited)", "key": "opening"}]
    rows, _ = extract_face_from(lines, specs, 2, 0)
    assert rows[0]["values"] == [Decimal("3515999"), Decimal("5499530")]
    assert rows[0]["flags"] == []


def test_joined_label_with_dash_glued_last_word():
    # pdftotext -layout glues the values' dash columns onto the
    # second line's last word ("interest------------"); the join
    # acceptance must strip those dashes before comparing.
    # Real 16-column shape: 14 dash columns, then the NCI and
    # total-equity values on the second line.
    lines = [
        (39, "Transaction with owners - Dividend relating to year 2023"),
        (
            39,
            "paid to non-controlling interest " + "- " * 14 + "(954,006) (954,006)",
        ),
    ]
    specs = [
        {
            "label": (
                "Transaction with owners - Dividend relating to year 2023 "
                "paid to non-controlling interest"
            ),
            "key": "div_nci",
        }
    ]
    rows, _ = extract_face_from(lines, specs, 16, 0)
    assert "label_not_found" not in rows[0]["flags"]
    assert rows[0]["values"][14:] == [Decimal("-954006"), Decimal("-954006")]
    assert rows[0]["values"][:14] == [None] * 14


def test_check_cross_component_matrix_total():
    rows = [
        {
            "key": "balance_closing",
            "values": [
                Decimal("100"),
                Decimal("250"),
                Decimal("350"),
            ],
        }
    ]
    ok, detail = check_cross_component(rows, "balance_closing", 2, [0, 1])
    assert ok is True
    assert detail["difference"] == "0"
    ok, detail = check_cross_component(rows, "balance_closing", 2, [0])
    assert ok is False
    assert detail["difference"] == "250"


def test_check_cross_component_missing_as_zero_only_for_dashes():
    rows = [{"key": "balance_closing", "values": [Decimal("100"), None, Decimal("100")]}]
    ok, detail = check_cross_component(rows, "balance_closing", 2, [0, 1], missing="zero")
    assert ok is True
    assert detail["missing_as_zero"] == [1]
    ok, _ = check_cross_component(rows, "balance_closing", 2, [0, 1], missing="fail")
    assert ok is False


def test_validate_opinion_record_present_and_absent():
    present = {
        "company_symbol": "HUBC",
        "opinion_scope": "consolidated",
        "opinion_type": "unmodified",
        "firm_name": "A. F. Ferguson & Co.",
        "opinion_date": "2026-09-21",
        "opinion_text": "In our opinion, ...",
    }
    assert validate_opinion_record(present) == []
    assert "requires firm_name" in " ".join(validate_opinion_record({**present, "firm_name": None}))
    absent = {
        "company_symbol": "NML",
        "opinion_scope": "consolidated_interim",
        "opinion_type": "none",
        "absence_note": "No review report included.",
    }
    assert validate_opinion_record(absent) == []
    errors = validate_opinion_record({**absent, "firm_name": "Someone"})
    assert any("must not carry firm_name" in e for e in errors)
    errors = validate_opinion_record({**absent, "absence_note": None})
    assert any("requires absence_note" in e for e in errors)
    errors = validate_opinion_record({**present, "opinion_type": "glowing"})
    assert any("unknown opinion_type" in e for e in errors)


def test_bare_row_skip_values_collects_pkr_after_usd():
    # HBL dual-currency faces print USD columns before PKR columns
    # in content-stream order. A bare row with skip_values=2 must
    # collect the PKR pair, not the USD pair.
    lines = [
        (75, "Other assets"),
        (75, "373,155,122"),
        (75, "312,582,486"),
        (75, "27,516,990"),
        (75, "21,615,898"),
        (75, "7,708,144,220"),
        (75, "6,055,112,877"),
    ]
    specs = [
        {"label": "Other assets", "key": "other_assets"},
        {"label": None, "key": "total_assets", "skip_values": 2},
    ]
    rows, _ = extract_face_from(lines, specs, 2, 0)
    assert rows[0]["values"] == [Decimal("373155122"), Decimal("312582486")]
    assert rows[1]["values"] == [Decimal("7708144220"), Decimal("6055112877")]
    assert "subtotal_position_inferred" in rows[1]["flags"]


def test_labeled_row_blank_columns_inserts_none_at_position():
    # HBL CE 2024 equity row: the NCI cell (index 2 of 4 here) is
    # blank in the source — no dash printed — while the total
    # column carries a value. blank_columns=[2] records None for
    # the blank cell instead of shifting the total into NCI.
    lines = [
        (78, "Movement in surplus on revaluation of equity investments - net of tax"),
        (78, "-"),
        (78, "3,278,951"),
        (78, "3,278,951"),
    ]
    specs = [
        {
            "label": "Movement in surplus on revaluation of equity investments - net of tax",
            "key": "oci_equity_investments",
            "blank_columns": [2],
        },
    ]
    rows, _ = extract_face_from(lines, specs, 4, 0)
    assert rows[0]["values"] == [None, Decimal("3278951"), None, Decimal("3278951")]
    assert "blank_column_recorded" in rows[0]["flags"]
    assert "incomplete_values" not in rows[0]["flags"]


def test_blank_columns_wrong_count_leaves_row_incomplete():
    # blank_columns applies only on an exact token fit; a row
    # that is short for another reason must still gate out.
    lines = [
        (78, "Movement in surplus on revaluation of equity investments - net of tax"),
        (78, "3,278,951"),
    ]
    specs = [
        {
            "label": "Movement in surplus on revaluation of equity investments - net of tax",
            "key": "oci_equity_investments",
            "blank_columns": [2],
        },
    ]
    rows, _ = extract_face_from(lines, specs, 4, 0)
    assert "incomplete_values" in rows[0]["flags"]
    assert "blank_column_recorded" not in rows[0]["flags"]


def test_label_parts_matches_value_interleaved_split_label():
    # HBL CF translation row: the label prints in two halves with
    # the USD value pair between them. label_parts matches each
    # half in order and collects the PKR pair after the last half.
    lines = [
        (79, "Proceeds from sale of property and equipment"),
        (79, "498,467"),
        (79, "550,830"),
        (79, "Effect of translation of net investment in foreign branches, subsidiaries"),
        (79, "17,119"),
        (79, "(9,818)"),
        (79, "and associates - net of tax"),
        (79, "4,795,377"),
        (79, "(2,750,167)"),
    ]
    specs = [
        {"label": "Proceeds from sale of property and equipment", "key": "ppe_sale_proceeds"},
        {
            "label": "Effect of translation of net investment in foreign branches, subsidiaries and associates - net of tax",
            "key": "translation_effect_investing",
            "label_parts": [
                "Effect of translation of net investment in foreign branches, subsidiaries",
                "and associates - net of tax",
            ],
        },
    ]
    rows, _ = extract_face_from(lines, specs, 2, 0)
    assert rows[1]["values"] == [Decimal("4795377"), Decimal("-2750167")]
    assert rows[1]["flags"] == []
