from __future__ import annotations

import pandas as pd

from src.features.feature_pipeline import FEATURE_COLUMNS
from src.models.calibrator import fit_probability_calibrator
from src.models.trainer import fit_model


def make_labeled_frame(rows: int = 80) -> pd.DataFrame:
    idx = pd.bdate_range("2022-01-03", periods=rows)
    data = pd.DataFrame(index=idx)
    for column in FEATURE_COLUMNS:
        data[column] = 0.0
    data["return_1d"] = [i / rows for i in range(rows)]
    data["rolling_return_5d"] = data["return_1d"]
    data["rsi_14"] = 40 + data["return_1d"] * 20
    data["label"] = (data["return_1d"] > 0.5).astype(int)
    data["label_executable"] = True
    return data


def test_fit_probability_calibrator_returns_predict_proba_model() -> None:
    frame = make_labeled_frame()
    train = pd.concat([frame.iloc[:30], frame.iloc[50:70]])
    validation = pd.concat([frame.iloc[30:50], frame.iloc[70:]])
    model = fit_model(train)

    calibrator = fit_probability_calibrator(model, validation, method="sigmoid")
    probabilities = calibrator.predict_proba(validation[FEATURE_COLUMNS])[:, 1]

    assert len(probabilities) == len(validation)
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
