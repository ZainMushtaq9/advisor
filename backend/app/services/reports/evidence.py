"""Pure figure helpers for Phase 22 reports.

A figure is one of five kinds (see the package __init__):
sourced_fact, deterministic_calculation, model_output,
analyst_inference, assumption. Every figure carries a
computation status: computed, insufficient_inputs, or
not_applicable. A computed figure carries exactly one value
form (numeric `value` for prices, ratios, and counts, or
`value_text` for dates and labels); a non-computed figure
carries neither — a NOT_CALCULABLE output is never shown as
a number, never zero-filled, and never estimated. There is
no price_target kind: figure() rejects it outright.

Dates: the stale threshold is 365 days, matching Phase 14.
NULL renders as "not available", never as 0 and never as a
dash that could be read as a number.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from app.services.reports import (
    COMPUTATION_STATUSES,
    DATA_CUTOFF_DATE,
    FIGURE_KINDS,
)

STALE_THRESHOLD_DAYS = 365


def figure(
    figure_key: str,
    label: str,
    *,
    kind: str,
    status: str,
    value=None,
    value_text: str | None = None,
    unit: str | None = None,
    source_table: str,
    source_row_ids: list,
    source_note: str,
    quality_status: str = "UNVERIFIED",
) -> dict:
    """Build one validated figure dict. Raises ValueError on
    any rule breach, so a bad builder fails loudly instead of
    emitting a misleading report."""
    if figure_key == "price_target" or "price_target" in figure_key:
        raise ValueError("price_target figures are forbidden")
    if kind not in FIGURE_KINDS:
        raise ValueError(f"unknown figure kind {kind!r}")
    if status not in COMPUTATION_STATUSES:
        raise ValueError(f"unknown computation status {status!r}")
    if kind == "analyst_inference" and status == "computed":
        # An inference is a judgement, not a computed value.
        raise ValueError("analyst_inference figures are never computed")
    numeric = None
    if value is not None:
        try:
            numeric = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"figure {figure_key} value not numeric") from exc
    if status == "computed":
        if (numeric is None) == (value_text is None):
            raise ValueError(
                f"computed figure {figure_key} needs exactly one "
                "value form (numeric value xor value_text)"
            )
    else:
        if numeric is not None or value_text is not None:
            raise ValueError(f"non-computed figure {figure_key} must carry no value")
    if not source_table or not source_note:
        raise ValueError(f"figure {figure_key} needs source table and note")
    return {
        "figure_key": figure_key,
        "label": label,
        "kind": kind,
        "computation_status": status,
        "value": numeric,
        "value_text": value_text,
        "unit": unit,
        "source_table": source_table,
        "source_row_ids": list(source_row_ids),
        "source_note": source_note,
        "quality_status": quality_status,
    }


def check_figure(fig: dict) -> list[str]:
    """QA problems for one figure dict (empty means clean).
    Mirrors figure()'s rules so stored or hand-built drafts
    can be checked without rebuilding them."""
    problems: list[str] = []
    if "price_target" in fig.get("figure_key", ""):
        problems.append("price_target figures are forbidden")
    if fig.get("kind") not in FIGURE_KINDS:
        problems.append(f"unknown figure kind {fig.get('kind')!r}")
    if fig.get("computation_status") not in COMPUTATION_STATUSES:
        problems.append(f"unknown computation status {fig.get('computation_status')!r}")
    if fig.get("kind") == "analyst_inference" and fig.get("computation_status") == "computed":
        problems.append("analyst_inference figures are never computed")
    numeric = fig.get("value")
    text = fig.get("value_text")
    if fig.get("computation_status") == "computed":
        if (numeric is None) == (text is None):
            problems.append("computed figure needs exactly one value form")
    elif fig.get("computation_status") in COMPUTATION_STATUSES:
        if numeric is not None or text is not None:
            problems.append("non-computed figure must carry no value")
    if not fig.get("source_table") or not fig.get("source_note"):
        problems.append("figure needs source table and note")
    return problems


def after_cutoff(day) -> bool:
    """True when a date (or ISO date string) is after the
    data cut-off. Future observations must never appear as
    occurred facts."""
    if day is None:
        return False
    if isinstance(day, str):
        day = date.fromisoformat(day[:10])
    return day > DATA_CUTOFF_DATE


def stale_days(period_end, as_of: date = DATA_CUTOFF_DATE) -> int | None:
    if period_end is None:
        return None
    if isinstance(period_end, str):
        period_end = date.fromisoformat(period_end[:10])
    return (as_of - period_end).days


def stale_warning(period_end, as_of: date = DATA_CUTOFF_DATE) -> str | None:
    days = stale_days(period_end, as_of)
    if days is not None and days > STALE_THRESHOLD_DAYS:
        return (
            f"Latest statement period ended {period_end.isoformat()} "
            f"({days} days before the cut-off) — older than the "
            f"{STALE_THRESHOLD_DAYS}-day stale threshold."
        )
    return None


def fmt_value(value, value_text: str | None = None) -> str:
    if value is not None:
        return str(value)
    if value_text is not None:
        return value_text
    return "not available"


def fmt_figure(fig: dict) -> str:
    return fmt_value(fig.get("value"), fig.get("value_text"))
