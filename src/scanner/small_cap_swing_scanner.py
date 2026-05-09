from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SmallCapSwingScannerConfig:
    min_relative_volume: float = 1.5
    min_panic_gap_down: float = -0.05
    max_panic_rolling_return_5d: float = -0.10
    min_panic_close_position: float = 0.60
    min_breakout_close_position: float = 0.80
    min_breakout_range_pct: float = 0.03
    max_breakout_distance_from_high: float = 0.005
    max_breakout_rolling_volatility: float = 0.08
    min_post_gap: float = 0.04
    max_post_gap: float = 0.10
    min_post_gap_close_position: float = 0.60
    min_post_gap_open_to_close_return: float = 0.01
    min_atr_pct: float = 0.005
    max_atr_pct: float = 0.20


DEFAULT_SMALL_CAP_SWING_SCANNER_CONFIG = SmallCapSwingScannerConfig()
REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "relative_volume_20d", "atr_pct")


def add_small_cap_swing_scanner_columns(
    frame: pd.DataFrame,
    config: SmallCapSwingScannerConfig = DEFAULT_SMALL_CAP_SWING_SCANNER_CONFIG,
) -> pd.DataFrame:
    data = _with_derived_columns(frame.copy())
    rows = data.apply(lambda row: _scan_row(row, data.columns, config), axis=1, result_type="expand")
    for column in rows.columns:
        data[column] = rows[column]
    data["small_cap_scanner_pass"] = data["small_cap_scanner_pass"].astype(object)
    data["scanner_score"] = data["small_cap_scanner_score"]
    data["scanner_pass"] = data["small_cap_scanner_pass"]
    data["scanner_reason"] = data["small_cap_scanner_reason"]
    return data


def latest_small_cap_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    latest = frame.groupby("symbol", group_keys=False).tail(1) if "symbol" in frame.columns else frame.tail(1)
    return latest[latest["small_cap_scanner_pass"].fillna(False).astype(bool)].copy()


def _with_derived_columns(data: pd.DataFrame) -> pd.DataFrame:
    if "previous_close" not in data.columns and "Close" in data.columns:
        data["previous_close"] = data["Close"].shift(1)
    if {"Open", "previous_close"}.issubset(data.columns):
        data["gap_pct"] = (pd.to_numeric(data["Open"], errors="coerce") / pd.to_numeric(data["previous_close"], errors="coerce")) - 1
    if {"Open", "Close"}.issubset(data.columns):
        data["open_to_close_return"] = (pd.to_numeric(data["Close"], errors="coerce") / pd.to_numeric(data["Open"], errors="coerce")) - 1
    if {"High", "Low", "Close"}.issubset(data.columns):
        high = pd.to_numeric(data["High"], errors="coerce")
        low = pd.to_numeric(data["Low"], errors="coerce")
        close = pd.to_numeric(data["Close"], errors="coerce")
        daily_range = (high - low).replace(0, pd.NA)
        data["close_position_daily_range"] = ((close - low) / daily_range).clip(0, 1)
        data["intraday_range_pct"] = daily_range / close
    return data


def _scan_row(row: pd.Series, columns: pd.Index, config: SmallCapSwingScannerConfig) -> dict[str, object]:
    reject_reasons = _base_reject_reasons(row, columns, config)
    setup_scores = {
        "panic_reversal": _panic_reversal_score(row, columns, config),
        "breakout_continuation": _breakout_continuation_score(row, columns, config),
        "post_gap_drift": _post_gap_drift_score(row, columns, config),
    }
    setup, score = max(setup_scores.items(), key=lambda item: item[1])
    passed = not reject_reasons and score >= 70
    active_setup = setup if passed else ""
    return {
        "small_cap_setup": active_setup,
        "small_cap_scanner_score": float(score if not reject_reasons else 0),
        "small_cap_scanner_pass": bool(passed),
        "small_cap_scanner_reason": active_setup if passed else "",
        "small_cap_scanner_reject_reason": ";".join(reject_reasons),
    }


def _base_reject_reasons(row: pd.Series, columns: pd.Index, config: SmallCapSwingScannerConfig) -> list[str]:
    reasons: list[str] = []
    for column in REQUIRED_COLUMNS:
        if column not in columns or pd.isna(row.get(column)):
            reasons.append(f"missing_{column}")
    if "previous_close" not in columns or pd.isna(row.get("previous_close")):
        reasons.append("missing_previous_close")
    if "gap_pct" not in columns or pd.isna(row.get("gap_pct")):
        reasons.append("missing_gap_pct")
    if "close_position_daily_range" not in columns or pd.isna(row.get("close_position_daily_range")):
        reasons.append("missing_close_position_daily_range")
    if reasons:
        return reasons

    if float(row["relative_volume_20d"]) < config.min_relative_volume:
        reasons.append("relative_volume_below_min")
    atr_pct = float(row["atr_pct"])
    if atr_pct < config.min_atr_pct:
        reasons.append("atr_pct_below_min")
    if atr_pct > config.max_atr_pct:
        reasons.append("atr_pct_above_max")
    if float(row["gap_pct"]) > config.max_post_gap:
        reasons.append("gap_above_max")
    return reasons


def _panic_reversal_score(row: pd.Series, columns: pd.Index, config: SmallCapSwingScannerConfig) -> float:
    criteria = [
        _lte(row, "gap_pct", config.min_panic_gap_down),
        _lte(row, "rolling_return_5d", config.max_panic_rolling_return_5d),
        _gte(row, "close_position_daily_range", config.min_panic_close_position),
        _gte(row, "relative_volume_20d", config.min_relative_volume),
        _between(row, "atr_pct", config.min_atr_pct, config.max_atr_pct),
    ]
    return _score(criteria)


def _breakout_continuation_score(row: pd.Series, columns: pd.Index, config: SmallCapSwingScannerConfig) -> float:
    criteria = [
        _gte(row, "close_position_daily_range", config.min_breakout_close_position),
        _gte(row, "relative_volume_20d", config.min_relative_volume),
        _gte(row, "intraday_range_pct", config.min_breakout_range_pct),
        _gte(row, "distance_from_20d_high", -config.max_breakout_distance_from_high),
        _lte(row, "rolling_volatility_20d", config.max_breakout_rolling_volatility),
        _between(row, "atr_pct", config.min_atr_pct, config.max_atr_pct),
    ]
    return _score(criteria)


def _post_gap_drift_score(row: pd.Series, columns: pd.Index, config: SmallCapSwingScannerConfig) -> float:
    criteria = [
        _between(row, "gap_pct", config.min_post_gap, config.max_post_gap),
        _gte(row, "open_to_close_return", config.min_post_gap_open_to_close_return),
        _gte(row, "close_position_daily_range", config.min_post_gap_close_position),
        _gte(row, "relative_volume_20d", config.min_relative_volume),
        _between(row, "atr_pct", config.min_atr_pct, config.max_atr_pct),
    ]
    return _score(criteria)


def _score(criteria: list[bool]) -> float:
    return float(sum(criteria) / len(criteria) * 100)


def _gte(row: pd.Series, column: str, threshold: float) -> bool:
    value = row.get(column)
    return False if pd.isna(value) else float(value) >= threshold


def _lte(row: pd.Series, column: str, threshold: float) -> bool:
    value = row.get(column)
    return False if pd.isna(value) else float(value) <= threshold


def _between(row: pd.Series, column: str, low: float, high: float) -> bool:
    value = row.get(column)
    return False if pd.isna(value) else low <= float(value) <= high
