from __future__ import annotations

import pytest

from src.models.trainer import build_model


def test_supported_model_types_build_predict_proba_pipelines() -> None:
    for model_type in ("logistic_regression", "random_forest", "hist_gradient_boosting"):
        model = build_model(model_type)
        assert hasattr(model, "predict_proba")


def test_build_model_applies_random_forest_params() -> None:
    model = build_model("random_forest", model_params={"max_depth": 4, "min_samples_leaf": 30})

    estimator = model.named_steps["model"]
    assert estimator.max_depth == 4
    assert estimator.min_samples_leaf == 30


def test_unsupported_model_type_raises() -> None:
    with pytest.raises(ValueError):
        build_model("not_a_model")
