from __future__ import annotations

import numpy as np
import pandas as pd


def add_signal_columns(
    frame: pd.DataFrame,
    min_scanner_score: float = 70,
    min_model_probability: float = 0.60,
    min_relative_volume: float | None = None,
    max_distance_from_20d_high: float | None = None,
    max_atr_pct: float | None = None,
    min_signal_quality_score: float | None = None,
) -> pd.DataFrame:
    data = frame.copy()
    data["signal_quality_score"] = score_signal_quality(data)
    relative_volume_filter = _min_filter(data, "relative_volume_20d", min_relative_volume)
    distance_filter = _max_filter(data, "distance_from_20d_high", max_distance_from_20d_high)
    atr_filter = _max_filter(data, "atr_pct", max_atr_pct)
    quality_filter = _min_filter(data, "signal_quality_score", min_signal_quality_score)
    data["signal"] = (
        (data["scanner_score"] > min_scanner_score)
        & (data["model_probability"] > min_model_probability)
        & data["spy_trend_positive"].fillna(False).astype(bool)
        & relative_volume_filter
        & distance_filter
        & atr_filter
        & quality_filter
    )
    data["signal_before_rank"] = data["signal"].fillna(False).astype(bool)
    data["signal_rank"] = pd.NA
    data["signal_rank_selected"] = data["signal_before_rank"]
    data["signal_filter_reason"] = ""
    data["signal_reason"] = ""
    mask = data["signal"]
    data.loc[mask, "signal_reason"] = (
        "scanner_score="
        + data.loc[mask, "scanner_score"].round(1).astype(str)
        + ", model_probability="
        + data.loc[mask, "model_probability"].round(3).astype(str)
        + ", signal_quality_score="
        + data.loc[mask, "signal_quality_score"].round(3).astype(str)
        + ", market trend positive"
    )
    reason_suffixes = _filter_reason_suffixes(
        min_relative_volume=min_relative_volume,
        max_distance_from_20d_high=max_distance_from_20d_high,
        max_atr_pct=max_atr_pct,
        min_signal_quality_score=min_signal_quality_score,
    )
    if reason_suffixes:
        data.loc[mask, "signal_reason"] = data.loc[mask, "signal_reason"] + ", " + ", ".join(reason_suffixes)
    return data


def score_signal_quality(frame: pd.DataFrame) -> pd.Series:
    data = frame.copy()
    probability = _numeric(data, "model_probability").clip(0, 1).fillna(0)
    scanner = (_numeric(data, "scanner_score") / 100).clip(0, 1).fillna(0)
    relative_volume = ((_numeric(data, "relative_volume_20d") - 1) / 1.5).clip(0, 1).fillna(0)
    breakout_proximity = (1 + (_numeric(data, "distance_from_20d_high") / 0.05)).clip(0, 1).fillna(0)
    volatility_stability = (1 - ((_numeric(data, "atr_pct") - 0.005) / 0.075)).clip(0, 1).fillna(0.5)

    score = (
        (0.55 * probability)
        + (0.25 * scanner)
        + (0.10 * relative_volume)
        + (0.05 * breakout_proximity)
        + (0.05 * volatility_stability)
    )
    return score.replace([np.inf, -np.inf], np.nan).fillna(0).clip(0, 1)


def apply_daily_signal_rank_filter(
    frame: pd.DataFrame,
    max_signals_per_day: int | None = None,
    rank_column: str = "signal_quality_score",
) -> pd.DataFrame:
    data = frame.copy()
    if "signal" not in data.columns:
        data["signal"] = False
    if "signal_before_rank" not in data.columns:
        data["signal_before_rank"] = data["signal"].fillna(False).astype(bool)
    if "signal_quality_score" not in data.columns:
        data["signal_quality_score"] = score_signal_quality(data)
    data["signal_rank"] = pd.NA
    data["signal_rank_selected"] = data["signal_before_rank"]
    if "signal_filter_reason" not in data.columns:
        data["signal_filter_reason"] = ""
    data["signal_filter_reason"] = data["signal_filter_reason"].fillna("").astype(str)

    if max_signals_per_day is None:
        return data
    if max_signals_per_day <= 0:
        raise ValueError("max_signals_per_day must be positive when provided")
    if rank_column not in data.columns:
        raise ValueError(f"rank_column is not available: {rank_column}")

    candidates = data[data["signal_before_rank"].fillna(False).astype(bool)].copy()
    if candidates.empty:
        data["signal"] = False
        return data

    candidates["_position"] = np.flatnonzero(data["signal_before_rank"].fillna(False).to_numpy())
    candidates["_signal_date"] = pd.to_datetime(candidates.index)
    if "symbol" in candidates.columns:
        candidates["_symbol_sort"] = candidates["symbol"].astype(str)
    else:
        candidates["_symbol_sort"] = ""
    candidates["_rank_value"] = pd.to_numeric(candidates[rank_column], errors="coerce").fillna(float("-inf"))
    candidates = candidates.sort_values(
        [
            "_signal_date",
            "_rank_value",
            "signal_quality_score",
            "model_probability",
            "scanner_score",
            "_symbol_sort",
        ],
        ascending=[True, False, False, False, False, True],
        kind="mergesort",
    )
    candidates["_signal_rank"] = candidates.groupby("_signal_date").cumcount() + 1

    rank_col = data.columns.get_loc("signal_rank")
    selected_col = data.columns.get_loc("signal_rank_selected")
    filter_col = data.columns.get_loc("signal_filter_reason")
    signal_col = data.columns.get_loc("signal")

    positions = candidates["_position"].astype(int).to_numpy()
    ranks = candidates["_signal_rank"].astype(int).to_numpy()
    selected = ranks <= max_signals_per_day

    data.iloc[positions, rank_col] = ranks
    data.iloc[positions, selected_col] = selected
    data.iloc[positions[~selected], filter_col] = f"daily_rank>{max_signals_per_day}"
    data.iloc[:, signal_col] = data["signal_before_rank"].fillna(False).to_numpy() & data[
        "signal_rank_selected"
    ].fillna(False).to_numpy()
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
    min_signal_quality_score: float | None,
) -> list[str]:
    suffixes: list[str] = []
    if min_relative_volume is not None:
        suffixes.append(f"relative_volume_20d>={min_relative_volume}")
    if max_distance_from_20d_high is not None:
        suffixes.append(f"distance_from_20d_high<={max_distance_from_20d_high}")
    if max_atr_pct is not None:
        suffixes.append(f"atr_pct<={max_atr_pct}")
    if min_signal_quality_score is not None:
        suffixes.append(f"signal_quality_score>={min_signal_quality_score}")
    return suffixes


def _numeric(data: pd.DataFrame, column: str) -> pd.Series:
    if column not in data.columns:
        return pd.Series(np.nan, index=data.index)
    return pd.to_numeric(data[column], errors="coerce")
