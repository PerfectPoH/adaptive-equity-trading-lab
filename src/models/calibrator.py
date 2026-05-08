from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from src.features.feature_pipeline import FEATURE_COLUMNS
from src.models.trainer import training_rows


@dataclass
class ProbabilityCalibrator:
    base_model: Any
    calibration_model: Any
    method: str
    classes_: np.ndarray = field(default_factory=lambda: np.array([0, 1]))

    def predict_proba(self, x: pd.DataFrame) -> np.ndarray:
        raw_probabilities = np.asarray(self.base_model.predict_proba(x)[:, 1], dtype=float)
        if self.method == "isotonic":
            calibrated = np.asarray(self.calibration_model.predict(raw_probabilities), dtype=float)
        elif self.method == "sigmoid":
            calibrated = np.asarray(
                self.calibration_model.predict_proba(raw_probabilities.reshape(-1, 1))[:, 1],
                dtype=float,
            )
        else:
            raise ValueError(f"Unsupported calibration method: {self.method}")

        calibrated = np.clip(calibrated, 0.0, 1.0)
        return np.column_stack([1.0 - calibrated, calibrated])

    def predict(self, x: pd.DataFrame) -> np.ndarray:
        return (self.predict_proba(x)[:, 1] >= 0.5).astype(int)


def fit_probability_calibrator(
    model: Any,
    validation: pd.DataFrame,
    feature_columns: list[str] | None = None,
    method: str = "isotonic",
) -> ProbabilityCalibrator:
    features = feature_columns or FEATURE_COLUMNS
    rows = training_rows(validation, features)
    if rows.empty:
        raise ValueError("No validation rows available for calibration")
    if rows["label"].nunique() < 2:
        raise ValueError("Calibration requires both positive and negative validation labels")

    x_validation = rows[features].apply(pd.to_numeric, errors="coerce").replace({pd.NA: np.nan})
    y_validation = rows["label"].astype(int)
    raw_probabilities = np.asarray(model.predict_proba(x_validation)[:, 1], dtype=float)

    if method == "isotonic":
        calibration_model = IsotonicRegression(out_of_bounds="clip")
        calibration_model.fit(raw_probabilities, y_validation)
    elif method == "sigmoid":
        calibration_model = LogisticRegression(random_state=42)
        calibration_model.fit(raw_probabilities.reshape(-1, 1), y_validation)
    else:
        raise ValueError(f"Unsupported calibration method: {method}")

    return ProbabilityCalibrator(base_model=model, calibration_model=calibration_model, method=method)
