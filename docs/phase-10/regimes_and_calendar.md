# Phase 10 — Regimes and event calendar

## Regime method (regime-v1)

A regime label is assigned only when stored observations (public by the
assessment date) support it AND the source's own assessment does not
contradict it. Labels considered but not assigned are recorded with
reasons — an absent label is a finding, not an oversight. Regime rows
are immutable; a revised assessment is a new row.

## Assessment as of 2026-11-04: TIGHTENING

Basis: the SBP MPC raised the policy rate 50 bps to 12% on 2026-10-26
(effective 2026-10-27, 9/10 votes, SBP MPS, VERIFIED) with September
CPI at 10.3% y/y, above the 5–7% target range. The MPS states the
decision's intent: keep the real policy rate adequately positive and
bring inflation into target. That is a tightening stance by the
decision-maker's own description.

## Labels NOT assigned (with reasons)

| Label | Why not assigned |
|---|---|
| Disinflation | October CPI YoY (press 9.6%) was not read from PBS directly and is not a stored observation. September YoY (10.3%) + October MoM (1.1%) alone do not establish a trend. |
| External pressure | The MPS itself says the external account and growth outlook remained broadly unchanged, with reserves stable around US$21.5 bn. A single-quarter CAD of US$874 m does not override the source's own assessment. |
| Slowdown | The MPS says activity started to recover gradually (LSM +1.9% y/y Jul–Aug FY27; GDP FY26 3.7%). A slowdown label would contradict the source. |
| Fiscal consolidation | Q1-FY27 FBR collection beat target and the MPS notes continued consolidation, but one quarter's collection growth (7.0% y/y) is not a regime determination. |

## Outlook (FORECASTS — never observations)

- SBP FY27 real GDP projection: 3.5–4.5% (MPS 2026-10-26).
- SBP inflation target: 5–7% over the medium term (MPS 2026-10-26).
- SBP FY27 current account deficit projection: 0–1% of GDP (MPS 2026-10-26).
- IMF FY27 inflation forecast: 9.9% (as reported in press; NOT read
  from the IMF, NOT stored).

## Event calendar

| Date | Event | Quality | Source |
|---|---|---|---|
| 2026-10-26 | SBP MPC decision: policy rate to 12% | VERIFIED | SBP MPS (read directly) + press agreement |
| 2026-11-02 | PBS Monthly Inflation Report for October 2026 published | PARTIALLY_VERIFIED | Business Recorder + Profit reporting PBS (release page not directly read) |
| 2026-11-20 | SBP MPC minutes for 26 Oct meeting due | UNVERIFIED | Single press source; confirm against sbp.org.pk |
| 2026-12-14 | SBP MPC meeting scheduled | PARTIALLY_VERIFIED | SBP FY27 calendar as read by Pakera, corroborated by The Scoop; SBP calendar page not directly read; date may change if SBP announces a revision |

## Freshness discipline

Monthly data is never presented as real-time. Every observation
carries its reference period, its publication date where known (else
the collection-date fallback), and its collection timestamp. The API
point-in-time endpoint enforces this: it returns only what was public
on the chosen date.
