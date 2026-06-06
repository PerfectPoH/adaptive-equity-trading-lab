from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments import candidate_006_kronos_overlay_readiness as readiness


def _gate(path: Path) -> None:
    path.mkdir()
    payload = {
        "status": "APPROVED_KRONOS_OVERLAY_READINESS_DIAGNOSTIC_ONLY",
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "coverage_contract": {
            "minimum_symbols_covered_ratio": 0.8,
            "minimum_trade_rows_covered_ratio": 0.8,
            "minimum_rebalance_dates_covered_ratio": 0.8,
            "minimum_unique_symbols": 3,
            "minimum_unique_signal_dates": 2,
            "single_symbol_smoke_is_never_sufficient": True,
        },
    }
    (path / "gate_manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def test_overlay_coverage_blocks_single_symbol_smoke() -> None:
    trades = pd.DataFrame(
        [
            {"symbol": "AAA", "signal_date": "2026-01-02"},
            {"symbol": "BBB", "signal_date": "2026-01-02"},
            {"symbol": "CCC", "signal_date": "2026-01-05"},
        ]
    )
    feature_rows = [{"symbol": "SPY", "as_of_date": "2026-01-02", "kronos_probability_up": 0.4}]
    coverage = readiness.compute_overlay_coverage(trades, feature_rows)

    assert coverage["unique_trade_symbols"] == 3
    assert coverage["unique_feature_symbols"] == 1
    assert coverage["symbols_covered_ratio"] == 0.0
    assert coverage["trade_rows_covered_ratio"] == 0.0


def test_readiness_run_is_no_backtest_and_no_promotion(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    _gate(gate_dir)
    trade_path = tmp_path / "trade_log.csv"
    pd.DataFrame(
        [
            {"symbol": "AAA", "signal_date": "2026-01-02"},
            {"symbol": "BBB", "signal_date": "2026-01-02"},
            {"symbol": "CCC", "signal_date": "2026-01-05"},
        ]
    ).to_csv(trade_path, index=False)
    smoke_path = tmp_path / "kronos_smoke_result.json"
    smoke_path.write_text(
        json.dumps(
            {
                "decision": "CANDIDATE_006_KRONOS_INFERENCE_SMOKE_COMPLETE_NO_BACKTEST",
                "feature_summary": {"kronos_probability_up": 0.0},
                "inference_performed": True,
            }
        ),
        encoding="utf-8",
    )

    result = readiness.run_candidate_006_kronos_overlay_readiness(
        gate_dir=gate_dir,
        output_dir=tmp_path / "out",
        trade_log_path=trade_path,
        kronos_smoke_result_path=smoke_path,
    )

    assert result["decision"] == "CANDIDATE_006_KRONOS_OVERLAY_READINESS_BLOCKED_INSUFFICIENT_FEATURE_COVERAGE"
    assert result["portfolio_backtest_performed"] is False
    assert result["new_kronos_inference_performed"] is False
    assert result["promotion_allowed"] is False
    assert "kronos_feature_coverage_below_contract" in result["blockers"]
    assert (tmp_path / "out" / "kronos_overlay_readiness_result.json").is_file()
