from __future__ import annotations

from src.experiments.walk_forward_validation import select_threshold_from_validation, summarize_walk_forward


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
