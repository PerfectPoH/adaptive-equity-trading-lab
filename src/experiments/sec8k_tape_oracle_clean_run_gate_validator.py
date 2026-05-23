from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "README.md",
    "run_authorization_manifest.json",
    "allowed_symbols.csv",
    "blocked_actions.csv",
    "decision_rule.csv",
]

REQUIRED_SYMBOLS = {"AEHR", "ARRY", "CABA", "CRMD", "IOVA"}

REQUIRED_BLOCKED_ACTIONS = {
    "use_sec8k_mini_panel_001_for_calibration",
    "use_xmom_pnl_for_thresholds",
    "parameter_sweep",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
    "short_selling",
    "raw_payload_retention",
}

REQUIRED_DECISION_ITEMS = {
    "query_scope",
    "direction_source",
    "cost_gate",
    "sample_size_gate",
    "outlier_gate",
    "dsr_gate",
    "promotion_rule",
    "archive_rule",
}


def validate_sec8k_tape_oracle_clean_run_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)

    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)

    manifest = _read_json(path / "run_authorization_manifest.json")
    symbols = _read_csv_set(path / "allowed_symbols.csv", "symbol")
    blocked_actions = _read_csv_set(path / "blocked_actions.csv", "action")
    decision_items = _read_csv_set(path / "decision_rule.csv", "decision_item")

    _check(checks, "run_id_clean_002", manifest.get("run_id") == "SEC8K-TAPE-ORACLE-CLEAN-RUN-002", str(manifest.get("run_id")))
    _check(checks, "status_pre_run_not_executed", manifest.get("status") == "APPROVED_PRE_RUN_NOT_EXECUTED", str(manifest.get("status")))
    _check(checks, "provider_databento", manifest.get("provider") == "Databento", str(manifest.get("provider")))
    _check(checks, "dataset_xnas_itch", manifest.get("dataset") == "XNAS.ITCH", str(manifest.get("dataset")))
    _check(checks, "schema_ohlcv_1m", manifest.get("schema") == "ohlcv-1m", str(manifest.get("schema")))
    _check(checks, "max_events_bounded", isinstance(manifest.get("max_events"), int) and manifest["max_events"] <= 50, str(manifest.get("max_events")))
    _check(checks, "max_provider_calls_bounded", isinstance(manifest.get("max_provider_calls"), int) and manifest["max_provider_calls"] <= 50, str(manifest.get("max_provider_calls")))
    _check(checks, "control_sessions_fixed", manifest.get("control_sessions_per_event") == 5, str(manifest.get("control_sessions_per_event")))
    _check(checks, "oracle_window_frozen", manifest.get("oracle_window") == "09:30-09:45 America/New_York", str(manifest.get("oracle_window")))
    _check(checks, "entry_time_frozen", manifest.get("entry_time") == "09:46 America/New_York", str(manifest.get("entry_time")))
    _check(checks, "exit_time_frozen", manifest.get("exit_time") == "15:55 America/New_York", str(manifest.get("exit_time")))
    _check(checks, "volume_threshold_frozen", manifest.get("volume_ratio_threshold") == 3.0, str(manifest.get("volume_ratio_threshold")))
    _check(checks, "cost_model_worst_case_500bps", manifest.get("cost_model_bps") == 500, str(manifest.get("cost_model_bps")))
    _check(checks, "minimum_trade_count_30", manifest.get("minimum_trade_count") == 30, str(manifest.get("minimum_trade_count")))
    _check(checks, "dsr_threshold_095", manifest.get("dsr_threshold") == 0.95, str(manifest.get("dsr_threshold")))
    _check(checks, "raw_payload_not_retained", manifest.get("raw_payload_retention") is False, str(manifest.get("raw_payload_retention")))
    _check(checks, "invalidated_run_usage_blocked", manifest.get("invalidated_run_usage") == "blocked_audit_trail_only", str(manifest.get("invalidated_run_usage")))
    _check(checks, "provider_query_allowed_explicit", manifest.get("provider_query_allowed") is True, str(manifest.get("provider_query_allowed")))
    _check(checks, "market_data_download_allowed_explicit", manifest.get("market_data_download_allowed") is True, str(manifest.get("market_data_download_allowed")))
    _check(checks, "parameter_sweep_blocked", manifest.get("parameter_sweep_allowed") is False, str(manifest.get("parameter_sweep_allowed")))
    _check(checks, "paper_trading_blocked", manifest.get("paper_trading_allowed") is False, str(manifest.get("paper_trading_allowed")))
    _check(checks, "live_trading_blocked", manifest.get("live_trading_allowed") is False, str(manifest.get("live_trading_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))

    _check(checks, "required_symbols_present", REQUIRED_SYMBOLS.issubset(symbols), f"missing={sorted(REQUIRED_SYMBOLS - symbols)}")
    _check(checks, "blocked_actions_present", REQUIRED_BLOCKED_ACTIONS.issubset(blocked_actions), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - blocked_actions)}")
    _check(checks, "decision_items_present", REQUIRED_DECISION_ITEMS.issubset(decision_items), f"missing={sorted(REQUIRED_DECISION_ITEMS - decision_items)}")

    return _report(checks)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_set(path: Path, column: str) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return {str(row[column]) for row in reader if row.get(column)}


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "SEC8K_TAPE_ORACLE_CLEAN_RUN_GATE_PASS" if failed == 0 else "SEC8K_TAPE_ORACLE_CLEAN_RUN_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate SEC8K Tape Oracle clean run gate.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_sec8k_tape_oracle_clean_run_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
