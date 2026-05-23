from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELD_GROUPS = {"earnings_date", "timing", "actual_eps", "consensus_eps", "pit_metadata"}
REQUIRED_BLOCKED_ACTIONS = {"backtest", "market_data_download", "parameter_sweep", "paper_trading", "live_trading", "strategy_promotion", "raw_payload_retention"}


def validate_pead_earnings_source_probe_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in ("README.md", "probe_manifest.json", "required_fields.csv", "decision_rule.csv", "blocked_actions.csv"):
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    manifest = json.loads((path / "probe_manifest.json").read_text(encoding="utf-8"))
    fields = _read_csv_set(path / "required_fields.csv", "field_group")
    blocked = _read_csv_set(path / "blocked_actions.csv", "action")
    _check(checks, "probe_id", manifest.get("probe_id") == "PROBE-PEAD-EARNINGS-SOURCE-001", str(manifest.get("probe_id")))
    _check(checks, "status_pre_query", manifest.get("status") == "APPROVED_PRE_QUERY_NOT_EXECUTED", str(manifest.get("status")))
    _check(checks, "provider_intrinio", manifest.get("provider") == "Intrinio", str(manifest.get("provider")))
    _check(checks, "symbol_crmd", manifest.get("symbol") == "CRMD", str(manifest.get("symbol")))
    _check(checks, "max_one_call", manifest.get("max_provider_calls") == 1, str(manifest.get("max_provider_calls")))
    _check(checks, "raw_payload_blocked", manifest.get("raw_payload_retention") is False, str(manifest.get("raw_payload_retention")))
    _check(checks, "provider_query_explicit", manifest.get("provider_query_allowed") is True, str(manifest.get("provider_query_allowed")))
    _check(checks, "market_download_blocked", manifest.get("market_data_download_allowed") is False, str(manifest.get("market_data_download_allowed")))
    _check(checks, "backtest_blocked", manifest.get("backtest_allowed") is False, str(manifest.get("backtest_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))
    _check(checks, "required_field_groups_present", REQUIRED_FIELD_GROUPS.issubset(fields), f"missing={sorted(REQUIRED_FIELD_GROUPS - fields)}")
    _check(checks, "blocked_actions_present", REQUIRED_BLOCKED_ACTIONS.issubset(blocked), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - blocked)}")
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
        "gate_decision": "PEAD_EARNINGS_SOURCE_PROBE_GATE_PASS" if failed == 0 else "PEAD_EARNINGS_SOURCE_PROBE_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_pead_earnings_source_probe_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
