from __future__ import annotations

import pandas as pd

from src.backtest.execution import add_execution_columns, planned_trade_for_signal
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
