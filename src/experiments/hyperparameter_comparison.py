from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.experiments.walk_forward_validation import ModelConfig, run_walk_forward_validation


OUTPUT_JSON = Path("experiments/hyperparameter_comparison_latest.json")
OUTPUT_CSV = Path("experiments/hyperparameter_comparison_latest.csv")
MODEL_CONFIGS = (
    ModelConfig(name="random_forest_default", model_type="random_forest"),
    ModelConfig(
        name="random_forest_shallow",
        model_type="random_forest",
        model_params={"max_depth": 4, "min_samples_leaf": 30},
    ),
    ModelConfig(
        name="random_forest_deeper",
        model_type="random_forest",
        model_params={"max_depth": 8, "min_samples_leaf": 15},
    ),
)


def run_hyperparameter_comparison() -> dict[str, Any]:
    return run_walk_forward_validation(
        model_configs=MODEL_CONFIGS,
        min_validation_trades=30,
        output_json=OUTPUT_JSON,
        output_csv=OUTPUT_CSV,
    )


if __name__ == "__main__":
    result = run_hyperparameter_comparison()
    print(json.dumps(result["summary"], indent=2))
