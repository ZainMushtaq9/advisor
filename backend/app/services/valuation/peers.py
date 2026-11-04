"""Comparable-peer selection for Phase 9.

A peer is genuinely comparable only when ALL of these hold:
  * same sector (Phase 4 registry sector, verbatim),
  * same reporting frequency (annual vs nine_month vs half_yearly —
    a 9M flow must never be averaged with an annual flow),
  * period alignment: period_end within 90 days of the target's
    period_end (same reporting season, not a stale year),
  * not the company itself.

Outlier treatment (brief): applied only when at least 4 peers exist
— a peer multiple beyond 3x the peer median is excluded and the
exclusion is reported. With fewer than 4 peers no outlier step runs
(the median itself is already fragile, and peer_median() requires
>= 3 peers before any peer multiple is reported at all).

Production truth: HUBC, NML and OGDC are each alone in their sector,
so every production peer set is empty and every peer multiple is
NOT_CALCULABLE. Cross-sector peers are never forced to fill the gap.
"""

from __future__ import annotations

from datetime import date

PERIOD_ALIGNMENT_DAYS = 90


def select_peers(target: dict, candidates: list[dict]) -> list[dict]:
    """Return the comparable peers for ``target``.

    ``target`` and each candidate carry: ticker, sector,
    reporting_frequency, period_end (a date). Candidates failing any
    rule are excluded; the reason for an empty result is for the
    caller to state (sector-alone vs frequency/period mismatch).
    """
    out = []
    for cand in candidates:
        if cand.get("ticker") == target.get("ticker"):
            continue
        if cand.get("sector") != target.get("sector"):
            continue
        if cand.get("reporting_frequency") != target.get("reporting_frequency"):
            continue
        t_end = target.get("period_end")
        c_end = cand.get("period_end")
        if not isinstance(t_end, date) or not isinstance(c_end, date):
            continue
        if abs((c_end - t_end).days) > PERIOD_ALIGNMENT_DAYS:
            continue
        out.append(cand)
    return out


def apply_outlier_rule(peer_multiples: list) -> tuple[list, list]:
    """Split peer multiples into (kept, excluded) by the 3x-median
    rule. Returns ([], excluded=[]) unchanged when fewer than 4
    peers: no outlier step runs on a fragile set."""
    from decimal import Decimal

    vals = [Decimal(str(m)) for m in peer_multiples if m is not None]
    if len(vals) < 4:
        return vals, []
    ordered = sorted(vals)
    n = len(ordered)
    mid = n // 2
    median = ordered[mid] if n % 2 == 1 else (ordered[mid - 1] + ordered[mid]) / Decimal(2)
    kept = [v for v in vals if v <= median * 3]
    excluded = [v for v in vals if v > median * 3]
    return kept, excluded
