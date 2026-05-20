from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from src.execution.market_impact import SquareRootImpactConfig, square_root_impact_bps
from src.risk.risk_manager import calculate_position_size


@dataclass(frozen=True)
class SmallCapExecutionConfig:
    max_next_open_gap: float = 0.10
    spread_bps: float = 50.0
    slippage_bps: float = 50.0
    risk_fraction: float = 0.01
    stop_atr_multiple: float = 1.5
    take_profit_atr_multiple: float = 3.0
    max_position_dollar_volume_fraction: float = 0.01
    min_trade_notional: float = 1_000.0
    impact_coefficient_bps: float = 15.0
    impact_participation_cap: float = 0.25


DEFAULT_SMALL_CAP_EXECUTION_CONFIG = SmallCapExecutionConfig()


def add_small_cap_execution_columns(
    frame: pd.DataFrame,
    equity: float = 100_000,
    config: SmallCapExecutionConfig = DEFAULT_SMALL_CAP_EXECUTION_CONFIG,
) -> pd.DataFrame:
    data = frame.copy().sort_index()
    if "signal" not in data.columns:
        data["signal"] = False

    data["small_cap_entry_reference_price"] = data["Open"].shift(-1) if "Open" in data.columns else pd.NA
    data["small_cap_next_open_gap_pct"] = _next_open_gap_pct(data)
    data["small_cap_static_cost_pct"] = _static_cost_pct(config)
    data["small_cap_impact_cost_pct"] = 0.0
    data["small_cap_estimated_cost_pct"] = data["small_cap_static_cost_pct"]
    data["small_cap_entry_price"] = pd.to_numeric(data["small_cap_entry_reference_price"], errors="coerce") * (
        1 + data["small_cap_estimated_cost_pct"]
    )
    data["small_cap_entry_price"] = data["small_cap_entry_price"].round(6)
    data["small_cap_stop_loss"] = data["small_cap_entry_price"] - (
        pd.to_numeric(data.get("atr", pd.Series(pd.NA, index=data.index)), errors="coerce") * config.stop_atr_multiple
    )
    data["small_cap_take_profit"] = data["small_cap_entry_price"] + (
        pd.to_numeric(data.get("atr", pd.Series(pd.NA, index=data.index)), errors="coerce") * config.take_profit_atr_multiple
    )
    data["small_cap_stop_loss"] = data["small_cap_stop_loss"].round(6)
    data["small_cap_take_profit"] = data["small_cap_take_profit"].round(6)
    data["small_cap_execution_valid"] = False
    data["small_cap_execution_skip_reason"] = ""
    data["small_cap_position_size"] = 0
    data["small_cap_position_notional"] = 0.0
    data["small_cap_max_liquidity_notional"] = _max_liquidity_notional(data, config)

    for i in range(len(data)):
        if not bool(data["signal"].iat[i]):
            continue
        reason = _skip_reason(data, i, config)
        if reason:
            data.iat[i, data.columns.get_loc("small_cap_execution_skip_reason")] = reason
            continue

        entry = float(data["small_cap_entry_price"].iat[i])
        stop = float(data["small_cap_stop_loss"].iat[i])
        risk_size = calculate_position_size(equity, entry, stop, config.risk_fraction)
        max_notional = float(data["small_cap_max_liquidity_notional"].iat[i])
        liquidity_size = math.floor(max_notional / entry)
        size = max(0, min(risk_size, liquidity_size))
        provisional_notional = size * entry
        adv_notional = _safe_float(data["avg_dollar_volume_20d"].iat[i])
        volatility = _execution_volatility(data, i)
        impact_bps = square_root_impact_bps(
            order_notional=provisional_notional,
            adv_notional=adv_notional or 0.0,
            volatility=volatility,
            config=SquareRootImpactConfig(
                coefficient_bps=config.impact_coefficient_bps,
                participation_cap=config.impact_participation_cap,
            ),
        )
        if math.isinf(impact_bps):
            data.iat[i, data.columns.get_loc("small_cap_execution_skip_reason")] = "impact_participation_above_cap"
            continue
        impact_cost_pct = impact_bps / 10_000.0
        estimated_cost_pct = float(data["small_cap_static_cost_pct"].iat[i]) + impact_cost_pct
        entry = float(data["small_cap_entry_reference_price"].iat[i]) * (1 + estimated_cost_pct)
        stop = entry - (float(data["atr"].iat[i]) * config.stop_atr_multiple)
        take = entry + (float(data["atr"].iat[i]) * config.take_profit_atr_multiple)
        risk_size = calculate_position_size(equity, entry, stop, config.risk_fraction)
        liquidity_size = math.floor(max_notional / entry) if entry > 0 else 0
        size = max(0, min(risk_size, liquidity_size))
        notional = size * entry
        if size <= 0 or notional < config.min_trade_notional:
            data.iat[i, data.columns.get_loc("small_cap_execution_skip_reason")] = "position_below_min_trade_notional"
            continue

        data.iat[i, data.columns.get_loc("small_cap_impact_cost_pct")] = float(impact_cost_pct)
        data.iat[i, data.columns.get_loc("small_cap_estimated_cost_pct")] = float(estimated_cost_pct)
        data.iat[i, data.columns.get_loc("small_cap_entry_price")] = round(float(entry), 6)
        data.iat[i, data.columns.get_loc("small_cap_stop_loss")] = round(float(stop), 6)
        data.iat[i, data.columns.get_loc("small_cap_take_profit")] = round(float(take), 6)
        data.iat[i, data.columns.get_loc("small_cap_execution_valid")] = True
        data.iat[i, data.columns.get_loc("small_cap_position_size")] = int(size)
        data.iat[i, data.columns.get_loc("small_cap_position_notional")] = float(notional)

    data["small_cap_execution_valid"] = data["small_cap_execution_valid"].astype(object)
    return data


def _next_open_gap_pct(data: pd.DataFrame) -> pd.Series:
    if "Close" not in data.columns or "Open" not in data.columns:
        return pd.Series(pd.NA, index=data.index, dtype=object)
    close = pd.to_numeric(data["Close"], errors="coerce")
    next_open = pd.to_numeric(data["Open"].shift(-1), errors="coerce")
    return ((next_open / close) - 1).abs()


def _max_liquidity_notional(data: pd.DataFrame, config: SmallCapExecutionConfig) -> pd.Series:
    if "avg_dollar_volume_20d" not in data.columns:
        return pd.Series(pd.NA, index=data.index, dtype=object)
    return pd.to_numeric(data["avg_dollar_volume_20d"], errors="coerce") * config.max_position_dollar_volume_fraction


def _static_cost_pct(config: SmallCapExecutionConfig) -> float:
    return float((config.spread_bps + config.slippage_bps) / 10_000)


def _execution_volatility(data: pd.DataFrame, i: int) -> float:
    for column in ("rolling_volatility_20d", "atr_pct"):
        if column in data.columns:
            value = _safe_float(data[column].iat[i])
            if value is not None and value > 0:
                return float(value)
    return 0.0


def _safe_float(value: object) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _skip_reason(data: pd.DataFrame, i: int, config: SmallCapExecutionConfig) -> str:
    if i + 1 >= len(data):
        return "no_next_open"

    required_columns = (
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "atr",
        "avg_dollar_volume_20d",
    )
    for column in required_columns:
        if column not in data.columns or pd.isna(data[column].iat[i]):
            return f"missing_{column}"

    gap = data["small_cap_next_open_gap_pct"].iat[i]
    entry = data["small_cap_entry_price"].iat[i]
    stop = data["small_cap_stop_loss"].iat[i]
    take = data["small_cap_take_profit"].iat[i]
    max_notional = data["small_cap_max_liquidity_notional"].iat[i]

    if pd.isna(gap):
        return "missing_next_open_gap"
    if float(gap) > config.max_next_open_gap:
        return "gap_above_max"
    if pd.isna(entry):
        return "missing_entry_price"
    if pd.isna(stop) or pd.isna(take):
        return "missing_exit_levels"
    if not float(stop) < float(entry) < float(take):
        return "invalid_risk_reward"
    if pd.isna(max_notional):
        return "missing_avg_dollar_volume_20d"
    if float(max_notional) < config.min_trade_notional:
        return "liquidity_cap_below_min_trade_notional"
    return ""
