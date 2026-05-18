from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "pre_execution_output_ledger_manifest.json",
    "output_directory_gate.csv",
    "trial_ledger_gate.csv",
    "pre_execution_blockers.csv",
    "pre_execution_output_ledger_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "research_stage",
    "preregistration_id",
    "trial_id",
    "run_id",
    "planned_output_dir",
    "output_directory_created",
    "trial_ledger_entry_created",
    "trial_consumed",
    "provider_query_performed",
    "backtest_performed",
    "strategy_promotion_performed",
    "execution_approval_status",
    "required_tables",
]


def validate_pre_execution_output_ledger(artifact_dir: str | Path) -> dict[str, Any]:
    root = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "artifact_dir_exists", root.exists() and root.is_dir(), str(root))
    for name in REQUIRED_FILES:
        _add_check(checks, f"required_file:{name}", (root / name).exists(), str(root / name))
    manifest = _read_json(root / "pre_execution_output_ledger_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    output_gate = _read_csv(root / "output_directory_gate.csv", checks)
    ledger_gate = _read_csv(root / "trial_ledger_gate.csv", checks)
    blockers = _read_csv(root / "pre_execution_blockers.csv", checks)
    _read_markdown(root / "pre_execution_output_ledger_summary.md", checks)
    prepared_mode = isinstance(manifest, dict) and manifest.get("status") == "PRE_EXECUTION_PREPARED_NOT_EXECUTED"
    if output_gate is not None:
        _validate_output_gate(output_gate, checks, prepared_mode)
    if ledger_gate is not None:
        _validate_ledger_gate(ledger_gate, checks, prepared_mode)
    if blockers is not None:
        _validate_blockers(blockers, checks)
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "artifact_dir": str(root),
        "status": "pass" if failed == 0 else "fail",
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pre-execution output and ledger gate artifact.")
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_pre_execution_output_ledger(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    safe_status = manifest.get("status") in {"SPEC_ONLY_NOT_EXECUTED", "PRE_EXECUTION_PREPARED_NOT_EXECUTED"}
    blocked = manifest.get("decision") in {"OUTPUT_LEDGER_GATES_DEFINED_EXECUTION_BLOCKED", "OUTPUT_LEDGER_GATES_PREPARED_EXECUTION_PENDING"}
    stage_ok = manifest.get("research_stage") == "new_signal_research"
    no_execution = (
        manifest.get("trial_consumed") is False
        and manifest.get("provider_query_performed") is False
        and manifest.get("backtest_performed") is False
        and manifest.get("strategy_promotion_performed") is False
    )
    approval_block = manifest.get("execution_approval_status") in {"not_granted", "granted_for_single_diagnostic_run"}
    _add_check(checks, "manifest_required_fields", not missing, f"missing={missing}")
    _add_check(checks, "manifest_spec_only_blocked", safe_status and blocked, f"status={manifest.get('status')}; decision={manifest.get('decision')}")
    _add_check(checks, "manifest_stage_new_signal_research", stage_ok, f"research_stage={manifest.get('research_stage')}")
    _add_check(checks, "manifest_no_provider_execution_side_effects", no_execution, f"no_execution={no_execution}")
    _add_check(checks, "manifest_approval_not_granted", approval_block, f"execution_approval_status={manifest.get('execution_approval_status')}")


def _validate_output_gate(frame: pd.DataFrame, checks: list[dict[str, str]], prepared_mode: bool) -> None:
    required_columns = {"field", "value", "status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    fields = set(frame["field"].astype(str).tolist()) if not missing_columns else set()
    required_fields = {"planned_output_dir", "directory_creation_allowed", "raw_payload_retention", "immutable_run_manifest_required", "write_test_performed"}
    creation = frame[frame["field"].astype(str).eq("directory_creation_allowed")]
    write_test = frame[frame["field"].astype(str).eq("write_test_performed")]
    raw = frame[frame["field"].astype(str).eq("raw_payload_retention")]
    _add_check(checks, "output_gate_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "output_gate_required_fields", required_fields.issubset(fields), f"missing={sorted(required_fields - fields)}")
    creation_ok = len(creation) == 1 and (
        str(creation.iloc[0]["value"]).lower() == "false" or prepared_mode and str(creation.iloc[0]["value"]).lower() == "true"
    )
    _add_check(checks, "output_gate_directory_not_allowed", creation_ok, f"rows={len(creation)}; prepared_mode={prepared_mode}")
    _add_check(checks, "output_gate_write_test_controlled", len(write_test) == 1 and str(write_test.iloc[0]["value"]).lower() in {"false", "true"}, f"rows={len(write_test)}")
    _add_check(checks, "output_gate_raw_retention_false", len(raw) == 1 and str(raw.iloc[0]["value"]).lower() == "false", f"rows={len(raw)}")


def _validate_ledger_gate(frame: pd.DataFrame, checks: list[dict[str, str]], prepared_mode: bool) -> None:
    required_columns = {"field", "value", "status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    fields = set(frame["field"].astype(str).tolist()) if not missing_columns else set()
    required_fields = {"trial_id", "preregistration_id", "trial_consumed", "trial_budget_remaining_after_run", "ledger_entry_created", "result_status"}
    consumed = frame[frame["field"].astype(str).eq("trial_consumed")]
    created = frame[frame["field"].astype(str).eq("ledger_entry_created")]
    result = frame[frame["field"].astype(str).eq("result_status")]
    _add_check(checks, "ledger_gate_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "ledger_gate_required_fields", required_fields.issubset(fields), f"missing={sorted(required_fields - fields)}")
    _add_check(checks, "ledger_gate_trial_not_consumed", len(consumed) == 1 and str(consumed.iloc[0]["value"]).lower() == "false", f"rows={len(consumed)}")
    created_ok = len(created) == 1 and (
        str(created.iloc[0]["value"]).lower() == "false" or prepared_mode and str(created.iloc[0]["value"]).lower() == "true"
    )
    _add_check(checks, "ledger_gate_entry_not_created", created_ok, f"rows={len(created)}; prepared_mode={prepared_mode}")
    _add_check(checks, "ledger_gate_result_not_executed", len(result) == 1 and str(result.iloc[0]["value"]).lower() in {"not_run", "prepared_not_executed"}, f"rows={len(result)}")


def _validate_blockers(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"blocker", "severity", "current_status", "required_response"}
    missing_columns = sorted(required_columns - set(frame.columns))
    critical_count = int(frame["severity"].astype(str).str.lower().eq("critical").sum()) if not missing_columns else 0
    present = frame["current_status"].astype(str).str.lower().eq("present").any() if not missing_columns else False
    _add_check(checks, "blockers_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "blockers_critical_present", critical_count >= 1, f"critical_count={critical_count}")
    _add_check(checks, "blockers_currently_present", bool(present), f"present={bool(present)}")


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]]) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, f"csv_readable:{path.name}", False, f"{path}: {exc}")
        return None
    _add_check(checks, f"csv_readable:{path.name}", True, f"rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_markdown(path: Path, checks: list[dict[str, str]]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, f"markdown_readable:{path.name}", False, f"{path}: {exc}")
        return
    _add_check(checks, f"markdown_readable:{path.name}", bool(text.strip()), f"chars={len(text)}")


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": detail})


if __name__ == "__main__":
    raise SystemExit(main())
