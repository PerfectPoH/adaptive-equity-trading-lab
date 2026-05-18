from __future__ import annotations

import json
from pathlib import Path

from src.experiments.dry_run_preflight_validator import main, validate_dry_run_preflight


def _valid_artifact(tmp_path: Path) -> Path:
    artifact = tmp_path / "preflight"
    artifact.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "DRY_RUN_PREFLIGHT_DEFINED_BLOCKED_NOT_RUN",
        "scope": "preflight",
        "research_stage": "new_signal_research",
        "preflight_decision": "blocked_until_manual_execution_inputs_resolved",
        "no_provider_query": True,
        "no_backtest": True,
        "no_strategy_promotion": True,
        "required_tables": ["preflight_components.csv"],
    }
    (artifact / "dry_run_preflight_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "preflight_components.csv").write_text(
        "component_type,artifact_dir,validator_module,validator_function,required_status,current_expected_status\n"
        "research_run_gate,missing,missing,missing,pass,pass\n"
        "preregistered_research_plan,missing,missing,missing,pass,pass\n"
        "execution_authorization,missing,missing,missing,pass,pass\n"
        "execution_command_output_schema,missing,missing,missing,pass,pass\n"
        "governance_calibration,missing,missing,missing,pass,pass\n"
        "manual_preflight_inputs,missing,missing,missing,pass,pass\n"
        "pre_execution_output_ledger,missing,missing,missing,pass,pass\n"
        "final_command_review,missing,missing,missing,pass,pass\n",
        encoding="utf-8",
    )
    (artifact / "preflight_required_inputs.csv").write_text(
        "input_name,required,current_status,blocks_execution,resolution_required\n"
        "explicit_user_execution_approval,yes,missing,yes,approve\n"
        "final_execution_module,yes,not_final,yes,module\n"
        "final_output_directory,yes,placeholder,yes,dir\n"
        "trial_ledger_entry,yes,missing,yes,ledger\n"
        "provider_credentials_check,yes,not_checked,yes,credentials\n"
        "command_dry_review,yes,not_reviewed,yes,review\n",
        encoding="utf-8",
    )
    (artifact / "preflight_decision_matrix.csv").write_text(
        "preflight_result,condition,allowed_action,blocked_action\n"
        "pass,all resolved,allow separately approved controlled execution,none\n"
        "blocked,inputs unresolved,continue spec-only preparation,provider_query;backtest;execution\n"
        "fail,component fails,revise artifacts,provider_query;backtest;execution\n"
        "not_alpha_evidence,no run,do not claim performance,strategy_promotion\n",
        encoding="utf-8",
    )
    (artifact / "preflight_blocker_register.csv").write_text(
        "blocker,severity,current_status,required_response\n"
        "explicit_user_execution_approval_missing,critical,present,approve\n"
        "execution_module_not_final,critical,present,module\n"
        "output_directory_placeholder,critical,present,dir\n"
        "trial_ledger_entry_missing,critical,present,ledger\n"
        "provider_credentials_not_checked,high,present,credentials\n"
        "command_not_reviewed,high,present,review\n",
        encoding="utf-8",
    )
    (artifact / "dry_run_preflight_summary.md").write_text("# Summary\nBlocked spec only.\n", encoding="utf-8")
    return artifact


def test_validate_dry_run_preflight_returns_fail_when_component_validators_missing(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    report = validate_dry_run_preflight(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "components_required_items" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"].startswith("component_validator_load:") and check["status"] == "fail" for check in report["checks"])


def test_validate_dry_run_preflight_fails_if_manifest_not_blocked(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    manifest_path = artifact / "dry_run_preflight_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["preflight_decision"] = "pass"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_dry_run_preflight(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_spec_only_blocked" and check["status"] == "fail" for check in report["checks"])


def test_validate_dry_run_preflight_fails_without_unresolved_input_block(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "preflight_required_inputs.csv").write_text(
        "input_name,required,current_status,blocks_execution,resolution_required\n"
        "explicit_user_execution_approval,yes,missing,no,approve\n"
        "final_execution_module,yes,not_final,no,module\n"
        "final_output_directory,yes,placeholder,no,dir\n"
        "trial_ledger_entry,yes,missing,no,ledger\n"
        "provider_credentials_check,yes,not_checked,no,credentials\n"
        "command_dry_review,yes,not_reviewed,no,review\n",
        encoding="utf-8",
    )

    report = validate_dry_run_preflight(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "inputs_unresolved_block_execution" and check["status"] == "fail" for check in report["checks"])


def test_dry_run_preflight_validator_cli_exit_code_fails_for_invalid_components(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    assert main(["--artifact-dir", str(artifact)]) == 1

    (artifact / "dry_run_preflight_manifest.json").unlink()

    assert main(["--artifact-dir", str(artifact)]) == 1
