from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "README.md",
    "universe_expansion_manifest.json",
    "blocked_actions.csv",
    "universe_quality_rules.csv",
    "provider_requirements.csv",
    "candidate_universe_template.csv",
]
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
REQUIRED_RULES = {
    "exchange_whitelist",
    "security_type_common",
    "min_price",
    "min_liquidity",
    "survivorship_source",
    "active_window",
}
REQUIRED_PROVIDER_REQUIREMENTS = {
    "official_or_licensed_source",
    "point_in_time_membership",
    "security_type_metadata",
    "exchange_metadata",
    "rate_limit_budget",
    "raw_retention_policy",
}
REQUIRED_TEMPLATE_COLUMNS = {
    "symbol",
    "exchange",
    "security_type",
    "first_trade_date",
    "last_trade_date",
    "median_dollar_volume_60d",
    "median_close_60d",
    "survivorship_source",
    "include_candidate",
    "exclusion_reason",
}


def validate_universe_expansion_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)
    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)

    manifest = json.loads((path / "universe_expansion_manifest.json").read_text(encoding="utf-8"))
    blocked = _read_csv_set(path / "blocked_actions.csv", "action")
    rules = _read_csv_set(path / "universe_quality_rules.csv", "rule_id")
    provider_requirements = _read_csv_set(path / "provider_requirements.csv", "requirement_id")
    template_columns = _csv_columns(path / "candidate_universe_template.csv")

    _check(checks, "gate_id", manifest.get("gate_id") == "UNIVERSE-EXPANSION-GATE-001", str(manifest.get("gate_id")))
    _check(checks, "trial_id", manifest.get("trial_id") == "UNIVERSE-EXPANSION-GATE-001", str(manifest.get("trial_id")))
    _check(checks, "status_not_executable", manifest.get("status") == "APPROVED_UNIVERSE_GATE_NOT_EXECUTABLE", str(manifest.get("status")))
    _check(checks, "provider_query_blocked", manifest.get("provider_query_allowed") is False, str(manifest.get("provider_query_allowed")))
    _check(checks, "market_download_blocked", manifest.get("market_data_download_allowed") is False, str(manifest.get("market_data_download_allowed")))
    _check(checks, "backtest_blocked", manifest.get("backtest_allowed") is False, str(manifest.get("backtest_allowed")))
    _check(checks, "parameter_sweep_blocked", manifest.get("parameter_sweep_allowed") is False, str(manifest.get("parameter_sweep_allowed")))
    _check(checks, "short_selling_blocked", manifest.get("short_selling_allowed") is False, str(manifest.get("short_selling_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))
    _check(checks, "target_size_range", int(manifest.get("min_target_universe_size", 0)) >= 300 and int(manifest.get("max_target_universe_size", 0)) <= 1000, str(manifest))
    _check(checks, "liquidity_floor", float(manifest.get("min_median_dollar_volume_60d", 0)) >= 1_000_000, str(manifest.get("min_median_dollar_volume_60d")))
    _check(checks, "price_floor", float(manifest.get("min_median_close_60d", 0)) >= 1.0, str(manifest.get("min_median_close_60d")))
    _check(checks, "survivorship_required", manifest.get("survivorship_policy_required") is True, str(manifest.get("survivorship_policy_required")))
    _check(checks, "quality_report_before_backtest", manifest.get("universe_quality_report_required_before_backtest") is True, str(manifest.get("universe_quality_report_required_before_backtest")))
    _check(checks, "required_blocked_actions", REQUIRED_BLOCKED_ACTIONS.issubset(blocked), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - blocked)}")
    _check(checks, "required_quality_rules", REQUIRED_RULES.issubset(rules), f"missing={sorted(REQUIRED_RULES - rules)}")
    _check(checks, "required_provider_requirements", REQUIRED_PROVIDER_REQUIREMENTS.issubset(provider_requirements), f"missing={sorted(REQUIRED_PROVIDER_REQUIREMENTS - provider_requirements)}")
    _check(checks, "required_template_columns", REQUIRED_TEMPLATE_COLUMNS.issubset(template_columns), f"missing={sorted(REQUIRED_TEMPLATE_COLUMNS - template_columns)}")
    return _report(checks)


def _read_csv_set(path: Path, column: str) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {str(row[column]) for row in csv.DictReader(handle) if row.get(column)}


def _csv_columns(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return set(csv.DictReader(handle).fieldnames or [])


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "UNIVERSE_EXPANSION_GATE_PASS" if failed == 0 else "UNIVERSE_EXPANSION_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Universe Expansion Gate 001.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_universe_expansion_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
