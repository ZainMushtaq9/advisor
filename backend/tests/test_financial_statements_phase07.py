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
    extract_ogdc_face,
)
from app.services.financial_statements.validate import (
    check_balance_identity,
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
