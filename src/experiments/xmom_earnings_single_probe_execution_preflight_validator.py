from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.experiments.xmom_earnings_single_probe_approval_validator import (
    validate_xmom_earnings_single_probe_approval,
)


DEFAULT_APPROVAL_GATE_DIR = "experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521"
DEFAULT_EXPLICIT_APPROVAL_DIR = "experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_20260521"
DEFAULT_OUTPUT_DIR = "experiments/provider_aware_research/execution_outputs/XMOM-EARNINGS-SINGLE-PROBE-001"
DEFAULT_LEDGER_PATH = "experiments/provider_aware_research/trial_ledger/xmom_earnings_single_probe_trial_ledger.csv"
EXPECTED_GATE_ID = "EARNINGS-SINGLE-PROBE-XMOM-CATALYST-001"
EXPECTED_TRIAL_ID = "TRIAL-XMOM-CATALYST-001"
EXPECTED_OUTPUT_NAME = "XMOM-EARNINGS-SINGLE-PROBE-001"


def validate_xmom_earnings_single_probe_execution_preflight(
    approval_gate_dir: str | Path = DEFAULT_APPROVAL_GATE_DIR,
    explicit_approval_dir: str | Path = DEFAULT_EXPLICIT_APPROVAL_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    gate_report = validate_xmom_earnings_single_probe_approval(approval_gate_dir)
    _add_check(checks, "approval_gate_validator_passed", gate_report["status"] == "pass", f"failed={gate_report['summary']['failed']}")

    approval = _read_json(Path(explicit_approval_dir) / "single_probe_explicit_approval_manifest.json", checks)
    output_path = Path(output_dir)
    ledger = _read_csv(Path(ledger_path), checks)

    _validate_explicit_approval(approval, output_path, checks)
    _validate_output_dir(output_path, approval, checks)
    _validate_ledger(ledger, approval, output_path, checks)

    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "blocked",
        "decision": "XMOM_EARNINGS_SINGLE_PROBE_PREFLIGHT_PASS_READY_FOR_APPROVED_EXECUTION" if failed == 0 else "XMOM_EARNINGS_SINGLE_PROBE_PREFLIGHT_BLOCKED",
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate XMOM earnings single-probe execution preflight.")
    parser.add_argument("--approval-gate-dir", default=DEFAULT_APPROVAL_GATE_DIR)
    parser.add_argument("--explicit-approval-dir", default=DEFAULT_EXPLICIT_APPROVAL_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ledger-path", default=DEFAULT_LEDGER_PATH)
    args = parser.parse_args(argv)
    report = validate_xmom_earnings_single_probe_execution_preflight(
        approval_gate_dir=args.approval_gate_dir,
        explicit_approval_dir=args.explicit_approval_dir,
        output_dir=args.output_dir,
        ledger_path=args.ledger_path,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_explicit_approval(approval: dict[str, Any], output_path: Path, checks: list[dict[str, str]]) -> None:
    identity_ok = (
        approval.get("status") == "APPROVAL_GRANTED_FOR_SINGLE_PROBE_PREPARATION"
        and approval.get("gate_id") == EXPECTED_GATE_ID
        and approval.get("trial_id") == EXPECTED_TRIAL_ID
    )
    provider_selected = bool(approval.get("provider")) and approval.get("provider") != "unselected"
    symbol_selected = bool(approval.get("symbol")) and approval.get("symbol") != "unselected"
    endpoint_selected = bool(approval.get("endpoint")) and approval.get("endpoint") != "unselected"
    output_ok = approval.get("output_directory_created") is True and output_path.name == approval.get("output_id")
    ledger_ok = approval.get("trial_ledger_entry_created") is True
    scope_ok = (
        approval.get("max_provider_calls") == 1
        and approval.get("max_provider_count") == 1
        and approval.get("max_symbol_count") == 1
        and approval.get("max_endpoint_count") == 1
    )
    safe = (
        approval.get("provider_query_performed") is False
        and approval.get("network_call_performed") is False
        and approval.get("market_data_downloaded") is False
        and approval.get("raw_payload_retention_allowed") is False
        and approval.get("extractor_implemented") is False
        and approval.get("backtest_performed") is False
        and approval.get("strategy_promotion_performed") is False
    )
    _add_check(checks, "explicit_approval_identity", identity_ok, f"status={approval.get('status')}; gate={approval.get('gate_id')}; trial={approval.get('trial_id')}")
    _add_check(checks, "explicit_approval_provider_selected", provider_selected, f"provider={approval.get('provider')}")
    _add_check(checks, "explicit_approval_symbol_selected", symbol_selected, f"symbol={approval.get('symbol')}")
    _add_check(checks, "explicit_approval_endpoint_selected", endpoint_selected, f"endpoint={approval.get('endpoint')}")
    _add_check(checks, "explicit_approval_output_directory_created", output_ok, f"output_id={approval.get('output_id')}; output={output_path}")
    _add_check(checks, "explicit_approval_ledger_entry_created", ledger_ok, f"trial_ledger_entry_created={approval.get('trial_ledger_entry_created')}")
    _add_check(checks, "explicit_approval_scope_bounded", scope_ok, f"calls={approval.get('max_provider_calls')}; providers={approval.get('max_provider_count')}; symbols={approval.get('max_symbol_count')}; endpoints={approval.get('max_endpoint_count')}")
    _add_check(checks, "explicit_approval_pre_execution_safety_flags", safe, f"safe={safe}")


def _validate_output_dir(output_path: Path, approval: dict[str, Any], checks: list[dict[str, str]]) -> None:
    pre_manifest = output_path / "single_probe_pre_execution_manifest.json"
    execution_manifest = output_path / "single_probe_execution_manifest.json"
    _add_check(checks, "output_dir_exists", output_path.exists() and output_path.is_dir(), str(output_path))
    _add_check(checks, "output_name_expected", output_path.name == approval.get("output_id") == EXPECTED_OUTPUT_NAME, f"output={output_path.name}; approval={approval.get('output_id')}")
    _add_check(checks, "pre_execution_manifest_exists", pre_manifest.exists(), str(pre_manifest))
    _add_check(checks, "execution_manifest_absent", not execution_manifest.exists(), str(execution_manifest))
    if pre_manifest.exists():
        manifest = json.loads(pre_manifest.read_text(encoding="utf-8"))
        safe = (
            manifest.get("status") == "prepared_not_executed"
            and manifest.get("provider_query_performed") is False
            and manifest.get("network_call_performed") is False
            and manifest.get("max_provider_calls") == 1
            and manifest.get("raw_payload_retention_allowed") is False
        )
        _add_check(checks, "pre_execution_manifest_safe", safe, f"status={manifest.get('status')}; calls={manifest.get('max_provider_calls')}")


def _validate_ledger(rows: list[dict[str, str]], approval: dict[str, Any], output_path: Path, checks: list[dict[str, str]]) -> None:
    _add_check(checks, "ledger_has_one_pre_execution_row", len(rows) == 1, f"rows={len(rows)}")
    if not rows:
        return
    row = rows[0]
    identity_ok = (
        row.get("gate_id") == EXPECTED_GATE_ID
        and row.get("trial_id") == EXPECTED_TRIAL_ID
        and row.get("provider") == approval.get("provider")
        and row.get("symbol") == approval.get("symbol")
        and row.get("endpoint") == approval.get("endpoint")
    )
    status_ok = row.get("result_status") == "prepared_not_executed" and row.get("decision") == "pending_execution"
    output_ok = Path(row.get("artifact_dir", "")).name == output_path.name
    budget_ok = row.get("trial_number") == "1" and row.get("within_budget") == "yes"
    _add_check(checks, "ledger_identity_matches_approval", identity_ok, f"row={row}")
    _add_check(checks, "ledger_pre_execution_status", status_ok, f"status={row.get('result_status')}; decision={row.get('decision')}")
    _add_check(checks, "ledger_output_matches", output_ok, f"artifact_dir={row.get('artifact_dir')}; output={output_path}")
    _add_check(checks, "ledger_budget_bounded", budget_ok, f"trial_number={row.get('trial_number')}; within_budget={row.get('within_budget')}")


def _read_json(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, f"json_readable:{path.name}", False, f"{path}: {type(exc).__name__}: {exc}")
        return {}
    _add_check(checks, f"json_readable:{path.name}", True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as exc:
        _add_check(checks, f"csv_readable:{path.name}", False, f"{path}: {type(exc).__name__}: {exc}")
        return []
    _add_check(checks, f"csv_readable:{path.name}", bool(rows), f"rows={len(rows)}")
    return rows


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


if __name__ == "__main__":
    raise SystemExit(main())
