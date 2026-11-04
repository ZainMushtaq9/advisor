"""Phase 10 macro/sector intelligence services.

Pure data and deterministic rules over official statistics. Nothing here
invents a value: an indicator without a directly read official value is
absent (NOT_CALCULABLE in assessments), never zero, never estimated.
FRED is NOT used anywhere in this package (Phase 1 gate G-06 keeps FRED
out of AI training/caching/commercial output; SBP and PBS suffice here).

Observation discipline (project-wide provenance rules, applied):
- observation_date = the reference period the value is FOR (month-end
  for monthly, quarter-end for quarterly, effective date for the policy
  rate, fiscal-year-end for annual).
- source_timestamp = the publication date where the publisher states
  one (SBP MPS dated 2026-10-26; PBS October CPI posted 2026-11-02).
  Where the publisher page shows no publication date (PBS homepage
  headline values), source_timestamp is NULL and point-in-time
  retrieval falls back to collected_at — the earliest date the value
  is provably public. Collection time is NEVER an observation time.
- quality_status follows rule H1: VERIFIED requires >=2 distinct
  agreeing sources including one official. "Agreeing" is judged at the
  precision the official source publishes (e.g. PBS 3.65% vs SBP MPS
  3.7% agree at one decimal). The second source and its value are
  recorded per indicator in CROSS_CHECKS below and in the run report;
  a row never claims VERIFIED on a single source.
- Revisions are new versions (version_number + 1, supersedes_id set,
  old row kept, only is_current flips) — never edits. The
  economic_indicators table enforces this at the database level.
- Forecasts are never stored as observations. SBP outlook ranges and
  the IMF forecast cited in press appear only in regime evidence under
  evidence["outlook"], explicitly marked FORECAST.

Company exposures: every row cites issuer-disclosure evidence (a Phase 7
statement line key). Sector membership alone is never an exposure.
Cases reviewed but NOT established are listed in the run report, not
stored as exposures: HUBC foreign-exchange exposure (no FX line in its
loaded statements), OGDC borrowing-cost exposure (no finance-cost line;
interest coverage is not_applicable by structure), and any
commodity-level split of OGDC sales (sales_net carries no commodity
breakdown in the loaded statements).

HBL (Habib Bank Limited, company 277, COMMERCIAL BANKS) is PENDING:
its CY2025 statements are not loaded (PDF blocked at download; a
live-browser download runs separately). It has no exposure rows and no
computed sector values; the banking sector profile exists as framework
only, marked pending.
"""

from __future__ import annotations

CALCULATION_VERSION = "1.0"
REGIME_METHOD_VERSION = "regime-v1"

# Company ids in the live registry (post-recovery numbering).
# Company tickers in the live registry. Config is keyed by TICKER, never by
# surrogate company id: ids shift across fresh registry imports (see the
# Phase 8 note), and id-keyed config silently stopped matching after
# that shift. Live ids are resolved from the database by ticker at run time.
HUBC = "HUBC"  # The Hub Power Company Limited
NML = "NML"  # Nishat Mills Limited
OGDC = "OGDC"  # Oil & Gas Development Company Limited
HBL = "HBL"  # Habib Bank Limited (PENDING input)

PENDING_COMPANIES = {HBL: "statements not yet loaded (HBL CY2025 PDF blocked at download)"}

# Sector ids in the live registry.
SECTOR_POWER = 16  # POWER GENERATION & DISTRIBUTION
SECTOR_TEXTILE = 8  # TEXTILE COMPOSITE
SECTOR_EP = 36  # OIL & GAS EXPLORATION COMPANIES
SECTOR_BANKS = 4  # COMMERCIAL BANKS

# ---------------------------------------------------------------------------
# Indicator registry. Keys are stable; units and frequencies are part of
# the definition so a consumer can never mistake a MoM rate for a YoY one.
# ---------------------------------------------------------------------------

INDICATORS = {
    "sbp_policy_rate": {
        "name": "SBP policy rate (target rate)",
        "unit": "% p.a.",
        "frequency": "event",
        "publisher": "State Bank of Pakistan",
    },
    "cpi_yoy": {
        "name": "CPI inflation, year on year (national)",
        "unit": "% y/y",
        "frequency": "monthly",
        "publisher": "PBS via SBP MPS (SBP citing PBS)",
    },
    "cpi_core": {
        "name": "Core inflation (non-food non-energy, national)",
        "unit": "% y/y",
        "frequency": "monthly",
        "publisher": "State Bank of Pakistan",
    },
    "cpi_mom": {
        "name": "CPI inflation, month on month (national)",
        "unit": "% m/m",
        "frequency": "monthly",
        "publisher": "Pakistan Bureau of Statistics",
    },
    "gdp_growth_fy": {
        "name": "Real GDP growth, fiscal year (provisional)",
        "unit": "% y/y",
        "frequency": "annual",
        "publisher": "Pakistan Bureau of Statistics",
    },
    "gdp_growth_q4": {
        "name": "Real GDP growth, Q4 of fiscal year",
        "unit": "% y/y",
        "frequency": "quarterly",
        "publisher": "Pakistan Bureau of Statistics",
    },
    "lsm_growth": {
        "name": "Large-scale manufacturing output growth",
        "unit": "% y/y",
        "frequency": "monthly",
        "publisher": "Pakistan Bureau of Statistics",
    },
    "sbp_fx_reserves": {
        "name": "SBP foreign exchange reserves",
        "unit": "US$ billion",
        "frequency": "weekly",
        "publisher": "State Bank of Pakistan",
    },
    "current_account_deficit": {
        "name": "Current account deficit",
        "unit": "US$ million",
        "frequency": "quarterly",
        "publisher": "State Bank of Pakistan",
    },
    "m2_growth": {
        "name": "Broad money (M2) growth",
        "unit": "% y/y",
        "frequency": "weekly",
        "publisher": "State Bank of Pakistan",
    },
    "fbr_tax_growth": {
        "name": "FBR tax collection growth",
        "unit": "% y/y",
        "frequency": "quarterly",
        "publisher": "FBR via SBP MPS (SBP citing FBR)",
    },
    "spi_wow": {
        "name": "Sensitive Price Index change, week on week",
        "unit": "% w/w",
        "frequency": "weekly",
        "publisher": "Pakistan Bureau of Statistics",
    },
}

# Second-source agreement basis for every VERIFIED row (rule H1). The
# stored value is the first source's value; the second source agrees at
# the precision stated. Rows without an entry here are UNVERIFIED.
CROSS_CHECKS = {
    "sbp_policy_rate": (
        "SBP MPS 2026-10-26: 12% from 2026-10-27; Business Recorder / "
        "Express Tribune / Daily Star reporting the same decision: 12%."
    ),
    "cpi_yoy": (
        "SBP MPS 2026-10-26 (citing PBS): 10.3% for September 2026; "
        "Business Recorder / Profit reporting PBS: 10.3% (precise PBS "
        "figure 10.26% rounds to 10.3 at SBP's one-decimal precision)."
    ),
    "cpi_mom": (
        "PBS homepage: 1.1% for October 2026; Business Recorder / Profit "
        "reporting PBS: 1.1% month on month."
    ),
    "gdp_growth_fy": (
        "PBS homepage: 3.65% provisional for 2025-26; SBP MPS 2026-10-26 "
        "(citing PBS revised figure): 3.7% — agrees at one decimal."
    ),
    "lsm_growth": (
        "PBS homepage: 1.85% for Jul-Aug 2026-27; SBP MPS 2026-10-26: "
        "1.9% y/y for July-August FY27 — agrees at one decimal."
    ),
    "sbp_fx_reserves": (
        "SBP MPS 2026-10-26: 'around US$21.5 billion'; SBP weekly reserves "
        "figure as reported: US$21.52 billion as of 2026-10-23 — agrees "
        "at 0.1 billion precision."
    ),
}

# ---------------------------------------------------------------------------
# Observations collected for v1. Each row: indicator_code,
# observation_date (reference period), value, source_key,
# source_timestamp (publication date or None), quality_status.
# Values are Decimal strings; "around" values keep the published figure
# with an explicit note in the run report, never a sharpened estimate.
# ---------------------------------------------------------------------------

OBSERVATIONS = [
    {
        "indicator_code": "sbp_policy_rate",
        "observation_date": "2026-10-27",
        "value": "12.00",
        "source_key": "sbp_mps_oct_2026",
        "source_timestamp": "2026-10-26",
        "quality_status": "VERIFIED",
    },
    {
        "indicator_code": "cpi_yoy",
        "observation_date": "2026-09-30",
        "value": "10.3",
        "source_key": "sbp_mps_oct_2026",
        "source_timestamp": "2026-10-26",
        "quality_status": "VERIFIED",
    },
    {
        "indicator_code": "cpi_core",
        "observation_date": "2026-09-30",
        "value": "8.4",
        "source_key": "sbp_mps_oct_2026",
        "source_timestamp": "2026-10-26",
        "quality_status": "UNVERIFIED",
    },
    {
        "indicator_code": "cpi_mom",
        "observation_date": "2026-10-31",
        "value": "1.1",
        "source_key": "pbs_homepage",
        "source_timestamp": "2026-11-02",
        "quality_status": "VERIFIED",
    },
    {
        "indicator_code": "gdp_growth_fy",
        "observation_date": "2026-06-30",
        "value": "3.65",
        "source_key": "pbs_homepage",
        "source_timestamp": None,
        "quality_status": "VERIFIED",
    },
    {
        "indicator_code": "gdp_growth_q4",
        "observation_date": "2026-06-30",
        "value": "2.00",
        "source_key": "pbs_homepage",
        "source_timestamp": None,
        "quality_status": "UNVERIFIED",
    },
    {
        "indicator_code": "lsm_growth",
        "observation_date": "2026-08-31",
        "value": "1.85",
        "source_key": "pbs_homepage",
        "source_timestamp": None,
        "quality_status": "VERIFIED",
    },
    {
        "indicator_code": "sbp_fx_reserves",
        "observation_date": "2026-10-26",
        "value": "21.5",
        "source_key": "sbp_mps_oct_2026",
        "source_timestamp": "2026-10-26",
        "quality_status": "VERIFIED",
    },
    {
        "indicator_code": "current_account_deficit",
        "observation_date": "2026-09-30",
        "value": "874",
        "source_key": "sbp_mps_oct_2026",
        "source_timestamp": "2026-10-26",
        "quality_status": "UNVERIFIED",
    },
    {
        "indicator_code": "m2_growth",
        "observation_date": "2026-10-09",
        "value": "12.7",
        "source_key": "sbp_mps_oct_2026",
        "source_timestamp": "2026-10-26",
        "quality_status": "UNVERIFIED",
    },
    {
        "indicator_code": "fbr_tax_growth",
        "observation_date": "2026-09-30",
        "value": "7.0",
        "source_key": "sbp_mps_oct_2026",
        "source_timestamp": "2026-10-26",
        "quality_status": "UNVERIFIED",
    },
    {
        "indicator_code": "spi_wow",
        "observation_date": "2026-10-02",
        "value": "-0.35",
        "source_key": "pbs_homepage",
        "source_timestamp": None,
        "quality_status": "UNVERIFIED",
    },
]

# ---------------------------------------------------------------------------
# Company exposures: issuer-disclosure evidence only. evidence_ref cites
# "statement_type:line_item_key" from the loaded Phase 7 statements.
# ---------------------------------------------------------------------------

EXPOSURES = [
    {
        "ticker": HUBC,
        "exposure_key": "rates_borrowing_cost",
        "exposure_name": "Interest-rate / borrowing-cost exposure",
        "direction": "cost",
        "evidence_type": "statement_line_item",
        "evidence_ref": (
            "income:finance_costs; cash_flow:interest_paid; balance_sheet:short_term_borrowings"
        ),
        "note": (
            "FY2026 income statement carries finance costs and the cash-flow "
            "statement carries interest paid; a higher policy rate raises "
            "this company's borrowing costs. No FX line exists in its loaded "
            "statements, so no FX exposure is recorded for HUBC."
        ),
        "quality_status": "UNVERIFIED",
    },
    {
        "ticker": NML,
        "exposure_key": "rates_borrowing_cost",
        "exposure_name": "Interest-rate / borrowing-cost exposure",
        "direction": "cost",
        "evidence_type": "statement_line_item",
        "evidence_ref": (
            "income:finance_cost; balance_sheet:long_term_financing; "
            "balance_sheet:short_term_borrowings"
        ),
        "note": (
            "Income statement carries finance cost and the balance sheet "
            "carries secured long-term financing and short-term borrowings."
        ),
        "quality_status": "UNVERIFIED",
    },
    {
        "ticker": NML,
        "exposure_key": "fx_forward_contracts",
        "exposure_name": "Foreign-exchange exposure via forward contracts",
        "direction": "revenue",
        "evidence_type": "statement_line_item",
        "evidence_ref": "cash_flow:exchange_gain_forward",
        "note": (
            "Cash-flow statement records exchange gains on forward exchange "
            "contracts received — the company hedges FX exposure, which is "
            "itself evidence of FX exposure."
        ),
        "quality_status": "UNVERIFIED",
    },
    {
        "ticker": NML,
        "exposure_key": "fx_translation",
        "exposure_name": "Foreign-exchange translation exposure",
        "direction": "balance_sheet",
        "evidence_type": "statement_line_item",
        "evidence_ref": "cash_flow:exchange_translation",
        "note": (
            "Cash-flow statement records exchange differences on translation "
            "of net investments in foreign subsidiaries."
        ),
        "quality_status": "UNVERIFIED",
    },
    {
        "ticker": OGDC,
        "exposure_key": "fx_transaction",
        "exposure_name": "Foreign-exchange transaction exposure",
        "direction": "revenue",
        "evidence_type": "statement_line_item",
        "evidence_ref": "cash_flow:exchange_gain_loss",
        "note": (
            "Cash-flow statement records net exchange (gain)/loss — "
            "dollar-linked sales and costs flow through earnings."
        ),
        "quality_status": "UNVERIFIED",
    },
    {
        "ticker": OGDC,
        "exposure_key": "rates_interest_income",
        "exposure_name": "Interest-rate exposure via interest income",
        "direction": "income",
        "evidence_type": "statement_line_item",
        "evidence_ref": ("cash_flow:interest_income_investments; cash_flow:interest_income_lease"),
        "note": (
            "Direction is INCOME, not cost: this company earns interest on "
            "investments, bank deposits and leases, so higher rates raise "
            "its interest income. It carries no finance-cost line in its "
            "loaded statements, so no borrowing-cost exposure is recorded."
        ),
        "quality_status": "UNVERIFIED",
    },
]

# ---------------------------------------------------------------------------
# Sector profiles (stored in sector_metric_profiles with metric_key
# "macro:<indicator_code>"). These are framework notes — which indicators
# matter for the sector and why — not company exposure claims. The
# "latest value" pointer in source_requirements names the stored
# observation; HBL's sector row is framework only (HBL pending).
# ---------------------------------------------------------------------------

SECTOR_PROFILES = [
    {
        "sector_id": SECTOR_POWER,
        "metric_key": "macro:sbp_policy_rate",
        "applicability": (
            "Power generation is capital-intensive and debt-funded: the "
            "policy rate drives borrowing costs (HUBC finance costs are "
            "issuer-evidenced). Transmission: rate rise -> higher finance "
            "costs -> lower margins, unless tariffs pass costs through."
        ),
        "source_requirements": "Latest stored observation: sbp_policy_rate 12.00% p.a. effective"
        " 2026-10-27 (SBP MPS 2026-10-26, VERIFIED).",
    },
    {
        "sector_id": SECTOR_POWER,
        "metric_key": "macro:cpi_yoy",
        "applicability": (
            "Energy and wheat prices drive headline CPI and feed back into "
            "fuel/power purchase costs. Transmission: energy-price shock -> "
            "CPI up -> policy tightening -> borrowing costs up. Correlation "
            "is not causation: CPI does not set tariffs."
        ),
        "source_requirements": "Latest stored observation: cpi_yoy 10.3% for September 2026 (SBP"
        " MPS citing PBS, VERIFIED). October YoY (press 9.6%) is NOT stored: the PBS monthly"
        " review was not directly read.",
    },
    {
        "sector_id": SECTOR_POWER,
        "metric_key": "macro:sbp_fx_reserves",
        "applicability": (
            "Import cover context for fuel imports: reserves near 3 months "
            "of import cover constrain the external buffer for energy "
            "imports. Framework context only — no HUBC fuel-import exposure "
            "is claimed from sector membership."
        ),
        "source_requirements": "Latest stored observation: sbp_fx_reserves around US$21.5 billion"
        " (SBP MPS 2026-10-26, VERIFIED).",
    },
    {
        "sector_id": SECTOR_TEXTILE,
        "metric_key": "macro:sbp_policy_rate",
        "applicability": (
            "Textiles carry large working-capital borrowings: the policy "
            "rate drives finance cost directly (NML finance cost and "
            "short/long-term borrowings are issuer-evidenced). "
            "Transmission: rate rise -> working-capital cost up -> margins "
            "compressed, especially for exporters facing soft demand."
        ),
        "source_requirements": "Latest stored observation: sbp_policy_rate 12.00% p.a. effective"
        " 2026-10-27 (SBP MPS 2026-10-26, VERIFIED).",
    },
    {
        "sector_id": SECTOR_TEXTILE,
        "metric_key": "macro:lsm_growth",
        "applicability": (
            "LSM is the closest official output proxy for manufacturing "
            "demand, including textiles. Transmission: LSM recovery -> "
            "order books improve; LSM weakness -> pricing pressure. "
            "Sector-level context only."
        ),
        "source_requirements": "Latest stored observation: lsm_growth 1.85% y/y for Jul-Aug 2026-27"
        " (PBS homepage, VERIFIED).",
    },
    {
        "sector_id": SECTOR_TEXTILE,
        "metric_key": "macro:cpi_mom",
        "applicability": (
            "Monthly CPI momentum proxies input-cost and wage pressure "
            "facing manufacturers. Transmission: sustained MoM pressure -> "
            "cost-push margins squeeze before output prices adjust."
        ),
        "source_requirements": "Latest stored observation: cpi_mom 1.1% for October 2026 (PBS"
        " homepage, VERIFIED).",
    },
    {
        "sector_id": SECTOR_EP,
        "metric_key": "macro:current_account_deficit",
        "applicability": (
            "E&P earnings are dollar-linked while the external account sets "
            "the FX context: a widening deficit pressures the rupee and "
            "raises the PKR value of dollar sales, but also raises import "
            "and financing costs. Framework context only."
        ),
        "source_requirements": "Latest stored observation: current_account_deficit US$874 million"
        " for Q1-FY27 (SBP MPS 2026-10-26, UNVERIFIED).",
    },
    {
        "sector_id": SECTOR_EP,
        "metric_key": "macro:sbp_fx_reserves",
        "applicability": (
            "Reserve cover frames how much external shock the economy can "
            "absorb before FX adjustment; E&P cash flows are among the most "
            "FX-sensitive in the registry (OGDC exchange gain/loss is "
            "issuer-evidenced)."
        ),
        "source_requirements": "Latest stored observation: sbp_fx_reserves around US$21.5 billion"
        " (SBP MPS 2026-10-26, VERIFIED).",
    },
    {
        "sector_id": SECTOR_EP,
        "metric_key": "macro:cpi_yoy",
        "applicability": (
            "Energy prices are a first-order CPI driver, so CPI is both a "
            "consequence of energy prices and a trigger for policy that "
            "feeds back into E&P financing conditions. No causal claim is "
            "made from correlation alone."
        ),
        "source_requirements": "Latest stored observation: cpi_yoy 10.3% for September 2026 (SBP"
        " MPS citing PBS, VERIFIED).",
    },
    {
        "sector_id": SECTOR_BANKS,
        "metric_key": "macro:sbp_policy_rate",
        "applicability": (
            "Banks are the transmission channel itself: the policy rate "
            "sets the corridor (floor/ceiling) and reprices assets and "
            "liabilities. Framework only — HBL has no loaded statements, "
            "so no HBL exposure or margin claim is made."
        ),
        "source_requirements": "Latest stored observation: sbp_policy_rate 12.00% p.a. effective"
        " 2026-10-27 (SBP MPS 2026-10-26, VERIFIED). HBL PENDING.",
    },
    {
        "sector_id": SECTOR_BANKS,
        "metric_key": "macro:m2_growth",
        "applicability": (
            "M2 growth proxies system liquidity and deposit growth, which "
            "frame bank funding conditions. Framework only — no HBL "
            "deposit or advance claim is made."
        ),
        "source_requirements": "Latest stored observation: m2_growth 12.7% y/y as of 2026-10-09"
        " (SBP MPS 2026-10-26, UNVERIFIED). HBL PENDING.",
    },
    {
        "sector_id": SECTOR_BANKS,
        "metric_key": "macro:current_account_deficit",
        "applicability": (
            "External deficits drive FX and reserve dynamics that feed bank "
            "treasury and trade-finance conditions. Framework only."
        ),
        "source_requirements": "Latest stored observation: current_account_deficit US$874 million"
        " for Q1-FY27 (SBP MPS 2026-10-26, UNVERIFIED). HBL PENDING.",
    },
]

# ---------------------------------------------------------------------------
# Regime assessment (regime-v1) as of 2026-11-04, using ONLY data public
# by that date. One label is assigned; three candidate labels are
# explicitly NOT assigned with reasons — an absent label is a finding,
# not an oversight. Outlook figures are FORECASTS, never observations.
# ---------------------------------------------------------------------------

REGIME_ASSESSMENT = {
    "observation_date": "2026-11-04",
    "regime_label": "tightening",
    "method_version": REGIME_METHOD_VERSION,
    "evidence": {
        "assigned_basis": (
            "SBP MPC raised the policy rate 50 bps to 12% on 2026-10-26, "
            "effective 2026-10-27 (SBP MPS, VERIFIED), with September CPI "
            "10.3% y/y above the 5-7% target range — a tightening stance "
            "by the central bank's own stated intent (keep real policy "
            "rate adequately positive, bring inflation into target)."
        ),
        "not_assigned": {
            "disinflation": (
                "Not assigned: October CPI YoY (press 9.6%) was not read "
                "from PBS directly and is not a stored observation; "
                "September YoY (10.3%) plus October MoM (1.1%) alone do "
                "not establish a disinflation trend."
            ),
            "external_pressure": (
                "Not assigned: the SBP MPS itself says the external "
                "account and growth outlook remained broadly unchanged, "
                "with reserves stable around US$21.5 billion; a Q1-FY27 "
                "current account deficit of US$874 million alone does not "
                "override the source's own assessment."
            ),
            "slowdown": (
                "Not assigned: the SBP MPS says activity started to "
                "recover gradually (LSM +1.9% y/y Jul-Aug FY27, GDP FY26 "
                "3.7%), which contradicts a slowdown label."
            ),
            "fiscal_consolidation": (
                "Not assigned: Q1-FY27 FBR collection beat target and the "
                "MPS notes continued fiscal consolidation, but a single "
                "quarter's collection growth (7.0% y/y) is not a regime "
                "determination."
            ),
        },
        "outlook_FORECAST_not_observation": {
            "sbp_gdp_fy27_projection": "3.5-4.5% (SBP MPS 2026-10-26, projection)",
            "sbp_inflation_target": "5-7% medium term (SBP MPS 2026-10-26, target)",
            "sbp_cad_fy27_projection": "0-1% of GDP (SBP MPS 2026-10-26, projection)",
            "imf_fy27_inflation_forecast_press_reported": (
                "9.9% (IMF forecast as reported in press; NOT stored as an "
                "observation and NOT independently read from the IMF)"
            ),
        },
    },
    "quality_status": "UNVERIFIED",
    "source_key": "sbp_mps_oct_2026",
    "source_timestamp": "2026-10-26",
}

# ---------------------------------------------------------------------------
# Event calendar. source_key names the actual channel read; press-sourced
# events carry press keys and lower quality — never an official key.
# ---------------------------------------------------------------------------

EVENTS = [
    {
        "event_date": "2026-10-26",
        "event_type": "mpc_meeting",
        "title": "SBP Monetary Policy Committee decision: policy rate raised to 12%",
        "source_key": "sbp_mps_oct_2026",
        "source_timestamp": "2026-10-26",
        "quality_status": "VERIFIED",
        "note": "SBP MPS dated 2026-10-26, read directly; decision (50 bps to 12%, 9/10 votes,"
        " effective 2026-10-27) agrees with press reporting.",
    },
    {
        "event_date": "2026-11-02",
        "event_type": "cpi_release",
        "title": "PBS Monthly Inflation Report for October 2026 published",
        "source_key": "press_brecorder_pbs_release",
        "source_timestamp": None,
        "quality_status": "PARTIALLY_VERIFIED",
        "note": "PBS publication date 2026-11-02 as reported by Business Recorder and Profit (both:"
        " PBS released October CPI on Monday 2026-11-02); the PBS release page itself was not"
        " directly read, so this event is press-sourced, not official-keyed.",
    },
    {
        "event_date": "2026-11-20",
        "event_type": "mpc_minutes",
        "title": "SBP MPC minutes for the 26 October 2026 meeting due",
        "source_key": "press_pakera_mps_minutes",
        "source_timestamp": None,
        "quality_status": "UNVERIFIED",
        "note": "Single press source (Pakera: minutes due 20 November 2026); the SBP calendar page"
        " was not directly read. Confirm against sbp.org.pk before relying on it.",
    },
    {
        "event_date": "2026-12-14",
        "event_type": "mpc_meeting",
        "title": "SBP Monetary Policy Committee meeting scheduled",
        "source_key": "press_pakera_sbp_calendar",
        "source_timestamp": None,
        "quality_status": "PARTIALLY_VERIFIED",
        "note": "SBP FY27 advance calendar as read by Pakera (2026-10-26) and corroborated by The"
        " Scoop; the SBP calendar page itself was not directly read. The SBP may change the"
        " date if something unforeseen happens.",
    },
]

# ---------------------------------------------------------------------------
# Indicators reviewed but NOT stored (with exact unblockers). A missing
# indicator is absent, never zero-filled or estimated.
# ---------------------------------------------------------------------------

NOT_STORED = {
    "cpi_yoy_oct2026": (
        "Press reports PBS October YoY at 9.6% (precise 9.61%), but the PBS "
        "Monthly Review on Price Indices for October 2026 was not directly "
        "read. Unblocker: live-browser fetch of the PBS monthly review PDF "
        "(linked from the PBS 'Monthly Inflation Report for Oct 2026' "
        "release page) or the PBS CPI release page itself."
    ),
    "kibor_yields": (
        "SBP publishes KIBOR and yield curves, but no KIBOR/yield value "
        "was read from an SBP page in this run. Unblocker: direct read of "
        "the SBP money-market/KIBOR page."
    ),
    "usd_pkr_rate": (
        "No USD/PKR reference rate was read from an SBP page in this run. "
        "Unblocker: direct read of the SBP exchange-rate page."
    ),
    "oil_commodity_prices": (
        "No crude-oil or commodity price series was read from an official "
        "source in this run (OGRA/World Bank commodity series not fetched). "
        "Unblocker: direct read of an OGRA or World Bank commodity series."
    ),
    "remittances_level": (
        "The MPS says remittances 'remained resilient' without a level in "
        "the text read; no remittance level was stored. Unblocker: direct "
        "read of the SBP remittances release."
    ),
    "trade_figures": (
        "No export/import levels were read in this run (MPS gives only a "
        "qualitative exports-recovering/imports-rising account). "
        "Unblocker: direct read of PBS trade statistics."
    ),
    "fiscal_balances": (
        "Only FBR collection growth is stored; overall/primary balances "
        "are described qualitatively in the MPS ('assessed to remain in "
        "surplus') without levels. Unblocker: direct read of Ministry of "
        "Finance fiscal operations data."
    ),
    "budget_events": (
        "No FY28 budget date was verified in this run. Unblocker: direct "
        "read of the Ministry of Finance budget calendar."
    ),
}
