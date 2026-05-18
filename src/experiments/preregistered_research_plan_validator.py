from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "research_plan_manifest.json",
    "preregistered_research_plan.csv",
    "feature_freeze.csv",
    "parameter_freeze.csv",
    "sample_definition_policy.csv",
    "decision_rule.csv",
    "pre_run_checklist.csv",
    "research_plan_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "research_stage",
    "linked_gate_spec",
    "linked_provider_coverage_contract",
    "linked_adjustment_tradability_policy",
    "linked_trial_accounting_preregistration",
    "no_provider_query",
    "no_backtest",
    "no_strategy_promotion",
    "execution_status",
    "required_tables",
]

REQUIRED_PLAN_COLUMNS = [
    "preregistration_id",
    "research_question",
    "hypothesis",
    "research_stage",
    "provider_contract_id",
    "adjustment_tradability_policy_id",
    "trial_budget_id",
    "stop_go_threshold_id",
    "primary_metric",
    "secondary_metrics",
    "execution_status",
]

REQUIRED_PRE_RUN_CHECKS = [
    "research_run_gate_passed",
    "primary_metric_finalized",
    "feature_list_finalized",
    "parameters_finalized",
    "sample_definition_finalized",
    "trial_ledger_ready",
    "raw_retention_policy_confirmed",
]

BLOCKED_FINAL_VALUES = {
    "",
    "unknown",
    "tbd",
    "todo",
    "to_be_declared_before_execution",
    "single_value_required_before_execution",
}


def validate_preregistered_research_plan(plan_dir: str | Path) -> dict[str, Any]:
    path = Path(plan_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "plan_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "research_plan_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    plan = _read_csv(path / "preregistered_research_plan.csv", checks, "csv_readable:preregistered_research_plan.csv")
    features = _read_csv(path / "feature_freeze.csv", checks, "csv_readable:feature_freeze.csv")
    parameters = _read_csv(path / "parameter_freeze.csv", checks, "csv_readable:parameter_freeze.csv")
    sample = _read_csv(path / "sample_definition_policy.csv", checks, "csv_readable:sample_definition_policy.csv")
    decision = _read_csv(path / "decision_rule.csv", checks, "csv_readable:decision_rule.csv")
    checklist = _read_csv(path / "pre_run_checklist.csv", checks, "csv_readable:pre_run_checklist.csv")
    _read_text_file(path / "research_plan_summary.md", checks, "markdown_readable:research_plan_summary.md")

    if plan is not None:
        _validate_plan(plan, checks)
    if features is not None:
        _validate_features(features, checks)
    if parameters is not None:
        _validate_parameters(parameters, checks)
    if sample is not None:
        _validate_sample(sample, checks)
    if decision is not None:
        _validate_decision(decision, checks)
    if checklist is not None:
        _validate_checklist(checklist, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_preregistered_research_plan(args.plan_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate preregistered provider-aware research plan artifacts.")
    parser.add_argument("--plan-dir", required=True, help="Preregistered research plan directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    tables_ok = isinstance(manifest.get("required_tables"), list) and bool(manifest.get("required_tables"))
    execution_blocked_ok = manifest.get("status") == "PLAN_ONLY_NOT_EXECUTED" and manifest.get("execution_status") == "not_executed"
    pre_run_fields_status = manifest.get("pre_run_fields_status")
    pre_run_status_ok = pre_run_fields_status in {None, "finalized"}
    no_provider_query_ok = manifest.get("no_provider_query") is True
    no_backtest_ok = manifest.get("no_backtest") is True
    no_strategy_promotion_ok = manifest.get("no_strategy_promotion") is True
    stage_ok = manifest.get("research_stage") == "new_signal_research"
    _add_check(checks, "manifest_required_fields", not missing and tables_ok, f"missing={missing}; required_tables_ok={tables_ok}")
    _add_check(checks, "manifest_plan_not_executed", execution_blocked_ok, f"status={manifest.get('status')}; execution_status={manifest.get('execution_status')}")
    _add_check(checks, "manifest_pre_run_fields_status_allowed", pre_run_status_ok, f"pre_run_fields_status={pre_run_fields_status}")
    _add_check(checks, "manifest_stage_new_signal_research", stage_ok, f"research_stage={manifest.get('research_stage')}")
    _add_check(
        checks,
        "manifest_no_execution_flags",
        no_provider_query_ok and no_backtest_ok and no_strategy_promotion_ok,
        f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}; no_strategy_promotion={manifest.get('no_strategy_promotion')}",
    )


def _validate_plan(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    missing_columns = [column for column in REQUIRED_PLAN_COLUMNS if column not in frame.columns]
    _add_check(checks, "plan_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    _add_check(checks, "plan_single_row", len(frame) == 1, f"rows={len(frame)}")
    if frame.empty:
        return
    row = frame.iloc[0]
    execution_status_ok = str(row["execution_status"]).lower() == "not_executed"
    stage_ok = str(row["research_stage"]) == "new_signal_research"
    ids_present = all(bool(str(row[column]).strip()) for column in ["preregistration_id", "provider_contract_id", "adjustment_tradability_policy_id", "trial_budget_id", "stop_go_threshold_id"])
    primary_metric_final = str(row["primary_metric"]).strip().lower() not in BLOCKED_FINAL_VALUES
    _add_check(checks, "plan_execution_not_executed", execution_status_ok, f"execution_status={row['execution_status']}")
    _add_check(checks, "plan_stage_new_signal_research", stage_ok, f"research_stage={row['research_stage']}")
    _add_check(checks, "plan_required_ids_present", ids_present, "required ids populated")
    _add_check(checks, "plan_primary_metric_declared", primary_metric_final, f"primary_metric={row['primary_metric']}")


def _validate_features(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"feature_name", "status", "allowed_before_execution", "change_after_execution_policy", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "features_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    change_policy_ok = frame["change_after_execution_policy"].astype(str).str.lower().eq("new_preregistration_required").all()
    final_or_required = frame["status"].astype(str).str.lower().isin({"final", "required"}).all()
    _add_check(checks, "features_changes_require_new_preregistration", bool(change_policy_ok), f"change_policy_ok={bool(change_policy_ok)}")
    _add_check(checks, "features_final_or_required", bool(final_or_required), f"final_or_required={bool(final_or_required)}")


def _validate_parameters(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"parameter_name", "status", "allowed_values", "change_after_execution_policy", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "parameters_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    reset_blocked = frame["change_after_execution_policy"].astype(str).str.lower().isin({"new_preregistration_required", "no_reset_allowed"}).all()
    no_blocked_values = ~frame["allowed_values"].astype(str).str.lower().isin(BLOCKED_FINAL_VALUES)
    max_trials_rows = frame[frame["parameter_name"].astype(str).eq("max_trials")]
    max_trials_ok = len(max_trials_rows) == 1 and str(max_trials_rows.iloc[0]["allowed_values"]) == "3"
    _add_check(checks, "parameters_changes_blocked_or_preregistered", bool(reset_blocked), f"reset_blocked={bool(reset_blocked)}")
    _add_check(checks, "parameters_values_finalized", bool(no_blocked_values.all()), f"values_finalized={bool(no_blocked_values.all())}")
    _add_check(checks, "parameters_max_trials_fixed", max_trials_ok, f"max_trials_rows={len(max_trials_rows)}")


def _validate_sample(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"sample_element", "status", "policy", "blocked_until_resolved"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "sample_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    elements = {str(value) for value in frame["sample_element"].dropna().tolist()}
    required_elements = {"symbol_universe", "date_window", "provider_coverage", "PIT_claim", "raw_data_retention"}
    missing_elements = sorted(required_elements - elements)
    unresolved_blocks = frame[frame["status"].astype(str).str.lower().isin({"not_final", "blocked"})]
    unresolved_marked_blocked = unresolved_blocks["blocked_until_resolved"].astype(str).str.lower().eq("yes").all()
    _add_check(checks, "sample_required_elements", not missing_elements, f"missing={missing_elements}")
    _add_check(checks, "sample_unresolved_items_block_execution", bool(unresolved_marked_blocked), f"unresolved_marked_blocked={bool(unresolved_marked_blocked)}")


def _validate_decision(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"decision_item", "status", "rule"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "decision_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    items = {str(value) for value in frame["decision_item"].dropna().tolist()}
    required_items = {"gate_precondition", "primary_metric", "go_rule", "stop_rule", "promotion_rule"}
    missing_items = sorted(required_items - items)
    promotion_rows = frame[frame["decision_item"].astype(str).eq("promotion_rule")]
    promotion_blocked = len(promotion_rows) == 1 and str(promotion_rows.iloc[0]["status"]).lower() == "blocked"
    _add_check(checks, "decision_required_items", not missing_items, f"missing={missing_items}")
    _add_check(checks, "decision_promotion_blocked", promotion_blocked, f"promotion_rows={len(promotion_rows)}")


def _validate_checklist(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"check", "required", "current_status", "failure_action"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "checklist_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    checks_present = {str(value) for value in frame["check"].dropna().tolist()}
    missing_checks = [check for check in REQUIRED_PRE_RUN_CHECKS if check not in checks_present]
    all_required = frame["required"].astype(str).str.lower().eq("yes").all()
    unresolved_items = frame[frame["current_status"].astype(str).str.lower().isin({"not_run", "not_final", "template_only"})]
    unresolved_block = unresolved_items["failure_action"].astype(str).str.lower().str.contains("block").all()
    _add_check(checks, "checklist_required_checks", not missing_checks, f"missing={missing_checks}")
    _add_check(checks, "checklist_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "checklist_unresolved_items_block_execution", bool(unresolved_block), f"unresolved_block={bool(unresolved_block)}")


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
        "plan_dir": str(path),
        "status": "pass" if not failed else "fail",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
