from __future__ import annotations

import pandas as pd

from src.strategy.signal_engine import add_signal_columns


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
