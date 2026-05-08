from __future__ import annotations

import math

import pandas as pd


def buy_and_hold_return(frame: pd.DataFrame) -> float:
    data = frame.dropna(subset=["Close"])
    if len(data) < 2:
        return float("nan")
    return float((data["Close"].iloc[-1] / data["Close"].iloc[0]) - 1)


def stats_to_summary(stats: pd.Series, frame: pd.DataFrame) -> dict[str, float | bool]:
    strategy_return = _percent_to_decimal(stats.get("Return [%]", float("nan")))
    benchmark = buy_and_hold_return(frame)
    excess = strategy_return - benchmark if not math.isnan(strategy_return) and not math.isnan(benchmark) else float("nan")
    return {
        "strategy_return": strategy_return,
        "buy_and_hold_return": benchmark,
        "excess_return": excess,
        "beats_buy_and_hold": bool(excess > 0) if not math.isnan(excess) else False,
        "max_drawdown": _percent_to_decimal(stats.get("Max. Drawdown [%]", float("nan"))),
        "sharpe": _safe_float(stats.get("Sharpe Ratio", float("nan"))),
        "profit_factor": _safe_float(stats.get("Profit Factor", float("nan"))),
        "win_rate": _percent_to_decimal(stats.get("Win Rate [%]", float("nan"))),
    }


def _percent_to_decimal(value: object) -> float:
    parsed = _safe_float(value)
    return parsed / 100 if not math.isnan(parsed) else parsed


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")
