from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.experiments.walk_forward_validation import run_walk_forward_validation
from src.risk.market_exposure import MarketExposureConfig


OUTPUT_JSON = Path("experiments/market_exposure_comparison_latest.json")
OUTPUT_CSV = Path("experiments/market_exposure_comparison_latest.csv")
MARKET_EXPOSURE_CONFIGS = (
    MarketExposureConfig(name="default_1pct", base_risk_fraction=0.01),
    MarketExposureConfig(name="fixed_1_5pct", base_risk_fraction=0.015),
    MarketExposureConfig(name="fixed_2pct", base_risk_fraction=0.02),
    MarketExposureConfig(
        name="strong_market_1_5pct",
        base_risk_fraction=0.01,
        strong_market_risk_fraction=0.015,
        strong_spy_ema_50_ratio=0.02,
        strong_spy_return_5d=0.0,
    ),
    MarketExposureConfig(
        name="strong_market_2pct",
        base_risk_fraction=0.01,
        strong_market_risk_fraction=0.02,
        strong_spy_ema_50_ratio=0.02,
        strong_spy_return_5d=0.0,
    ),
    MarketExposureConfig(
        name="weak_0_5pct_strong_1_5pct",
        base_risk_fraction=0.01,
        strong_market_risk_fraction=0.015,
        weak_market_risk_fraction=0.005,
        strong_spy_ema_50_ratio=0.02,
        strong_spy_return_5d=0.0,
    ),
)


def run_market_exposure_comparison() -> dict[str, Any]:
    return run_walk_forward_validation(
        market_exposure_configs=MARKET_EXPOSURE_CONFIGS,
        model_types=("random_forest",),
        min_validation_trades=30,
        output_json=OUTPUT_JSON,
        output_csv=OUTPUT_CSV,
    )


if __name__ == "__main__":
    result = run_market_exposure_comparison()
    print(json.dumps(result["summary"], indent=2))
