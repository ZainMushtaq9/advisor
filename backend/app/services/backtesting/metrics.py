"""Pure performance-metric functions for Phase 17.

Every function takes already-validated Decimal inputs and returns
a Decimal or None. None means "not computable from these inputs"
and is never converted to zero by callers. Gating against the
METRIC_MINIMA table lives in :func:`assess_metric`, which is the
single place that turns short series into insufficient_inputs
(or not_applicable for benchmark-relative return) with a reason.

Conventions:
- Returns are simple returns: close[t] / close[t-1] - 1.
- Volatility, Sharpe and Sortino annualise with sqrt(252).
- Sharpe/Sortino need a daily risk-free rate; callers pass None
  when no validated risk-free series exists, and the metric is
  then insufficient_inputs (never computed against an invented
  or policy-rate-as-risk-free figure).
- CAGR needs a positive year fraction; a zero-length window is
  insufficient_inputs, never infinite or zero.
- Tail loss is the mean of the worst 5% of returns (at least one
  return in the tail once the 20-return minimum is met).
- No function here touches the database, the network, or the
  clock, so every function is fixture-testable.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.backtesting import METRIC_MINIMA

TRADING_DAYS_PER_YEAR = Decimal(252)


def simple_returns(closes: list[Decimal]) -> list[Decimal]:
    """Simple returns between consecutive closes; [] for < 2 closes."""
    out: list[Decimal] = []
    for prev, cur in zip(closes, closes[1:]):
        if prev == 0:
            return []
        out.append(cur / prev - Decimal(1))
    return out


def total_return(closes: list[Decimal]) -> Decimal | None:
    """End / start - 1; None for fewer than 2 closes."""
    if len(closes) < 2 or closes[0] == 0:
        return None
    return closes[-1] / closes[0] - Decimal(1)


def cagr(closes: list[Decimal], years: Decimal) -> Decimal | None:
    """Annualised return; None for < 2 closes or years <= 0."""
    tr = total_return(closes)
    if tr is None or years <= 0 or (Decimal(1) + tr) <= 0:
        return None
    return (Decimal(1) + tr) ** (Decimal(1) / years) - Decimal(1)


def _mean(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal(0)) / Decimal(len(values))


def _stdev(values: list[Decimal]) -> Decimal | None:
    if len(values) < 2:
        return None
    mean = _mean(values)
    variance = sum((v - mean) ** 2 for v in values) / Decimal(len(values) - 1)
    return variance.sqrt()


def volatility(returns: list[Decimal]) -> Decimal | None:
    """Annualised sample stdev of returns; None for < 2 returns."""
    sd = _stdev(returns)
    if sd is None:
        return None
    return sd * TRADING_DAYS_PER_YEAR.sqrt()


def sharpe_ratio(returns: list[Decimal], daily_risk_free: Decimal | None) -> Decimal | None:
    """Annualised Sharpe; None without a risk-free rate or stdev."""
    if daily_risk_free is None:
        return None
    sd = _stdev(returns)
    if sd is None or sd == 0:
        return None
    excess_mean = _mean(returns) - daily_risk_free
    return excess_mean / sd * TRADING_DAYS_PER_YEAR.sqrt()


def sortino_ratio(returns: list[Decimal], daily_risk_free: Decimal | None) -> Decimal | None:
    """Annualised Sortino; None without a risk-free rate or downside."""
    if daily_risk_free is None:
        return None
    downside = [min(Decimal(0), r - daily_risk_free) for r in returns]
    if not downside:
        return None
    mean_sq = sum(d * d for d in downside) / Decimal(len(downside))
    downside_dev = mean_sq.sqrt()
    if downside_dev == 0:
        return None
    excess_mean = _mean(returns) - daily_risk_free
    return excess_mean / downside_dev * TRADING_DAYS_PER_YEAR.sqrt()


def max_drawdown(closes: list[Decimal]) -> Decimal | None:
    """Largest peak-to-trough fall as a positive fraction; None < 2."""
    if len(closes) < 2:
        return None
    peak = closes[0]
    worst = Decimal(0)
    for price in closes[1:]:
        if price > peak:
            peak = price
        elif peak != 0:
            drawdown = (peak - price) / peak
            if drawdown > worst:
                worst = drawdown
    return worst


def win_rate(returns: list[Decimal]) -> Decimal | None:
    """Share of positive returns; None with no returns."""
    if not returns:
        return None
    wins = sum(1 for r in returns if r > 0)
    return Decimal(wins) / Decimal(len(returns))


def turnover(traded_values: list[Decimal], avg_portfolio_value: Decimal) -> Decimal | None:
    """Total traded value / average portfolio value; None if no trades."""
    if not traded_values or avg_portfolio_value == 0:
        return None
    return sum(traded_values, Decimal(0)) / avg_portfolio_value


def exposure(invested_values: list[Decimal], capitals: list[Decimal]) -> Decimal | None:
    """Mean invested / capital across snapshots; None with no snapshots."""
    if not invested_values or len(invested_values) != len(capitals):
        return None
    ratios = [(inv / cap) if cap != 0 else None for inv, cap in zip(invested_values, capitals)]
    if any(r is None for r in ratios):
        return None
    return _mean([r for r in ratios if r is not None])


def benchmark_relative_return(
    strategy_return: Decimal | None, benchmark_return: Decimal | None
) -> Decimal | None:
    """Strategy minus benchmark; None when either side is missing."""
    if strategy_return is None or benchmark_return is None:
        return None
    return strategy_return - benchmark_return


def tail_loss(returns: list[Decimal]) -> Decimal | None:
    """Mean of the worst 5% of returns (at least one); None if empty."""
    if not returns:
        return None
    ordered = sorted(returns)
    tail_count = max(1, len(ordered) * 5 // 100)
    tail = ordered[:tail_count]
    return _mean(tail)


def assess_metric(
    metric: str,
    closes: list[Decimal],
    returns: list[Decimal],
    snapshots: int,
    benchmark_return: Decimal | None,
    years: Decimal,
    daily_risk_free: Decimal | None,
    traded_values: list[Decimal] | None = None,
    avg_portfolio_value: Decimal | None = None,
    invested_values: list[Decimal] | None = None,
    capitals: list[Decimal] | None = None,
) -> tuple[Decimal | None, str, str]:
    """Gate one metric against its minimum and compute it if met.

    Returns (value, status, reason). Status is "computed",
    "insufficient_inputs", or "not_applicable" (benchmark-relative
    return only, when no benchmark series exists). Reasons always
    name the counts and the minimum so the gating is auditable.
    """
    spec = METRIC_MINIMA[metric]
    kind = spec["kind"]
    minimum = spec["minimum"]
    if kind == "benchmark":
        if benchmark_return is None:
            return (
                None,
                "not_applicable",
                ("No benchmark series is loaded, so benchmark-relative return cannot be computed."),
            )
        strategy = total_return(closes)
        if strategy is None:
            return (
                None,
                "insufficient_inputs",
                (
                    "Strategy total return is not computable from "
                    f"{len(closes)} close(s); need at least 2."
                ),
            )
        return (
            benchmark_relative_return(strategy, benchmark_return),
            "computed",
            "Strategy total return minus benchmark total return.",
        )
    counts = {"closes": len(closes), "returns": len(returns), "snapshots": snapshots}
    observed = counts[kind]
    if observed < minimum:
        return (
            None,
            "insufficient_inputs",
            (f"Need at least {minimum} {kind} observation(s); observed {observed}."),
        )
    if metric == "total_return":
        return total_return(closes), "computed", "End / start - 1."
    if metric == "cagr":
        value = cagr(closes, years)
        if value is None:
            return None, "insufficient_inputs", ("Year fraction is not positive for this window.")
        return value, "computed", "Annualised from total return."
    if metric == "volatility":
        return volatility(returns), "computed", "Annualised sample stdev."
    if metric == "sharpe_ratio":
        if daily_risk_free is None:
            return (
                None,
                "insufficient_inputs",
                (
                    "No validated daily risk-free series exists; the SBP "
                    "policy rate is not used as a risk-free rate."
                ),
            )
        return (
            sharpe_ratio(returns, daily_risk_free),
            "computed",
            ("Annualised excess mean / stdev."),
        )
    if metric == "sortino_ratio":
        if daily_risk_free is None:
            return (
                None,
                "insufficient_inputs",
                (
                    "No validated daily risk-free series exists; the SBP "
                    "policy rate is not used as a risk-free rate."
                ),
            )
        return (
            sortino_ratio(returns, daily_risk_free),
            "computed",
            ("Annualised excess mean / downside deviation."),
        )
    if metric == "max_drawdown":
        return max_drawdown(closes), "computed", "Largest peak-to-trough fall."
    if metric == "win_rate":
        return win_rate(returns), "computed", "Share of positive returns."
    if metric == "turnover":
        if not traded_values or avg_portfolio_value is None:
            return (
                None,
                "insufficient_inputs",
                (
                    "Turnover needs traded values from a trade interval; "
                    "no trade interval exists in this window."
                ),
            )
        value = turnover(traded_values, avg_portfolio_value)
        if value is None:
            return (
                None,
                "insufficient_inputs",
                ("Turnover inputs are missing or average value is zero."),
            )
        return value, "computed", "Traded value / average portfolio value."
    if metric == "exposure":
        if not invested_values or not capitals:
            return (
                None,
                "insufficient_inputs",
                (
                    "Window-average exposure needs valuation snapshots; "
                    "no snapshot series exists for this window."
                ),
            )
        value = exposure(invested_values, capitals)
        if value is None:
            return (
                None,
                "insufficient_inputs",
                ("Exposure inputs are missing or a capital value is zero."),
            )
        return value, "computed", "Mean invested / capital across snapshots."
    if metric == "tail_loss":
        return tail_loss(returns), "computed", "Mean of worst 5% of returns."
    raise ValueError(f"Unknown metric: {metric}")
