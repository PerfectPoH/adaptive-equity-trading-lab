from __future__ import annotations

import pandas as pd

from src.analysis.error_analyzer import build_run_analysis, build_signal_diagnostics


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


def test_signal_diagnostics_identifies_scanner_and_model_bottlenecks() -> None:
    idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-02", "2024-01-03"])
    signals = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA", "BBB", "BBB"],
            "scanner_score": [80, 85, 20, 30],
            "model_probability": [0.30, 0.40, 0.80, 0.85],
            "spy_trend_positive": [True, True, True, True],
            "signal": [False, False, False, False],
        },
        index=idx,
    )

    diagnostics, summary = build_signal_diagnostics(signals)

    bottlenecks = dict(zip(diagnostics["symbol"], diagnostics["bottleneck"], strict=True))
    assert bottlenecks["AAA"] == "model_probability_filter"
    assert bottlenecks["BBB"] == "scanner_filter"
    assert summary["symbols_with_scanner_pass"] == 1
    assert summary["symbols_with_model_pass"] == 1
