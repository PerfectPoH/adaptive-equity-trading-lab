from __future__ import annotations

import json
from pathlib import Path

from src.experiments.preregistered_research_plan_validator import main, validate_preregistered_research_plan


def _valid_plan_dir(tmp_path: Path) -> Path:
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    manifest = {
        "status": "PLAN_ONLY_NOT_EXECUTED",
        "decision": "FIRST_PROVIDER_AWARE_RESEARCH_PLAN_PREREGISTERED_NOT_RUN",
        "scope": "Provider-aware small-cap research track",
        "research_stage": "new_signal_research",
        "linked_gate_spec": "gate",
        "linked_provider_coverage_contract": "pcc",
        "linked_adjustment_tradability_policy": "atp",
        "linked_trial_accounting_preregistration": "tap",
        "no_provider_query": True,
        "no_backtest": True,
        "no_strategy_promotion": True,
        "execution_status": "not_executed",
        "required_tables": ["preregistered_research_plan.csv"],
    }
    (plan_dir / "research_plan_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (plan_dir / "preregistered_research_plan.csv").write_text(
        "preregistration_id,research_question,hypothesis,research_stage,provider_contract_id,adjustment_tradability_policy_id,trial_budget_id,stop_go_threshold_id,primary_metric,secondary_metrics,execution_status\n"
        "PREREG,Q,H,new_signal_research,PCC,ATP,TB,TH,metric,secondary,not_executed\n",
        encoding="utf-8",
    )
    (plan_dir / "feature_freeze.csv").write_text(
        "feature_name,status,allowed_before_execution,change_after_execution_policy,notes\n"
        "provider_quality_flag,final,yes,new_preregistration_required,notes\n",
        encoding="utf-8",
    )
    (plan_dir / "parameter_freeze.csv").write_text(
        "parameter_name,status,allowed_values,change_after_execution_policy,notes\n"
        "event_window,final,next_session_open_to_close,new_preregistration_required,notes\n"
        "max_trials,fixed,3,no_reset_allowed,notes\n",
        encoding="utf-8",
    )
    (plan_dir / "sample_definition_policy.csv").write_text(
        "sample_element,status,policy,blocked_until_resolved\n"
        "symbol_universe,not_final,freeze,yes\n"
        "date_window,not_final,freeze,yes\n"
        "provider_coverage,linked,validate,no\n"
        "PIT_claim,blocked,no claim,yes\n"
        "raw_data_retention,derived_only,no raw,no\n",
        encoding="utf-8",
    )
    (plan_dir / "decision_rule.csv").write_text(
        "decision_item,status,rule\n"
        "gate_precondition,required,gate pass required\n"
        "primary_metric,not_final,metric required\n"
        "go_rule,not_final,go rule required\n"
        "stop_rule,required,stop on failure\n"
        "promotion_rule,blocked,no promotion\n",
        encoding="utf-8",
    )
    (plan_dir / "pre_run_checklist.csv").write_text(
        "check,required,current_status,failure_action\n"
        "research_run_gate_passed,yes,not_run,block_execution\n"
        "primary_metric_finalized,yes,not_final,block_execution\n"
        "feature_list_finalized,yes,not_final,block_execution\n"
        "parameters_finalized,yes,not_final,block_execution\n"
        "sample_definition_finalized,yes,not_final,block_execution\n"
        "trial_ledger_ready,yes,template_only,block_execution\n"
        "raw_retention_policy_confirmed,yes,derived_only,block_raw_retention\n",
        encoding="utf-8",
    )
    (plan_dir / "research_plan_summary.md").write_text("# Summary\nPlan not executed.\n", encoding="utf-8")
    return plan_dir


def test_validate_preregistered_research_plan_passes_valid_plan(tmp_path: Path) -> None:
    plan_dir = _valid_plan_dir(tmp_path)

    report = validate_preregistered_research_plan(plan_dir)

    assert report["status"] == "pass"
    assert report["plan_dir"] == str(plan_dir)
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "manifest_plan_not_executed" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"] == "checklist_unresolved_items_block_execution" and check["status"] == "pass" for check in report["checks"])


def test_validate_preregistered_research_plan_fails_missing_required_file(tmp_path: Path) -> None:
    plan_dir = _valid_plan_dir(tmp_path)
    (plan_dir / "decision_rule.csv").unlink()

    report = validate_preregistered_research_plan(plan_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "required_file:decision_rule.csv" and check["status"] == "fail" for check in report["checks"])


def test_validate_preregistered_research_plan_fails_if_executed(tmp_path: Path) -> None:
    plan_dir = _valid_plan_dir(tmp_path)
    manifest_path = plan_dir / "research_plan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["execution_status"] = "executed"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_preregistered_research_plan(plan_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_plan_not_executed" and check["status"] == "fail" for check in report["checks"])


def test_validate_preregistered_research_plan_fails_if_promotion_not_blocked(tmp_path: Path) -> None:
    plan_dir = _valid_plan_dir(tmp_path)
    (plan_dir / "decision_rule.csv").write_text(
        "decision_item,status,rule\n"
        "gate_precondition,required,gate pass required\n"
        "primary_metric,not_final,metric required\n"
        "go_rule,not_final,go rule required\n"
        "stop_rule,required,stop on failure\n"
        "promotion_rule,allowed,promotion allowed\n",
        encoding="utf-8",
    )

    report = validate_preregistered_research_plan(plan_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "decision_promotion_blocked" and check["status"] == "fail" for check in report["checks"])


def test_preregistered_research_plan_validator_cli_exit_codes(tmp_path: Path) -> None:
    plan_dir = _valid_plan_dir(tmp_path)

    assert main(["--plan-dir", str(plan_dir)]) == 0

    (plan_dir / "research_plan_manifest.json").unlink()

    assert main(["--plan-dir", str(plan_dir)]) == 1
