# Phase 6 — Test report

## Backend tests (executed 2026-11-04)

- Full backend suite: 114 passed, 0 failed (85 pre-existing +
  29 Phase 6 tests, including 5 added for audit findings H2/M3/
  M4/M7 and one corrected stochastic warm-up expectation),
  plus 1 pre-existing Starlette TestClient deprecation warning.
  Ruff clean on all new files.
- New test file: backend/tests/test_technical_indicators.py
  (hand-calculated cases, checked independently of the
  implementation, not copied from its output):
  SMA(5)=12, SMA(3)=13; EMA(3)=13 (k=0.5, SMA seed); RSI
  all-gains=100, flat=50, mixed window-2 ≈ 85.7143; MACD(2,3,2)
  line=signal=0.5, histogram=0; Bollinger(3,2) middle 12, upper
  ≈ 15.265986, lower ≈ 8.734014 (population std); ATR(2)=2;
  Stochastic(2,3) %K=%D ≈ 66.6667; Williams %R(2) ≈ -33.3333;
  CCI(3)=100; volume SMA(2)=250, relative volume 1.2; OBV
  -100; A/D -50; MFI(2)=100; volatility(2) ≈ 0.0045455;
  drawdown/max drawdown ≈ -0.0833333; VaR95/ES95 0.1 (window 3);
  Donchian(2) 15/12/13.5; Keltner(2, ATR2, x2) 12.5/18.25/6.75;
  pivots from prior bar (H14,L12,C12): P ≈ 12.6667, R1 ≈
  13.3333, S1 ≈ 11.3333, R2 ≈ 14.6667, S2 ≈ 10.6667;
  Fibonacci(3) swing 11–15: 236 = 11.944, 500 = 13, 786 =
  14.144; Ichimoku(2,3,4) tenkan 13.5, kijun 13, senkou_a
  13.25, senkou_b 12.5, chikou 14, and on 3 bars senkou_b
  missing with tenkan 12.5; Parabolic SAR = 10 on a rising
  ramp; ADX(2) = 100; daily return 0.1 (close 110 /
  previous_close 100) and missing_data when blank.
- Edge cases covered: warm-up errors (SMA(5) on 2 bars),
  degenerate inputs (zero-range Stochastic, flat-TP CCI),
  no-look-ahead (as-of slice reproduces prefix results),
  single-bar security (0 calculable of 62), empty security
  (all missing_data), conflicted inputs excluded (all
  conflicted_input), weekly/monthly aggregation (Monday-week
  groups, monthly group, partial status, observed_days),
  intraday refusal, empty activated-rule set, example rule
  raising NotImplementedError.
- New API test file: backend/tests/test_indicators_api.py —
  route registration via OpenAPI paths (a first version failed
  because newer FastAPI wraps included routers; fixed to read
  openapi()["paths"]); all four endpoints 503 without a
  database, with the DATABASE_URL reason stated.
- Test-authoring errors found and fixed during review (not
  implementation errors): stochastic %D needs 4 bars, pivots
  prior-bar close is 12 not 13, Ichimoku 3-bar tenkan is 12.5
  not 13, ADX +DI comment values 25/37.5, one dead snippet
  removed. The implementation was not adjusted to match a
  wrong test — the tests were corrected to the documented
  conventions.

## Frontend tests (executed 2026-11-04)

- TypeScript typecheck: pass. ESLint: pass. `next build`:
  pass (12 routes including /indicators). Vitest: 11 passed
  (pre-existing suite). No dedicated page unit test was added;
  see frontend_documentation.md for why this is stated, not
  padded. After the audit fixes, the page fetches stored
  values/signals totals and the API scope/signal notes from
  the backend instead of rendering static "none yet" text
  (audit M5), and splits the ticker error into "Unknown
  ticker" (404) vs "Backend unavailable".

## Live inspection (executed 2026-11-04, real production DB)

- Coverage API: 200, 470 securities, 62 indicators, 0 with
  any calculable indicator; sma_5 reasons exactly
  insufficient_warmup 444 + missing_data 26; daily_return
  missing_data 470. First full-coverage call ~375ms (the
  auditor's independent TestClient call took ~216ms; timings
  are not directly comparable).
- OGDC coverage: 200, 1 bar, 0 calculable, 62 not calculable,
  with per-indicator reasons and unblockers. Unknown ticker:
  404. Values: total 0. Signals: total 0 with the observation
  note. Bad as_of: 422. Bad indicator_key: 422.
- Immutability triggers: UPDATE and DELETE on a test row both
  raised the append-only error; rolled back; residue 0; real
  value rows still 0. (Two earlier script attempts failed on
  script-side transaction handling, not on the product; the
  corrected attempt is the one recorded here.)
