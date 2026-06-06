from pathlib import Path

import pandas as pd

from src.experiments.candidate_006_kronos_overlay_attribution import (
    compute_kept_rejected_attribution,
    random_same_count_baseline,
    run_candidate_006_kronos_overlay_attribution,
)


def test_compute_kept_rejected_attribution_separates_quality():
    log = pd.DataFrame(
        {
            "symbol": ["A", "B", "C", "D"],
            "exit_date": ["2025-01-02", "2025-01-02", "2025-01-03", "2025-01-03"],
            "net_return": [0.10, -0.05, 0.08, -0.12],
            "weighted_net_return": [0.010, -0.005, 0.008, -0.012],
            "overlay_weighted_net_return": [0.010, 0.0, 0.008, 0.0],
            "kronos_keep_trade": [True, False, True, False],
        }
    )

    attribution = compute_kept_rejected_attribution(log)

    assert attribution["kept_trade_count"] == 2
    assert attribution["rejected_trade_count"] == 2
    assert attribution["kept_win_rate"] == 1.0
    assert attribution["rejected_win_rate"] == 0.0
    assert attribution["winner_capture_rate"] == 1.0
    assert attribution["loser_rejection_rate"] == 1.0
    assert attribution["overlay_minus_baseline_weighted_net_return"] == 0.017


def test_random_same_count_baseline_is_deterministic_and_scores_observed():
    log = pd.DataFrame(
        {
            "symbol": ["A", "B", "C", "D", "E"],
            "exit_date": ["2025-01-02", "2025-01-02", "2025-01-03", "2025-01-03", "2025-01-04"],
            "net_return": [0.10, -0.05, 0.08, -0.12, -0.02],
            "weighted_net_return": [0.010, -0.005, 0.008, -0.012, -0.002],
            "overlay_weighted_net_return": [0.010, 0.0, 0.008, 0.0, 0.0],
            "kronos_keep_trade": [True, False, True, False, False],
        }
    )

    first = random_same_count_baseline(log, kept_count=2, observed_weighted_net_sum=0.018, iterations=100, seed=7)
    second = random_same_count_baseline(log, kept_count=2, observed_weighted_net_sum=0.018, iterations=100, seed=7)

    assert first["summary"] == second["summary"]
    assert first["summary"]["iterations"] == 100
    assert first["summary"]["observed_weighted_net_sum"] == 0.018
    assert 0.0 <= first["summary"]["observed_net_percentile"] <= 1.0
    assert len(first["trials"]) == 100


def test_run_candidate_006_kronos_overlay_attribution_writes_artifacts(tmp_path):
    gate_dir = tmp_path / "gate"
    gate_dir.mkdir()
    (gate_dir / "gate_manifest.json").write_text(
        """{
  "status": "APPROVED_KRONOS_OVERLAY_ATTRIBUTION_DIAGNOSTIC_ONLY",
  "promotion_allowed": false,
  "paper_trading_allowed": false,
  "live_trading_allowed": false,
  "random_baseline": {"seed": 3, "iterations": 50, "same_kept_trade_count": true},
  "forbidden_actions": ["query providers", "run new Kronos inference", "download market data"]
}""",
        encoding="utf-8",
    )
    log_path = tmp_path / "overlay_trade_log.csv"
    pd.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "exit_date": ["2025-01-02", "2025-01-03", "2025-01-04"],
            "net_return": [0.10, -0.05, 0.08],
            "weighted_net_return": [0.010, -0.005, 0.008],
            "overlay_weighted_net_return": [0.010, 0.0, 0.008],
            "kronos_keep_trade": [True, False, True],
        }
    ).to_csv(log_path, index=False)
    output_dir = tmp_path / "out"

    result = run_candidate_006_kronos_overlay_attribution(
        gate_dir=gate_dir,
        output_dir=output_dir,
        overlay_trade_log_path=log_path,
    )

    assert result["decision"] == "CANDIDATE_006_KRONOS_OVERLAY_ATTRIBUTION_COMPLETE_NO_PROMOTION"
    assert result["provider_query_performed"] is False
    assert result["new_kronos_inference_performed"] is False
    assert result["strategy_backtest_performed"] is False
    assert (output_dir / "kronos_overlay_attribution_result.json").exists()
    assert (output_dir / "random_same_count_baseline.csv").exists()
    assert (output_dir / "final_decision.json").exists()
