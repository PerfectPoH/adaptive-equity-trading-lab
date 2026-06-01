from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/NORGATE-PORTFOLIO-TRIAL-BACKTEST-001")
FROZEN_SLEEVE_WEIGHTS = {
    "Catalyst": 0.25,
    "Dollar-Bar Microstructure": 0.25,
    "Mean Reversion": 0.25,
    "Momentum": 0.25,
}
DISABLED_SLEEVES = {
    "Catalyst": "missing_point_in_time_event_and_direction_source",
    "Dollar-Bar Microstructure": "daily_bars_cannot_reconstruct_dollar_bars",
}


def build_tradability_filtered_frames(
    frames: dict[str, pd.DataFrame],
    *,
    min_price: float,
    min_median_turnover: float,
    min_rows: int,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    filtered: dict[str, pd.DataFrame] = {}
    rejections: dict[str, str] = {}
    diagnostics: dict[str, dict[str, Any]] = {}
    for symbol, frame in frames.items():
        if frame is None or frame.empty or len(frame) < min_rows:
            rejections[symbol] = "insufficient_rows"
            diagnostics[symbol] = {"rows": 0 if frame is None else int(len(frame))}
            continue
        data = frame.copy().sort_index()
        close = pd.to_numeric(data.get("Close"), errors="coerce").dropna()
        turnover = _turnover_series(data).dropna()
        minimum_price = float(close.min()) if not close.empty else 0.0
        median_turnover = float(turnover.median()) if not turnover.empty else 0.0
        diagnostics[symbol] = {
            "rows": int(len(data)),
            "minimum_close": minimum_price,
            "median_turnover": median_turnover,
        }
        if minimum_price < min_price:
            rejections[symbol] = "minimum_price_below_threshold"
            continue
        if median_turnover < min_median_turnover:
            rejections[symbol] = "median_turnover_below_threshold"
            continue
        filtered[symbol] = data
    return filtered, {
        "filter_id": "NORGATE-TRADABILITY-GATE-001",
        "min_price": min_price,
        "min_median_turnover": min_median_turnover,
        "min_rows": min_rows,
        "accepted_symbols": sorted(filtered),
        "rejections": rejections,
        "diagnostics": diagnostics,
    }


def build_norgate_admissible_bundle_manifest(
    probe_result: dict[str, Any],
    *,
    active_symbols: list[str],
    delisted_symbols: list[str],
) -> dict[str, Any]:
    evidence = probe_result.get("evidence", {})
    blockers: list[str] = []
    if not active_symbols:
        blockers.append("active_symbol_sample_missing")
    if not delisted_symbols:
        blockers.append("delisted_symbol_sample_missing")
    required_evidence = {
        "us_delisted_prices_accessible",
        "us_active_adjusted_daily_prices_available",
        "us_delisted_listing_or_delisting_dates_available",
    }
    missing_evidence = sorted(key for key in required_evidence if evidence and not evidence.get(key))
    blockers.extend(missing_evidence)
    status = "NORGATE_ADMISSIBLE_DATA_BUNDLE_TRIAL_LIMITED" if not blockers else "NORGATE_DATA_BUNDLE_BLOCKED"
    return {
        "bundle_id": "NORGATE-ADMISSIBLE-DATA-BUNDLE-001",
        "linked_probe": probe_result.get("probe_id", "NORGATE-DATA-PROBE-001"),
        "provider": "Norgate Data",
        "status": status,
        "trial_limited": True,
        "trial_history_limit": "2_years_expected_from_trial_terms",
        "survivorship_free_universe": not blockers,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claim_allowed": False,
        "blockers": blockers,
        "covered_fields": [
            "survivorship_free_universe",
            "point_in_time_membership",
            "listing_and_delisting_dates",
            "delisted_symbol_prices",
            "split_dividend_adjusted_ohlcv",
            "tradability_and_liquidity_history",
            "benchmark_panel",
            "raw_payload_retention_manifest",
        ],
        "symbol_counts": {
            "active": len(active_symbols),
            "delisted": len(delisted_symbols),
            "total": len(active_symbols) + len(delisted_symbols),
        },
        "active_symbols": active_symbols,
        "delisted_symbols": delisted_symbols,
    }


def run_trial_limited_portfolio_diagnostic(
    frames: dict[str, pd.DataFrame],
    bundle: dict[str, Any],
    gate: dict[str, Any],
    *,
    cost_bps: int = 500,
    tradability_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if gate.get("parameter_sweep_allowed"):
        raise ValueError("parameter sweeps are forbidden for the Norgate trial diagnostic")
    active_symbols = [str(symbol) for symbol in bundle.get("active_symbols", [])]
    delisted_symbols = [str(symbol) for symbol in bundle.get("delisted_symbols", [])]
    tradable_symbols = [symbol for symbol in [*active_symbols, *delisted_symbols] if symbol in frames]
    trade_rows: list[dict[str, Any]] = []
    for sleeve in ("Momentum", "Mean Reversion"):
        trade_rows.extend(_generate_sleeve_trades(sleeve, tradable_symbols, frames, cost_bps=cost_bps))
    trade_log = pd.DataFrame(trade_rows)
    equity_curve = _build_equity_curve(trade_log)
    summary = _summary(trade_log, equity_curve)
    robustness = _robustness(trade_log)
    benchmark = _benchmark_summary(frames)
    blockers = [
        "trial_history_below_full_validation_requirement",
        "promotion_locked_until_long_history_oos_gate",
        *[f"{sleeve}:{reason}" for sleeve, reason in DISABLED_SLEEVES.items()],
    ]
    if robustness.get("ex_best_symbol_weighted_net_return", 0.0) <= 0:
        blockers.append("outlier_dependency_ex_best_symbol_nonpositive")
    if summary.get("win_rate", 0.0) < 0.5:
        blockers.append("weak_distribution_win_rate_below_half")
    if not trade_log.empty and float(trade_log["entry_price"].min()) < 1.0:
        blockers.append("sub_dollar_trade_quality_blocker")
    if not trade_log.empty and float(trade_log["score"].abs().max()) > 10.0:
        blockers.append("extreme_rank_score_instability")
    if summary.get("total_trades", 0) < 20:
        blockers.append("sample_starved_after_tradability_filter")
    return {
        "run_id": "NORGATE-PORTFOLIO-TRIAL-BACKTEST-001",
        "gate_id": gate.get("gate_id", "NORGATE-PORTFOLIO-TRIAL-BACKTEST-GATE-001"),
        "bundle_id": bundle.get("bundle_id", "NORGATE-ADMISSIBLE-DATA-BUNDLE-001"),
        "status": "NORGATE_PORTFOLIO_TRIAL_LIMITED_COMPLETE",
        "trial_limited": True,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "parameter_sweep_performed": False,
        "market_data_download_performed": False,
        "provider_query_performed": True,
        "disabled_sleeves": DISABLED_SLEEVES,
        "frozen_sleeve_weights": FROZEN_SLEEVE_WEIGHTS,
        "cost_bps": cost_bps,
        "tradability_filter": tradability_report or {},
        "symbol_counts": {
            "active": len(active_symbols),
            "delisted": len(delisted_symbols),
            "tradable_with_frames": len(tradable_symbols),
        },
        "summary": summary,
        "robustness": robustness,
        "benchmark": benchmark,
        "trade_log": _records(trade_log),
        "equity_curve": _records(equity_curve),
        "final_decision": {
            "decision": "NORGATE_PORTFOLIO_TRIAL_LIMITED_ARCHIVE_NO_PROMOTION",
            "blockers": blockers,
            "promotion_allowed": False,
            "portfolio_backtest_performed": True,
            "trial_limited": True,
            "financial_performance_claimed": False,
        },
    }


def load_norgate_trial_frames(
    *,
    active_limit: int = 80,
    delisted_limit: int = 80,
    min_rows: int = 90,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    import norgatedata

    active_symbols = _select_norgate_symbols(norgatedata, "US Equities", active_limit, min_rows=min_rows)
    delisted_symbols = _select_norgate_symbols(norgatedata, "US Equities Delisted", delisted_limit, min_rows=min_rows)
    frames: dict[str, pd.DataFrame] = {}
    for symbol in [*active_symbols, *delisted_symbols, "SPY", "IWM"]:
        if symbol in frames:
            continue
        frame = _norgate_price_frame(norgatedata, symbol)
        if frame is not None and len(frame) >= min_rows:
            frames[symbol] = frame
    metadata = {
        "active_symbols": active_symbols,
        "delisted_symbols": delisted_symbols,
        "benchmark_symbols": [symbol for symbol in ("SPY", "IWM") if symbol in frames],
    }
    return frames, metadata


def persist_norgate_trial_outputs(bundle: dict[str, Any], result: dict[str, Any], *, output_dir: Path = OUTPUT_DIR) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / "norgate_admissible_data_bundle.json"
    result_path = output_dir / "norgate_portfolio_trial_result.json"
    decision_path = output_dir / "final_decision.json"
    report_path = output_dir / "norgate_portfolio_trial_report.md"
    trade_path = output_dir / "trade_log.csv"
    equity_path = output_dir / "equity_curve.csv"
    bundle_path.write_text(json.dumps(_jsonable(bundle), indent=2, sort_keys=True), encoding="utf-8")
    result_path.write_text(json.dumps(_jsonable(_result_without_records(result)), indent=2, sort_keys=True), encoding="utf-8")
    decision_path.write_text(json.dumps(_jsonable(result["final_decision"]), indent=2, sort_keys=True), encoding="utf-8")
    pd.DataFrame(result.get("trade_log", [])).to_csv(trade_path, index=False)
    pd.DataFrame(result.get("equity_curve", [])).to_csv(equity_path, index=False)
    report_path.write_text(_markdown_report(bundle, result), encoding="utf-8")
    return {
        "output_dir": str(output_dir),
        "bundle_path": str(bundle_path),
        "result_path": str(result_path),
        "final_decision_path": str(decision_path),
        "report_path": str(report_path),
        "trade_log_path": str(trade_path),
        "equity_curve_path": str(equity_path),
    }


def _select_norgate_symbols(norgatedata: Any, database_name: str, limit: int, *, min_rows: int) -> list[str]:
    selected: list[str] = []
    for symbol in list(norgatedata.database_symbols(database_name)):
        symbol = str(symbol)
        if _skip_non_common_like_symbol(symbol):
            continue
        frame = _norgate_price_frame(norgatedata, symbol)
        if frame is not None and len(frame) >= min_rows:
            selected.append(symbol)
        if len(selected) >= limit:
            break
    return selected


def _skip_non_common_like_symbol(symbol: str) -> bool:
    upper = symbol.upper()
    return any(token in upper for token in (".U", ".WS", ".W", "-WS", "-WT", "-RIGHT", "-UNIT"))


def _norgate_price_frame(norgatedata: Any, symbol: str) -> pd.DataFrame | None:
    try:
        frame = norgatedata.price_timeseries(symbol, timeseriesformat="pandas-dataframe")
    except Exception:
        return None
    if frame is None or frame.empty:
        return None
    frame = frame.copy()
    frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(frame.columns):
        return None
    return frame.sort_index()


def _turnover_series(frame: pd.DataFrame) -> pd.Series:
    if "Turnover" in frame.columns:
        return pd.to_numeric(frame["Turnover"], errors="coerce")
    close = pd.to_numeric(frame.get("Close"), errors="coerce")
    volume = pd.to_numeric(frame.get("Volume"), errors="coerce")
    return close * volume


def _generate_sleeve_trades(sleeve: str, symbols: list[str], frames: dict[str, pd.DataFrame], *, cost_bps: int) -> list[dict[str, Any]]:
    lookback = 20 if sleeve == "Momentum" else 5
    hold = 20 if sleeve == "Momentum" else 10
    warmup = 60
    all_dates = sorted({date for symbol in symbols for date in frames[symbol].index})
    rebalance_dates = all_dates[warmup::20]
    rows: list[dict[str, Any]] = []
    for signal_date in rebalance_dates:
        ranked = []
        for symbol in symbols:
            score = _score_symbol(frames[symbol], signal_date, lookback)
            if score is not None:
                ranked.append((symbol, score))
        if not ranked:
            continue
        ranked.sort(key=lambda item: (item[1], item[0]), reverse=sleeve == "Momentum")
        symbol, score = ranked[0]
        trade = _trade_from_signal(symbol, frames[symbol], signal_date, hold, sleeve=sleeve, score=score, cost_bps=cost_bps)
        if trade:
            rows.append(trade)
    return rows


def _score_symbol(frame: pd.DataFrame, signal_date: pd.Timestamp, lookback: int) -> float | None:
    data = frame[frame.index <= signal_date]
    if len(data) <= lookback:
        return None
    current = float(data["Close"].iloc[-1])
    prior = float(data["Close"].iloc[-lookback - 1])
    if prior <= 0:
        return None
    return (current / prior) - 1.0


def _trade_from_signal(
    symbol: str,
    frame: pd.DataFrame,
    signal_date: pd.Timestamp,
    hold: int,
    *,
    sleeve: str,
    score: float,
    cost_bps: int,
) -> dict[str, Any] | None:
    data = frame.sort_index()
    dates = data.index[data.index <= signal_date]
    if len(dates) == 0:
        return None
    signal_pos = data.index.get_loc(dates[-1])
    entry_pos = signal_pos + 1
    if entry_pos >= len(data):
        return None
    exit_pos = min(entry_pos + hold, len(data) - 1)
    entry_date = data.index[entry_pos]
    exit_date = data.index[exit_pos]
    entry = float(data.loc[entry_date, "Open"])
    exit_price = float(data.loc[exit_date, "Close"])
    if entry <= 0 or exit_price <= 0:
        return None
    gross = (exit_price / entry) - 1.0
    cost = cost_bps / 10_000.0
    net = gross - cost
    weight = FROZEN_SLEEVE_WEIGHTS[sleeve]
    return {
        "symbol": symbol,
        "sleeve": sleeve,
        "signal_date": signal_date.date().isoformat(),
        "entry_date": entry_date.date().isoformat(),
        "exit_date": exit_date.date().isoformat(),
        "entry_price": entry,
        "exit_price": exit_price,
        "score": score,
        "gross_return": gross,
        "cost_return": cost,
        "net_return": net,
        "sleeve_weight": weight,
        "weighted_net_return": net * weight,
        "forced_end_of_history_exit": exit_pos < entry_pos + hold,
    }


def _build_equity_curve(trade_log: pd.DataFrame) -> pd.DataFrame:
    if trade_log.empty:
        return pd.DataFrame(columns=["date", "period_net_return", "cumulative_weighted_net_return", "drawdown"])
    by_date = trade_log.copy()
    by_date["date"] = pd.to_datetime(by_date["exit_date"])
    grouped = by_date.groupby("date", as_index=False)["weighted_net_return"].sum().sort_values("date")
    grouped["cumulative_weighted_net_return"] = grouped["weighted_net_return"].cumsum()
    grouped["running_peak"] = grouped["cumulative_weighted_net_return"].cummax()
    grouped["drawdown"] = grouped["cumulative_weighted_net_return"] - grouped["running_peak"]
    return grouped.rename(columns={"weighted_net_return": "period_net_return"}).drop(columns=["running_peak"])


def _summary(trade_log: pd.DataFrame, equity_curve: pd.DataFrame) -> dict[str, Any]:
    total = float(trade_log["weighted_net_return"].sum()) if not trade_log.empty else 0.0
    return {
        "total_trades": int(len(trade_log)),
        "weighted_net_return_sum": total,
        "gross_return_sum": float(trade_log["gross_return"].sum()) if not trade_log.empty else 0.0,
        "win_rate": float((trade_log["net_return"] > 0).mean()) if not trade_log.empty else 0.0,
        "max_drawdown": float(equity_curve["drawdown"].min()) if not equity_curve.empty else 0.0,
    }


def _robustness(trade_log: pd.DataFrame) -> dict[str, Any]:
    if trade_log.empty:
        return {"ex_best_symbol_weighted_net_return": 0.0, "best_symbol": None}
    by_symbol = trade_log.groupby("symbol")["weighted_net_return"].sum().sort_values(ascending=False)
    best_symbol = str(by_symbol.index[0])
    total = float(by_symbol.sum())
    return {
        "best_symbol": best_symbol,
        "best_symbol_weighted_net_return": float(by_symbol.iloc[0]),
        "ex_best_symbol_weighted_net_return": float(total - by_symbol.iloc[0]),
        "symbol_concentration_top1": float(by_symbol.iloc[0] / total) if total else None,
    }


def _benchmark_summary(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    rows = {}
    for symbol in ("SPY", "IWM"):
        frame = frames.get(symbol)
        if frame is None or len(frame) < 2:
            continue
        start = float(frame["Close"].iloc[0])
        end = float(frame["Close"].iloc[-1])
        rows[symbol] = {"total_return": (end / start) - 1.0 if start else None}
    return rows


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _result_without_records(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key not in {"trade_log", "equity_curve"}}


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def _markdown_report(bundle: dict[str, Any], result: dict[str, Any]) -> str:
    summary = result["summary"]
    robustness = result["robustness"]
    decision = result["final_decision"]
    tradability = result.get("tradability_filter", {}) or {}
    tradability_lines: list[str] = []
    if tradability:
        tradability_lines = [
            "",
            "## Tradability Filter",
            "",
            f"- accepted symbols after filter: `{len(tradability.get('accepted_symbols', []))}`",
            f"- tradability rejections: `{len(tradability.get('rejections', {}))}`",
            f"- minimum price: `{tradability.get('min_price')}`",
            f"- minimum median turnover: `{tradability.get('min_median_turnover')}`",
        ]
    return "\n".join(
        [
            "# Norgate Portfolio Trial Backtest 001",
            "",
            f"- decision: `{decision['decision']}`",
            f"- bundle: `{bundle.get('bundle_id')}`",
            f"- trial limited: `{str(result.get('trial_limited')).lower()}`",
            f"- total trades: `{summary['total_trades']}`",
            f"- weighted net return sum: `{summary['weighted_net_return_sum']:.6f}`",
            f"- max drawdown: `{summary['max_drawdown']:.6f}`",
            f"- ex-best-symbol weighted net return: `{robustness['ex_best_symbol_weighted_net_return']:.6f}`",
            f"- active symbols: `{result['symbol_counts']['active']}`",
            f"- delisted symbols: `{result['symbol_counts']['delisted']}`",
            *tradability_lines,
            "",
            "## Disabled Sleeves",
            "",
            *[f"- `{sleeve}`: {reason}" for sleeve, reason in DISABLED_SLEEVES.items()],
            "",
            "## Final Blockers",
            "",
            *[f"- `{blocker}`" for blocker in decision.get("blockers", [])],
            "",
            "No promotion, paper trading, live trading, parameter sweep, or durable financial performance claim is allowed from this trial-limited run.",
        ]
    )
