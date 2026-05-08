from __future__ import annotations

import pandas as pd


def build_trade_labels(
    frame: pd.DataFrame,
    stop_atr_multiple: float = 1.5,
    take_profit_atr_multiple: float = 3.0,
    timeout_bars: int = 10,
    max_gap_threshold: float = 0.05,
    skip_entry_bar_exit_touch: bool = True,
) -> pd.DataFrame:
    data = frame.copy().sort_index()
    n = len(data)

    data["entry_price"] = data["Open"].shift(-1)
    data["gap_pct"] = ((data["entry_price"] / data["Close"]) - 1).abs()
    data["stop_distance"] = stop_atr_multiple * data["atr"]
    data["take_profit_distance"] = take_profit_atr_multiple * data["atr"]
    data["stop_loss"] = data["entry_price"] - data["stop_distance"]
    data["take_profit"] = data["entry_price"] + data["take_profit_distance"]
    data["label"] = pd.NA
    data["label_trade_return"] = pd.NA
    data["label_horizon_return"] = pd.NA
    data["label_excess_return"] = pd.NA
    data["label_trade_positive"] = pd.NA
    data["label_beats_horizon_return"] = pd.NA
    data["label_tp_and_beats_horizon"] = pd.NA
    data["label_exit_reason"] = ""
    data["label_executable"] = False
    data["label_skip_reason"] = ""

    for i in range(n):
        entry_idx = i + 1
        if entry_idx >= n:
            data.iat[i, data.columns.get_loc("label_skip_reason")] = "no_next_open"
            continue

        entry = data["entry_price"].iat[i]
        atr = data["atr"].iat[i]
        gap = data["gap_pct"].iat[i]
        stop = data["stop_loss"].iat[i]
        take = data["take_profit"].iat[i]

        skip_reason = _skip_reason(entry, atr, gap, stop, take, max_gap_threshold)
        if not skip_reason and skip_entry_bar_exit_touch:
            if _entry_bar_touches_exit(data, entry_idx, stop, take):
                skip_reason = "entry_bar_exit_touch"
        if skip_reason:
            data.iat[i, data.columns.get_loc("label_skip_reason")] = skip_reason
            continue

        data.iat[i, data.columns.get_loc("label_executable")] = True
        end_idx = min(n - 1, i + timeout_bars)
        label = 0
        exit_price = data["Close"].iat[end_idx]
        exit_reason = "timeout"

        for j in range(entry_idx, end_idx + 1):
            high = data["High"].iat[j]
            low = data["Low"].iat[j]
            hit_stop = low <= stop
            hit_take = high >= take

            # With daily OHLC we do not know intraday order when both are hit.
            # Conservative rule: assume stop was hit first.
            if hit_stop and hit_take:
                label = 0
                exit_price = stop
                exit_reason = "stop_and_take_same_bar"
                break
            if hit_stop:
                label = 0
                exit_price = stop
                exit_reason = "stop_loss"
                break
            if hit_take:
                label = 1
                exit_price = take
                exit_reason = "take_profit"
                break

        horizon_close = data["Close"].iat[end_idx]
        trade_return = (exit_price / entry) - 1
        horizon_return = (horizon_close / entry) - 1
        excess_return = trade_return - horizon_return
        data.iat[i, data.columns.get_loc("label")] = label
        data.iat[i, data.columns.get_loc("label_trade_return")] = trade_return
        data.iat[i, data.columns.get_loc("label_horizon_return")] = horizon_return
        data.iat[i, data.columns.get_loc("label_excess_return")] = excess_return
        data.iat[i, data.columns.get_loc("label_trade_positive")] = int(trade_return > 0)
        data.iat[i, data.columns.get_loc("label_beats_horizon_return")] = int(excess_return > 0)
        data.iat[i, data.columns.get_loc("label_tp_and_beats_horizon")] = int(label == 1 and excess_return > 0)
        data.iat[i, data.columns.get_loc("label_exit_reason")] = exit_reason

    data["label"] = pd.to_numeric(data["label"], errors="coerce")
    numeric_label_columns = [
        "label_trade_return",
        "label_horizon_return",
        "label_excess_return",
        "label_trade_positive",
        "label_beats_horizon_return",
        "label_tp_and_beats_horizon",
    ]
    for column in numeric_label_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def _entry_bar_touches_exit(data: pd.DataFrame, entry_idx: int, stop: float, take: float) -> bool:
    high = data["High"].iat[entry_idx]
    low = data["Low"].iat[entry_idx]
    return bool(high >= take or low <= stop)


def _skip_reason(
    entry: float,
    atr: float,
    gap: float,
    stop: float,
    take: float,
    max_gap_threshold: float,
) -> str:
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
    return ""
