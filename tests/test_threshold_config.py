from __future__ import annotations

from src.strategy.threshold_config import DEFAULT_THRESHOLD_CONFIG, ThresholdConfig


def test_default_threshold_config_versions_current_research_defaults() -> None:
    assert DEFAULT_THRESHOLD_CONFIG.version == "thresholds_v2026_05_08_isotonic_025"
    assert DEFAULT_THRESHOLD_CONFIG.min_scanner_score == 70
    assert DEFAULT_THRESHOLD_CONFIG.min_model_probability == 0.25
    assert DEFAULT_THRESHOLD_CONFIG.calibration_method == "isotonic"
    assert DEFAULT_THRESHOLD_CONFIG.model_type == "random_forest"


def test_threshold_config_serializes_stable_metadata() -> None:
    config = ThresholdConfig(
        version="custom_thresholds_v1",
        min_scanner_score=75,
        min_model_probability=0.35,
        calibration_method="raw",
        model_type="logistic_regression",
        selection_basis="validation_only",
    )

    assert config.to_dict() == {
        "version": "custom_thresholds_v1",
        "min_scanner_score": 75,
        "min_model_probability": 0.35,
        "calibration_method": "raw",
        "model_type": "logistic_regression",
        "selection_basis": "validation_only",
    }
