"""Phase 14 risk formulas — pure Decimal math, no I/O.

Every function states its minimum input and returns None when the
input does not meet it; callers turn None into an
insufficient_inputs row with the exact reason. Nothing here
estimates, annualises a single observation, or invents a series.
"""

from __future__ import annotations

import math
from decimal import Decimal


def log_returns(closes: list[Decimal]) -> list[Decimal]:
    """Daily log returns from a close series (needs >= 2 closes)."""
    if len(closes) < 2:
        return []
    out: list[Decimal] = []
    for prev, cur in zip(closes, closes[1:]):
        if prev <= 0 or cur <= 0:
            continue
        out.append(Decimal(str(math.log(float(cur / prev)))))
    return out


def _mean(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values) / Decimal(len(values))


def _stdev(values: list[Decimal]) -> Decimal | None:
    if len(values) < 2:
        return None
    mean = _mean(values)
    assert mean is not None
    var = sum((v - mean) ** 2 for v in values) / Decimal(len(values) - 1)
    return Decimal(str(math.sqrt(float(var))))


def volatility(returns: list[Decimal]) -> Decimal | None:
    """Annualised volatility (%) from >= 30 daily log returns."""
    if len(returns) < 30:
        return None
    sd = _stdev(returns)
    if sd is None:
        return None
    return sd * Decimal(str(math.sqrt(252))) * Decimal(100)


def beta(security_returns: list[Decimal], benchmark_returns: list[Decimal]) -> Decimal | None:
    """Beta from >= 30 paired daily returns."""
    if len(security_returns) < 30 or len(benchmark_returns) < 30:
        return None
    pairs = list(zip(security_returns, benchmark_returns))[:30]
    bench = [b for _, b in pairs]
    bench_var = _stdev(bench)
    if bench_var is None or bench_var == 0:
        return None
    mean_s = _mean([s for s, _ in pairs])
    mean_b = _mean(bench)
    assert mean_s is not None and mean_b is not None
    cov = sum((s - mean_s) * (b - mean_b) for s, b in pairs) / Decimal(len(pairs) - 1)
    var = sum((b - mean_b) ** 2 for b in bench) / Decimal(len(bench) - 1)
    if var == 0:
        return None
    return cov / var


def correlation(xs: list[Decimal], ys: list[Decimal]) -> Decimal | None:
    """Pearson correlation from >= 30 paired observations."""
    if len(xs) < 30 or len(ys) < 30:
        return None
    pairs = list(zip(xs, ys))[:30]
    sx = _stdev([x for x, _ in pairs])
    sy = _stdev([y for _, y in pairs])
    if sx is None or sy is None or sx == 0 or sy == 0:
        return None
    mean_x = _mean([x for x, _ in pairs])
    mean_y = _mean([y for _, y in pairs])
    assert mean_x is not None and mean_y is not None
    cov = sum((x - mean_x) * (y - mean_y) for x, y in pairs) / Decimal(len(pairs) - 1)
    return cov / (sx * sy)


def max_drawdown(closes: list[Decimal]) -> Decimal | None:
    """Maximum drawdown (%) from >= 2 closes."""
    if len(closes) < 2:
        return None
    peak = closes[0]
    worst = Decimal(0)
    for close in closes:
        if close > peak:
            peak = close
        dd = (close / peak - 1) * Decimal(100)
        if dd < worst:
            worst = dd
    return worst


def downside_deviation(returns: list[Decimal]) -> Decimal | None:
    """Annualised downside deviation (%) vs 0% MAR, >= 30 returns."""
    if len(returns) < 30:
        return None
    downside = [min(r, Decimal(0)) for r in returns]
    mean_sq = sum(d * d for d in downside) / Decimal(len(downside))
    return Decimal(str(math.sqrt(float(mean_sq)))) * Decimal(str(math.sqrt(252))) * Decimal(100)


def var95_hist(returns: list[Decimal]) -> Decimal | None:
    """Historical 95% VaR (%) = 5th percentile of >= 251 daily returns."""
    if len(returns) < 251:
        return None
    ordered = sorted(returns)
    idx = int(Decimal("0.05") * Decimal(len(ordered)))
    return ordered[max(idx - 1, 0)] * Decimal(100)


def es95_hist(returns: list[Decimal]) -> Decimal | None:
    """Historical 95% ES (%) = mean of returns at/below VaR, >= 251."""
    var = var95_hist(returns)
    if var is None:
        return None
    tail = [r for r in returns if r * Decimal(100) <= var]
    if not tail:
        return None
    mean = _mean(tail)
    return None if mean is None else mean * Decimal(100)


def gap_pct(open_price: Decimal | None, previous_close: Decimal | None) -> Decimal | None:
    """Overnight gap (%) — None when previous_close is absent."""
    if open_price is None or previous_close is None or previous_close == 0:
        return None
    return (open_price - previous_close) / previous_close * Decimal(100)


def volume_tier(volume: int, median_volume: Decimal) -> str:
    """Liquidity tier for one session's volume.

    HIGH >= 1,000,000 shares; MEDIUM >= session median; else LOW.
    """
    if volume >= 1_000_000:
        return "HIGH"
    if Decimal(volume) >= median_volume:
        return "MEDIUM"
    return "LOW"


def top_n_share(shares: list[Decimal], n: int) -> Decimal:
    """Sum of the n largest shares (percentages)."""
    return sum(sorted(shares, reverse=True)[:n])


def hhi(shares_pct: list[Decimal]) -> Decimal | None:
    """Herfindahl index from percentage shares (0-10000 scale)."""
    if not shares_pct:
        return None
    return sum((s / Decimal(100)) ** 2 for s in shares_pct) * Decimal(10000)


def portfolio_shock_impact(weights_pct: list[Decimal], shocks_pct: list[Decimal]) -> Decimal:
    """Weight-weighted portfolio shock (%).

    weights_pct and shocks_pct are parallel lists; weights need not
    sum to exactly 100 (6dp rounding) — the impact is the weighted
    mean, so a uniform shock returns exactly that shock.
    """
    total_w = sum(weights_pct)
    if total_w == 0:
        return Decimal(0)
    return sum(w * s for w, s in zip(weights_pct, shocks_pct)) / total_w
