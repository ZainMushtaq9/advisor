"""Coverage assessment: what the data actually supports (Phase 6).

This module never invents a value. For each registered indicator
it answers one question per security: CALCULABLE or
NOT_CALCULABLE, with a reason and the exact data that would
unblock it. No-look-ahead is enforced here by slicing every series
to bars dated on or before the as-of date before any computation.

Quality governance (Phase 5 rules, applied here):

- CONFLICTED input rows are never silently included: if any input
  bar for a security is CONFLICTED, every indicator for that
  security is NOT_CALCULABLE with reason 'conflicted_input'.
  (REJECTED rows are never stored, so they cannot appear; if one
  did, it would be excluded the same way.)
- A computed value inherits the lowest input quality (rank:
  VERIFIED > PARTIALLY_VERIFIED > UNVERIFIED). All production
  inputs today are UNVERIFIED, so any future value would be
  UNVERIFIED too — never upgraded by calculation.
- Missing bars are absent, never zero-filled; a missing
  previous_close is missing_data, never the close itself.
"""

from __future__ import annotations

from datetime import date

from app.services.technical_indicators import conventions, formulas

_QUALITY_RANK = {
    "CONFLICTED": 0,
    "UNVERIFIED": 1,
    "PARTIALLY_VERIFIED": 2,
    "VERIFIED": 3,
}


def _lowest_quality(bars: list[dict]) -> str:
    worst = "VERIFIED"
    for bar in bars:
        status = bar.get("quality_status", "UNVERIFIED")
        if _QUALITY_RANK.get(status, 1) < _QUALITY_RANK[worst]:
            worst = status
    return worst


def assess_security(
    ticker: str,
    bars: list[dict],
    as_of: date | None = None,
    has_conflicted_inputs: bool = False,
) -> dict:
    """Assess every registered indicator for one security.

    ``bars`` are daily bars in date order. When ``as_of`` is given,
    only bars dated on or before it are used (no-look-ahead).
    ``has_conflicted_inputs`` covers the case the runner sees:
    CONFLICTED/REJECTED rows are excluded from ``bars`` before
    this call, so a security whose only rows were conflicted
    would otherwise look like it had no data at all. When the
    flag is set, every indicator is NOT_CALCULABLE with reason
    conflicted_input, whether or not usable bars also exist.
    Returns a verdict dict; values are Decimals when CALCULABLE.
    """
    usable = sorted(bars, key=lambda b: b["date"])
    if as_of is not None:
        usable = [b for b in usable if b["date"] <= as_of]
    effective_as_of = as_of or (usable[-1]["date"] if usable else None)
    conflicted = has_conflicted_inputs or any(
        b.get("quality_status") in ("CONFLICTED", "REJECTED") for b in usable
    )
    input_quality = _lowest_quality(usable) if usable else "UNVERIFIED"
    verdicts = []
    for spec in conventions.INDICATORS:
        if not usable:
            if conflicted:
                verdicts.append(
                    _verdict(
                        spec, "NOT_CALCULABLE", None,
                        "conflicted_input",
                        "All input rows for this security are CONFLICTED "
                        "or REJECTED and are never silently included.",
                    )
                )
            else:
                verdicts.append(
                    _verdict(
                        spec, "NOT_CALCULABLE", None,
                        "missing_data", "No observations for this security.",
                    )
                )
            continue
        if conflicted:
            verdicts.append(
                _verdict(
                    spec, "NOT_CALCULABLE", None,
                    "conflicted_input",
                    "Input rows include CONFLICTED data, which is never "
                    "silently included.",
                )
            )
            continue
        if len(usable) < spec.warmup_bars:
            verdicts.append(
                _verdict(
                    spec, "NOT_CALCULABLE", None,
                    "insufficient_warmup",
                    f"Needs {spec.warmup_bars} bars, only {len(usable)} "
                    f"available; {spec.warmup_bars - len(usable)} more bars "
                    f"required.",
                )
            )
            continue
        try:
            value = formulas.compute_indicator(spec.key, usable, spec)
        except formulas.InsufficientData as exc:
            verdicts.append(
                _verdict(spec, "NOT_CALCULABLE", None, exc.code, exc.message)
            )
            continue
        verdicts.append(
            _verdict(spec, "CALCULABLE", value, None, None)
        )
    calculable = sum(1 for v in verdicts if v["status"] == "CALCULABLE")
    return {
        "ticker": ticker,
        "as_of": effective_as_of.isoformat() if effective_as_of else None,
        "bars_available": len(usable),
        "first_date": usable[0]["date"].isoformat() if usable else None,
        "last_date": usable[-1]["date"].isoformat() if usable else None,
        "input_quality": input_quality,
        "calculable_count": calculable,
        "not_calculable_count": len(verdicts) - calculable,
        "verdicts": verdicts,
    }


def _verdict(
    spec, status: str, value, reason: str | None, detail: str | None
) -> dict:
    return {
        "indicator_key": spec.key,
        "category": spec.category,
        "status": status,
        "value": str(value) if value is not None else None,
        "reason": reason,
        "detail": detail,
        "warmup_bars": spec.warmup_bars,
        "formula_version": spec.formula_version,
        "parameters": spec.default_parameters(),
    }


def assess_market(
    securities_bars: dict[str, list[dict]],
    as_of: date | None = None,
    conflicted_tickers: set[str] | None = None,
) -> dict:
    """Assess the whole market; returns a summary plus per-ticker detail.

    ``conflicted_tickers`` are tickers with CONFLICTED/REJECTED
    rows excluded upstream (see assess_security).
    """
    flagged = conflicted_tickers or set()
    per_ticker = {
        ticker: assess_security(
            ticker, bars, as_of, has_conflicted_inputs=ticker in flagged
        )
        for ticker, bars in securities_bars.items()
    }
    per_indicator: dict[str, dict] = {}
    for spec in conventions.INDICATORS:
        calc = sum(
            1
            for a in per_ticker.values()
            for v in a["verdicts"]
            if v["indicator_key"] == spec.key and v["status"] == "CALCULABLE"
        )
        reasons: dict[str, int] = {}
        for a in per_ticker.values():
            for v in a["verdicts"]:
                if v["indicator_key"] == spec.key and v["status"] != "CALCULABLE":
                    reasons[v["reason"] or "unknown"] = (
                        reasons.get(v["reason"] or "unknown", 0) + 1
                    )
        per_indicator[spec.key] = {
            "category": spec.category,
            "warmup_bars": spec.warmup_bars,
            "calculable": calc,
            "not_calculable": len(per_ticker) - calc,
            "reasons": reasons,
        }
    return {
        "securities_assessed": len(per_ticker),
        "indicators_registered": len(conventions.INDICATORS),
        "securities_with_any_calculable": sum(
            1 for a in per_ticker.values() if a["calculable_count"] > 0
        ),
        "per_indicator": per_indicator,
        "per_ticker": per_ticker,
    }
