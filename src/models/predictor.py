from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline

from src.features.feature_pipeline import FEATURE_COLUMNS


def add_model_probabilities(
    frame: pd.DataFrame,
    model: Pipeline,
    feature_columns: list[str] | None = None,
    output_column: str = "model_probability",
) -> pd.DataFrame:
    features = feature_columns or FEATURE_COLUMNS
    data = frame.copy()
    valid = data[features].notna().any(axis=1)
    data[output_column] = pd.NA
    if valid.any():
        x_pred = data.loc[valid, features].apply(pd.to_numeric, errors="coerce").replace({pd.NA: np.nan})
        data.loc[valid, output_column] = model.predict_proba(x_pred)[:, 1]
    data[output_column] = pd.to_numeric(data[output_column], errors="coerce")
    return data
