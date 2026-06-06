from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "CANDIDATE-006-KRONOS-OVERLAY-BACKTEST-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_006_kronos_overlay_backtest_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
TRADE_LOG = Path("experiments/provider_aware_research/execution_outputs/CANDIDATE-005-RECOVERY-BREADTH-BACKTEST-001/trade_log.csv")
FEATURE_ROWS = Path("experiments/provider_aware_research/execution_outputs/CANDIDATE-006-KRONOS-BATCH-FEATURES-001/kronos_batch_features.csv")


def apply_kronos_sign_filter(trade_log: pd.DataFrame, feature_rows: pd.DataFrame) -> pd.DataFrame:
    trades = trade_log.copy()
    features = feature_rows.copy()
    trades["symbol"] = trades["symbol"].astype(str)
    trades["signal_date"] = trades["signal_date"].astype(str)
    features["symbol"] = features["symbol"].astype(str)
    features["as_of_date"] = features["as_of_date"].astype(str)
    joined = trades.merge(
        features,
        left_on=["symbol", "signal_date"],
        right_on=["symbol", "as_of_date"],
        how="left",
        validate="many_to_one",
    )
    if joined["kronos_forecast_return_median"].isna().any():
        missing = joined.loc[joined["kronos_forecast_return_median"].isna(), ["symbol", "signal_date"]].to_dict(orient="records")
        raise ValueError(f"Missing Kronos features for trades: {missing[:5]}")
    joined["kronos_keep_trade"] = joined["kronos_forecast_return_median"].astype(float) > 0.0
    joined["overlay_weighted_net_return"] = joined["weighted_net_return"].where(joined["kronos_keep_trade"], 0.0)
    return joined


def run_candidate_006_kronos_overlay_backtest(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    trade_log_path: Path = TRADE_LOG,
    feature_rows_path: Path = FEATURE_ROWS,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    trade_log = pd.read_csv(trade_log_path)
    feature_rows = pd.read_csv(feature_rows_path)
    overlay_log = apply_kronos_sign_filter(trade_log, feature_rows)
    equity = _equity_curve(overlay_log)
    summary = _summary(trade_log, overlay_log, equity)
    robustness = _robustness(overlay_log)
    blockers = _blockers(summary, robustness)
    result = {
        "run_id": output_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_006_KRONOS_OVERLAY_BACKTEST_ARCHIVE_NO_PROMOTION",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_trade_log": str(trade_log_path),
        "linked_feature_rows": str(feature_rows_path),
        "overlay_rule": gate["overlay_rule"],
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "new_kronos_inference_performed": False,
        "portfolio_backtest_performed": True,
        "threshold_optimization_performed": False,
        "rerank_topk_performed": False,
        "rejected_weight_redistributed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "summary": summary,
        "robustness": robustness,
        "blockers": blockers,
        "next_allowed_action": "Review overlay result; no promotion without OOS and benchmark-aware gate.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    overlay_log.to_csv(output_dir / "overlay_trade_log.csv", index=False)
    equity.to_csv(output_dir / "overlay_equity_curve.csv", index=False)
    _write_json(output_dir / "kronos_overlay_backtest_result.json", result)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    (output_dir / "kronos_overlay_backtest_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _equity_curve(overlay_log: pd.DataFrame) -> pd.DataFrame:
    data = overlay_log.copy()
    data["date"] = pd.to_datetime(data["exit_date"])
    grouped = data.groupby("date", as_index=False)["overlay_weighted_net_return"].sum().sort_values("date")
    grouped["cumulative_overlay_net_return"] = grouped["overlay_weighted_net_return"].cumsum()
    grouped["running_peak"] = grouped["cumulative_overlay_net_return"].cummax()
    grouped["drawdown"] = grouped["cumulative_overlay_net_return"] - grouped["running_peak"]
    return grouped.drop(columns=["running_peak"])


def _summary(baseline_log: pd.DataFrame, overlay_log: pd.DataFrame, equity: pd.DataFrame) -> dict[str, Any]:
    kept = overlay_log[overlay_log["kronos_keep_trade"]]
    return {
        "baseline_trade_count": int(len(baseline_log)),
        "overlay_trade_count": int(len(kept)),
        "cash_routed_trade_count": int((~overlay_log["kronos_keep_trade"]).sum()),
        "baseline_weighted_net_return_sum": float(baseline_log["weighted_net_return"].sum()),
        "overlay_weighted_net_return_sum": float(overlay_log["overlay_weighted_net_return"].sum()),
        "overlay_minus_baseline_weighted_net_return": float(
            overlay_log["overlay_weighted_net_return"].sum() - baseline_log["weighted_net_return"].sum()
        ),
        "overlay_win_rate": float((kept["net_return"] > 0).mean()) if len(kept) else 0.0,
        "max_drawdown": float(equity["drawdown"].min()) if not equity.empty else 0.0,
    }


def _robustness(overlay_log: pd.DataFrame) -> dict[str, Any]:
    by_symbol = overlay_log.groupby("symbol")["overlay_weighted_net_return"].sum().sort_values(ascending=False)
    total = float(by_symbol.sum()) if len(by_symbol) else 0.0
    best = float(by_symbol.iloc[0]) if len(by_symbol) else 0.0
    return {
        "best_symbol": str(by_symbol.index[0]) if len(by_symbol) else None,
        "best_symbol_overlay_weighted_net_return": best,
        "ex_best_symbol_overlay_weighted_net_return": float(total - best),
        "top_symbol_concentration": float(best / total) if total > 0 else None,
    }


def _blockers(summary: dict[str, Any], robustness: dict[str, Any]) -> list[str]:
    blockers = ["promotion_locked_until_separate_oos_gate", "single_trial_overlay_diagnostic_only"]
    if summary["overlay_trade_count"] < 30:
        blockers.append("overlay_trade_count_below_30")
    if summary["overlay_weighted_net_return_sum"] <= 0:
        blockers.append("overlay_weighted_net_return_nonpositive")
    if robustness["ex_best_symbol_overlay_weighted_net_return"] <= 0:
        blockers.append("overlay_ex_best_symbol_nonpositive")
    if robustness["top_symbol_concentration"] is not None and robustness["top_symbol_concentration"] > 0.30:
        blockers.append("overlay_top_symbol_concentration_above_30pct")
    return blockers


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_ONE_KRONOS_OVERLAY_BACKTEST_SIGN_FILTER_ONLY":
        raise RuntimeError("Kronos overlay backtest gate is not approved.")
    rule = gate.get("overlay_rule", {})
    if rule.get("feature") != "kronos_forecast_return_median" or float(rule.get("threshold")) != 0.0 or rule.get("operator") != ">":
        raise RuntimeError("Kronos overlay rule must remain the frozen sign filter.")
    if rule.get("weight_redistribution_allowed"):
        raise RuntimeError("Rejected trade weight redistribution is forbidden.")
    for key in ("promotion_allowed", "paper_trading_allowed", "live_trading_allowed"):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "new_kronos_inference_performed": False,
        "portfolio_backtest_performed": True,
        "threshold_optimization_performed": False,
        "promotion_allowed": False,
        "blockers": result["blockers"],
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    robustness = result["robustness"]
    lines = [
        "# Candidate 006 Kronos Overlay Backtest 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: one frozen sign-filter overlay backtest. No threshold optimization, no reranking, no promotion.",
        "",
        "## Summary",
        "",
        f"- Baseline trades: `{summary['baseline_trade_count']}`",
        f"- Overlay kept trades: `{summary['overlay_trade_count']}`",
        f"- Cash-routed trades: `{summary['cash_routed_trade_count']}`",
        f"- Baseline weighted net: `{summary['baseline_weighted_net_return_sum']}`",
        f"- Overlay weighted net: `{summary['overlay_weighted_net_return_sum']}`",
        f"- Overlay minus baseline: `{summary['overlay_minus_baseline_weighted_net_return']}`",
        f"- Overlay max drawdown: `{summary['max_drawdown']}`",
        f"- Overlay win rate: `{summary['overlay_win_rate']}`",
        "",
        "## Robustness",
        "",
        f"- Best symbol: `{robustness['best_symbol']}`",
        f"- Ex-best-symbol overlay net: `{robustness['ex_best_symbol_overlay_weighted_net_return']}`",
        f"- Top-symbol concentration: `{robustness['top_symbol_concentration']}`",
        "",
        "## Blockers",
        "",
    ]
    for blocker in result["blockers"]:
        lines.append(f"- `{blocker}`")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_006_kronos_overlay_backtest()
