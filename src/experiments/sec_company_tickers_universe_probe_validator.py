from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = ["README.md", "probe_manifest.json", "blocked_actions.csv", "pass_fail_requirements.csv"]
REQUIRED_BLOCKED_ACTIONS = {
    "market_data_download",
    "run_backtest",
    "raw_payload_retention",
    "parameter_sweep",
    "short_selling",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}
REQUIRED_PASS_FIELDS = {"ticker", "cik_str", "exchange", "security_type", "first_trade_date_and_last_trade_date", "delisted_symbols"}


def validate_sec_company_tickers_universe_probe_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)
    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)

    manifest = json.loads((path / "probe_manifest.json").read_text(encoding="utf-8"))
    blocked = _read_csv_set(path / "blocked_actions.csv", "action")
    pass_fields = _read_csv_set(path / "pass_fail_requirements.csv", "field")

    _check(checks, "probe_id", manifest.get("probe_id") == "PROBE-SEC-COMPANY-TICKERS-UNIVERSE-001", str(manifest.get("probe_id")))
    _check(checks, "trial_id", manifest.get("trial_id") == "UNIVERSE-SOURCE-PROBE-001", str(manifest.get("trial_id")))
    _check(checks, "status_pre_run", manifest.get("status") == "APPROVED_SINGLE_CALL_NOT_EXECUTED", str(manifest.get("status")))
    _check(checks, "provider_sec", manifest.get("provider") == "SEC", str(manifest.get("provider")))
    _check(checks, "endpoint_fixed", manifest.get("endpoint") == "https://www.sec.gov/files/company_tickers.json", str(manifest.get("endpoint")))
    _check(checks, "single_call_bound", manifest.get("expected_max_calls") == 1, str(manifest.get("expected_max_calls")))
    _check(checks, "provider_query_allowed", manifest.get("provider_query_allowed") is True, str(manifest.get("provider_query_allowed")))
    _check(checks, "raw_retention_blocked", manifest.get("raw_payload_retention") is False, str(manifest.get("raw_payload_retention")))
    _check(checks, "market_download_blocked", manifest.get("market_data_download_allowed") is False, str(manifest.get("market_data_download_allowed")))
    _check(checks, "backtest_blocked", manifest.get("backtest_allowed") is False, str(manifest.get("backtest_allowed")))
    _check(checks, "parameter_sweep_blocked", manifest.get("parameter_sweep_allowed") is False, str(manifest.get("parameter_sweep_allowed")))
    _check(checks, "short_selling_blocked", manifest.get("short_selling_allowed") is False, str(manifest.get("short_selling_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))
    _check(checks, "required_blocked_actions", REQUIRED_BLOCKED_ACTIONS.issubset(blocked), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - blocked)}")
    _check(checks, "required_pass_fields", REQUIRED_PASS_FIELDS.issubset(pass_fields), f"missing={sorted(REQUIRED_PASS_FIELDS - pass_fields)}")
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
        "gate_decision": "SEC_COMPANY_TICKERS_UNIVERSE_PROBE_GATE_PASS" if failed == 0 else "SEC_COMPANY_TICKERS_UNIVERSE_PROBE_GATE_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate SEC company tickers universe probe gate.")
    parser.add_argument("--spec-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_sec_company_tickers_universe_probe_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
