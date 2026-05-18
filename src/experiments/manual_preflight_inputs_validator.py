from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "manual_preflight_inputs_manifest.json",
    "manual_input_resolution.csv",
    "final_command_review.csv",
    "output_directory_plan.csv",
    "trial_ledger_planned_entry.csv",
    "credential_check_policy.csv",
    "manual_preflight_inputs_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "linked_preflight",
    "research_stage",
    "execution_approval_status",
    "no_provider_query",
    "no_backtest",
    "no_strategy_promotion",
    "required_tables",
]

REQUIRED_INPUTS = {
    "explicit_user_execution_approval",
    "final_execution_module",
    "final_output_directory",
    "trial_ledger_entry",
    "provider_credentials_check",
    "command_dry_review",
}


def validate_manual_preflight_inputs(artifact_dir: str | Path) -> dict[str, Any]:
    path = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "artifact_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "manual_preflight_inputs_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    resolution = _read_csv(path / "manual_input_resolution.csv", checks, "csv_readable:manual_input_resolution.csv")
    command = _read_csv(path / "final_command_review.csv", checks, "csv_readable:final_command_review.csv")
    output_dir = _read_csv(path / "output_directory_plan.csv", checks, "csv_readable:output_directory_plan.csv")
    ledger = _read_csv(path / "trial_ledger_planned_entry.csv", checks, "csv_readable:trial_ledger_planned_entry.csv")
    credentials = _read_csv(path / "credential_check_policy.csv", checks, "csv_readable:credential_check_policy.csv")
    _read_text_file(path / "manual_preflight_inputs_summary.md", checks, "markdown_readable:manual_preflight_inputs_summary.md")

    if resolution is not None:
        _validate_resolution(resolution, checks)
    if command is not None:
        _validate_command(command, checks)
    if output_dir is not None:
        _validate_output_dir(output_dir, checks)
    if ledger is not None:
        _validate_ledger(ledger, checks)
    if credentials is not None:
        _validate_credentials(credentials, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_manual_preflight_inputs(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate manual preflight input resolution artifact.")
    parser.add_argument("--artifact-dir", required=True, help="Manual preflight input artifact directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    tables_ok = isinstance(manifest.get("required_tables"), list) and bool(manifest.get("required_tables"))
    spec_only_ok = manifest.get("status") == "SPEC_ONLY_NOT_EXECUTED" and manifest.get("execution_approval_status") == "not_granted"
    stage_ok = manifest.get("research_stage") == "new_signal_research"
    flags_ok = manifest.get("no_provider_query") is True and manifest.get("no_backtest") is True and manifest.get("no_strategy_promotion") is True
    _add_check(checks, "manifest_required_fields", not missing and tables_ok, f"missing={missing}; required_tables_ok={tables_ok}")
    _add_check(checks, "manifest_spec_only_not_approved", spec_only_ok, f"status={manifest.get('status')}; execution_approval_status={manifest.get('execution_approval_status')}")
    _add_check(checks, "manifest_stage_new_signal_research", stage_ok, f"research_stage={manifest.get('research_stage')}")
    _add_check(checks, "manifest_no_execution_flags", flags_ok, f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}; no_strategy_promotion={manifest.get('no_strategy_promotion')}")


def _validate_resolution(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"input_name", "previous_status", "new_status", "blocks_execution", "resolution_detail"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "resolution_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    inputs = set(frame["input_name"].astype(str).tolist())
    missing_inputs = sorted(REQUIRED_INPUTS - inputs)
    approval = frame[frame["input_name"].astype(str).eq("explicit_user_execution_approval")]
    approval_not_granted = len(approval) == 1 and str(approval.iloc[0]["new_status"]).lower() == "not_granted"
    blocking_inputs = {
        "explicit_user_execution_approval",
        "final_execution_module",
        "final_output_directory",
        "trial_ledger_entry",
        "command_dry_review",
    }
    blocking_rows = frame[frame["input_name"].astype(str).isin(blocking_inputs)]
    all_block = len(blocking_rows) == len(blocking_inputs) and blocking_rows["blocks_execution"].astype(str).str.lower().eq("yes").all()
    _add_check(checks, "resolution_required_inputs", not missing_inputs, f"missing={missing_inputs}")
    _add_check(checks, "resolution_approval_not_granted", approval_not_granted, f"approval_rows={len(approval)}")
    _add_check(checks, "resolution_all_block_execution", bool(all_block), f"all_block={bool(all_block)}")


def _validate_command(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "value", "status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "command_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    fields = set(frame["field"].astype(str).tolist())
    required_fields = {"command_id", "module", "entrypoint", "arguments", "forbidden_flags_absent", "execution_approval"}
    missing_fields = sorted(required_fields - fields)
    approval = frame[frame["field"].astype(str).eq("execution_approval")]
    approval_blocks = len(approval) == 1 and str(approval.iloc[0]["value"]).lower() == "not_granted" and str(approval.iloc[0]["status"]).lower() == "blocks_execution"
    forbidden = frame[frame["field"].astype(str).eq("forbidden_flags_absent")]
    forbidden_ok = len(forbidden) == 1 and str(forbidden.iloc[0]["status"]).lower() == "pass"
    statuses = frame["status"].astype(str).str.lower()
    not_executed = not statuses.isin({"executed", "completed", "run"}).any()
    _add_check(checks, "command_required_fields", not missing_fields, f"missing={missing_fields}")
    _add_check(checks, "command_approval_blocks_execution", approval_blocks, f"approval_rows={len(approval)}")
    _add_check(checks, "command_forbidden_flags_absent", forbidden_ok, f"forbidden_rows={len(forbidden)}")
    _add_check(checks, "command_not_marked_executed", bool(not_executed), f"not_executed={bool(not_executed)}")


def _validate_output_dir(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "value", "status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "output_dir_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    creation = frame[frame["field"].astype(str).eq("directory_creation")]
    not_created = len(creation) == 1 and str(creation.iloc[0]["value"]).lower() == "not_performed"
    raw_retention = frame[frame["field"].astype(str).eq("raw_payload_retention")]
    raw_false = len(raw_retention) == 1 and str(raw_retention.iloc[0]["value"]).lower() == "false"
    _add_check(checks, "output_dir_not_created_in_spec", not_created, f"creation_rows={len(creation)}")
    _add_check(checks, "output_dir_raw_retention_false", raw_false, f"raw_rows={len(raw_retention)}")


def _validate_ledger(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "planned_value", "status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "ledger_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    consumed = frame[frame["field"].astype(str).eq("trial_consumed")]
    not_consumed = len(consumed) == 1 and str(consumed.iloc[0]["planned_value"]).lower() == "false"
    result = frame[frame["field"].astype(str).eq("result_status")]
    not_run = len(result) == 1 and str(result.iloc[0]["planned_value"]).lower() == "not_run"
    write = frame[frame["field"].astype(str).eq("ledger_write_status")]
    not_created = len(write) == 1 and str(write.iloc[0]["planned_value"]).lower() == "not_created"
    _add_check(checks, "ledger_trial_not_consumed", not_consumed, f"consumed_rows={len(consumed)}")
    _add_check(checks, "ledger_result_not_run", not_run, f"result_rows={len(result)}")
    _add_check(checks, "ledger_not_created", not_created, f"write_rows={len(write)}")


def _validate_credentials(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"credential", "required", "check_status", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "credentials_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    credentials = set(frame["credential"].astype(str).tolist())
    required_credentials = {"DATABENTO_API_KEY", "POLYGON_API_KEY", "provider_query_performed"}
    missing_credentials = sorted(required_credentials - credentials)
    query = frame[frame["credential"].astype(str).eq("provider_query_performed")]
    no_query = len(query) == 1 and str(query.iloc[0]["required"]).lower() == "no" and str(query.iloc[0]["check_status"]).lower() == "false"
    checked = frame[frame["credential"].astype(str).isin({"DATABENTO_API_KEY", "POLYGON_API_KEY"})]
    safe_credential_statuses = {"not_checked", "presence_check_implemented_not_run", "missing_local_env", "present_env_file_no_disclosure"}
    not_checked = checked["check_status"].astype(str).str.lower().isin(safe_credential_statuses).all()
    _add_check(checks, "credentials_required_items", not missing_credentials, f"missing={missing_credentials}")
    _add_check(checks, "credentials_no_provider_query", no_query, f"query_rows={len(query)}")
    _add_check(checks, "credentials_not_checked_in_spec", bool(not_checked), f"not_checked={bool(not_checked)}")


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, not frame.empty and bool(frame.columns.tolist()), f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_text_file(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "artifact_dir": str(path),
        "status": "pass" if not failed else "fail",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
