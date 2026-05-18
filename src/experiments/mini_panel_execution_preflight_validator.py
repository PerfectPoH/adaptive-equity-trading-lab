from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.experiments.mini_panel_approval_gate_validator import validate_mini_panel_approval_gate

DEFAULT_GATE_DIR = "experiments/provider_aware_research/mini_panel_approval_gate_20260518"
DEFAULT_APPROVAL_DIR = "experiments/provider_aware_research/mini_panel_explicit_approval_20260518"
DEFAULT_OUTPUT_DIR = "experiments/provider_aware_research/execution_outputs/MINIPANEL-PREREG-PA-SMALLCAP-001-001"
DEFAULT_LEDGER_PATH = "experiments/provider_aware_research/trial_ledger/mini_panel_trial_ledger.csv"
EXPECTED_PANEL_ID = "MINIPANEL-PREREG-PA-SMALLCAP-001-001"
EXPECTED_PREREGISTRATION_ID = "PREREG-PA-SMALLCAP-001"


def validate_mini_panel_execution_preflight(
    gate_dir: str | Path = DEFAULT_GATE_DIR,
    approval_dir: str | Path = DEFAULT_APPROVAL_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    gate_report = validate_mini_panel_approval_gate(gate_dir)
    _add_check(checks, "gate_validator_passed", gate_report["status"] == "pass", f"failed={gate_report['summary']['failed']}")
    approval = _read_json(Path(approval_dir) / "mini_panel_explicit_approval_manifest.json", checks)
    output_path = Path(output_dir)
    ledger = _read_csv(Path(ledger_path), checks)
    _validate_approval(approval, output_path, checks)
    _validate_output_dir(output_path, checks)
    _validate_ledger(ledger, checks)
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "blocked",
        "decision": "MINI_PANEL_PREFLIGHT_PASS_READY_FOR_APPROVED_EXECUTION" if failed == 0 else "MINI_PANEL_PREFLIGHT_BLOCKED",
        "provider_query_performed": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate mini-panel execution preflight.")
    parser.add_argument("--gate-dir", default=DEFAULT_GATE_DIR)
    parser.add_argument("--approval-dir", default=DEFAULT_APPROVAL_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ledger-path", default=DEFAULT_LEDGER_PATH)
    args = parser.parse_args(argv)
    report = validate_mini_panel_execution_preflight(args.gate_dir, args.approval_dir, args.output_dir, args.ledger_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_approval(approval: dict[str, Any], output_path: Path, checks: list[dict[str, str]]) -> None:
    _add_check(checks, "approval_status_granted", approval.get("status") == "APPROVAL_GRANTED_FOR_MINI_PANEL_PREPARATION", f"status={approval.get('status')}")
    _add_check(checks, "approval_panel_identity", approval.get("panel_id") == EXPECTED_PANEL_ID and approval.get("preregistration_id") == EXPECTED_PREREGISTRATION_ID, f"panel_id={approval.get('panel_id')}; preregistration_id={approval.get('preregistration_id')}")
    _add_check(checks, "approval_output_dir_created", approval.get("output_directory_created") is True and output_path.name == approval.get("panel_id"), f"output={output_path}")
    _add_check(checks, "approval_ledger_created", approval.get("trial_ledger_entries_created") is True, f"trial_ledger_entries_created={approval.get('trial_ledger_entries_created')}")
    _add_check(checks, "approval_query_budget_bounded", approval.get("max_new_provider_queries") == 3 and approval.get("max_total_panel_candidates") == 4, f"max_new={approval.get('max_new_provider_queries')}; max_total={approval.get('max_total_panel_candidates')}")
    safe = approval.get("provider_query_performed") is False and approval.get("backtest_performed") is False and approval.get("strategy_promotion_performed") is False and approval.get("raw_payload_retention_allowed") is False
    _add_check(checks, "approval_pre_execution_safety_flags", safe, f"safe={safe}")


def _validate_output_dir(output_path: Path, checks: list[dict[str, str]]) -> None:
    pre_manifest = output_path / "mini_panel_pre_execution_manifest.json"
    execution_manifest = output_path / "mini_panel_execution_manifest.json"
    _add_check(checks, "output_dir_exists", output_path.exists() and output_path.is_dir(), str(output_path))
    _add_check(checks, "pre_execution_manifest_exists", pre_manifest.exists(), str(pre_manifest))
    _add_check(checks, "execution_manifest_absent", not execution_manifest.exists(), str(execution_manifest))
    if pre_manifest.exists():
        manifest = json.loads(pre_manifest.read_text(encoding="utf-8"))
        safe = manifest.get("status") == "prepared_not_executed" and manifest.get("provider_query_performed") is False and manifest.get("new_provider_query_count_planned") == 3
        _add_check(checks, "pre_execution_manifest_safe", safe, f"status={manifest.get('status')}; planned={manifest.get('new_provider_query_count_planned')}")


def _validate_ledger(rows: list[dict[str, str]], checks: list[dict[str, str]]) -> None:
    _add_check(checks, "ledger_has_four_pre_execution_rows", len(rows) == 4, f"rows={len(rows)}")
    if not rows:
        return
    panel_ids = {row.get("panel_id") for row in rows}
    result_statuses = {row.get("result_status") for row in rows}
    roles = [row.get("candidate_role") for row in rows]
    _add_check(checks, "ledger_panel_identity", panel_ids == {EXPECTED_PANEL_ID}, f"panel_ids={sorted(str(item) for item in panel_ids)}")
    _add_check(checks, "ledger_pre_execution_statuses", result_statuses == {"already_executed_single_diagnostic", "prepared_not_executed"}, f"result_statuses={sorted(str(item) for item in result_statuses)}")
    _add_check(checks, "ledger_one_anchor_three_proposed", roles.count("executed_anchor") == 1 and roles.count("proposed_new_query") == 3, f"roles={roles}")


def _read_json(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, f"json_readable:{path.name}", False, f"{path}: {exc}")
        return {}
    _add_check(checks, f"json_readable:{path.name}", True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as exc:
        _add_check(checks, f"csv_readable:{path.name}", False, f"{path}: {exc}")
        return []
    _add_check(checks, f"csv_readable:{path.name}", bool(rows), f"rows={len(rows)}")
    return rows


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


if __name__ == "__main__":
    raise SystemExit(main())
