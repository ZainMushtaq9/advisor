"""Deterministic data-quality and validation helpers — Phase 3.

Pure functions, no LLM arithmetic, no I/O. They are the single place
where the integrity rules are computed, so the database constraints,
the tests and the docs all describe the same behaviour:

- missing is never zero: a missing value stays None and the caller
  records MISSING in the quality registry;
- collection time is never observation time: callers pass both;
- conflicting sources are kept side-by-side: this module never picks
  a winner — it only reports that values conflict;
- unverified is never upgraded to verified without evidence: see
  upgrade_quality_status(), which requires an evidence string;
- OHLC validity, balance-sheet identity and cash-flow identity are
  checked with a documented rounding tolerance, and a failed check
  never silently rejects an entire document (it returns a finding).
"""

from __future__ import annotations

from decimal import Decimal

QUALITY_ORDER = ("UNVERIFIED", "PARTIALLY_VERIFIED", "VERIFIED")


def is_missing(value) -> bool:
    """Missing means absent/None — never zero, never a blank string
    silently converted. Zero is a real value and must stay zero."""
    return value is None


def validate_ohlc(open_, high, low, close):
    """Return a list of findings (empty = valid). None values are
    reported as missing, not filled. high >= max(open, close) and
    low <= min(open, close) are required when all four are present."""
    findings = []
    for name, value in (("open", open_), ("high", high), ("low", low), ("close", close)):
        if value is None:
            findings.append(f"missing_{name}")
        elif value < 0:
            findings.append(f"negative_{name}")
    if not findings:
        if high < max(open_, close):
            findings.append("high_below_open_or_close")
        if low > min(open_, close):
            findings.append("low_above_open_or_close")
    return findings


def check_balance_sheet(total_assets, total_liabilities, total_equity, tolerance=Decimal("0.01")):
    """Assets = Liabilities + Equity, within a documented rounding
    tolerance. Returns (ok, difference). A failed check is a finding
    on the statement, not a reason to delete the statement."""
    if total_assets is None or total_liabilities is None or total_equity is None:
        return False, None
    difference = Decimal(str(total_assets)) - (
        Decimal(str(total_liabilities)) + Decimal(str(total_equity))
    )
    return abs(difference) <= tolerance, difference


def check_cash_flow(opening_cash, net_change, closing_cash, tolerance=Decimal("0.01")):
    """Opening cash + net movement = closing cash, within tolerance."""
    if opening_cash is None or net_change is None or closing_cash is None:
        return False, None
    difference = Decimal(str(opening_cash)) + Decimal(str(net_change)) - Decimal(str(closing_cash))
    return abs(difference) <= tolerance, difference


def values_conflict(values):
    """True when two or more distinct non-None values exist for the
    same observation across sources. The caller must keep them
    side-by-side (separate rows per source) — never pick one here."""
    distinct = {v for v in values if v is not None}
    return len(distinct) > 1


def upgrade_quality_status(current: str, target: str, evidence: str) -> str:
    """Quality may only be upgraded with evidence. Downgrades (e.g.
    to CONFLICTED or STALE on new information) are always allowed.
    Raises ValueError when an upgrade is attempted without evidence
    — that is the 'never mark unverified as verified' rule in code.

    Audit M1 fix: the guard applies to ANY transition into VERIFIED
    or PARTIALLY_VERIFIED from any non-verified state (UNVERIFIED,
    REJECTED, CONFLICTED, MISSING, STALE, PENDING_REVIEW), not only
    from UNVERIFIED. Re-affirming an already-verified row needs no
    new evidence. Note: this helper can never be the whole
    enforcement — direct database writes bypass it — which is why
    the quality CHECK constraints in the migrations matter.

    Tolerance note (audit L7): balance-sheet / cash-flow tolerances
    are in the caller's units. Callers must pass normalised
    base-unit values (see financial_statement_line_items.
    normalized_value); a tolerance of 0.01 in base rupees is not
    the same claim as 0.01 in millions."""
    if target in ("VERIFIED", "PARTIALLY_VERIFIED") and current not in (
        "VERIFIED",
        "PARTIALLY_VERIFIED",
    ):
        if not evidence or not evidence.strip():
            raise ValueError("quality upgrade requires evidence (source check reference)")
    return target


def duplicate_key_for_document(content_hash: str | None, source_url: str | None) -> str | None:
    """Duplicate-detection key for documents/announcements: the
    content hash when available, else the source URL. None means the
    record cannot be duplicate-checked and must be flagged for review."""
    if content_hash:
        return f"sha256:{content_hash}"
    if source_url:
        return f"url:{source_url}"
    return None
