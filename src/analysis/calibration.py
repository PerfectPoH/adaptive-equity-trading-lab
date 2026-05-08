from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss

from src.features.feature_pipeline import FEATURE_COLUMNS
from src.models.trainer import TemporalSplit, training_rows


def build_calibration_report(
    model: Any,
    split: TemporalSplit,
    feature_columns: list[str] | None = None,
    bins: int = 10,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    features = feature_columns or FEATURE_COLUMNS
    frames = [
        _calibration_for_period(model, split.validation, "validation", features, bins),
        _calibration_for_period(model, split.test, "test", features, bins),
    ]
    calibration = pd.concat(frames, ignore_index=True)
    return calibration, summarize_calibration(calibration)


def summarize_calibration(calibration: pd.DataFrame) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for period, rows in calibration.groupby("period"):
        populated = rows[rows["count"] > 0].copy()
        if populated.empty:
            summaries[period] = {
                "rows": 0,
                "brier_score": float("nan"),
                "mean_abs_calibration_error": float("nan"),
                "max_abs_calibration_error": float("nan"),
            }
            continue

        weights = populated["count"] / populated["count"].sum()
        summaries[period] = {
            "rows": int(populated["count"].sum()),
            "brier_score": _safe_float(populated["brier_score"].iloc[0]),
            "mean_abs_calibration_error": _safe_float((populated["abs_error"] * weights).sum()),
            "max_abs_calibration_error": _safe_float(populated["abs_error"].max()),
        }
    return summaries


def _calibration_for_period(
    model: Any,
    frame: pd.DataFrame,
    period: str,
    feature_columns: list[str],
    bins: int,
) -> pd.DataFrame:
    rows = training_rows(frame, feature_columns)
    if rows.empty:
        return _empty_calibration(period, bins)

    x_eval = rows[feature_columns].apply(pd.to_numeric, errors="coerce").replace({pd.NA: np.nan})
    y_true = rows["label"].astype(int)
    y_prob = pd.Series(model.predict_proba(x_eval)[:, 1], index=rows.index)
    brier = _safe_float(brier_score_loss(y_true, y_prob))

    edges = np.linspace(0, 1, bins + 1)
    assignments = pd.cut(y_prob, bins=edges, include_lowest=True, right=True, labels=False)
    output_rows = []
    for bin_id in range(bins):
        mask = assignments == bin_id
        count = int(mask.sum())
        lower = float(edges[bin_id])
        upper = float(edges[bin_id + 1])
        if count == 0:
            avg_predicted = float("nan")
            observed = float("nan")
            abs_error = float("nan")
        else:
            avg_predicted = _safe_float(y_prob[mask].mean())
            observed = _safe_float(y_true[mask].mean())
            abs_error = abs(avg_predicted - observed)
        output_rows.append(
            {
                "period": period,
                "bin": bin_id,
                "lower": lower,
                "upper": upper,
                "count": count,
                "avg_predicted_probability": avg_predicted,
                "observed_success_rate": observed,
                "abs_error": abs_error,
                "brier_score": brier,
            }
        )
    return pd.DataFrame(output_rows)


def _empty_calibration(period: str, bins: int) -> pd.DataFrame:
    edges = np.linspace(0, 1, bins + 1)
    return pd.DataFrame(
        [
            {
                "period": period,
                "bin": bin_id,
                "lower": float(edges[bin_id]),
                "upper": float(edges[bin_id + 1]),
                "count": 0,
                "avg_predicted_probability": float("nan"),
                "observed_success_rate": float("nan"),
                "abs_error": float("nan"),
                "brier_score": float("nan"),
            }
            for bin_id in range(bins)
        ]
    )


def _safe_float(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return parsed if math.isfinite(parsed) else float("nan")
