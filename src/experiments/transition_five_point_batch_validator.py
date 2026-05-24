from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = ["README.md", "batch_manifest.json", "blocked_actions.csv", "pass_fail_requirements.csv"]
REQUIRED_POINTS = {
    "etf_largecap_regime_map",
    "risk_overlay_replay",
    "portfolio_allocation_smoke",
    "smallcap_microstructure_diagnostic",
    "data_upgrade_decision_matrix",
}
REQUIRED_BLOCKED_ACTIONS = {
    "provider_query",
    "market_data_download",
    "raw_payload_retention",
    "new_backtest",
    "parameter_sweep",
    "short_selling",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}
FALSE_FLAGS = {
    "provider_query_allowed": "provider_query_blocked",
    "market_data_download_allowed": "market_data_download_blocked",
    "raw_payload_retention_allowed": "raw_payload_retention_blocked",
    "backtest_allowed": "new_backtest_blocked",
    "parameter_sweep_allowed": "parameter_sweep_blocked",
    "short_selling_allowed": "short_selling_blocked",
    "paper_trading_allowed": "paper_trading_blocked",
    "live_trading_allowed": "live_trading_blocked",
    "promotion_allowed": "promotion_blocked",
}


def validate_transition_five_point_batch_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)
    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)

    manifest = json.loads((path / "batch_manifest.json").read_text(encoding="utf-8"))
    blocked_actions = _read_csv_set(path / "blocked_actions.csv", "action")
    _check(checks, "trial_id", manifest.get("trial_id") == "TRANSITION-FIVE-POINT-BATCH-001", str(manifest.get("trial_id")))
    _check(
        checks,
        "status_pre_run",
        manifest.get("status") == "APPROVED_EXISTING_ARTIFACTS_DIAGNOSTIC_NOT_EXECUTED",
        str(manifest.get("status")),
    )
    for key, check_name in FALSE_FLAGS.items():
        _check(checks, check_name, manifest.get(key) is False, str(manifest.get(key)))
    _check(checks, "five_points_declared", set(manifest.get("diagnostic_points", [])) == REQUIRED_POINTS, str(manifest.get("diagnostic_points")))
    _check(
        checks,
        "required_blocked_actions",
        REQUIRED_BLOCKED_ACTIONS.issubset(blocked_actions),
        f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - blocked_actions)}",
    )
    _check(checks, "transition_policy_exists", Path(str(manifest.get("transition_policy_decision", ""))).is_file(), str(manifest.get("transition_policy_decision")))
    _check(checks, "active_only_trade_panel_exists", Path(str(manifest.get("active_only_trade_panel", ""))).is_file(), str(manifest.get("active_only_trade_panel")))
    _check(checks, "active_only_robustness_exists", Path(str(manifest.get("active_only_robustness_decision", ""))).is_file(), str(manifest.get("active_only_robustness_decision")))
    _check(checks, "delisted_decision_exists", Path(str(manifest.get("delisted_listing_date_decision", ""))).is_file(), str(manifest.get("delisted_listing_date_decision")))
    _check(checks, "smallcap_prices_exist", Path(str(manifest.get("smallcap_price_file", ""))).is_file(), str(manifest.get("smallcap_price_file")))
    snapshot_files = [Path(str(item)) for item in manifest.get("snapshot_files", [])]
    _check(checks, "snapshot_files_non_empty", len(snapshot_files) > 0, str(snapshot_files))
    _check(checks, "snapshot_files_exist", all(path.is_file() for path in snapshot_files), str(snapshot_files))
    _check(checks, "min_symbols_for_allocation", int(manifest.get("minimum_allocation_symbols", 0)) >= 3, str(manifest.get("minimum_allocation_symbols")))
    return _report(checks)


def _read_csv_set(path: Path, column: str) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {str(row[column]) for row in csv.DictReader(handle) if row.get(column)}


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "TRANSITION_FIVE_POINT_BATCH_GATE_PASS" if failed == 0 else "TRANSITION_FIVE_POINT_BATCH_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TRANSITION-FIVE-POINT-BATCH-001 gate.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_transition_five_point_batch_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
