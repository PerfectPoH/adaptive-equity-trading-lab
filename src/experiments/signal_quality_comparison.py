from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.experiments.walk_forward_validation import SignalQualityConfig, run_walk_forward_validation


OUTPUT_JSON = Path("experiments/signal_quality_comparison_latest.json")
OUTPUT_CSV = Path("experiments/signal_quality_comparison_latest.csv")
SIGNAL_QUALITY_CONFIGS = (
    SignalQualityConfig(name="no_quality_rank_filter"),
    SignalQualityConfig(name="top_3_daily_quality_score", max_signals_per_day=3),
    SignalQualityConfig(name="top_2_daily_quality_score", max_signals_per_day=2),
    SignalQualityConfig(name="top_1_daily_quality_score", max_signals_per_day=1),
    SignalQualityConfig(name="top_2_daily_model_probability", max_signals_per_day=2, rank_column="model_probability"),
    SignalQualityConfig(name="top_2_daily_scanner_score", max_signals_per_day=2, rank_column="scanner_score"),
    SignalQualityConfig(
        name="top_2_daily_quality_0_50",
        min_signal_quality_score=0.50,
        max_signals_per_day=2,
    ),
)


def run_signal_quality_comparison() -> dict[str, Any]:
    return run_walk_forward_validation(
        signal_quality_configs=SIGNAL_QUALITY_CONFIGS,
        model_types=("random_forest",),
        min_validation_trades=20,
        output_json=OUTPUT_JSON,
        output_csv=OUTPUT_CSV,
    )


if __name__ == "__main__":
    result = run_signal_quality_comparison()
    print(json.dumps(result["summary"], indent=2))
