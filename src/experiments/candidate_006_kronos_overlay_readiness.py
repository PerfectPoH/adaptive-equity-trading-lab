from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "CANDIDATE-006-KRONOS-OVERLAY-READINESS-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_006_kronos_overlay_feature_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
TRADE_LOG = Path("experiments/provider_aware_research/execution_outputs/CANDIDATE-005-RECOVERY-BREADTH-BACKTEST-001/trade_log.csv")
KRONOS_SMOKE_RESULT = Path(
    "experiments/provider_aware_research/execution_outputs/CANDIDATE-006-KRONOS-INFERENCE-SMOKE-RERUN-002/kronos_smoke_result.json"
)


def compute_overlay_coverage(trade_log: pd.DataFrame, feature_rows: list[dict[str, Any]]) -> dict[str, Any]:
    trades = trade_log.copy()
    features = pd.DataFrame(feature_rows)
    if features.empty:
        features = pd.DataFrame(columns=["symbol", "as_of_date"])
    trades["symbol"] = trades["symbol"].astype(str)
    trades["signal_date"] = trades["signal_date"].astype(str)
    features["symbol"] = features["symbol"].astype(str)
    features["as_of_date"] = features["as_of_date"].astype(str)
    trade_pairs = set(zip(trades["symbol"], trades["signal_date"], strict=False))
    feature_pairs = set(zip(features["symbol"], features["as_of_date"], strict=False))
    covered_pairs = trade_pairs & feature_pairs
    trade_symbols = set(trades["symbol"])
    feature_symbols = set(features["symbol"])
    trade_dates = set(trades["signal_date"])
    feature_dates = set(features["as_of_date"])
    covered_symbols = trade_symbols & feature_symbols
    covered_dates = trade_dates & feature_dates
    covered_rows = trades.apply(lambda row: (row["symbol"], row["signal_date"]) in feature_pairs, axis=1)
    return {
        "trade_rows": int(len(trades)),
        "feature_rows": int(len(features)),
        "unique_trade_symbols": int(len(trade_symbols)),
        "unique_feature_symbols": int(len(feature_symbols)),
        "unique_trade_signal_dates": int(len(trade_dates)),
        "unique_feature_dates": int(len(feature_dates)),
        "covered_symbol_date_pairs": int(len(covered_pairs)),
        "covered_symbols": sorted(covered_symbols),
        "covered_signal_dates": sorted(covered_dates),
        "symbols_covered_ratio": float(len(covered_symbols) / len(trade_symbols)) if trade_symbols else 0.0,
        "trade_rows_covered_ratio": float(covered_rows.mean()) if len(trades) else 0.0,
        "rebalance_dates_covered_ratio": float(len(covered_dates) / len(trade_dates)) if trade_dates else 0.0,
    }


def run_candidate_006_kronos_overlay_readiness(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    trade_log_path: Path = TRADE_LOG,
    kronos_smoke_result_path: Path = KRONOS_SMOKE_RESULT,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    trades = pd.read_csv(trade_log_path)
    feature_rows = _feature_rows_from_smoke(kronos_smoke_result_path)
    coverage = compute_overlay_coverage(trades, feature_rows)
    blockers = _coverage_blockers(coverage, gate["coverage_contract"])
    decision = (
        "CANDIDATE_006_KRONOS_OVERLAY_READINESS_COMPLETE_FEATURE_COVERAGE_OK"
        if not blockers
        else "CANDIDATE_006_KRONOS_OVERLAY_READINESS_BLOCKED_INSUFFICIENT_FEATURE_COVERAGE"
    )
    result = {
        "run_id": output_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_candidate_005_trade_log": str(trade_log_path),
        "linked_kronos_smoke_result": str(kronos_smoke_result_path),
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "new_kronos_inference_performed": False,
        "portfolio_backtest_performed": False,
        "parameter_sweep_performed": False,
        "threshold_optimization_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "coverage_contract": gate["coverage_contract"],
        "coverage": coverage,
        "blockers": blockers,
        "next_allowed_action": _next_action(blockers),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "kronos_overlay_readiness_result.json", result)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    (output_dir / "kronos_overlay_readiness_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _feature_rows_from_smoke(path: Path) -> list[dict[str, Any]]:
    smoke = _read_json(path)
    if not smoke.get("feature_summary"):
        return []
    return [
        {
            "symbol": "SPY",
            "as_of_date": "2026-05-08",
            **smoke["feature_summary"],
        }
    ]


def _coverage_blockers(coverage: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if contract.get("single_symbol_smoke_is_never_sufficient") and coverage["unique_feature_symbols"] <= 1:
        blockers.append("single_symbol_kronos_smoke_not_overlay_admissible")
    if coverage["unique_feature_symbols"] < int(contract["minimum_unique_symbols"]):
        blockers.append("kronos_feature_unique_symbol_count_below_contract")
    if coverage["unique_feature_dates"] < int(contract["minimum_unique_signal_dates"]):
        blockers.append("kronos_feature_unique_date_count_below_contract")
    if coverage["symbols_covered_ratio"] < float(contract["minimum_symbols_covered_ratio"]):
        blockers.append("kronos_symbol_coverage_below_contract")
    if coverage["trade_rows_covered_ratio"] < float(contract["minimum_trade_rows_covered_ratio"]):
        blockers.append("kronos_trade_row_coverage_below_contract")
    if coverage["rebalance_dates_covered_ratio"] < float(contract["minimum_rebalance_dates_covered_ratio"]):
        blockers.append("kronos_rebalance_date_coverage_below_contract")
    if blockers:
        blockers.append("kronos_feature_coverage_below_contract")
    return blockers


def _next_action(blockers: list[str]) -> str:
    if blockers:
        return "Create a separate batch Kronos feature-generation gate with frozen symbol/date coverage before any overlay backtest."
    return "Create a separate Kronos overlay backtest gate with frozen reranking rule and no threshold optimization."


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_KRONOS_OVERLAY_READINESS_DIAGNOSTIC_ONLY":
        raise RuntimeError("Kronos overlay readiness gate is not approved.")
    for key in ("promotion_allowed", "paper_trading_allowed", "live_trading_allowed"):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "new_kronos_inference_performed": False,
        "portfolio_backtest_performed": False,
        "promotion_allowed": False,
        "blockers": result["blockers"],
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    coverage = result["coverage"]
    lines = [
        "# Candidate 006 Kronos Overlay Readiness 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: readiness diagnostic only. No new inference, no backtest, no threshold optimization, no promotion.",
        "",
        "## Coverage",
        "",
        f"- Trade rows: `{coverage['trade_rows']}`",
        f"- Feature rows: `{coverage['feature_rows']}`",
        f"- Trade symbols: `{coverage['unique_trade_symbols']}`",
        f"- Feature symbols: `{coverage['unique_feature_symbols']}`",
        f"- Symbol coverage ratio: `{coverage['symbols_covered_ratio']}`",
        f"- Trade-row coverage ratio: `{coverage['trade_rows_covered_ratio']}`",
        f"- Rebalance-date coverage ratio: `{coverage['rebalance_dates_covered_ratio']}`",
        "",
        "## Interpretation",
        "",
        "The archived Kronos smoke proves the model can emit features, but it is not broad enough to touch Candidate 005.",
        "Using one SPY forecast to rerank a 37-trade, 282-symbol recovery breadth basket would be an overfitting trap.",
        "",
        "## Blockers",
        "",
    ]
    if result["blockers"]:
        for blocker in result["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Next Allowed Action", "", f"`{result['next_allowed_action']}`", ""])
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_006_kronos_overlay_readiness()
