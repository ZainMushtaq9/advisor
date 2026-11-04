"""Phase 8 fundamental-analysis services.

Pure deterministic computation over Phase 7 statement rows. Nothing
here invents a value: a metric whose inputs are missing, zero in a
denominator, or methodologically unavailable is NOT_CALCULABLE
(value NULL, computation_status 'insufficient_inputs'), never zero,
never an estimate. Computed values inherit the lowest input quality
(all production inputs today are UNVERIFIED, so every output is
UNVERIFIED too — never upgraded by calculation).

Period discipline (Phase 6 as-of discipline, applied to statements):
a "period" is identified by (statement_type, period_start,
period_end, reporting_frequency, statement_scope). Rows are never
matched by period_end alone: NML and OGDC both carry a quarterly
column and a cumulative column sharing one period_end. No trailing
twelve months are synthesised: a TTM needs a full-year flow minus a
prior interim flow plus the current interim flow, and no full-year
income row exists for NML or OGDC in this set — interim ratios are
reported with their exact periods, never annualised.

Units: statement values are normalised to PKR (thousands x 1,000)
except per-share EPS rows, which are rupees per share. Ratios are
dimensionless, days metrics are calendar days in the flow period,
levels are PKR.
"""

from __future__ import annotations

CALCULATION_VERSION = "1.0"
HEALTH_METHOD_VERSION = "health-v1"

# Company ids in the live registry (post-recovery numbering).
HUBC = 289  # The Hub Power Company Limited — POWER GENERATION & DISTRIBUTION
NML = 394  # Nishat Mills Limited — TEXTILE COMPOSITE
OGDC = 403  # Oil & Gas Development Company Limited — OIL & GAS EXPLORATION
HBL = 277  # Habib Bank Limited — COMMERCIAL BANKS (PENDING input, see below)

# HBL is a pending 4th company: its CY2025 annual report PDF could not
# be fetched (issuer-site bot-management challenge on the PDF asset)
# and a live-browser download runs separately. Every structure below
# accepts a new company by adding one PERIODS entry and one KEY_MAP
# entry; no redesign is needed. Until its statements exist, HBL has
# no ratios, no health row, and no warning row — it is reported as
# PENDING, never as zero or NOT_CALCULABLE-by-missing-data confusion.
PENDING_COMPANIES = {HBL: "statements not yet loaded (HBL CY2025 PDF blocked at download)"}

# ---------------------------------------------------------------------------
# Period configuration. BS dates are point-in-time statement dates;
# flow periods are the income/cash-flow windows they pair with.
# period_days is computed from the dates, never assumed (365/274/184).
# ---------------------------------------------------------------------------

PERIODS = {
    HUBC: {
        "label": "FY2026 annual (audited, consolidated)",
        "flow_current": ("2025-07-01", "2026-06-30", "annual"),
        "flow_prior": ("2024-07-01", "2025-06-30", "annual"),
        "bs_current": "2026-06-30",
        "bs_prior": "2025-06-30",
    },
    NML: {
        "label": "nine months to 31 Mar 2025 (unaudited, consolidated)",
        "flow_current": ("2024-07-01", "2025-03-31", "nine_month"),
        "flow_prior": ("2023-07-01", "2024-03-31", "nine_month"),
        "bs_current": "2025-03-31",
        "bs_prior": "2024-06-30",  # comparative column date, NOT the flow start
    },
    OGDC: {
        "label": "six months to 31 Dec 2025 (unaudited, consolidated)",
        "flow_current": ("2025-07-01", "2025-12-31", "half_yearly"),
        "flow_prior": ("2024-07-01", "2024-12-31", "half_yearly"),
        "bs_current": "2025-12-31",
        "bs_prior": "2025-06-30",
    },
}

# ---------------------------------------------------------------------------
# Per-company line-item key maps. Keys differ by issuer presentation;
# the canonical name is what formulas consume. A None value means the
# issuer's extracted statements carry no such line — the dependent
# metrics are NOT_CALCULABLE (or, for OGDC finance costs, not
# applicable by structure: see coverage.py).
# ---------------------------------------------------------------------------

KEY_MAPS = {
    HUBC: {
        "revenue": "revenue",
        "cost": "cost_of_revenue",
        "gross_profit": "gross_profit",
        "operating_profit": "profit_from_operations",
        "finance_cost": "finance_costs",
        "pat": "net_profit_for_year",
        "owners_profit": "profit_year",  # changes_in_equity face, scope NULL
        "eps": "eps_total",
        "ocf": "net_operating",
        "capex": "fixed_capex",
        "dividends": ("div_owners", "div_nci"),  # summed, absolute value
        "cash": "cash_and_bank_balances",
        "current_assets": "current_assets_total",
        "current_liabilities": "current_liabilities_total",
        "inventory": ("stock_in_trade", "stores_spares_consumables"),
        "trade_debts": "trade_debts",
        "payables": "trade_and_other_payables",
        "total_assets": "total_assets",
        "total_liabilities": None,  # derived: total_assets - total_equity
        "total_equity": "total_equity",
        "owners_equity": "equity_attributable_to_owners",
        "ib_debt": (
            "long_term_loans",
            "long_term_lease_liabilities",
            "current_maturity_long_term_loans",
            "current_maturity_long_term_lease_liabilities",
            "short_term_borrowings",
        ),
    },
    NML: {
        "revenue": "revenue",
        "cost": "cost_of_sales",
        "gross_profit": "gross_profit",
        "operating_profit": "profit_from_operations",
        "finance_cost": "finance_cost",
        "pat": "profit_after_taxation",
        "owners_profit": None,
        "eps": "eps_basic",
        "ocf": "net_operating",
        "capex": "capex",
        "dividends": ("dividend_paid",),
        "cash": "cash_and_bank_balances",
        "current_assets": "current_assets_total",
        "current_liabilities": "current_liabilities_total",
        "inventory": ("stock_in_trade", "stores_spare_parts"),
        "trade_debts": "trade_debts",
        "payables": "trade_and_other_payables",
        "total_assets": "total_assets",
        "total_liabilities": "total_liabilities",
        "total_equity": "total_equity",
        "owners_equity": "equity_attributable_to_owners",
        "ib_debt": (
            "long_term_financing",
            "lease_liabilities",
            "current_portion_non_current_liabilities",
            "short_term_borrowings",
        ),
    },
    OGDC: {
        "revenue": "sales_net",
        "cost": None,  # derived exactly: sales_net - gross_profit (documented)
        "gross_profit": "gross_profit",
        "operating_profit": None,  # no operating-profit line extracted
        "finance_cost": None,  # no finance-cost line; no interest-bearing loans
        "pat": "profit_for_period",
        "owners_profit": None,
        "eps": "eps_basic",
        "ocf": "net_operating",
        "capex": "capex",
        "dividends": ("dividends_paid",),
        "cash": "cash_and_bank_balances",
        "current_assets": "current_assets_total",
        "current_liabilities": "current_liabilities_total",
        "inventory": ("stock_in_trade", "stores_spare_parts"),
        "trade_debts": "trade_debts",
        "payables": "trade_and_other_payables",
        "total_assets": "total_assets",
        "total_liabilities": "total_liabilities",
        "total_equity": "total_equity",
        "owners_equity": None,  # no NCI split on the extracted balance sheet
        "ib_debt": ("long_term_lease_liability", "short_term_lease_liability"),
    },
}

# ---------------------------------------------------------------------------
# Metric registry v1.0: (category, formula_text, unit).
# Categories match the FinancialHealthAssessment vocabulary plus
# 'market' (multiples) and 'level' (cash-flow levels, not ratios).
# ---------------------------------------------------------------------------

METRICS: dict[str, tuple[str, str, str]] = {
    # Profitability
    "gross_margin": ("profitability", "gross_profit / revenue", "ratio"),
    "operating_margin": ("profitability", "profit_from_operations / revenue", "ratio"),
    "net_margin": ("profitability", "profit_after_tax / revenue", "ratio"),
    "roa": ("profitability", "profit_after_tax / average total_assets", "ratio"),
    "roe_total": ("profitability", "profit_after_tax / average total_equity", "ratio"),
    "roe_owners": (
        "profitability",
        "profit_attributable_to_owners / average equity_attributable_to_owners",
        "ratio",
    ),
    "roce": (
        "profitability",
        "profit_from_operations / average capital_employed "
        "(capital_employed = total_equity + interest_bearing_debt)",
        "ratio",
    ),
    "roic": (
        "profitability",
        "NOT_CALCULABLE in v1.0: NOPAT needs a validated tax allocation; "
        "HUBC operating profit includes post-tax associate earnings, so a "
        "group-rate NOPAT would misstate. Formula reserved, not estimated.",
        "ratio",
    ),
    # Liquidity
    "current_ratio": ("liquidity", "current_assets / current_liabilities", "x"),
    "quick_ratio": (
        "liquidity",
        "(current_assets - inventory) / current_liabilities; "
        "inventory = stock_in_trade + stores/spares",
        "x",
    ),
    "cash_ratio": ("liquidity", "cash_and_bank_balances / current_liabilities", "x"),
    # Leverage
    "debt_to_assets": ("leverage", "total_liabilities / total_assets", "ratio"),
    "debt_to_equity": ("leverage", "total_liabilities / total_equity", "ratio"),
    "ib_debt_to_equity": ("leverage", "interest_bearing_debt / total_equity", "ratio"),
    "interest_coverage": (
        "leverage",
        "profit_from_operations / absolute finance_cost",
        "x",
    ),
    # Efficiency (days use exact calendar days in the flow period)
    "receivables_days": (
        "efficiency",
        "average trade_debts / revenue x period_days",
        "days",
    ),
    "inventory_days": (
        "efficiency",
        "average inventory / cost x period_days",
        "days",
    ),
    "payables_days": (
        "efficiency",
        "average trade_and_other_payables / cost x period_days; "
        "payables line is total trade_and_other_payables as printed "
        "(no trade-only split available), so this is an upper bound",
        "days",
    ),
    "receivables_turnover": ("efficiency", "revenue / average trade_debts", "x"),
    # Growth (same-length comparison only: FY-vs-FY, 9M-vs-9M, 6M-vs-6M)
    "revenue_growth": ("growth", "(revenue - prior_revenue) / prior_revenue", "ratio"),
    "pat_growth": ("growth", "(pat - prior_pat) / prior_pat", "ratio"),
    "eps_growth": ("growth", "(eps - prior_eps) / prior_eps", "ratio"),
    "assets_growth": (
        "growth",
        "(total_assets_current_bs - total_assets_prior_bs) / total_assets_prior_bs",
        "ratio",
    ),
    "equity_growth": (
        "growth",
        "(total_equity_current_bs - total_equity_prior_bs) / total_equity_prior_bs",
        "ratio",
    ),
    # Cash flow
    "ocf": ("cash_flow", "net cash from operating activities (as printed)", "PKR"),
    "fcf": ("cash_flow", "net_operating + capex (capex is negative as printed)", "PKR"),
    "cash_conversion": ("cash_flow", "net_operating / profit_after_tax", "ratio"),
    "dividend_cash_coverage": (
        "cash_flow",
        "net_operating / absolute dividends_paid",
        "x",
    ),
    "accruals": ("cash_flow", "profit_after_tax - net_operating", "PKR"),
    # Earnings quality
    "accruals_to_pat": (
        "earnings_quality",
        "accruals / absolute profit_after_tax",
        "ratio",
    ),
    "gross_margin_change_pp": (
        "earnings_quality",
        "gross_margin_current - gross_margin_prior, in percentage points",
        "pp",
    ),
    "receivables_divergence_pp": (
        "earnings_quality",
        "trade_debts growth (current vs prior BS) minus revenue growth, in pp",
        "pp",
    ),
    "inventory_growth_pct": (
        "earnings_quality",
        "(inventory_current_bs - inventory_prior_bs) / inventory_prior_bs",
        "ratio",
    ),
    # Market multiples — NOT_CALCULABLE in v1.0 (see coverage.py).
    "pe_ratio": (
        "market",
        "NOT_CALCULABLE in v1.0: single unadjusted close (2026-11-03), "
        "no corporate-action adjustment methodology, price date not aligned "
        "to statement publication; EPS periods are interim for NML/OGDC.",
        "x",
    ),
    "pb_ratio": (
        "market",
        "NOT_CALCULABLE in v1.0: book value per share needs a share count, "
        "which no extracted statement provides; same price limitations as pe_ratio.",
        "x",
    ),
    "dividend_yield": (
        "market",
        "NOT_CALCULABLE in v1.0: needs dividends per share (needs a share "
        "count) and an aligned adjusted price; neither is available.",
        "ratio",
    ),
}

# Metrics whose NOT_CALCULABLE state is structural (not missing data).
NOT_APPLICABLE = {
    # OGDC carries no interest-bearing loans in its extracted statements
    # (lease liabilities only) and no finance-cost line: coverage is not
    # applicable by structure, not merely missing.
    ("interest_coverage", OGDC): (
        "not_applicable_by_structure: no finance-cost line and no "
        "interest-bearing loans in the extracted statements (lease "
        "liabilities only); a coverage ratio has no denominator by design"
    ),
}
