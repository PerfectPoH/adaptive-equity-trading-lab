from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.news_features import NEWS_FEATURE_COLUMNS, add_market_news_features
from src.features.indicators import (
    atr,
    close_position_in_rolling_range,
    distance_from_rolling_high,
    ema,
    macd,
    relative_volume,
    rolling_volatility,
    rolling_zscore,
    rsi,
)


BASE_FEATURE_COLUMNS = [
    "return_1d",
    "rolling_return_5d",
    "rsi_14",
    "ema_20_ratio",
    "ema_50_ratio",
    "macd",
    "atr",
    "atr_pct",
    "rolling_volatility_20d",
    "relative_volume_20d",
    "distance_from_20d_high",
    "spy_trend_positive",
    *NEWS_FEATURE_COLUMNS,
]

ENHANCED_ONLY_FEATURE_COLUMNS = [
    "rolling_return_10d",
    "rolling_return_20d",
    "ema_20_slope_5d",
    "ema_50_slope_5d",
    "intraday_range_pct",
    "close_position_20d_range",
    "volume_zscore_20d",
    "log_avg_dollar_volume_20d",
    "spy_return_5d",
    "spy_ema_50_ratio",
    "spy_rolling_volatility_20d",
]

FEATURE_COLUMNS = [*BASE_FEATURE_COLUMNS]
ENHANCED_FEATURE_COLUMNS = [*BASE_FEATURE_COLUMNS, *ENHANCED_ONLY_FEATURE_COLUMNS]


def build_features(
    frame: pd.DataFrame,
    spy_frame: pd.DataFrame | None = None,
    market_news: pd.DataFrame | None = None,
) -> pd.DataFrame:
    data = frame.copy().sort_index()

    data["return_1d"] = data["Close"].pct_change()
    data["rolling_return_5d"] = data["Close"].pct_change(5)
    data["rolling_return_10d"] = data["Close"].pct_change(10)
    data["rolling_return_20d"] = data["Close"].pct_change(20)
    data["rsi_14"] = rsi(data["Close"], 14)

    ema_20 = ema(data["Close"], 20)
    ema_50 = ema(data["Close"], 50)
    data["ema_20"] = ema_20
    data["ema_50"] = ema_50
    data["ema_20_ratio"] = (data["Close"] / ema_20) - 1
    data["ema_50_ratio"] = (data["Close"] / ema_50) - 1
    data["ema_20_slope_5d"] = ema_20.pct_change(5)
    data["ema_50_slope_5d"] = ema_50.pct_change(5)

    data["macd"] = macd(data["Close"])
    data["atr"] = atr(data["High"], data["Low"], data["Close"], 14)
    data["atr_pct"] = data["atr"] / data["Close"]
    data["rolling_volatility_20d"] = rolling_volatility(data["Close"], 20)
    data["relative_volume_20d"] = relative_volume(data["Volume"], 20)
    data["volume_zscore_20d"] = rolling_zscore(data["Volume"].astype(float), 20)
    data["distance_from_20d_high"] = distance_from_rolling_high(data["Close"], data["High"], 20)
    data["intraday_range_pct"] = (data["High"] - data["Low"]) / data["Close"]
    data["close_position_20d_range"] = close_position_in_rolling_range(
        data["Close"],
        data["High"],
        data["Low"],
        20,
    )
    dollar_volume = data["Close"] * data["Volume"]
    data["log_avg_dollar_volume_20d"] = np.log1p(dollar_volume.rolling(20, min_periods=20).mean())

    if spy_frame is not None:
        spy = spy_frame.copy().sort_index()
        spy_ema_50 = ema(spy["Close"], 50)
        spy_trend = (spy["Close"] > spy_ema_50).rename("spy_trend_positive")
        data["spy_trend_positive"] = spy_trend.reindex(data.index).ffill().fillna(False)
        data["spy_return_5d"] = spy["Close"].pct_change(5).reindex(data.index).ffill()
        data["spy_ema_50_ratio"] = ((spy["Close"] / spy_ema_50) - 1).reindex(data.index).ffill()
        data["spy_rolling_volatility_20d"] = rolling_volatility(spy["Close"], 20).reindex(data.index).ffill()
    else:
        data["spy_trend_positive"] = data["Close"] > ema_50
        data["spy_return_5d"] = data["rolling_return_5d"]
        data["spy_ema_50_ratio"] = data["ema_50_ratio"]
        data["spy_rolling_volatility_20d"] = data["rolling_volatility_20d"]

    data["spy_trend_positive"] = data["spy_trend_positive"].astype(bool)
    data = add_market_news_features(data, market_news)
    return data
