from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis.small_cap_backtest_report import build_small_cap_backtest_report, write_small_cap_backtest_report_markdown


def _candidate_export() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of": "2024-01-01",
                "symbol": "AAA",
                "operational_candidate": True,
                "small_cap_setup": "breakout_continuation",
                "market_regime_trade_allowed": True,
                "market_regime_block_reason": "",
                "small_cap_execution_valid": True,
                "small_cap_execution_skip_reason": "",
                "small_cap_position_notional": 1_000.0,
            },
            {
                "as_of": "2024-01-01",
                "symbol": "BBB",
                "operational_candidate": False,
                "small_cap_setup": "",
                "market_regime_trade_allowed": False,
                "market_regime_block_reason": "vix_above_max",
                "small_cap_execution_valid": False,
                "small_cap_execution_skip_reason": "",
                "small_cap_position_notional": 0.0,
            },
            {
                "as_of": "2024-01-02",
                "symbol": "CCC",
                "operational_candidate": False,
                "small_cap_setup": "post_gap_drift",
                "market_regime_trade_allowed": True,
                "market_regime_block_reason": "",
                "small_cap_execution_valid": False,
                "small_cap_execution_skip_reason": "gap_above_max",
                "small_cap_position_notional": 0.0,
            },
        ]
    )


def _benchmark_report() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"benchmark": "cash_flat", "return": 0.0, "observations": 2, "description": "Cash"},
            {"benchmark": "iwm_proxy", "return": 0.03, "observations": 1, "description": "IWM"},
            {"benchmark": "equal_weight_universe", "return": 0.04, "observations": 3, "description": "Universe"},
            {"benchmark": "random_entry_baseline", "return": 0.02, "observations": 3, "description": "Random"},
            {"benchmark": "ticker_holding_window", "return": 0.08, "observations": 1, "description": "Candidates"},
        ]
    )


def test_build_small_cap_backtest_report_summarizes_candidates_and_verdict() -> None:
    report = build_small_cap_backtest_report(_candidate_export(), _benchmark_report())

    assert report["verdict"] == "beats_primary_benchmark"
    assert report["candidate_summary"] == {
        "rows": 3,
        "operational_candidates": 1,
        "unique_symbols": 3,
        "candidate_dates": 2,
        "conversion_rate": 1 / 3,
        "total_position_notional": 1_000.0,
    }
    assert report["primary_benchmark"] == "equal_weight_universe"
    assert report["strategy_proxy_return"] == 0.08
    assert report["primary_benchmark_return"] == 0.04
    assert report["excess_return"] == 0.04


def test_build_small_cap_backtest_report_includes_diagnostics() -> None:
    report = build_small_cap_backtest_report(_candidate_export(), _benchmark_report())

    assert report["setup_counts"] == {"breakout_continuation": 1}
    assert report["regime_block_reasons"] == {"vix_above_max": 1}
    assert report["execution_skip_reasons"] == {"gap_above_max": 1}


def test_build_small_cap_backtest_report_handles_insufficient_benchmark_data() -> None:
    benchmark_report = pd.DataFrame(
        [
            {"benchmark": "ticker_holding_window", "return": float("nan"), "observations": 0, "description": "Candidates"},
            {"benchmark": "equal_weight_universe", "return": float("nan"), "observations": 0, "description": "Universe"},
        ]
    )

    report = build_small_cap_backtest_report(_candidate_export(), benchmark_report)

    assert report["verdict"] == "insufficient_data"
    assert report["decision"].startswith("Non promuovere")


def test_write_small_cap_backtest_report_markdown_includes_verdict(tmp_path: Path) -> None:
    output_path = tmp_path / "small_cap_report.md"

    report = write_small_cap_backtest_report_markdown(_candidate_export(), _benchmark_report(), output_path)

    content = output_path.read_text(encoding="utf-8")
    assert report["verdict"] == "beats_primary_benchmark"
    assert "# Small-Cap Backtest Report" in content
    assert "beats_primary_benchmark" in content
    assert "equal_weight_universe" in content
    assert "gap_above_max" in content
