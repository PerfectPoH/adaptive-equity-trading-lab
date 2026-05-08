from __future__ import annotations

import pandas as pd

from src.strategy.signal_engine import add_signal_columns, apply_daily_signal_rank_filter


def make_signal_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "scanner_score": [80, 80, 80],
            "model_probability": [0.60, 0.60, 0.60],
            "spy_trend_positive": [True, True, True],
            "relative_volume_20d": [1.2, 0.8, 1.3],
            "distance_from_20d_high": [-0.03, -0.03, -0.005],
            "atr_pct": [0.02, 0.02, 0.04],
        }
    )


def test_add_signal_columns_applies_optional_regime_filters() -> None:
    result = add_signal_columns(
        make_signal_frame(),
        min_model_probability=0.55,
        min_relative_volume=1.0,
        max_distance_from_20d_high=-0.021,
        max_atr_pct=0.0315,
    )

    assert result["signal"].tolist() == [True, False, False]
    assert "relative_volume_20d>=1.0" in result.loc[0, "signal_reason"]


def test_add_signal_columns_keeps_default_behavior_without_regime_filters() -> None:
    result = add_signal_columns(make_signal_frame(), min_model_probability=0.55)

    assert result["signal"].tolist() == [True, True, True]


def test_add_signal_columns_can_filter_by_quality_score() -> None:
    frame = make_signal_frame()
    frame["model_probability"] = [0.70, 0.26, 0.25]

    result = add_signal_columns(
        frame,
        min_model_probability=0.20,
        min_signal_quality_score=0.55,
    )

    assert result["signal"].tolist() == [True, False, False]
    assert "signal_quality_score>=0.55" in result.loc[0, "signal_reason"]


def test_apply_daily_signal_rank_filter_keeps_top_n_per_day() -> None:
    idx = pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-02", "2024-01-03"])
    frame = make_signal_frame()
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    frame.index = idx
    frame["symbol"] = ["AAA", "BBB", "CCC", "DDD"]
    frame["model_probability"] = [0.50, 0.80, 0.70, 0.40]
    signaled = add_signal_columns(frame, min_model_probability=0.20)

    ranked = apply_daily_signal_rank_filter(signaled, max_signals_per_day=2)

    first_day = ranked.loc[pd.Timestamp("2024-01-02")]
    assert first_day["signal_before_rank"].tolist() == [True, True, True]
    assert first_day["signal"].tolist() == [False, True, True]
    assert first_day["signal_rank"].tolist() == [3, 1, 2]
    assert bool(ranked.loc[pd.Timestamp("2024-01-03"), "signal"]) is True


def test_apply_daily_signal_rank_filter_can_rank_by_model_probability() -> None:
    idx = pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-02"])
    frame = make_signal_frame()
    frame.index = idx
    frame["symbol"] = ["AAA", "BBB", "CCC"]
    frame["model_probability"] = [0.30, 0.80, 0.70]
    frame["relative_volume_20d"] = [4.0, 1.0, 1.0]
    signaled = add_signal_columns(frame, min_model_probability=0.20)

    ranked = apply_daily_signal_rank_filter(
        signaled,
        max_signals_per_day=1,
        rank_column="model_probability",
    )

    assert ranked["signal"].tolist() == [False, True, False]
    assert ranked["signal_rank"].tolist() == [3, 1, 2]
