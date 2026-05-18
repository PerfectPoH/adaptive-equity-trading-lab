from __future__ import annotations

import json
from pathlib import Path

from src.experiments.execution_command_output_schema_validator import main, validate_execution_command_output_schema


def _valid_artifact(tmp_path: Path) -> Path:
    artifact = tmp_path / "schema"
    artifact.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "EXECUTION_COMMAND_AND_OUTPUT_SCHEMA_DEFINED_NOT_RUN",
        "scope": "schema",
        "linked_authorization": "auth",
        "linked_preregistered_plan": "plan",
        "research_stage": "new_signal_research",
        "execution_status": "not_executed",
        "no_provider_query": True,
        "no_backtest": True,
        "no_strategy_promotion": True,
        "required_tables": ["execution_command_spec.csv"],
    }
    (artifact / "execution_command_output_schema_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "execution_command_spec.csv").write_text(
        "field,value,status,notes\n"
        "command_id,CMD-1,defined,id\n"
        "command_type,future_controlled_diagnostic_execution,defined,type\n"
        "module,to_be_implemented_or_selected,not_final,module\n"
        "arguments,--output-dir <future_output_dir>,template_only,args\n"
        "max_execution_count,1,defined,max\n"
        "allowed_providers,databento;polygon;yfinance_reference,defined,providers\n"
        "forbidden_flags,--all-symbols;--sweep;--promote;--paper;--live,defined,forbidden\n",
        encoding="utf-8",
    )
    (artifact / "output_artifact_schema.csv").write_text(
        "artifact_name,required,format,schema_status,notes\n"
        "execution_manifest,yes,json,defined,manifest\n"
        "provider_coverage_audit,yes,csv,defined,audit\n"
        "derived_event_panel,yes,csv,defined,panel\n"
        "diagnostic_summary,yes,csv,defined,summary\n"
        "interpretation_report,yes,md,defined,report\n"
        "trial_ledger_update,yes,csv,defined,ledger\n",
        encoding="utf-8",
    )
    (artifact / "run_manifest_schema.csv").write_text(
        "field,required,allowed_values_or_format,notes\n"
        "run_id,yes,RUN-1,id\n"
        "preregistration_id,yes,PREREG-PA-SMALLCAP-001,plan\n"
        "authorization_id,yes,AUTH-1,auth\n"
        "git_sha,yes,40_hex_or_short_sha,sha\n"
        "execution_started_at_utc,yes,ISO-8601,start\n"
        "execution_completed_at_utc,yes,ISO-8601,end\n"
        "execution_status,yes,not_started|completed|failed|aborted,status\n"
        "raw_payload_retained,yes,false,raw\n"
        "strategy_promotion,yes,false,promotion\n",
        encoding="utf-8",
    )
    (artifact / "trial_ledger_entry_schema.csv").write_text(
        "field,required,current_planned_value,notes\n"
        "trial_id,yes,TRIAL-001,id\n"
        "preregistration_id,yes,PREREG-PA-SMALLCAP-001,plan\n"
        "trial_consumed,yes,false_until_execution,consumed\n"
        "trial_budget_remaining_after_run,yes,2_if_executed,budget\n"
        "result_status,yes,not_run,result\n"
        "notes,yes,spec_only_no_execution,notes\n",
        encoding="utf-8",
    )
    (artifact / "preflight_blockers.csv").write_text(
        "blocker,current_status,failure_action\n"
        "output_dir_placeholder,present,block_execution\n"
        "execution_module_not_final,present,block_execution\n"
        "explicit_user_approval_missing,present,block_execution\n"
        "provider_credentials_not_checked,present,block_execution\n"
        "trial_ledger_not_created,present,block_execution\n"
        "raw_payload_retention_forbidden,enforced,block_raw_retention\n",
        encoding="utf-8",
    )
    (artifact / "execution_command_output_schema_summary.md").write_text("# Summary\nSpec only.\n", encoding="utf-8")
    return artifact


def test_validate_execution_command_output_schema_passes_valid_artifact(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    report = validate_execution_command_output_schema(artifact)

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "command_output_placeholder_present" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"] == "ledger_result_not_run" and check["status"] == "pass" for check in report["checks"])


def test_validate_execution_command_output_schema_fails_if_executed(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    manifest_path = artifact / "execution_command_output_schema_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["execution_status"] = "completed"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_execution_command_output_schema(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_spec_only_not_executed" and check["status"] == "fail" for check in report["checks"])


def test_validate_execution_command_output_schema_fails_missing_forbidden_flag(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "execution_command_spec.csv").write_text(
        "field,value,status,notes\n"
        "command_id,CMD-1,defined,id\n"
        "command_type,future_controlled_diagnostic_execution,defined,type\n"
        "module,to_be_implemented_or_selected,not_final,module\n"
        "arguments,--output-dir <future_output_dir>,template_only,args\n"
        "max_execution_count,1,defined,max\n"
        "allowed_providers,databento;polygon;yfinance_reference,defined,providers\n"
        "forbidden_flags,--all-symbols;--sweep,defined,forbidden\n",
        encoding="utf-8",
    )

    report = validate_execution_command_output_schema(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "command_forbidden_flags_declared" and check["status"] == "fail" for check in report["checks"])


def test_validate_execution_command_output_schema_fails_missing_blocker(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "preflight_blockers.csv").write_text(
        "blocker,current_status,failure_action\n"
        "output_dir_placeholder,present,block_execution\n",
        encoding="utf-8",
    )

    report = validate_execution_command_output_schema(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "blockers_required_items" and check["status"] == "fail" for check in report["checks"])


def test_execution_command_output_schema_validator_cli_exit_codes(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    assert main(["--artifact-dir", str(artifact)]) == 0

    (artifact / "execution_command_output_schema_manifest.json").unlink()

    assert main(["--artifact-dir", str(artifact)]) == 1
