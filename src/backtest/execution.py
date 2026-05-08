from __future__ import annotations

import pandas as pd

from src.risk.risk_manager import calculate_position_size


def add_execution_columns(
    frame: pd.DataFrame,
    equity: float = 100_000,
    risk_fraction: float = 0.01,
    max_gap_threshold: float = 0.05,
    skip_entry_bar_exit_touch: bool = True,
) -> pd.DataFrame:
    data = frame.copy().sort_index()

    if "signal" not in data.columns:
        data["signal"] = False

    data["execution_valid"] = False
    data["execution_skip_reason"] = ""
    data["position_size"] = 0

    for i in range(len(data)):
        if not bool(data["signal"].iat[i]):
            continue

        reason = _execution_skip_reason(data, i, max_gap_threshold, skip_entry_bar_exit_touch)
        if reason:
            data.iat[i, data.columns.get_loc("execution_skip_reason")] = reason
            continue

        entry = float(data["entry_price"].iat[i])
        stop = float(data["stop_loss"].iat[i])
        size = calculate_position_size(equity, entry, stop, risk_fraction)
        if size <= 0:
            data.iat[i, data.columns.get_loc("execution_skip_reason")] = "invalid_position_size"
            continue

        data.iat[i, data.columns.get_loc("execution_valid")] = True
        data.iat[i, data.columns.get_loc("position_size")] = size

    return data


def planned_trade_for_signal(frame: pd.DataFrame, signal_index: int) -> dict[str, object]:
    if signal_index + 1 >= len(frame):
        return {"valid": False, "skip_reason": "no_next_open"}

    row = frame.iloc[signal_index]
    entry_date = frame.index[signal_index + 1]
    return {
        "valid": bool(row.get("execution_valid", False)),
        "signal_date": frame.index[signal_index],
        "entry_date": entry_date,
        "entry_price": row.get("entry_price"),
        "stop_loss": row.get("stop_loss"),
        "take_profit": row.get("take_profit"),
        "position_size": int(row.get("position_size", 0)),
        "skip_reason": row.get("execution_skip_reason", ""),
    }


def _execution_skip_reason(
    data: pd.DataFrame,
    i: int,
    max_gap_threshold: float,
    skip_entry_bar_exit_touch: bool,
) -> str:
    if i + 1 >= len(data):
        return "no_next_open"

    entry = data["entry_price"].iat[i]
    atr = data["atr"].iat[i]
    gap = data["gap_pct"].iat[i]
    stop = data["stop_loss"].iat[i]
    take = data["take_profit"].iat[i]

    if pd.isna(entry):
        return "missing_entry"
    if pd.isna(atr) or atr <= 0:
        return "invalid_atr"
    if pd.isna(gap) or gap > max_gap_threshold:
        return "gap_too_large"
    if pd.isna(stop) or pd.isna(take):
        return "missing_exit_levels"
    if not stop < entry < take:
        return "invalid_risk_reward"
    if skip_entry_bar_exit_touch:
        entry_bar = i + 1
        if data["High"].iat[entry_bar] >= take or data["Low"].iat[entry_bar] <= stop:
            return "entry_bar_exit_touch"
    return ""
