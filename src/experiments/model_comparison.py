from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.experiments.walk_forward_validation import run_walk_forward_validation


OUTPUT_JSON = Path("experiments/model_comparison_latest.json")
OUTPUT_CSV = Path("experiments/model_comparison_latest.csv")
MODEL_TYPES = ("logistic_regression", "random_forest", "hist_gradient_boosting")


def run_model_comparison() -> dict[str, Any]:
    return run_walk_forward_validation(
        model_types=MODEL_TYPES,
        min_validation_trades=30,
        output_json=OUTPUT_JSON,
        output_csv=OUTPUT_CSV,
    )


if __name__ == "__main__":
    result = run_model_comparison()
    print(json.dumps(result["summary"], indent=2))
