from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.experiments.walk_forward_validation import SymbolSelectionConfig, run_walk_forward_validation


OUTPUT_JSON = Path("experiments/universe_selection_comparison_latest.json")
OUTPUT_CSV = Path("experiments/universe_selection_comparison_latest.csv")
SYMBOL_SELECTION_CONFIGS = (
    SymbolSelectionConfig(name="all_symbols"),
    SymbolSelectionConfig(name="top_7_by_validation_strategy", mode="top_n_strategy_return", top_n=7),
    SymbolSelectionConfig(name="top_5_by_validation_strategy", mode="top_n_strategy_return", top_n=5),
    SymbolSelectionConfig(name="top_3_by_validation_strategy", mode="top_n_strategy_return", top_n=3),
    SymbolSelectionConfig(name="top_5_by_validation_excess", mode="top_n_excess_return", top_n=5),
    SymbolSelectionConfig(name="top_5_by_validation_sharpe", mode="top_n_sharpe", top_n=5),
    SymbolSelectionConfig(name="positive_validation_strategy", mode="positive_strategy_return"),
    SymbolSelectionConfig(
        name="large_cap_stocks_only",
        include_symbols=("AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL"),
    ),
    SymbolSelectionConfig(name="index_etfs_only", include_symbols=("SPY", "QQQ")),
)


def run_universe_selection_comparison() -> dict[str, Any]:
    return run_walk_forward_validation(
        symbol_selection_configs=SYMBOL_SELECTION_CONFIGS,
        model_types=("random_forest",),
        min_validation_trades=20,
        output_json=OUTPUT_JSON,
        output_csv=OUTPUT_CSV,
    )


if __name__ == "__main__":
    result = run_universe_selection_comparison()
    print(json.dumps(result["summary"], indent=2))
