from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = ["README.md", "scan_manifest.json", "blocked_actions.csv", "provider_matrix.csv", "decision_rule.csv"]
REQUIRED_BLOCKED_ACTIONS = {
    "provider_query",
    "market_data_download",
    "run_backtest",
    "parameter_sweep",
    "short_selling",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}
REQUIRED_PROVIDERS = {"Polygon/Massive", "Sharadar/Nasdaq Data Link", "Intrinio Securities", "Tiingo", "SEC company_tickers"}
REQUIRED_DECISION_ITEMS = {"hard_requirements", "api_probe_priority", "cost_priority", "blocked_if_current_only", "next_step"}


def validate_reference_data_provider_scan_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)
    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)

    manifest = json.loads((path / "scan_manifest.json").read_text(encoding="utf-8"))
    blocked = _read_csv_set(path / "blocked_actions.csv", "action")
    providers = _read_csv_set(path / "provider_matrix.csv", "provider")
    decision_items = _read_csv_set(path / "decision_rule.csv", "decision_item")

    _check(checks, "scan_id", manifest.get("scan_id") == "REFERENCE-DATA-PROVIDER-SCAN-001", str(manifest.get("scan_id")))
    _check(checks, "trial_id", manifest.get("trial_id") == "REFERENCE-DATA-PROVIDER-SCAN-001", str(manifest.get("trial_id")))
    _check(checks, "status_pre_run", manifest.get("status") == "APPROVED_DOCUMENTATION_SCAN_NOT_EXECUTED", str(manifest.get("status")))
    _check(checks, "provider_query_blocked", manifest.get("provider_query_allowed") is False, str(manifest.get("provider_query_allowed")))
    _check(checks, "market_download_blocked", manifest.get("market_data_download_allowed") is False, str(manifest.get("market_data_download_allowed")))
    _check(checks, "backtest_blocked", manifest.get("backtest_allowed") is False, str(manifest.get("backtest_allowed")))
    _check(checks, "parameter_sweep_blocked", manifest.get("parameter_sweep_allowed") is False, str(manifest.get("parameter_sweep_allowed")))
    _check(checks, "short_selling_blocked", manifest.get("short_selling_allowed") is False, str(manifest.get("short_selling_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))
    _check(checks, "required_blocked_actions", REQUIRED_BLOCKED_ACTIONS.issubset(blocked), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - blocked)}")
    _check(checks, "required_providers", REQUIRED_PROVIDERS.issubset(providers), f"missing={sorted(REQUIRED_PROVIDERS - providers)}")
    _check(checks, "required_decision_items", REQUIRED_DECISION_ITEMS.issubset(decision_items), f"missing={sorted(REQUIRED_DECISION_ITEMS - decision_items)}")
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
        "gate_decision": "REFERENCE_DATA_PROVIDER_SCAN_GATE_PASS" if failed == 0 else "REFERENCE_DATA_PROVIDER_SCAN_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate reference-data provider scan gate.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_reference_data_provider_scan_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
