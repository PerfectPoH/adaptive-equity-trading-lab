from __future__ import annotations

import json
from pathlib import Path

from src.experiments.trial_accounting_preregistration_validator import main, validate_trial_accounting_preregistration


def _valid_spec_dir(tmp_path: Path) -> Path:
    spec_dir = tmp_path / "trial_spec"
    spec_dir.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "TRIAL_ACCOUNTING_AND_PREREGISTRATION_REQUIRED_BEFORE_SIGNAL_RESEARCH",
        "scope": "Provider-aware small-cap research track",
        "purpose": "Prevent p-hacking.",
        "no_provider_query": True,
        "no_backtest": True,
        "no_strategy_promotion": True,
        "required_tables": ["preregistration_template.csv"],
    }
    (spec_dir / "trial_accounting_preregistration_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (spec_dir / "preregistration_schema.csv").write_text(
        "field,required,allowed_or_format,description\n"
        "preregistration_id,yes,string,id\n"
        "research_question,yes,string,question\n"
        "hypothesis,yes,string,hypothesis\n"
        "provider_contract_id,yes,string,contract\n"
        "adjustment_tradability_policy_id,yes,string,policy\n"
        "sample_definition,yes,string,sample\n"
        "in_sample_window,yes,date_range,window\n"
        "holdout_window,conditional,date_range,holdout\n"
        "features_allowed,yes,list,features\n"
        "parameters_allowed,yes,list,parameters\n"
        "primary_metric,yes,string,metric\n"
        "secondary_metrics,yes,list,metrics\n"
        "trial_budget_id,yes,string,budget\n"
        "stop_go_threshold_id,yes,string,threshold\n"
        "forbidden_changes_after_execution,yes,list,forbidden\n"
        "raw_data_retention_policy,yes,string,retention\n",
        encoding="utf-8",
    )
    (spec_dir / "preregistration_template.csv").write_text(
        "preregistration_id,research_question,hypothesis,provider_contract_id,adjustment_tradability_policy_id,sample_definition,in_sample_window,holdout_window,features_allowed,parameters_allowed,primary_metric,secondary_metrics,trial_budget_id,stop_go_threshold_id,forbidden_changes_after_execution,raw_data_retention_policy\n"
        "PREREG-001,Question,Hypothesis,PCC-001,ATP-001,frozen,2024-01-01_to_2024-12-31,not_used,features,params,metric,secondary,TB-001,TH-001,metric_switching,derived_only\n",
        encoding="utf-8",
    )
    (spec_dir / "trial_budget_policy.csv").write_text(
        "trial_budget_id,stage,max_trials,what_counts_as_trial,reset_allowed,notes\n"
        "TB-001,new_signal_research,3,signal run,no,notes\n"
        "TB-002,portfolio_backtest,1,portfolio run,no,notes\n"
        "TB-003,OOS,1,oos run,no,notes\n"
        "TB-004,paper_live,1,paper attempt,no,notes\n",
        encoding="utf-8",
    )
    (spec_dir / "decision_thresholds.csv").write_text(
        "threshold_id,stage,primary_metric,go_condition,stop_condition,caveat_condition\n"
        "TH-001,new_signal_research,metric,go,stop,caveat\n"
        "TH-002,portfolio_backtest,metric,go,stop,caveat\n"
        "TH-003,OOS,metric,go,stop,caveat\n",
        encoding="utf-8",
    )
    (spec_dir / "trial_ledger_template.csv").write_text(
        "trial_id,preregistration_id,stage,executed_at,code_commit,artifact_dir,trial_number,within_budget,result_status,decision,notes\n"
        "TRIAL-001,PREREG-001,new_signal_research,not_executed,commit,artifact,1,yes,not_executed,not_decided,template\n",
        encoding="utf-8",
    )
    (spec_dir / "research_stage_enforcement.csv").write_text(
        "research_stage,preregistration_required,trial_ledger_required,trial_budget_required,promotion_allowed\n"
        "data_quality_diagnostic,recommended,recommended,no,no\n"
        "fixed_signal_replay,recommended,recommended,no,no\n"
        "new_signal_research,yes,yes,yes,no\n"
        "portfolio_backtest,yes,yes,yes,no_until_separate_promotion_gate\n"
        "OOS,yes,yes,yes,no_until_separate_promotion_gate\n"
        "paper_live,yes,yes,yes,conditional\n",
        encoding="utf-8",
    )
    (spec_dir / "trial_accounting_preregistration_summary.md").write_text("# Summary\nSpec complete.\n", encoding="utf-8")
    return spec_dir


def test_validate_trial_accounting_preregistration_passes_valid_spec(tmp_path: Path) -> None:
    spec_dir = _valid_spec_dir(tmp_path)

    report = validate_trial_accounting_preregistration(spec_dir)

    assert report["status"] == "pass"
    assert report["spec_dir"] == str(spec_dir)
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "schema_required_preregistration_fields" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"] == "enforcement_required_after_diagnostics" and check["status"] == "pass" for check in report["checks"])


def test_validate_trial_accounting_preregistration_fails_missing_required_file(tmp_path: Path) -> None:
    spec_dir = _valid_spec_dir(tmp_path)
    (spec_dir / "trial_budget_policy.csv").unlink()

    report = validate_trial_accounting_preregistration(spec_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "required_file:trial_budget_policy.csv" and check["status"] == "fail" for check in report["checks"])


def test_validate_trial_accounting_preregistration_fails_missing_template_column(tmp_path: Path) -> None:
    spec_dir = _valid_spec_dir(tmp_path)
    (spec_dir / "preregistration_template.csv").write_text("preregistration_id,research_question\nPREREG,Question\n", encoding="utf-8")

    report = validate_trial_accounting_preregistration(spec_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "template_required_columns" and check["status"] == "fail" for check in report["checks"])


def test_validate_trial_accounting_preregistration_fails_execution_flags(tmp_path: Path) -> None:
    spec_dir = _valid_spec_dir(tmp_path)
    manifest_path = spec_dir / "trial_accounting_preregistration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["no_provider_query"] = False
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_trial_accounting_preregistration(spec_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_flags" and check["status"] == "fail" for check in report["checks"])


def test_trial_accounting_preregistration_validator_cli_exit_codes(tmp_path: Path) -> None:
    spec_dir = _valid_spec_dir(tmp_path)

    assert main(["--spec-dir", str(spec_dir)]) == 0

    (spec_dir / "trial_accounting_preregistration_manifest.json").unlink()

    assert main(["--spec-dir", str(spec_dir)]) == 1
