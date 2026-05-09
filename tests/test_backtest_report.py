from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.analysis.backtest_report import build_backtest_report, write_backtest_report_markdown


def test_build_backtest_report_highlights_underperformance_and_worst_symbol(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_001"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "aggregate_backtest": {
                    "strategy_return": 0.05,
                    "buy_and_hold_return": 0.48,
                    "excess_return": -0.43,
                    "trades": 10,
                },
                "trade_analysis_summary": {"total_trades": 10, "win_rate": 0.4},
                "feature_regime_summary": {"primary_findings": ["Losses had higher volatility."]},
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {"symbol": "AAA", "strategy_return": 0.02, "buy_and_hold_return": 0.20, "excess_return": -0.18, "trades": 4},
            {"symbol": "BBB", "strategy_return": -0.03, "buy_and_hold_return": 0.10, "excess_return": -0.13, "trades": 6},
        ]
    ).to_csv(run_dir / "backtests.csv", index=False)
    pd.DataFrame(
        [
            {"symbol": "AAA", "trades": 4, "avg_return_pct": 0.01, "win_rate": 0.5},
            {"symbol": "BBB", "trades": 6, "avg_return_pct": -0.02, "win_rate": 0.33},
        ]
    ).to_csv(run_dir / "trade_analysis_by_symbol.csv", index=False)

    report = build_backtest_report(run_dir)

    assert report["run_id"] == "run_001"
    assert report["verdict"] == "underperforming_buy_and_hold"
    assert report["aggregate"]["excess_return"] == -0.43
    assert report["worst_symbols"][0]["symbol"] == "AAA"
    assert report["trade_summary"]["win_rate"] == 0.4
    assert report["primary_findings"] == ["Losses had higher volatility."]


def test_write_backtest_report_markdown_includes_decision(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    run_dir.mkdir()
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "aggregate_backtest": {"strategy_return": 0.1, "buy_and_hold_return": 0.2, "excess_return": -0.1},
                "trade_analysis_summary": {"total_trades": 3, "win_rate": 0.33},
                "feature_regime_summary": {"primary_findings": []},
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame([{"symbol": "AAA", "strategy_return": 0.1, "buy_and_hold_return": 0.2, "excess_return": -0.1}]).to_csv(
        run_dir / "backtests.csv", index=False
    )
    pd.DataFrame().to_csv(run_dir / "trade_analysis_by_symbol.csv", index=False)
    output_path = tmp_path / "report.md"

    write_backtest_report_markdown(run_dir, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "# Backtest Analysis" in content
    assert "underperforming_buy_and_hold" in content
    assert "Non promuovere la strategia" in content
