from __future__ import annotations

import pandas as pd


def add_signal_columns(
    frame: pd.DataFrame,
    min_scanner_score: float = 70,
    min_model_probability: float = 0.60,
) -> pd.DataFrame:
    data = frame.copy()
    data["signal"] = (
        (data["scanner_score"] > min_scanner_score)
        & (data["model_probability"] > min_model_probability)
        & data["spy_trend_positive"].fillna(False).astype(bool)
    )
    data["signal_reason"] = ""
    mask = data["signal"]
    data.loc[mask, "signal_reason"] = (
        "scanner_score="
        + data.loc[mask, "scanner_score"].round(1).astype(str)
        + ", model_probability="
        + data.loc[mask, "model_probability"].round(3).astype(str)
        + ", market trend positive"
    )
    return data
