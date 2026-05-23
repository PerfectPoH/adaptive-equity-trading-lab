from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_BLOCKED_ACTIONS = {
    "sec8k_tape_oracle_retrial",
    "sec8k_predrift_long_retrial",
    "sec8k_window_shopping",
    "sec8k_short_trial",
    "sec8k_directional_promotion",
}


def validate_sec8k_directional_alpha_retirement(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in ("README.md", "retirement_manifest.json", "blocked_actions.csv"):
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    manifest = json.loads((path / "retirement_manifest.json").read_text(encoding="utf-8"))
    actions = _read_csv_set(path / "blocked_actions.csv", "action")
    _check(checks, "artifact_id", manifest.get("artifact_id") == "SEC8K-DIRECTIONAL-ALPHA-RETIREMENT-001", str(manifest.get("artifact_id")))
    _check(checks, "regime_retained", manifest.get("regime_status") == "SEC8K_VOLATILITY_RISK_REGIME_RETAINED", str(manifest.get("regime_status")))
    _check(checks, "alpha_retired", manifest.get("alpha_status") == "SEC8K_LONG_ONLY_DIRECTIONAL_ALPHA_RETIRED", str(manifest.get("alpha_status")))
    _check(checks, "future_sec8k_long_only_trials_blocked", manifest.get("future_sec8k_long_only_directional_trials_allowed") is False, str(manifest.get("future_sec8k_long_only_directional_trials_allowed")))
    _check(checks, "future_sec8k_short_trials_blocked", manifest.get("future_sec8k_short_trials_allowed") is False, str(manifest.get("future_sec8k_short_trials_allowed")))
    _check(checks, "external_direction_required_for_reopen", manifest.get("requires_external_point_in_time_direction_source_for_reopening") is True, str(manifest.get("requires_external_point_in_time_direction_source_for_reopening")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))
    _check(checks, "blocked_actions_present", REQUIRED_BLOCKED_ACTIONS.issubset(actions), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - actions)}")
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
        "gate_decision": "SEC8K_DIRECTIONAL_ALPHA_RETIRED_PASS" if failed == 0 else "SEC8K_DIRECTIONAL_ALPHA_RETIRED_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_sec8k_directional_alpha_retirement(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
