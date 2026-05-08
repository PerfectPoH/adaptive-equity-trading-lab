from __future__ import annotations

import pandas as pd

from src.backtest.execution import add_execution_columns, planned_trade_for_signal
from src.backtest.runner import run_backtest
from src.models.label_builder import build_trade_labels


def test_signal_on_bar_two_executes_on_bar_three_next_open() -> None:
    idx = pd.bdate_range("2024-01-01", periods=5)
    frame = pd.DataFrame(
        {
            "Open": [100, 101, 102, 103, 104],
            "High": [101, 102, 103, 104, 105],
            "Low": [99, 100, 101, 102, 103],
            "Close": [100, 101, 102, 103, 104],
            "Volume": [1_000_000] * 5,
            "atr": [2] * 5,
            "signal": [False, False, True, False, False],
        },
        index=idx,
    )
    labeled = build_trade_labels(frame, max_gap_threshold=0.10)
    executed = add_execution_columns(labeled, equity=100_000, max_gap_threshold=0.10)
    plan = planned_trade_for_signal(executed, 2)

    assert plan["valid"] is True
    assert plan["signal_date"] == idx[2]
    assert plan["entry_date"] == idx[3]
    assert plan["entry_price"] == 103
    assert plan["position_size"] > 0


def test_entry_bar_exit_touch_skips_execution() -> None:
    idx = pd.bdate_range("2024-01-01", periods=5)
    frame = pd.DataFrame(
        {
            "Open": [100, 101, 102, 103, 104],
            "High": [101, 102, 110, 104, 105],
            "Low": [99, 100, 101, 102, 103],
            "Close": [100, 101, 102, 103, 104],
            "Volume": [1_000_000] * 5,
            "atr": [2] * 5,
            "signal": [False, True, False, False, False],
        },
        index=idx,
    )
    labeled = build_trade_labels(frame, max_gap_threshold=0.10)
    executed = add_execution_columns(labeled, equity=100_000, max_gap_threshold=0.10)
    plan = planned_trade_for_signal(executed, 1)

    assert plan["valid"] is False
    assert plan["skip_reason"] == "entry_bar_exit_touch"


def test_backtest_fills_precomputed_signal_at_next_open() -> None:
    idx = pd.bdate_range("2024-01-01", periods=8)
    frame = pd.DataFrame(
        {
            "Open": [100, 101, 150, 151, 152, 153, 154, 155],
            "High": [101, 102, 151, 151, 160, 161, 162, 163],
            "Low": [99, 100, 149, 150, 151, 152, 153, 154],
            "Close": [100, 101, 149, 151, 152, 153, 154, 155],
            "Volume": [1_000_000] * 8,
            "atr": [2] * 8,
            "signal": [False, True, False, False, False, False, False, False],
        },
        index=idx,
    )

    labeled = build_trade_labels(frame, max_gap_threshold=1.0)
    executed = add_execution_columns(labeled, equity=100_000, max_gap_threshold=1.0)
    stats, _summary = run_backtest(executed)
    trades = stats["_trades"]

    assert len(trades) == 1
    assert int(trades.iloc[0]["EntryBar"]) == 2
    assert trades.iloc[0]["EntryTime"] == idx[2]
    assert trades.iloc[0]["EntryPrice"] == 150


def test_backtest_closes_trade_after_timeout_window() -> None:
    idx = pd.bdate_range("2024-01-01", periods=8)
    frame = pd.DataFrame(
        {
            "Open": [100, 101, 102, 103, 104, 105, 106, 107],
            "High": [101, 102, 103, 104, 105, 106, 107, 108],
            "Low": [99, 100, 101, 102, 103, 104, 105, 106],
            "Close": [100, 101, 102, 103, 104, 105, 106, 107],
            "Volume": [1_000_000] * 8,
            "atr": [20] * 8,
            "signal": [False, True, False, False, False, False, False, False],
        },
        index=idx,
    )

    labeled = build_trade_labels(frame, timeout_bars=3, max_gap_threshold=0.10)
    executed = add_execution_columns(labeled, equity=100_000, max_gap_threshold=0.10)
    stats, _summary = run_backtest(executed, timeout_bars=3)
    trades = stats["_trades"]

    assert len(trades) == 1
    assert int(trades.iloc[0]["EntryBar"]) == 2
    assert int(trades.iloc[0]["ExitBar"]) == 5


def test_execution_uses_row_level_risk_fraction_when_available() -> None:
    idx = pd.bdate_range("2024-01-01", periods=5)
    frame = pd.DataFrame(
        {
            "Open": [100, 101, 102, 103, 104],
            "High": [101, 102, 103, 104, 105],
            "Low": [99, 100, 101, 102, 103],
            "Close": [100, 101, 102, 103, 104],
            "Volume": [1_000_000] * 5,
            "atr": [2] * 5,
            "signal": [False, False, True, False, False],
            "risk_fraction": [0.01, 0.01, 0.02, 0.01, 0.01],
        },
        index=idx,
    )

    labeled = build_trade_labels(frame, max_gap_threshold=0.10)
    executed = add_execution_columns(labeled, equity=100_000, risk_fraction=0.01, max_gap_threshold=0.10)
    plan = planned_trade_for_signal(executed, 2)

    assert plan["valid"] is True
    assert plan["risk_fraction_used"] == 0.02
    assert plan["position_size"] == 666
