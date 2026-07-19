"""Technical indicator series computed on the fly from close prices.

Ported from pravafin's TechnicalIndicatorsService, reshaped to emit full
per-day series in one pass — recomputing the MACD signal line per day from
scratch would be cubic in history length.
"""

import coresat.domain as csd


def sma_series(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    window_sum = 0.0
    for index, value in enumerate(values):
        window_sum += value
        if index >= period:
            window_sum -= values[index - period]
        if index >= period - 1:
            result[index] = window_sum / period
    return result


def ema_series(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result
    k = 2.0 / (period + 1)
    ema = sum(values[:period]) / period
    result[period - 1] = ema
    for index in range(period, len(values)):
        ema = values[index] * k + ema * (1.0 - k)
        result[index] = ema
    return result


def rsi_series(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) < period + 1:
        return result
    changes = [values[index] - values[index - 1] for index in range(1, len(values))]
    gain_sum = loss_sum = 0.0
    for index, change in enumerate(changes):
        gain_sum += max(change, 0.0)
        loss_sum += max(-change, 0.0)
        if index >= period:
            oldest = changes[index - period]
            gain_sum -= max(oldest, 0.0)
            loss_sum -= max(-oldest, 0.0)
        if index >= period - 1:
            day = index + 1
            if loss_sum == 0.0:
                result[day] = 100.0
            else:
                relative_strength = gain_sum / loss_sum
                result[day] = 100.0 - 100.0 / (1.0 + relative_strength)
    return result


def macd_series(
    values: list[float], fast: int, slow: int, signal: int
) -> tuple[list[float | None], list[float | None]]:
    fast_ema = ema_series(values, fast)
    slow_ema = ema_series(values, slow)
    macd: list[float | None] = [
        f - s if f is not None and s is not None else None
        for f, s in zip(fast_ema, slow_ema, strict=True)
    ]
    macd_values = [value for value in macd if value is not None]
    signal_dense = ema_series(macd_values, signal)
    signal_full: list[float | None] = [None] * len(values)
    dense_index = 0
    for index, value in enumerate(macd):
        if value is not None:
            signal_full[index] = signal_dense[dense_index]
            dense_index += 1
    return macd, signal_full


def indicator_points(bars: list[csd.CandleBar]) -> list[csd.IndicatorPoint]:
    closes = [bar.close for bar in bars]
    sma_20 = sma_series(closes, 20)
    sma_50 = sma_series(closes, 50)
    sma_200 = sma_series(closes, 200)
    ema_12 = ema_series(closes, 12)
    ema_26 = ema_series(closes, 26)
    rsi = rsi_series(closes, 14)
    macd, macd_signal = macd_series(closes, 12, 26, 9)
    return [
        csd.IndicatorPoint(
            date=bar.date,
            close=bar.close,
            sma_20=s20,
            sma_50=s50,
            sma_200=s200,
            ema_12=e12,
            ema_26=e26,
            rsi=r,
            macd=m,
            macd_signal=ms,
        )
        for bar, s20, s50, s200, e12, e26, r, m, ms in zip(
            bars, sma_20, sma_50, sma_200, ema_12, ema_26, rsi, macd, macd_signal, strict=True
        )
    ]
