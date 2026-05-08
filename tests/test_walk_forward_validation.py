from __future__ import annotations

from src.experiments.walk_forward_validation import (
    SymbolSelectionConfig,
    _select_symbols,
    select_threshold_from_validation,
    summarize_walk_forward,
)


def test_select_threshold_from_validation_prefers_viable_excess_return() -> None:
    rows = [
        {"threshold": 0.45, "excess_return": 0.05, "strategy_return": 0.10, "closed_trades": 3},
        {"threshold": 0.55, "excess_return": 0.02, "strategy_return": 0.08, "closed_trades": 20},
        {"threshold": 0.60, "excess_return": 0.01, "strategy_return": 0.07, "closed_trades": 25},
    ]

    selected = select_threshold_from_validation(rows, min_validation_trades=10)

    assert selected["threshold"] == 0.55


def test_select_threshold_from_validation_can_choose_across_models() -> None:
    rows = [
        {
            "model_type": "random_forest",
            "probability_variant": "isotonic",
            "threshold": 0.25,
            "excess_return": 0.01,
            "strategy_return": 0.06,
            "closed_trades": 20,
        },
        {
            "model_type": "hist_gradient_boosting",
            "probability_variant": "isotonic",
            "threshold": 0.30,
            "excess_return": 0.03,
            "strategy_return": 0.08,
            "closed_trades": 18,
        },
    ]

    selected = select_threshold_from_validation(rows, min_validation_trades=10)

    assert selected["model_type"] == "hist_gradient_boosting"
    assert selected["threshold"] == 0.30


def test_select_threshold_from_validation_can_choose_across_feature_sets() -> None:
    rows = [
        {
            "feature_set": "baseline",
            "model_type": "random_forest",
            "probability_variant": "isotonic",
            "threshold": 0.25,
            "excess_return": 0.01,
            "strategy_return": 0.06,
            "closed_trades": 20,
        },
        {
            "feature_set": "enhanced_context",
            "model_type": "random_forest",
            "probability_variant": "raw",
            "threshold": 0.45,
            "excess_return": 0.04,
            "strategy_return": 0.09,
            "closed_trades": 18,
        },
    ]

    selected = select_threshold_from_validation(rows, min_validation_trades=10)

    assert selected["feature_set"] == "enhanced_context"
    assert selected["threshold"] == 0.45


def test_select_threshold_from_validation_can_choose_across_target_exit_configs() -> None:
    rows = [
        {
            "target_exit_config": "default",
            "feature_set": "baseline",
            "model_type": "random_forest",
            "probability_variant": "isotonic",
            "threshold": 0.25,
            "excess_return": 0.01,
            "strategy_return": 0.06,
            "closed_trades": 20,
        },
        {
            "target_exit_config": "balanced",
            "feature_set": "baseline",
            "model_type": "random_forest",
            "probability_variant": "isotonic",
            "threshold": 0.20,
            "excess_return": 0.05,
            "strategy_return": 0.10,
            "closed_trades": 22,
        },
    ]

    selected = select_threshold_from_validation(rows, min_validation_trades=10)

    assert selected["target_exit_config"] == "balanced"
    assert selected["threshold"] == 0.20


def test_select_threshold_from_validation_can_choose_across_signal_quality_configs() -> None:
    rows = [
        {
            "signal_quality_config": "no_quality_rank_filter",
            "threshold": 0.25,
            "excess_return": 0.01,
            "strategy_return": 0.06,
            "closed_trades": 20,
        },
        {
            "signal_quality_config": "top_2_daily",
            "threshold": 0.25,
            "excess_return": 0.04,
            "strategy_return": 0.08,
            "closed_trades": 16,
        },
    ]

    selected = select_threshold_from_validation(rows, min_validation_trades=10)

    assert selected["signal_quality_config"] == "top_2_daily"


def test_select_threshold_from_validation_can_choose_across_market_exposure_configs() -> None:
    rows = [
        {
            "market_exposure_config": "default_1pct",
            "threshold": 0.25,
            "excess_return": 0.01,
            "strategy_return": 0.06,
            "closed_trades": 20,
        },
        {
            "market_exposure_config": "strong_market_2pct",
            "threshold": 0.25,
            "excess_return": 0.05,
            "strategy_return": 0.11,
            "closed_trades": 20,
        },
    ]

    selected = select_threshold_from_validation(rows, min_validation_trades=10)

    assert selected["market_exposure_config"] == "strong_market_2pct"


def test_select_threshold_from_validation_can_choose_across_symbol_selection_configs() -> None:
    rows = [
        {
            "symbol_selection_config": "all_symbols",
            "threshold": 0.25,
            "excess_return": 0.01,
            "strategy_return": 0.06,
            "closed_trades": 20,
        },
        {
            "symbol_selection_config": "top_5_by_validation_strategy",
            "threshold": 0.25,
            "excess_return": 0.04,
            "strategy_return": 0.09,
            "closed_trades": 20,
        },
    ]

    selected = select_threshold_from_validation(rows, min_validation_trades=10)

    assert selected["symbol_selection_config"] == "top_5_by_validation_strategy"


def test_select_symbols_can_pick_top_n_by_strategy_return() -> None:
    rows = [
        {"symbol": "AAA", "trades": 5, "strategy_return": 0.01, "excess_return": -0.10, "sharpe": 0.2},
        {"symbol": "BBB", "trades": 5, "strategy_return": 0.10, "excess_return": 0.02, "sharpe": 1.0},
        {"symbol": "CCC", "trades": 5, "strategy_return": 0.05, "excess_return": 0.01, "sharpe": 0.8},
    ]
    config = SymbolSelectionConfig(name="top_2", mode="top_n_strategy_return", top_n=2)

    selected = _select_symbols(rows, config)

    assert selected == ("BBB", "CCC")


def test_select_symbols_uses_forced_validation_symbols_for_test() -> None:
    rows = [
        {"symbol": "AAA", "trades": 5, "strategy_return": 0.01},
        {"symbol": "BBB", "trades": 5, "strategy_return": 0.10},
        {"symbol": "CCC", "trades": 5, "strategy_return": 0.05},
    ]

    selected = _select_symbols(rows, SymbolSelectionConfig(name="all"), forced_symbols=("BBB", "CCC"))

    assert selected == ("BBB", "CCC")


def test_select_symbols_all_mode_keeps_low_trade_symbols() -> None:
    rows = [
        {"symbol": "AAA", "trades": 0, "strategy_return": 0.0},
        {"symbol": "BBB", "trades": 5, "strategy_return": 0.10},
    ]

    selected = _select_symbols(rows, SymbolSelectionConfig(name="all_symbols", min_symbol_trades=5))

    assert selected == ("AAA", "BBB")


def test_summarize_walk_forward_marks_positive_under_benchmark() -> None:
    summary = summarize_walk_forward(
        [
            {"test_strategy_return": 0.05, "test_excess_return": -0.10, "test_beats_buy_and_hold": False},
            {"test_strategy_return": 0.03, "test_excess_return": -0.20, "test_beats_buy_and_hold": False},
        ]
    )

    assert summary["folds"] == 2
    assert summary["folds_beating_buy_and_hold"] == 0
    assert summary["verdict"] == "positive_but_under_benchmark"
