from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "dry_run_preflight_manifest.json",
    "preflight_components.csv",
    "preflight_required_inputs.csv",
    "preflight_decision_matrix.csv",
    "preflight_blocker_register.csv",
    "dry_run_preflight_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "research_stage",
    "preflight_decision",
    "no_provider_query",
    "no_backtest",
    "no_strategy_promotion",
    "required_tables",
]

REQUIRED_COMPONENTS = {
    "research_run_gate",
    "preregistered_research_plan",
    "execution_authorization",
    "execution_command_output_schema",
    "governance_calibration",
    "manual_preflight_inputs",
}

REQUIRED_INPUTS = {
    "explicit_user_execution_approval",
    "final_execution_module",
    "final_output_directory",
    "trial_ledger_entry",
    "provider_credentials_check",
    "command_dry_review",
}


def validate_dry_run_preflight(artifact_dir: str | Path) -> dict[str, Any]:
    path = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    component_reports: list[dict[str, Any]] = []
    _add_check(checks, "artifact_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks, component_reports, "fail")

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "dry_run_preflight_manifest.json", checks, "manifest_json")
    research_stage = "new_signal_research"
    if isinstance(manifest, dict):
        research_stage = str(manifest.get("research_stage", research_stage))
        _validate_manifest(manifest, checks)

    components = _read_csv(path / "preflight_components.csv", checks, "csv_readable:preflight_components.csv")
    inputs = _read_csv(path / "preflight_required_inputs.csv", checks, "csv_readable:preflight_required_inputs.csv")
    decisions = _read_csv(path / "preflight_decision_matrix.csv", checks, "csv_readable:preflight_decision_matrix.csv")
    blockers = _read_csv(path / "preflight_blocker_register.csv", checks, "csv_readable:preflight_blocker_register.csv")
    _read_text_file(path / "dry_run_preflight_summary.md", checks, "markdown_readable:dry_run_preflight_summary.md")

    if components is not None:
        _validate_components_table(components, checks)
        _run_component_validators(components, checks, component_reports, research_stage)
    unresolved_inputs = False
    if inputs is not None:
        unresolved_inputs = _validate_inputs(inputs, checks)
    if decisions is not None:
        _validate_decisions(decisions, checks)
    if blockers is not None:
        _validate_blockers(blockers, checks)

    failed = any(check["status"] == "fail" for check in checks)
    preflight_status = "fail" if failed else "blocked" if unresolved_inputs else "pass"
    _add_check(checks, "preflight_expected_blocked_until_manual_inputs", preflight_status == "blocked", f"preflight_status={preflight_status}")
    return _report(path, checks, component_reports, preflight_status)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_dry_run_preflight(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] in {"pass", "blocked"} else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate dry-run preflight artifact.")
    parser.add_argument("--artifact-dir", required=True, help="Dry-run preflight artifact directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    tables_ok = isinstance(manifest.get("required_tables"), list) and bool(manifest.get("required_tables"))
    spec_only_ok = manifest.get("status") == "SPEC_ONLY_NOT_EXECUTED" and manifest.get("preflight_decision") in {
        "blocked_until_manual_execution_inputs_resolved",
        "blocked_until_explicit_execution_approval_and_implementation",
    }
    stage_ok = manifest.get("research_stage") == "new_signal_research"
    flags_ok = manifest.get("no_provider_query") is True and manifest.get("no_backtest") is True and manifest.get("no_strategy_promotion") is True
    _add_check(checks, "manifest_required_fields", not missing and tables_ok, f"missing={missing}; required_tables_ok={tables_ok}")
    _add_check(checks, "manifest_spec_only_blocked", spec_only_ok, f"status={manifest.get('status')}; preflight_decision={manifest.get('preflight_decision')}")
    _add_check(checks, "manifest_stage_new_signal_research", stage_ok, f"research_stage={manifest.get('research_stage')}")
    _add_check(checks, "manifest_no_execution_flags", flags_ok, f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}; no_strategy_promotion={manifest.get('no_strategy_promotion')}")


def _validate_components_table(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"component_type", "artifact_dir", "validator_module", "validator_function", "required_status", "current_expected_status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "components_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    components = set(frame["component_type"].astype(str).tolist())
    missing_components = sorted(REQUIRED_COMPONENTS - components)
    required_pass = frame["required_status"].astype(str).str.lower().eq("pass").all()
    _add_check(checks, "components_required_items", not missing_components, f"missing={missing_components}")
    _add_check(checks, "components_all_require_pass", bool(required_pass), f"required_pass={bool(required_pass)}")


def _run_component_validators(frame: pd.DataFrame, checks: list[dict[str, str]], component_reports: list[dict[str, Any]], research_stage: str) -> None:
    if not {"component_type", "artifact_dir", "validator_module", "validator_function"}.issubset(frame.columns):
        return
    root = Path.cwd()
    for _, row in frame.iterrows():
        component_type = str(row["component_type"])
        module_name = str(row["validator_module"])
        function_name = str(row["validator_function"])
        artifact_dir = root / str(row["artifact_dir"])
        try:
            module = importlib.import_module(module_name)
            validator = getattr(module, function_name)
        except Exception as exc:
            _add_check(checks, f"component_validator_load:{component_type}", False, f"{module_name}.{function_name}: {exc}")
            continue
        try:
            if component_type == "research_run_gate":
                report = validator(artifact_dir, research_stage)
            else:
                report = validator(artifact_dir)
        except Exception as exc:
            _add_check(checks, f"component_validator_run:{component_type}", False, f"{artifact_dir}: {exc}")
            continue
        status = report.get("status") if isinstance(report, dict) else None
        summary = report.get("summary", {}) if isinstance(report, dict) else {}
        component_reports.append({"component_type": component_type, "artifact_dir": str(artifact_dir), "status": status, "summary": summary})
        _add_check(checks, f"component_validator_pass:{component_type}", status == "pass", f"status={status}; artifact_dir={artifact_dir}")


def _validate_inputs(frame: pd.DataFrame, checks: list[dict[str, str]]) -> bool:
    required_columns = {"input_name", "required", "current_status", "blocks_execution", "resolution_required"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "inputs_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return False
    inputs = set(frame["input_name"].astype(str).tolist())
    missing_inputs = sorted(REQUIRED_INPUTS - inputs)
    all_required = frame["required"].astype(str).str.lower().eq("yes").all()
    unresolved_statuses = {
        "missing",
        "not_final",
        "placeholder",
        "not_checked",
        "not_reviewed",
        "not_granted",
        "specified_not_implemented",
        "specified_not_created",
        "planned_not_created",
        "policy_defined_not_checked",
        "reviewed_template_only",
        "dry_only_implemented",
        "reviewed_dry_only",
        "real_runner_gated",
        "reviewed_gated_real_runner",
    }
    unresolved = frame["current_status"].astype(str).str.lower().isin(unresolved_statuses)
    unresolved_block = frame.loc[unresolved, "blocks_execution"].astype(str).str.lower().eq("yes").all()
    _add_check(checks, "inputs_required_items", not missing_inputs, f"missing={missing_inputs}")
    _add_check(checks, "inputs_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "inputs_unresolved_block_execution", bool(unresolved.any() and unresolved_block), f"unresolved_count={int(unresolved.sum())}; unresolved_block={bool(unresolved_block)}")
    return bool(unresolved.any())


def _validate_decisions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"preflight_result", "condition", "allowed_action", "blocked_action"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "decisions_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    results = set(frame["preflight_result"].astype(str).tolist())
    required_results = {"pass", "blocked", "fail", "not_alpha_evidence"}
    blocked_rows = frame[frame["preflight_result"].astype(str).eq("blocked")]
    blocked_blocks_execution = len(blocked_rows) == 1 and "execution" in str(blocked_rows.iloc[0]["blocked_action"]).lower()
    _add_check(checks, "decisions_required_results", not sorted(required_results - results), f"missing={sorted(required_results - results)}")
    _add_check(checks, "decisions_blocked_blocks_execution", blocked_blocks_execution, f"blocked_rows={len(blocked_rows)}")


def _validate_blockers(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"blocker", "severity", "current_status", "required_response"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "blockers_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    critical_present = frame[frame["severity"].astype(str).str.lower().eq("critical")]
    present_blockers = frame["current_status"].astype(str).str.lower().eq("present").any()
    responses_present = frame["required_response"].astype(str).str.strip().ne("").all()
    _add_check(checks, "blockers_critical_present", len(critical_present) >= 4, f"critical_count={len(critical_present)}")
    _add_check(checks, "blockers_currently_present", bool(present_blockers), f"present_blockers={bool(present_blockers)}")
    _add_check(checks, "blockers_responses_present", bool(responses_present), f"responses_present={bool(responses_present)}")


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


def _report(path: Path, checks: list[dict[str, str]], component_reports: list[dict[str, Any]], preflight_status: str) -> dict[str, Any]:
    failed = [check for check in checks if check["status"] == "fail"]
    status = "fail" if failed else preflight_status
    return {
        "artifact_dir": str(path),
        "status": status,
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "component_reports": component_reports,
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
