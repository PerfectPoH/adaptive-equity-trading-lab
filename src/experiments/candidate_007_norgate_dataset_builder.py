from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import pandas as pd


RUN_ID = "CANDIDATE-007-NORGATE-DATASET-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_007_norgate_dataset_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/data_inputs") / RUN_ID


class NorgateLikeAdapter(Protocol):
    def database_symbols(self, database_name: str) -> list[str]:
        ...

    def price_timeseries(self, symbol: str) -> pd.DataFrame:
        ...


class LocalNorgateAdapter:
    def __init__(self) -> None:
        import norgatedata

        self._norgate = norgatedata

    def database_symbols(self, database_name: str) -> list[str]:
        return [str(symbol) for symbol in self._norgate.database_symbols(database_name)]

    def price_timeseries(self, symbol: str) -> pd.DataFrame:
        return self._norgate.price_timeseries(symbol, timeseriesformat="pandas-dataframe")


def build_candidate_007_dataset(
    adapter: NorgateLikeAdapter,
    *,
    output_dir: Path,
    active_limit: int,
    delisted_limit: int,
    min_rows: int,
    benchmark_symbols: list[str],
    active_database: str = "US Equities",
    delisted_database: str = "US Equities Delisted",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    active_symbols, active_rejections = _select_symbols(adapter, active_database, active_limit, min_rows)
    delisted_symbols, delisted_rejections = _select_symbols(adapter, delisted_database, delisted_limit, min_rows)
    selected_symbols = [*active_symbols, *delisted_symbols, *benchmark_symbols]
    frames: dict[str, pd.DataFrame] = {}
    load_errors: dict[str, str] = {}
    for symbol in dict.fromkeys(selected_symbols):
        try:
            frame = _normalize_price_frame(adapter.price_timeseries(symbol), symbol)
        except Exception as exc:  # pragma: no cover - provider-specific failure path
            load_errors[symbol] = f"{type(exc).__name__}: {exc}"
            continue
        if len(frame) >= min_rows:
            frames[symbol] = frame
        else:
            load_errors[symbol] = "insufficient_rows_after_normalization"
    prices = pd.concat(frames.values(), ignore_index=True) if frames else pd.DataFrame(columns=_price_columns())
    security_master = _security_master(active_symbols, delisted_symbols, benchmark_symbols, frames)
    tradability_report = _tradability_report(frames, active_rejections, delisted_rejections, load_errors, min_rows)
    prices.to_csv(output_dir / "prices.csv", index=False)
    security_master.to_csv(output_dir / "security_master.csv", index=False)
    _write_json(output_dir / "tradability_report.json", tradability_report)
    validation = validate_candidate_007_dataset(output_dir)
    _write_json(output_dir / "data_input_validation_report.json", validation)
    blockers = _blockers(active_symbols, delisted_symbols, frames, validation)
    decision = (
        "CANDIDATE_007_NORGATE_DATASET_COMPLETE_DATASET_READY_NO_PROMOTION"
        if not blockers
        else "CANDIDATE_007_NORGATE_DATASET_BLOCKED"
    )
    run_id = output_dir.name
    manifest = _dataset_manifest(
        output_dir,
        run_id,
        active_symbols,
        delisted_symbols,
        benchmark_symbols,
        active_database=active_database,
        delisted_database=delisted_database,
        min_rows=min_rows,
        blockers=blockers,
        decision=decision,
    )
    _write_json(output_dir / "dataset_manifest.json", manifest)
    result = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "provider": "Norgate Data",
        "local_provider_only": True,
        "provider_query_performed": True,
        "internet_market_data_download_performed": False,
        "strategy_backtest_performed": False,
        "kronos_inference_performed": False,
        "portfolio_selection_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "survivorship_free_claim_allowed": not blockers,
        "trial_limited": True,
        "trial_history_limit_declared": "Norgate trial terms limit history to 2 years.",
        "symbol_counts": {
            "active": len(active_symbols),
            "delisted": len(delisted_symbols),
            "benchmarks": len([symbol for symbol in benchmark_symbols if symbol in frames]),
            "frames_loaded": len(frames),
            "price_rows": int(len(prices)),
        },
        "blockers": blockers,
        "file_hashes": manifest["file_hashes"],
        "validation": validation,
        "tradability_report": tradability_report,
        "final_decision": {
            "decision": decision,
            "blockers": blockers,
            "promotion_allowed": False,
            "strategy_backtest_performed": False,
            "kronos_inference_performed": False,
            "survivorship_free_claim_allowed": not blockers,
        },
    }
    _write_json(output_dir / "candidate_007_norgate_dataset_result.json", result)
    _write_json(output_dir / "final_decision.json", result["final_decision"])
    (output_dir / "candidate_007_norgate_dataset_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def run_candidate_007_norgate_dataset_builder(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    adapter: NorgateLikeAdapter | None = None,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    try:
        provider = adapter or LocalNorgateAdapter()
    except Exception as exc:
        return _write_blocked_provider_result(output_dir, gate_dir, f"{type(exc).__name__}: {exc}")
    limits = gate.get("limits", {})
    databases = gate.get("target_database_names", {})
    return build_candidate_007_dataset(
        provider,
        output_dir=output_dir,
        active_limit=int(limits.get("active_symbol_limit", 250)),
        delisted_limit=int(limits.get("delisted_symbol_limit", 250)),
        min_rows=int(limits.get("min_rows", 90)),
        benchmark_symbols=[str(symbol) for symbol in gate.get("benchmark_symbols", ["SPY", "IWM"])],
        active_database=str(databases.get("active", "US Equities")),
        delisted_database=str(databases.get("delisted", "US Equities Delisted")),
    )


def validate_candidate_007_dataset(dataset_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    prices_path = dataset_dir / "prices.csv"
    master_path = dataset_dir / "security_master.csv"
    _check(checks, "required_file:prices.csv", prices_path.exists(), str(prices_path))
    _check(checks, "required_file:security_master.csv", master_path.exists(), str(master_path))
    if not prices_path.exists() or not master_path.exists():
        return {"status": "fail", "gate_decision": "DATA_INPUT_VALIDATION_BLOCK", "checks": checks}
    prices = pd.read_csv(prices_path)
    master = pd.read_csv(master_path)
    required_prices = set(_price_columns())
    _check(checks, "prices_required_columns", required_prices.issubset(prices.columns), sorted(required_prices - set(prices.columns)))
    _check(checks, "security_master_required_columns", {"symbol", "universe_status", "is_delisted"}.issubset(master.columns), list(master.columns))
    _check(checks, "prices_nonempty", not prices.empty, int(len(prices)))
    _check(checks, "security_master_nonempty", not master.empty, int(len(master)))
    if not prices.empty and required_prices.issubset(prices.columns):
        duplicates = int(prices.duplicated(["symbol", "date"]).sum())
        _check(checks, "symbol_date_duplicates_absent", duplicates == 0, duplicates)
        positive_ohlc = bool((prices[["open", "high", "low", "close"]] > 0).all().all())
        _check(checks, "positive_ohlc", positive_ohlc, "all OHLC > 0")
        tolerance = 1e-4
        row_min = prices[["open", "close", "high"]].min(axis=1)
        row_max = prices[["open", "close", "low"]].max(axis=1)
        lower_ok = prices["low"] <= (row_min + tolerance)
        upper_ok = prices["high"] >= (row_max - tolerance)
        ordered = bool((lower_ok & upper_ok).all())
        violations = int((~(lower_ok & upper_ok)).sum())
        _check(checks, "ohlc_bounds_consistent", ordered, {"absolute_tolerance": tolerance, "violations": violations})
    if not master.empty and "is_delisted" in master.columns:
        delisted_count = int(master["is_delisted"].astype(bool).sum())
        active_count = int((~master["is_delisted"].astype(bool)).sum())
        _check(checks, "active_symbols_present", active_count > 0, active_count)
        _check(checks, "delisted_symbols_present", delisted_count > 0, delisted_count)
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    return {
        "status": status,
        "gate_decision": "DATA_INPUT_VALIDATION_PASS" if status == "pass" else "DATA_INPUT_VALIDATION_BLOCK",
        "checks": checks,
    }


def _select_symbols(adapter: NorgateLikeAdapter, database_name: str, limit: int, min_rows: int) -> tuple[list[str], dict[str, str]]:
    selected: list[str] = []
    rejections: dict[str, str] = {}
    try:
        symbols = adapter.database_symbols(database_name)
    except Exception as exc:
        return [], {database_name: f"database_symbols_error:{type(exc).__name__}:{exc}"}
    for symbol in symbols:
        symbol = str(symbol)
        if _skip_non_common_like_symbol(symbol):
            rejections[symbol] = "non_common_or_derivative_symbol"
            continue
        try:
            frame = adapter.price_timeseries(symbol)
        except Exception as exc:
            rejections[symbol] = f"price_timeseries_error:{type(exc).__name__}:{exc}"
            continue
        if frame is None or len(frame) < min_rows:
            rejections[symbol] = "insufficient_rows"
            continue
        selected.append(symbol)
        if len(selected) >= limit:
            break
    return selected, rejections


def _normalize_price_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=_price_columns())
    data = frame.copy()
    column_map = {column.lower(): column for column in data.columns}
    out = pd.DataFrame(
        {
            "symbol": symbol,
            "date": pd.to_datetime(data.index).date.astype(str),
            "open": pd.to_numeric(data[column_map["open"]], errors="coerce"),
            "high": pd.to_numeric(data[column_map["high"]], errors="coerce"),
            "low": pd.to_numeric(data[column_map["low"]], errors="coerce"),
            "close": pd.to_numeric(data[column_map["close"]], errors="coerce"),
            "volume": pd.to_numeric(data[column_map["volume"]], errors="coerce").fillna(0).astype("int64"),
            "provider_dataset": "Norgate Data",
        }
    )
    return out.dropna(subset=["date", "open", "high", "low", "close"]).sort_values(["symbol", "date"])


def _security_master(
    active_symbols: list[str],
    delisted_symbols: list[str],
    benchmark_symbols: list[str],
    frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    for symbol in active_symbols:
        if symbol in frames:
            rows.append(_security_row(symbol, "active", False, frames[symbol]))
    for symbol in delisted_symbols:
        if symbol in frames:
            rows.append(_security_row(symbol, "delisted", True, frames[symbol]))
    for symbol in benchmark_symbols:
        if symbol in frames and symbol not in {*active_symbols, *delisted_symbols}:
            rows.append(_security_row(symbol, "benchmark", False, frames[symbol]))
    return pd.DataFrame(rows)


def _security_row(symbol: str, universe_status: str, is_delisted: bool, frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "universe_status": universe_status,
        "is_delisted": bool(is_delisted),
        "first_date": str(frame["date"].min()) if not frame.empty else None,
        "last_date": str(frame["date"].max()) if not frame.empty else None,
        "row_count": int(len(frame)),
        "provider": "Norgate Data",
    }


def _tradability_report(
    frames: dict[str, pd.DataFrame],
    active_rejections: dict[str, str],
    delisted_rejections: dict[str, str],
    load_errors: dict[str, str],
    min_rows: int,
) -> dict[str, Any]:
    diagnostics = {}
    for symbol, frame in frames.items():
        turnover = frame["close"] * frame["volume"]
        diagnostics[symbol] = {
            "rows": int(len(frame)),
            "first_date": str(frame["date"].min()),
            "last_date": str(frame["date"].max()),
            "min_close": float(frame["close"].min()),
            "median_turnover": float(turnover.median()),
        }
    return {
        "filter_id": "CANDIDATE-007-NORGATE-DATASET-QUALITY-001",
        "min_rows": int(min_rows),
        "accepted_symbols": sorted(frames),
        "active_rejections": active_rejections,
        "delisted_rejections": delisted_rejections,
        "load_errors": load_errors,
        "diagnostics": diagnostics,
    }


def _dataset_manifest(
    output_dir: Path,
    dataset_id: str,
    active_symbols: list[str],
    delisted_symbols: list[str],
    benchmark_symbols: list[str],
    *,
    active_database: str,
    delisted_database: str,
    min_rows: int,
    blockers: list[str],
    decision: str,
) -> dict[str, Any]:
    files = [
        "prices.csv",
        "security_master.csv",
        "tradability_report.json",
        "data_input_validation_report.json",
    ]
    return {
        "dataset_id": dataset_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": "Norgate Data",
        "provider_scope": "local_norgate_installation",
        "active_database": active_database,
        "delisted_database": delisted_database,
        "benchmark_symbols": benchmark_symbols,
        "min_rows": int(min_rows),
        "trial_limited": True,
        "trial_history_limit_declared": "2_years_expected_from_trial_terms",
        "raw_payload_retention": "derived_csv_only_no_raw_vendor_payload",
        "survivorship_free_claim_allowed": not blockers,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "decision": decision,
        "blockers": blockers,
        "symbol_counts": {
            "active": len(active_symbols),
            "delisted": len(delisted_symbols),
            "benchmarks": len(benchmark_symbols),
            "total_declared": len(active_symbols) + len(delisted_symbols) + len(benchmark_symbols),
        },
        "file_hashes": {name: _sha256(output_dir / name) for name in files if (output_dir / name).exists()},
    }


def _blockers(active_symbols: list[str], delisted_symbols: list[str], frames: dict[str, pd.DataFrame], validation: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not active_symbols:
        blockers.append("active_symbol_sample_missing")
    if not delisted_symbols:
        blockers.append("delisted_symbol_sample_missing")
    if "SPY" not in frames or "IWM" not in frames:
        blockers.append("benchmark_frame_missing")
    if validation.get("gate_decision") != "DATA_INPUT_VALIDATION_PASS":
        blockers.append("data_input_validation_failed")
    return blockers


def _write_blocked_provider_result(output_dir: Path, gate_dir: Path, error: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_007_NORGATE_DATASET_BLOCKED",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "provider": "Norgate Data",
        "provider_query_performed": False,
        "internet_market_data_download_performed": False,
        "strategy_backtest_performed": False,
        "kronos_inference_performed": False,
        "portfolio_selection_performed": False,
        "promotion_allowed": False,
        "blockers": ["norgate_local_adapter_unavailable"],
        "error": error,
    }
    _write_json(output_dir / "candidate_007_norgate_dataset_result.json", result)
    _write_json(output_dir / "final_decision.json", {"decision": result["decision"], "blockers": result["blockers"], "promotion_allowed": False})
    (output_dir / "candidate_007_norgate_dataset_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _validate_gate(gate: dict[str, Any]) -> None:
    approved_statuses = {
        "APPROVED_NORGATE_SURVIVORSHIP_FREE_PANEL_BUILD_ONLY",
        "APPROVED_NORGATE_SURVIVORSHIP_FREE_PANEL_RERUN_AFTER_VALIDATOR_TOLERANCE_FIX",
    }
    if gate.get("status") not in approved_statuses:
        raise RuntimeError("Candidate 007 Norgate dataset gate is not approved.")
    for key in ("strategy_backtest_allowed", "kronos_inference_allowed", "portfolio_selection_allowed", "promotion_allowed", "paper_trading_allowed", "live_trading_allowed"):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")
    if gate.get("internet_market_data_download_allowed"):
        raise RuntimeError("Internet market-data downloads are forbidden for this run.")


def _skip_non_common_like_symbol(symbol: str) -> bool:
    upper = symbol.upper()
    return any(token in upper for token in (".U", ".WS", ".W", "-WS", "-WT", "-RIGHT", "-UNIT", ".RT"))


def _price_columns() -> list[str]:
    return ["symbol", "date", "open", "high", "low", "close", "volume", "provider_dataset"]


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: Any) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _markdown_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {result.get('run_id', RUN_ID)}",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: local Norgate dataset engineering only. No strategy backtest, no Kronos inference, no promotion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in result.get("symbol_counts", {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Blockers", ""])
    for blocker in result.get("blockers", []):
        lines.append(f"- `{blocker}`")
    if result.get("error"):
        lines.extend(["", "## Provider Error", "", f"`{result['error']}`"])
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_007_norgate_dataset_builder()
