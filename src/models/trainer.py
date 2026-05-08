from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.features.feature_pipeline import FEATURE_COLUMNS


@dataclass
class TemporalSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


DEFAULT_LABEL_PURGE_BARS = 10


def temporal_split(
    frame: pd.DataFrame,
    train_end: str = "2022-12-31",
    validation_end: str = "2023-12-31",
    test_end: str = "2024-12-31",
    label_horizon_bars: int = DEFAULT_LABEL_PURGE_BARS,
) -> TemporalSplit:
    data = frame.sort_index()
    train = purge_label_boundary(data.loc[:train_end].copy(), label_horizon_bars=label_horizon_bars)
    validation = purge_label_boundary(
        data.loc[pd.Timestamp(train_end) + pd.Timedelta(days=1) : validation_end].copy(),
        label_horizon_bars=label_horizon_bars,
    )
    test = purge_label_boundary(
        data.loc[pd.Timestamp(validation_end) + pd.Timedelta(days=1) : test_end].copy(),
        label_horizon_bars=label_horizon_bars,
    )
    return TemporalSplit(train=train, validation=validation, test=test)


def purge_label_boundary(
    frame: pd.DataFrame,
    label_horizon_bars: int = DEFAULT_LABEL_PURGE_BARS,
    symbol_column: str = "symbol",
) -> pd.DataFrame:
    """Drop rows whose forward label horizon crosses a temporal split boundary."""
    if label_horizon_bars <= 0 or frame.empty:
        return frame.copy()

    data = frame.sort_index().copy()
    if symbol_column not in data.columns:
        if len(data) <= label_horizon_bars:
            return data.iloc[0:0].copy()
        return data.iloc[:-label_horizon_bars].copy()

    purged_groups = []
    for _symbol, group in data.groupby(symbol_column, sort=False):
        group = group.sort_index()
        if len(group) > label_horizon_bars:
            purged_groups.append(group.iloc[:-label_horizon_bars].copy())

    if not purged_groups:
        return data.iloc[0:0].copy()
    return pd.concat(purged_groups).sort_index()


def training_rows(frame: pd.DataFrame, feature_columns: list[str] | None = None) -> pd.DataFrame:
    features = feature_columns or FEATURE_COLUMNS
    needed = features + ["label"]
    data = frame.copy()
    data = data[data["label_executable"].fillna(False)]
    data = data.dropna(subset=["label"])
    data[features] = data[features].apply(pd.to_numeric, errors="coerce").replace({pd.NA: np.nan})
    return data.dropna(subset=[col for col in needed if col in data.columns], how="all")


def build_model(model_type: str = "random_forest", model_params: dict[str, Any] | None = None) -> Pipeline:
    overrides = model_params or {}
    if model_type == "logistic_regression":
        params = {"max_iter": 1000, "class_weight": "balanced", "random_state": 42, **overrides}
        model = LogisticRegression(**params)
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", model),
            ]
        )

    if model_type == "random_forest":
        params = {
            "n_estimators": 200,
            "max_depth": 6,
            "min_samples_leaf": 20,
            "class_weight": "balanced_subsample",
            "random_state": 42,
            "n_jobs": -1,
            **overrides,
        }
        model = RandomForestClassifier(**params)
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("model", model),
            ]
        )

    if model_type == "hist_gradient_boosting":
        params = {
            "max_iter": 250,
            "learning_rate": 0.04,
            "max_leaf_nodes": 15,
            "min_samples_leaf": 30,
            "l2_regularization": 0.05,
            "class_weight": "balanced",
            "random_state": 42,
            **overrides,
        }
        model = HistGradientBoostingClassifier(**params)
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("model", model),
            ]
        )

    raise ValueError(f"Unsupported model_type: {model_type}")


def fit_model(
    train: pd.DataFrame,
    feature_columns: list[str] | None = None,
    model_type: str = "random_forest",
    model_params: dict[str, Any] | None = None,
) -> Pipeline:
    features = feature_columns or FEATURE_COLUMNS
    rows = training_rows(train, features)
    if rows.empty:
        raise ValueError("No executable labeled rows available for training")
    if rows["label"].nunique() < 2:
        raise ValueError("Training requires both positive and negative labels")

    model = build_model(model_type, model_params=model_params)
    x_train = rows[features].apply(pd.to_numeric, errors="coerce").replace({pd.NA: np.nan})
    model.fit(x_train, rows["label"].astype(int))
    return model


def evaluate_classifier(model: Any, frame: pd.DataFrame, feature_columns: list[str] | None = None) -> dict[str, float]:
    features = feature_columns or FEATURE_COLUMNS
    rows = training_rows(frame, features)
    if rows.empty:
        return {"accuracy": float("nan"), "roc_auc": float("nan"), "rows": 0}

    y_true = rows["label"].astype(int)
    x_eval = rows[features].apply(pd.to_numeric, errors="coerce").replace({pd.NA: np.nan})
    y_pred = model.predict(x_eval)
    y_prob = model.predict_proba(x_eval)[:, 1]

    roc_auc = float("nan")
    if y_true.nunique() > 1:
        roc_auc = float(roc_auc_score(y_true, y_prob))

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "roc_auc": roc_auc,
        "rows": float(len(rows)),
    }
