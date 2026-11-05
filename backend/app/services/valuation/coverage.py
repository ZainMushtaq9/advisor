"""Calculability assessment for Phase 9 (mirrors Phase 8 coverage.py).

For one company, every registered method gets exactly one verdict:
``computed`` (a Decimal value), ``insufficient_inputs`` (value None
+ the exact missing input or methodological reason), or
``not_applicable`` (the method has no meaning for this company's
structure — the bank residual-income model for industrial companies,
and industrial EV/DCF models for banks). No verdict ever carries a substituted zero
or an estimate, and no method is ever averaged with an incompatible
one: each row stands alone with its own method, inputs, and reason.

``inputs`` is the canonical dict built by runner.load_valuation_inputs:
price + price id + price date, EPS + income-statement publication
date, total/owners equity + balance-sheet date, sector + peer list,
and the exact statement/price id lists. A missing canonical input is
simply absent or None.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.valuation import PRICE_DATE, formulas
from app.services.valuation.formulas import book_value, trailing_pe

D = Decimal

NO_SHARES_REASON = (
    "no share-count data in the registry or statements: share capital "
    "is carried in PKR and cannot be converted to shares without a par "
    "value, which is not in the data"
)

NO_DCF_ASSUMPTIONS = (
    "no source-backed discount rate, growth rate, or forecast cash "
    "flows (Phase 10 macro inputs not available); assumptions must "
    "not be invented"
)


def _result(
    method_key: str,
    value,
    status: str,
    reason: str | None = None,
    flags: list[str] | None = None,
    sensitivity: dict | None = None,
) -> dict:
    return {
        "method_key": method_key,
        "status": status,
        "value": value,
        "reason": reason,
        "flags": flags or [],
        "sensitivity": sensitivity,
    }


def _computed(method_key: str, value, flags=None, sensitivity=None) -> dict:
    return _result(method_key, value, "computed", None, flags, sensitivity)


def _insufficient(method_key: str, reason: str, flags=None) -> dict:
    return _result(method_key, None, "insufficient_inputs", reason, flags)


def _na(method_key: str, reason: str) -> dict:
    return _result(method_key, None, "not_applicable", reason)


def _assess_pe(inputs: dict) -> dict:
    """Trailing P/E: the one price-based multiple that needs no share
    count. Point-in-time validity is enforced, not assumed."""
    price = inputs.get("price")
    eps = inputs.get("eps")
    pub = inputs.get("publication_date")
    if price is None:
        return _insufficient(
            "multiples:pe_trailing",
            "no close price on the valuation date",
        )
    if eps is None:
        return _insufficient(
            "multiples:pe_trailing",
            "no EPS line in the extracted income statement",
        )
    if eps <= 0:
        reason = f"non-meaningful multiple: printed EPS is {eps} (<= 0)"
        if pub is None:
            reason += (
                "; independently, point-in-time unverifiable: the income "
                "statement carries no publication date"
            )
        return _insufficient("multiples:pe_trailing", reason)
    if pub is None:
        return _insufficient(
            "multiples:pe_trailing",
            "point-in-time unverifiable: the income statement carries "
            "no publication date, so it cannot be shown published by "
            "the valuation date",
        )
    if pub > PRICE_DATE:
        return _insufficient(
            "multiples:pe_trailing",
            f"look-ahead: income statement published {pub} is after "
            f"the valuation date {PRICE_DATE}",
        )
    value = trailing_pe(price, eps)
    sensitivity = {
        "price_minus_10pct": formulas.price_sensitivity(price, eps, D("-0.10")),
        "price_plus_10pct": formulas.price_sensitivity(price, eps, D("0.10")),
        "note": "mechanical price sensitivity only; EPS held at its printed value",
    }
    return _computed(
        "multiples:pe_trailing",
        value,
        flags=[
            "single unadjusted official close; adjustment methodology "
            "matters for series, not for a single-date multiple",
            f"EPS period: {inputs.get('eps_period_label')}",
            f"statement published {pub}, on/before valuation date {PRICE_DATE}",
        ],
        sensitivity=sensitivity,
    )


def assess(ticker: str, inputs: dict) -> list[dict]:
    """Assess every registered method for one company.

    The ticker is accepted for a uniform call signature; the assessment
    itself reads only the inputs dict (no company-id lookup).
    """
    out: list[dict] = []
    sector = inputs.get("sector")
    peers = inputs.get("peers") or []
    # Banking branch: the financial-company rule (brief) — industrial
    # enterprise-value multiples and industrial DCF are never applied
    # to a bank. The sector name is the Phase 4 registry sector,
    # verbatim; COMMERCIAL BANKS is the only bank sector in scope.
    is_bank = sector == "COMMERCIAL BANKS"

    out.append(_assess_pe(inputs))

    for key, reason in (
        ("multiples:pb", NO_SHARES_REASON),
        ("multiples:ps", NO_SHARES_REASON),
        (
            "multiples:div_yield",
            "no dividend-per-share series: dividends_paid totals exist "
            "but no share count converts them to DPS",
        ),
        ("multiples:market_cap", NO_SHARES_REASON),
        (
            "multiples:enterprise_value",
            NO_SHARES_REASON + " (market cap unavailable)",
        ),
        (
            "multiples:cf_yield",
            NO_SHARES_REASON + " (operating cash flow per share unavailable)",
        ),
    ):
        out.append(_insufficient(key, reason))
    # EV multiples keep their registered position in the method order
    # (after ps, before div_yield); for banks they are
    # not_applicable by structure, not merely missing data.
    if is_bank:
        ev_entries = [
            _na(
                "multiples:ev_ebitda",
                "not_applicable_by_structure: enterprise-value multiples "
                "are industrial models; for a bank, debt is raw material "
                "and enterprise value has no meaning",
            ),
            _na(
                "multiples:ev_ebit",
                "not_applicable_by_structure: enterprise-value multiples "
                "are industrial models; for a bank, debt is raw material "
                "and enterprise value has no meaning",
            ),
        ]
    else:
        ev_entries = [
            _insufficient(
                "multiples:ev_ebitda",
                NO_SHARES_REASON + "; and no EBITDA line in the extracted statements",
            ),
            _insufficient(
                "multiples:ev_ebit",
                NO_SHARES_REASON + " (market cap unavailable)",
            ),
        ]
    # out currently holds pe, pb, ps, div_yield, market_cap,
    # enterprise_value, cf_yield; splice the EV entries back into
    # their registered position (index 3, after ps).
    out[3:3] = ev_entries

    if not peers:
        out.append(
            _insufficient(
                "multiples:peer_median_pe",
                "no genuinely comparable peers: the company is alone in "
                f"its sector ({sector}) among companies with statements; "
                "cross-sector peers are never forced",
            )
        )
    elif len(peers) < 3:
        out.append(
            _insufficient(
                "multiples:peer_median_pe",
                f"fewer than 3 comparable peers ({len(peers)}): a peer "
                "median is not robust and outlier treatment cannot run",
            )
        )
    else:
        out.append(
            _insufficient(
                "multiples:peer_median_pe",
                "peer multiples not yet computed: peer P/E values are "
                "themselves subject to each peer's point-in-time and "
                "EPS-validity rules (Phase 9 v1.0 records the peer set "
                "but does not average across it)",
            )
        )

    if is_bank:
        out.append(
            _na(
                "dcf:fcff",
                "not_applicable_by_structure: industrial enterprise-value "
                "DCF is never applied to a bank; free cash flow to the "
                "firm has no meaning when debt is raw material",
            )
        )
        out.append(
            _na(
                "dcf:fcfe",
                "not_applicable_by_structure: industrial DCF is never "
                "applied to a bank; the bank intrinsic model is "
                "residual income (assessed below), not FCFE",
            )
        )
    else:
        out.append(_insufficient("dcf:fcff", NO_DCF_ASSUMPTIONS))
        out.append(_insufficient("dcf:fcfe", NO_DCF_ASSUMPTIONS))
    out.append(
        _insufficient(
            "dividend:ddm",
            "no dividend-per-share series and no established payout-growth pattern",
        )
    )

    total_equity = inputs.get("total_equity")
    if total_equity is None:
        out.append(
            _insufficient(
                "asset_based:equity_book_value_total",
                "no total_equity line on the extracted balance sheet",
            )
        )
    else:
        out.append(
            _computed(
                "asset_based:equity_book_value_total",
                book_value(total_equity),
                flags=[
                    "statement-date book value, not a market fair value at the price date",
                    "company-level value, not per-share (no share counts)",
                    f"balance-sheet date: {inputs.get('bs_date')}",
                ],
            )
        )
    owners_equity = inputs.get("owners_equity")
    if owners_equity is None:
        out.append(
            _insufficient(
                "asset_based:equity_book_value_owners",
                "no equity-attributable-to-owners split on the extracted balance sheet",
            )
        )
    else:
        out.append(
            _computed(
                "asset_based:equity_book_value_owners",
                book_value(owners_equity),
                flags=[
                    "statement-date book value, not a market fair value at the price date",
                    "company-level value, not per-share (no share counts)",
                    f"balance-sheet date: {inputs.get('bs_date')}",
                ],
            )
        )
    out.append(
        _insufficient(
            "asset_based:sum_of_parts",
            "no segment-level statements",
        )
    )
    if is_bank:
        # The bank model APPLIES to HBL, but it cannot compute: a
        # residual-income value needs a source-backed cost of equity,
        # a forecast residual-income series, and a book-value growth
        # assumption — none exists in the data, and none may be
        # invented. insufficient_inputs, never a fabricated value and
        # never not_applicable (the model is the right model for a bank).
        out.append(
            _insufficient(
                "residual_income:bank",
                "bank residual-income model applies, but no source-backed "
                "cost of equity, forecast residual-income series, or "
                "book-value growth assumption exists in the data; "
                "assumptions must not be invented",
            )
        )
    else:
        out.append(
            _na(
                "residual_income:bank",
                "residual-income model is bank-appropriate; the company "
                f"is industrial (sector {sector})",
            )
        )
    return out
