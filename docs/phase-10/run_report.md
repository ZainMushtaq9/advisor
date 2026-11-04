# Phase 10 — Run report (2026-11-04)

## Verdict: PARTIALLY COMPLETE

The macro engine, registry, sector profiles, exposure register, regime
assessment and event calendar are complete and verified end-to-end.
The verdict is PARTIALLY COMPLETE, not COMPLETE, because: coverage is
2 official sources and 12 observations (no KIBOR/yields, FX rate,
commodity, remittance/trade or fiscal-balance series); October CPI YoY
was not read from PBS directly; all company inputs remain UNVERIFIED;
and HBL is pending. Nothing mandatory is claimed as done that is not
evidenced.

## Acceptance gate (brief, all mandatory items)

| Gate item | Result |
|---|---|
| At least one relevant official source successfully collected and verified | PASS — SBP (MPS 2026-10-26) and PBS (homepage) collected; 6 of 12 observations VERIFIED under rule H1 with documented second sources. |
| Units, periods and releases are preserved | PASS — MoM/YoY/event/annual/quarterly kept distinct; effective date vs decision date kept distinct; "around" values flagged, not sharpened. |
| Company exposures have evidence | PASS — all 6 exposure rows cite Phase 7 statement line keys; sector membership never used as evidence. |
| Point-in-time retrieval and revision handling work | PASS — point-in-time proven live via API (policy rate absent 2026-10-25, known 2026-10-27; CPI MoM absent 2026-11-01, known 2026-11-02); revision proven live in a rolled-back transaction (v1 preserved, v2 current, value edit rejected by trigger, zero scratch rows left). |

## DB counts before / after (live DB verified)

| Measure | Before | After |
|---|---|---|
| `economic_indicators` | 0 | 12 (6 VERIFIED, 6 UNVERIFIED) |
| `company_macro_exposures` | 0 (table new) | 6 |
| `sector_metric_profiles` with `macro:%` | 0 | 12 |
| `macro_regimes` | 0 (table new) | 1 (tightening, 2026-11-04) |
| `macro_events` | 0 (table new) | 4 |
| `data_sources` | 6 | 11 (+5: sbp_mps_oct_2026, pbs_homepage, 3 press keys) |
| Migration head | 20261104_0006 | 20261104_0007 |

Idempotency proven: second `--commit` wrote 0 new rows
(12 observations, 6 exposures, 12 profiles, 1 regime, 4 events,
5 sources all skipped as existing). Phase 7/8/9 rows untouched
(statements 88, prices 444, valuations 51 — unchanged by this run).

## Source-text audit (stored value vs source text read)

| Observation | Source text read | Match |
|---|---|---|
| Policy rate 12.00%, eff. 2026-10-27 | MPS: "increase the policy rate by 50 bps to 12 percent … with effect from October 27, 2026" | Exact |
| CPI YoY Sep 10.3% | MPS: "headline inflation of 10.3 percent y/y in September" | Exact |
| CPI core Sep ~8.4% | MPS: "core inflation has steadied at an elevated level of around 8.4 percent" | Exact, flagged approximate |
| CPI MoM Oct 1.1% | PBS homepage: "Monthly Consumer Price Index — For the Month Ended on Oct 2026: 1.1%" | Exact |
| GDP FY26 3.65% | PBS homepage: "GDP Growth Rate During (2025-26): 3.65%" | Exact |
| GDP Q4 FY26 2.00% | PBS homepage: "Quarterly Growth Q4 2025-26: 2.00%" | Exact |
| LSM Jul–Aug 1.85% | PBS homepage: "Large Scale Manufacturing growth, Jul-Aug 2026-27: 1.85%" | Exact |
| Reserves ~21.5 US$ bn | MPS: "SBP's reserves remained stable at around US$21.5 billion" | Exact, flagged approximate; weekly date not stated in MPS, so observation date = MPS date |
| CAD Q1-FY27 874 US$ m | MPS: "current account balance recorded a deficit of US$874 million in Q1-FY27" | Exact |
| M2 12.7% as of 2026-10-09 | MPS: "Broad money (M2) growth increased to 12.7 percent y/y as of October 9" | Exact |
| FBR growth Q1-FY27 7.0% | MPS: "FBR tax collection grew 7.0 percent y/y" | Exact |
| SPI w/w −0.35% | PBS homepage: "Weekly Sensitive Price Index (SPI) for the Week Ended on 2.10.2026: -0.35%" | Exact |

## Tests and live checks

- Backend suite: 179 passed, 0 failed (162 prior + 17 new pure tests).
- Ruff check + format clean on all new/changed files.
- Live API: `/macro` 200 (12 indicators, 12 with latest);
  point-in-time policy rate absent/known across the publication boundary;
  CPI MoM absent 2026-11-01 / known 2026-11-02; regimes 200
  (tightening); exposures NML 200 (3 rows), HBL 200 (pending),
  unknown ticker 404; events 200 (4); sectors 200 (12 profiles).
- Audit fix applied during this run: `point_in_time` initially trusted
  the caller to filter non-current rows; a test exposed the gap and
  the function now ignores non-current rows itself.

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has no exposure
rows and no computed sector values: its CY2025 statements are not
loaded (PDF blocked at download; live-browser download runs
separately). The banking sector profile exists as framework only.
Design accepts HBL via one exposure set + one sector-value refresh
once its statements load; no redesign needed.

## Remaining blockers (exact unblockers)

1. **October CPI YoY official read** — live-browser fetch of the PBS
   monthly review PDF (linked from the PBS "Monthly Inflation Report
   for Oct 2026" release page).
2. **KIBOR/yields, USD/PKR, commodity, remittance/trade, fiscal
   series** — direct reads of the SBP money-market, exchange-rate and
   remittances pages; PBS trade statistics; Ministry of Finance fiscal
   operations; OGRA/World Bank commodity series.
3. **HBL statements** — separate live-browser HBL CY2025 PDF download,
   then a Phase 7 load, then a Phase 10 re-run adding HBL exposures.
4. **Wider-company / KSE-100 expansion** — Phase 7 expansion beyond
   the 3-company sample (per-company source verification pass).
5. **VERIFIED promotion** — H1 second agreeing source including an
   official source for the 6 UNVERIFIED observations; everything else
   stays at its stored status until then.
6. **Event-date confirmations** — direct reads of the SBP MPC calendar
   (Dec 14 meeting, Nov 20 minutes) and the PBS release page (Nov 2
   CPI release) to upgrade the press-sourced events.
