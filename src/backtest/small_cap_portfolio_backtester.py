from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.backtest.small_cap_execution import SmallCapExecutionConfig
from src.backtest.small_cap_execution_planner import SmallCapExecutionPlanner


@dataclass(frozen=True)
class SmallCapPortfolioBacktestConfig:
    initial_cash: float = 100_000.0
    holding_period_bars: int = 5
    max_concurrent_positions: int = 5
    execution: SmallCapExecutionConfig = SmallCapExecutionConfig()
    rank_column: str = "small_cap_scanner_score"


@dataclass(frozen=True)
class SmallCapPortfolioBacktestResult:
    trade_log: pd.DataFrame
    equity_curve: pd.DataFrame
    rejections: pd.DataFrame
    rejection_summary: dict[str, int]
    summary: dict[str, float | int]


def run_small_cap_portfolio_backtest(
    candidate_export: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    config: SmallCapPortfolioBacktestConfig = SmallCapPortfolioBacktestConfig(),
) -> SmallCapPortfolioBacktestResult:
    if config.holding_period_bars <= 0:
        raise ValueError("holding_period_bars must be positive")
    if config.max_concurrent_positions <= 0:
        raise ValueError("max_concurrent_positions must be positive")

    planner = SmallCapExecutionPlanner(config.execution)
    cash = float(config.initial_cash)
    open_positions: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    rejection_rows: list[dict[str, Any]] = []
    equity_rows: list[dict[str, Any]] = []

    candidates = _operational_candidates(candidate_export)
    for as_of, day_candidates in candidates.groupby("as_of_ts", sort=True):
        cash = _close_due_positions(as_of, cash, open_positions, trade_rows)
        for _, candidate in _rank_candidates(day_candidates, config.rank_column).iterrows():
            symbol = str(candidate.get("symbol", ""))
            if len(open_positions) >= config.max_concurrent_positions:
                rejection_rows.append(_rejection_row(candidate, "max_concurrent_positions", cash))
                continue
            plan_input = _planner_candidate(candidate, frames.get(symbol), as_of)
            entry = _entry_and_exit(frames.get(symbol), as_of, config.holding_period_bars)
            if plan_input is None or entry is None:
                rejection_rows.append(_rejection_row(candidate, "missing_price_path", cash))
                continue
            entry_date, next_open, exit_date, exit_price = entry
            decision = planner.plan_trade(plan_input, next_open=next_open, available_cash=cash)
            if not decision.accepted:
                rejection_rows.append(_rejection_row(candidate, decision.reject_reason, cash))
                continue
            cash -= decision.position_notional
            open_positions.append(
                {
                    "symbol": symbol,
                    "signal_date": as_of,
                    "entry_date": entry_date,
                    "exit_date": exit_date,
                    "entry_price": float(decision.entry_price),
                    "exit_price": float(exit_price),
                    "position_size": int(decision.position_size),
                    "position_notional": float(decision.position_notional),
                    "max_liquidity_notional": decision.max_liquidity_notional,
                    "next_open_gap_pct": decision.next_open_gap_pct,
                    "estimated_cost_pct": decision.estimated_cost_pct,
                    "small_cap_scanner_score": _candidate_score(candidate, "small_cap_scanner_score"),
                    "cash_after_entry": cash,
                }
            )
        equity_rows.append(_equity_row(as_of, cash, open_positions, config.initial_cash))

    for exit_date in sorted({position["exit_date"] for position in open_positions}):
        cash = _close_due_positions(exit_date, cash, open_positions, trade_rows)
        equity_rows.append(_equity_row(exit_date, cash, open_positions, config.initial_cash))

    trade_log = pd.DataFrame(trade_rows)
    rejections = pd.DataFrame(rejection_rows)
    equity_curve = pd.DataFrame(equity_rows).drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    rejection_summary = _rejection_summary(rejections)
    ending_cash = float(cash)
    total_pnl = float(trade_log["pnl"].sum()) if not trade_log.empty and "pnl" in trade_log.columns else 0.0
    summary = {
        "initial_cash": float(config.initial_cash),
        "ending_cash": ending_cash,
        "total_pnl": total_pnl,
        "return_pct": float((ending_cash / config.initial_cash) - 1) if config.initial_cash else 0.0,
        "total_trades": int(len(trade_log)),
        "total_rejections": int(len(rejections)),
    }
    return SmallCapPortfolioBacktestResult(
        trade_log=trade_log,
        equity_curve=equity_curve,
        rejections=rejections,
        rejection_summary=rejection_summary,
        summary=summary,
    )


def _operational_candidates(candidate_export: pd.DataFrame) -> pd.DataFrame:
    if candidate_export.empty:
        return pd.DataFrame(columns=["as_of_ts"])
    data = candidate_export.copy()
    if "operational_candidate" in data.columns:
        data = data[data["operational_candidate"].fillna(False).astype(bool)].copy()
    data["as_of_ts"] = pd.to_datetime(data.get("as_of"), errors="coerce").dt.normalize()
    return data.dropna(subset=["as_of_ts"])


def _rank_candidates(candidates: pd.DataFrame, rank_column: str) -> pd.DataFrame:
    if rank_column not in candidates.columns:
        return candidates.sort_values("symbol").copy()
    return candidates.sort_values([rank_column, "symbol"], ascending=[False, True]).copy()


def _planner_candidate(candidate: pd.Series, frame: pd.DataFrame | None, as_of: pd.Timestamp) -> dict[str, Any] | None:
    if frame is None or frame.empty:
        return None
    data = frame.copy().sort_index()
    signal_date = _nearest_index_on_or_before(data, as_of)
    if signal_date is None:
        return None
    row = data.loc[signal_date]
    return {
        "symbol": str(candidate.get("symbol", "")),
        "as_of": as_of,
        "Close": row.get("Close"),
        "atr": row.get("atr"),
        "avg_dollar_volume_20d": candidate.get("avg_dollar_volume_20d", row.get("avg_dollar_volume_20d")),
    }


def _entry_and_exit(
    frame: pd.DataFrame | None,
    as_of: pd.Timestamp,
    holding_period_bars: int,
) -> tuple[pd.Timestamp, float, pd.Timestamp, float] | None:
    if frame is None or frame.empty or "Open" not in frame.columns or "Close" not in frame.columns:
        return None
    data = frame.copy().sort_index()
    signal_date = _nearest_index_on_or_before(data, as_of)
    if signal_date is None:
        return None
    signal_position = data.index.get_loc(signal_date)
    entry_position = signal_position + 1
    exit_position = entry_position + holding_period_bars
    if exit_position >= len(data):
        return None
    entry_date = data.index[entry_position]
    exit_date = data.index[exit_position]
    next_open = pd.to_numeric(pd.Series([data.loc[entry_date, "Open"]]), errors="coerce").iat[0]
    exit_price = pd.to_numeric(pd.Series([data.loc[exit_date, "Close"]]), errors="coerce").iat[0]
    if pd.isna(next_open) or pd.isna(exit_price):
        return None
    return entry_date, float(next_open), exit_date, float(exit_price)


def _close_due_positions(
    current_date: pd.Timestamp,
    cash: float,
    open_positions: list[dict[str, Any]],
    trade_rows: list[dict[str, Any]],
) -> float:
    remaining: list[dict[str, Any]] = []
    for position in open_positions:
        if position["exit_date"] <= current_date:
            pnl = float(position["position_size"] * (position["exit_price"] - position["entry_price"]))
            cash += float(position["position_notional"] + pnl)
            trade_rows.append(
                {
                    **position,
                    "pnl": pnl,
                    "return_pct": float((position["exit_price"] / position["entry_price"]) - 1) if position["entry_price"] else 0.0,
                    "cash_after_exit": cash,
                }
            )
        else:
            remaining.append(position)
    open_positions[:] = remaining
    return cash


def _rejection_row(candidate: pd.Series, reason: str, available_cash: float) -> dict[str, Any]:
    return {
        "symbol": str(candidate.get("symbol", "")),
        "as_of": pd.to_datetime(candidate.get("as_of"), errors="coerce"),
        "reject_reason": reason,
        "available_cash": float(available_cash),
    }


def _equity_row(
    date: pd.Timestamp,
    cash: float,
    open_positions: list[dict[str, Any]],
    initial_cash: float,
) -> dict[str, float | pd.Timestamp | int]:
    open_notional = float(sum(position["position_notional"] for position in open_positions))
    equity = float(cash + open_notional)
    return {
        "date": pd.Timestamp(date).normalize(),
        "cash": float(cash),
        "open_position_notional": open_notional,
        "open_positions": int(len(open_positions)),
        "equity": equity,
        "return_pct": float((equity / initial_cash) - 1) if initial_cash else 0.0,
    }


def _rejection_summary(rejections: pd.DataFrame) -> dict[str, int]:
    if rejections.empty or "reject_reason" not in rejections.columns:
        return {}
    return {str(key): int(value) for key, value in rejections["reject_reason"].value_counts().sort_index().items()}


def _candidate_score(candidate: pd.Series, column: str) -> float | None:
    value = pd.to_numeric(pd.Series([candidate.get(column)]), errors="coerce").iat[0]
    if pd.isna(value):
        return None
    return float(value)


def _nearest_index_on_or_before(frame: pd.DataFrame, date: pd.Timestamp) -> pd.Timestamp | None:
    candidates = frame.index[frame.index <= date]
    if len(candidates) == 0:
        return None
    return candidates[-1]
