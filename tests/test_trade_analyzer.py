from __future__ import annotations

import pandas as pd

from src.analysis.trade_analyzer import build_trade_analysis


def test_trade_analysis_summarizes_by_symbol_and_worst_trade() -> None:
    trades = pd.DataFrame(
        [
            {"symbol": "AAA", "return_pct": 0.03, "pnl": 300, "signal_model_probability": 0.7, "signal_scanner_score": 80},
            {"symbol": "AAA", "return_pct": -0.01, "pnl": -100, "signal_model_probability": 0.6, "signal_scanner_score": 75},
            {"symbol": "BBB", "return_pct": -0.02, "pnl": -200, "signal_model_probability": 0.65, "signal_scanner_score": 90},
        ]
    )

    by_symbol, summary = build_trade_analysis(trades)

    assert summary["total_trades"] == 3
    assert summary["wins"] == 1
    assert summary["losses"] == 2
    assert summary["worst_trade"]["symbol"] == "BBB"
    assert set(by_symbol["symbol"]) == {"AAA", "BBB"}
