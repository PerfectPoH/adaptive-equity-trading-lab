from __future__ import annotations

import pandas as pd

from src.backtest.small_cap_execution import SmallCapExecutionConfig, add_small_cap_execution_columns


def _frame(**overrides: object) -> pd.DataFrame:
    data: dict[str, object] = {
        "Open": [10.0, 10.4, 10.5],
        "High": [10.2, 10.8, 10.9],
        "Low": [9.8, 10.2, 10.3],
        "Close": [10.0, 10.6, 10.7],
        "Volume": [1_000_000, 900_000, 800_000],
        "atr": [0.5, 0.5, 0.5],
        "avg_dollar_volume_20d": [8_000_000, 8_000_000, 8_000_000],
        "signal": [True, False, False],
    }
    data.update(overrides)
    return pd.DataFrame(data, index=pd.bdate_range("2024-01-01", periods=3))


def test_small_cap_execution_applies_conservative_entry_haircut() -> None:
    frame = _frame()
    config = SmallCapExecutionConfig(spread_bps=40, slippage_bps=60, risk_fraction=0.01)

    result = add_small_cap_execution_columns(frame, equity=100_000, config=config)

    assert result.iloc[0]["small_cap_execution_valid"] is True
    assert result.iloc[0]["small_cap_entry_reference_price"] == 10.4
    assert result.iloc[0]["small_cap_entry_price"] == 10.504
    assert result.iloc[0]["small_cap_execution_skip_reason"] == ""
    assert result.iloc[0]["small_cap_position_size"] > 0


def test_small_cap_execution_skips_extreme_next_open_gap() -> None:
    frame = _frame(Open=[10.0, 11.2, 11.3])

    result = add_small_cap_execution_columns(frame, equity=100_000)

    assert result.iloc[0]["small_cap_execution_valid"] is False
    assert result.iloc[0]["small_cap_execution_skip_reason"] == "gap_above_max"


def test_small_cap_execution_skips_when_dollar_volume_is_missing() -> None:
    frame = _frame()
    frame = frame.drop(columns=["avg_dollar_volume_20d"])

    result = add_small_cap_execution_columns(frame, equity=100_000)

    assert result.iloc[0]["small_cap_execution_valid"] is False
    assert result.iloc[0]["small_cap_execution_skip_reason"] == "missing_avg_dollar_volume_20d"


def test_small_cap_execution_skips_when_requested_notional_exceeds_liquidity_cap() -> None:
    frame = _frame(avg_dollar_volume_20d=[50_000, 50_000, 50_000])
    config = SmallCapExecutionConfig(max_position_dollar_volume_fraction=0.01, min_trade_notional=1_000)

    result = add_small_cap_execution_columns(frame, equity=100_000, config=config)

    assert result.iloc[0]["small_cap_execution_valid"] is False
    assert result.iloc[0]["small_cap_execution_skip_reason"] == "liquidity_cap_below_min_trade_notional"
    assert result.iloc[0]["small_cap_max_liquidity_notional"] == 500


def test_small_cap_execution_caps_position_by_dollar_volume() -> None:
    frame = _frame(avg_dollar_volume_20d=[200_000, 200_000, 200_000])
    config = SmallCapExecutionConfig(max_position_dollar_volume_fraction=0.01, min_trade_notional=1_000)

    result = add_small_cap_execution_columns(frame, equity=100_000, config=config)

    assert result.iloc[0]["small_cap_execution_valid"] is True
    assert result.iloc[0]["small_cap_position_notional"] <= 2_000
    assert result.iloc[0]["small_cap_position_size"] > 0


def test_small_cap_execution_fails_closed_on_no_next_open() -> None:
    frame = _frame(signal=[False, False, True])

    result = add_small_cap_execution_columns(frame, equity=100_000)

    assert result.iloc[2]["small_cap_execution_valid"] is False
    assert result.iloc[2]["small_cap_execution_skip_reason"] == "no_next_open"


def test_small_cap_execution_computes_impact_cost_with_volatility_proxy() -> None:
    frame = _frame(rolling_volatility_20d=[0.04, 0.04, 0.04])
    config = SmallCapExecutionConfig(
        spread_bps=0.0,
        slippage_bps=0.0,
        impact_coefficient_bps=50.0,
        risk_fraction=0.01,
    )

    result = add_small_cap_execution_columns(frame, equity=100_000, config=config)

    assert result.iloc[0]["small_cap_execution_valid"] is True
    assert result.iloc[0]["small_cap_impact_cost_pct"] > 0.0
    assert result.iloc[0]["small_cap_estimated_cost_pct"] == result.iloc[0]["small_cap_impact_cost_pct"]
