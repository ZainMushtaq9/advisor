"""Indicator registry: the single source of truth for Phase 6.

Every indicator the framework knows is registered here with its
category, formula text, formula version, default parameters, warm-up
requirement (minimum bars, counted in the indicator's own input
series), and the pure function in ``formulas.py`` that computes it.
Warm-up counts are part of the convention, not an implementation
detail: changing one changes what the framework claims is
calculable, so warm-ups live here, in one auditable place.

Conventions fixed here (see docs/phase-06/formula_conventions.md
for the full reasoning and worked examples):

- SMA(n): arithmetic mean of the last n closes. First value uses
  closes[0..n-1]; warm-up = n closes.
- EMA(n): smoothing k = 2/(n+1); seed = SMA of the first n closes;
  EMA_t = close_t*k + EMA_{t-1}*(1-k). Warm-up = n closes.
- RSI(14): Wilder smoothing. First average gain/loss = simple mean
  of the first 14 changes; later averages = (prev*13 + current)/14.
  avg_loss == 0 and avg_gain > 0 -> 100; both zero -> 50 (flat
  market, documented edge). Warm-up = 15 closes (14 changes).
- MACD(12,26,9): line = EMA12 - EMA26; signal = EMA9 of the line
  (seeded by the SMA of the first 9 line values); histogram =
  line - signal. Warm-up: line 26 closes, signal/histogram 34.
- Stochastic %K(14) = 100*(C - lowest low 14)/(highest high 14 -
  lowest low 14); %D = SMA(3) of %K. Warm-up: %K 14 bars, %D 16.
- ROC(12) = 100*(C / C_12_ago - 1); Momentum(12) = C - C_12_ago.
  Warm-up = 13 closes.
- Williams %R(14) = -100*(highest high 14 - C)/(highest high 14 -
  lowest low 14). Warm-up = 14 bars.
- CCI(20): TP = (H+L+C)/3; CCI = (TP - SMA20(TP)) / (0.015 * mean
  |TP - SMA20(TP)|). Zero mean deviation -> undefined, not zero.
  Warm-up = 20 bars.
- Bollinger(20, 2): middle = SMA20; band = population standard
  deviation of the same 20 closes (population, not sample);
  upper/lower = middle +/- 2*std. Warm-up = 20 closes.
- ATR(14): Wilder smoothing of true range. TR_0 = H_0 - L_0 (no
  prior close); TR_t = max(H-L, |H - prevC|, |L - prevC|). First
  ATR = mean of the first 14 TRs; later = Wilder smoothing.
  Warm-up = 14 bars.
- Rolling volatility(20): population std of the last 20 daily
  simple returns; annualized = daily * sqrt(252) (252 = documented
  trading-day assumption, not a measured PSX calendar). Warm-up =
  21 closes (20 returns).
- Drawdown / max drawdown: running maximum of closes; drawdown_t =
  (C_t - max_so_far) / max_so_far. A single close gives a
  degenerate 0, so the framework requires >= 2 closes.
- Historical VaR95 / ES95: 250-return window (251 closes). Below
  that, tail estimates are unstable, so the framework refuses
  rather than publishing a thin estimate.
- Volume SMA(20): mean of the last 20 volumes. Relative volume =
  volume / volume SMA(20). Warm-up = 20 bars.
- OBV: cumulative; OBV_0 = 0; OBV_t = OBV_{t-1} + volume if C_t >
  C_{t-1}, - volume if C_t < C_{t-1}, unchanged if equal. Needs
  >= 2 bars (no prior close on bar 0).
- Accumulation/Distribution: MFM = ((C-L)-(H-C))/(H-L), or 0 when
  H == L; MFV = MFM * volume; AD = cumulative MFV. Needs >= 2
  bars (a one-bar line is degenerate).
- MFI(14): typical price, money flow, positive/negative flow
  over 14 flows (flows start at bar 1). Warm-up = 15 bars.
- ADX(14): Wilder smoothing of TR, +DM, -DM; +DI/-DI; DX =
  100*|+DI - -DI|/(+DI + -DI); ADX seed = mean of the first 14 DX
  values. First ADX at bar 26 -> warm-up 27 bars.
- Parabolic SAR: AF starts 0.02, step 0.02, cap 0.20; trend from
  the first two closes; SAR never crosses the prior two bars'
  extremes (standard SAR rule). Warm-up = 2 bars.
- Ichimoku: Tenkan(9) = (max high 9 + min low 9)/2; Kijun(26)
  likewise; Senkou A = (Tenkan + Kijun)/2; Senkou B = (max high
  52 + min low 52)/2; Chikou = close. NO-LOOK-AHEAD STORAGE RULE:
  Senkou values are stored at their computation date, never at
  the plotted date 26 periods ahead; Chikou is stored at its
  source date, never shifted back. Warm-up: Tenkan 9, Kijun /
  Senkou A / Chikou 26, Senkou B 52 bars.
- Fibonacci retracement: swing high/low over a 20-bar lookback;
  the five intermediate levels 23.6 / 38.2 / 50 / 61.8 / 78.6
  percent of the swing (0% and 100% are the swing endpoints
  themselves, not separate outputs). Zero-range swing ->
  undefined. Warm-up = 20 bars.
- Classic floor pivots: computed from the PRIOR bar's HLC
  (P = (H+L+C)/3; R1 = 2P - L; S1 = 2P - H; R2 = P + (H-L);
  S2 = P - (H-L)). Same-bar HLC would be same-day, not prior
  period, so warm-up = 2 bars.
- Donchian(20): upper = max high 20, lower = min low 20, middle
  = (upper + lower)/2. Warm-up = 20 bars.
- Keltner(20, 2): middle = EMA20; ATR(10) with Wilder smoothing;
  upper/lower = middle +/- 2*ATR10. Warm-up = 20 bars.
- Daily return: C / previous_close - 1, using the stored
  previous_close column. A blank previous_close is missing data,
  never zero or the close itself. Warm-up: none beyond the input
  being present.
"""

from __future__ import annotations

FORMULA_VERSION = "1.0"


class IndicatorSpec:
    """One registered indicator output."""

    def __init__(
        self,
        key: str,
        category: str,
        formula_text: str,
        warmup_bars: int,
        compute: str,
        parameters: dict | None = None,
        requires: str = "bars",
    ) -> None:
        self.key = key
        self.category = category
        self.formula_text = formula_text
        self.formula_version = FORMULA_VERSION
        self.warmup_bars = warmup_bars
        self.compute = compute
        self.parameters = parameters or {}
        self.requires = requires  # 'bars' (OHLCV) or 'closes'

    def default_parameters(self) -> dict:
        return dict(self.parameters)


def _sma(n: int) -> IndicatorSpec:
    return IndicatorSpec(
        key=f"sma_{n}",
        category="trend",
        formula_text=f"Arithmetic mean of the last {n} closes.",
        warmup_bars=n,
        compute="sma",
        parameters={"window": n},
        requires="closes",
    )


def _ema(n: int) -> IndicatorSpec:
    return IndicatorSpec(
        key=f"ema_{n}",
        category="trend",
        formula_text=(
            f"EMA with k = 2/({n}+1), seeded by the SMA of the first "
            f"{n} closes."
        ),
        warmup_bars=n,
        compute="ema",
        parameters={"window": n},
        requires="closes",
    )


INDICATORS: list[IndicatorSpec] = [
    # Trend: moving averages.
    _sma(5),
    _sma(10),
    _sma(20),
    _sma(50),
    _sma(100),
    _sma(200),
    _ema(5),
    _ema(10),
    _ema(12),
    _ema(20),
    _ema(26),
    _ema(50),
    _ema(200),
    # Trend: MACD components.
    IndicatorSpec(
        key="macd_line",
        category="trend",
        formula_text="EMA(12) - EMA(26), both SMA-seeded.",
        warmup_bars=26,
        compute="macd",
        parameters={"fast": 12, "slow": 26, "signal": 9},
        requires="closes",
    ),
    IndicatorSpec(
        key="macd_signal",
        category="trend",
        formula_text="EMA(9) of the MACD line, seeded by the SMA of the "
        "first 9 line values.",
        warmup_bars=34,
        compute="macd",
        parameters={"fast": 12, "slow": 26, "signal": 9},
        requires="closes",
    ),
    IndicatorSpec(
        key="macd_histogram",
        category="trend",
        formula_text="MACD line - MACD signal.",
        warmup_bars=34,
        compute="macd",
        parameters={"fast": 12, "slow": 26, "signal": 9},
        requires="closes",
    ),
    # Momentum.
    IndicatorSpec(
        key="rsi_14",
        category="momentum",
        formula_text="Wilder-smoothed RSI(14); flat market (no gains or "
        "losses) reads 50 by documented convention.",
        warmup_bars=15,
        compute="rsi",
        parameters={"window": 14},
        requires="closes",
    ),
    IndicatorSpec(
        key="roc_12",
        category="momentum",
        formula_text="100 * (close / close_12_ago - 1).",
        warmup_bars=13,
        compute="roc",
        parameters={"window": 12},
        requires="closes",
    ),
    IndicatorSpec(
        key="momentum_12",
        category="momentum",
        formula_text="close - close_12_ago.",
        warmup_bars=13,
        compute="momentum",
        parameters={"window": 12},
        requires="closes",
    ),
    IndicatorSpec(
        key="stochastic_k_14",
        category="momentum",
        formula_text="100 * (close - lowest low 14) / (highest high 14 - "
        "lowest low 14).",
        warmup_bars=14,
        compute="stochastic",
        parameters={"window": 14, "smooth": 3},
    ),
    IndicatorSpec(
        key="stochastic_d_14",
        category="momentum",
        formula_text="SMA(3) of stochastic %K(14).",
        warmup_bars=16,
        compute="stochastic",
        parameters={"window": 14, "smooth": 3},
    ),
    IndicatorSpec(
        key="williams_r_14",
        category="momentum",
        formula_text="-100 * (highest high 14 - close) / (highest high "
        "14 - lowest low 14).",
        warmup_bars=14,
        compute="williams_r",
        parameters={"window": 14},
    ),
    IndicatorSpec(
        key="cci_20",
        category="momentum",
        formula_text="CCI(20) on typical price (H+L+C)/3 with 0.015 "
        "constant; zero mean deviation is undefined, not zero.",
        warmup_bars=20,
        compute="cci",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="mfi_14",
        category="momentum",
        formula_text="Money Flow Index(14) on typical price and volume; "
        "zero negative flow reads 100, zero total flow undefined.",
        warmup_bars=15,
        compute="mfi",
        parameters={"window": 14},
    ),
    # Volatility.
    IndicatorSpec(
        key="bollinger_middle_20",
        category="volatility",
        formula_text="SMA(20) of closes (Bollinger middle band).",
        warmup_bars=20,
        compute="bollinger",
        parameters={"window": 20, "std_dev": 2},
        requires="closes",
    ),
    IndicatorSpec(
        key="bollinger_upper_20",
        category="volatility",
        formula_text="Middle + 2 * population std of the same 20 closes.",
        warmup_bars=20,
        compute="bollinger",
        parameters={"window": 20, "std_dev": 2},
        requires="closes",
    ),
    IndicatorSpec(
        key="bollinger_lower_20",
        category="volatility",
        formula_text="Middle - 2 * population std of the same 20 closes.",
        warmup_bars=20,
        compute="bollinger",
        parameters={"window": 20, "std_dev": 2},
        requires="closes",
    ),
    IndicatorSpec(
        key="atr_14",
        category="volatility",
        formula_text="Wilder-smoothed ATR(14) of true range; first true "
        "range is high - low (no prior close).",
        warmup_bars=14,
        compute="atr",
        parameters={"window": 14},
    ),
    IndicatorSpec(
        key="volatility_20",
        category="volatility",
        formula_text="Population std of the last 20 daily simple returns.",
        warmup_bars=21,
        compute="volatility",
        parameters={"window": 20},
        requires="closes",
    ),
    IndicatorSpec(
        key="volatility_ann_20",
        category="volatility",
        formula_text="Daily rolling volatility(20) * sqrt(252); 252 is a "
        "documented trading-day assumption, not a measured calendar.",
        warmup_bars=21,
        compute="volatility_ann",
        parameters={"window": 20},
        requires="closes",
    ),
    # Risk (historical, never predictive).
    IndicatorSpec(
        key="drawdown",
        category="risk",
        formula_text="(close - running maximum close) / running maximum "
        "close. Requires >= 2 closes; a single close is degenerate.",
        warmup_bars=2,
        compute="drawdown",
        parameters={},
        requires="closes",
    ),
    IndicatorSpec(
        key="max_drawdown",
        category="risk",
        formula_text="Minimum drawdown over the observed history. "
        "Requires >= 2 closes.",
        warmup_bars=2,
        compute="max_drawdown",
        parameters={},
        requires="closes",
    ),
    IndicatorSpec(
        key="var95_hist",
        category="risk",
        formula_text="Historical 95% Value-at-Risk over 250 daily simple "
        "returns (5th percentile loss, reported as a positive "
        "number). Historical only, never predictive.",
        warmup_bars=251,
        compute="var_hist",
        parameters={"window": 250, "confidence": 0.95},
        requires="closes",
    ),
    IndicatorSpec(
        key="es95_hist",
        category="risk",
        formula_text="Historical 95% Expected Shortfall: mean loss beyond "
        "the 95% VaR over 250 daily simple returns. Historical only.",
        warmup_bars=251,
        compute="es_hist",
        parameters={"window": 250, "confidence": 0.95},
        requires="closes",
    ),
    # Volume.
    IndicatorSpec(
        key="volume_sma_20",
        category="volume",
        formula_text="Arithmetic mean of the last 20 volumes.",
        warmup_bars=20,
        compute="volume_sma",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="relative_volume_20",
        category="volume",
        formula_text="Volume / volume SMA(20). A value above 1 is higher "
        "volume than the average, never by itself buying pressure.",
        warmup_bars=20,
        compute="relative_volume",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="obv",
        category="volume",
        formula_text="Cumulative on-balance volume from close direction; "
        "starts at 0 on the first bar. Requires >= 2 bars.",
        warmup_bars=2,
        compute="obv",
        parameters={},
    ),
    IndicatorSpec(
        key="ad_line",
        category="volume",
        formula_text="Cumulative money-flow volume from the money-flow "
        "multiplier. Requires >= 2 bars.",
        warmup_bars=2,
        compute="ad_line",
        parameters={},
    ),
    # Trend strength / structure.
    IndicatorSpec(
        key="adx_14",
        category="trend",
        formula_text="Wilder ADX(14): smoothed TR, +DM, -DM, +DI/-DI, DX, "
        "then Wilder-smoothed DX. First ADX at bar 26 (27 bars).",
        warmup_bars=27,
        compute="adx",
        parameters={"window": 14},
    ),
    IndicatorSpec(
        key="parabolic_sar",
        category="trend",
        formula_text="Parabolic SAR, AF step 0.02, cap 0.20, trend from "
        "the first two closes, SAR never crossing the prior two "
        "bars' extremes. Requires >= 2 bars.",
        warmup_bars=2,
        compute="parabolic_sar",
        parameters={"af_step": 0.02, "af_max": 0.20},
    ),
    IndicatorSpec(
        key="ichimoku_tenkan_9",
        category="trend",
        formula_text="(max high 9 + min low 9) / 2.",
        warmup_bars=9,
        compute="ichimoku",
        parameters={"tenkan": 9, "kijun": 26, "senkou_b": 52},
    ),
    IndicatorSpec(
        key="ichimoku_kijun_26",
        category="trend",
        formula_text="(max high 26 + min low 26) / 2.",
        warmup_bars=26,
        compute="ichimoku",
        parameters={"tenkan": 9, "kijun": 26, "senkou_b": 52},
    ),
    IndicatorSpec(
        key="ichimoku_senkou_a",
        category="trend",
        formula_text="(Tenkan + Kijun) / 2, stored at its computation "
        "date, never at the plotted date 26 periods ahead.",
        warmup_bars=26,
        compute="ichimoku",
        parameters={"tenkan": 9, "kijun": 26, "senkou_b": 52},
    ),
    IndicatorSpec(
        key="ichimoku_senkou_b",
        category="trend",
        formula_text="(max high 52 + min low 52) / 2, stored at its "
        "computation date, never at the plotted date ahead.",
        warmup_bars=52,
        compute="ichimoku",
        parameters={"tenkan": 9, "kijun": 26, "senkou_b": 52},
    ),
    IndicatorSpec(
        key="ichimoku_chikou",
        category="trend",
        formula_text="Lagging span: the close itself, stored at its "
        "source date, never shifted back. Presentation only.",
        warmup_bars=26,
        compute="ichimoku",
        parameters={"tenkan": 9, "kijun": 26, "senkou_b": 52},
    ),
    IndicatorSpec(
        key="fib_236",
        category="trend",
        formula_text="Swing low + 23.6% of the 20-bar swing range.",
        warmup_bars=20,
        compute="fibonacci",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="fib_382",
        category="trend",
        formula_text="Swing low + 38.2% of the 20-bar swing range.",
        warmup_bars=20,
        compute="fibonacci",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="fib_500",
        category="trend",
        formula_text="Swing low + 50% of the 20-bar swing range.",
        warmup_bars=20,
        compute="fibonacci",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="fib_618",
        category="trend",
        formula_text="Swing low + 61.8% of the 20-bar swing range.",
        warmup_bars=20,
        compute="fibonacci",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="fib_786",
        category="trend",
        formula_text="Swing low + 78.6% of the 20-bar swing range.",
        warmup_bars=20,
        compute="fibonacci",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="pivot_p",
        category="trend",
        formula_text="Classic floor pivot from the PRIOR bar: "
        "(H + L + C) / 3.",
        warmup_bars=2,
        compute="pivots",
        parameters={},
    ),
    IndicatorSpec(
        key="pivot_r1",
        category="trend",
        formula_text="2 * P - prior low.",
        warmup_bars=2,
        compute="pivots",
        parameters={},
    ),
    IndicatorSpec(
        key="pivot_s1",
        category="trend",
        formula_text="2 * P - prior high.",
        warmup_bars=2,
        compute="pivots",
        parameters={},
    ),
    IndicatorSpec(
        key="pivot_r2",
        category="trend",
        formula_text="P + (prior high - prior low).",
        warmup_bars=2,
        compute="pivots",
        parameters={},
    ),
    IndicatorSpec(
        key="pivot_s2",
        category="trend",
        formula_text="P - (prior high - prior low).",
        warmup_bars=2,
        compute="pivots",
        parameters={},
    ),
    IndicatorSpec(
        key="donchian_upper_20",
        category="trend",
        formula_text="Max high of the last 20 bars.",
        warmup_bars=20,
        compute="donchian",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="donchian_middle_20",
        category="trend",
        formula_text="(Donchian upper + lower) / 2.",
        warmup_bars=20,
        compute="donchian",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="donchian_lower_20",
        category="trend",
        formula_text="Min low of the last 20 bars.",
        warmup_bars=20,
        compute="donchian",
        parameters={"window": 20},
    ),
    IndicatorSpec(
        key="keltner_middle_20",
        category="trend",
        formula_text="EMA(20) of closes (Keltner middle line).",
        warmup_bars=20,
        compute="keltner",
        parameters={"window": 20, "atr_window": 10, "multiplier": 2},
        requires="closes",
    ),
    IndicatorSpec(
        key="keltner_upper_20",
        category="trend",
        formula_text="EMA(20) + 2 * ATR(10) (Wilder).",
        warmup_bars=20,
        compute="keltner",
        parameters={"window": 20, "atr_window": 10, "multiplier": 2},
    ),
    IndicatorSpec(
        key="keltner_lower_20",
        category="trend",
        formula_text="EMA(20) - 2 * ATR(10) (Wilder).",
        warmup_bars=20,
        compute="keltner",
        parameters={"window": 20, "atr_window": 10, "multiplier": 2},
    ),
    # Return (input-dependent, not window-dependent).
    IndicatorSpec(
        key="daily_return",
        category="momentum",
        formula_text="close / previous_close - 1, using the stored "
        "previous_close column. A blank previous_close is missing "
        "data, never zero or the close itself.",
        warmup_bars=1,
        compute="daily_return",
        parameters={},
    ),
]

BY_KEY = {spec.key: spec for spec in INDICATORS}

# Multi-output computations: one formulas.py function returns a dict;
# each component key maps to one dict field.
COMPONENT_FIELD = {
    "macd_line": "line",
    "macd_signal": "signal",
    "macd_histogram": "histogram",
    "bollinger_middle_20": "middle",
    "bollinger_upper_20": "upper",
    "bollinger_lower_20": "lower",
    "stochastic_k_14": "k",
    "stochastic_d_14": "d",
    "ichimoku_tenkan_9": "tenkan",
    "ichimoku_kijun_26": "kijun",
    "ichimoku_senkou_a": "senkou_a",
    "ichimoku_senkou_b": "senkou_b",
    "ichimoku_chikou": "chikou",
    "fib_236": "fib_236",
    "fib_382": "fib_382",
    "fib_500": "fib_500",
    "fib_618": "fib_618",
    "fib_786": "fib_786",
    "pivot_p": "p",
    "pivot_r1": "r1",
    "pivot_s1": "s1",
    "pivot_r2": "r2",
    "pivot_s2": "s2",
    "donchian_upper_20": "upper",
    "donchian_middle_20": "middle",
    "donchian_lower_20": "lower",
    "keltner_middle_20": "middle",
    "keltner_upper_20": "upper",
    "keltner_lower_20": "lower",
}
