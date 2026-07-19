"""Technical indicator series: SMA, EMA, RSI, MACD computed on the fly.

Ported from pravafin's calculators but emitting full per-day series (one pass)
instead of a single latest value. Values match the classic definitions:
SMA = rolling mean; EMA seeded with SMA(period), k = 2/(period+1);
RSI = simple average of last-N gains/losses; MACD = EMA12 - EMA26,
signal = EMA9 over the MACD series.
"""

import math

import coresat.services as css


def test_sma_series_rolling_mean() -> None:
    result = css.sma_series([1.0, 2.0, 3.0, 4.0, 5.0], period=3)
    assert result[:2] == [None, None]
    assert result[2:] == [2.0, 3.0, 4.0]


def test_sma_series_short_input_is_all_none() -> None:
    assert css.sma_series([1.0, 2.0], period=3) == [None, None]


def test_ema_series_seeds_with_sma_then_smooths() -> None:
    result = css.ema_series([1.0, 2.0, 3.0, 4.0, 5.0], period=3)
    assert result[:2] == [None, None]
    assert result[2] == 2.0  # seed = SMA(3)
    # k = 2/4 = 0.5 → ema = price*0.5 + prev*0.5
    assert result[3] == 3.0
    assert result[4] == 4.0


def test_rsi_all_gains_is_100() -> None:
    closes = [float(i) for i in range(1, 17)]
    result = css.rsi_series(closes, period=14)
    assert result[14] == 100.0
    assert result[:14] == [None] * 14


def test_rsi_alternating_moves_is_bounded() -> None:
    closes = [100.0 + (1.0 if i % 2 else -1.0) for i in range(30)]
    result = css.rsi_series(closes, period=14)
    tail = [value for value in result if value is not None]
    assert tail
    assert all(0.0 <= value <= 100.0 for value in tail)


def test_macd_series_shapes_and_warmup() -> None:
    closes = [100.0 + math.sin(i / 5.0) * 10.0 for i in range(60)]
    macd, signal = css.macd_series(closes, fast=12, slow=26, signal=9)
    assert len(macd) == len(signal) == 60
    assert macd[24] is None  # slow EMA not ready
    assert macd[25] is not None
    assert signal[32] is None  # signal EMA needs 9 macd values
    assert signal[33] is not None


def test_macd_is_fast_minus_slow_ema() -> None:
    closes = [float(i) for i in range(1, 61)]
    macd, _ = css.macd_series(closes, fast=12, slow=26, signal=9)
    fast = css.ema_series(closes, 12)
    slow = css.ema_series(closes, 26)
    last_fast, last_slow, last_macd = fast[-1], slow[-1], macd[-1]
    assert last_fast is not None and last_slow is not None and last_macd is not None
    assert math.isclose(last_macd, last_fast - last_slow)
