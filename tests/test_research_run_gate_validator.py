from __future__ import annotations

import json
from pathlib import Path

from src.experiments.research_run_gate_validator import main, validate_research_run_gate


def _write_component_dirs(root: Path) -> tuple[Path, Path, Path]:
    pcc = root / "pcc"
    atp = root / "atp"
    tap = root / "tap"
    pcc.mkdir()
    atp.mkdir()
    tap.mkdir()
    (pcc / "provider_coverage_contract_manifest.json").write_text(json.dumps({"status":"SPEC_ONLY_NOT_EXECUTED","decision":"x","scope":"x","purpose":"x","no_provider_query":True,"no_backtest":True,"required_for":["x"],"minimum_contract_tables":["x"]}), encoding="utf-8")
    (pcc / "coverage_contract_schema.csv").write_text("field,required,allowed_or_format,description\ncontract_id,yes,string,x\nprovider_combo,yes,string,x\ndataset_or_endpoint,yes,string,x\ncoverage_start,yes,date,x\ncoverage_end,yes,date,x\nsymbol_scope,yes,string,x\nmissingness_policy,yes,string,x\nadjustment_policy,yes,string,x\ncorporate_action_policy,yes,string,x\nhalt_tradability_policy,yes,string,x\nPIT_universe_policy,yes,string,x\nlicensing_retention_policy,yes,string,x\nprovider_quality_warnings,yes,string,x\nstop_conditions,yes,string,x\napproved_uses,yes,string,x\nblocked_uses,yes,string,x\n", encoding="utf-8")
    (pcc / "coverage_contract_template.csv").write_text("contract_id,provider_combo,dataset_or_endpoint,coverage_start,coverage_end,symbol_scope,missingness_policy,adjustment_policy,corporate_action_policy,halt_tradability_policy,PIT_universe_policy,licensing_retention_policy,provider_quality_warnings,stop_conditions,approved_uses,blocked_uses\nC,P,D,2024-01-01,open,S,M,A,CA,H,PIT,L,W,STOP,OK,BLOCK\n", encoding="utf-8")
    (pcc / "coverage_validation_checklist.csv").write_text("check,severity,pass_condition,failure_action\ncoverage_dates_declared,critical,x,x\nsymbol_scope_frozen,critical,x,x\nmissingness_policy_declared,critical,x,x\nadjustment_policy_declared,critical,x,x\ncorporate_action_policy_declared,high,x,x\nhalt_tradability_policy_declared,high,x,x\nPIT_universe_policy_declared,critical,x,x\nlicensing_policy_declared,critical,x,x\nprovider_warning_capture,high,x,x\nstop_conditions_declared,critical,x,x\n", encoding="utf-8")
    (pcc / "coverage_contract_enforcement_policy.csv").write_text("use_case,contract_required,minimum_status\ndata_quality_audit,yes,x\nfixed_signal_replay,yes,x\nnew_signal_research,yes,x\nportfolio_backtest,yes,x\nOOS,yes,x\npaper_live_trading,yes,x\n", encoding="utf-8")
    (pcc / "provider_coverage_contract_summary.md").write_text("# Summary\n", encoding="utf-8")
    (atp / "adjustment_tradability_policy_manifest.json").write_text(json.dumps({"status":"SPEC_ONLY_NOT_EXECUTED","decision":"x","scope":"x","purpose":"x","no_provider_query":True,"no_backtest":True,"no_strategy_promotion":True,"required_policy_tables":["x"]}), encoding="utf-8")
    (atp / "adjustment_tradability_policy.csv").write_text("policy_area,current_status,allowed_for_diagnostics,allowed_for_performance,required_before_performance,notes\nprice_adjustment,x,yes,no,x,x\ncorporate_actions,x,yes,no,x,x\nhalt_tradability,x,yes,no,x,x\nPIT_universe,x,yes,no,x,x\nlicensing_retention,x,yes,conditional,x,x\nprovider_quality_warnings,x,yes,conditional,x,x\n", encoding="utf-8")
    (atp / "policy_stop_conditions.csv").write_text("stop_condition,severity,blocked_work,resolution_required\nadjustment_policy_unknown_and_performance_requested,critical,x,x\ncorporate_action_source_missing_for_adjusted_claim,critical,x,x\nhalt_tradability_unknown_for_small_cap_execution,critical,x,x\nPIT_universe_missing_for_universe_claim,critical,x,x\nraw_retention_required_without_license,critical,x,x\nprovider_quality_warning_ignored,high,x,x\n", encoding="utf-8")
    (atp / "policy_enforcement_matrix.csv").write_text("research_stage,policy_required,minimum_policy_status,promotion_allowed\ndata_quality_diagnostic,yes,x,no\nfixed_signal_replay,yes,x,no\nnew_signal_research,yes,x,no\nportfolio_backtest,yes,x,no_until_separate_promotion_gate\nOOS,yes,x,no_until_separate_promotion_gate\npaper_live,yes,x,conditional\n", encoding="utf-8")
    (atp / "adjustment_tradability_policy_summary.md").write_text("# Summary\n", encoding="utf-8")
    (tap / "trial_accounting_preregistration_manifest.json").write_text(json.dumps({"status":"SPEC_ONLY_NOT_EXECUTED","decision":"x","scope":"x","purpose":"x","no_provider_query":True,"no_backtest":True,"no_strategy_promotion":True,"required_tables":["x"]}), encoding="utf-8")
    (tap / "preregistration_schema.csv").write_text("field,required,allowed_or_format,description\npreregistration_id,yes,string,x\nresearch_question,yes,string,x\nhypothesis,yes,string,x\nprovider_contract_id,yes,string,x\nadjustment_tradability_policy_id,yes,string,x\nsample_definition,yes,string,x\nin_sample_window,yes,string,x\nholdout_window,conditional,string,x\nfeatures_allowed,yes,string,x\nparameters_allowed,yes,string,x\nprimary_metric,yes,string,x\nsecondary_metrics,yes,string,x\ntrial_budget_id,yes,string,x\nstop_go_threshold_id,yes,string,x\nforbidden_changes_after_execution,yes,string,x\nraw_data_retention_policy,yes,string,x\n", encoding="utf-8")
    (tap / "preregistration_template.csv").write_text("preregistration_id,research_question,hypothesis,provider_contract_id,adjustment_tradability_policy_id,sample_definition,in_sample_window,holdout_window,features_allowed,parameters_allowed,primary_metric,secondary_metrics,trial_budget_id,stop_go_threshold_id,forbidden_changes_after_execution,raw_data_retention_policy\nP,Q,H,C,A,S,W,HU,F,PA,M,SM,TB,TH,FC,R\n", encoding="utf-8")
    (tap / "trial_budget_policy.csv").write_text("trial_budget_id,stage,max_trials,what_counts_as_trial,reset_allowed,notes\nTB,new_signal_research,1,x,no,x\nTB2,portfolio_backtest,1,x,no,x\nTB3,OOS,1,x,no,x\nTB4,paper_live,1,x,no,x\n", encoding="utf-8")
    (tap / "decision_thresholds.csv").write_text("threshold_id,stage,primary_metric,go_condition,stop_condition,caveat_condition\nTH,new_signal_research,m,g,s,c\nTH2,portfolio_backtest,m,g,s,c\nTH3,OOS,m,g,s,c\n", encoding="utf-8")
    (tap / "trial_ledger_template.csv").write_text("trial_id,preregistration_id,stage,executed_at,code_commit,artifact_dir,trial_number,within_budget,result_status,decision,notes\nT,P,new_signal_research,not_executed,c,a,1,yes,not_executed,not_decided,x\n", encoding="utf-8")
    (tap / "research_stage_enforcement.csv").write_text("research_stage,preregistration_required,trial_ledger_required,trial_budget_required,promotion_allowed\ndata_quality_diagnostic,recommended,recommended,no,no\nfixed_signal_replay,recommended,recommended,no,no\nnew_signal_research,yes,yes,yes,no\nportfolio_backtest,yes,yes,yes,no_until_separate_promotion_gate\nOOS,yes,yes,yes,no_until_separate_promotion_gate\npaper_live,yes,yes,yes,conditional\n", encoding="utf-8")
    (tap / "trial_accounting_preregistration_summary.md").write_text("# Summary\n", encoding="utf-8")
    return pcc, atp, tap


def _valid_gate_dir(tmp_path: Path) -> Path:
    pcc, atp, tap = _write_component_dirs(tmp_path)
    gate = tmp_path / "gate"
    gate.mkdir()
    manifest = {"status":"SPEC_ONLY_NOT_EXECUTED","decision":"RESEARCH_RUN_GATE_REQUIRED_BEFORE_ANY_PROVIDER_AWARE_RUN","scope":"x","purpose":"x","no_provider_query":True,"no_backtest":True,"no_strategy_promotion":True,"required_components":["provider_coverage_contract","adjustment_tradability_policy","trial_accounting_preregistration"],"default_gate_decision":"BLOCK_UNLESS_ALL_REQUIRED_COMPONENTS_PASS"}
    (gate / "research_run_gate_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (gate / "research_run_gate_components.csv").write_text(
        "component_id,component_type,artifact_dir,validator_module,minimum_status,required_for_run,notes\n"
        f"PCC,provider_coverage_contract,{pcc},src.experiments.provider_coverage_contract_validator,pass,yes,x\n"
        f"ATP,adjustment_tradability_policy,{atp},src.experiments.adjustment_tradability_policy_validator,pass,yes,x\n"
        f"TAP,trial_accounting_preregistration,{tap},src.experiments.trial_accounting_preregistration_validator,pass,yes,x\n",
        encoding="utf-8",
    )
    (gate / "research_stage_gate_matrix.csv").write_text(
        "research_stage,gate_required,required_components,allowed_if_gate_passes,blocked_if_gate_fails\n"
        "data_quality_diagnostic,yes,provider_coverage_contract;adjustment_tradability_policy,diagnostic,blocked\n"
        "fixed_signal_replay,yes,provider_coverage_contract;adjustment_tradability_policy,diagnostic,blocked\n"
        "new_signal_research,yes,provider_coverage_contract;adjustment_tradability_policy;trial_accounting_preregistration,research,blocked\n"
        "portfolio_backtest,yes,provider_coverage_contract;adjustment_tradability_policy;trial_accounting_preregistration,run,blocked\n"
        "OOS,yes,provider_coverage_contract;adjustment_tradability_policy;trial_accounting_preregistration,run,blocked\n"
        "paper_live,yes,provider_coverage_contract;adjustment_tradability_policy;trial_accounting_preregistration,conditional,blocked\n",
        encoding="utf-8",
    )
    (gate / "gate_decision_policy.csv").write_text("gate_result,meaning,allowed_action,blocked_action\npass,x,x,x\nfail,x,x,x\nnot_applicable,x,x,x\n", encoding="utf-8")
    (gate / "research_run_gate_summary.md").write_text("# Summary\n", encoding="utf-8")
    return gate


def test_validate_research_run_gate_passes_valid_gate(tmp_path: Path, monkeypatch) -> None:
    gate = _valid_gate_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    report = validate_research_run_gate(gate, "new_signal_research")

    assert report["status"] == "pass"
    assert len(report["component_reports"]) == 3
    assert any(check["name"] == "component_validator_pass:trial_accounting_preregistration" and check["status"] == "pass" for check in report["checks"])


def test_validate_research_run_gate_uses_stage_specific_components(tmp_path: Path, monkeypatch) -> None:
    gate = _valid_gate_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    report = validate_research_run_gate(gate, "fixed_signal_replay")

    assert report["status"] == "pass"
    assert [component["component_type"] for component in report["component_reports"]] == ["provider_coverage_contract", "adjustment_tradability_policy"]


def test_validate_research_run_gate_fails_missing_required_file(tmp_path: Path, monkeypatch) -> None:
    gate = _valid_gate_dir(tmp_path)
    (gate / "gate_decision_policy.csv").unlink()
    monkeypatch.chdir(tmp_path)

    report = validate_research_run_gate(gate, "new_signal_research")

    assert report["status"] == "fail"
    assert any(check["name"] == "required_file:gate_decision_policy.csv" and check["status"] == "fail" for check in report["checks"])


def test_validate_research_run_gate_fails_component_validator_failure(tmp_path: Path, monkeypatch) -> None:
    gate = _valid_gate_dir(tmp_path)
    tap = tmp_path / "tap"
    (tap / "trial_budget_policy.csv").unlink()
    monkeypatch.chdir(tmp_path)

    report = validate_research_run_gate(gate, "new_signal_research")

    assert report["status"] == "fail"
    assert any(check["name"] == "component_validator_pass:trial_accounting_preregistration" and check["status"] == "fail" for check in report["checks"])


def test_research_run_gate_validator_cli_exit_codes(tmp_path: Path, monkeypatch) -> None:
    gate = _valid_gate_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert main(["--gate-dir", str(gate), "--research-stage", "new_signal_research"]) == 0

    (gate / "research_run_gate_manifest.json").unlink()

    assert main(["--gate-dir", str(gate), "--research-stage", "new_signal_research"]) == 1
