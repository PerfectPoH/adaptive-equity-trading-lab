from __future__ import annotations

import pandas as pd

from src.features.feature_pipeline import build_features


def make_price_frame(rows: int = 80) -> pd.DataFrame:
    idx = pd.bdate_range("2024-01-01", periods=rows)
    close = pd.Series(range(100, 100 + rows), index=idx, dtype=float)
    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 1_000_000 + close * 100,
        },
        index=idx,
    )


def test_feature_pipeline_is_point_in_time_when_future_changes() -> None:
    original = make_price_frame()
    mutated = original.copy()
    cutoff = original.index[45]
    mutated.loc[mutated.index > cutoff, ["Open", "High", "Low", "Close"]] *= 100
    mutated.loc[mutated.index > cutoff, "Volume"] *= 10

    original_features = build_features(original)
    mutated_features = build_features(mutated)

    columns = ["ema_20_ratio", "ema_50_ratio", "atr", "relative_volume_20d", "distance_from_20d_high"]
    pd.testing.assert_frame_equal(
        original_features.loc[:cutoff, columns],
        mutated_features.loc[:cutoff, columns],
        check_exact=False,
        rtol=1e-12,
        atol=1e-12,
    )
