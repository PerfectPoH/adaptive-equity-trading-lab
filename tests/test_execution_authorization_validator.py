from __future__ import annotations

import json
from pathlib import Path

from src.experiments.execution_authorization_validator import main, validate_execution_authorization


def _valid_artifact(tmp_path: Path) -> Path:
    artifact = tmp_path / "authorization"
    artifact.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "EXPLICIT_EXECUTION_AUTHORIZATION_DEFINED_NOT_RUN",
        "scope": "One controlled future execution",
        "authorization_status": "defined_not_granted",
        "linked_preregistered_plan": "plan",
        "linked_research_run_gate": "gate",
        "research_stage": "new_signal_research",
        "no_provider_query": True,
        "no_backtest": True,
        "no_strategy_promotion": True,
        "execution_performed": False,
        "required_tables": ["authorization_conditions.csv"],
    }
    (artifact / "execution_authorization_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "authorization_conditions.csv").write_text(
        "condition,required,current_status,failure_action\n"
        "preregistered_plan_validator_pass,yes,passed,block_execution\n"
        "research_run_gate_pass,yes,passed,block_execution\n"
        "user_explicit_run_approval,yes,not_granted,block_execution\n"
        "provider_credentials_available,yes,not_checked,block_execution\n"
        "trial_budget_available,yes,available,block_execution\n"
        "raw_retention_policy_confirmed,yes,derived_only,block_raw_retention\n"
        "execution_command_dry_reviewed,yes,not_defined,block_execution\n",
        encoding="utf-8",
    )
    (artifact / "allowed_execution_scope.csv").write_text(
        "scope_item,allowed,limit,notes\n"
        "preregistration_id,yes,PREREG-PA-SMALLCAP-001,Only this plan\n"
        "execution_count,yes,1,One controlled diagnostic execution only\n"
        "provider_data_access,conditional,minimum required symbols/date window only,No ALL_SYMBOLS query\n",
        encoding="utf-8",
    )
    (artifact / "blocked_actions.csv").write_text(
        "blocked_action,severity,reason\n"
        "ALL_SYMBOLS_query,critical,no uncontrolled universe\n"
        "parameter_sweep,critical,no sweep\n"
        "strategy_promotion,critical,no promotion\n"
        "OOS_claim,critical,no OOS claim\n"
        "paper_or_live_trading,critical,no trading\n"
        "raw_payload_retention,critical,no raw retention\n",
        encoding="utf-8",
    )
    (artifact / "pre_execution_evidence_checklist.csv").write_text(
        "evidence_item,required,current_status,source\n"
        "plan_validation_report,yes,available,validator\n"
        "gate_validation_report,yes,available,validator\n"
        "explicit_user_approval,yes,missing,user\n"
        "execution_command,yes,missing,command\n"
        "artifact_output_directory,yes,missing,path\n"
        "trial_ledger_entry,yes,missing,ledger\n",
        encoding="utf-8",
    )
    (artifact / "post_execution_artifact_requirements.csv").write_text(
        "artifact_requirement,required,notes\n"
        "execution_manifest,yes,manifest\n"
        "trial_ledger_update,yes,ledger\n"
        "derived_results_only,yes,derived only\n"
        "provider_coverage_audit,yes,audit\n"
        "interpretation_report,yes,report\n",
        encoding="utf-8",
    )
    (artifact / "execution_authorization_summary.md").write_text("# Summary\nSpec only. Not executed.\n", encoding="utf-8")
    return artifact


def test_validate_execution_authorization_passes_valid_artifact(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    report = validate_execution_authorization(artifact)

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "manifest_spec_only_not_executed" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"] == "conditions_user_approval_not_granted" and check["status"] == "pass" for check in report["checks"])


def test_validate_execution_authorization_fails_if_execution_performed(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    manifest_path = artifact / "execution_authorization_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["execution_performed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_execution_authorization(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_spec_only_not_executed" and check["status"] == "fail" for check in report["checks"])


def test_validate_execution_authorization_fails_if_user_approval_granted_in_spec(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "authorization_conditions.csv").write_text(
        "condition,required,current_status,failure_action\n"
        "preregistered_plan_validator_pass,yes,passed,block_execution\n"
        "research_run_gate_pass,yes,passed,block_execution\n"
        "user_explicit_run_approval,yes,granted,block_execution\n"
        "provider_credentials_available,yes,not_checked,block_execution\n"
        "trial_budget_available,yes,available,block_execution\n"
        "raw_retention_policy_confirmed,yes,derived_only,block_raw_retention\n"
        "execution_command_dry_reviewed,yes,not_defined,block_execution\n",
        encoding="utf-8",
    )

    report = validate_execution_authorization(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "conditions_user_approval_not_granted" and check["status"] == "fail" for check in report["checks"])


def test_validate_execution_authorization_fails_missing_blocked_action(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "blocked_actions.csv").write_text(
        "blocked_action,severity,reason\n"
        "ALL_SYMBOLS_query,critical,no uncontrolled universe\n",
        encoding="utf-8",
    )

    report = validate_execution_authorization(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocked_actions_required_items" and check["status"] == "fail" for check in report["checks"])


def test_execution_authorization_validator_cli_exit_codes(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    assert main(["--artifact-dir", str(artifact)]) == 0

    (artifact / "execution_authorization_manifest.json").unlink()

    assert main(["--artifact-dir", str(artifact)]) == 1
