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
    _summary_by_split,
    _tradable_asof,
    _trade_from_signal,
    build_frames_from_candidate_007_dataset,
)


RUN_ID = "CANDIDATE-011-RISK-OFF-MEAN-REVERSION-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_011_risk_off_mean_reversion_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
TRADE_COLUMNS = [
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
    "split",
]


def generate_candidate_011_trades(
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    regime_map: pd.DataFrame,
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    all_dates = sorted({date for symbol in symbols if symbol in frames for date in frames[symbol].index})
    min_history = int(contract["tradability"]["min_history_rows"])
    rebalance_every = int(contract["rebalance_every_n_trading_days"])
    regime_by_date = _regime_by_date(regime_map)
    allowed_regimes = set(contract["allowed_regimes"])
    rebalance_dates = all_dates[min_history::rebalance_every]
    trades: list[dict[str, Any]] = []
    for signal_date in rebalance_dates:
        regime_label = regime_by_date.get(signal_date.date().isoformat(), "UNMAPPED")
        if regime_label not in allowed_regimes:
            continue
        tradable_symbols = [
            symbol
            for symbol in symbols
            if symbol in frames and _tradable_asof(symbol, frames[symbol], signal_date, contract["tradability"])
        ]
        trades.extend(
            _risk_off_mean_reversion_trades(
                tradable_symbols,
                frames,
                signal_date,
                regime_label=regime_label,
                sleeve_contract=contract["sleeve"],
                cost_bps=int(contract["cost_bps_round_trip"]),
            )
        )
    return trades


def run_candidate_011_risk_off_mean_reversion(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    dataset_dir = Path(gate["linked_dataset"])
    frames, symbols, benchmarks, master = build_frames_from_candidate_007_dataset(dataset_dir)
    regime_map = build_market_regime_map(frames["SPY"], frames["IWM"])
    trades = generate_candidate_011_trades(symbols, frames, regime_map, gate["strategy_contract"])
    trade_log = pd.DataFrame(trades)
    if trade_log.empty:
        trade_log = pd.DataFrame(columns=TRADE_COLUMNS)
    oos_start = pd.Timestamp(gate["oos_split"]["out_of_sample_start"])
    if not trade_log.empty:
        trade_log["split"] = pd.to_datetime(trade_log["entry_date"]).apply(lambda date: "oos" if date >= oos_start else "is")

    equity = _equity_curve(trade_log)
    summary_by_split = _summary_by_split(trade_log)
    robustness = _robustness(trade_log)
    benchmark = _benchmark_summary(frames, gate["oos_split"])
    regime_summary = _regime_summary(trade_log)
    blockers = _blockers(summary_by_split, robustness, benchmark, gate["robustness_gates"])
    performance_gates_passed = _performance_gates_passed(blockers)
    decision = "CANDIDATE_011_RISK_OFF_MEAN_REVERSION_ARCHIVE_NO_PROMOTION"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_dataset": str(dataset_dir),
        "linked_candidate_010": gate.get("linked_candidate_010"),
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
        "same_dataset_as_discovery": bool(gate.get("same_dataset_as_discovery")),
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
        "regime_summary": regime_summary,
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
    _write_csv(output_dir / "regime_summary.csv", pd.DataFrame(regime_summary))
    _write_json(output_dir / "candidate_011_risk_off_mean_reversion_result.json", result)
    _write_json(output_dir / "final_decision.json", result["final_decision"])
    (output_dir / "candidate_011_risk_off_mean_reversion_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _risk_off_mean_reversion_trades(
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    signal_date: pd.Timestamp,
    *,
    regime_label: str,
    sleeve_contract: dict[str, Any],
    cost_bps: int,
) -> list[dict[str, Any]]:
    lookback = int(sleeve_contract["lookback_days"])
    top_k = int(sleeve_contract["top_k"])
    ranked: list[tuple[str, float]] = []
    for symbol in symbols:
        score = _return_score(frames[symbol], signal_date, lookback)
        if score is not None:
            ranked.append((symbol, score))
    ranked.sort(key=lambda item: (item[1], item[0]))
    selected = ranked[:top_k]
    if not selected:
        return []
    per_trade_weight = 1.0 / len(selected)
    trades: list[dict[str, Any]] = []
    for symbol, score in selected:
        trade = _trade_from_signal(
            symbol,
            frames[symbol],
            signal_date,
            int(sleeve_contract["holding_days"]),
            sleeve=str(sleeve_contract["name"]),
            score=score,
            cost_bps=cost_bps,
            per_trade_weight=per_trade_weight,
        )
        if trade:
            trade["regime_label"] = regime_label
            trades.append(trade)
    return trades


def _return_score(frame: pd.DataFrame, signal_date: pd.Timestamp, lookback: int) -> float | None:
    data = frame[frame.index <= signal_date]
    if len(data) <= lookback:
        return None
    current = float(data["Close"].iloc[-1])
    prior = float(data["Close"].iloc[-lookback - 1])
    if prior <= 0:
        return None
    return current / prior - 1.0


def _regime_summary(trade_log: pd.DataFrame) -> list[dict[str, Any]]:
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
    blockers = ["diagnostic_only_same_dataset_as_discovery", "trial_limited_two_year_history"]
    oos = summary["oos"]
    if oos["trade_count"] < int(gates["min_oos_trades"]):
        blockers.append("oos_trade_count_below_threshold")
    if gates.get("require_positive_oos_net") and oos["weighted_net_sum"] <= 0:
        blockers.append("oos_weighted_net_nonpositive")
    if gates.get("require_positive_oos_median") and oos["median_net_return"] <= 0:
        blockers.append("oos_median_net_nonpositive")
    if float(oos["win_rate"]) < float(gates.get("require_oos_win_rate_at_least", 0.0)):
        blockers.append("oos_win_rate_below_threshold")
    if gates.get("require_positive_ex_top3_oos_net") and robustness["oos_ex_top3_weighted_net_sum"] <= 0:
        blockers.append("oos_ex_top3_weighted_net_nonpositive")
    if gates.get("require_oos_beats_cash") and oos["weighted_net_sum"] <= 0:
        blockers.append("oos_does_not_beat_cash")
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
    methodological = {"diagnostic_only_same_dataset_as_discovery", "trial_limited_two_year_history"}
    return not [blocker for blocker in blockers if blocker not in methodological]


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_ONE_RISK_OFF_MEAN_REVERSION_DIAGNOSTIC_ONLY":
        raise RuntimeError("Candidate 011 gate is not approved.")
    if gate.get("allowed_backtest_count") != 1:
        raise RuntimeError("Gate must authorize exactly one backtest.")
    contract = gate.get("strategy_contract", {})
    if set(contract.get("allowed_regimes", [])) != {"RISK_OFF"}:
        raise RuntimeError("Candidate 011 can only run in RISK_OFF.")
    sleeve = contract.get("sleeve", {})
    if sleeve.get("name") != "risk_off_mean_reversion_5d" or sleeve.get("rank_direction") != "lowest_return":
        raise RuntimeError("Candidate 011 can only run the fixed mean-reversion sleeve.")
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
        "# Candidate 011 Risk-Off Mean Reversion 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: one fixed follow-up diagnostic for RISK_OFF mean reversion. No provider query, no parameter sweep, no promotion.",
        "",
        "## IS/OOS Summary",
        "",
        f"- IS trades: `{is_summary['trade_count']}`",
        f"- IS weighted net: `{is_summary['weighted_net_sum']}`",
        f"- OOS trades: `{oos['trade_count']}`",
        f"- OOS weighted net: `{oos['weighted_net_sum']}`",
        f"- OOS median net: `{oos['median_net_return']}`",
        f"- OOS win rate: `{oos['win_rate']}`",
        f"- OOS max drawdown: `{oos['max_drawdown']}`",
        f"- OOS ex-top3 weighted net: `{result['robustness']['oos_ex_top3_weighted_net_sum']}`",
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
    run_candidate_011_risk_off_mean_reversion()
