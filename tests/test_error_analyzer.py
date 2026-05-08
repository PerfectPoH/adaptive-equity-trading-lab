from __future__ import annotations

import pandas as pd

from src.analysis.error_analyzer import build_run_analysis


def test_run_analysis_summarizes_underperformance_and_skips() -> None:
    idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-02", "2024-01-03"])
    signals = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA", "BBB", "BBB"],
            "signal": [True, False, True, False],
            "execution_valid": [True, False, False, False],
            "execution_skip_reason": ["", "", "gap_too_large", ""],
            "model_probability": [0.7, 0.2, 0.8, 0.3],
            "scanner_score": [80, 20, 90, 30],
        },
        index=idx,
    )
    backtests = pd.DataFrame(
        [
            {"symbol": "AAA", "trades": 1, "strategy_return": 0.01, "buy_and_hold_return": 0.20, "excess_return": -0.19},
            {"symbol": "BBB", "trades": 0, "strategy_return": 0.00, "buy_and_hold_return": 0.10, "excess_return": -0.10},
        ]
    )

    analysis, summary = build_run_analysis(signals, backtests)

    assert list(analysis["symbol"]) == ["AAA", "BBB"]
    assert summary["total_signals"] == 2
    assert summary["total_executable_signals"] == 1
    assert summary["total_skipped_signals"] == 1
    assert summary["underperforming_symbols"] == 2
    assert summary["top_skip_reason"] == "gap_too_large"
