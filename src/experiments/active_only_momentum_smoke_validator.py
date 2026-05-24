from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = ["README.md", "trial_manifest.json", "blocked_actions.csv", "pass_fail_requirements.csv"]
REQUIRED_BLOCKED = {
    "provider_query",
    "market_data_download",
    "raw_payload_retention",
    "parameter_sweep",
    "short_selling",
    "paper_trading",
    "live_trading",
    "survivorship_free_claim",
    "strategy_promotion",
}
REQUIRED_CAVEATS = {
    "provider_query_allowed": False,
    "market_data_download_allowed": False,
    "parameter_sweep_allowed": False,
    "short_selling_allowed": False,
    "paper_trading_allowed": False,
    "promotion_allowed": False,
    "survivorship_free_claim_allowed": False,
}


def validate_active_only_momentum_smoke_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)
    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    manifest = json.loads((path / "trial_manifest.json").read_text(encoding="utf-8"))
    blocked = _read_csv_set(path / "blocked_actions.csv", "action")
    _check(checks, "trial_id", manifest.get("trial_id") == "ACTIVE-ONLY-MOMENTUM-SMOKE-001", str(manifest.get("trial_id")))
    _check(checks, "status_pre_run", manifest.get("status") == "APPROVED_ACTIVE_ONLY_EXPLORATORY_BACKTEST_NOT_EXECUTED", str(manifest.get("status")))
    _check(checks, "policy_decision_exists", Path(str(manifest.get("active_only_policy_decision", ""))).is_file(), str(manifest.get("active_only_policy_decision")))
    _check(checks, "prices_exist", Path(str(manifest.get("input_prices", ""))).is_file(), str(manifest.get("input_prices")))
    _check(checks, "backtest_allowed", manifest.get("backtest_allowed") is True, str(manifest.get("backtest_allowed")))
    for key, expected in REQUIRED_CAVEATS.items():
        _check(checks, key.replace("_allowed", "_blocked"), manifest.get(key) is expected, str(manifest.get(key)))
    _check(checks, "cost_realism", manifest.get("cost_bps_round_trip") == 500, str(manifest.get("cost_bps_round_trip")))
    _check(checks, "fixed_symbols", manifest.get("symbols") == ["AEHR", "ARRY", "CABA", "CRMD", "IOVA"], str(manifest.get("symbols")))
    _check(checks, "fixed_parameters", manifest.get("lookback_days") == 63 and manifest.get("hold_days") == 21 and manifest.get("rebalance_step_days") == 21, str(manifest))
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
        "gate_decision": "ACTIVE_ONLY_MOMENTUM_SMOKE_GATE_PASS" if failed == 0 else "ACTIVE_ONLY_MOMENTUM_SMOKE_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate active-only momentum smoke gate.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_active_only_momentum_smoke_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
