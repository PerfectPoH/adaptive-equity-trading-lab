from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any, Callable

import pandas as pd

REQUIRED_FILES = [
    "research_run_gate_manifest.json",
    "research_run_gate_components.csv",
    "research_stage_gate_matrix.csv",
    "gate_decision_policy.csv",
    "research_run_gate_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "purpose",
    "no_provider_query",
    "no_backtest",
    "no_strategy_promotion",
    "required_components",
    "default_gate_decision",
]

REQUIRED_COMPONENT_TYPES = [
    "provider_coverage_contract",
    "adjustment_tradability_policy",
    "trial_accounting_preregistration",
]

REQUIRED_RESEARCH_STAGES = [
    "data_quality_diagnostic",
    "fixed_signal_replay",
    "new_signal_research",
    "portfolio_backtest",
    "OOS",
    "paper_live",
]

VALIDATOR_FUNCTIONS = {
    "src.experiments.provider_coverage_contract_validator": "validate_provider_coverage_contract",
    "src.experiments.adjustment_tradability_policy_validator": "validate_adjustment_tradability_policy",
    "src.experiments.trial_accounting_preregistration_validator": "validate_trial_accounting_preregistration",
}


def validate_research_run_gate(gate_dir: str | Path, research_stage: str) -> dict[str, Any]:
    gate_path = Path(gate_dir)
    repo_root = Path.cwd()
    checks: list[dict[str, str]] = []
    component_reports: list[dict[str, Any]] = []
    _add_check(checks, "gate_dir_exists", gate_path.exists() and gate_path.is_dir(), str(gate_path))
    if not gate_path.exists() or not gate_path.is_dir():
        return _report(gate_path, research_stage, checks, component_reports)

    for filename in REQUIRED_FILES:
        file_path = gate_path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(gate_path / "research_run_gate_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    components = _read_csv(gate_path / "research_run_gate_components.csv", checks, "csv_readable:research_run_gate_components.csv")
    matrix = _read_csv(gate_path / "research_stage_gate_matrix.csv", checks, "csv_readable:research_stage_gate_matrix.csv")
    decision_policy = _read_csv(gate_path / "gate_decision_policy.csv", checks, "csv_readable:gate_decision_policy.csv")
    _read_text_file(gate_path / "research_run_gate_summary.md", checks, "markdown_readable:research_run_gate_summary.md")

    required_component_types: list[str] = []
    if matrix is not None:
        required_component_types = _validate_matrix(matrix, research_stage, checks)
    if decision_policy is not None:
        _validate_decision_policy(decision_policy, checks)
    if components is not None:
        _validate_components_table(components, checks)
        component_reports = _run_component_validators(components, required_component_types, repo_root, checks)

    return _report(gate_path, research_stage, checks, component_reports)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_research_run_gate(args.gate_dir, args.research_stage)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the aggregate research run gate.")
    parser.add_argument("--gate-dir", required=True, help="Research run gate spec directory to validate.")
    parser.add_argument("--research-stage", required=True, choices=REQUIRED_RESEARCH_STAGES, help="Requested research stage.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    components = manifest.get("required_components")
    components_ok = isinstance(components, list) and all(component in components for component in REQUIRED_COMPONENT_TYPES)
    no_provider_query_ok = manifest.get("no_provider_query") is True
    no_backtest_ok = manifest.get("no_backtest") is True
    no_strategy_promotion_ok = manifest.get("no_strategy_promotion") is True
    default_block_ok = manifest.get("default_gate_decision") == "BLOCK_UNLESS_ALL_REQUIRED_COMPONENTS_PASS"
    _add_check(checks, "manifest_required_fields", not missing and components_ok and default_block_ok, f"missing={missing}; components_ok={components_ok}; default_block_ok={default_block_ok}")
    _add_check(
        checks,
        "manifest_no_execution_flags",
        no_provider_query_ok and no_backtest_ok and no_strategy_promotion_ok,
        f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}; no_strategy_promotion={manifest.get('no_strategy_promotion')}",
    )


def _validate_components_table(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"component_id", "component_type", "artifact_dir", "validator_module", "minimum_status", "required_for_run", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "components_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    component_types = {str(value) for value in frame["component_type"].dropna().tolist()}
    missing_types = [component for component in REQUIRED_COMPONENT_TYPES if component not in component_types]
    all_required = frame["required_for_run"].astype(str).str.lower().eq("yes").all()
    all_min_pass = frame["minimum_status"].astype(str).str.lower().eq("pass").all()
    _add_check(checks, "components_required_types", not missing_types, f"missing={missing_types}")
    _add_check(checks, "components_all_required_for_run", bool(all_required), f"all_required_for_run={bool(all_required)}")
    _add_check(checks, "components_minimum_status_pass", bool(all_min_pass), f"all_minimum_status_pass={bool(all_min_pass)}")


def _validate_matrix(frame: pd.DataFrame, research_stage: str, checks: list[dict[str, str]]) -> list[str]:
    required_columns = {"research_stage", "gate_required", "required_components", "allowed_if_gate_passes", "blocked_if_gate_fails"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "matrix_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return []
    stages = {str(value) for value in frame["research_stage"].dropna().tolist()}
    missing_stages = [stage for stage in REQUIRED_RESEARCH_STAGES if stage not in stages]
    stage_rows = frame[frame["research_stage"].astype(str).eq(research_stage)]
    stage_present = len(stage_rows) == 1
    all_gate_required = frame["gate_required"].astype(str).str.lower().eq("yes").all()
    _add_check(checks, "matrix_required_stages", not missing_stages, f"missing={missing_stages}")
    _add_check(checks, "matrix_requested_stage_present", stage_present, f"research_stage={research_stage}; rows={len(stage_rows)}")
    _add_check(checks, "matrix_all_stages_gate_required", bool(all_gate_required), f"all_gate_required={bool(all_gate_required)}")
    if not stage_present:
        return []
    raw_components = str(stage_rows.iloc[0]["required_components"])
    required_components = [component.strip() for component in raw_components.split(";") if component.strip()]
    known_components = all(component in REQUIRED_COMPONENT_TYPES for component in required_components)
    _add_check(checks, "matrix_requested_stage_components_known", known_components, f"required_components={required_components}")
    return required_components if known_components else []


def _validate_decision_policy(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"gate_result", "meaning", "allowed_action", "blocked_action"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "decision_policy_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    results = {str(value) for value in frame["gate_result"].dropna().tolist()}
    required_results = {"pass", "fail", "not_applicable"}
    missing_results = sorted(required_results - results)
    _add_check(checks, "decision_policy_required_results", not missing_results, f"missing={missing_results}")


def _run_component_validators(frame: pd.DataFrame, required_component_types: list[str], repo_root: Path, checks: list[dict[str, str]]) -> list[dict[str, Any]]:
    if not required_component_types:
        _add_check(checks, "component_validators_requested_components_present", False, "no required components for requested stage")
        return []
    reports: list[dict[str, Any]] = []
    required_rows = frame[frame["component_type"].astype(str).isin(required_component_types)]
    missing_rows = sorted(set(required_component_types) - set(required_rows["component_type"].astype(str).tolist()))
    _add_check(checks, "component_validators_rows_present", not missing_rows, f"missing={missing_rows}")
    for _, row in required_rows.iterrows():
        component_type = str(row["component_type"])
        validator_module = str(row["validator_module"])
        artifact_dir = repo_root / str(row["artifact_dir"])
        validator = _load_validator(validator_module)
        if validator is None:
            _add_check(checks, f"component_validator_load:{component_type}", False, validator_module)
            reports.append({"component_type": component_type, "status": "fail", "detail": f"could not load {validator_module}"})
            continue
        _add_check(checks, f"component_validator_load:{component_type}", True, validator_module)
        report = validator(artifact_dir)
        status = str(report.get("status", "fail"))
        _add_check(checks, f"component_validator_pass:{component_type}", status == "pass", f"status={status}; artifact_dir={artifact_dir}")
        reports.append({"component_type": component_type, "artifact_dir": str(artifact_dir), "status": status, "summary": report.get("summary", {})})
    return reports


def _load_validator(module_name: str) -> Callable[[Path], dict[str, Any]] | None:
    function_name = VALIDATOR_FUNCTIONS.get(module_name)
    if function_name is None:
        return None
    module = importlib.import_module(module_name)
    validator = getattr(module, function_name, None)
    if not callable(validator):
        return None
    return validator


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


def _report(gate_path: Path, research_stage: str, checks: list[dict[str, str]], component_reports: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "gate_dir": str(gate_path),
        "research_stage": research_stage,
        "status": "pass" if not failed else "fail",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
        "component_reports": component_reports,
    }


if __name__ == "__main__":
    raise SystemExit(main())
