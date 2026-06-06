from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "CANDIDATE-006-KRONOS-OVERLAY-ATTRIBUTION-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_006_kronos_overlay_attribution_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
OVERLAY_TRADE_LOG = Path(
    "experiments/provider_aware_research/execution_outputs/"
    "CANDIDATE-006-KRONOS-OVERLAY-BACKTEST-001/overlay_trade_log.csv"
)


def compute_kept_rejected_attribution(overlay_log: pd.DataFrame) -> dict[str, Any]:
    log = _normalize_log(overlay_log)
    kept = log[log["kronos_keep_trade"]]
    rejected = log[~log["kronos_keep_trade"]]
    winners = log[log["net_return"] > 0]
    losers = log[log["net_return"] <= 0]
    kept_winners = kept[kept["net_return"] > 0]
    kept_losers = kept[kept["net_return"] <= 0]
    rejected_winners = rejected[rejected["net_return"] > 0]
    rejected_losers = rejected[rejected["net_return"] <= 0]
    baseline_sum = float(log["weighted_net_return"].sum())
    overlay_sum = float(log["overlay_weighted_net_return"].sum())
    return {
        "baseline_trade_count": int(len(log)),
        "kept_trade_count": int(len(kept)),
        "rejected_trade_count": int(len(rejected)),
        "kept_win_rate": _win_rate(kept),
        "rejected_win_rate": _win_rate(rejected),
        "baseline_win_rate": _win_rate(log),
        "kept_weighted_net_sum": float(kept["weighted_net_return"].sum()),
        "rejected_weighted_net_sum": float(rejected["weighted_net_return"].sum()),
        "baseline_weighted_net_sum": baseline_sum,
        "overlay_weighted_net_sum": overlay_sum,
        "overlay_minus_baseline_weighted_net_return": float(overlay_sum - baseline_sum),
        "kept_winner_count": int(len(kept_winners)),
        "kept_loser_count": int(len(kept_losers)),
        "rejected_winner_count": int(len(rejected_winners)),
        "rejected_loser_count": int(len(rejected_losers)),
        "total_winner_count": int(len(winners)),
        "total_loser_count": int(len(losers)),
        "winner_capture_rate": _safe_ratio(len(kept_winners), len(winners)),
        "loser_rejection_rate": _safe_ratio(len(rejected_losers), len(losers)),
        "kept_mean_net_return": float(kept["net_return"].mean()) if len(kept) else 0.0,
        "rejected_mean_net_return": float(rejected["net_return"].mean()) if len(rejected) else 0.0,
        "kept_median_net_return": float(kept["net_return"].median()) if len(kept) else 0.0,
        "rejected_median_net_return": float(rejected["net_return"].median()) if len(rejected) else 0.0,
    }


def random_same_count_baseline(
    overlay_log: pd.DataFrame,
    *,
    kept_count: int,
    observed_weighted_net_sum: float,
    iterations: int = 1000,
    seed: int = 606,
) -> dict[str, Any]:
    log = _normalize_log(overlay_log).reset_index(drop=True)
    if kept_count < 0 or kept_count > len(log):
        raise ValueError("kept_count must be between zero and the trade count.")
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    indexes = np.arange(len(log))
    for iteration in range(iterations):
        selected = np.zeros(len(log), dtype=bool)
        if kept_count:
            selected_indexes = rng.choice(indexes, size=kept_count, replace=False)
            selected[selected_indexes] = True
        selected_log = log.loc[selected].copy()
        selected_sum = float(selected_log["weighted_net_return"].sum())
        equity = _selected_equity_curve(log, selected)
        rows.append(
            {
                "iteration": iteration,
                "selected_trade_count": int(kept_count),
                "weighted_net_sum": selected_sum,
                "win_rate": _win_rate(selected_log),
                "max_drawdown": float(equity["drawdown"].min()) if not equity.empty else 0.0,
            }
        )
    trials = pd.DataFrame(rows)
    weighted = trials["weighted_net_sum"]
    win_rates = trials["win_rate"]
    summary = {
        "seed": int(seed),
        "iterations": int(iterations),
        "same_kept_trade_count": int(kept_count),
        "observed_weighted_net_sum": float(observed_weighted_net_sum),
        "random_weighted_net_mean": float(weighted.mean()) if len(weighted) else 0.0,
        "random_weighted_net_median": float(weighted.median()) if len(weighted) else 0.0,
        "random_weighted_net_p05": float(weighted.quantile(0.05)) if len(weighted) else 0.0,
        "random_weighted_net_p95": float(weighted.quantile(0.95)) if len(weighted) else 0.0,
        "observed_net_percentile": float((weighted <= observed_weighted_net_sum).mean()) if len(weighted) else 0.0,
        "random_win_rate_mean": float(win_rates.mean()) if len(win_rates) else 0.0,
        "random_win_rate_p95": float(win_rates.quantile(0.95)) if len(win_rates) else 0.0,
    }
    return {"summary": summary, "trials": rows}


def run_candidate_006_kronos_overlay_attribution(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    overlay_trade_log_path: Path = OVERLAY_TRADE_LOG,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    overlay_log = pd.read_csv(overlay_trade_log_path)
    attribution = compute_kept_rejected_attribution(overlay_log)
    baseline_cfg = gate.get("random_baseline", {})
    random_baseline = random_same_count_baseline(
        overlay_log,
        kept_count=int(attribution["kept_trade_count"]),
        observed_weighted_net_sum=float(attribution["overlay_weighted_net_sum"]),
        iterations=int(baseline_cfg.get("iterations", 1000)),
        seed=int(baseline_cfg.get("seed", 606)),
    )
    interpretation = _interpret(attribution, random_baseline["summary"])
    blockers = _blockers(attribution, random_baseline["summary"])
    result = {
        "run_id": output_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_006_KRONOS_OVERLAY_ATTRIBUTION_COMPLETE_NO_PROMOTION",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_overlay_trade_log": str(overlay_trade_log_path),
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "new_kronos_inference_performed": False,
        "strategy_backtest_performed": False,
        "threshold_optimization_performed": False,
        "rerank_topk_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "attribution": attribution,
        "random_same_count_baseline": random_baseline["summary"],
        "interpretation": interpretation,
        "blockers": blockers,
        "next_allowed_action": "If useful, preregister a separate OOS-style Kronos sizing diagnostic; do not promote from this attribution.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(random_baseline["trials"]).to_csv(output_dir / "random_same_count_baseline.csv", index=False)
    _write_json(output_dir / "kronos_overlay_attribution_result.json", result)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    (output_dir / "kronos_overlay_attribution_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _normalize_log(log: pd.DataFrame) -> pd.DataFrame:
    required = {
        "symbol",
        "exit_date",
        "net_return",
        "weighted_net_return",
        "overlay_weighted_net_return",
        "kronos_keep_trade",
    }
    missing = sorted(required - set(log.columns))
    if missing:
        raise ValueError(f"Missing required overlay trade log columns: {missing}")
    data = log.copy()
    if data["kronos_keep_trade"].dtype != bool:
        data["kronos_keep_trade"] = data["kronos_keep_trade"].astype(str).str.lower().isin({"true", "1", "yes"})
    for column in ("net_return", "weighted_net_return", "overlay_weighted_net_return"):
        data[column] = pd.to_numeric(data[column], errors="raise")
    data["exit_date"] = pd.to_datetime(data["exit_date"], errors="raise")
    return data


def _selected_equity_curve(log: pd.DataFrame, selected: np.ndarray) -> pd.DataFrame:
    data = log.copy()
    data["selected_weighted_net_return"] = np.where(selected, data["weighted_net_return"], 0.0)
    grouped = (
        data.groupby("exit_date", as_index=False)["selected_weighted_net_return"]
        .sum()
        .sort_values("exit_date")
    )
    grouped["cumulative_selected_net_return"] = grouped["selected_weighted_net_return"].cumsum()
    grouped["running_peak"] = grouped["cumulative_selected_net_return"].cummax()
    grouped["drawdown"] = grouped["cumulative_selected_net_return"] - grouped["running_peak"]
    return grouped.drop(columns=["running_peak"])


def _interpret(attribution: dict[str, Any], random_summary: dict[str, Any]) -> dict[str, str]:
    if attribution["kept_win_rate"] > attribution["rejected_win_rate"]:
        quality = "Kronos kept trades had a higher win rate than rejected trades."
    else:
        quality = "Kronos did not keep a higher-win-rate subset than rejected trades."
    if attribution["loser_rejection_rate"] >= 0.70:
        avoidance = "The overlay rejected most losing trades in this archived panel."
    else:
        avoidance = "The overlay did not reject enough losers to call the selection robust."
    if random_summary["observed_net_percentile"] >= 0.95:
        random = "The frozen Kronos subset beat at least 95% of same-count random filters on weighted net."
    else:
        random = "The frozen Kronos subset did not decisively beat same-count random filters."
    return {
        "kept_vs_rejected": quality,
        "loser_avoidance": avoidance,
        "random_baseline": random,
    }


def _blockers(attribution: dict[str, Any], random_summary: dict[str, Any]) -> list[str]:
    blockers = ["diagnostic_only_no_promotion", "single_archived_panel_only"]
    if attribution["kept_trade_count"] < 30:
        blockers.append("kept_trade_count_below_30")
    if random_summary["observed_net_percentile"] < 0.95:
        blockers.append("random_same_count_baseline_not_decisively_beaten")
    if attribution["winner_capture_rate"] < 0.50:
        blockers.append("winner_capture_rate_below_50pct")
    if attribution["loser_rejection_rate"] < 0.70:
        blockers.append("loser_rejection_rate_below_70pct")
    return blockers


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_KRONOS_OVERLAY_ATTRIBUTION_DIAGNOSTIC_ONLY":
        raise RuntimeError("Kronos overlay attribution gate is not approved.")
    for key in ("promotion_allowed", "paper_trading_allowed", "live_trading_allowed"):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")
    forbidden = set(gate.get("forbidden_actions", []))
    required_forbidden = {"run new Kronos inference", "query providers", "download market data"}
    if not required_forbidden.issubset(forbidden):
        raise RuntimeError("Attribution gate does not forbid every required external action.")


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "new_kronos_inference_performed": False,
        "strategy_backtest_performed": False,
        "threshold_optimization_performed": False,
        "promotion_allowed": False,
        "blockers": result["blockers"],
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    attr = result["attribution"]
    random = result["random_same_count_baseline"]
    lines = [
        "# Candidate 006 Kronos Overlay Attribution 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: attribution diagnostic only. No new inference, no provider query, no threshold sweep, no promotion.",
        "",
        "## Kept Versus Rejected",
        "",
        f"- Baseline trades: `{attr['baseline_trade_count']}`",
        f"- Kept trades: `{attr['kept_trade_count']}`",
        f"- Rejected trades: `{attr['rejected_trade_count']}`",
        f"- Kept win rate: `{attr['kept_win_rate']}`",
        f"- Rejected win rate: `{attr['rejected_win_rate']}`",
        f"- Winner capture rate: `{attr['winner_capture_rate']}`",
        f"- Loser rejection rate: `{attr['loser_rejection_rate']}`",
        f"- Baseline weighted net: `{attr['baseline_weighted_net_sum']}`",
        f"- Overlay weighted net: `{attr['overlay_weighted_net_sum']}`",
        f"- Overlay minus baseline: `{attr['overlay_minus_baseline_weighted_net_return']}`",
        "",
        "## Same-Count Random Baseline",
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


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_006_kronos_overlay_attribution()
