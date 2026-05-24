from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = ["README.md", "preregistration_manifest.json", "blocked_actions.csv", "decision_rule.csv"]
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
REQUIRED_DECISION_ITEMS = {
    "data_scope",
    "regime_features",
    "regime_priority",
    "trade_mapping",
    "attribution",
    "sample_size_gate",
    "promotion_rule",
}


def validate_regime_map_preregistration(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)
    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)

    manifest = json.loads((path / "preregistration_manifest.json").read_text(encoding="utf-8"))
    blocked = _read_csv_set(path / "blocked_actions.csv", "action")
    decisions = _read_csv_set(path / "decision_rule.csv", "decision_item")
    labels = set(manifest.get("regime_labels", []))

    _check(checks, "preregistration_id", manifest.get("preregistration_id") == "PREREG-REGIME-MAP-001", str(manifest.get("preregistration_id")))
    _check(checks, "trial_id", manifest.get("trial_id") == "REGIME-MAP-001", str(manifest.get("trial_id")))
    _check(checks, "status_pre_run", manifest.get("status") == "APPROVED_EXISTING_ARTIFACT_DIAGNOSTIC_NOT_EXECUTED", str(manifest.get("status")))
    _check(checks, "provider_query_blocked", manifest.get("provider_query_allowed") is False, str(manifest.get("provider_query_allowed")))
    _check(checks, "market_download_blocked", manifest.get("market_data_download_allowed") is False, str(manifest.get("market_data_download_allowed")))
    _check(checks, "backtest_blocked", manifest.get("backtest_allowed") is False, str(manifest.get("backtest_allowed")))
    _check(checks, "parameter_sweep_blocked", manifest.get("parameter_sweep_allowed") is False, str(manifest.get("parameter_sweep_allowed")))
    _check(checks, "short_selling_blocked", manifest.get("short_selling_allowed") is False, str(manifest.get("short_selling_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))
    _check(checks, "lookback_20", manifest.get("lookback_days") == 20, str(manifest.get("lookback_days")))
    _check(checks, "required_labels", {"VOLATILITY_SHOCK", "TREND_UP", "TREND_DOWN", "QUIET_RANGE", "MIXED_NORMAL"}.issubset(labels), str(sorted(labels)))
    _check(checks, "thresholds_positive", float(manifest.get("shock_abs_return_threshold", 0)) > 0 and float(manifest.get("trend_return_threshold", 0)) > 0, str(manifest))
    _check(checks, "required_blocked_actions", REQUIRED_BLOCKED_ACTIONS.issubset(blocked), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - blocked)}")
    _check(checks, "required_decision_items", REQUIRED_DECISION_ITEMS.issubset(decisions), f"missing={sorted(REQUIRED_DECISION_ITEMS - decisions)}")
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
        "gate_decision": "REGIME_MAP_PREREGISTRATION_PASS" if failed == 0 else "REGIME_MAP_PREREGISTRATION_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate REGIME-MAP-001 preregistration.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_regime_map_preregistration(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
