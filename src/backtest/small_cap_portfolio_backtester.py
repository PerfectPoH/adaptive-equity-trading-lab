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
    allowed_setups: tuple[str, ...] | None = None
    feature_filters: tuple[dict[str, Any], ...] | None = None
    regime_filters: tuple[dict[str, Any], ...] | None = None


@dataclass(frozen=True)
class SmallCapPortfolioBacktestResult:
    trade_log: pd.DataFrame
    equity_curve: pd.DataFrame
    rejections: pd.DataFrame
    rejection_summary: dict[str, int]
    summary: dict[str, float | int]


SCANNER_FEATURE_COLUMNS = (
    "gap_pct",
    "open_to_close_return",
    "close_position_daily_range",
    "intraday_range_pct",
    "relative_volume_20d",
    "atr_pct",
    "distance_from_20d_high",
    "rolling_volatility_20d",
)


REGIME_FEATURE_COLUMNS = (
    "iwm_close",
    "iwm_ema_50",
    "iwm_ema_200",
    "vix_close",
)


RANKEX_TIE_BREAK_COLUMNS = ("relative_volume_20d", "open_to_close_return")


def filter_small_cap_portfolio_candidates(
    candidate_export: pd.DataFrame,
    config: SmallCapPortfolioBacktestConfig = SmallCapPortfolioBacktestConfig(),
) -> pd.DataFrame:
    candidates = _operational_candidates(candidate_export)
    allowed_setups = _normalise_allowed_setups(config.allowed_setups)
    feature_filters = _normalise_feature_filters(config.feature_filters)
    regime_filters = _normalise_regime_filters(config.regime_filters)
    if candidates.empty:
        return candidates.drop(columns=["as_of_ts"], errors="ignore").reset_index(drop=True)
    accepted = []
    for _, candidate in candidates.iterrows():
        accepted.append(
            _setup_allowed(candidate, allowed_setups)
            and _feature_filter_rejection(candidate, feature_filters) is None
            and _regime_filter_rejection(candidate, regime_filters) is None
        )
    return candidates.loc[accepted].drop(columns=["as_of_ts"], errors="ignore").reset_index(drop=True)


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
    allowed_setups = _normalise_allowed_setups(config.allowed_setups)
    feature_filters = _normalise_feature_filters(config.feature_filters)
    regime_filters = _normalise_regime_filters(config.regime_filters)
    for as_of, day_candidates in candidates.groupby("as_of_ts", sort=True):
        cash = _close_due_positions(as_of, cash, open_positions, trade_rows)
        for _, candidate in _rank_candidates(day_candidates, config.rank_column).iterrows():
            symbol = str(candidate.get("symbol", ""))
            if not _setup_allowed(candidate, allowed_setups):
                rejection_rows.append(_rejection_row(candidate, "setup_excluded", cash))
                continue
            feature_rejection = _feature_filter_rejection(candidate, feature_filters)
            if feature_rejection is not None:
                rejection_rows.append(_rejection_row(candidate, "feature_filtered", cash, feature_rejection))
                continue
            regime_rejection = _regime_filter_rejection(candidate, regime_filters)
            if regime_rejection is not None:
                rejection_rows.append(_rejection_row(candidate, "regime_filtered", cash, regime_rejection))
                continue
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
                rejection_rows.append(_rejection_row(candidate, decision.reject_reason, cash, _decision_diagnostics(decision)))
                continue
            cash -= decision.position_notional
            open_positions.append(
                {
                    "symbol": symbol,
                    "signal_date": as_of,
                    "entry_date": entry_date,
                    "exit_date": exit_date,
                    "entry_reference_price": decision.entry_reference_price,
                    "entry_price": float(decision.entry_price),
                    "exit_price": float(exit_price),
                    "position_size": int(decision.position_size),
                    "position_notional": float(decision.position_notional),
                    "max_liquidity_notional": decision.max_liquidity_notional,
                    "next_open_gap_pct": decision.next_open_gap_pct,
                    "estimated_cost_pct": decision.estimated_cost_pct,
                    "impact_cost_pct": decision.impact_cost_pct,
                    "small_cap_scanner_score": _candidate_score(candidate, "small_cap_scanner_score"),
                    "small_cap_setup": _candidate_setup(candidate),
                    **_candidate_feature_values(candidate),
                    **_candidate_regime_values(candidate),
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
    if rank_column == "small_cap_scanner_score":
        tie_break_columns = [column for column in RANKEX_TIE_BREAK_COLUMNS if column in candidates.columns]
        sort_columns = [rank_column, *tie_break_columns, "symbol"]
        ascending = [False, *([False] * len(tie_break_columns)), True]
        return candidates.sort_values(sort_columns, ascending=ascending).copy()
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
        "rolling_volatility_20d": candidate.get("rolling_volatility_20d", row.get("rolling_volatility_20d")),
        "atr_pct": candidate.get("atr_pct", row.get("atr_pct")),
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


def _rejection_row(candidate: pd.Series, reason: str, available_cash: float, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "symbol": str(candidate.get("symbol", "")),
        "as_of": pd.to_datetime(candidate.get("as_of"), errors="coerce"),
        "reject_reason": reason,
        "small_cap_setup": _candidate_setup(candidate),
        **_candidate_feature_values(candidate),
        **_candidate_regime_values(candidate),
        "available_cash": float(available_cash),
    }
    if extra:
        row.update(extra)
    return row


def _decision_diagnostics(decision: Any) -> dict[str, Any]:
    return {
        "entry_reference_price": decision.entry_reference_price,
        "entry_price": decision.entry_price,
        "estimated_cost_pct": decision.estimated_cost_pct,
        "impact_cost_pct": decision.impact_cost_pct,
        "next_open_gap_pct": decision.next_open_gap_pct,
        "stop_loss": decision.stop_loss,
        "take_profit": decision.take_profit,
        "max_liquidity_notional": decision.max_liquidity_notional,
        "position_size": decision.position_size,
        "position_notional": decision.position_notional,
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


def _candidate_setup(candidate: pd.Series) -> str:
    value = candidate.get("small_cap_setup", "")
    if pd.isna(value):
        return ""
    return str(value)


def _candidate_feature_values(candidate: pd.Series) -> dict[str, float | None]:
    return {column: _candidate_score(candidate, column) for column in SCANNER_FEATURE_COLUMNS}


def _candidate_regime_values(candidate: pd.Series) -> dict[str, float | None]:
    return {column: _candidate_score(candidate, column) for column in REGIME_FEATURE_COLUMNS}


def _normalise_allowed_setups(allowed_setups: tuple[str, ...] | None) -> set[str] | None:
    if allowed_setups is None:
        return None
    return {str(setup).strip() for setup in allowed_setups if str(setup).strip()}


def _setup_allowed(candidate: pd.Series, allowed_setups: set[str] | None) -> bool:
    if allowed_setups is None:
        return True
    return _candidate_setup(candidate) in allowed_setups


def _normalise_feature_filters(feature_filters: tuple[dict[str, Any], ...] | None) -> list[dict[str, Any]]:
    if feature_filters is None:
        return []
    normalised: list[dict[str, Any]] = []
    for feature_filter in feature_filters:
        feature = str(feature_filter.get("feature", "")).strip()
        if not feature:
            continue
        setup = str(feature_filter.get("setup", "")).strip()
        normalised.append(
            {
                "setup": setup,
                "feature": feature,
                "min_value": _numeric_or_none(feature_filter.get("min_value")),
                "max_value": _numeric_or_none(feature_filter.get("max_value")),
            }
        )
    return normalised


def _feature_filter_rejection(candidate: pd.Series, feature_filters: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidate_setup = _candidate_setup(candidate)
    for feature_filter in feature_filters:
        filter_setup = feature_filter["setup"]
        if filter_setup and filter_setup != candidate_setup:
            continue
        feature = feature_filter["feature"]
        value = _candidate_score(candidate, feature)
        min_value = feature_filter["min_value"]
        max_value = feature_filter["max_value"]
        rejected = value is None
        if value is not None and min_value is not None and value < min_value:
            rejected = True
        if value is not None and max_value is not None and value > max_value:
            rejected = True
        if rejected:
            return {
                "filter_setup": filter_setup,
                "filter_feature": feature,
                "filter_value": value,
                "filter_min_value": min_value,
                "filter_max_value": max_value,
            }
    return None


def _normalise_regime_filters(regime_filters: tuple[dict[str, Any], ...] | None) -> list[dict[str, Any]]:
    if regime_filters is None:
        return []
    normalised: list[dict[str, Any]] = []
    for regime_filter in regime_filters:
        feature = str(regime_filter.get("feature", "")).strip()
        operator = str(regime_filter.get("operator", "")).strip()
        if not feature or operator not in {">", ">=", "<", "<=", "=="}:
            continue
        threshold_feature = str(regime_filter.get("threshold_feature", "")).strip()
        threshold_value = _numeric_or_none(regime_filter.get("threshold_value"))
        normalised.append(
            {
                "feature": feature,
                "operator": operator,
                "threshold_feature": threshold_feature,
                "threshold_value": threshold_value,
            }
        )
    return normalised


def _regime_filter_rejection(candidate: pd.Series, regime_filters: list[dict[str, Any]]) -> dict[str, Any] | None:
    for regime_filter in regime_filters:
        feature = regime_filter["feature"]
        operator = regime_filter["operator"]
        threshold_feature = regime_filter["threshold_feature"]
        value = _candidate_score(candidate, feature)
        threshold_value = regime_filter["threshold_value"]
        if threshold_feature:
            threshold_value = _candidate_score(candidate, threshold_feature)
        passed = value is not None and threshold_value is not None and _compare(value, threshold_value, operator)
        if not passed:
            return {
                "regime_filter_feature": feature,
                "regime_filter_operator": operator,
                "regime_filter_value": value,
                "regime_filter_threshold_feature": threshold_feature,
                "regime_filter_threshold_value": threshold_value,
            }
    return None


def _compare(value: float, threshold_value: float, operator: str) -> bool:
    if operator == ">":
        return value > threshold_value
    if operator == ">=":
        return value >= threshold_value
    if operator == "<":
        return value < threshold_value
    if operator == "<=":
        return value <= threshold_value
    if operator == "==":
        return value == threshold_value
    return False


def _numeric_or_none(value: Any) -> float | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iat[0]
    if pd.isna(numeric):
        return None
    return float(numeric)


def _nearest_index_on_or_before(frame: pd.DataFrame, date: pd.Timestamp) -> pd.Timestamp | None:
    candidates = frame.index[frame.index <= date]
    if len(candidates) == 0:
        return None
    return candidates[-1]
