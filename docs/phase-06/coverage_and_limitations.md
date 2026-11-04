# Phase 6 — Coverage and limitations

## The honest headline

All 62 registered indicators are NOT_CALCULABLE for every one of
the 470 securities on production data today. Zero securities have
any calculable indicator. Zero value rows, zero signal events,
zero regime features. The table below is generated from the live
assessment report (not hand-typed), so its counts are exact.

## Per-indicator NOT_CALCULABLE matrix (as of 2026-11-03)

| Indicator | Category | Warm-up bars | Calculable | Not calculable | Reasons | What would unblock it |
|---|---|---|---|---|---|---|
| cci_20 | momentum | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| daily_return | momentum | 1 | 0 | 470 | missing_data (470) | A present previous_close for the latest bar (future source files must carry it; it cannot be derived from the close column without changing the documented convention; the resulting value would remain UNVERIFIED on single-source data) |
| mfi_14 | momentum | 15 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 15 bars total: 14 more trading days for the 444 one-bar securities, 15 for the 26 zero-bar securities |
| momentum_12 | momentum | 13 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 13 bars total: 12 more trading days for the 444 one-bar securities, 13 for the 26 zero-bar securities |
| roc_12 | momentum | 13 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 13 bars total: 12 more trading days for the 444 one-bar securities, 13 for the 26 zero-bar securities |
| rsi_14 | momentum | 15 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 15 bars total: 14 more trading days for the 444 one-bar securities, 15 for the 26 zero-bar securities |
| stochastic_d_14 | momentum | 16 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 16 bars total: 15 more trading days for the 444 one-bar securities, 16 for the 26 zero-bar securities |
| stochastic_k_14 | momentum | 14 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 14 bars total: 13 more trading days for the 444 one-bar securities, 14 for the 26 zero-bar securities |
| williams_r_14 | momentum | 14 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 14 bars total: 13 more trading days for the 444 one-bar securities, 14 for the 26 zero-bar securities |
| drawdown | risk | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| es95_hist | risk | 251 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 251 bars total: 250 more trading days for the 444 one-bar securities, 251 for the 26 zero-bar securities |
| max_drawdown | risk | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| var95_hist | risk | 251 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 251 bars total: 250 more trading days for the 444 one-bar securities, 251 for the 26 zero-bar securities |
| adx_14 | trend | 27 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 27 bars total: 26 more trading days for the 444 one-bar securities, 27 for the 26 zero-bar securities |
| donchian_lower_20 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| donchian_middle_20 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| donchian_upper_20 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| ema_10 | trend | 10 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 10 bars total: 9 more trading days for the 444 one-bar securities, 10 for the 26 zero-bar securities |
| ema_12 | trend | 12 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 12 bars total: 11 more trading days for the 444 one-bar securities, 12 for the 26 zero-bar securities |
| ema_20 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| ema_200 | trend | 200 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 200 bars total: 199 more trading days for the 444 one-bar securities, 200 for the 26 zero-bar securities |
| ema_26 | trend | 26 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 26 bars total: 25 more trading days for the 444 one-bar securities, 26 for the 26 zero-bar securities |
| ema_5 | trend | 5 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 5 bars total: 4 more trading days for the 444 one-bar securities, 5 for the 26 zero-bar securities |
| ema_50 | trend | 50 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 50 bars total: 49 more trading days for the 444 one-bar securities, 50 for the 26 zero-bar securities |
| fib_236 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| fib_382 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| fib_500 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| fib_618 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| fib_786 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| ichimoku_chikou | trend | 26 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 26 bars total: 25 more trading days for the 444 one-bar securities, 26 for the 26 zero-bar securities |
| ichimoku_kijun_26 | trend | 26 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 26 bars total: 25 more trading days for the 444 one-bar securities, 26 for the 26 zero-bar securities |
| ichimoku_senkou_a | trend | 26 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 26 bars total: 25 more trading days for the 444 one-bar securities, 26 for the 26 zero-bar securities |
| ichimoku_senkou_b | trend | 52 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 52 bars total: 51 more trading days for the 444 one-bar securities, 52 for the 26 zero-bar securities |
| ichimoku_tenkan_9 | trend | 9 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 9 bars total: 8 more trading days for the 444 one-bar securities, 9 for the 26 zero-bar securities |
| keltner_lower_20 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| keltner_middle_20 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| keltner_upper_20 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| macd_histogram | trend | 34 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 34 bars total: 33 more trading days for the 444 one-bar securities, 34 for the 26 zero-bar securities |
| macd_line | trend | 26 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 26 bars total: 25 more trading days for the 444 one-bar securities, 26 for the 26 zero-bar securities |
| macd_signal | trend | 34 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 34 bars total: 33 more trading days for the 444 one-bar securities, 34 for the 26 zero-bar securities |
| parabolic_sar | trend | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| pivot_p | trend | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| pivot_r1 | trend | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| pivot_r2 | trend | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| pivot_s1 | trend | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| pivot_s2 | trend | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| sma_10 | trend | 10 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 10 bars total: 9 more trading days for the 444 one-bar securities, 10 for the 26 zero-bar securities |
| sma_100 | trend | 100 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 100 bars total: 99 more trading days for the 444 one-bar securities, 100 for the 26 zero-bar securities |
| sma_20 | trend | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| sma_200 | trend | 200 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 200 bars total: 199 more trading days for the 444 one-bar securities, 200 for the 26 zero-bar securities |
| sma_5 | trend | 5 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 5 bars total: 4 more trading days for the 444 one-bar securities, 5 for the 26 zero-bar securities |
| sma_50 | trend | 50 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 50 bars total: 49 more trading days for the 444 one-bar securities, 50 for the 26 zero-bar securities |
| atr_14 | volatility | 14 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 14 bars total: 13 more trading days for the 444 one-bar securities, 14 for the 26 zero-bar securities |
| bollinger_lower_20 | volatility | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| bollinger_middle_20 | volatility | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| bollinger_upper_20 | volatility | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| volatility_20 | volatility | 21 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 21 bars total: 20 more trading days for the 444 one-bar securities, 21 for the 26 zero-bar securities |
| volatility_ann_20 | volatility | 21 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 21 bars total: 20 more trading days for the 444 one-bar securities, 21 for the 26 zero-bar securities |
| ad_line | volume | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| obv | volume | 2 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 2 bars total: 1 more trading days for the 444 one-bar securities, 2 for the 26 zero-bar securities |
| relative_volume_20 | volume | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |
| volume_sma_20 | volume | 20 | 0 | 470 | insufficient_warmup (444), missing_data (26) | 20 bars total: 19 more trading days for the 444 one-bar securities, 20 for the 26 zero-bar securities |

## What the data DOES support today (and only this)

- The deterministic framework itself, validated on synthetic
  multi-day series (see test_report.md).
- The coverage verdicts, the run/error records, the read-only
  APIs with transparent explanations, and immutability
  enforcement.
- No indicator table, chart, or signal may be presented as if
  values existed.

## Additional limitations (beyond warm-up)

- Weekly/monthly aggregated indicators additionally need a
  validated trading calendar before any aggregated period can
  be called complete (all aggregated periods are partial).
- Regime features additionally need calculable indicator values
  first, then versioned threshold activation.
- Signal events additionally need activated rules with
  evaluators plus calculable inputs.
- Adjusted indicators need a validated corporate-action
  methodology (none exists today).
- Scope: Main Board / Normal Counter only (470 securities).
  GEM (5) and Non-Compliant (93) are NOT captured; KSE-100
  completeness is NOT established; all prices are UNVERIFIED
  single-source; no VERIFIED or full-market claim is made.
- Terms basis: written permission requested 2026-11-04 16:58 PKT;
  the reply was reported then permanently deleted; the Phase 5
  commit landed on the user's explicit override and the user
  is handling the permission side later. Terms are NOT cleared;
  Phase 6 sends no email to PSX and collects no new external data.
