from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "governance_calibration_manifest.json",
    "constraint_taxonomy.csv",
    "falsifiability_checks.csv",
    "allowed_research_flexibility.csv",
    "overconstraint_red_flags.csv",
    "calibration_decision_policy.csv",
    "governance_calibration_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "purpose",
    "no_provider_query",
    "no_backtest",
    "no_strategy_promotion",
    "required_tables",
]

REQUIRED_FALSIFIABILITY_CHECKS = {"FAL-001", "FAL-002", "FAL-003", "FAL-004", "FAL-005"}
REQUIRED_DECISIONS = {"calibrated", "overconstrained", "needs_review", "not_alpha_evidence"}
CRITICAL_RED_FLAGS = {"no_execution_path_even_with_approval", "validators_require_positive_return", "trial_budget_zero"}


def validate_governance_calibration(artifact_dir: str | Path) -> dict[str, Any]:
    path = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "artifact_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "governance_calibration_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    taxonomy = _read_csv(path / "constraint_taxonomy.csv", checks, "csv_readable:constraint_taxonomy.csv")
    falsifiability = _read_csv(path / "falsifiability_checks.csv", checks, "csv_readable:falsifiability_checks.csv")
    flexibility = _read_csv(path / "allowed_research_flexibility.csv", checks, "csv_readable:allowed_research_flexibility.csv")
    red_flags = _read_csv(path / "overconstraint_red_flags.csv", checks, "csv_readable:overconstraint_red_flags.csv")
    decisions = _read_csv(path / "calibration_decision_policy.csv", checks, "csv_readable:calibration_decision_policy.csv")
    _read_text_file(path / "governance_calibration_summary.md", checks, "markdown_readable:governance_calibration_summary.md")

    if taxonomy is not None:
        _validate_taxonomy(taxonomy, checks)
    if falsifiability is not None:
        _validate_falsifiability(falsifiability, checks)
    if flexibility is not None:
        _validate_flexibility(flexibility, checks)
    if red_flags is not None:
        _validate_red_flags(red_flags, checks)
    if decisions is not None:
        _validate_decisions(decisions, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_governance_calibration(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate governance calibration and falsifiability artifact.")
    parser.add_argument("--artifact-dir", required=True, help="Governance calibration artifact directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    tables_ok = isinstance(manifest.get("required_tables"), list) and bool(manifest.get("required_tables"))
    spec_only_ok = manifest.get("status") == "SPEC_ONLY_NOT_EXECUTED"
    flags_ok = manifest.get("no_provider_query") is True and manifest.get("no_backtest") is True and manifest.get("no_strategy_promotion") is True
    _add_check(checks, "manifest_required_fields", not missing and tables_ok, f"missing={missing}; required_tables_ok={tables_ok}")
    _add_check(checks, "manifest_spec_only", spec_only_ok, f"status={manifest.get('status')}")
    _add_check(checks, "manifest_no_execution_flags", flags_ok, f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}; no_strategy_promotion={manifest.get('no_strategy_promotion')}")


def _validate_taxonomy(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"constraint", "constraint_type", "may_block_execution", "may_block_positive_result", "rationale"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "taxonomy_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    types = set(frame["constraint_type"].astype(str).tolist())
    has_governance = any(value.startswith("hard_") for value in types)
    has_research_design = "research_design" in types
    hard_rows = frame[frame["constraint_type"].astype(str).str.startswith("hard_")]
    hard_not_performance_block = hard_rows["may_block_positive_result"].astype(str).str.lower().eq("no").all()
    design_rows = frame[frame["constraint_type"].astype(str).eq("research_design")]
    design_may_affect_result = design_rows["may_block_positive_result"].astype(str).str.lower().eq("yes").any()
    _add_check(checks, "taxonomy_has_hard_and_design_constraints", has_governance and has_research_design, f"types={sorted(types)}")
    _add_check(checks, "taxonomy_hard_constraints_not_performance_requirements", bool(hard_not_performance_block), f"hard_not_performance_block={bool(hard_not_performance_block)}")
    _add_check(checks, "taxonomy_design_choices_can_affect_results", bool(design_may_affect_result), f"design_may_affect_result={bool(design_may_affect_result)}")


def _validate_falsifiability(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"check_id", "check", "required", "pass_condition", "interpretation"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "falsifiability_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    check_ids = set(frame["check_id"].astype(str).tolist())
    missing_checks = sorted(REQUIRED_FALSIFIABILITY_CHECKS - check_ids)
    all_required = frame["required"].astype(str).str.lower().eq("yes").all()
    positive_negative = frame["check"].astype(str).str.contains("Positive and negative empirical outcomes", case=False, regex=False).any()
    no_performance_in_validators = frame["check"].astype(str).str.contains("Performance thresholds are not embedded", case=False, regex=False).any()
    _add_check(checks, "falsifiability_required_checks", not missing_checks, f"missing={missing_checks}")
    _add_check(checks, "falsifiability_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "falsifiability_positive_and_negative_outcomes", bool(positive_negative), f"positive_negative={bool(positive_negative)}")
    _add_check(checks, "falsifiability_no_performance_threshold_validators", bool(no_performance_in_validators), f"no_performance_in_validators={bool(no_performance_in_validators)}")


def _validate_flexibility(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"flexibility_item", "allowed", "mechanism", "guardrail"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "flexibility_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    allowed_all = frame["allowed"].astype(str).str.lower().eq("yes").all()
    mechanisms = " ".join(frame["mechanism"].astype(str).tolist()).lower()
    preregistration_path = "new preregistration" in mechanisms
    _add_check(checks, "flexibility_items_allowed", bool(allowed_all), f"allowed_all={bool(allowed_all)}")
    _add_check(checks, "flexibility_new_preregistration_path_exists", preregistration_path, f"preregistration_path={preregistration_path}")


def _validate_red_flags(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"red_flag", "severity", "meaning", "required_response"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "red_flags_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    flags = set(frame["red_flag"].astype(str).tolist())
    missing_critical = sorted(CRITICAL_RED_FLAGS - flags)
    critical_rows = frame[frame["red_flag"].astype(str).isin(CRITICAL_RED_FLAGS)]
    critical_marked = critical_rows["severity"].astype(str).str.lower().eq("critical").all()
    responses_present = frame["required_response"].astype(str).str.strip().ne("").all()
    _add_check(checks, "red_flags_critical_items_present", not missing_critical, f"missing={missing_critical}")
    _add_check(checks, "red_flags_critical_marked_critical", bool(critical_marked), f"critical_marked={bool(critical_marked)}")
    _add_check(checks, "red_flags_responses_present", bool(responses_present), f"responses_present={bool(responses_present)}")


def _validate_decisions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"decision", "condition", "action"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "decisions_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    decisions = set(frame["decision"].astype(str).tolist())
    missing_decisions = sorted(REQUIRED_DECISIONS - decisions)
    overconstrained = frame[frame["decision"].astype(str).eq("overconstrained")]
    revise_on_overconstraint = len(overconstrained) == 1 and "revise" in str(overconstrained.iloc[0]["action"]).lower()
    not_alpha = frame[frame["decision"].astype(str).eq("not_alpha_evidence")]
    no_alpha_claim = len(not_alpha) == 1 and "do not claim performance" in str(not_alpha.iloc[0]["action"]).lower()
    _add_check(checks, "decisions_required_items", not missing_decisions, f"missing={missing_decisions}")
    _add_check(checks, "decisions_revise_if_overconstrained", revise_on_overconstraint, f"overconstrained_rows={len(overconstrained)}")
    _add_check(checks, "decisions_governance_not_alpha_evidence", no_alpha_claim, f"not_alpha_rows={len(not_alpha)}")


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
