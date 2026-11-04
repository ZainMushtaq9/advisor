"""Phase 6 formula + coverage + aggregation + signal tests.

All expected values below are hand-calculated (see the comments)
from the documented conventions in conventions.py — they are the
independent check on the implementation, not a copy of its output.
Synthetic bars only; no test ever touches a real database.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.services.technical_indicators import aggregation, coverage, formulas, signals
from app.services.technical_indicators.conventions import INDICATORS
from app.services.technical_indicators.formulas import InsufficientData


def bar(day: int, close, high=None, low=None, volume=1000, previous_close=None):
    return {
        "date": date(2026, 11, 2) + timedelta(days=day),
        "open": Decimal(str(close)),
        "high": Decimal(str(close if high is None else high)),
        "low": Decimal(str(close if low is None else low)),
        "close": Decimal(str(close)),
        "volume": volume,
        "previous_close": (
            Decimal(str(previous_close)) if previous_close is not None else None
        ),
        "quality_status": "UNVERIFIED",
    }


def approx(value: Decimal, expected: float, tol: float = 1e-6) -> bool:
    return abs(float(value) - expected) <= tol


def test_sma_and_ema_hand_calculated():
    bars = [bar(i, c) for i, c in enumerate([10, 11, 12, 13, 14])]
    assert formulas.sma(bars, 5) == Decimal("12")  # (10+11+12+13+14)/5
    assert formulas.sma(bars, 3) == Decimal("13")  # (12+13+14)/3
    # EMA(3): k=0.5, seed SMA(10,11,12)=11 -> 12 -> 13.
    assert formulas.ema(bars, 3) == Decimal("13")


def test_rsi_wilder_and_flat_edge():
    # All gains: avg_loss 0 -> 100.
    bars = [bar(i, c) for i, c in enumerate([10, 11, 12, 13])]
    assert formulas.rsi(bars, 3) == Decimal("100")
    # Flat market: both averages 0 -> documented 50.
    bars = [bar(i, 10) for i in range(4)]
    assert formulas.rsi(bars, 3) == Decimal("50")
    # Mixed: changes [2,-1,2], window 2 -> avg_gain 1.5, avg_loss
    # 0.25, RS 6, RSI = 100 - 100/7 = 85.714...
    bars = [bar(i, c) for i, c in enumerate([10, 12, 11, 13])]
    assert approx(formulas.rsi(bars, 2), 85.7142857, tol=1e-4)


def test_macd_constant_line():
    # EMA2 and EMA3 of a +1/day ramp differ by a constant 0.5.
    bars = [bar(i, c) for i, c in enumerate([10, 11, 12, 13, 14, 15])]
    out = formulas.macd(bars, 2, 3, 2)
    assert out["line"] == Decimal("0.5")
    assert out["signal"] == Decimal("0.5")
    assert out["histogram"] == Decimal("0")


def test_bollinger_population_std():
    bars = [bar(i, c) for i, c in enumerate([10, 12, 14])]
    out = formulas.bollinger(bars, 3, 2)
    assert out["middle"] == Decimal("12")
    # variance = (4+0+4)/3 = 8/3; std = sqrt(8/3) ~ 1.63299.
    assert approx(out["upper"], 15.2659863, tol=1e-4)
    assert approx(out["lower"], 8.7340137, tol=1e-4)


def test_atr_wilder():
    bars = [
        bar(0, 11, high=12, low=10),
        bar(1, 12, high=13, low=11),
        bar(2, 13, high=14, low=12),
    ]
    # TRs all 2 -> ATR(2) = 2.
    assert formulas.atr(bars, 2) == Decimal("2")


def test_stochastic_and_williams():
    bars = [
        bar(0, 11, high=12, low=10),
        bar(1, 12, high=13, low=11),
        bar(2, 13, high=14, low=12),
        bar(3, 14, high=15, low=13),
    ]
    out = formulas.stochastic(bars, 2, 3)
    # Every 2-bar window here has hi-lo = 3 and C-lo = 2 -> %K 66.67
    # at every step, so %D (SMA3 of %K) is 66.67 too.
    assert approx(out["k"], 66.6666667, tol=1e-4)
    assert approx(out["d"], 66.6666667, tol=1e-4)
    # Only one %K value exists, so %D (SMA3 of %K) is warm-up short.
    with pytest.raises(InsufficientData):
        formulas.stochastic(bars[:2], 2, 3)
    assert approx(formulas.williams_r(bars, 2), -33.3333333, tol=1e-4)


def test_cci_hand_calculated():
    # TP = close here (H=C+1, L=C-1): TP [10,11,12], SMA 11,
    # MD = 2/3, CCI = 1/(0.015*2/3) = 100.
    bars = [
        bar(0, 10, high=11, low=9),
        bar(1, 11, high=12, low=10),
        bar(2, 12, high=13, low=11),
    ]
    assert formulas.cci(bars, 3) == Decimal("100")


def test_volume_obv_ad_mfi():
    bars = [
        bar(0, 10, volume=100),
        bar(1, 11, volume=200),
        bar(2, 10, volume=300),
    ]
    assert formulas.volume_sma(bars, 2) == Decimal("250")
    assert approx(formulas.relative_volume(bars, 2), 1.2)
    # OBV: +200 (up), -300 (down) = -100.
    assert formulas.obv(bars) == Decimal("-100")
    # A/D: bar0 MFM 0 (H=C+1, L=C-1 with C=10? use explicit bars).
    bars = [
        bar(0, 11, high=12, low=8, volume=100),
        bar(1, 11, high=14, low=10, volume=200),
    ]
    # MFM0 = ((11-8)-(12-11))/4 = 0.5 -> 50; MFM1 = ((11-10)-(14-11))/4
    # = -0.5 -> -100; total -50.
    assert formulas.ad_line(bars) == Decimal("-50")
    # MFI: TP rising both flows, no negative flow -> 100.
    bars = [bar(i, c, volume=100) for i, c in enumerate([10, 11, 12])]
    assert formulas.mfi(bars, 2) == Decimal("100")


def test_volatility_and_drawdown():
    bars = [bar(i, c) for i, c in enumerate([10, 11, 12])]
    # Returns [0.1, 1/11]; pop std ~ 0.0045455.
    assert approx(formulas.volatility(bars, 2), 0.0045455, tol=1e-5)
    bars = [bar(i, c) for i, c in enumerate([10, 12, 11])]
    assert approx(formulas.drawdown(bars), -0.0833333, tol=1e-5)
    assert approx(formulas.max_drawdown(bars), -0.0833333, tol=1e-5)


def test_var_es_nearest_rank():
    bars = [bar(i, c) for i, c in enumerate([100, 110, 99, 121])]
    # Returns [0.1, -0.1, 0.2222]; sorted [-0.1, 0.1, 0.2222];
    # rank ceil(0.05*3)=1 -> VaR 0.1, ES 0.1.
    assert approx(formulas.var_hist(bars, 3, 0.95), 0.1)
    assert approx(formulas.es_hist(bars, 3, 0.95), 0.1)


def test_donchian_keltner_pivots_fibonacci():
    bars = [
        bar(0, 10, high=12, low=10),
        bar(1, 11, high=13, low=11),
        bar(2, 12, high=14, low=12),
        bar(3, 13, high=15, low=13),
    ]
    out = formulas.donchian(bars, 2)
    assert out["upper"] == Decimal("15")  # max high last 2
    assert out["lower"] == Decimal("12")  # min low last 2
    assert out["middle"] == Decimal("13.5")
    # Keltner(2, ATR2, x2): EMA2 last 12.5; ATR2 last 2.875;
    # upper 18.25, lower 6.75.
    out = formulas.keltner(bars, 2, 2, 2)
    assert out["middle"] == Decimal("12.5")
    assert out["upper"] == Decimal("18.25")
    assert out["lower"] == Decimal("6.75")
    # Pivots from prior bar (H 14, L 12, C 12): P = 38/3, R1 = 40/3,
    # S1 = 34/3, R2 = 44/3, S2 = 32/3.
    out = formulas.pivots(bars)
    assert approx(out["p"], 12.6666667, tol=1e-4)
    assert approx(out["r1"], 13.3333333, tol=1e-4)
    assert approx(out["s1"], 11.3333333, tol=1e-4)
    assert approx(out["r2"], 14.6666667, tol=1e-4)
    assert approx(out["s2"], 10.6666667, tol=1e-4)
    # Fibonacci(3): swing hi 15, lo 11, range 4.
    out = formulas.fibonacci(bars, 3)
    assert out["fib_236"] == Decimal("11.944")
    assert out["fib_500"] == Decimal("13")
    assert out["fib_786"] == Decimal("14.144")


def test_ichimoku_components_and_warmup():
    bars = [
        bar(0, 11, high=12, low=10),
        bar(1, 12, high=13, low=11),
        bar(2, 13, high=14, low=12),
        bar(3, 14, high=15, low=13),
    ]
    out = formulas.ichimoku(bars, 2, 3, 4)
    assert out["tenkan"] == Decimal("13.5")
    assert out["kijun"] == Decimal("13")
    assert out["senkou_a"] == Decimal("13.25")
    assert out["senkou_b"] == Decimal("12.5")
    assert out["chikou"] == Decimal("14")
    # Fewer than 4 bars: senkou_b missing, others present.
    # Tenkan on bars[:3] uses bars 1..2: (14 + 11) / 2 = 12.5.
    out = formulas.ichimoku(bars[:3], 2, 3, 4)
    assert "senkou_b" not in out
    assert out["tenkan"] == Decimal("12.5")


def test_parabolic_sar_clamp_rule():
    bars = [
        bar(0, 11, high=12, low=10),
        bar(1, 12, high=13, low=11),
        bar(2, 13, high=14, low=12),
    ]
    # Rising: SAR starts at low0=10 and is clamped to prior lows,
    # so it stays 10 through this ramp.
    assert formulas.parabolic_sar(bars, 0.02, 0.20) == Decimal("10")


def test_adx_hand_calculated():
    bars = [
        bar(0, 11, high=12, low=10),
        bar(1, 12, high=13, low=11),
        bar(2, 13, high=14, low=12),
    ]
    # TR [2,2,2]; +DM [0,1,1]; -DM [0,0,0]; +DI 25 then 37.5;
    # DX 100 then 100; ADX(2) seed 100 -> 100.
    assert formulas.adx(bars, 2) == Decimal("100")


def test_daily_return_and_missing_previous_close():
    bars = [bar(0, 110, previous_close=100)]
    assert formulas.daily_return(bars) == Decimal("0.1")
    bars = [bar(0, 110, previous_close=None)]
    with pytest.raises(InsufficientData) as exc:
        formulas.daily_return(bars)
    assert exc.value.code == "missing_data"


def test_warmup_and_degenerate_errors():
    bars = [bar(i, c) for i, c in enumerate([10, 11])]
    with pytest.raises(InsufficientData) as exc:
        formulas.sma(bars, 5)
    assert exc.value.code == "insufficient_warmup"
    # Zero-range stochastic window is degenerate, not zero. Four
    # bars meet the window-2/smooth-3 warm-up (2+3-1), so the
    # failure is degeneracy, not warm-up.
    bars = [bar(i, 10, high=10, low=10) for i in range(4)]
    with pytest.raises(InsufficientData) as exc:
        formulas.stochastic(bars, 2, 3)
    assert exc.value.code == "degenerate_input"
    # Flat typical price -> CCI undefined.
    with pytest.raises(InsufficientData) as exc:
        formulas.cci(bars, 2)
    assert exc.value.code == "degenerate_input"


def test_no_look_ahead_via_as_of():
    bars = [bar(i, c) for i, c in enumerate([10, 11, 12, 13, 14])]
    as_of = date(2026, 11, 4)  # third bar (index 2)
    detail = coverage.assess_security("TEST", bars, as_of)
    assert detail["bars_available"] == 3
    # SMA(5) must be NOT_CALCULABLE on 3 bars even though 5 exist later.
    sma5 = next(v for v in detail["verdicts"] if v["indicator_key"] == "sma_5")
    assert sma5["status"] == "NOT_CALCULABLE"
    assert sma5["reason"] == "insufficient_warmup"
    # And the direct computation on the prefix equals the as-of value.
    assert formulas.sma(bars[:3], 3) == Decimal("11")


def test_coverage_single_bar_and_empty():
    bars = [bar(0, 100)]
    detail = coverage.assess_security("ONE", bars)
    assert detail["bars_available"] == 1
    assert detail["calculable_count"] == 0
    assert len(detail["verdicts"]) == len(INDICATORS)
    by_key = {v["indicator_key"]: v for v in detail["verdicts"]}
    assert by_key["daily_return"]["reason"] == "missing_data"
    assert by_key["sma_5"]["reason"] == "insufficient_warmup"
    assert by_key["sma_200"]["detail"].startswith("Needs 200 bars")
    detail = coverage.assess_security("NONE", [])
    assert detail["bars_available"] == 0
    assert all(v["reason"] == "missing_data" for v in detail["verdicts"])


def test_coverage_conflicted_inputs_excluded():
    bars = [bar(i, c) for i, c in enumerate([10, 11, 12, 13, 14, 15])]
    bars[0]["quality_status"] = "CONFLICTED"
    detail = coverage.assess_security("CF", bars)
    assert all(v["reason"] == "conflicted_input" for v in detail["verdicts"])


def test_aggregation_weekly_monthly_and_partial():
    # 2026-11-02 is a Monday; 5 weekday bars + next Monday.
    bars = []
    for i, day in enumerate([2, 3, 4, 5, 6, 9]):
        bars.append(
            {
                "date": date(2026, 11, day),
                "open": Decimal("10"),
                "high": Decimal(10 + i),
                "low": Decimal("9"),
                "close": Decimal(10 + i),
                "volume": 100,
                "previous_close": None,
                "quality_status": "UNVERIFIED",
            }
        )
    weekly = aggregation.aggregate(bars, "weekly")
    assert len(weekly) == 2
    assert weekly[0]["observed_days"] == 5
    assert weekly[0]["status"] == "partial"  # never "complete" without a calendar
    assert weekly[0]["open"] == Decimal("10")
    assert weekly[0]["high"] == Decimal("14")
    assert weekly[0]["close"] == Decimal("14")
    assert weekly[0]["volume"] == 500
    monthly = aggregation.aggregate(bars, "monthly")
    assert len(monthly) == 1
    assert monthly[0]["observed_days"] == 6
    with pytest.raises(InsufficientData):
        aggregation.aggregate(bars, "intraday")


def test_drawdown_zero_running_max_is_degenerate():
    # Audit M3: a zero close must yield a clean degenerate verdict,
    # never a Decimal division crash escaping coverage.
    bars = [bar(0, 0), bar(1, 10)]
    with pytest.raises(InsufficientData) as exc:
        formulas.drawdown(bars)
    assert exc.value.code == "degenerate_input"
    with pytest.raises(InsufficientData) as exc:
        formulas.max_drawdown(bars)
    assert exc.value.code == "degenerate_input"


def test_stochastic_flat_early_window_does_not_veto_clean_final():
    # Audit M4: only the windows feeding %K/%D matter. Bars 0-1 are
    # flat (hi == lo), but they fall outside the last 3 windows
    # (window 2, smooth 3, 5 bars): %K windows end at bars 2, 3, 4.
    # %K: (12-10)/3=66.6667, (14-11)/4=75, (16-12)/5=80.
    # %D = mean(66.6667, 75, 80) = 73.8889.
    raw = [
        (10, 10, 10),
        (10, 10, 10),
        (12, 13, 11),
        (14, 15, 12),
        (16, 17, 13),
    ]
    bars = [
        {
            "date": date(2026, 11, 2) + timedelta(days=i),
            "open": Decimal(str(c)),
            "high": Decimal(str(h)),
            "low": Decimal(str(low)),
            "close": Decimal(str(c)),
            "volume": 1000,
            "previous_close": None,
            "quality_status": "UNVERIFIED",
        }
        for i, (c, h, low) in enumerate(raw)
    ]
    result = formulas.stochastic(bars, 2, 3)
    assert approx(result["k"], 80.0)
    assert approx(result["d"], 73.8889, tol=1e-4)
    # A flat FINAL window still raises: make bars 3-4 share one
    # high == low (14), so the window ending at bar 4 is degenerate.
    bars[-2]["high"] = bars[-2]["low"] = bars[-2]["close"] = Decimal("14")
    bars[-1]["high"] = bars[-1]["low"] = bars[-1]["close"] = Decimal("14")
    with pytest.raises(InsufficientData) as exc:
        formulas.stochastic(bars, 2, 3)
    assert exc.value.code == "degenerate_input"


def test_aggregation_missing_ohlc_is_clean_missing_data():
    # Audit M7: a None high/low/open/close must raise
    # InsufficientData, never TypeError from max()/min().
    bars = [
        {
            "date": date(2026, 11, 2),
            "open": Decimal("10"),
            "high": None,
            "low": Decimal("9"),
            "close": Decimal("10"),
            "volume": 100,
            "previous_close": None,
            "quality_status": "UNVERIFIED",
        },
        {
            "date": date(2026, 11, 3),
            "open": Decimal("10"),
            "high": Decimal("11"),
            "low": Decimal("9"),
            "close": Decimal("11"),
            "volume": 100,
            "previous_close": None,
            "quality_status": "UNVERIFIED",
        },
    ]
    with pytest.raises(InsufficientData) as exc:
        aggregation.aggregate(bars, "weekly")
    assert exc.value.code == "missing_data"


def test_coverage_conflicted_flag_path():
    # Audit H2: the flag covers securities whose conflicted rows
    # were excluded upstream, with or without usable bars.
    detail = coverage.assess_security("CF", [], has_conflicted_inputs=True)
    assert all(v["reason"] == "conflicted_input" for v in detail["verdicts"])
    bars = [bar(i, c) for i, c in enumerate([10, 11, 12, 13, 14, 15])]
    detail = coverage.assess_security("CF", bars, has_conflicted_inputs=True)
    assert all(v["reason"] == "conflicted_input" for v in detail["verdicts"])
    market = coverage.assess_market(
        {"OK": bars, "CF": []}, conflicted_tickers={"CF"}
    )
    assert all(
        v["reason"] == "conflicted_input"
        for v in market["per_ticker"]["CF"]["verdicts"]
    )
    assert market["per_ticker"]["OK"]["calculable_count"] > 0


def test_load_series_flags_conflicted_tickers():
    # Audit H2, runner path: conflicted rows stay out of the
    # series but their ticker is flagged (fake session, no DB).
    from types import SimpleNamespace

    from app.services.technical_indicators.runner import load_series

    class FakeQuery:
        def __init__(self, rows):
            self._rows = rows

        def join(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            return self._rows

    class FakeSession:
        def __init__(self, price_rows, securities):
            self._price_rows = price_rows
            self._securities = securities

        def query(self, *args):
            if len(args) == 2:
                return FakeQuery(self._price_rows)
            return FakeQuery(self._securities)

    def price(day, close, quality):
        return SimpleNamespace(
            trading_date=date(2026, 11, 3),
            open_price=Decimal(str(close)),
            high_price=Decimal(str(close)),
            low_price=Decimal(str(close)),
            close_price=Decimal(str(close)),
            volume=100,
            previous_close=None,
            quality_status=quality,
            source_key="test_source",
        )

    session = FakeSession(
        [("AAA", price(0, 100, "UNVERIFIED")), ("BBB", price(0, 50, "CONFLICTED"))],
        [SimpleNamespace(ticker="AAA", id=1), SimpleNamespace(ticker="BBB", id=2)],
    )
    series, ids, conflicted = load_series(session)
    assert len(series["AAA"]) == 1
    assert series["BBB"] == []
    assert conflicted == {"BBB"}
    assert ids == {"AAA": 1, "BBB": 2}


def test_signals_empty_rules_and_no_fabrication():
    assert signals.evaluate_rules((), {"sma_5": Decimal("10")}, date(2026, 11, 3)) == []
    assert signals.ACTIVATED_RULES == ()
    # A rule without an evaluator must fail loudly, never emit.
    with pytest.raises(NotImplementedError):
        signals.evaluate_rules(
            signals.EXAMPLE_RULES,
            {"sma_50": Decimal("10"), "sma_200": Decimal("9")},
            date(2026, 11, 3),
        )
