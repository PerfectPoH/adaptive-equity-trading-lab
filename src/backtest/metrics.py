from __future__ import annotations

import math

import pandas as pd


def buy_and_hold_return(frame: pd.DataFrame) -> float:
    # RISK-043: total return (Adj Close, dividendi inclusi) quando disponibile,
    # altrimenti price return su Close. Confronto onesto col benchmark.
    column = "Adj Close" if "Adj Close" in frame.columns else "Close"
    data = frame.dropna(subset=[column])
    if len(data) < 2:
        return float("nan")
    return float((data[column].iloc[-1] / data[column].iloc[0]) - 1)


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


def equity_curve_to_frame(stats: pd.Series, symbol: str) -> pd.DataFrame:
    curve = stats.get("_equity_curve")
    if not isinstance(curve, pd.DataFrame) or curve.empty:
        return pd.DataFrame()

    output = curve.copy()
    output.index.name = output.index.name or "Date"
    output = output.reset_index()
    if output.columns[0] != "Date":
        output = output.rename(columns={output.columns[0]: "Date"})

    output["symbol"] = symbol
    if "Equity" in output.columns and output["Equity"].iloc[0] != 0:
        output["normalized_equity"] = output["Equity"] / output["Equity"].iloc[0]
    return output


def _percent_to_decimal(value: object) -> float:
    parsed = _safe_float(value)
    return parsed / 100 if not math.isnan(parsed) else parsed


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")
