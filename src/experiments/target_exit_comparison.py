from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.experiments.walk_forward_validation import TargetExitConfig, run_walk_forward_validation


OUTPUT_JSON = Path("experiments/target_exit_comparison_latest.json")
OUTPUT_CSV = Path("experiments/target_exit_comparison_latest.csv")
TARGET_EXIT_CONFIGS = (
    TargetExitConfig(
        name="default_1_5x_stop_3x_tp_10d",
        stop_atr_multiple=1.5,
        take_profit_atr_multiple=3.0,
        timeout_bars=10,
    ),
    TargetExitConfig(
        name="fast_1x_stop_2x_tp_5d",
        stop_atr_multiple=1.0,
        take_profit_atr_multiple=2.0,
        timeout_bars=5,
    ),
    TargetExitConfig(
        name="balanced_1_5x_stop_2_25x_tp_10d",
        stop_atr_multiple=1.5,
        take_profit_atr_multiple=2.25,
        timeout_bars=10,
    ),
    TargetExitConfig(
        name="patient_2x_stop_4x_tp_15d",
        stop_atr_multiple=2.0,
        take_profit_atr_multiple=4.0,
        timeout_bars=15,
    ),
)


def run_target_exit_comparison() -> dict[str, Any]:
    return run_walk_forward_validation(
        target_exit_configs=TARGET_EXIT_CONFIGS,
        model_types=("random_forest",),
        min_validation_trades=30,
        output_json=OUTPUT_JSON,
        output_csv=OUTPUT_CSV,
    )


if __name__ == "__main__":
    result = run_target_exit_comparison()
    print(json.dumps(result["summary"], indent=2))
