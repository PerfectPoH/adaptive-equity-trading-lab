from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.experiments.candidate_004_regime_attribution import build_market_regime_map
from src.experiments.norgate_portfolio_trial_backtest import build_tradability_filtered_frames


RUN_ID = "CANDIDATE-005-RECOVERY-BREADTH-BACKTEST-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_005_recovery_breadth_gate_20260602")
REPRESENTATIVE_SYMBOLS = Path(
    "experiments/provider_aware_research/execution_outputs/NORGATE-CANDIDATE-003-REPRESENTATIVE-UNIVERSE-001/representative_universe_symbols.csv"
)
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID


def run_candidate_005_recovery_breadth_backtest(
    *,
    output_dir: Path = OUTPUT_DIR,
    gate_dir: Path = GATE_DIR,
    representative_symbols_path: Path = REPRESENTATIVE_SYMBOLS,
    frames: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    contract = gate["strategy_contract"]
    provider_query_performed = False
    if frames is None:
        symbols = _accepted_representative_symbols(representative_symbols_path)
        frames = _load_norgate_frames([*symbols, "SPY", "IWM"])
        provider_query_performed = True
    else:
        symbols = sorted(symbol for symbol in frames if symbol not in {"SPY", "IWM"})

    filtered_frames, tradability = build_tradability_filtered_frames(
        {symbol: frame for symbol, frame in frames.items() if symbol not in {"SPY", "IWM"}},
        min_price=float(contract["tradability_min_price"]),
        min_median_turnover=float(contract["tradability_min_median_turnover"]),
        min_rows=90,
    )
    tradable_symbols = [symbol for symbol in symbols if symbol in filtered_frames]
    regime_map = build_market_regime_map(frames["SPY"], frames["IWM"])
    trades = generate_recovery_breadth_trades(
        tradable_symbols,
        filtered_frames,
        regime_map,
        lookback_days=int(contract["lookback_days"]),
        holding_days=int(contract["holding_days"]),
        top_k=int(contract["top_k"]),
        min_candidates=int(contract["min_candidates_per_rebalance"]),
        per_trade_weight=float(contract["per_trade_weight"]),
        cost_bps=int(contract["cost_bps"]),
    )
    trade_log = pd.DataFrame(trades)
    equity = _build_equity_curve(trade_log)
    summary = _summary(trade_log, equity)
    robustness = _robustness(trade_log)
    benchmark = _benchmark_summary(frames)
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "CANDIDATE_005_RECOVERY_BREADTH_BACKTEST_COMPLETE_TRIAL_LIMITED",
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
        "strategy_contract": contract,
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
    }
    result["final_decision"] = _final_decision(result)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "trade_log.csv", trade_log)
    _write_csv(output_dir / "equity_curve.csv", equity)
    _write_csv(output_dir / "market_regime_map.csv", regime_map)
    _write_json(output_dir / "candidate_005_recovery_breadth_backtest_result.json", result)
    _write_json(output_dir / "final_decision.json", result["final_decision"])
    (output_dir / "candidate_005_recovery_breadth_backtest_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def generate_recovery_breadth_trades(
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    regime_map: pd.DataFrame,
    *,
    lookback_days: int,
    holding_days: int,
    top_k: int,
    min_candidates: int,
    per_trade_weight: float,
    cost_bps: int,
) -> list[dict[str, Any]]:
    regime_by_date = {str(row["date"]): str(row["regime_label"]) for row in regime_map.to_dict(orient="records")}
    all_dates = sorted({date for symbol in symbols for date in frames[symbol].index})
    rebalance_dates = all_dates[60::20]
    trades: list[dict[str, Any]] = []
    for signal_date in rebalance_dates:
        if regime_by_date.get(signal_date.date().isoformat()) != "RECOVERY_BOUNCE":
            continue
        ranked = []
        for symbol in symbols:
            score = _score_symbol(frames[symbol], signal_date, lookback_days)
            if score is not None:
                ranked.append((symbol, score))
        if len(ranked) < min_candidates:
            continue
        ranked.sort(key=lambda item: (item[1], item[0]), reverse=True)
        for symbol, score in ranked[:top_k]:
            trade = _trade_from_signal(
                symbol,
                frames[symbol],
                signal_date,
                holding_days,
                score=score,
                cost_bps=cost_bps,
                per_trade_weight=per_trade_weight,
            )
            if trade:
                trades.append(trade)
    return trades


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
    score: float,
    cost_bps: int,
    per_trade_weight: float,
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
        "sleeve": "Recovery Breadth Momentum",
        "regime_label": "RECOVERY_BOUNCE",
        "signal_date": signal_date.date().isoformat(),
        "entry_date": entry_date.date().isoformat(),
        "exit_date": exit_date.date().isoformat(),
        "entry_price": entry,
        "exit_price": exit_price,
        "score": score,
        "gross_return": gross,
        "cost_return": cost,
        "net_return": net,
        "per_trade_weight": per_trade_weight,
        "weighted_net_return": net * per_trade_weight,
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
        raise RuntimeError("SPY and IWM are required for Candidate 005 regime routing.")
    return frames


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_ONE_TRIAL_LIMITED_RECOVERY_BREADTH_BACKTEST":
        raise RuntimeError("Candidate 005 gate is not approved.")
    if gate.get("allowed_backtest_count") != 1:
        raise RuntimeError("Candidate 005 gate must allow exactly one backtest.")
    for key in ("promotion_allowed", "paper_trading_allowed", "live_trading_allowed"):
        if gate.get(key):
            raise RuntimeError(f"Candidate 005 gate unexpectedly allows {key}.")
    constraints = gate.get("anti_overfit_constraints", {})
    if constraints.get("parameter_sweep_allowed") or constraints.get("top_k_change_allowed"):
        raise RuntimeError("Candidate 005 gate must freeze top_k and forbid parameter sweeps.")


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
    rows = {}
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
    return {symbol: total - float(values["total_return"]) for symbol, values in benchmark.items() if values.get("total_return") is not None}


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    robustness = result["robustness"]
    blockers = ["trial_history_window_limited", "promotion_locked_until_long_history_oos_gate"]
    if int(summary["total_trades"]) < 30:
        blockers.append("trade_count_below_30")
    if float(robustness.get("ex_best_symbol_weighted_net_return", 0.0)) <= 0:
        blockers.append("outlier_dependency_ex_best_symbol_nonpositive")
    if float(summary.get("win_rate", 0.0)) < 0.5:
        blockers.append("weak_distribution_win_rate_below_half")
    if float(robustness.get("symbol_concentration_top1") or 0.0) > 0.30:
        blockers.append("single_symbol_concentration_above_30pct")
    relative = result["benchmark_relative"]
    if relative and any(value <= 0 for value in relative.values()):
        blockers.append("benchmark_relative_not_positive")
    return {
        "decision": "CANDIDATE_005_RECOVERY_BREADTH_BACKTEST_ARCHIVE_NO_PROMOTION",
        "blockers": blockers,
        "provider_query_performed": result["provider_query_performed"],
        "market_data_download_performed": False,
        "portfolio_backtest_performed": True,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "next_allowed_action": "review_candidate_005_recovery_breadth_backtest",
    }


def _markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    robustness = result["robustness"]
    lines = [
        "# Candidate 005 Recovery Breadth Backtest 001",
        "",
        f"Decision: `{result['final_decision']['decision']}`",
        "",
        "Scope: one trial-limited breadth-basket backtest. No parameter sweep, no promotion.",
        "",
        "## Summary",
        "",
        f"- Trades: `{summary['total_trades']}`.",
        f"- Weighted net return sum: `{summary['weighted_net_return_sum']:.6f}`.",
        f"- Win rate: `{summary['win_rate']:.3f}`.",
        f"- Max drawdown: `{summary['max_drawdown']:.6f}`.",
        f"- Best symbol: `{robustness['best_symbol']}`.",
        f"- Ex-best-symbol weighted net: `{robustness['ex_best_symbol_weighted_net_return']:.6f}`.",
        f"- Top-symbol concentration: `{robustness.get('symbol_concentration_top1')}`.",
        "",
        "## Blockers",
        "",
    ]
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
    run_candidate_005_recovery_breadth_backtest()
