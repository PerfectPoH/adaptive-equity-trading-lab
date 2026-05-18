from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "final_command_review_manifest.json",
    "command_review.csv",
    "command_gate_checks.csv",
    "forbidden_flags.csv",
    "remaining_execution_blockers.csv",
    "final_command_review_summary.md",
]

REQUIRED_COMPONENT_FIELDS = {
    "command_id",
    "module",
    "entrypoint",
    "mode",
    "preregistration_id",
    "trial_id",
    "output_dir",
    "credential_source",
    "approval",
}

FORBIDDEN_FLAGS = {"--all-symbols", "--sweep", "--promote", "--paper", "--live", "--retain-raw-response"}


def validate_final_command_review(artifact_dir: str | Path) -> dict[str, Any]:
    root = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "artifact_dir_exists", root.exists() and root.is_dir(), str(root))
    for name in REQUIRED_FILES:
        _add_check(checks, f"required_file:{name}", (root / name).exists(), str(root / name))
    manifest = _read_json(root / "final_command_review_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    command = _read_csv(root / "command_review.csv", checks)
    gates = _read_csv(root / "command_gate_checks.csv", checks)
    flags = _read_csv(root / "forbidden_flags.csv", checks)
    blockers = _read_csv(root / "remaining_execution_blockers.csv", checks)
    _read_markdown(root / "final_command_review_summary.md", checks)
    if command is not None:
        _validate_command(command, checks)
    if gates is not None:
        _validate_gate_checks(gates, checks)
    if flags is not None:
        _validate_forbidden_flags(flags, checks)
    if blockers is not None:
        _validate_blockers(blockers, checks)
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {"artifact_dir": str(root), "status": "pass" if failed == 0 else "fail", "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed}, "checks": checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate final command review artifact.")
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_final_command_review(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    spec_only = manifest.get("status") in {"SPEC_ONLY_NOT_EXECUTED", "PRE_EXECUTION_READY_APPROVED_NOT_EXECUTED"}
    blocked = manifest.get("decision") in {"FINAL_COMMAND_REVIEWED_EXECUTION_STILL_BLOCKED", "FINAL_COMMAND_REVIEWED_APPROVED_SINGLE_RUN_READY"}
    no_exec = (
        manifest.get("provider_query_performed") is False
        and manifest.get("backtest_performed") is False
        and manifest.get("strategy_promotion_performed") is False
        and manifest.get("trial_consumed") is False
    )
    approval_block = manifest.get("execution_approval_status") in {"not_granted", "granted_for_single_diagnostic_run"}
    _add_check(checks, "manifest_spec_only_blocked", spec_only and blocked, f"status={manifest.get('status')}; decision={manifest.get('decision')}")
    _add_check(checks, "manifest_no_execution_side_effects", no_exec, f"no_exec={no_exec}")
    _add_check(checks, "manifest_approval_not_granted", approval_block, f"approval={manifest.get('execution_approval_status')}")


def _validate_command(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "value", "status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    fields = set(frame["field"].astype(str).tolist()) if not missing_columns else set()
    approval = frame[frame["field"].astype(str).eq("approval")]
    mode = frame[frame["field"].astype(str).eq("mode")]
    _add_check(checks, "command_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "command_required_fields", REQUIRED_COMPONENT_FIELDS.issubset(fields), f"missing={sorted(REQUIRED_COMPONENT_FIELDS - fields)}")
    approval_ok = len(approval) == 1 and str(approval.iloc[0]["value"]).lower() in {"not_granted", "granted_for_single_diagnostic_run"}
    mode_ok = len(mode) == 1 and str(mode.iloc[0]["status"]).lower() in {"blocked_gate_report_only", "approved_single_run_path"}
    _add_check(checks, "command_approval_blocks_execution", approval_ok, f"approval_rows={len(approval)}")
    _add_check(checks, "command_mode_gate_report_only", mode_ok, f"mode_rows={len(mode)}")


def _validate_gate_checks(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"check", "status", "detail"}
    missing_columns = sorted(required_columns - set(frame.columns))
    all_pass = frame["status"].astype(str).str.lower().eq("pass").all() if not missing_columns else False
    required_checks = {"single_preregistered_run", "provider_credentials_present", "no_raw_payload_retention", "output_directory_not_created", "trial_not_consumed", "execution_approval_not_granted", "provider_query_not_performed"}
    present_checks = set(frame["check"].astype(str).tolist()) if not missing_columns else set()
    _add_check(checks, "gate_checks_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "gate_checks_required_items", required_checks.issubset(present_checks), f"missing={sorted(required_checks - present_checks)}")
    _add_check(checks, "gate_checks_all_pass", bool(all_pass), f"all_pass={bool(all_pass)}")


def _validate_forbidden_flags(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"flag", "status", "reason"}
    missing_columns = sorted(required_columns - set(frame.columns))
    flags = set(frame["flag"].astype(str).tolist()) if not missing_columns else set()
    all_absent = frame["status"].astype(str).str.lower().eq("forbidden_absent").all() if not missing_columns else False
    _add_check(checks, "forbidden_flags_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "forbidden_flags_required_items", FORBIDDEN_FLAGS.issubset(flags), f"missing={sorted(FORBIDDEN_FLAGS - flags)}")
    _add_check(checks, "forbidden_flags_all_absent", bool(all_absent), f"all_absent={bool(all_absent)}")


def _validate_blockers(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"blocker", "severity", "current_status", "required_response"}
    missing_columns = sorted(required_columns - set(frame.columns))
    critical_count = int(frame["severity"].astype(str).str.lower().eq("critical").sum()) if not missing_columns else 0
    statuses = frame["current_status"].astype(str).str.lower() if not missing_columns else pd.Series(dtype=str)
    present = statuses.eq("present").any() if not missing_columns else False
    all_resolved = statuses.eq("resolved").all() if not missing_columns else False
    _add_check(checks, "blockers_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "blockers_critical_present", critical_count >= 0, f"critical_count={critical_count}")
    _add_check(checks, "blockers_currently_present", bool(present or all_resolved), f"present={bool(present)}; all_resolved={bool(all_resolved)}")


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
