"""Phase 17 backtesting, paper trading and strategy evaluation.

Registry, execution assumptions, and observation minima.

- SIMULATION ONLY. No backtest result here is real performance,
  no paper order is a real order, and no execution path exists
  anywhere in this project.
- Observation minima are the gating rule: a metric whose minimum
  is not met is insufficient_inputs (or not_applicable where its
  input series does not exist at all), never a number. With one
  price date the production windows have zero return intervals,
  so every production run is NOT_RUNNABLE.
- Risk-free convention is NOT established: the SBP policy rate
  (12.00% p.a.) is a policy rate, not a Treasury-bill risk-free
  series, and it is never used as one. Sharpe/Sortino therefore
  also lack a validated risk-free input in production.
- Cost assumptions (fees, taxes, slippage) have no validated
  source in the loaded data, so they are recorded as UNVALIDATED
  assumption parameters and sensitivity is demonstrated on
  fixtures only; production cost sensitivity is not_applicable
  because production holds zero trades.
"""

from __future__ import annotations

from datetime import date

# Strategy registry: name -> (version, description, rule_reference, parameters).
STRATEGIES: dict[str, dict] = {
    "equal_weight_statements_3": {
        "version": "backtest-v1",
        "description": (
            "Equal-weight baseline over the 3 statement companies "
            "(HUBC, NML, OGDC), mirroring the Phase 16 "
            "ew_statements_3_balanced construction."
        ),
        "rule_reference": "phase16:ew_statements_3_balanced",
        "parameters": {
            "universe": ["HUBC", "NML", "OGDC"],
            "rebalance": "buy_and_hold_from_construction",
            "weights": "equal_weight",
        },
    },
    "rule_screen_pass_balanced": {
        "version": "backtest-v1",
        "description": (
            "Rule-based portfolio over Phase 15 SCREEN_PASS names "
            "(HUBC, OGDC), balanced profile, mirroring the Phase 16 "
            "rule_screen_pass_balanced construction."
        ),
        "rule_reference": "phase15:decision-rules-v1+phase16:rule_screen_pass_balanced",
        "parameters": {
            "universe": ["HUBC", "OGDC"],
            "rebalance": "buy_and_hold_from_construction",
            "weights": "equal_weight_capped_50pct",
        },
    },
    "rule_screen_pass_conservative": {
        "version": "backtest-v1",
        "description": (
            "Rule-based portfolio over Phase 15 SCREEN_PASS names "
            "(HUBC, OGDC), conservative profile with a 10% cash "
            "floor, mirroring the Phase 16 "
            "rule_screen_pass_conservative construction."
        ),
        "rule_reference": "phase15:decision-rules-v1+phase16:rule_screen_pass_conservative",
        "parameters": {
            "universe": ["HUBC", "OGDC"],
            "rebalance": "buy_and_hold_from_construction",
            "weights": "equal_weight_capped_50pct_cash_floor_10pct",
        },
    },
    "buy_and_hold_hubc": {
        "version": "backtest-v1",
        "description": (
            "Single-name buy-and-hold baseline for HUBC, for "
            "comparison against the multi-name strategies."
        ),
        "rule_reference": "buy_and_hold_single_name",
        "parameters": {"universe": ["HUBC"], "rebalance": "buy_and_hold"},
    },
    "buy_and_hold_ogdc": {
        "version": "backtest-v1",
        "description": (
            "Single-name buy-and-hold baseline for OGDC, for "
            "comparison against the multi-name strategies."
        ),
        "rule_reference": "buy_and_hold_single_name",
        "parameters": {"universe": ["OGDC"], "rebalance": "buy_and_hold"},
    },
}

# Production backtest window: the only price date. A window with a
# single price observation has zero return intervals.
PRODUCTION_START: date = date(2026, 11, 3)
PRODUCTION_END: date = date(2026, 11, 3)

# Execution assumptions recorded on every run. The cost figures
# are UNVALIDATED placeholders (no validated fee/tax/slippage
# source exists in the loaded data) and are never applied to a
# production trade, because production holds zero trades.
EXECUTION_ASSUMPTIONS: dict = {
    "signal_time": "close",
    "execution_timing": "next_eligible_close_after_signal",
    "fees_bps": None,
    "fees_source": "UNVALIDATED_no_source_in_loaded_data",
    "taxes_bps": None,
    "taxes_source": "UNVALIDATED_no_source_in_loaded_data",
    "slippage_bps": None,
    "slippage_source": "UNVALIDATED_no_source_in_loaded_data",
    "risk_free_convention": "not_established",
    "risk_free_note": (
        "SBP policy rate 12.00% p.a. is a policy rate, not a "
        "Treasury-bill risk-free series, and is never used as one."
    ),
    "benchmark": None,
    "benchmark_note": "No benchmark series (e.g. KSE-100) is loaded.",
}

# Metric -> minimum observation requirement, and the metric's kind.
# "closes" counts price observations; "returns" counts return
# intervals (closes - 1 for a single series); "snapshots" counts
# portfolio valuation points; "benchmark" requires a benchmark
# series to exist at all.
METRIC_MINIMA: dict[str, dict] = {
    "total_return": {"kind": "closes", "minimum": 2},
    "cagr": {"kind": "closes", "minimum": 2},
    "volatility": {"kind": "returns", "minimum": 30},
    "sharpe_ratio": {"kind": "returns", "minimum": 30},
    "sortino_ratio": {"kind": "returns", "minimum": 30},
    "max_drawdown": {"kind": "closes", "minimum": 2},
    "win_rate": {"kind": "returns", "minimum": 1},
    "turnover": {"kind": "snapshots", "minimum": 2},
    "exposure": {"kind": "snapshots", "minimum": 2},
    "benchmark_relative_return": {"kind": "benchmark", "minimum": 1},
    "tail_loss": {"kind": "returns", "minimum": 20},
}

METRIC_NAMES: list[str] = list(METRIC_MINIMA)

# Order lifecycle states for the paper-trading simulator.
ORDER_STATUSES: tuple[str, ...] = (
    "proposed",
    "accepted",
    "filled",
    "partially_filled",
    "cancelled",
    "rejected",
)
