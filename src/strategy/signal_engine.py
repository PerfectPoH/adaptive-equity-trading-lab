from __future__ import annotations

import pandas as pd


def add_signal_columns(
    frame: pd.DataFrame,
    min_scanner_score: float = 70,
    min_model_probability: float = 0.60,
    min_relative_volume: float | None = None,
    max_distance_from_20d_high: float | None = None,
    max_atr_pct: float | None = None,
) -> pd.DataFrame:
    data = frame.copy()
    relative_volume_filter = _min_filter(data, "relative_volume_20d", min_relative_volume)
    distance_filter = _max_filter(data, "distance_from_20d_high", max_distance_from_20d_high)
    atr_filter = _max_filter(data, "atr_pct", max_atr_pct)
    data["signal"] = (
        (data["scanner_score"] > min_scanner_score)
        & (data["model_probability"] > min_model_probability)
        & data["spy_trend_positive"].fillna(False).astype(bool)
        & relative_volume_filter
        & distance_filter
        & atr_filter
    )
    data["signal_reason"] = ""
    mask = data["signal"]
    data.loc[mask, "signal_reason"] = (
        "scanner_score="
        + data.loc[mask, "scanner_score"].round(1).astype(str)
        + ", model_probability="
        + data.loc[mask, "model_probability"].round(3).astype(str)
        + ", market trend positive"
    )
    reason_suffixes = _filter_reason_suffixes(
        min_relative_volume=min_relative_volume,
        max_distance_from_20d_high=max_distance_from_20d_high,
        max_atr_pct=max_atr_pct,
    )
    if reason_suffixes:
        data.loc[mask, "signal_reason"] = data.loc[mask, "signal_reason"] + ", " + ", ".join(reason_suffixes)
    return data


def _min_filter(data: pd.DataFrame, column: str, threshold: float | None) -> pd.Series:
    if threshold is None:
        return pd.Series(True, index=data.index)
    if column not in data.columns:
        return pd.Series(False, index=data.index)
    return pd.to_numeric(data[column], errors="coerce") >= threshold


def _max_filter(data: pd.DataFrame, column: str, threshold: float | None) -> pd.Series:
    if threshold is None:
        return pd.Series(True, index=data.index)
    if column not in data.columns:
        return pd.Series(False, index=data.index)
    return pd.to_numeric(data[column], errors="coerce") <= threshold


def _filter_reason_suffixes(
    min_relative_volume: float | None,
    max_distance_from_20d_high: float | None,
    max_atr_pct: float | None,
) -> list[str]:
    suffixes: list[str] = []
    if min_relative_volume is not None:
        suffixes.append(f"relative_volume_20d>={min_relative_volume}")
    if max_distance_from_20d_high is not None:
        suffixes.append(f"distance_from_20d_high<={max_distance_from_20d_high}")
    if max_atr_pct is not None:
        suffixes.append(f"atr_pct<={max_atr_pct}")
    return suffixes
