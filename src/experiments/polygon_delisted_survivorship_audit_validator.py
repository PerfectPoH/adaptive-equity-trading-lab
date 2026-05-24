from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = ["README.md", "audit_manifest.json", "blocked_actions.csv", "pass_fail_requirements.csv"]
REQUIRED_BLOCKED_ACTIONS = {
    "raw_payload_retention",
    "market_data_download",
    "run_backtest",
    "parameter_sweep",
    "short_selling",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}
REQUIRED_FIELDS = {"ticker", "primary_exchange", "type", "active", "delisted_utc"}


def validate_polygon_delisted_survivorship_audit_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)
    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    manifest = json.loads((path / "audit_manifest.json").read_text(encoding="utf-8"))
    blocked = _read_csv_set(path / "blocked_actions.csv", "action")
    fields = set(manifest.get("required_fields", []))

    _check(checks, "probe_id", manifest.get("probe_id") == "PROBE-POLYGON-DELISTED-SURVIVORSHIP-AUDIT-001", str(manifest.get("probe_id")))
    _check(checks, "trial_id", manifest.get("trial_id") == "UNIVERSE-SURVIVORSHIP-AUDIT-001", str(manifest.get("trial_id")))
    _check(checks, "status_pre_run", manifest.get("status") == "APPROVED_SINGLE_INACTIVE_REFERENCE_CALL_NOT_EXECUTED", str(manifest.get("status")))
    _check(checks, "provider_polygon", manifest.get("provider") == "Polygon/Massive", str(manifest.get("provider")))
    _check(checks, "api_key_env", manifest.get("api_key_env_var") == "POLYGON_API_KEY", str(manifest.get("api_key_env_var")))
    _check(checks, "single_call_bound", manifest.get("expected_max_calls") == 1, str(manifest.get("expected_max_calls")))
    _check(checks, "limit_bounded", 300 <= int(manifest.get("limit", 0)) <= 1000, str(manifest.get("limit")))
    _check(checks, "inactive_reference_query", manifest.get("query_active") is False, str(manifest.get("query_active")))
    _check(checks, "provider_query_allowed", manifest.get("provider_query_allowed") is True, str(manifest.get("provider_query_allowed")))
    _check(checks, "raw_retention_blocked", manifest.get("raw_payload_retention") is False, str(manifest.get("raw_payload_retention")))
    _check(checks, "market_download_blocked", manifest.get("market_data_download_allowed") is False, str(manifest.get("market_data_download_allowed")))
    _check(checks, "backtest_blocked", manifest.get("backtest_allowed") is False, str(manifest.get("backtest_allowed")))
    _check(checks, "parameter_sweep_blocked", manifest.get("parameter_sweep_allowed") is False, str(manifest.get("parameter_sweep_allowed")))
    _check(checks, "short_selling_blocked", manifest.get("short_selling_allowed") is False, str(manifest.get("short_selling_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))
    _check(checks, "pit_backtest_not_authorized", manifest.get("pit_universe_backtest_authorized") is False, str(manifest.get("pit_universe_backtest_authorized")))
    _check(checks, "pit_construction_required", manifest.get("requires_pit_membership_construction") is True, str(manifest.get("requires_pit_membership_construction")))
    _check(checks, "required_fields", REQUIRED_FIELDS.issubset(fields), f"missing={sorted(REQUIRED_FIELDS - fields)}")
    _check(checks, "required_blocked_actions", REQUIRED_BLOCKED_ACTIONS.issubset(blocked), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - blocked)}")
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
        "gate_decision": "POLYGON_DELISTED_SURVIVORSHIP_AUDIT_GATE_PASS" if failed == 0 else "POLYGON_DELISTED_SURVIVORSHIP_AUDIT_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Polygon delisted survivorship audit gate.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_polygon_delisted_survivorship_audit_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
