from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import pandas as pd


RUN_ID = "CANDIDATE-014-NORGATE-FRESH-DATA-AUDIT-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_014_norgate_fresh_data_audit_gate_20260607")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID


class NorgateAuditAdapter(Protocol):
    def database_symbols(self, database_name: str) -> list[str]:
        ...

    def price_timeseries(self, symbol: str) -> pd.DataFrame:
        ...


class LocalNorgateAuditAdapter:
    def __init__(self) -> None:
        import norgatedata

        self._norgate = norgatedata

    def database_symbols(self, database_name: str) -> list[str]:
        return [str(symbol) for symbol in self._norgate.database_symbols(database_name)]

    def price_timeseries(self, symbol: str) -> pd.DataFrame:
        return self._norgate.price_timeseries(symbol, timeseriesformat="pandas-dataframe")


def audit_norgate_fresh_data_coverage(
    adapter: NorgateAuditAdapter,
    *,
    active_database: str = "US Equities",
    delisted_database: str = "US Equities Delisted",
    active_sample_limit: int = 500,
    delisted_sample_limit: int = 500,
    benchmark_symbols: list[str] | None = None,
    min_history_years: int = 5,
    min_loaded_active_symbols: int = 50,
    min_loaded_delisted_symbols: int = 50,
) -> dict[str, Any]:
    benchmark_symbols = benchmark_symbols or ["SPY", "IWM"]
    active_symbols = _database_symbols(adapter, active_database)
    delisted_symbols = _database_symbols(adapter, delisted_database)
    active_sample = _load_sample(adapter, active_symbols, active_sample_limit)
    delisted_sample = _load_sample(adapter, delisted_symbols, delisted_sample_limit)
    benchmark_sample = _load_sample(adapter, benchmark_symbols, len(benchmark_symbols))
    all_summaries = [*active_sample["summaries"], *delisted_sample["summaries"], *benchmark_sample["summaries"]]
    coverage = _coverage_summary(
        active_symbol_count=len(active_symbols),
        delisted_symbol_count=len(delisted_symbols),
        active_sample=active_sample,
        delisted_sample=delisted_sample,
        benchmark_sample=benchmark_sample,
        all_summaries=all_summaries,
    )
    blockers = _blockers(
        coverage,
        min_history_years=min_history_years,
        min_loaded_active_symbols=min_loaded_active_symbols,
        min_loaded_delisted_symbols=min_loaded_delisted_symbols,
        benchmark_symbols=benchmark_symbols,
    )
    decision = (
        "CANDIDATE_014_NORGATE_FRESH_DATA_AUDIT_READY_FOR_FRESH_DATA_GATE"
        if not blockers
        else "CANDIDATE_014_NORGATE_FRESH_DATA_AUDIT_BLOCKED"
    )
    return {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "provider": "Norgate Data",
        "local_provider_only": True,
        "provider_query_performed": True,
        "internet_market_data_download_performed": False,
        "market_data_download_performed": False,
        "strategy_backtest_performed": False,
        "backtest_allowed": False,
        "kronos_inference_performed": False,
        "portfolio_selection_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "blockers": blockers,
        "coverage": coverage,
        "limits": {
            "active_sample_limit": active_sample_limit,
            "delisted_sample_limit": delisted_sample_limit,
            "min_history_years": min_history_years,
            "min_loaded_active_symbols": min_loaded_active_symbols,
            "min_loaded_delisted_symbols": min_loaded_delisted_symbols,
        },
        "fresh_validation_contract": {
            "linked_candidate_012_spec": str(
                Path("experiments/provider_aware_research/execution_outputs")
                / "CANDIDATE-012-FROZEN-RECIPE-FRESH-VALIDATION-SPEC-001"
                / "fresh_validation_spec.json"
            ),
            "candidate_012_backtest_allowed_from_this_audit": False,
            "next_allowed_action": "commit_fresh_data_build_gate" if not blockers else "resolve_norgate_coverage_or_choose_provider",
        },
        "final_decision": {
            "decision": decision,
            "blockers": blockers,
            "promotion_allowed": False,
            "backtest_allowed": False,
            "next_allowed_action": "commit_fresh_data_build_gate" if not blockers else "resolve_norgate_coverage_or_choose_provider",
        },
    }


def run_candidate_014_norgate_fresh_data_audit(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    adapter: NorgateAuditAdapter | None = None,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    try:
        provider = adapter or LocalNorgateAuditAdapter()
    except Exception as exc:
        result = _blocked_provider_result(f"{type(exc).__name__}: {exc}")
        _persist(output_dir, result)
        return result
    limits = gate.get("limits", {})
    databases = gate.get("target_database_names", {})
    result = audit_norgate_fresh_data_coverage(
        provider,
        active_database=str(databases.get("active", "US Equities")),
        delisted_database=str(databases.get("delisted", "US Equities Delisted")),
        active_sample_limit=int(limits.get("active_sample_limit", 500)),
        delisted_sample_limit=int(limits.get("delisted_sample_limit", 500)),
        benchmark_symbols=[str(symbol) for symbol in gate.get("benchmark_symbols", ["SPY", "IWM"])],
        min_history_years=int(limits.get("min_history_years", 5)),
        min_loaded_active_symbols=int(limits.get("min_loaded_active_symbols", 50)),
        min_loaded_delisted_symbols=int(limits.get("min_loaded_delisted_symbols", 50)),
    )
    _persist(output_dir, result)
    return result


def _database_symbols(adapter: NorgateAuditAdapter, database_name: str) -> list[str]:
    try:
        return [str(symbol) for symbol in adapter.database_symbols(database_name)]
    except Exception:
        return []


def _load_sample(adapter: NorgateAuditAdapter, symbols: list[str], limit: int) -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    for symbol in symbols[: max(0, limit)]:
        try:
            summary = _price_summary(symbol, adapter.price_timeseries(symbol))
        except Exception as exc:
            errors[symbol] = f"{type(exc).__name__}: {exc}"
            continue
        if summary["row_count"] > 0:
            summaries.append(summary)
    return {
        "requested": min(len(symbols), max(0, limit)),
        "loaded": len(summaries),
        "errors": errors,
        "summaries": summaries,
    }


def _price_summary(symbol: str, frame: pd.DataFrame | None) -> dict[str, Any]:
    if frame is None or frame.empty:
        return {"symbol": symbol, "row_count": 0, "first_date": None, "last_date": None, "history_years": 0.0}
    index = pd.to_datetime(frame.index, errors="coerce")
    index = index[~pd.isna(index)]
    if len(index) == 0:
        return {"symbol": symbol, "row_count": 0, "first_date": None, "last_date": None, "history_years": 0.0}
    first = index.min()
    last = index.max()
    history_years = float((last - first).days / 365.25)
    return {
        "symbol": symbol,
        "row_count": int(len(index)),
        "first_date": first.date().isoformat(),
        "last_date": last.date().isoformat(),
        "history_years": round(history_years, 4),
    }


def _coverage_summary(
    *,
    active_symbol_count: int,
    delisted_symbol_count: int,
    active_sample: dict[str, Any],
    delisted_sample: dict[str, Any],
    benchmark_sample: dict[str, Any],
    all_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    history_years = [float(row["history_years"]) for row in all_summaries]
    first_dates = [str(row["first_date"]) for row in all_summaries if row.get("first_date")]
    last_dates = [str(row["last_date"]) for row in all_summaries if row.get("last_date")]
    return {
        "active_symbol_count": active_symbol_count,
        "delisted_symbol_count": delisted_symbol_count,
        "loaded_active_symbols": int(active_sample["loaded"]),
        "loaded_delisted_symbols": int(delisted_sample["loaded"]),
        "loaded_benchmark_symbols": int(benchmark_sample["loaded"]),
        "benchmark_symbols_loaded": [row["symbol"] for row in benchmark_sample["summaries"]],
        "earliest_first_date": min(first_dates) if first_dates else None,
        "latest_last_date": max(last_dates) if last_dates else None,
        "max_history_years": round(max(history_years), 4) if history_years else 0.0,
        "median_history_years": round(float(pd.Series(history_years).median()), 4) if history_years else 0.0,
        "active_sample_errors": active_sample["errors"],
        "delisted_sample_errors": delisted_sample["errors"],
        "benchmark_sample_errors": benchmark_sample["errors"],
        "active_sample_summaries": active_sample["summaries"][:20],
        "delisted_sample_summaries": delisted_sample["summaries"][:20],
        "benchmark_sample_summaries": benchmark_sample["summaries"],
    }


def _blockers(
    coverage: dict[str, Any],
    *,
    min_history_years: int,
    min_loaded_active_symbols: int,
    min_loaded_delisted_symbols: int,
    benchmark_symbols: list[str],
) -> list[str]:
    blockers: list[str] = []
    if coverage["active_symbol_count"] == 0:
        blockers.append("active_database_unavailable")
    if coverage["delisted_symbol_count"] == 0:
        blockers.append("delisted_database_unavailable")
    if coverage["loaded_active_symbols"] < min_loaded_active_symbols:
        blockers.append("active_sample_below_required_count")
    if coverage["loaded_delisted_symbols"] < min_loaded_delisted_symbols:
        blockers.append("delisted_sample_below_required_count")
    if coverage["loaded_benchmark_symbols"] < len(benchmark_symbols):
        blockers.append("benchmark_symbols_incomplete")
    if float(coverage["max_history_years"]) < float(min_history_years):
        blockers.append(f"history_span_below_{min_history_years}_years")
    return blockers


def _validate_gate(gate: dict[str, Any]) -> None:
    required = {
        "provider_query_allowed": True,
        "local_provider_only": True,
        "internet_market_data_download_allowed": False,
        "strategy_backtest_allowed": False,
        "kronos_inference_allowed": False,
        "portfolio_selection_allowed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
    }
    if gate.get("status") != "APPROVED_NORGATE_LOCAL_FRESH_DATA_AUDIT_ONLY":
        raise RuntimeError("Candidate 014 Norgate fresh data audit gate is not approved.")
    for key, expected in required.items():
        if gate.get(key) is not expected:
            raise RuntimeError(f"Candidate 014 gate invalid: {key} must be {expected!r}.")


def _blocked_provider_result(error: str) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_014_NORGATE_FRESH_DATA_AUDIT_BLOCKED",
        "provider": "Norgate Data",
        "local_provider_only": True,
        "provider_query_performed": False,
        "strategy_backtest_performed": False,
        "promotion_allowed": False,
        "blockers": ["norgate_local_adapter_unavailable"],
        "adapter_error": error,
        "final_decision": {
            "decision": "CANDIDATE_014_NORGATE_FRESH_DATA_AUDIT_BLOCKED",
            "blockers": ["norgate_local_adapter_unavailable"],
            "promotion_allowed": False,
            "backtest_allowed": False,
            "next_allowed_action": "install_or_repair_norgate_local_adapter",
        },
    }


def _persist(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "norgate_fresh_data_audit_result.json", result)
    _write_json(output_dir / "final_decision.json", result["final_decision"])
    (output_dir / "norgate_fresh_data_audit_report.md").write_text(_markdown_report(result), encoding="utf-8")


def _markdown_report(result: dict[str, Any]) -> str:
    coverage = result.get("coverage", {})
    lines = [
        "# Candidate 014 Norgate Fresh Data Audit",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: bounded local Norgate coverage audit only. No dataset build, no market-data download, no backtest, no Kronos inference, no portfolio selection, and no promotion.",
        "",
        "## Coverage",
        "",
        f"- Active symbols available: `{coverage.get('active_symbol_count', 0)}`",
        f"- Delisted symbols available: `{coverage.get('delisted_symbol_count', 0)}`",
        f"- Loaded active sample: `{coverage.get('loaded_active_symbols', 0)}`",
        f"- Loaded delisted sample: `{coverage.get('loaded_delisted_symbols', 0)}`",
        f"- Loaded benchmarks: `{coverage.get('loaded_benchmark_symbols', 0)}`",
        f"- Earliest first date: `{coverage.get('earliest_first_date')}`",
        f"- Latest last date: `{coverage.get('latest_last_date')}`",
        f"- Max history years: `{coverage.get('max_history_years', 0)}`",
        f"- Median history years: `{coverage.get('median_history_years', 0)}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = result.get("blockers", [])
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- None. Next allowed action is a separate fresh-data build gate, not a backtest.")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_014_norgate_fresh_data_audit()
