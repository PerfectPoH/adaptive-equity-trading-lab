from __future__ import annotations

import pandas as pd
import numpy as np


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window, min_periods=window).mean()
    avg_loss = loss.rolling(window, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series) -> pd.Series:
    fast = ema(close, 12)
    slow = ema(close, 26)
    return fast - slow


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window, min_periods=window).mean()


def rolling_volatility(close: pd.Series, window: int = 20) -> pd.Series:
    return close.pct_change().rolling(window, min_periods=window).std()


def relative_volume(volume: pd.Series, window: int = 20) -> pd.Series:
    return volume / volume.rolling(window, min_periods=window).mean()


def rolling_zscore(series: pd.Series, window: int = 20) -> pd.Series:
    rolling_mean = series.rolling(window, min_periods=window).mean()
    rolling_std = series.rolling(window, min_periods=window).std()
    return (series - rolling_mean) / rolling_std.replace(0, np.nan)


def distance_from_rolling_high(close: pd.Series, high: pd.Series, window: int = 20) -> pd.Series:
    rolling_high = high.rolling(window, min_periods=window).max()
    return (close / rolling_high) - 1


def close_position_in_rolling_range(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    window: int = 20,
) -> pd.Series:
    rolling_high = high.rolling(window, min_periods=window).max()
    rolling_low = low.rolling(window, min_periods=window).min()
    range_width = (rolling_high - rolling_low).replace(0, np.nan)
    return (close - rolling_low) / range_width
