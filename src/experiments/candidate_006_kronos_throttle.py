from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "CANDIDATE-006-KRONOS-THROTTLE-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_006_kronos_throttle_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
OVERLAY_TRADE_LOG = Path(
    "experiments/provider_aware_research/execution_outputs/"
    "CANDIDATE-006-KRONOS-OVERLAY-BACKTEST-001/overlay_trade_log.csv"
)


def apply_fixed_half_size_throttle(overlay_log: pd.DataFrame) -> pd.DataFrame:
    log = _normalize_log(overlay_log)
    positive_forecast = log["kronos_forecast_return_median"] > 0.0
    log["throttle_weight_multiplier"] = np.where(positive_forecast, 1.0, 0.5)
    log["throttle_weighted_net_return"] = log["weighted_net_return"] * log["throttle_weight_multiplier"]
    log["binary_overlay_weighted_net_return"] = log["overlay_weighted_net_return"]
    return log


def summarize_throttle(throttled_log: pd.DataFrame) -> dict[str, Any]:
    log = throttled_log.copy()
    reduced = log[log["throttle_weight_multiplier"] < 1.0]
    full = log[log["throttle_weight_multiplier"] == 1.0]
    baseline_equity = _equity_curve(log, "weighted_net_return")
    binary_equity = _equity_curve(log, "binary_overlay_weighted_net_return")
    throttle_equity = _equity_curve(log, "throttle_weighted_net_return")
    baseline_sum = float(log["weighted_net_return"].sum())
    binary_sum = float(log["binary_overlay_weighted_net_return"].sum())
    throttle_sum = float(log["throttle_weighted_net_return"].sum())
    return {
        "baseline_trade_count": int(len(log)),
        "full_weight_trade_count": int(len(full)),
        "reduced_weight_trade_count": int(len(reduced)),
        "baseline_weighted_net_sum": baseline_sum,
        "binary_overlay_weighted_net_sum": binary_sum,
        "throttle_weighted_net_sum": throttle_sum,
        "throttle_minus_baseline_weighted_net": float(throttle_sum - baseline_sum),
        "throttle_minus_binary_overlay_weighted_net": float(throttle_sum - binary_sum),
        "baseline_win_rate": _win_rate(log),
        "full_weight_win_rate": _win_rate(full),
        "reduced_weight_win_rate": _win_rate(reduced),
        "baseline_max_drawdown": _max_drawdown(baseline_equity),
        "binary_overlay_max_drawdown": _max_drawdown(binary_equity),
        "throttle_max_drawdown": _max_drawdown(throttle_equity),
        "drawdown_improvement_vs_baseline": float(_max_drawdown(throttle_equity) - _max_drawdown(baseline_equity)),
        "drawdown_change_vs_binary_overlay": float(_max_drawdown(throttle_equity) - _max_drawdown(binary_equity)),
    }


def random_same_reduced_count_baseline(
    throttled_log: pd.DataFrame,
    *,
    reduced_count: int,
    observed_weighted_net_sum: float,
    iterations: int = 1000,
    seed: int = 607,
) -> dict[str, Any]:
    log = throttled_log.copy().reset_index(drop=True)
    if reduced_count < 0 or reduced_count > len(log):
        raise ValueError("reduced_count must be between zero and the trade count.")
    rng = np.random.default_rng(seed)
    indexes = np.arange(len(log))
    rows: list[dict[str, Any]] = []
    for iteration in range(iterations):
        reduced_mask = np.zeros(len(log), dtype=bool)
        if reduced_count:
            reduced_indexes = rng.choice(indexes, size=reduced_count, replace=False)
            reduced_mask[reduced_indexes] = True
        random_returns = log["weighted_net_return"].to_numpy(dtype=float).copy()
        random_returns[reduced_mask] *= 0.5
        random_equity = _equity_curve_from_values(log["exit_date"], random_returns)
        rows.append(
            {
                "iteration": iteration,
                "reduced_trade_count": int(reduced_count),
                "weighted_net_sum": float(random_returns.sum()),
                "win_rate_full_weight_subset": _win_rate(log.loc[~reduced_mask]),
                "max_drawdown": _max_drawdown(random_equity),
            }
        )
    trials = pd.DataFrame(rows)
    weighted = trials["weighted_net_sum"]
    drawdown = trials["max_drawdown"]
    summary = {
        "seed": int(seed),
        "iterations": int(iterations),
        "same_reduced_trade_count": int(reduced_count),
        "observed_weighted_net_sum": float(observed_weighted_net_sum),
        "random_weighted_net_mean": float(weighted.mean()) if len(weighted) else 0.0,
        "random_weighted_net_median": float(weighted.median()) if len(weighted) else 0.0,
        "random_weighted_net_p05": float(weighted.quantile(0.05)) if len(weighted) else 0.0,
        "random_weighted_net_p95": float(weighted.quantile(0.95)) if len(weighted) else 0.0,
        "observed_net_percentile": float((weighted <= observed_weighted_net_sum).mean()) if len(weighted) else 0.0,
        "random_max_drawdown_median": float(drawdown.median()) if len(drawdown) else 0.0,
        "random_max_drawdown_p05": float(drawdown.quantile(0.05)) if len(drawdown) else 0.0,
        "random_max_drawdown_p95": float(drawdown.quantile(0.95)) if len(drawdown) else 0.0,
    }
    return {"summary": summary, "trials": rows}


def run_candidate_006_kronos_throttle(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    overlay_trade_log_path: Path = OVERLAY_TRADE_LOG,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    overlay_log = pd.read_csv(overlay_trade_log_path)
    throttled = apply_fixed_half_size_throttle(overlay_log)
    summary = summarize_throttle(throttled)
    baseline_cfg = gate.get("random_baseline", {})
    random_baseline = random_same_reduced_count_baseline(
        throttled,
        reduced_count=int(summary["reduced_weight_trade_count"]),
        observed_weighted_net_sum=float(summary["throttle_weighted_net_sum"]),
        iterations=int(baseline_cfg.get("iterations", 1000)),
        seed=int(baseline_cfg.get("seed", 607)),
    )
    interpretation = _interpret(summary, random_baseline["summary"])
    blockers = _blockers(summary, random_baseline["summary"])
    result = {
        "run_id": output_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_006_KRONOS_THROTTLE_COMPLETE_NO_PROMOTION",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_overlay_trade_log": str(overlay_trade_log_path),
        "throttle_rule": gate["throttle_rule"],
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "new_kronos_inference_performed": False,
        "strategy_selection_search_performed": False,
        "threshold_optimization_performed": False,
        "multiplier_optimization_performed": False,
        "rerank_topk_performed": False,
        "reduced_weight_redistributed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "summary": summary,
        "random_same_reduced_count_baseline": random_baseline["summary"],
        "interpretation": interpretation,
        "blockers": blockers,
        "next_allowed_action": "Review fixed throttle diagnostic; no promotion without separate OOS and benchmark-aware gate.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    throttled.to_csv(output_dir / "kronos_throttle_trade_log.csv", index=False)
    pd.DataFrame(random_baseline["trials"]).to_csv(output_dir / "random_same_reduced_count_baseline.csv", index=False)
    _equity_curve(throttled, "throttle_weighted_net_return").to_csv(output_dir / "kronos_throttle_equity_curve.csv", index=False)
    _write_json(output_dir / "kronos_throttle_result.json", result)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    (output_dir / "kronos_throttle_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _normalize_log(log: pd.DataFrame) -> pd.DataFrame:
    required = {
        "symbol",
        "exit_date",
        "net_return",
        "weighted_net_return",
        "overlay_weighted_net_return",
        "kronos_forecast_return_median",
        "kronos_keep_trade",
    }
    missing = sorted(required - set(log.columns))
    if missing:
        raise ValueError(f"Missing required overlay trade log columns: {missing}")
    data = log.copy()
    for column in ("net_return", "weighted_net_return", "overlay_weighted_net_return", "kronos_forecast_return_median"):
        data[column] = pd.to_numeric(data[column], errors="raise")
    data["exit_date"] = pd.to_datetime(data["exit_date"], errors="raise")
    if data["kronos_keep_trade"].dtype != bool:
        data["kronos_keep_trade"] = data["kronos_keep_trade"].astype(str).str.lower().isin({"true", "1", "yes"})
    return data


def _equity_curve(log: pd.DataFrame, return_column: str) -> pd.DataFrame:
    return _equity_curve_from_values(log["exit_date"], log[return_column].to_numpy(dtype=float), return_column=return_column)


def _equity_curve_from_values(exit_dates: pd.Series, returns: np.ndarray, *, return_column: str = "weighted_net_return") -> pd.DataFrame:
    data = pd.DataFrame({"exit_date": pd.to_datetime(exit_dates), return_column: returns})
    grouped = data.groupby("exit_date", as_index=False)[return_column].sum().sort_values("exit_date")
    grouped["cumulative_net_return"] = grouped[return_column].cumsum()
    grouped["running_peak"] = grouped["cumulative_net_return"].cummax()
    grouped["drawdown"] = grouped["cumulative_net_return"] - grouped["running_peak"]
    return grouped.drop(columns=["running_peak"])


def _max_drawdown(equity: pd.DataFrame) -> float:
    if equity.empty:
        return 0.0
    return float(equity["drawdown"].min())


def _interpret(summary: dict[str, Any], random_summary: dict[str, Any]) -> dict[str, str]:
    if summary["throttle_weighted_net_sum"] > summary["binary_overlay_weighted_net_sum"]:
        recovery = "The half-size throttle recovered return versus the binary keep/reject overlay."
    else:
        recovery = "The half-size throttle did not recover return versus the binary overlay."
    if summary["throttle_max_drawdown"] > summary["baseline_max_drawdown"]:
        drawdown = "The throttle reduced local drawdown versus the unthrottled baseline."
    else:
        drawdown = "The throttle did not reduce local drawdown versus the unthrottled baseline."
    if random_summary["observed_net_percentile"] >= 0.95:
        random = "The fixed Kronos throttle beat at least 95% of same-reduced-count random throttles."
    else:
        random = "The fixed Kronos throttle did not decisively beat same-reduced-count random throttles."
    return {"return_recovery": recovery, "drawdown": drawdown, "random_baseline": random}


def _blockers(summary: dict[str, Any], random_summary: dict[str, Any]) -> list[str]:
    blockers = ["diagnostic_only_no_promotion", "single_archived_panel_only"]
    if summary["baseline_trade_count"] < 30:
        blockers.append("trade_count_below_30")
    if random_summary["observed_net_percentile"] < 0.95:
        blockers.append("random_same_reduced_count_baseline_not_decisively_beaten")
    if summary["throttle_weighted_net_sum"] <= summary["binary_overlay_weighted_net_sum"]:
        blockers.append("throttle_does_not_improve_binary_overlay_net")
    if summary["throttle_max_drawdown"] <= summary["baseline_max_drawdown"]:
        blockers.append("throttle_does_not_improve_baseline_drawdown")
    return blockers


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_KRONOS_FIXED_HALF_SIZE_THROTTLE_DIAGNOSTIC_ONLY":
        raise RuntimeError("Kronos throttle gate is not approved.")
    rule = gate.get("throttle_rule", {})
    expected = {
        "feature": "kronos_forecast_return_median",
        "operator": ">",
        "threshold": 0.0,
        "positive_forecast_weight_multiplier": 1.0,
        "non_positive_forecast_weight_multiplier": 0.5,
    }
    for key, value in expected.items():
        if rule.get(key) != value:
            raise RuntimeError(f"Frozen throttle rule changed at {key}.")
    forbidden_rule_flags = (
        "weight_redistribution_allowed",
        "threshold_sweep_allowed",
        "multiplier_sweep_allowed",
        "rerank_allowed",
    )
    for key in forbidden_rule_flags:
        if rule.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")
    for key in ("promotion_allowed", "paper_trading_allowed", "live_trading_allowed"):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")
    forbidden = set(gate.get("forbidden_actions", []))
    required_forbidden = {"run new Kronos inference", "query providers", "download market data"}
    if not required_forbidden.issubset(forbidden):
        raise RuntimeError("Throttle gate does not forbid every required external action.")


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "new_kronos_inference_performed": False,
        "strategy_selection_search_performed": False,
        "threshold_optimization_performed": False,
        "multiplier_optimization_performed": False,
        "promotion_allowed": False,
        "blockers": result["blockers"],
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    random = result["random_same_reduced_count_baseline"]
    lines = [
        "# Candidate 006 Kronos Throttle 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: fixed half-size risk throttle diagnostic only. No new inference, no sweep, no promotion.",
        "",
        "## Baseline Versus Binary Versus Throttle",
        "",
        f"- Baseline trades: `{summary['baseline_trade_count']}`",
        f"- Full-weight trades: `{summary['full_weight_trade_count']}`",
        f"- Half-weight trades: `{summary['reduced_weight_trade_count']}`",
        f"- Baseline weighted net: `{summary['baseline_weighted_net_sum']}`",
        f"- Binary overlay weighted net: `{summary['binary_overlay_weighted_net_sum']}`",
        f"- Throttle weighted net: `{summary['throttle_weighted_net_sum']}`",
        f"- Throttle minus baseline: `{summary['throttle_minus_baseline_weighted_net']}`",
        f"- Throttle minus binary overlay: `{summary['throttle_minus_binary_overlay_weighted_net']}`",
        f"- Baseline max drawdown: `{summary['baseline_max_drawdown']}`",
        f"- Binary overlay max drawdown: `{summary['binary_overlay_max_drawdown']}`",
        f"- Throttle max drawdown: `{summary['throttle_max_drawdown']}`",
        "",
        "## Same-Reduced-Count Random Baseline",
        "",
        f"- Iterations: `{random['iterations']}`",
        f"- Random weighted net median: `{random['random_weighted_net_median']}`",
        f"- Random weighted net p95: `{random['random_weighted_net_p95']}`",
        f"- Observed weighted net percentile: `{random['observed_net_percentile']}`",
        "",
        "## Interpretation",
        "",
    ]
    for text in result["interpretation"].values():
        lines.append(f"- {text}")
    lines.extend(["", "## Blockers", ""])
    for blocker in result["blockers"]:
        lines.append(f"- `{blocker}`")
    return "\n".join(lines) + "\n"


def _win_rate(data: pd.DataFrame) -> float:
    if data.empty:
        return 0.0
    return float((data["net_return"] > 0).mean())


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_006_kronos_throttle()
