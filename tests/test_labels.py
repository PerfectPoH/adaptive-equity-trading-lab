from __future__ import annotations

import pandas as pd

from src.models.label_builder import build_trade_labels


def base_frame() -> pd.DataFrame:
    idx = pd.bdate_range("2024-01-01", periods=6)
    return pd.DataFrame(
        {
            "Open": [100, 100, 100, 100, 100, 100],
            "High": [101, 101, 107, 101, 101, 101],
            "Low": [99, 99, 99, 99, 99, 99],
            "Close": [100, 100, 100, 100, 100, 100],
            "Volume": [1_000_000] * 6,
            "atr": [2] * 6,
        },
        index=idx,
    )


def test_label_is_one_when_take_profit_hits_before_stop() -> None:
    labeled = build_trade_labels(base_frame(), timeout_bars=3, max_gap_threshold=0.20)
    assert labeled["label"].iloc[0] == 1
    assert bool(labeled["label_executable"].iloc[0]) is True


def test_label_is_zero_when_stop_hits_first() -> None:
    frame = base_frame()
    frame.loc[frame.index[2], "High"] = 101
    frame.loc[frame.index[2], "Low"] = 96
    labeled = build_trade_labels(frame, timeout_bars=3, max_gap_threshold=0.20)
    assert labeled["label"].iloc[0] == 0


def test_same_day_stop_and_take_profit_is_conservative_zero() -> None:
    frame = base_frame()
    frame.loc[frame.index[2], "High"] = 107
    frame.loc[frame.index[2], "Low"] = 96
    labeled = build_trade_labels(frame, timeout_bars=3, max_gap_threshold=0.20)
    assert labeled["label"].iloc[0] == 0


def test_entry_bar_exit_touch_skips_label() -> None:
    frame = base_frame()
    frame.loc[frame.index[1], "High"] = 107
    labeled = build_trade_labels(frame, timeout_bars=3, max_gap_threshold=0.20)

    assert pd.isna(labeled["label"].iloc[0])
    assert bool(labeled["label_executable"].iloc[0]) is False
    assert labeled["label_skip_reason"].iloc[0] == "entry_bar_exit_touch"


def test_large_gap_skips_label() -> None:
    frame = base_frame()
    frame.loc[frame.index[1], "Open"] = 120
    labeled = build_trade_labels(frame, timeout_bars=3, max_gap_threshold=0.05)
    assert pd.isna(labeled["label"].iloc[0])
    assert bool(labeled["label_executable"].iloc[0]) is False
    assert labeled["label_skip_reason"].iloc[0] == "gap_too_large"
