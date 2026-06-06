from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "CANDIDATE-008-NORGATE-OOS-BASELINE-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_008_norgate_oos_baseline_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID


def build_frames_from_candidate_007_dataset(dataset_dir: Path) -> tuple[dict[str, pd.DataFrame], list[str], set[str], pd.DataFrame]:
    prices = pd.read_csv(dataset_dir / "prices.csv")
    master = pd.read_csv(dataset_dir / "security_master.csv")
    benchmarks = set(master.loc[master["universe_status"].astype(str).eq("benchmark"), "symbol"].astype(str))
    research_symbols = sorted(
        symbol
        for symbol in master.loc[~master["universe_status"].astype(str).eq("benchmark"), "symbol"].astype(str).tolist()
    )
    frames: dict[str, pd.DataFrame] = {}
    for symbol, group in prices.groupby("symbol"):
        data = group.copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values("date").set_index("date")
        frames[str(symbol)] = pd.DataFrame(
            {
                "Open": pd.to_numeric(data["open"], errors="coerce"),
                "High": pd.to_numeric(data["high"], errors="coerce"),
                "Low": pd.to_numeric(data["low"], errors="coerce"),
                "Close": pd.to_numeric(data["close"], errors="coerce"),
                "Volume": pd.to_numeric(data["volume"], errors="coerce"),
            }
        ).dropna()
    return frames, research_symbols, benchmarks, master


def generate_candidate_008_trades(symbols: list[str], frames: dict[str, pd.DataFrame], contract: dict[str, Any]) -> list[dict[str, Any]]:
    all_dates = sorted({date for symbol in symbols if symbol in frames for date in frames[symbol].index})
    min_history = int(contract["tradability"]["min_history_rows"])
    rebalance_every = int(contract["rebalance_every_n_trading_days"])
    rebalance_dates = all_dates[min_history::rebalance_every]
    trades: list[dict[str, Any]] = []
    for signal_date in rebalance_dates:
        tradable_symbols = [
            symbol
            for symbol in symbols
            if symbol in frames and _tradable_asof(symbol, frames[symbol], signal_date, contract["tradability"])
        ]
        for sleeve, sleeve_contract in contract["sleeves"].items():
            trades.extend(_trades_for_sleeve(sleeve, tradable_symbols, frames, signal_date, sleeve_contract, int(contract["cost_bps_round_trip"])))
    return trades


def run_candidate_008_norgate_oos_baseline(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    dataset_dir = Path(gate["linked_dataset"])
    frames, symbols, benchmarks, master = build_frames_from_candidate_007_dataset(dataset_dir)
    trades = generate_candidate_008_trades(symbols, frames, gate["strategy_contract"])
    trade_log = pd.DataFrame(trades)
    oos_start = pd.Timestamp(gate["oos_split"]["out_of_sample_start"])
    if not trade_log.empty:
        trade_log["split"] = pd.to_datetime(trade_log["entry_date"]).where(lambda s: s >= oos_start, other=pd.NaT)
        trade_log["split"] = pd.to_datetime(trade_log["entry_date"]).apply(lambda date: "oos" if date >= oos_start else "is")
    equity = _equity_curve(trade_log)
    summary_by_split = _summary_by_split(trade_log)
    robustness = _robustness(trade_log)
    benchmark = _benchmark_summary(frames, gate["oos_split"])
    blockers = _blockers(summary_by_split, robustness, benchmark, gate["robustness_gates"])
    decision = (
        "CANDIDATE_008_NORGATE_OOS_BASELINE_RESEARCH_CANDIDATE_ONLY"
        if not blockers
        else "CANDIDATE_008_NORGATE_OOS_BASELINE_ARCHIVE_NO_PROMOTION"
    )
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_dataset": str(dataset_dir),
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "portfolio_backtest_performed": True,
        "kronos_inference_performed": False,
        "portfolio_search_performed": False,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "trial_limited": True,
        "strategy_contract": gate["strategy_contract"],
        "oos_split": gate["oos_split"],
        "symbol_counts": {
            "research_symbols": len(symbols),
            "benchmarks": len(benchmarks),
            "frames": len(frames),
            "active_symbols": int(master["universe_status"].astype(str).eq("active").sum()),
            "delisted_symbols": int(master["is_delisted"].astype(bool).sum()),
        },
        "summary_by_split": summary_by_split,
        "robustness": robustness,
        "benchmark": benchmark,
        "final_decision": {
            "decision": decision,
            "blockers": blockers,
            "promotion_allowed": False,
            "research_candidate_only": decision.endswith("RESEARCH_CANDIDATE_ONLY"),
            "provider_query_performed": False,
            "market_data_download_performed": False,
            "parameter_sweep_performed": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "trade_log.csv", trade_log)
    _write_csv(output_dir / "equity_curve.csv", equity)
    _write_json(output_dir / "candidate_008_norgate_oos_baseline_result.json", result)
    _write_json(output_dir / "final_decision.json", result["final_decision"])
    (output_dir / "candidate_008_norgate_oos_baseline_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _tradable_asof(symbol: str, frame: pd.DataFrame, signal_date: pd.Timestamp, tradability: dict[str, Any]) -> bool:
    data = frame[frame.index <= signal_date].copy()
    min_history = int(tradability["min_history_rows"])
    if len(data) < min_history:
        return False
    close = float(data["Close"].iloc[-1])
    if close < float(tradability["min_price_asof"]):
        return False
    trailing = data.tail(20)
    turnover = trailing["Close"] * trailing["Volume"]
    return float(turnover.median()) >= float(tradability["min_trailing_20d_median_turnover"])


def _trades_for_sleeve(
    sleeve: str,
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    signal_date: pd.Timestamp,
    sleeve_contract: dict[str, Any],
    cost_bps: int,
) -> list[dict[str, Any]]:
    lookback = int(sleeve_contract["lookback_days"])
    top_k = int(sleeve_contract["top_k"])
    ranked: list[tuple[str, float]] = []
    for symbol in symbols:
        score = _score(frames[symbol], signal_date, lookback)
        if score is not None:
            ranked.append((symbol, score))
    reverse = sleeve_contract["rank_direction"] == "highest_return"
    ranked.sort(key=lambda item: (item[1], item[0]), reverse=reverse)
    selected = ranked[:top_k]
    if not selected:
        return []
    per_trade_weight = float(sleeve_contract["sleeve_weight"]) / len(selected)
    trades = []
    for symbol, score in selected:
        trade = _trade_from_signal(
            symbol,
            frames[symbol],
            signal_date,
            int(sleeve_contract["holding_days"]),
            sleeve=sleeve,
            score=score,
            cost_bps=cost_bps,
            per_trade_weight=per_trade_weight,
        )
        if trade:
            trades.append(trade)
    return trades


def _score(frame: pd.DataFrame, signal_date: pd.Timestamp, lookback: int) -> float | None:
    data = frame[frame.index <= signal_date]
    if len(data) <= lookback:
        return None
    current = float(data["Close"].iloc[-1])
    prior = float(data["Close"].iloc[-lookback - 1])
    if prior <= 0:
        return None
    return current / prior - 1.0


def _trade_from_signal(
    symbol: str,
    frame: pd.DataFrame,
    signal_date: pd.Timestamp,
    holding_days: int,
    *,
    sleeve: str,
    score: float,
    cost_bps: int,
    per_trade_weight: float,
) -> dict[str, Any] | None:
    data = frame.sort_index()
    valid_dates = data.index[data.index <= signal_date]
    if len(valid_dates) == 0:
        return None
    signal_pos = data.index.get_loc(valid_dates[-1])
    entry_pos = signal_pos + 1
    if entry_pos >= len(data):
        return None
    exit_pos = min(entry_pos + holding_days, len(data) - 1)
    entry_date = data.index[entry_pos]
    exit_date = data.index[exit_pos]
    entry = float(data.loc[entry_date, "Open"])
    exit_price = float(data.loc[exit_date, "Close"])
    if entry <= 0 or exit_price <= 0:
        return None
    gross = exit_price / entry - 1.0
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
        "per_trade_weight": per_trade_weight,
        "weighted_net_return": net * per_trade_weight,
        "forced_end_of_history_exit": exit_pos < entry_pos + holding_days,
        "provider_query_performed": False,
    }


def _equity_curve(trade_log: pd.DataFrame) -> pd.DataFrame:
    if trade_log.empty:
        return pd.DataFrame(columns=["date", "period_net_return", "cumulative_weighted_net_return", "drawdown"])
    data = trade_log.copy()
    data["date"] = pd.to_datetime(data["exit_date"])
    grouped = data.groupby("date", as_index=False)["weighted_net_return"].sum().sort_values("date")
    grouped = grouped.rename(columns={"weighted_net_return": "period_net_return"})
    grouped["cumulative_weighted_net_return"] = grouped["period_net_return"].cumsum()
    grouped["running_peak"] = grouped["cumulative_weighted_net_return"].cummax()
    grouped["drawdown"] = grouped["cumulative_weighted_net_return"] - grouped["running_peak"]
    return grouped.drop(columns=["running_peak"])


def _summary_by_split(trade_log: pd.DataFrame) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for split in ("is", "oos"):
        data = trade_log[trade_log["split"] == split] if not trade_log.empty and "split" in trade_log else pd.DataFrame()
        equity = _equity_curve(data)
        summaries[split] = {
            "trade_count": int(len(data)),
            "weighted_net_sum": float(data["weighted_net_return"].sum()) if not data.empty else 0.0,
            "median_net_return": float(data["net_return"].median()) if not data.empty else 0.0,
            "win_rate": float((data["net_return"] > 0).mean()) if not data.empty else 0.0,
            "max_drawdown": float(equity["drawdown"].min()) if not equity.empty else 0.0,
        }
    return summaries


def _robustness(trade_log: pd.DataFrame) -> dict[str, Any]:
    if trade_log.empty:
        return {"oos_ex_top3_weighted_net_sum": 0.0, "oos_top3_weighted_net_sum": 0.0}
    oos = trade_log[trade_log["split"] == "oos"].copy()
    ranked = oos.sort_values("weighted_net_return", ascending=False)
    top3 = ranked.head(3)
    ex_top3 = ranked.iloc[3:]
    return {
        "oos_top3_weighted_net_sum": float(top3["weighted_net_return"].sum()) if not top3.empty else 0.0,
        "oos_ex_top3_weighted_net_sum": float(ex_top3["weighted_net_return"].sum()) if not ex_top3.empty else 0.0,
        "oos_best_symbol": str(oos.groupby("symbol")["weighted_net_return"].sum().sort_values(ascending=False).index[0]) if not oos.empty else None,
    }


def _benchmark_summary(frames: dict[str, pd.DataFrame], split: dict[str, str]) -> dict[str, Any]:
    start = pd.Timestamp(split["out_of_sample_start"])
    result: dict[str, Any] = {}
    for symbol in ("SPY", "IWM"):
        frame = frames.get(symbol)
        if frame is None or frame.empty:
            result[symbol] = {"oos_return": None}
            continue
        data = frame[frame.index >= start]
        if len(data) < 2:
            result[symbol] = {"oos_return": None}
            continue
        result[symbol] = {"oos_return": float(data["Close"].iloc[-1] / data["Open"].iloc[0] - 1.0)}
    return result


def _blockers(summary: dict[str, dict[str, Any]], robustness: dict[str, Any], benchmark: dict[str, Any], gates: dict[str, Any]) -> list[str]:
    blockers = ["diagnostic_only_no_promotion", "trial_limited_two_year_history"]
    oos = summary["oos"]
    if oos["trade_count"] < int(gates["min_oos_trades"]):
        blockers.append("oos_trade_count_below_threshold")
    if gates.get("require_positive_oos_net") and oos["weighted_net_sum"] <= 0:
        blockers.append("oos_weighted_net_nonpositive")
    if gates.get("require_positive_ex_top3_oos_net") and robustness["oos_ex_top3_weighted_net_sum"] <= 0:
        blockers.append("oos_ex_top3_weighted_net_nonpositive")
    if gates.get("require_oos_beats_spy"):
        spy = benchmark.get("SPY", {}).get("oos_return")
        if spy is None or oos["weighted_net_sum"] <= spy:
            blockers.append("oos_does_not_beat_spy")
    if gates.get("require_oos_beats_iwm"):
        iwm = benchmark.get("IWM", {}).get("oos_return")
        if iwm is None or oos["weighted_net_sum"] <= iwm:
            blockers.append("oos_does_not_beat_iwm")
    return blockers


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_ONE_NORGATE_OOS_BASELINE_BACKTEST_DIAGNOSTIC_ONLY":
        raise RuntimeError("Candidate 008 gate is not approved.")
    if gate.get("allowed_backtest_count") != 1:
        raise RuntimeError("Gate must authorize exactly one backtest.")
    for key in (
        "provider_query_allowed",
        "market_data_download_allowed",
        "kronos_inference_allowed",
        "portfolio_search_allowed",
        "parameter_sweep_allowed",
        "promotion_allowed",
        "paper_trading_allowed",
        "live_trading_allowed",
    ):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")


def _markdown_report(result: dict[str, Any]) -> str:
    oos = result["summary_by_split"]["oos"]
    is_summary = result["summary_by_split"]["is"]
    lines = [
        "# Candidate 008 Norgate OOS Baseline 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: one fixed diagnostic backtest on Candidate 007. No provider query, no sweep, no promotion.",
        "",
        "## IS/OOS Summary",
        "",
        f"- IS trades: `{is_summary['trade_count']}`",
        f"- IS weighted net: `{is_summary['weighted_net_sum']}`",
        f"- OOS trades: `{oos['trade_count']}`",
        f"- OOS weighted net: `{oos['weighted_net_sum']}`",
        f"- OOS win rate: `{oos['win_rate']}`",
        f"- OOS max drawdown: `{oos['max_drawdown']}`",
        "",
        "## Benchmarks",
        "",
        f"- SPY OOS return: `{result['benchmark'].get('SPY', {}).get('oos_return')}`",
        f"- IWM OOS return: `{result['benchmark'].get('IWM', {}).get('oos_return')}`",
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
        frame.to_csv(path, index=False)
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(frame.columns))
        writer.writeheader()
        writer.writerows(frame.to_dict(orient="records"))


if __name__ == "__main__":
    run_candidate_008_norgate_oos_baseline()
