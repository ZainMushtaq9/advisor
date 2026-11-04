"""Pure breadth/liquidity computation (Phase 12).

Input is plain data (one row per priced security: ticker, sector,
volume); output is metric dicts. No database access here, so the
tests run without a DB.

Completeness discipline: every metric that cannot be computed from
the inputs is returned with status insufficient_inputs and a NULL
value — never zero, never estimated. The 2026-11-03 snapshot can
support coverage, sector participation and volume distribution only:
- advances / declines / unchanged need previous_close (NULL for all
  444 stored rows);
- new highs / lows need price history (exactly one date exists);
- turnover distribution needs turnover (NULL for all 444 rows).
"""

from __future__ import annotations

from decimal import Decimal


def compute_breadth(priced: list[dict], universe: list[dict]) -> list[dict]:
    """Compute market and sector breadth metrics.

    ``priced``: [{ticker, sector, volume}] for one trading date.
    ``universe``: [{ticker, sector}] for every registry security.
    """
    out: list[dict] = []
    total = len(universe)
    n_priced = len(priced)
    out.append(
        {
            "scope": "MARKET",
            "metric_key": "priced_coverage",
            "value": (Decimal(n_priced) / Decimal(total) * 100) if total else None,
            "numerator": n_priced,
            "denominator": total,
            "status": "computed",
            "note": f"{n_priced} of {total} registry securities have a price row.",
        }
    )
    out.append(
        {
            "scope": "MARKET",
            "metric_key": "missing_securities",
            "value": Decimal(total - n_priced),
            "numerator": total - n_priced,
            "denominator": total,
            "status": "computed",
            "note": "Securities with no price row on the date (rejected rows and "
            "absent symbols, per the Phase 5 record).",
        }
    )
    sectors: dict[str, dict] = {}
    for row in universe:
        sectors.setdefault(row["sector"], {"total": 0, "priced": 0})
        sectors[row["sector"]]["total"] += 1
    for row in priced:
        sectors.setdefault(row["sector"], {"total": 0, "priced": 0})
        sectors[row["sector"]]["priced"] += 1
    for sector in sorted(sectors):
        counts = sectors[sector]
        out.append(
            {
                "scope": f"SECTOR:{sector}",
                "metric_key": "priced_coverage",
                "value": (Decimal(counts["priced"]) / Decimal(counts["total"]) * 100)
                if counts["total"]
                else None,
                "numerator": counts["priced"],
                "denominator": counts["total"],
                "status": "computed",
                "note": f"Sector participation: {counts['priced']} of {counts['total']} priced.",
            }
        )
    volumes = sorted(row["volume"] for row in priced if row.get("volume") is not None)
    total_volume = sum(volumes)
    out.append(
        {
            "scope": "MARKET",
            "metric_key": "total_volume",
            "value": Decimal(total_volume),
            "numerator": None,
            "denominator": None,
            "status": "computed",
            "note": "Sum of volume over priced securities.",
        }
    )
    if volumes:
        mid = len(volumes) // 2
        median = (
            Decimal(volumes[mid])
            if len(volumes) % 2 == 1
            else (Decimal(volumes[mid - 1]) + Decimal(volumes[mid])) / 2
        )
        out.append(
            {
                "scope": "MARKET",
                "metric_key": "median_volume",
                "value": median,
                "numerator": None,
                "denominator": None,
                "status": "computed",
                "note": "Median security volume on the date.",
            }
        )
        top10 = sum(sorted(volumes, reverse=True)[:10])
        out.append(
            {
                "scope": "MARKET",
                "metric_key": "top10_volume_share_pct",
                "value": (Decimal(top10) / Decimal(total_volume) * 100) if total_volume else None,
                "numerator": top10,
                "denominator": total_volume,
                "status": "computed",
                "note": "Volume concentration: top 10 securities' share of total volume. "
                "This is activity concentration, NOT market-cap concentration "
                "(no share counts or free float exist for the universe).",
            }
        )
    out.append(
        {
            "scope": "MARKET",
            "metric_key": "zero_volume_securities",
            "value": Decimal(sum(1 for v in volumes if v == 0)),
            "numerator": None,
            "denominator": None,
            "status": "computed",
            "note": "Priced securities with zero volume on the date.",
        }
    )
    for key, reason in [
        (
            "advances",
            "previous_close is NULL for every stored price row, so no "
            "security can be classified as advancing.",
        ),
        (
            "declines",
            "previous_close is NULL for every stored price row, so no "
            "security can be classified as declining.",
        ),
        (
            "unchanged",
            "previous_close is NULL for every stored price row, so no "
            "security can be classified as unchanged.",
        ),
        (
            "new_highs",
            "Exactly one trading date exists; no look-back history exists.",
        ),
        (
            "new_lows",
            "Exactly one trading date exists; no look-back history exists.",
        ),
        (
            "turnover_distribution",
            "turnover is NULL for every stored price row, so no turnover "
            "distribution can be computed.",
        ),
    ]:
        out.append(
            {
                "scope": "MARKET",
                "metric_key": key,
                "value": None,
                "numerator": None,
                "denominator": None,
                "status": "insufficient_inputs",
                "note": reason,
            }
        )
    out.append(
        {
            "scope": "MARKET",
            "metric_key": "trading_day_frequency",
            "value": Decimal(1),
            "numerator": 1,
            "denominator": None,
            "status": "partial",
            "note": "Only one trading date is observed; this is a snapshot count, "
            "not a frequency measure. More trading days are needed.",
        }
    )
    return out


def compute_liquidity(priced: list[dict]) -> list[dict]:
    """Per-security volume and volume share, plus a market row."""
    total_volume = sum(row["volume"] for row in priced if row.get("volume") is not None)
    out: list[dict] = []
    for row in priced:
        volume = row.get("volume")
        out.append(
            {
                "scope_key": f"SEC:{row['ticker']}",
                "metric_key": "volume",
                "value": Decimal(volume) if volume is not None else None,
                "status": "computed" if volume is not None else "insufficient_inputs",
                "note": "Traded volume on the date.",
            }
        )
        out.append(
            {
                "scope_key": f"SEC:{row['ticker']}",
                "metric_key": "volume_share_pct",
                "value": (Decimal(volume) / Decimal(total_volume) * 100)
                if volume is not None and total_volume
                else None,
                "status": "computed"
                if volume is not None and total_volume
                else "insufficient_inputs",
                "note": "Security volume as a percentage of total market volume.",
            }
        )
    out.append(
        {
            "scope_key": "MARKET",
            "metric_key": "total_volume",
            "value": Decimal(total_volume),
            "status": "computed",
            "note": "Sum of volume over priced securities.",
        }
    )
    return out
