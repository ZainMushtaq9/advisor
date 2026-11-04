# Phase 10 — Macro source and indicator registry

## Sources read directly in this run

| Source key | Publisher | Document read | Terms note |
|---|---|---|---|
| `sbp_mps_oct_2026` | State Bank of Pakistan | Monetary Policy Statement, 26 October 2026 (PDF, sbp.org.pk) | Official publication, read directly. Internal analysis only; no republication. |
| `pbs_homepage` | Pakistan Bureau of Statistics | PBS homepage headline values (pbs.gov.pk, crawled 2026-11-04) | Official page, read directly. Headline values only; the page shows no publication dates, so `source_timestamp` is NULL for these rows and point-in-time retrieval falls back to `collected_at`. |

Press keys (`press_brecorder_pbs_release`, `press_pakera_mps_minutes`,
`press_pakera_sbp_calendar`) name the actual press channel read. They are
never keyed as official sources.

FRED was NOT used (Phase 1 gate G-06). World Bank / IMF series were NOT
fetched in this run; SBP and PBS suffice for v1.

## Observations stored (12)

| Indicator | Value | Reference period | Source | Published | Quality | Second-source basis (rule H1) |
|---|---|---|---|---|---|---|
| `sbp_policy_rate` | 12.00 % p.a. | effective 2026-10-27 | SBP MPS | 2026-10-26 | VERIFIED | Tribune / Business Recorder / Daily Star report the same decision: 12%. |
| `cpi_yoy` | 10.3 % y/y | September 2026 | SBP MPS (citing PBS) | 2026-10-26 | VERIFIED | Business Recorder / Profit report PBS September at 10.3% (precise PBS figure 10.26% rounds to 10.3 at SBP's one-decimal precision). |
| `cpi_core` | 8.4 % y/y | September 2026 | SBP MPS | 2026-10-26 | UNVERIFIED | MPS wording is "around 8.4%"; press urban core (8.6%) is a different cut, not agreement. |
| `cpi_mom` | 1.1 % m/m | October 2026 | PBS homepage | 2026-11-02 | VERIFIED | Business Recorder / Profit report PBS October MoM at 1.1%. |
| `gdp_growth_fy` | 3.65 % y/y | FY 2025-26 (provisional) | PBS homepage | not shown | VERIFIED | SBP MPS (citing PBS revised figure) 3.7% — agrees at one decimal. |
| `gdp_growth_q4` | 2.00 % y/y | Q4 2025-26 | PBS homepage | not shown | UNVERIFIED | Single source. |
| `lsm_growth` | 1.85 % y/y | Jul–Aug 2026-27 | PBS homepage | not shown | VERIFIED | SBP MPS 1.9% y/y for July–August FY27 — agrees at one decimal. |
| `sbp_fx_reserves` | ~21.5 US$ bn | as cited 2026-10-26 | SBP MPS | 2026-10-26 | VERIFIED | SBP weekly figure as reported: US$21.52 bn as of 2026-10-23 — agrees at 0.1 bn precision. The MPS itself states no weekly date, so the observation date is the MPS date. |
| `current_account_deficit` | 874 US$ m | Q1-FY27 | SBP MPS | 2026-10-26 | UNVERIFIED | Single source. |
| `m2_growth` | 12.7 % y/y | as of 2026-10-09 | SBP MPS | 2026-10-26 | UNVERIFIED | Single source. |
| `fbr_tax_growth` | 7.0 % y/y | Q1-FY27 | SBP MPS (citing FBR) | 2026-10-26 | UNVERIFIED | Single source. |
| `spi_wow` | −0.35 % w/w | week ended 2026-10-02 | PBS homepage | not shown | UNVERIFIED | Single source. |

Units, periods and releases are preserved: MoM is never mixed with YoY,
the policy rate carries its effective date (not the decision date) as
the observation date, and "around" values keep the published figure
with this note rather than a sharpened estimate.

## Indicators reviewed but NOT stored (absent, never estimated)

| Indicator | Why absent | Exact unblocker |
|---|---|---|
| CPI YoY, October 2026 (press 9.6% / precise 9.61%) | PBS Monthly Review not directly read | Live-browser fetch of the PBS monthly review PDF (linked from the PBS "Monthly Inflation Report for Oct 2026" release page). |
| KIBOR / yields | No SBP money-market value read | Direct read of the SBP KIBOR/yield page. |
| USD/PKR reference rate | No SBP exchange-rate value read | Direct read of the SBP exchange-rate page. |
| Crude-oil / commodity prices | No official commodity series fetched | Direct read of an OGRA or World Bank commodity series. |
| Workers' remittances level | MPS gives only "remained resilient", no level | Direct read of the SBP remittances release. |
| Export / import levels | MPS gives only qualitative direction | Direct read of PBS trade statistics. |
| Fiscal balances (levels) | MPS says "assessed to remain in surplus", no levels | Direct read of Ministry of Finance fiscal operations data. |
| Budget dates | No FY28 budget date verified | Direct read of the Ministry of Finance budget calendar. |
