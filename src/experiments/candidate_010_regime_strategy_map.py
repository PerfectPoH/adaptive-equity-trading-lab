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
    _summary_by_split,
    _tradable_asof,
    _trade_from_signal,
    build_frames_from_candidate_007_dataset,
)


RUN_ID = "CANDIDATE-010-REGIME-STRATEGY-MAP-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_010_regime_strategy_map_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
TRADE_COLUMNS = [
    "symbol",
    "sleeve",
    "family",
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
    "selection_policy",
    "split",
]


def generate_candidate_010_trades(
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
        tradable_symbols = [
            symbol
            for symbol in symbols
            if symbol in frames and _tradable_asof(symbol, frames[symbol], signal_date, contract["tradability"])
        ]
        regime_label = regime_by_date.get(signal_date.date().isoformat(), "UNMAPPED")
        for family, family_contract in contract["families"].items():
            family_weight = float(contract.get("family_weights", {}).get(family, 1.0))
            trades.extend(
                _trades_for_family(
                    family,
                    tradable_symbols,
                    frames,
                    signal_date,
                    regime_label=regime_label,
                    family_contract=family_contract,
                    cost_bps=int(contract["cost_bps_round_trip"]),
                    family_weight=family_weight,
                )
            )
    return trades


def run_candidate_010_regime_strategy_map(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    dataset_dir = Path(gate["linked_dataset"])
    frames, symbols, benchmarks, master = build_frames_from_candidate_007_dataset(dataset_dir)
    regime_map = build_market_regime_map(frames["SPY"], frames["IWM"])
    trades = generate_candidate_010_trades(symbols, frames, regime_map, gate["strategy_contract"])
    trade_log = pd.DataFrame(trades)
    if trade_log.empty:
        trade_log = pd.DataFrame(columns=TRADE_COLUMNS)
    oos_start = pd.Timestamp(gate["oos_split"]["out_of_sample_start"])
    if not trade_log.empty:
        trade_log["split"] = pd.to_datetime(trade_log["entry_date"]).apply(lambda date: "oos" if date >= oos_start else "is")

    equity = _equity_curve(trade_log)
    summary_by_split = _summary_by_split(trade_log)
    family_regime_summary = _family_regime_summary(trade_log, gate["robustness_gates"])
    top_descriptive_cells = _top_descriptive_cells(family_regime_summary)
    benchmark = _benchmark_summary(frames, gate["oos_split"])
    blockers = [
        "diagnostic_only_regime_atlas",
        "same_dataset_as_prior_candidates",
        "trial_limited_two_year_history",
        "descriptive_ranking_not_promotable",
    ]
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_010_REGIME_STRATEGY_MAP_ARCHIVE_NO_PROMOTION",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_dataset": str(dataset_dir),
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "portfolio_backtest_performed": False,
        "regime_strategy_map_performed": True,
        "kronos_inference_performed": False,
        "portfolio_search_performed": False,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "ranking_scope": gate["ranking_policy"]["scope"],
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
        "family_regime_summary": family_regime_summary,
        "top_descriptive_cells": top_descriptive_cells,
        "benchmark": benchmark,
        "final_decision": {
            "decision": "CANDIDATE_010_REGIME_STRATEGY_MAP_ARCHIVE_NO_PROMOTION",
            "blockers": blockers,
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
    _write_csv(output_dir / "family_regime_summary.csv", pd.DataFrame(family_regime_summary))
    _write_json(output_dir / "candidate_010_regime_strategy_map_result.json", result)
    _write_json(output_dir / "final_decision.json", result["final_decision"])
    (output_dir / "candidate_010_regime_strategy_map_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _trades_for_family(
    family: str,
    symbols: list[str],
    frames: dict[str, pd.DataFrame],
    signal_date: pd.Timestamp,
    *,
    regime_label: str,
    family_contract: dict[str, Any],
    cost_bps: int,
    family_weight: float,
) -> list[dict[str, Any]]:
    ranked: list[tuple[str, float]] = []
    for symbol in symbols:
        score = _family_score(family, frames[symbol], signal_date, family_contract)
        if score is not None:
            ranked.append((symbol, score))
    reverse = _rank_reverse(family_contract)
    ranked.sort(key=lambda item: (item[1], item[0]), reverse=reverse)
    selected = ranked[: int(family_contract["top_k"])]
    if not selected:
        return []
    per_trade_weight = family_weight / len(selected)
    trades: list[dict[str, Any]] = []
    for symbol, score in selected:
        trade = _trade_from_signal(
            symbol,
            frames[symbol],
            signal_date,
            int(family_contract["holding_days"]),
            sleeve=family,
            score=score,
            cost_bps=cost_bps,
            per_trade_weight=per_trade_weight,
        )
        if trade:
            trade["family"] = family
            trade["regime_label"] = regime_label
            trade["selection_policy"] = "predeclared_family_map"
            trades.append(trade)
    return trades


def _family_score(family: str, frame: pd.DataFrame, signal_date: pd.Timestamp, contract: dict[str, Any]) -> float | None:
    if family in {"momentum_60d", "mean_reversion_5d"}:
        return _return_score(frame, signal_date, int(contract["lookback_days"]))
    if family == "volatility_compression_20d":
        return _volatility_score(frame, signal_date, int(contract["volatility_window_days"]))
    if family == "dollar_volume_shock_20d":
        return _dollar_volume_ratio_score(frame, signal_date, int(contract["dollar_volume_window_days"]))
    raise RuntimeError(f"Unsupported Candidate 010 family: {family}")


def _return_score(frame: pd.DataFrame, signal_date: pd.Timestamp, lookback: int) -> float | None:
    data = frame[frame.index <= signal_date]
    if len(data) <= lookback:
        return None
    current = float(data["Close"].iloc[-1])
    prior = float(data["Close"].iloc[-lookback - 1])
    if prior <= 0:
        return None
    return current / prior - 1.0


def _volatility_score(frame: pd.DataFrame, signal_date: pd.Timestamp, window: int) -> float | None:
    data = frame[frame.index <= signal_date].tail(window + 1)
    if len(data) <= window:
        return None
    returns = data["Close"].pct_change().dropna()
    if returns.empty:
        return None
    return float(returns.std())


def _dollar_volume_ratio_score(frame: pd.DataFrame, signal_date: pd.Timestamp, window: int) -> float | None:
    data = frame[frame.index <= signal_date].copy()
    if len(data) < window * 2:
        return None
    dollar_volume = data["Close"] * data["Volume"]
    recent = float(dollar_volume.tail(window).mean())
    prior = float(dollar_volume.iloc[-window * 2 : -window].mean())
    if prior <= 0:
        return None
    return recent / prior - 1.0


def _rank_reverse(contract: dict[str, Any]) -> bool:
    return str(contract["rank_direction"]) in {"highest_return", "highest_dollar_volume_ratio"}


def _family_regime_summary(trade_log: pd.DataFrame, gates: dict[str, Any]) -> list[dict[str, Any]]:
    if trade_log.empty:
        return []
    rows: list[dict[str, Any]] = []
    for (split, family, regime), data in trade_log.groupby(["split", "family", "regime_label"], dropna=False):
        ranked = data.sort_values("weighted_net_return", ascending=False)
        ex_top3 = ranked.iloc[3:]
        weighted_net = float(data["weighted_net_return"].sum())
        ex_top3_net = float(ex_top3["weighted_net_return"].sum()) if not ex_top3.empty else 0.0
        win_rate = float((data["net_return"] > 0).mean())
        trade_count = int(len(data))
        rows.append(
            {
                "split": str(split),
                "family": str(family),
                "regime_label": str(regime),
                "trade_count": trade_count,
                "weighted_net_sum": weighted_net,
                "median_net_return": float(data["net_return"].median()),
                "win_rate": win_rate,
                "ex_top3_weighted_net_sum": ex_top3_net,
                "passes_cell_gates": _passes_cell_gates(trade_count, weighted_net, ex_top3_net, win_rate, gates),
            }
        )
    return sorted(rows, key=lambda row: (row["split"], row["family"], row["regime_label"]))


def _passes_cell_gates(
    trade_count: int,
    weighted_net: float,
    ex_top3_net: float,
    win_rate: float,
    gates: dict[str, Any],
) -> bool:
    return bool(
        trade_count >= int(gates["min_oos_trades_per_family_regime"])
        and weighted_net > float(gates["min_oos_weighted_net_sum"])
        and ex_top3_net > float(gates["min_oos_ex_top3_weighted_net_sum"])
        and win_rate >= float(gates["min_oos_win_rate"])
    )


def _top_descriptive_cells(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    oos = [row for row in summary if row["split"] == "oos"]
    ranked = sorted(oos, key=lambda row: (row["passes_cell_gates"], row["weighted_net_sum"]), reverse=True)
    return ranked[:10]


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_ONE_REGIME_STRATEGY_MAP_DIAGNOSTIC_ONLY":
        raise RuntimeError("Candidate 010 gate is not approved.")
    if gate.get("allowed_backtest_count") != 1:
        raise RuntimeError("Gate must authorize exactly one diagnostic run.")
    if gate.get("ranking_policy", {}).get("scope") != "descriptive_only":
        raise RuntimeError("Candidate 010 ranking must be descriptive only.")
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
    lines = [
        "# Candidate 010 Regime Strategy Map 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: fixed diagnostic atlas across predeclared strategy families and market regimes.",
        "This is not a parameter search, not a portfolio optimizer, and not promotable from this dataset.",
        "",
        "## Dataset",
        "",
        f"- Research symbols: `{result['symbol_counts']['research_symbols']}`",
        f"- Active symbols: `{result['symbol_counts']['active_symbols']}`",
        f"- Delisted symbols: `{result['symbol_counts']['delisted_symbols']}`",
        "",
        "## Overall Split Summary",
        "",
    ]
    for split, summary in result["summary_by_split"].items():
        lines.append(
            f"- `{split}`: trades `{summary['trade_count']}`, weighted net `{summary['weighted_net_sum']}`, "
            f"win rate `{summary['win_rate']}`, max drawdown `{summary['max_drawdown']}`"
        )
    lines.extend(["", "## Top Descriptive OOS Cells", ""])
    for row in result["top_descriptive_cells"]:
        lines.append(
            f"- `{row['family']}` / `{row['regime_label']}`: trades `{row['trade_count']}`, "
            f"weighted net `{row['weighted_net_sum']}`, ex-top3 `{row['ex_top3_weighted_net_sum']}`, "
            f"passes cell gates `{row['passes_cell_gates']}`"
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
    run_candidate_010_regime_strategy_map()
