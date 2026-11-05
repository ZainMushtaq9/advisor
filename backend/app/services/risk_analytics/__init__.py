"""Phase 14 risk metric library, control rules (v1) and stress scenarios.

Everything here is definition, not data: no row is written from
this module, and no threshold is hidden. Thresholds are Phase 14
defaults with a stated rationale; they are configurable and
versioned (see RiskControl), and they govern SIMULATED portfolios
only — no live execution exists in this project.

Metric minima follow the project's own conventions: Phase 6 sets
var95/es95 warm-ups at 251 observations; a volatility, beta,
downside-deviation or correlation estimate needs a return series
(30 observations is the Phase 14 minimum for a first estimate);
a drawdown needs at least 2 closes; a gap needs a previous close.
With one trading date (2026-11-03) and previous_close NULL on all
444 price rows, every series metric is insufficient_inputs.
"""

from __future__ import annotations

# (metric_key, category, formula, min_observations, window, unit, scope)
METRIC_DEFINITIONS: tuple[tuple, ...] = (
    # Market risk — per security, all series-gated.
    (
        "volatility",
        "market",
        "Std dev of daily log returns x sqrt(252), annualised",
        30,
        "30 daily returns",
        "pct",
        "security",
    ),
    (
        "beta_vs_benchmark",
        "market",
        "Cov(security returns, benchmark returns) / Var(benchmark returns); "
        "benchmark = KSE-100 index series",
        30,
        "30 daily return pairs",
        "ratio",
        "security",
    ),
    (
        "max_drawdown",
        "market",
        "Min over t of (close_t / running max close before t - 1)",
        2,
        "full close series",
        "pct",
        "security",
    ),
    (
        "downside_deviation",
        "market",
        "Std dev of returns below a 0% minimum acceptable return, annualised",
        30,
        "30 daily returns",
        "pct",
        "security",
    ),
    (
        "var95_hist",
        "market",
        "5th percentile of daily returns (historical, no distribution assumed)",
        251,
        "251 daily returns",
        "pct",
        "security",
    ),
    (
        "es95_hist",
        "market",
        "Mean of daily returns at or below var95_hist",
        251,
        "251 daily returns",
        "pct",
        "security",
    ),
    (
        "correlation_vs_market",
        "market",
        "Pearson correlation of security and benchmark daily returns",
        30,
        "30 daily return pairs",
        "ratio",
        "security",
    ),
    (
        "gap_risk",
        "market",
        "(open_t - previous_close) / previous_close; needs previous_close",
        1,
        "one session with previous_close",
        "pct",
        "security",
    ),
    # Liquidity — per security.
    (
        "volume_liquidity_tier",
        "liquidity",
        "2026-11-03 volume vs tiers: >=1,000,000 HIGH, >=median MEDIUM, else LOW",
        1,
        "2026-11-03 session",
        "shares",
        "security",
    ),
    (
        "turnover_liquidity",
        "liquidity",
        "Turnover-based liquidity (needs turnover, NULL on all 2026-11-03 rows)",
        1,
        "2026-11-03 session",
        "pkr",
        "security",
    ),
    # Market scope — from Phase 12 breadth rows.
    (
        "sector_participation",
        "concentration",
        "Priced securities / registry securities in the sector, 2026-11-03",
        1,
        "2026-11-03 session",
        "pct",
        "sector",
    ),
    (
        "priced_coverage",
        "concentration",
        "Priced securities / registry securities, whole market, 2026-11-03",
        1,
        "2026-11-03 session",
        "pct",
        "market",
    ),
    (
        "top10_volume_share",
        "concentration",
        "Top-10 securities' volume / total market volume, 2026-11-03",
        1,
        "2026-11-03 session",
        "pct",
        "market",
    ),
    # Concentration — ownership (per company with ownership rows;
    # HUBC from Phase 12 run 1, HBL from the HBL re-run batch) and
    # sector volume HHI (needs per-sector volume shares, which
    # Phase 12 did not store).
    (
        "largest_holder_share",
        "concentration",
        "Largest single holder category's percentage of shares",
        1,
        "as at reporting date",
        "pct",
        "security",
    ),
    (
        "top3_holder_share",
        "concentration",
        "Sum of the three largest holder categories' percentages",
        1,
        "as at reporting date",
        "pct",
        "security",
    ),
    (
        "sector_volume_hhi",
        "concentration",
        "Sum of squared sector volume shares, 2026-11-03",
        1,
        "2026-11-03 session",
        "index",
        "market",
    ),
    # Sensitivity coefficients — direction is evidenced (Phase 10
    # exposures), coefficients are NOT in stored data.
    (
        "fx_sensitivity_coeff",
        "sensitivity",
        "P&L change per 1% PKR move; needs FX-denominated amounts",
        1,
        "per exposure",
        "pkr_per_pct",
        "security",
    ),
    (
        "rate_sensitivity_coeff",
        "sensitivity",
        "P&L change per 100bps rate move; needs floating/fixed debt split",
        1,
        "per exposure",
        "pkr_per_100bps",
        "security",
    ),
    (
        "commodity_sensitivity_coeff",
        "sensitivity",
        "Revenue change per 1% commodity price move; needs an elasticity",
        1,
        "per exposure",
        "pkr_per_pct",
        "security",
    ),
    # Model risk — market scope.
    (
        "forecast_abstention_rate",
        "model",
        "Phase 13 insufficient_inputs assessments / all assessments",
        1,
        "as at run date",
        "pct",
        "market",
    ),
    (
        "technical_coverage_rate",
        "model",
        "Phase 6 calculable indicator values / assessed securities",
        1,
        "as at run date",
        "pct",
        "market",
    ),
    (
        "input_drift",
        "model",
        "Change in feature values between two vintages; needs two vintages",
        2,
        "two vintages",
        "pct",
        "market",
    ),
)

# Per-security series metrics: (metric_key, reason when insufficient).
SERIES_METRICS: tuple[tuple[str, str], ...] = (
    ("volatility", "Needs 30 daily returns; only 1 close (2026-11-03) exists."),
    (
        "beta_vs_benchmark",
        "Needs 30 daily return pairs; only 1 close exists and no KSE-100 index series is stored.",
    ),
    ("max_drawdown", "Needs at least 2 closes; only 1 close (2026-11-03) exists."),
    ("downside_deviation", "Needs 30 daily returns; only 1 close exists."),
    ("var95_hist", "Needs 251 daily returns (Phase 6 warm-up); only 1 close exists."),
    ("es95_hist", "Needs 251 daily returns (Phase 6 warm-up); only 1 close exists."),
    (
        "correlation_vs_market",
        "Needs 30 daily return pairs; only 1 close exists and no benchmark series is stored.",
    ),
    ("gap_risk", "Needs previous_close; previous_close is NULL on all 444 2026-11-03 price rows."),
)

# Sensitivity coefficients per exposed company: (ticker, metric_key, reason).
SENSITIVITY_ROWS: tuple[tuple[str, str, str], ...] = (
    (
        "NML",
        "fx_sensitivity_coeff",
        "FX forwards/translation exposure evidenced, but no FX-denominated "
        "amount is stored, so no coefficient can be computed.",
    ),
    (
        "OGDC",
        "fx_sensitivity_coeff",
        "FX transaction exposure evidenced, but no FX-denominated amount "
        "is stored, so no coefficient can be computed.",
    ),
    (
        "HUBC",
        "rate_sensitivity_coeff",
        "Borrowing-cost exposure evidenced, but the floating/fixed debt "
        "split is not stored, so no coefficient can be computed.",
    ),
    (
        "NML",
        "rate_sensitivity_coeff",
        "Borrowing-cost exposure evidenced, but the floating/fixed debt "
        "split is not stored, so no coefficient can be computed.",
    ),
    (
        "OGDC",
        "rate_sensitivity_coeff",
        "Interest-income exposure evidenced, but the rate-sensitive asset "
        "balance split is not stored, so no coefficient can be computed.",
    ),
    (
        "HBL",
        "rate_sensitivity_coeff",
        "Markup-income and funding-cost exposures evidenced (Phase 10), "
        "but the repricing split of advances/deposits is not stored, so "
        "no coefficient can be computed.",
    ),
    (
        "HBL",
        "fx_sensitivity_coeff",
        "FX income exposure evidenced (Phase 10), but no FX-denominated "
        "amount is stored, so no coefficient can be computed.",
    ),
    (
        "OGDC",
        "commodity_sensitivity_coeff",
        "Oil/gas revenue exposure is structural, but no revenue elasticity "
        "to commodity prices is stored, so no coefficient can be computed.",
    ),
)

# Control rules v1: (control_key, threshold, rationale).
# Thresholds are Phase 14 defaults for simulated portfolios, stated
# openly so a later version can change them with a reason.
CONTROLS_V1: tuple[tuple[str, str, str], ...] = (
    (
        "single_name_cap_pct",
        "25",
        "A simulated portfolio holds no single name above 25%; the "
        "equal-weight 3-name reference portfolio holds 33.33% per name "
        "and therefore breaches this rule by construction — the breach "
        "is the finding, not a reason to move the threshold.",
    ),
    ("sector_cap_pct", "50", "A simulated portfolio holds no single sector above 50%."),
    (
        "drawdown_warning_pct",
        "-10",
        "A simulated portfolio warns when its drawdown reaches -10%; "
        "with one price date no drawdown can be computed, so the check "
        "is BLOCKED, never passed.",
    ),
    (
        "min_daily_volume_shares",
        "50000",
        "A simulated portfolio holds only names trading at least 50,000 "
        "shares on the reference date (near the 2026-11-03 median volume "
        "of 54,631.5 shares).",
    ),
    ("min_diversification_names", "3", "A simulated portfolio holds at least 3 names."),
)

# Stress scenarios: (scenario_key, shock, applies_to, method).
STRESS_SCENARIOS: tuple[tuple[str, str, str, str], ...] = (
    (
        "market_minus_10",
        "Whole market -10% in one move",
        "SIMULATED_PORTFOLIO",
        "Apply -10% to each holding's 2026-11-03 close; portfolio impact "
        "is the weight-weighted mean (equal weights: -10%).",
    ),
    (
        "idiosyncratic_minus_20",
        "Single name -20%, others unchanged",
        "per ticker",
        "Apply -20% to one holding's 2026-11-03 close, others unchanged; "
        "portfolio impact is weight x -20%.",
    ),
    (
        "rate_plus_100bps",
        "Policy rate +100bps",
        "per exposed company",
        "Needs a rate sensitivity coefficient; none is stored, so the "
        "scenario is defined but not computed.",
    ),
    (
        "fx_pkr_minus_10",
        "PKR depreciates 10% against foreign currencies",
        "per FX-exposed company",
        "Needs an FX sensitivity coefficient; none is stored, so the "
        "scenario is defined but not computed.",
    ),
    (
        "commodity_oil_minus_10",
        "Oil price -10%",
        "OGDC",
        "Needs a revenue elasticity to oil prices; none is stored, so "
        "the scenario is defined but not computed.",
    ),
)

# The simulated reference portfolio: equal-weight HUBC/NML/OGDC,
# the statement companies. Stated here, used by the runner and the
# API, never presented as a real holding. HBL is NOT added to it by
# the HBL re-run batch: portfolio inclusion follows the Phase 15/16
# rules, not availability (its quote is eligible evidence, not an
# automatic inclusion).
REFERENCE_PORTFOLIO: tuple[tuple[str, str], ...] = (
    ("HUBC", "33.333333"),
    ("NML", "33.333333"),
    ("OGDC", "33.333333"),
)

# Per-company risk universe: the statement companies including HBL
# (HBL re-run batch). Per-company sections (series, liquidity,
# ownership concentration, sensitivity, staleness, volume checks,
# rate/FX stress) run over this universe; portfolio sections
# (single-name/sector caps, portfolio shocks) stay on
# REFERENCE_PORTFOLIO.
RISK_TICKERS = ("HUBC", "NML", "OGDC", "HBL")

ANALYSIS_DATE = "2026-11-04"
PRICE_DATE = "2026-11-03"
