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
    "intraday_data_query",
    "parameter_sweep",
    "short_selling",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
    "fundamental_quality_claim",
}
REQUIRED_DECISION_ITEMS = {
    "data_scope",
    "symbol_universe",
    "ranking_signal",
    "tradability_filter",
    "execution_rule",
    "cost_model",
    "sample_size_gate",
    "promotion_rule",
}


def validate_lowvol_tradability_preregistration(spec_dir: str | Path) -> dict[str, Any]:
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

    _check(checks, "preregistration_id", manifest.get("preregistration_id") == "PREREG-LOWVOL-TRADABILITY-001", str(manifest.get("preregistration_id")))
    _check(checks, "trial_id", manifest.get("trial_id") == "TRIAL-LOWVOL-TRADABILITY-001", str(manifest.get("trial_id")))
    _check(checks, "status_pre_run", manifest.get("status") == "APPROVED_EXISTING_DAILY_BACKTEST_NOT_EXECUTED", str(manifest.get("status")))
    _check(checks, "lookback_60", manifest.get("lookback_days") == 60, str(manifest.get("lookback_days")))
    _check(checks, "holding_5", manifest.get("holding_days") == 5, str(manifest.get("holding_days")))
    _check(checks, "rebalance_step_5", manifest.get("rebalance_step_days") == 5, str(manifest.get("rebalance_step_days")))
    _check(checks, "cost_500bps", manifest.get("round_trip_cost_bps") == 500, str(manifest.get("round_trip_cost_bps")))
    _check(checks, "minimum_trade_count_30", manifest.get("minimum_trade_count") == 30, str(manifest.get("minimum_trade_count")))
    _check(checks, "provider_query_blocked", manifest.get("provider_query_allowed") is False, str(manifest.get("provider_query_allowed")))
    _check(checks, "market_download_blocked", manifest.get("market_data_download_allowed") is False, str(manifest.get("market_data_download_allowed")))
    _check(checks, "intraday_query_blocked", manifest.get("intraday_query_allowed") is False, str(manifest.get("intraday_query_allowed")))
    _check(checks, "parameter_sweep_blocked", manifest.get("parameter_sweep_allowed") is False, str(manifest.get("parameter_sweep_allowed")))
    _check(checks, "short_selling_blocked", manifest.get("short_selling_allowed") is False, str(manifest.get("short_selling_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))
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
        "gate_decision": "LOWVOL_TRADABILITY_PREREGISTRATION_PASS" if failed == 0 else "LOWVOL_TRADABILITY_PREREGISTRATION_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate LowVol Tradability preregistration.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_lowvol_tradability_preregistration(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
