"""Pure indicator formulas (Phase 6).

Every function here is deterministic and side-effect free: it takes
an explicit list of bars and returns a Decimal (or a dict of
Decimals), or raises InsufficientData. No function reads the
database, the network, or the clock, and no function fills a gap:
a missing close/high/low/volume is missing data, never zero.

A "bar" is a dict with keys: date, open, high, low, close, volume,
previous_close. Prices are Decimal (or int); volumes are int. A
function only ever uses bars it was given, so no-look-ahead is a
property of the caller slicing the series to the as-of date — see
coverage.py, which enforces that slice, and the no-look-ahead test.

Conventions are fixed in conventions.py and documented in
docs/phase-06/formula_conventions.md. This module implements them
exactly; where a textbook convention is ambiguous (flat-market RSI,
zero-range Stochastic, zero-deviation CCI), the documented choice
is implemented and tested, not silently picked per call.
"""

from __future__ import annotations

from decimal import Decimal, getcontext

getcontext().prec = 28

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


class InsufficientData(Exception):
    """Raised when an indicator cannot be computed honestly.

    ``code`` uses the Phase 3 error vocabulary: 'insufficient_warmup'
    (fewer bars than the convention requires), 'missing_data' (a
    needed input is absent), 'degenerate_input' (inputs exist but
    make the formula undefined, e.g. a zero range).
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _dec(value: object, name: str) -> Decimal:
    if value is None:
        raise InsufficientData("missing_data", f"{name} is missing")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    raise InsufficientData("missing_data", f"{name} has an unusable value")


def _closes(bars: list[dict]) -> list[Decimal]:
    return [_dec(b.get("close"), "close") for b in bars]


def _check_warmup(bars: list[dict], needed: int, key: str) -> None:
    if len(bars) < needed:
        raise InsufficientData(
            "insufficient_warmup",
            f"{key} needs {needed} bars, only {len(bars)} available",
        )


def _mean(values: list[Decimal]) -> Decimal:
    return sum(values) / Decimal(len(values))


def _pop_std(values: list[Decimal]) -> Decimal:
    mean = _mean(values)
    variance = sum((v - mean) ** 2 for v in values) / Decimal(len(values))
    return variance.sqrt()


def sma_series(closes: list[Decimal], window: int) -> list[Decimal]:
    """SMA values, first at index window-1."""
    if len(closes) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"SMA({window}) needs {window} closes, got {len(closes)}",
        )
    return [
        _mean(closes[i - window + 1 : i + 1]) for i in range(window - 1, len(closes))
    ]


def ema_series(closes: list[Decimal], window: int) -> list[Decimal]:
    """EMA values with SMA seed; first at index window-1."""
    if len(closes) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"EMA({window}) needs {window} closes, got {len(closes)}",
        )
    k = Decimal(2) / Decimal(window + 1)
    out = [_mean(closes[:window])]
    for close in closes[window:]:
        out.append(close * k + out[-1] * (ONE - k))
    return out


def wilder_series(values: list[Decimal], window: int) -> list[Decimal]:
    """Wilder-smoothed series; first at index window-1 (SMA seed)."""
    if len(values) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"Wilder({window}) needs {window} values, got {len(values)}",
        )
    out = [_mean(values[:window])]
    for value in values[window:]:
        out.append((out[-1] * Decimal(window - 1) + value) / Decimal(window))
    return out


def _true_ranges(bars: list[dict]) -> list[Decimal]:
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    closes = _closes(bars)
    trs = [highs[0] - lows[0]]
    for i in range(1, len(bars)):
        trs.append(
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        )
    return trs


def _atr_series(bars: list[dict], window: int) -> list[Decimal]:
    return wilder_series(_true_ranges(bars), window)


def sma(bars: list[dict], window: int) -> Decimal:
    return sma_series(_closes(bars), window)[-1]


def ema(bars: list[dict], window: int) -> Decimal:
    return ema_series(_closes(bars), window)[-1]


def macd(bars: list[dict], fast: int, slow: int, signal: int) -> dict:
    closes = _closes(bars)
    if len(closes) < slow:
        raise InsufficientData(
            "insufficient_warmup", f"MACD line needs {slow} closes, got {len(closes)}"
        )
    fast_e = ema_series(closes, fast)
    slow_e = ema_series(closes, slow)
    # Align: slow series starts at index slow-1; fast series at fast-1.
    line = [f - s for f, s in zip(fast_e[slow - fast :], slow_e)]
    if len(line) < signal:
        raise InsufficientData(
            "insufficient_warmup",
            f"MACD signal needs {signal} line values, got {len(line)}",
        )
    sig = ema_series(line, signal)[-1]
    return {"line": line[-1], "signal": sig, "histogram": line[-1] - sig}


def rsi(bars: list[dict], window: int) -> Decimal:
    closes = _closes(bars)
    if len(closes) < window + 1:
        raise InsufficientData(
            "insufficient_warmup",
            f"RSI({window}) needs {window + 1} closes, got {len(closes)}",
        )
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [c if c > 0 else ZERO for c in changes]
    losses = [-c if c < 0 else ZERO for c in changes]
    avg_gain = _mean(gains[:window])
    avg_loss = _mean(losses[:window])
    for g, lo in zip(gains[window:], losses[window:]):
        avg_gain = (avg_gain * Decimal(window - 1) + g) / Decimal(window)
        avg_loss = (avg_loss * Decimal(window - 1) + lo) / Decimal(window)
    if avg_loss == 0:
        return HUNDRED if avg_gain > 0 else Decimal("50")
    rs = avg_gain / avg_loss
    return HUNDRED - HUNDRED / (ONE + rs)


def roc(bars: list[dict], window: int) -> Decimal:
    closes = _closes(bars)
    if len(closes) < window + 1:
        raise InsufficientData(
            "insufficient_warmup",
            f"ROC({window}) needs {window + 1} closes, got {len(closes)}",
        )
    ago = closes[-1 - window]
    if ago == 0:
        raise InsufficientData("degenerate_input", "ROC reference close is zero")
    return HUNDRED * (closes[-1] / ago - ONE)


def momentum(bars: list[dict], window: int) -> Decimal:
    closes = _closes(bars)
    if len(closes) < window + 1:
        raise InsufficientData(
            "insufficient_warmup",
            f"Momentum({window}) needs {window + 1} closes, got {len(closes)}",
        )
    return closes[-1] - closes[-1 - window]


def _stoch_k(
    highs: list[Decimal], lows: list[Decimal], closes: list[Decimal],
    window: int, end: int,
) -> Decimal:
    """%K for the window ending at index ``end``; degenerate only there.

    Only the windows that feed the returned values matter: %K uses
    the final window, %D uses the last ``smooth`` windows. A flat
    window earlier in history must not veto a clean final window.
    """
    hi = max(highs[end - window + 1 : end + 1])
    lo = min(lows[end - window + 1 : end + 1])
    if hi == lo:
        raise InsufficientData(
            "degenerate_input", "Stochastic window has zero high-low range"
        )
    return HUNDRED * (closes[end] - lo) / (hi - lo)


def stochastic(bars: list[dict], window: int, smooth: int) -> dict:
    if len(bars) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"Stochastic({window}) needs {window} bars, got {len(bars)}",
        )
    if len(bars) < window + smooth - 1:
        raise InsufficientData(
            "insufficient_warmup",
            f"Stochastic %D needs {smooth} %K values, got "
            f"{len(bars) - window + 1}",
        )
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    closes = _closes(bars)
    last = len(bars) - 1
    window_ends = range(last - smooth + 1, last + 1)
    k_values = [_stoch_k(highs, lows, closes, window, i) for i in window_ends]
    return {"k": k_values[-1], "d": _mean(k_values[-smooth:])}


def williams_r(bars: list[dict], window: int) -> Decimal:
    if len(bars) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"Williams %R({window}) needs {window} bars, got {len(bars)}",
        )
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    closes = _closes(bars)
    hi = max(highs[-window:])
    lo = min(lows[-window:])
    if hi == lo:
        raise InsufficientData(
            "degenerate_input", "Williams %R window has zero high-low range"
        )
    return -HUNDRED * (hi - closes[-1]) / (hi - lo)


def cci(bars: list[dict], window: int) -> Decimal:
    if len(bars) < window:
        raise InsufficientData(
            "insufficient_warmup", f"CCI({window}) needs {window} bars, got {len(bars)}"
        )
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    closes = _closes(bars)
    tps = [(h + lo + c) / Decimal(3) for h, lo, c in zip(highs, lows, closes)]
    window_tps = tps[-window:]
    sma_tp = _mean(window_tps)
    md = _mean([abs(t - sma_tp) for t in window_tps])
    if md == 0:
        raise InsufficientData(
            "degenerate_input", "CCI mean deviation is zero (flat typical price)"
        )
    return (tps[-1] - sma_tp) / (Decimal("0.015") * md)


def bollinger(bars: list[dict], window: int, std_dev: int) -> dict:
    closes = _closes(bars)
    if len(closes) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"Bollinger({window}) needs {window} closes, got {len(closes)}",
        )
    window_closes = closes[-window:]
    middle = _mean(window_closes)
    std = _pop_std(window_closes)
    mult = Decimal(std_dev)
    return {"middle": middle, "upper": middle + mult * std, "lower": middle - mult * std}


def atr(bars: list[dict], window: int) -> Decimal:
    if len(bars) < window:
        raise InsufficientData(
            "insufficient_warmup", f"ATR({window}) needs {window} bars, got {len(bars)}"
        )
    return _atr_series(bars, window)[-1]


def _simple_returns(closes: list[Decimal]) -> list[Decimal]:
    returns = []
    for i in range(1, len(closes)):
        if closes[i - 1] == 0:
            raise InsufficientData(
                "degenerate_input", "Return reference close is zero"
            )
        returns.append(closes[i] / closes[i - 1] - ONE)
    return returns


def volatility(bars: list[dict], window: int) -> Decimal:
    closes = _closes(bars)
    if len(closes) < window + 1:
        raise InsufficientData(
            "insufficient_warmup",
            f"Volatility({window}) needs {window + 1} closes, got {len(closes)}",
        )
    return _pop_std(_simple_returns(closes)[-window:])


def volatility_ann(bars: list[dict], window: int) -> Decimal:
    return volatility(bars, window) * Decimal(252).sqrt()


def drawdown(bars: list[dict]) -> Decimal:
    closes = _closes(bars)
    if len(closes) < 2:
        raise InsufficientData(
            "insufficient_warmup", "Drawdown needs >= 2 closes (single close is 0)"
        )
    running_max = closes[0]
    current = ZERO
    for close in closes:
        running_max = max(running_max, close)
        if running_max <= 0:
            raise InsufficientData(
                "degenerate_input",
                "Drawdown is undefined when the running maximum is not positive",
            )
        current = (close - running_max) / running_max
    return current


def max_drawdown(bars: list[dict]) -> Decimal:
    closes = _closes(bars)
    if len(closes) < 2:
        raise InsufficientData(
            "insufficient_warmup", "Max drawdown needs >= 2 closes"
        )
    running_max = closes[0]
    worst = ZERO
    for close in closes:
        running_max = max(running_max, close)
        if running_max <= 0:
            raise InsufficientData(
                "degenerate_input",
                "Max drawdown is undefined when the running maximum is not positive",
            )
        worst = min(worst, (close - running_max) / running_max)
    return worst


def _tail_returns(bars: list[dict], window: int) -> list[Decimal]:
    closes = _closes(bars)
    if len(closes) < window + 1:
        raise InsufficientData(
            "insufficient_warmup",
            f"Tail window {window} needs {window + 1} closes, got {len(closes)}",
        )
    return sorted(_simple_returns(closes)[-window:])


def var_hist(bars: list[dict], window: int, confidence: float) -> Decimal:
    ordered = _tail_returns(bars, window)
    # Nearest-rank percentile on ascending returns.
    import math

    rank = max(1, math.ceil((1 - confidence) * len(ordered)))
    return -ordered[rank - 1]


def es_hist(bars: list[dict], window: int, confidence: float) -> Decimal:
    ordered = _tail_returns(bars, window)
    import math

    rank = max(1, math.ceil((1 - confidence) * len(ordered)))
    tail = ordered[:rank]
    return -_mean(tail)


def volume_sma(bars: list[dict], window: int) -> Decimal:
    if len(bars) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"Volume SMA({window}) needs {window} bars, got {len(bars)}",
        )
    volumes = []
    for b in bars[-window:]:
        if b.get("volume") is None:
            raise InsufficientData("missing_data", "volume is missing")
        volumes.append(Decimal(b["volume"]))
    return _mean(volumes)


def relative_volume(bars: list[dict], window: int) -> Decimal:
    avg = volume_sma(bars, window)
    if bars[-1].get("volume") is None:
        raise InsufficientData("missing_data", "volume is missing")
    if avg == 0:
        raise InsufficientData(
            "degenerate_input", "Relative volume average volume is zero"
        )
    return Decimal(bars[-1]["volume"]) / avg


def obv(bars: list[dict]) -> Decimal:
    closes = _closes(bars)
    if len(closes) < 2:
        raise InsufficientData("insufficient_warmup", "OBV needs >= 2 bars")
    total = ZERO
    for i in range(1, len(closes)):
        if bars[i].get("volume") is None:
            raise InsufficientData("missing_data", "volume is missing")
        vol = Decimal(bars[i]["volume"])
        if closes[i] > closes[i - 1]:
            total += vol
        elif closes[i] < closes[i - 1]:
            total -= vol
    return total


def ad_line(bars: list[dict]) -> Decimal:
    if len(bars) < 2:
        raise InsufficientData("insufficient_warmup", "A/D line needs >= 2 bars")
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    closes = _closes(bars)
    total = ZERO
    for i in range(len(bars)):
        if bars[i].get("volume") is None:
            raise InsufficientData("missing_data", "volume is missing")
        if highs[i] == lows[i]:
            mfm = ZERO
        else:
            mfm = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / (
                highs[i] - lows[i]
            )
        total += mfm * Decimal(bars[i]["volume"])
    return total


def mfi(bars: list[dict], window: int) -> Decimal:
    if len(bars) < window + 1:
        raise InsufficientData(
            "insufficient_warmup",
            f"MFI({window}) needs {window + 1} bars, got {len(bars)}",
        )
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    closes = _closes(bars)
    tps = [(h + lo + c) / Decimal(3) for h, lo, c in zip(highs, lows, closes)]
    pos = ZERO
    neg = ZERO
    for i in range(len(bars) - window, len(bars)):
        if bars[i].get("volume") is None:
            raise InsufficientData("missing_data", "volume is missing")
        flow = tps[i] * Decimal(bars[i]["volume"])
        if tps[i] > tps[i - 1]:
            pos += flow
        elif tps[i] < tps[i - 1]:
            neg += flow
    if pos == 0 and neg == 0:
        raise InsufficientData("degenerate_input", "MFI has zero total money flow")
    if neg == 0:
        return HUNDRED
    return HUNDRED - HUNDRED / (ONE + pos / neg)


def adx(bars: list[dict], window: int) -> Decimal:
    if len(bars) < 2 * window - 1:
        raise InsufficientData(
            "insufficient_warmup",
            f"ADX({window}) needs {2 * window - 1} bars, got {len(bars)}",
        )
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    trs = _true_ranges(bars)
    plus_dm = [ZERO]
    minus_dm = [ZERO]
    for i in range(1, len(bars)):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if up > down and up > 0 else ZERO)
        minus_dm.append(down if down > up and down > 0 else ZERO)
    str_ = wilder_series(trs, window)
    splus = wilder_series(plus_dm, window)
    sminus = wilder_series(minus_dm, window)
    # Smoothed series start at index window-1; DX exists from there.
    dx = []
    for j in range(len(str_)):
        if str_[j] == 0:
            dx.append(ZERO)
            continue
        pdi = HUNDRED * splus[j] / str_[j]
        mdi = HUNDRED * sminus[j] / str_[j]
        denom = pdi + mdi
        dx.append(ZERO if denom == 0 else HUNDRED * abs(pdi - mdi) / denom)
    if len(dx) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"ADX({window}) needs {window} DX values, got {len(dx)}",
        )
    return wilder_series(dx, window)[-1]


def parabolic_sar(bars: list[dict], af_step: float, af_max: float) -> Decimal:
    if len(bars) < 2:
        raise InsufficientData(
            "insufficient_warmup", "Parabolic SAR needs >= 2 bars"
        )
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    closes = _closes(bars)
    step = Decimal(str(af_step))
    cap = Decimal(str(af_max))
    rising = closes[1] > closes[0]
    sar = lows[0] if rising else highs[0]
    ep = highs[0] if rising else lows[0]
    af = step
    for i in range(1, len(bars)):
        sar = sar + af * (ep - sar)
        if rising:
            sar = min(sar, lows[i - 1], lows[i - 2] if i >= 2 else lows[i - 1])
            if lows[i] < sar:
                rising = False
                sar = ep
                ep = lows[i]
                af = step
            else:
                if highs[i] > ep:
                    ep = highs[i]
                    af = min(af + step, cap)
        else:
            sar = max(sar, highs[i - 1], highs[i - 2] if i >= 2 else highs[i - 1])
            if highs[i] > sar:
                rising = True
                sar = ep
                ep = highs[i]
                af = step
            else:
                if lows[i] < ep:
                    ep = lows[i]
                    af = min(af + step, cap)
    return sar


def ichimoku(bars: list[dict], tenkan: int, kijun: int, senkou_b: int) -> dict:
    # Components are returned only when their own windows are met;
    # the caller maps a missing component to NOT_CALCULABLE.
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    closes = _closes(bars)
    out: dict = {}
    if len(bars) >= tenkan:
        out["tenkan"] = (
            max(highs[-tenkan:]) + min(lows[-tenkan:])
        ) / Decimal(2)
    if len(bars) >= kijun:
        out["kijun"] = (max(highs[-kijun:]) + min(lows[-kijun:])) / Decimal(2)
        out["senkou_a"] = (out["tenkan"] + out["kijun"]) / Decimal(2)
        out["chikou"] = closes[-1]
    if len(bars) >= senkou_b:
        out["senkou_b"] = (
            max(highs[-senkou_b:]) + min(lows[-senkou_b:])
        ) / Decimal(2)
    return out


def fibonacci(bars: list[dict], window: int) -> dict:
    if len(bars) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"Fibonacci({window}) needs {window} bars, got {len(bars)}",
        )
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    hi = max(highs[-window:])
    lo = min(lows[-window:])
    if hi == lo:
        raise InsufficientData(
            "degenerate_input", "Fibonacci swing has zero range"
        )
    rng = hi - lo
    return {
        f"fib_{int(p * 1000)}": lo + Decimal(str(p)) * rng
        for p in (0.236, 0.382, 0.5, 0.618, 0.786)
    }


def pivots(bars: list[dict]) -> dict:
    if len(bars) < 2:
        raise InsufficientData(
            "insufficient_warmup", "Pivots need a prior bar (>= 2 bars)"
        )
    h = _dec(bars[-2].get("high"), "high")
    lo = _dec(bars[-2].get("low"), "low")
    c = _dec(bars[-2].get("close"), "close")
    p = (h + lo + c) / Decimal(3)
    return {
        "p": p,
        "r1": 2 * p - lo,
        "s1": 2 * p - h,
        "r2": p + (h - lo),
        "s2": p - (h - lo),
    }


def donchian(bars: list[dict], window: int) -> dict:
    if len(bars) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"Donchian({window}) needs {window} bars, got {len(bars)}",
        )
    highs = [_dec(b.get("high"), "high") for b in bars]
    lows = [_dec(b.get("low"), "low") for b in bars]
    upper = max(highs[-window:])
    lower = min(lows[-window:])
    return {"upper": upper, "middle": (upper + lower) / Decimal(2), "lower": lower}


def keltner(bars: list[dict], window: int, atr_window: int, multiplier: int) -> dict:
    closes = _closes(bars)
    if len(closes) < window:
        raise InsufficientData(
            "insufficient_warmup",
            f"Keltner({window}) needs {window} closes, got {len(closes)}",
        )
    middle = ema_series(closes, window)[-1]
    atr_v = _atr_series(bars, atr_window)[-1]
    band = Decimal(multiplier) * atr_v
    return {"middle": middle, "upper": middle + band, "lower": middle - band}


def daily_return(bars: list[dict]) -> Decimal:
    last = bars[-1]
    prev = last.get("previous_close")
    if prev is None:
        raise InsufficientData(
            "missing_data", "previous_close is blank for the latest bar"
        )
    prev_d = _dec(prev, "previous_close")
    if prev_d == 0:
        raise InsufficientData(
            "degenerate_input", "previous_close is zero"
        )
    return _dec(last.get("close"), "close") / prev_d - ONE


# Dispatch: indicator key -> (function, parameter names).
_DISPATCH = {
    "sma": (sma, ("window",)),
    "ema": (ema, ("window",)),
    "macd": (macd, ("fast", "slow", "signal")),
    "rsi": (rsi, ("window",)),
    "roc": (roc, ("window",)),
    "momentum": (momentum, ("window",)),
    "stochastic": (stochastic, ("window", "smooth")),
    "williams_r": (williams_r, ("window",)),
    "cci": (cci, ("window",)),
    "bollinger": (bollinger, ("window", "std_dev")),
    "atr": (atr, ("window",)),
    "volatility": (volatility, ("window",)),
    "volatility_ann": (volatility_ann, ("window",)),
    "drawdown": (drawdown, ()),
    "max_drawdown": (max_drawdown, ()),
    "var_hist": (var_hist, ("window", "confidence")),
    "es_hist": (es_hist, ("window", "confidence")),
    "volume_sma": (volume_sma, ("window",)),
    "relative_volume": (relative_volume, ("window",)),
    "obv": (obv, ()),
    "ad_line": (ad_line, ()),
    "mfi": (mfi, ("window",)),
    "adx": (adx, ("window",)),
    "parabolic_sar": (parabolic_sar, ("af_step", "af_max")),
    "ichimoku": (ichimoku, ("tenkan", "kijun", "senkou_b")),
    "fibonacci": (fibonacci, ("window",)),
    "pivots": (pivots, ()),
    "donchian": (donchian, ("window",)),
    "keltner": (keltner, ("window", "atr_window", "multiplier")),
    "daily_return": (daily_return, ()),
}


def compute_indicator(key: str, bars: list[dict], spec) -> Decimal:
    """Compute one registered indicator output at the last bar.

    Raises InsufficientData for warm-up, missing, or degenerate
    inputs. Multi-output functions return a dict; the component
    field comes from conventions.COMPONENT_FIELD.
    """
    from app.services.technical_indicators.conventions import COMPONENT_FIELD

    func, param_names = _DISPATCH[spec.compute]
    kwargs = {name: spec.parameters[name] for name in param_names}
    result = func(bars, **kwargs)
    if isinstance(result, dict):
        field = COMPONENT_FIELD.get(key)
        if field is None or field not in result:
            raise InsufficientData(
                "insufficient_warmup",
                f"{key} is not available from this computation",
            )
        return result[field]
    return result
