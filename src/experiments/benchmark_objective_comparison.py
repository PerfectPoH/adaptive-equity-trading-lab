from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.experiments.walk_forward_validation import ModelObjectiveConfig, run_walk_forward_validation


OUTPUT_JSON = Path("experiments/benchmark_objective_comparison_latest.json")
OUTPUT_CSV = Path("experiments/benchmark_objective_comparison_latest.csv")
MODEL_OBJECTIVE_CONFIGS = (
    ModelObjectiveConfig(name="tp_before_sl", label_column="label"),
    ModelObjectiveConfig(name="trade_positive", label_column="label_trade_positive"),
    ModelObjectiveConfig(name="beats_horizon_return", label_column="label_beats_horizon_return"),
    ModelObjectiveConfig(name="tp_and_beats_horizon", label_column="label_tp_and_beats_horizon"),
)


def run_benchmark_objective_comparison() -> dict[str, Any]:
    return run_walk_forward_validation(
        model_objective_configs=MODEL_OBJECTIVE_CONFIGS,
        model_types=("random_forest",),
        min_validation_trades=30,
        output_json=OUTPUT_JSON,
        output_csv=OUTPUT_CSV,
    )


if __name__ == "__main__":
    result = run_benchmark_objective_comparison()
    print(json.dumps(result["summary"], indent=2))
