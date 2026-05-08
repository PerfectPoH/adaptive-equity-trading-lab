from __future__ import annotations

import math
from typing import Any

import pandas as pd


SIGNAL_CONTEXT_COLUMNS = [
    "model_probability",
    "scanner_score",
    "signal_quality_score",
    "signal_rank",
    "signal_before_rank",
    "signal_rank_selected",
    "atr_pct",
    "relative_volume_20d",
    "distance_from_20d_high",
    "rolling_volatility_20d",
    "news_market_stress",
    "news_market_avg_tone",
    "news_feature_available",
]


def trades_to_frame(stats: pd.Series, frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    trades = stats.get("_trades")
    if not isinstance(trades, pd.DataFrame) or trades.empty:
        return pd.DataFrame()

    output_rows: list[dict[str, Any]] = []
    for _, trade in trades.iterrows():
        entry_bar = int(trade.get("EntryBar", -1))
        signal_bar = entry_bar - 1
        signal_row = frame.iloc[signal_bar] if 0 <= signal_bar < len(frame) else pd.Series(dtype=object)
        return_pct = _safe_float(trade.get("ReturnPct"))
        row = {
            "symbol": symbol,
            "signal_date": frame.index[signal_bar] if 0 <= signal_bar < len(frame) else pd.NaT,
            "entry_date": trade.get("EntryTime"),
            "exit_date": trade.get("ExitTime"),
            "entry_bar": entry_bar,
            "exit_bar": int(trade.get("ExitBar", -1)),
            "size": int(trade.get("Size", 0)),
            "entry_price": _safe_float(trade.get("EntryPrice")),
            "exit_price": _safe_float(trade.get("ExitPrice")),
            "pnl": _safe_float(trade.get("PnL")),
            "return_pct": return_pct,
            "outcome": _outcome(return_pct),
            "duration": str(trade.get("Duration", "")),
        }
        for column in SIGNAL_CONTEXT_COLUMNS:
            row[f"signal_{column}"] = signal_row.get(column, None)
        output_rows.append(row)

    output = pd.DataFrame(output_rows)
    for column in ["signal_date", "entry_date", "exit_date"]:
        if column in output.columns:
            output[column] = pd.to_datetime(output[column], errors="coerce")
    return output


def build_trade_analysis(trades: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    if trades.empty:
        return pd.DataFrame(), {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": float("nan"),
            "avg_return_pct": float("nan"),
            "worst_trade": None,
            "best_trade": None,
        }

    trade_data = trades.copy()
    trade_data["return_pct"] = pd.to_numeric(trade_data["return_pct"], errors="coerce")
    trade_data["pnl"] = pd.to_numeric(trade_data["pnl"], errors="coerce")

    by_symbol = (
        trade_data.groupby("symbol", as_index=False)
        .agg(
            trades=("symbol", "size"),
            wins=("return_pct", lambda series: int((series > 0).sum())),
            losses=("return_pct", lambda series: int((series < 0).sum())),
            avg_return_pct=("return_pct", "mean"),
            median_return_pct=("return_pct", "median"),
            total_pnl=("pnl", "sum"),
            avg_model_probability=("signal_model_probability", "mean"),
            avg_scanner_score=("signal_scanner_score", "mean"),
        )
        .sort_values("avg_return_pct", ascending=False)
    )
    by_symbol["win_rate"] = by_symbol["wins"] / by_symbol["trades"]

    wins = int((trade_data["return_pct"] > 0).sum())
    losses = int((trade_data["return_pct"] < 0).sum())
    worst = trade_data.sort_values("return_pct", ascending=True).iloc[0]
    best = trade_data.sort_values("return_pct", ascending=False).iloc[0]
    summary = {
        "total_trades": int(len(trade_data)),
        "wins": wins,
        "losses": losses,
        "win_rate": _safe_float(wins / len(trade_data)),
        "avg_return_pct": _safe_float(trade_data["return_pct"].mean()),
        "median_return_pct": _safe_float(trade_data["return_pct"].median()),
        "total_pnl": _safe_float(trade_data["pnl"].sum()),
        "worst_trade": _trade_reference(worst),
        "best_trade": _trade_reference(best),
        "negative_symbols": int((by_symbol["avg_return_pct"] < 0).sum()),
        "positive_symbols": int((by_symbol["avg_return_pct"] > 0).sum()),
    }
    return by_symbol, summary


def _trade_reference(row: pd.Series) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "signal_date": _serialize_date(row.get("signal_date")),
        "entry_date": _serialize_date(row.get("entry_date")),
        "exit_date": _serialize_date(row.get("exit_date")),
        "return_pct": _safe_float(row.get("return_pct")),
        "pnl": _safe_float(row.get("pnl")),
    }


def _serialize_date(value: object) -> str | None:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _outcome(return_pct: float) -> str:
    if math.isnan(return_pct) or return_pct == 0:
        return "flat"
    return "win" if return_pct > 0 else "loss"


def _safe_float(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return parsed if math.isfinite(parsed) else float("nan")
