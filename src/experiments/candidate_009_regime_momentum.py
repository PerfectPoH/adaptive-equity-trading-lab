from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.experiments.candidate_004_regime_attribution import build_market_regime_map
from src.experiments.candidate_008_norgate_oos_baseline import (
    _benchmark_summary,
    _equity_curve,
    _robustness,
    _score,
    _summary_by_split,
    _tradable_asof,
    _trade_from_signal,
    build_frames_from_candidate_007_dataset,
)


RUN_ID = "CANDIDATE-009-REGIME-MOMENTUM-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_009_regime_momentum_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
_TRADE_LOG_COLUMNS = [
    "symbol",
    "sleeve",
    "signal_date",
    "entry_date",
    "exit_date",
    "entry_price",
    "exit_price",
    "score",
    "gross_return",
    "cost_return",
    "net_return",
    "per_trade_weight",
    "weighted_net_return",
    "forced_end_of_history_exit",
    "provider_query_performed",
    "regime_label",
    "route_weight",
    "split",
]


def generate_candidate_009_trades(
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    regime_map: pd.DataFrame,
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    all_dates = sorted({date for symbol in symbols if symbol in frames for date in frames[symbol].index})
    min_history = int(contract["tradability"]["min_history_rows"])
    rebalance_every = int(contract["rebalance_every_n_trading_days"])
    regime_by_date = _regime_by_date(regime_map)
    rebalance_dates = all_dates[min_history::rebalance_every]
    trades: list[dict[str, Any]] = []
    for signal_date in rebalance_dates:
        regime_label = regime_by_date.get(signal_date.date().isoformat(), "UNMAPPED")
        route = contract.get("routes", {}).get(regime_label, {})
        route_weight = float(route.get("momentum_60d", 0.0))
        if route_weight <= 0.0:
            continue
        tradable_symbols = [
            symbol
            for symbol in symbols
            if symbol in frames and _tradable_asof(symbol, frames[symbol], signal_date, contract["tradability"])
        ]
        trades.extend(
            _momentum_trades_for_route(
                tradable_symbols,
                frames,
                signal_date,
                regime_label=regime_label,
                route_weight=route_weight,
                sleeve_contract=contract["sleeves"]["momentum_60d"],
                cost_bps=int(contract["cost_bps_round_trip"]),
            )
        )
    return trades


def run_candidate_009_regime_momentum(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    dataset_dir = Path(gate["linked_dataset"])
    frames, symbols, benchmarks, master = build_frames_from_candidate_007_dataset(dataset_dir)
    regime_map = build_market_regime_map(frames["SPY"], frames["IWM"])
    trades = generate_candidate_009_trades(symbols, frames, regime_map, gate["strategy_contract"])
    trade_log = pd.DataFrame(trades)
    if trade_log.empty:
        trade_log = pd.DataFrame(columns=_TRADE_LOG_COLUMNS)
    oos_start = pd.Timestamp(gate["oos_split"]["out_of_sample_start"])
    if not trade_log.empty:
        trade_log["split"] = pd.to_datetime(trade_log["entry_date"]).apply(lambda date: "oos" if date >= oos_start else "is")

    equity = _equity_curve(trade_log)
    summary_by_split = _summary_by_split(trade_log)
    robustness = _robustness(trade_log)
    benchmark = _benchmark_summary(frames, gate["oos_split"])
    route_summary = _route_summary(trade_log)
    blockers = _blockers(summary_by_split, robustness, benchmark, gate["robustness_gates"])
    performance_gates_passed = _performance_gates_passed(blockers)
    decision = "CANDIDATE_009_REGIME_MOMENTUM_ARCHIVE_NO_PROMOTION"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_dataset": str(dataset_dir),
        "linked_autopsy": gate.get("linked_autopsy"),
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
        "post_autopsy_same_panel": bool(gate.get("post_autopsy_same_panel")),
        "trial_limited": True,
        "strategy_contract": gate["strategy_contract"],
        "oos_split": gate["oos_split"],
        "symbol_counts": {
            "research_symbols": len(symbols),
            "benchmarks": len(benchmarks),
            "frames": len(frames),
            "active_symbols": int(master["universe_status"].astype(str).eq("active").sum()),
            "delisted_symbols": int(master["is_delisted"].astype(bool).sum()) if "is_delisted" in master else 0,
        },
        "summary_by_split": summary_by_split,
        "route_summary": route_summary,
        "robustness": robustness,
        "benchmark": benchmark,
        "performance_gates_passed": performance_gates_passed,
        "final_decision": {
            "decision": decision,
            "blockers": blockers,
            "performance_gates_passed": performance_gates_passed,
            "promotion_allowed": False,
            "research_candidate_only": False,
            "provider_query_performed": False,
            "market_data_download_performed": False,
            "parameter_sweep_performed": False,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "trade_log.csv", trade_log)
    _write_csv(output_dir / "equity_curve.csv", equity)
    _write_csv(output_dir / "market_regime_map.csv", regime_map)
    _write_csv(output_dir / "route_summary.csv", pd.DataFrame(route_summary))
    _write_json(output_dir / "candidate_009_regime_momentum_result.json", result)
    _write_json(output_dir / "final_decision.json", result["final_decision"])
    (output_dir / "candidate_009_regime_momentum_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _momentum_trades_for_route(
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    signal_date: pd.Timestamp,
    *,
    regime_label: str,
    route_weight: float,
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
    ranked.sort(key=lambda item: (item[1], item[0]), reverse=True)
    selected = ranked[:top_k]
    if not selected:
        return []
    per_trade_weight = route_weight / len(selected)
    trades: list[dict[str, Any]] = []
    for symbol, score in selected:
        trade = _trade_from_signal(
            symbol,
            frames[symbol],
            signal_date,
            int(sleeve_contract["holding_days"]),
            sleeve="momentum_60d",
            score=score,
            cost_bps=cost_bps,
            per_trade_weight=per_trade_weight,
        )
        if trade:
            trade["regime_label"] = regime_label
            trade["route_weight"] = route_weight
            trades.append(trade)
    return trades


def _route_summary(trade_log: pd.DataFrame) -> list[dict[str, Any]]:
    if trade_log.empty:
        return []
    rows: list[dict[str, Any]] = []
    for (split, regime), data in trade_log.groupby(["split", "regime_label"], dropna=False):
        rows.append(
            {
                "split": str(split),
                "regime_label": str(regime),
                "trade_count": int(len(data)),
                "weighted_net_sum": float(data["weighted_net_return"].sum()),
                "median_net_return": float(data["net_return"].median()),
                "win_rate": float((data["net_return"] > 0).mean()),
            }
        )
    return sorted(rows, key=lambda row: (row["split"], row["regime_label"]))


def _blockers(
    summary: dict[str, dict[str, Any]],
    robustness: dict[str, Any],
    benchmark: dict[str, Any],
    gates: dict[str, Any],
) -> list[str]:
    blockers = ["diagnostic_only_post_autopsy_same_panel", "trial_limited_two_year_history"]
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


def _performance_gates_passed(blockers: list[str]) -> bool:
    methodological = {"diagnostic_only_post_autopsy_same_panel", "trial_limited_two_year_history"}
    return not [blocker for blocker in blockers if blocker not in methodological]


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_ONE_POST_AUTOPSY_REGIME_MOMENTUM_BACKTEST_DIAGNOSTIC_ONLY":
        raise RuntimeError("Candidate 009 gate is not approved.")
    if gate.get("allowed_backtest_count") != 1:
        raise RuntimeError("Gate must authorize exactly one backtest.")
    contract = gate.get("strategy_contract", {})
    if "mean_reversion_5d" in contract.get("sleeves", {}):
        raise RuntimeError("Candidate 009 cannot enable mean_reversion_5d.")
    for regime, route in contract.get("routes", {}).items():
        unexpected = set(route) - {"momentum_60d"}
        if unexpected:
            raise RuntimeError(f"Candidate 009 route {regime} enables unexpected sleeves: {sorted(unexpected)}")
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


def _regime_by_date(regime_map: pd.DataFrame) -> dict[str, str]:
    if regime_map.empty:
        return {}
    return {str(row["date"]): str(row["regime_label"]) for row in regime_map.to_dict(orient="records")}


def _markdown_report(result: dict[str, Any]) -> str:
    oos = result["summary_by_split"]["oos"]
    is_summary = result["summary_by_split"]["is"]
    lines = [
        "# Candidate 009 Regime Momentum 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: one post-autopsy diagnostic backtest. It only routes momentum_60d through RECOVERY_BOUNCE and DRAWDOWN_STRESS.",
        "No provider query, no parameter sweep, no Kronos inference, no promotion.",
        "",
        "## IS/OOS Summary",
        "",
        f"- IS trades: `{is_summary['trade_count']}`",
        f"- IS weighted net: `{is_summary['weighted_net_sum']}`",
        f"- OOS trades: `{oos['trade_count']}`",
        f"- OOS weighted net: `{oos['weighted_net_sum']}`",
        f"- OOS win rate: `{oos['win_rate']}`",
        f"- OOS max drawdown: `{oos['max_drawdown']}`",
        f"- OOS ex-top3 weighted net: `{result['robustness']['oos_ex_top3_weighted_net_sum']}`",
        "",
        "## Benchmarks",
        "",
        f"- SPY OOS return: `{result['benchmark'].get('SPY', {}).get('oos_return')}`",
        f"- IWM OOS return: `{result['benchmark'].get('IWM', {}).get('oos_return')}`",
        "",
        "## Route Summary",
        "",
    ]
    for row in result["route_summary"]:
        lines.append(
            f"- `{row['split']}` / `{row['regime_label']}`: trades `{row['trade_count']}`, "
            f"weighted net `{row['weighted_net_sum']}`, win rate `{row['win_rate']}`"
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
        frame.to_csv(path, index=False)
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(frame.columns))
        writer.writeheader()
        writer.writerows(frame.to_dict(orient="records"))


if __name__ == "__main__":
    run_candidate_009_regime_momentum()
