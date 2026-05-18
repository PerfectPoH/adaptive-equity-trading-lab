from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "execution_command_output_schema_manifest.json",
    "execution_command_spec.csv",
    "output_artifact_schema.csv",
    "run_manifest_schema.csv",
    "trial_ledger_entry_schema.csv",
    "preflight_blockers.csv",
    "execution_command_output_schema_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "linked_authorization",
    "linked_preregistered_plan",
    "research_stage",
    "execution_status",
    "no_provider_query",
    "no_backtest",
    "no_strategy_promotion",
    "required_tables",
]

REQUIRED_OUTPUT_ARTIFACTS = {
    "execution_manifest",
    "provider_coverage_audit",
    "derived_event_panel",
    "diagnostic_summary",
    "interpretation_report",
    "trial_ledger_update",
}

REQUIRED_RUN_MANIFEST_FIELDS = {
    "run_id",
    "preregistration_id",
    "authorization_id",
    "git_sha",
    "execution_started_at_utc",
    "execution_completed_at_utc",
    "execution_status",
    "raw_payload_retained",
    "strategy_promotion",
}

REQUIRED_BLOCKERS = {
    "output_dir_placeholder",
    "execution_module_not_final",
    "explicit_user_approval_missing",
    "provider_credentials_not_checked",
    "trial_ledger_not_created",
    "raw_payload_retention_forbidden",
}


def validate_execution_command_output_schema(artifact_dir: str | Path) -> dict[str, Any]:
    path = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "artifact_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "execution_command_output_schema_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    command = _read_csv(path / "execution_command_spec.csv", checks, "csv_readable:execution_command_spec.csv")
    outputs = _read_csv(path / "output_artifact_schema.csv", checks, "csv_readable:output_artifact_schema.csv")
    run_manifest = _read_csv(path / "run_manifest_schema.csv", checks, "csv_readable:run_manifest_schema.csv")
    ledger = _read_csv(path / "trial_ledger_entry_schema.csv", checks, "csv_readable:trial_ledger_entry_schema.csv")
    blockers = _read_csv(path / "preflight_blockers.csv", checks, "csv_readable:preflight_blockers.csv")
    _read_text_file(path / "execution_command_output_schema_summary.md", checks, "markdown_readable:execution_command_output_schema_summary.md")

    if command is not None:
        _validate_command(command, checks)
    if outputs is not None:
        _validate_outputs(outputs, checks)
    if run_manifest is not None:
        _validate_run_manifest(run_manifest, checks)
    if ledger is not None:
        _validate_ledger(ledger, checks)
    if blockers is not None:
        _validate_blockers(blockers, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_execution_command_output_schema(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate execution command and output schema artifact.")
    parser.add_argument("--artifact-dir", required=True, help="Execution command/output schema artifact directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    tables_ok = isinstance(manifest.get("required_tables"), list) and bool(manifest.get("required_tables"))
    spec_only_ok = manifest.get("status") == "SPEC_ONLY_NOT_EXECUTED" and manifest.get("execution_status") == "not_executed"
    stage_ok = manifest.get("research_stage") == "new_signal_research"
    flags_ok = manifest.get("no_provider_query") is True and manifest.get("no_backtest") is True and manifest.get("no_strategy_promotion") is True
    _add_check(checks, "manifest_required_fields", not missing and tables_ok, f"missing={missing}; required_tables_ok={tables_ok}")
    _add_check(checks, "manifest_spec_only_not_executed", spec_only_ok, f"status={manifest.get('status')}; execution_status={manifest.get('execution_status')}")
    _add_check(checks, "manifest_stage_new_signal_research", stage_ok, f"research_stage={manifest.get('research_stage')}")
    _add_check(checks, "manifest_no_execution_flags", flags_ok, f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}; no_strategy_promotion={manifest.get('no_strategy_promotion')}")


def _validate_command(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "value", "status", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "command_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    fields = set(frame["field"].astype(str).tolist())
    required_fields = {"command_id", "command_type", "module", "arguments", "max_execution_count", "allowed_providers", "forbidden_flags"}
    missing_fields = sorted(required_fields - fields)
    max_execution = frame[frame["field"].astype(str).eq("max_execution_count")]
    max_one = len(max_execution) == 1 and str(max_execution.iloc[0]["value"]) == "1"
    forbidden = frame[frame["field"].astype(str).eq("forbidden_flags")]
    forbidden_ok = len(forbidden) == 1 and all(flag in str(forbidden.iloc[0]["value"]) for flag in ["--all-symbols", "--sweep", "--promote", "--paper", "--live"])
    placeholder_blocks = frame["value"].astype(str).str.contains("<future_output_dir>", regex=False).any()
    _add_check(checks, "command_required_fields", not missing_fields, f"missing={missing_fields}")
    _add_check(checks, "command_max_execution_one", max_one, f"max_execution_rows={len(max_execution)}")
    _add_check(checks, "command_forbidden_flags_declared", forbidden_ok, f"forbidden_rows={len(forbidden)}")
    _add_check(checks, "command_output_placeholder_present", bool(placeholder_blocks), f"placeholder_present={bool(placeholder_blocks)}")


def _validate_outputs(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"artifact_name", "required", "format", "schema_status", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "outputs_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    artifacts = set(frame["artifact_name"].astype(str).tolist())
    missing_artifacts = sorted(REQUIRED_OUTPUT_ARTIFACTS - artifacts)
    all_required = frame["required"].astype(str).str.lower().eq("yes").all()
    schema_defined = frame["schema_status"].astype(str).str.lower().eq("defined").all()
    _add_check(checks, "outputs_required_artifacts", not missing_artifacts, f"missing={missing_artifacts}")
    _add_check(checks, "outputs_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "outputs_schema_defined", bool(schema_defined), f"schema_defined={bool(schema_defined)}")


def _validate_run_manifest(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "required", "allowed_values_or_format", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "run_manifest_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    fields = set(frame["field"].astype(str).tolist())
    missing_fields = sorted(REQUIRED_RUN_MANIFEST_FIELDS - fields)
    all_required = frame["required"].astype(str).str.lower().eq("yes").all()
    raw_field = frame[frame["field"].astype(str).eq("raw_payload_retained")]
    promotion_field = frame[frame["field"].astype(str).eq("strategy_promotion")]
    raw_false = len(raw_field) == 1 and str(raw_field.iloc[0]["allowed_values_or_format"]).lower() == "false"
    promotion_false = len(promotion_field) == 1 and str(promotion_field.iloc[0]["allowed_values_or_format"]).lower() == "false"
    _add_check(checks, "run_manifest_required_fields", not missing_fields, f"missing={missing_fields}")
    _add_check(checks, "run_manifest_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "run_manifest_no_raw_payload", raw_false, f"raw_rows={len(raw_field)}")
    _add_check(checks, "run_manifest_no_strategy_promotion", promotion_false, f"promotion_rows={len(promotion_field)}")


def _validate_ledger(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "required", "current_planned_value", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "ledger_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    fields = set(frame["field"].astype(str).tolist())
    required_fields = {"trial_id", "preregistration_id", "trial_consumed", "trial_budget_remaining_after_run", "result_status", "notes"}
    missing_fields = sorted(required_fields - fields)
    trial_consumed = frame[frame["field"].astype(str).eq("trial_consumed")]
    consumed_false = len(trial_consumed) == 1 and "false" in str(trial_consumed.iloc[0]["current_planned_value"]).lower()
    result_status = frame[frame["field"].astype(str).eq("result_status")]
    not_run = len(result_status) == 1 and str(result_status.iloc[0]["current_planned_value"]).lower() == "not_run"
    _add_check(checks, "ledger_required_fields", not missing_fields, f"missing={missing_fields}")
    _add_check(checks, "ledger_trial_not_consumed_in_spec", consumed_false, f"trial_consumed_rows={len(trial_consumed)}")
    _add_check(checks, "ledger_result_not_run", not_run, f"result_status_rows={len(result_status)}")


def _validate_blockers(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"blocker", "current_status", "failure_action"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "blockers_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    blockers = set(frame["blocker"].astype(str).tolist())
    missing_blockers = sorted(REQUIRED_BLOCKERS - blockers)
    block_actions = frame["failure_action"].astype(str).str.lower().str.contains("block").all()
    _add_check(checks, "blockers_required_items", not missing_blockers, f"missing={missing_blockers}")
    _add_check(checks, "blockers_block_execution", bool(block_actions), f"block_actions={bool(block_actions)}")


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
