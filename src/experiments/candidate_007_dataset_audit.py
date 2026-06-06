from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "CANDIDATE-007-DATASET-AUDIT-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_007_dataset_audit_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID


def audit_candidate_007_dataset(dataset_dir: Path, *, thresholds: dict[str, Any]) -> dict[str, Any]:
    prices = pd.read_csv(dataset_dir / "prices.csv")
    master = pd.read_csv(dataset_dir / "security_master.csv")
    manifest = _read_json(dataset_dir / "dataset_manifest.json")
    validation = _read_json(dataset_dir / "data_input_validation_report.json")
    coverage = _coverage(prices, master)
    liquidity = _liquidity(prices, master)
    readiness_blockers = _readiness_blockers(coverage, manifest, validation, thresholds)
    decision = (
        "CANDIDATE_007_DATASET_AUDIT_READY_FOR_BACKTEST_SPEC"
        if not readiness_blockers
        else "CANDIDATE_007_DATASET_AUDIT_NOT_READY"
    )
    return {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "linked_dataset": str(dataset_dir),
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "strategy_backtest_performed": False,
        "kronos_inference_performed": False,
        "portfolio_selection_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "dataset_manifest_decision": manifest.get("decision"),
        "dataset_validation_decision": validation.get("gate_decision"),
        "thresholds": thresholds,
        "coverage": coverage,
        "liquidity": liquidity,
        "readiness_blockers": readiness_blockers,
        "next_allowed_action": (
            "Create a separate preregistered backtest spec using this dataset."
            if not readiness_blockers
            else "Resolve dataset audit blockers before any backtest spec."
        ),
    }


def run_candidate_007_dataset_audit(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    dataset_dir = Path(gate["linked_dataset"])
    result = audit_candidate_007_dataset(dataset_dir, thresholds=gate["readiness_thresholds"])
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "candidate_007_dataset_audit_result.json", result)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    pd.DataFrame(_coverage_rows(result["coverage"])).to_csv(output_dir / "coverage_by_universe.csv", index=False)
    pd.DataFrame(result["liquidity"]["by_universe"]).to_csv(output_dir / "liquidity_by_universe.csv", index=False)
    (output_dir / "candidate_007_dataset_audit_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _coverage(prices: pd.DataFrame, master: pd.DataFrame) -> dict[str, Any]:
    data = prices.copy()
    data["date"] = pd.to_datetime(data["date"])
    rows_by_symbol = data.groupby("symbol").size()
    status_by_symbol = master.set_index("symbol")["universe_status"].astype(str).to_dict()
    is_delisted_by_symbol = master.set_index("symbol")["is_delisted"].astype(bool).to_dict()
    active_symbols = [symbol for symbol, status in status_by_symbol.items() if status == "active"]
    delisted_symbols = [symbol for symbol, flag in is_delisted_by_symbol.items() if flag]
    benchmark_symbols = [symbol for symbol, status in status_by_symbol.items() if status == "benchmark"]
    total_research_symbols = len(active_symbols) + len(delisted_symbols)
    return {
        "total_symbols": int(master["symbol"].nunique()),
        "research_symbols": int(total_research_symbols),
        "active_symbols": int(len(active_symbols)),
        "delisted_symbols": int(len(delisted_symbols)),
        "benchmark_symbols": int(len(benchmark_symbols)),
        "price_rows": int(len(data)),
        "first_date": str(data["date"].min().date()) if not data.empty else None,
        "last_date": str(data["date"].max().date()) if not data.empty else None,
        "median_rows_per_symbol": float(rows_by_symbol.median()) if len(rows_by_symbol) else 0.0,
        "min_rows_per_symbol": int(rows_by_symbol.min()) if len(rows_by_symbol) else 0,
        "max_rows_per_symbol": int(rows_by_symbol.max()) if len(rows_by_symbol) else 0,
        "required_benchmarks_present": sorted(set(benchmark_symbols)),
        "delisted_share_of_research_universe": float(len(delisted_symbols) / total_research_symbols) if total_research_symbols else 0.0,
        "trial_limited": True,
    }


def _liquidity(prices: pd.DataFrame, master: pd.DataFrame) -> dict[str, Any]:
    data = prices.copy()
    data["turnover"] = pd.to_numeric(data["close"], errors="coerce") * pd.to_numeric(data["volume"], errors="coerce")
    per_symbol = data.groupby("symbol").agg(
        rows=("date", "size"),
        min_close=("close", "min"),
        median_turnover=("turnover", "median"),
        median_volume=("volume", "median"),
    )
    joined = per_symbol.join(master.set_index("symbol")[["universe_status", "is_delisted"]], how="left").reset_index()
    by_universe = []
    for status, group in joined.groupby("universe_status"):
        by_universe.append(
            {
                "universe_status": str(status),
                "symbols": int(len(group)),
                "median_rows": float(group["rows"].median()),
                "median_min_close": float(group["min_close"].median()),
                "median_turnover": float(group["median_turnover"].median()),
                "sub_dollar_symbols": int((group["min_close"] < 1.0).sum()),
            }
        )
    return {
        "by_universe": by_universe,
        "tradable_symbol_count_price_ge_1_turnover_ge_1m": int(
            ((joined["min_close"] >= 1.0) & (joined["median_turnover"] >= 1_000_000.0)).sum()
        ),
        "sub_dollar_symbol_count": int((joined["min_close"] < 1.0).sum()),
    }


def _readiness_blockers(
    coverage: dict[str, Any],
    manifest: dict[str, Any],
    validation: dict[str, Any],
    thresholds: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if validation.get("gate_decision") != "DATA_INPUT_VALIDATION_PASS":
        blockers.append("dataset_validation_not_pass")
    if manifest.get("survivorship_free_claim_allowed") is not True:
        blockers.append("dataset_manifest_survivorship_claim_not_allowed")
    if coverage["active_symbols"] < int(thresholds["min_active_symbols"]):
        blockers.append("active_symbol_count_below_threshold")
    if coverage["delisted_symbols"] < int(thresholds["min_delisted_symbols"]):
        blockers.append("delisted_symbol_count_below_threshold")
    if coverage["research_symbols"] < int(thresholds["min_total_symbols"]):
        blockers.append("research_symbol_count_below_threshold")
    if coverage["price_rows"] < int(thresholds["min_price_rows"]):
        blockers.append("price_rows_below_threshold")
    if coverage["median_rows_per_symbol"] < float(thresholds["min_median_rows_per_symbol"]):
        blockers.append("median_rows_per_symbol_below_threshold")
    missing_benchmarks = sorted(set(thresholds.get("required_benchmarks", [])) - set(coverage["required_benchmarks_present"]))
    if missing_benchmarks:
        blockers.append("required_benchmark_missing:" + ",".join(missing_benchmarks))
    return blockers


def _coverage_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"metric": key, "value": value}
        for key, value in coverage.items()
        if key not in {"required_benchmarks_present"}
    ]


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_CANDIDATE_007_DATASET_AUDIT_ONLY":
        raise RuntimeError("Candidate 007 dataset audit gate is not approved.")
    for key in (
        "provider_query_allowed",
        "market_data_download_allowed",
        "strategy_backtest_allowed",
        "kronos_inference_allowed",
        "portfolio_selection_allowed",
        "promotion_allowed",
        "paper_trading_allowed",
        "live_trading_allowed",
    ):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "readiness_blockers": result["readiness_blockers"],
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "strategy_backtest_performed": False,
        "kronos_inference_performed": False,
        "promotion_allowed": False,
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    coverage = result["coverage"]
    lines = [
        "# Candidate 007 Dataset Audit 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: read-only dataset audit. No provider query, no backtest, no Kronos inference, no promotion.",
        "",
        "## Coverage",
        "",
        f"- Active symbols: `{coverage['active_symbols']}`",
        f"- Delisted symbols: `{coverage['delisted_symbols']}`",
        f"- Research symbols: `{coverage['research_symbols']}`",
        f"- Benchmarks: `{', '.join(coverage['required_benchmarks_present'])}`",
        f"- Price rows: `{coverage['price_rows']}`",
        f"- Median rows per symbol: `{coverage['median_rows_per_symbol']}`",
        f"- Date span: `{coverage['first_date']}` to `{coverage['last_date']}`",
        "",
        "## Readiness Blockers",
        "",
    ]
    if result["readiness_blockers"]:
        for blocker in result["readiness_blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- None. Dataset is ready for a separately preregistered backtest spec.")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_007_dataset_audit()
