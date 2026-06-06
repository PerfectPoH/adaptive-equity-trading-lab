from pathlib import Path

import pandas as pd

from src.experiments.candidate_006_kronos_throttle import (
    apply_fixed_half_size_throttle,
    random_same_reduced_count_baseline,
    run_candidate_006_kronos_throttle,
)


def test_apply_fixed_half_size_throttle_reduces_negative_forecast_weight_only():
    log = pd.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "exit_date": ["2025-01-02", "2025-01-03", "2025-01-04"],
            "net_return": [0.10, -0.05, 0.08],
            "weighted_net_return": [0.010, -0.005, 0.008],
            "overlay_weighted_net_return": [0.010, 0.0, 0.0],
            "kronos_forecast_return_median": [0.01, -0.02, 0.0],
            "kronos_keep_trade": [True, False, False],
        }
    )

    throttled = apply_fixed_half_size_throttle(log)

    assert throttled["throttle_weight_multiplier"].tolist() == [1.0, 0.5, 0.5]
    assert throttled["throttle_weighted_net_return"].tolist() == [0.010, -0.0025, 0.004]
    assert throttled["binary_overlay_weighted_net_return"].tolist() == [0.010, 0.0, 0.0]


def test_random_same_reduced_count_baseline_is_deterministic():
    log = pd.DataFrame(
        {
            "symbol": ["A", "B", "C", "D"],
            "exit_date": ["2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"],
            "net_return": [0.10, -0.05, 0.08, -0.02],
            "weighted_net_return": [0.010, -0.005, 0.008, -0.002],
            "overlay_weighted_net_return": [0.010, 0.0, 0.008, 0.0],
            "kronos_forecast_return_median": [0.01, -0.02, 0.03, -0.01],
            "kronos_keep_trade": [True, False, True, False],
        }
    )
    throttled = apply_fixed_half_size_throttle(log)

    first = random_same_reduced_count_baseline(
        throttled,
        reduced_count=2,
        observed_weighted_net_sum=0.0145,
        iterations=100,
        seed=11,
    )
    second = random_same_reduced_count_baseline(
        throttled,
        reduced_count=2,
        observed_weighted_net_sum=0.0145,
        iterations=100,
        seed=11,
    )

    assert first["summary"] == second["summary"]
    assert first["summary"]["iterations"] == 100
    assert len(first["trials"]) == 100
    assert 0.0 <= first["summary"]["observed_net_percentile"] <= 1.0


def test_run_candidate_006_kronos_throttle_writes_diagnostic_artifacts(tmp_path):
    gate_dir = tmp_path / "gate"
    gate_dir.mkdir()
    (gate_dir / "gate_manifest.json").write_text(
        """{
  "status": "APPROVED_KRONOS_FIXED_HALF_SIZE_THROTTLE_DIAGNOSTIC_ONLY",
  "promotion_allowed": false,
  "paper_trading_allowed": false,
  "live_trading_allowed": false,
  "throttle_rule": {
    "feature": "kronos_forecast_return_median",
    "operator": ">",
    "threshold": 0.0,
    "positive_forecast_weight_multiplier": 1.0,
    "non_positive_forecast_weight_multiplier": 0.5,
    "weight_redistribution_allowed": false,
    "threshold_sweep_allowed": false,
    "multiplier_sweep_allowed": false,
    "rerank_allowed": false
  },
  "random_baseline": {"seed": 4, "iterations": 50, "same_reduced_trade_count": true},
  "forbidden_actions": ["run new Kronos inference", "query providers", "download market data"]
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
            "kronos_forecast_return_median": [0.01, -0.02, 0.03],
            "kronos_keep_trade": [True, False, True],
        }
    ).to_csv(log_path, index=False)
    output_dir = tmp_path / "out"

    result = run_candidate_006_kronos_throttle(
        gate_dir=gate_dir,
        output_dir=output_dir,
        overlay_trade_log_path=log_path,
    )

    assert result["decision"] == "CANDIDATE_006_KRONOS_THROTTLE_COMPLETE_NO_PROMOTION"
    assert result["provider_query_performed"] is False
    assert result["new_kronos_inference_performed"] is False
    assert result["threshold_optimization_performed"] is False
    assert (output_dir / "kronos_throttle_result.json").exists()
    assert (output_dir / "kronos_throttle_trade_log.csv").exists()
    assert (output_dir / "random_same_reduced_count_baseline.csv").exists()
