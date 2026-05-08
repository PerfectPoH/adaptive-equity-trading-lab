from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.experiments.walk_forward_validation import run_walk_forward_validation
from src.features.feature_pipeline import ENHANCED_FEATURE_COLUMNS, FEATURE_COLUMNS


OUTPUT_JSON = Path("experiments/feature_set_comparison_latest.json")
OUTPUT_CSV = Path("experiments/feature_set_comparison_latest.csv")
FEATURE_SETS = {
    "baseline": FEATURE_COLUMNS,
    "enhanced_context": ENHANCED_FEATURE_COLUMNS,
}


def run_feature_set_comparison() -> dict[str, Any]:
    return run_walk_forward_validation(
        feature_sets=FEATURE_SETS,
        model_types=("random_forest",),
        min_validation_trades=30,
        output_json=OUTPUT_JSON,
        output_csv=OUTPUT_CSV,
    )


if __name__ == "__main__":
    result = run_feature_set_comparison()
    print(json.dumps(result["summary"], indent=2))
