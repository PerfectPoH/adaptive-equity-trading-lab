from __future__ import annotations

import json
from pathlib import Path

from src.experiments.manual_preflight_inputs_validator import main, validate_manual_preflight_inputs


def _valid_artifact(tmp_path: Path) -> Path:
    artifact = tmp_path / "manual"
    artifact.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "MANUAL_PREFLIGHT_INPUTS_PARTIALLY_RESOLVED_RUN_NOT_APPROVED",
        "scope": "manual inputs",
        "linked_preflight": "preflight",
        "research_stage": "new_signal_research",
        "execution_approval_status": "not_granted",
        "no_provider_query": True,
        "no_backtest": True,
        "no_strategy_promotion": True,
        "required_tables": ["manual_input_resolution.csv"],
    }
    (artifact / "manual_preflight_inputs_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "manual_input_resolution.csv").write_text(
        "input_name,previous_status,new_status,blocks_execution,resolution_detail\n"
        "explicit_user_execution_approval,missing,not_granted,yes,no approval\n"
        "final_execution_module,not_final,specified_not_implemented,yes,module\n"
        "final_output_directory,placeholder,specified_not_created,yes,dir\n"
        "trial_ledger_entry,missing,planned_not_created,yes,ledger\n"
        "provider_credentials_check,not_checked,policy_defined_not_checked,yes,credentials\n"
        "command_dry_review,not_reviewed,reviewed_template_only,yes,review\n",
        encoding="utf-8",
    )
    (artifact / "final_command_review.csv").write_text(
        "field,value,status\n"
        "command_id,CMD-1,reviewed_template_only\n"
        "module,src.experiments.provider_sensitivity_diagnostic_runner,specified_not_implemented\n"
        "entrypoint,python -m src.experiments.provider_sensitivity_diagnostic_runner,specified_not_executed\n"
        "arguments,--output-dir future,template_only\n"
        "forbidden_flags_absent,--all-symbols;--sweep;--promote;--paper;--live,pass\n"
        "execution_approval,not_granted,blocks_execution\n",
        encoding="utf-8",
    )
    (artifact / "output_directory_plan.csv").write_text(
        "field,value,status\n"
        "planned_output_dir,future,specified_not_created\n"
        "run_id,RUN-1,specified\n"
        "retention_policy,derived_outputs_only,specified\n"
        "raw_payload_retention,false,enforced\n"
        "directory_creation,not_performed,blocks_execution_until_approval\n",
        encoding="utf-8",
    )
    (artifact / "trial_ledger_planned_entry.csv").write_text(
        "field,planned_value,status\n"
        "trial_id,TRIAL-001,planned\n"
        "preregistration_id,PREREG-PA-SMALLCAP-001,planned\n"
        "trial_consumed,false,not_consumed\n"
        "trial_budget_remaining_after_run,2_if_executed,planned\n"
        "result_status,not_run,not_run\n"
        "ledger_write_status,not_created,blocks_execution_until_approval\n",
        encoding="utf-8",
    )
    (artifact / "credential_check_policy.csv").write_text(
        "credential,required,check_status,notes\n"
        "DATABENTO_API_KEY,yes,not_checked,no env inspect\n"
        "POLYGON_API_KEY,yes,not_checked,no env inspect\n"
        "provider_query_performed,no,false,no query\n"
        "credential_failure_action,yes,block_execution,block\n",
        encoding="utf-8",
    )
    (artifact / "manual_preflight_inputs_summary.md").write_text("# Summary\nSpec only.\n", encoding="utf-8")
    return artifact


def test_validate_manual_preflight_inputs_passes_valid_artifact(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    report = validate_manual_preflight_inputs(artifact)

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "resolution_approval_not_granted" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"] == "ledger_trial_not_consumed" and check["status"] == "pass" for check in report["checks"])


def test_validate_manual_preflight_inputs_fails_if_approval_granted(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    manifest_path = artifact / "manual_preflight_inputs_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["execution_approval_status"] = "granted"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_manual_preflight_inputs(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_spec_only_not_approved" and check["status"] == "fail" for check in report["checks"])


def test_validate_manual_preflight_inputs_fails_if_provider_query_performed(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "credential_check_policy.csv").write_text(
        "credential,required,check_status,notes\n"
        "DATABENTO_API_KEY,yes,not_checked,no env inspect\n"
        "POLYGON_API_KEY,yes,not_checked,no env inspect\n"
        "provider_query_performed,yes,true,bad\n"
        "credential_failure_action,yes,block_execution,block\n",
        encoding="utf-8",
    )

    report = validate_manual_preflight_inputs(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "credentials_no_provider_query" and check["status"] == "fail" for check in report["checks"])


def test_validate_manual_preflight_inputs_fails_if_trial_consumed(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "trial_ledger_planned_entry.csv").write_text(
        "field,planned_value,status\n"
        "trial_consumed,true,consumed\n"
        "result_status,completed,run\n"
        "ledger_write_status,created,created\n",
        encoding="utf-8",
    )

    report = validate_manual_preflight_inputs(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "ledger_trial_not_consumed" and check["status"] == "fail" for check in report["checks"])


def test_manual_preflight_inputs_validator_cli_exit_codes(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    assert main(["--artifact-dir", str(artifact)]) == 0

    (artifact / "manual_preflight_inputs_manifest.json").unlink()

    assert main(["--artifact-dir", str(artifact)]) == 1
