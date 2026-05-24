from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = ["README.md", "policy_manifest.json", "blocked_actions.csv", "pass_fail_requirements.csv"]
REQUIRED_BLOCKED = {
    "provider_query",
    "market_data_download",
    "raw_payload_retention",
    "run_broad_universe_backtest",
    "run_strategy_backtest",
    "parameter_sweep",
    "short_selling",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}


def validate_polygon_pit_membership_policy_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)
    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    manifest = json.loads((path / "policy_manifest.json").read_text(encoding="utf-8"))
    blocked = _read_csv_set(path / "blocked_actions.csv", "action")

    _check(checks, "policy_id", manifest.get("policy_id") == "POLYGON-PIT-MEMBERSHIP-POLICY-GATE-001", str(manifest.get("policy_id")))
    _check(checks, "trial_id", manifest.get("trial_id") == "UNIVERSE-PIT-POLICY-GATE-001", str(manifest.get("trial_id")))
    _check(checks, "status_non_executable", manifest.get("status") == "APPROVED_NON_EXECUTABLE_POLICY_GATE", str(manifest.get("status")))
    _check(checks, "provider_query_blocked", manifest.get("provider_query_allowed") is False, str(manifest.get("provider_query_allowed")))
    _check(checks, "market_download_blocked", manifest.get("market_data_download_allowed") is False, str(manifest.get("market_data_download_allowed")))
    _check(checks, "raw_retention_blocked", manifest.get("raw_payload_retention") is False, str(manifest.get("raw_payload_retention")))
    _check(checks, "backtest_blocked", manifest.get("backtest_allowed") is False, str(manifest.get("backtest_allowed")))
    _check(checks, "broad_backtest_blocked", manifest.get("broad_universe_backtest_allowed") is False, str(manifest.get("broad_universe_backtest_allowed")))
    _check(checks, "parameter_sweep_blocked", manifest.get("parameter_sweep_allowed") is False, str(manifest.get("parameter_sweep_allowed")))
    _check(checks, "short_selling_blocked", manifest.get("short_selling_allowed") is False, str(manifest.get("short_selling_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))
    _check(checks, "listing_dates_unavailable", manifest.get("pit_listing_dates_available") is False, str(manifest.get("pit_listing_dates_available")))
    _check(checks, "pit_history_unconstructed", manifest.get("pit_membership_history_constructed") is False, str(manifest.get("pit_membership_history_constructed")))
    _check(checks, "listing_date_source_required", manifest.get("requires_listing_date_source_before_broad_backtest") is True, str(manifest.get("requires_listing_date_source_before_broad_backtest")))
    _check(checks, "pit_construction_required", manifest.get("requires_pit_membership_construction_before_broad_backtest") is True, str(manifest.get("requires_pit_membership_construction_before_broad_backtest")))
    _check(checks, "single_day_snapshot_conditionally_allowed", manifest.get("single_day_liquid_snapshot_allowed_if_inputs_pass") is True, str(manifest.get("single_day_liquid_snapshot_allowed_if_inputs_pass")))
    _check(checks, "input_decisions_declared", all(bool(str(manifest.get(key, "")).strip()) for key in ["active_seed_decision", "liquidity_probe_decision", "delisted_audit_decision"]), str(manifest))
    _check(checks, "required_blocked_actions", REQUIRED_BLOCKED.issubset(blocked), f"missing={sorted(REQUIRED_BLOCKED - blocked)}")
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
        "gate_decision": "POLYGON_PIT_MEMBERSHIP_POLICY_GATE_PASS" if failed == 0 else "POLYGON_PIT_MEMBERSHIP_POLICY_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Polygon PIT membership policy gate.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_polygon_pit_membership_policy_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
