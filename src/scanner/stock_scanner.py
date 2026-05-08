from __future__ import annotations

import pandas as pd


def add_scanner_columns(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()

    criteria = {
        "trend_positive": data["Close"] > data["ema_50"],
        "relative_volume_high": data["relative_volume_20d"] > 1.3,
        "near_20d_high": data["distance_from_20d_high"] >= -0.03,
        "atr_not_extreme": data["atr_pct"].between(0.005, 0.08),
        "spy_trend_positive": data["spy_trend_positive"].astype(bool),
    }

    score = sum(mask.fillna(False).astype(int) * 20 for mask in criteria.values())
    data["scanner_score"] = score.astype(float)
    data["scanner_pass"] = data["scanner_score"] >= 70

    clean_criteria = {name: mask.fillna(False).astype(bool) for name, mask in criteria.items()}
    reasons: list[str] = []
    for idx in data.index:
        row_reasons = [name for name, mask in clean_criteria.items() if bool(mask.loc[idx])]
        reasons.append(", ".join(row_reasons))
    data["scanner_reason"] = reasons

    return data


def latest_candidates(frame: pd.DataFrame, min_score: float = 70) -> pd.DataFrame:
    latest = frame.groupby("symbol", group_keys=False).tail(1) if "symbol" in frame.columns else frame.tail(1)
    return latest[latest["scanner_score"] >= min_score].copy()
