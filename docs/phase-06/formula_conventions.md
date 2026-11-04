# Phase 6 — Formula conventions

Single source of truth: backend/app/services/technical_indicators/
conventions.py (registry) and formulas.py (implementation). This
document explains every convention choice so a reviewer can check
the code against it without guessing. All prices are unadjusted
closes unless stated. All math is Decimal (precision 28). No
convention is mixed silently: where textbooks differ, the choice
below is the one implemented and tested.

## Seeding rules (the usual silent-mixing trap)

- SMA(n): arithmetic mean of the last n closes. First value at
  index n-1.
- EMA(n): k = 2/(n+1); seed = SMA of the first n closes; then
  EMA_t = close_t*k + EMA_{t-1}*(1-k). First value at index n-1.
  (TA-Lib-style SMA seeding; alternatives that seed with the
  first close are NOT used.)
- Wilder smoothing (RSI, ATR, ADX only — MFI sums flows and is
  not Wilder-smoothed): first average =
  simple mean of the first window values; later averages =
  (prev*(window-1) + current)/window. This is Wilder's original
  smoothing, not a simple average and not an EMA.

## Momentum

- RSI(14): Wilder smoothing of gains/losses over 14 changes
  (needs 15 closes). avg_loss == 0 with avg_gain > 0 -> 100.
  Flat market (both averages zero) -> 50 by documented
  convention: no movement is neutral, not overbought.
- MACD(12,26,9): line = EMA12 - EMA26 (both SMA-seeded); signal
  = EMA9 of the line, seeded by the SMA of the first 9 line
  values; histogram = line - signal. Warm-ups: line 26 closes,
  signal/histogram 34 closes.
- Stochastic %K(14) = 100*(C - lowest low 14)/(highest high 14 -
  lowest low 14); %D = SMA(3) of %K. Warm-ups: %K 14 bars, %D 16.
  Zero high-low range -> undefined (degenerate), never 50 or 0.
- ROC(12) = 100*(C/C_12_ago - 1); Momentum(12) = C - C_12_ago.
  Warm-up 13 closes. Zero reference close -> degenerate.
- Williams %R(14) = -100*(highest high 14 - C)/(highest high 14
  - lowest low 14). Warm-up 14 bars; zero range -> degenerate.
- CCI(20): TP = (H+L+C)/3; CCI = (TP - SMA20(TP)) /
  (0.015 * mean|TP - SMA20(TP)|). Zero mean deviation ->
  undefined, not zero. Warm-up 20 bars.
- MFI(14): typical price and volume; flows are summed over the
  window (no Wilder smoothing — MFI is not a Wilder-smoothed
  indicator); flows start at bar 1, so 14 flows need 15 bars.
  Zero negative flow -> 100; zero total flow -> undefined.

## Volatility and risk (historical only, never predictive)

- Bollinger(20, 2): middle = SMA20; band = POPULATION standard
  deviation of the same 20 closes (population, not sample — the
  standard Bollinger choice); upper/lower = middle +/- 2*std.
- ATR(14): true range with TR_0 = H_0 - L_0 (no prior close);
  Wilder smoothing. Warm-up 14 bars.
- Rolling volatility(20): population std of the last 20 daily
  simple returns; annualized = daily * sqrt(252). 252 is a
  documented trading-day assumption, NOT a measured PSX
  calendar. Warm-up 21 closes.
- Drawdown: (C - running max C)/running max C; max drawdown is
  its minimum. A single close gives a degenerate 0, so >= 2
  closes are required.
- Historical VaR95 / ES95: 250-return window (251 closes),
  nearest-rank 5th percentile: rank = ceil(0.05 * n), VaR = the
  rank-th worst return (negated); ES = mean of the worst `rank`
  returns, negated. With ties at the threshold, returns equal to
  VaR beyond the rank are excluded — the rank rule, stated
  precisely, is the definition. Shorter windows give unstable
  tail estimates, so the framework refuses below 250 returns
  rather than publishing a thin estimate. Both are labelled
  historical.

## Volume (volume is never automatically buying pressure)

- Volume SMA(20): mean of the last 20 volumes.
- Relative volume = volume / volume SMA(20). A value above 1
  means higher-than-average volume, nothing more.
- OBV: starts at 0 on the first bar; adds volume on up closes,
  subtracts on down closes, unchanged on equal closes. Needs
  >= 2 bars (no prior close on bar 0).
- Accumulation/Distribution: MFM = ((C-L)-(H-C))/(H-L), or 0
  when H == L; MFV = MFM * volume; AD = cumulative MFV. Needs
  >= 2 bars (a one-bar line is degenerate).

## Trend structure

- ADX(14): Wilder-smoothed TR, +DM, -DM, +DI/-DI, DX =
  100*|+DI - -DI|/(+DI + -DI) (DX = 0 when both DIs are 0, i.e.
  no directional movement, and also 0 when smoothed TR is 0,
  i.e. no price range at all — both are "no direction to
  measure", not a computed zero); ADX seed = mean of the first
  14 DX values. First ADX at bar 26 -> warm-up 27 bars.
- Parabolic SAR: AF starts 0.02, step 0.02, cap 0.20; trend from
  the first two closes (up iff close[1] > close[0], else down);
  SAR never crosses the prior two bars' extremes (standard SAR
  rule); on reversal SAR becomes the prior extreme. Returned SAR
  is the stop computed through the last bar (it applies to the
  next bar). Warm-up 2 bars.
- Ichimoku: Tenkan(9), Kijun(26), Senkou A = (Tenkan+Kijun)/2,
  Senkou B = (max high 52 + min low 52)/2, Chikou = close.
  Chikou's warm-up is 26 bars by conservative convention
  (borrowed from Kijun, since Chikou is plotted against the
  26-bar structure), not because the close itself needs 26
  bars — a reviewer should expect warm-up 1 for a bare close,
  and this note is why it is 26 here.
  NO-LOOK-AHEAD STORAGE RULE: Senkou values are stored at their
  computation date, never at the plotted date 26 periods ahead;
  Chikou is stored at its source date, never shifted back.
  Warm-ups: Tenkan 9, Kijun/Senkou A/Chikou 26, Senkou B 52.
- Fibonacci retracement: swing high/low over a 20-bar lookback;
  levels 23.6 / 38.2 / 50 / 61.8 / 78.6 percent of the swing.
  Zero-range swing -> undefined. Warm-up 20 bars.
- Classic floor pivots: computed from the PRIOR bar's HLC
  (P = (H+L+C)/3; R1 = 2P-L; S1 = 2P-H; R2 = P+(H-L);
  S2 = P-(H-L)). Same-bar HLC would be same-day, not prior
  period, so warm-up is 2 bars.
- Donchian(20): upper = max high 20, lower = min low 20, middle
  = (upper+lower)/2. Warm-up 20 bars.
- Keltner(20, 2): middle = EMA20; band = 2 * ATR(10) (Wilder).
  Warm-up 20 bars.

## Returns

- Daily return = close / previous_close - 1, using the stored
  previous_close column. A blank previous_close is missing data,
  never zero and never the close itself. A zero previous_close
  is degenerate.
- Return series for volatility/VaR use consecutive stored
  closes (close_t / close_{t-1} - 1), never the previous_close
  column — the two must not be conflated.

## Worked example (verifiable by hand)

Closes [10, 11, 12, 13, 14]: SMA(5) = 12; SMA(3) = 13;
EMA(3) with k = 0.5 and seed SMA(10,11,12) = 11 gives 12, then 13.
MACD(2,3,2) on closes [10..15] gives line 0.5, signal 0.5,
histogram 0 (the EMA gap on a +1/day ramp is constant). These
are encoded as tests, not just prose.
