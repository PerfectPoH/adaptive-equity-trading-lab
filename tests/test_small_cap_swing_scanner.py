from __future__ import annotations

import pandas as pd

from src.scanner.small_cap_swing_scanner import SmallCapSwingScannerConfig, add_small_cap_swing_scanner_columns


def test_small_cap_swing_scanner_detects_panic_reversal() -> None:
    frame = pd.DataFrame(
        {
            "Open": [8.8],
            "High": [9.8],
            "Low": [8.0],
            "Close": [9.6],
            "previous_close": [10.0],
            "rolling_return_5d": [-0.18],
            "relative_volume_20d": [2.2],
            "atr_pct": [0.08],
        }
    )

    result = add_small_cap_swing_scanner_columns(frame)

    assert result.iloc[0]["small_cap_scanner_pass"] is True
    assert result.iloc[0]["small_cap_setup"] == "panic_reversal"
    assert "panic_reversal" in result.iloc[0]["small_cap_scanner_reason"]


def test_small_cap_swing_scanner_detects_breakout_continuation() -> None:
    frame = pd.DataFrame(
        {
            "Open": [10.0],
            "High": [11.2],
            "Low": [9.8],
            "Close": [11.1],
            "previous_close": [10.1],
            "relative_volume_20d": [2.0],
            "atr_pct": [0.06],
            "distance_from_20d_high": [0.0],
            "rolling_volatility_20d": [0.035],
        }
    )

    result = add_small_cap_swing_scanner_columns(frame)

    assert result.iloc[0]["small_cap_scanner_pass"] is True
    assert result.iloc[0]["small_cap_setup"] == "breakout_continuation"
    assert result.iloc[0]["small_cap_scanner_score"] >= 70


def test_small_cap_swing_scanner_detects_post_gap_drift() -> None:
    frame = pd.DataFrame(
        {
            "Open": [10.6],
            "High": [11.4],
            "Low": [10.5],
            "Close": [11.3],
            "previous_close": [10.0],
            "relative_volume_20d": [1.8],
            "atr_pct": [0.07],
        }
    )

    result = add_small_cap_swing_scanner_columns(frame)

    assert result.iloc[0]["small_cap_scanner_pass"] is True
    assert result.iloc[0]["small_cap_setup"] == "post_gap_drift"
    assert "post_gap_drift" in result.iloc[0]["small_cap_scanner_reason"]


def test_small_cap_swing_scanner_blocks_extreme_gap() -> None:
    frame = pd.DataFrame(
        {
            "Open": [11.5],
            "High": [11.8],
            "Low": [11.2],
            "Close": [11.7],
            "previous_close": [10.0],
            "relative_volume_20d": [2.0],
            "atr_pct": [0.05],
            "distance_from_20d_high": [0.0],
            "rolling_volatility_20d": [0.03],
        }
    )

    result = add_small_cap_swing_scanner_columns(frame)

    assert result.iloc[0]["small_cap_scanner_pass"] is False
    assert "gap_above_max" in result.iloc[0]["small_cap_scanner_reject_reason"]


def test_small_cap_swing_scanner_fails_closed_on_missing_required_fields() -> None:
    frame = pd.DataFrame({"Close": [10.0], "relative_volume_20d": [2.0]})

    result = add_small_cap_swing_scanner_columns(frame)

    assert result.iloc[0]["small_cap_scanner_pass"] is False
    assert "missing_Open" in result.iloc[0]["small_cap_scanner_reject_reason"]
    assert "missing_High" in result.iloc[0]["small_cap_scanner_reject_reason"]
    assert "missing_Low" in result.iloc[0]["small_cap_scanner_reject_reason"]


def test_small_cap_swing_scanner_config_can_tighten_volume() -> None:
    frame = pd.DataFrame(
        {
            "Open": [10.6],
            "High": [11.4],
            "Low": [10.5],
            "Close": [11.3],
            "previous_close": [10.0],
            "relative_volume_20d": [1.8],
            "atr_pct": [0.07],
        }
    )
    config = SmallCapSwingScannerConfig(min_relative_volume=2.5)

    result = add_small_cap_swing_scanner_columns(frame, config=config)

    assert result.iloc[0]["small_cap_scanner_pass"] is False
    assert "relative_volume_below_min" in result.iloc[0]["small_cap_scanner_reject_reason"]
