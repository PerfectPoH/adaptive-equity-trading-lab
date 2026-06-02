from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.experiments.candidate_004_regime_attribution import build_market_regime_map
from src.experiments.norgate_portfolio_trial_backtest import build_tradability_filtered_frames


RUN_ID = "CANDIDATE-004-REGIME-ROUTED-BACKTEST-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_004_regime_routed_backtest_gate_20260602")
REPRESENTATIVE_SYMBOLS = Path(
    "experiments/provider_aware_research/execution_outputs/NORGATE-CANDIDATE-003-REPRESENTATIVE-UNIVERSE-001/representative_universe_symbols.csv"
)
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID


def run_candidate_004_regime_routed_backtest(
    *,
    output_dir: Path = OUTPUT_DIR,
    gate_dir: Path = GATE_DIR,
    representative_symbols_path: Path = REPRESENTATIVE_SYMBOLS,
    frames: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    provider_query_performed = False
    if frames is None:
        symbols = _accepted_representative_symbols(representative_symbols_path)
        frames = _load_norgate_frames([*symbols, "SPY", "IWM"])
        provider_query_performed = True
    else:
        symbols = sorted(symbol for symbol in frames if symbol not in {"SPY", "IWM"})

    filtered_frames, tradability = build_tradability_filtered_frames(
        {symbol: frame for symbol, frame in frames.items() if symbol not in {"SPY", "IWM"}},
        min_price=1.0,
        min_median_turnover=1_000_000.0,
        min_rows=90,
    )
    tradable_symbols = [symbol for symbol in symbols if symbol in filtered_frames]
    regime_map = build_market_regime_map(frames["SPY"], frames["IWM"])
    trades = generate_regime_routed_trades(
        tradable_symbols,
        filtered_frames,
        regime_map,
        gate["router_contract"]["routes"],
        cost_bps=int(gate["cost_bps"]),
    )
    trade_log = pd.DataFrame(trades)
    equity = _build_equity_curve(trade_log)
    summary = _summary(trade_log, equity)
    robustness = _robustness(trade_log)
    benchmark = _benchmark_summary(frames)
    final_decision = _final_decision(summary, robustness, benchmark)
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "CANDIDATE_004_REGIME_ROUTED_BACKTEST_COMPLETE_TRIAL_LIMITED",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "provider_query_performed": provider_query_performed,
        "provider_query_scope": "accepted_representative_universe_plus_SPY_IWM" if provider_query_performed else "injected_test_frames",
        "market_data_download_performed": False,
        "portfolio_backtest_performed": True,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "trial_limited": True,
        "cost_bps": int(gate["cost_bps"]),
        "router_contract": gate["router_contract"],
        "symbol_counts": {
            "input_non_benchmark": len(symbols),
            "tradable_after_filter": len(tradable_symbols),
            "frames_loaded": len(frames),
        },
        "tradability_filter": tradability,
        "summary": summary,
        "robustness": robustness,
        "benchmark": benchmark,
        "benchmark_relative": _benchmark_relative(summary, benchmark),
        "route_summary": _route_summary(trade_log),
        "final_decision": final_decision,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "trade_log.csv", trade_log)
    _write_csv(output_dir / "equity_curve.csv", equity)
    _write_csv(output_dir / "market_regime_map.csv", regime_map)
    _write_csv(output_dir / "route_summary.csv", pd.DataFrame(result["route_summary"]))
    _write_json(output_dir / "candidate_004_regime_routed_backtest_result.json", result)
    _write_json(output_dir / "final_decision.json", final_decision)
    (output_dir / "candidate_004_regime_routed_backtest_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def generate_regime_routed_trades(
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    regime_map: pd.DataFrame,
    routes: dict[str, dict[str, float]],
    *,
    cost_bps: int,
) -> list[dict[str, Any]]:
    regime_by_date = {str(row["date"]): str(row["regime_label"]) for row in regime_map.to_dict(orient="records")}
    all_dates = sorted({date for symbol in symbols for date in frames[symbol].index})
    rebalance_dates = all_dates[60::20]
    trades: list[dict[str, Any]] = []
    for signal_date in rebalance_dates:
        regime = regime_by_date.get(signal_date.date().isoformat(), "UNMAPPED")
        route = routes.get(regime, {})
        for sleeve in ("Momentum", "Mean Reversion"):
            sleeve_weight = float(route.get(sleeve, 0.0))
            if sleeve_weight <= 0.0:
                continue
            trade = _best_trade_for_sleeve(sleeve, symbols, frames, signal_date, cost_bps=cost_bps, sleeve_weight=sleeve_weight)
            if trade:
                trade["regime_label"] = regime
                trade["route_weight"] = sleeve_weight
                trades.append(trade)
    return trades


def _best_trade_for_sleeve(
    sleeve: str,
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    signal_date: pd.Timestamp,
    *,
    cost_bps: int,
    sleeve_weight: float,
) -> dict[str, Any] | None:
    lookback = 20 if sleeve == "Momentum" else 5
    hold = 20 if sleeve == "Momentum" else 10
    ranked: list[tuple[str, float]] = []
    for symbol in symbols:
        score = _score_symbol(frames[symbol], signal_date, lookback)
        if score is not None:
            ranked.append((symbol, score))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[1], item[0]), reverse=sleeve == "Momentum")
    symbol, score = ranked[0]
    return _trade_from_signal(
        symbol,
        frames[symbol],
        signal_date,
        hold,
        sleeve=sleeve,
        score=score,
        cost_bps=cost_bps,
        sleeve_weight=sleeve_weight,
    )


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
    sleeve_weight: float,
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
        "sleeve_weight": sleeve_weight,
        "weighted_net_return": net * sleeve_weight,
        "forced_end_of_history_exit": exit_pos < entry_pos + hold,
    }


def _accepted_representative_symbols(path: Path) -> list[str]:
    rows = pd.read_csv(path)
    return sorted(str(symbol) for symbol in rows.loc[rows["accepted"].astype(str).str.lower().eq("true"), "symbol"].tolist())


def _load_norgate_frames(symbols: list[str]) -> dict[str, pd.DataFrame]:
    import norgatedata

    frames: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        try:
            frame = norgatedata.price_timeseries(symbol, timeseriesformat="pandas-dataframe")
        except Exception:
            continue
        if frame is None or frame.empty:
            continue
        frame = frame.copy()
        frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
        if {"Open", "High", "Low", "Close", "Volume"}.issubset(frame.columns):
            frames[symbol] = frame.sort_index()
    if "SPY" not in frames or "IWM" not in frames:
        raise RuntimeError("SPY and IWM are required for Candidate 004 regime routing.")
    return frames


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_ONE_TRIAL_LIMITED_REGIME_ROUTED_BACKTEST":
        raise RuntimeError("Candidate 004 regime routed backtest gate is not approved.")
    if gate.get("allowed_backtest_count") != 1:
        raise RuntimeError("Gate must authorize exactly one backtest.")
    forbidden_truthy = ["parameter_sweep_allowed", "promotion_allowed", "paper_trading_allowed", "live_trading_allowed"]
    for key in forbidden_truthy:
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")


def _build_equity_curve(trade_log: pd.DataFrame) -> pd.DataFrame:
    if trade_log.empty:
        return pd.DataFrame(columns=["date", "period_net_return", "cumulative_weighted_net_return", "drawdown"])
    data = trade_log.copy()
    data["date"] = pd.to_datetime(data["exit_date"])
    grouped = data.groupby("date", as_index=False)["weighted_net_return"].sum().sort_values("date")
    grouped["cumulative_weighted_net_return"] = grouped["weighted_net_return"].cumsum()
    grouped["running_peak"] = grouped["cumulative_weighted_net_return"].cummax()
    grouped["drawdown"] = grouped["cumulative_weighted_net_return"] - grouped["running_peak"]
    return grouped.rename(columns={"weighted_net_return": "period_net_return"}).drop(columns=["running_peak"])


def _summary(trade_log: pd.DataFrame, equity_curve: pd.DataFrame) -> dict[str, Any]:
    if trade_log.empty:
        return {"total_trades": 0, "weighted_net_return_sum": 0.0, "gross_return_sum": 0.0, "win_rate": 0.0, "max_drawdown": 0.0}
    return {
        "total_trades": int(len(trade_log)),
        "weighted_net_return_sum": float(trade_log["weighted_net_return"].sum()),
        "gross_return_sum": float(trade_log["gross_return"].sum()),
        "win_rate": float((trade_log["net_return"] > 0).mean()),
        "max_drawdown": float(equity_curve["drawdown"].min()) if not equity_curve.empty else 0.0,
    }


def _robustness(trade_log: pd.DataFrame) -> dict[str, Any]:
    if trade_log.empty:
        return {"best_symbol": None, "best_symbol_weighted_net_return": 0.0, "ex_best_symbol_weighted_net_return": 0.0}
    by_symbol = trade_log.groupby("symbol")["weighted_net_return"].sum().sort_values(ascending=False)
    total = float(by_symbol.sum())
    return {
        "best_symbol": str(by_symbol.index[0]),
        "best_symbol_weighted_net_return": float(by_symbol.iloc[0]),
        "ex_best_symbol_weighted_net_return": float(total - by_symbol.iloc[0]),
        "symbol_concentration_top1": float(by_symbol.iloc[0] / total) if total else None,
    }


def _benchmark_summary(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for symbol in ("SPY", "IWM"):
        frame = frames.get(symbol)
        if frame is None or len(frame) < 2:
            continue
        start = float(frame["Close"].iloc[0])
        end = float(frame["Close"].iloc[-1])
        rows[symbol] = {"total_return": (end / start) - 1.0 if start else None}
    return rows


def _benchmark_relative(summary: dict[str, Any], benchmark: dict[str, Any]) -> dict[str, float]:
    total = float(summary.get("weighted_net_return_sum", 0.0))
    return {
        symbol: total - float(values["total_return"])
        for symbol, values in benchmark.items()
        if values.get("total_return") is not None
    }


def _route_summary(trade_log: pd.DataFrame) -> list[dict[str, Any]]:
    if trade_log.empty:
        return []
    rows: list[dict[str, Any]] = []
    for (regime, sleeve), group in trade_log.groupby(["regime_label", "sleeve"]):
        rows.append(
            {
                "regime_label": str(regime),
                "sleeve": str(sleeve),
                "trade_count": int(len(group)),
                "weighted_net_return_sum": float(group["weighted_net_return"].sum()),
                "median_net_return": float(group["net_return"].median()),
                "win_rate": float((group["net_return"] > 0).mean()),
            }
        )
    return sorted(rows, key=lambda row: (row["regime_label"], row["sleeve"]))


def _final_decision(summary: dict[str, Any], robustness: dict[str, Any], benchmark: dict[str, Any]) -> dict[str, Any]:
    blockers = ["trial_history_window_limited", "promotion_locked_until_long_history_oos_gate"]
    if int(summary.get("total_trades", 0)) < 20:
        blockers.append("sample_starved_regime_router")
    if float(robustness.get("ex_best_symbol_weighted_net_return", 0.0)) <= 0:
        blockers.append("outlier_dependency_ex_best_symbol_nonpositive")
    if float(summary.get("win_rate", 0.0)) < 0.5:
        blockers.append("weak_distribution_win_rate_below_half")
    relative = _benchmark_relative(summary, benchmark)
    if relative and any(value <= 0 for value in relative.values()):
        blockers.append("benchmark_relative_not_positive")
    return {
        "decision": "CANDIDATE_004_REGIME_ROUTED_BACKTEST_ARCHIVE_NO_PROMOTION",
        "blockers": blockers,
        "provider_query_performed": True,
        "market_data_download_performed": False,
        "portfolio_backtest_performed": True,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "next_allowed_action": "review_candidate_004_regime_routed_backtest",
    }


def _markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    robustness = result["robustness"]
    lines = [
        "# Candidate 004 Regime-Routed Backtest 001",
        "",
        f"Decision: `{result['final_decision']['decision']}`",
        "",
        "Scope: one trial-limited Norgate backtest under the pre-committed regime router. No parameter sweep, no promotion.",
        "",
        "## Summary",
        "",
        f"- Trades: `{summary['total_trades']}`.",
        f"- Weighted net return sum: `{summary['weighted_net_return_sum']:.6f}`.",
        f"- Win rate: `{summary['win_rate']:.3f}`.",
        f"- Max drawdown: `{summary['max_drawdown']:.6f}`.",
        f"- Best symbol: `{robustness['best_symbol']}`.",
        f"- Ex-best-symbol weighted net: `{robustness['ex_best_symbol_weighted_net_return']:.6f}`.",
        "",
        "## Route Summary",
        "",
    ]
    for row in result["route_summary"]:
        lines.append(
            f"- {row['regime_label']} / {row['sleeve']}: trades={row['trade_count']} "
            f"weighted_net={row['weighted_net_return_sum']:.6f} win_rate={row['win_rate']:.3f}"
        )
    lines.extend(["", "## Blockers", ""])
    for blocker in result["final_decision"]["blockers"]:
        lines.append(f"- `{blocker}`")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    if frame.empty:
        path.write_text("", encoding="utf-8")
    else:
        frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


if __name__ == "__main__":
    run_candidate_004_regime_routed_backtest()
