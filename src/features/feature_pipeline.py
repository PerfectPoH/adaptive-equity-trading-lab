from __future__ import annotations

import pandas as pd

from src.features.indicators import (
    atr,
    distance_from_rolling_high,
    ema,
    macd,
    relative_volume,
    rolling_volatility,
    rsi,
)


FEATURE_COLUMNS = [
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
]


def build_features(frame: pd.DataFrame, spy_frame: pd.DataFrame | None = None) -> pd.DataFrame:
    data = frame.copy().sort_index()

    data["return_1d"] = data["Close"].pct_change()
    data["rolling_return_5d"] = data["Close"].pct_change(5)
    data["rsi_14"] = rsi(data["Close"], 14)

    ema_20 = ema(data["Close"], 20)
    ema_50 = ema(data["Close"], 50)
    data["ema_20"] = ema_20
    data["ema_50"] = ema_50
    data["ema_20_ratio"] = (data["Close"] / ema_20) - 1
    data["ema_50_ratio"] = (data["Close"] / ema_50) - 1

    data["macd"] = macd(data["Close"])
    data["atr"] = atr(data["High"], data["Low"], data["Close"], 14)
    data["atr_pct"] = data["atr"] / data["Close"]
    data["rolling_volatility_20d"] = rolling_volatility(data["Close"], 20)
    data["relative_volume_20d"] = relative_volume(data["Volume"], 20)
    data["distance_from_20d_high"] = distance_from_rolling_high(data["Close"], data["High"], 20)

    if spy_frame is not None:
        spy = spy_frame.copy().sort_index()
        spy_ema_50 = ema(spy["Close"], 50)
        spy_trend = (spy["Close"] > spy_ema_50).rename("spy_trend_positive")
        data["spy_trend_positive"] = spy_trend.reindex(data.index).ffill().fillna(False)
    else:
        data["spy_trend_positive"] = data["Close"] > ema_50

    data["spy_trend_positive"] = data["spy_trend_positive"].astype(bool)
    return data
