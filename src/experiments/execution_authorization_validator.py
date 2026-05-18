from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "execution_authorization_manifest.json",
    "authorization_conditions.csv",
    "allowed_execution_scope.csv",
    "blocked_actions.csv",
    "pre_execution_evidence_checklist.csv",
    "post_execution_artifact_requirements.csv",
    "execution_authorization_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "authorization_status",
    "linked_preregistered_plan",
    "linked_research_run_gate",
    "research_stage",
    "no_provider_query",
    "no_backtest",
    "no_strategy_promotion",
    "execution_performed",
    "required_tables",
]

REQUIRED_BLOCKED_ACTIONS = {
    "ALL_SYMBOLS_query",
    "parameter_sweep",
    "strategy_promotion",
    "OOS_claim",
    "paper_or_live_trading",
    "raw_payload_retention",
}

REQUIRED_CONDITIONS = {
    "preregistered_plan_validator_pass",
    "research_run_gate_pass",
    "user_explicit_run_approval",
    "provider_credentials_available",
    "trial_budget_available",
    "raw_retention_policy_confirmed",
    "execution_command_dry_reviewed",
}


def validate_execution_authorization(artifact_dir: str | Path) -> dict[str, Any]:
    path = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "artifact_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "execution_authorization_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    conditions = _read_csv(path / "authorization_conditions.csv", checks, "csv_readable:authorization_conditions.csv")
    scope = _read_csv(path / "allowed_execution_scope.csv", checks, "csv_readable:allowed_execution_scope.csv")
    blocked = _read_csv(path / "blocked_actions.csv", checks, "csv_readable:blocked_actions.csv")
    evidence = _read_csv(path / "pre_execution_evidence_checklist.csv", checks, "csv_readable:pre_execution_evidence_checklist.csv")
    requirements = _read_csv(path / "post_execution_artifact_requirements.csv", checks, "csv_readable:post_execution_artifact_requirements.csv")
    _read_text_file(path / "execution_authorization_summary.md", checks, "markdown_readable:execution_authorization_summary.md")

    if conditions is not None:
        _validate_conditions(conditions, checks)
    if scope is not None:
        _validate_scope(scope, checks)
    if blocked is not None:
        _validate_blocked_actions(blocked, checks)
    if evidence is not None:
        _validate_evidence(evidence, checks)
    if requirements is not None:
        _validate_post_requirements(requirements, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_execution_authorization(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate explicit execution authorization artifact.")
    parser.add_argument("--artifact-dir", required=True, help="Execution authorization artifact directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    tables_ok = isinstance(manifest.get("required_tables"), list) and bool(manifest.get("required_tables"))
    status_ok = manifest.get("status") == "SPEC_ONLY_NOT_EXECUTED"
    authorization_status_ok = manifest.get("authorization_status") == "defined_not_granted"
    execution_ok = manifest.get("execution_performed") is False
    stage_ok = manifest.get("research_stage") == "new_signal_research"
    flags_ok = manifest.get("no_provider_query") is True and manifest.get("no_backtest") is True and manifest.get("no_strategy_promotion") is True
    _add_check(checks, "manifest_required_fields", not missing and tables_ok, f"missing={missing}; required_tables_ok={tables_ok}")
    _add_check(checks, "manifest_spec_only_not_executed", status_ok and authorization_status_ok and execution_ok, f"status={manifest.get('status')}; authorization_status={manifest.get('authorization_status')}; execution_performed={manifest.get('execution_performed')}")
    _add_check(checks, "manifest_stage_new_signal_research", stage_ok, f"research_stage={manifest.get('research_stage')}")
    _add_check(checks, "manifest_no_execution_flags", flags_ok, f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}; no_strategy_promotion={manifest.get('no_strategy_promotion')}")


def _validate_conditions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"condition", "required", "current_status", "failure_action"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "conditions_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    conditions = set(frame["condition"].astype(str).tolist())
    missing_conditions = sorted(REQUIRED_CONDITIONS - conditions)
    all_required = frame["required"].astype(str).str.lower().eq("yes").all()
    user_approval = frame[frame["condition"].astype(str).eq("user_explicit_run_approval")]
    user_not_granted = len(user_approval) == 1 and str(user_approval.iloc[0]["current_status"]).lower() == "not_granted"
    blocked_on_failure = frame["failure_action"].astype(str).str.lower().str.contains("block").all()
    _add_check(checks, "conditions_required_items", not missing_conditions, f"missing={missing_conditions}")
    _add_check(checks, "conditions_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "conditions_user_approval_not_granted", user_not_granted, f"user_approval_rows={len(user_approval)}")
    _add_check(checks, "conditions_block_on_failure", bool(blocked_on_failure), f"blocked_on_failure={bool(blocked_on_failure)}")


def _validate_scope(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"scope_item", "allowed", "limit", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "scope_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    execution_count = frame[frame["scope_item"].astype(str).eq("execution_count")]
    one_execution_only = len(execution_count) == 1 and str(execution_count.iloc[0]["limit"]) == "1"
    no_all_symbols = frame["limit"].astype(str).str.contains("No ALL_SYMBOLS query", case=False, regex=False).any() or frame["notes"].astype(str).str.contains("No ALL_SYMBOLS query", case=False, regex=False).any()
    _add_check(checks, "scope_one_execution_only", one_execution_only, f"execution_count_rows={len(execution_count)}")
    _add_check(checks, "scope_blocks_all_symbols", bool(no_all_symbols), f"no_all_symbols={bool(no_all_symbols)}")


def _validate_blocked_actions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"blocked_action", "severity", "reason"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "blocked_actions_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    actions = set(frame["blocked_action"].astype(str).tolist())
    missing_actions = sorted(REQUIRED_BLOCKED_ACTIONS - actions)
    all_critical = frame["severity"].astype(str).str.lower().eq("critical").all()
    _add_check(checks, "blocked_actions_required_items", not missing_actions, f"missing={missing_actions}")
    _add_check(checks, "blocked_actions_all_critical", bool(all_critical), f"all_critical={bool(all_critical)}")


def _validate_evidence(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"evidence_item", "required", "current_status", "source"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "evidence_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    required_all = frame["required"].astype(str).str.lower().eq("yes").all()
    explicit_user_missing = frame[frame["evidence_item"].astype(str).eq("explicit_user_approval")]
    explicit_missing_ok = len(explicit_user_missing) == 1 and str(explicit_user_missing.iloc[0]["current_status"]).lower() == "missing"
    _add_check(checks, "evidence_all_required", bool(required_all), f"required_all={bool(required_all)}")
    _add_check(checks, "evidence_explicit_user_approval_missing", explicit_missing_ok, f"explicit_user_rows={len(explicit_user_missing)}")


def _validate_post_requirements(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"artifact_requirement", "required", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "post_requirements_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    required_all = frame["required"].astype(str).str.lower().eq("yes").all()
    requirements = set(frame["artifact_requirement"].astype(str).tolist())
    required_items = {"execution_manifest", "trial_ledger_update", "derived_results_only", "provider_coverage_audit", "interpretation_report"}
    missing_items = sorted(required_items - requirements)
    _add_check(checks, "post_requirements_all_required", bool(required_all), f"required_all={bool(required_all)}")
    _add_check(checks, "post_requirements_required_items", not missing_items, f"missing={missing_items}")


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
