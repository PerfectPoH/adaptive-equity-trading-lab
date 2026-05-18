from __future__ import annotations

import json
from pathlib import Path

from src.experiments.pre_execution_output_ledger_validator import main, validate_pre_execution_output_ledger


def _write_valid_artifact(root: Path) -> Path:
    artifact = root / "artifact"
    artifact.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "OUTPUT_LEDGER_GATES_DEFINED_EXECUTION_BLOCKED",
        "research_stage": "new_signal_research",
        "preregistration_id": "PREREG-PA-SMALLCAP-001",
        "trial_id": "TRIAL-001",
        "run_id": "RUN-PREREG-PA-SMALLCAP-001-001",
        "planned_output_dir": "future-output",
        "output_directory_created": False,
        "trial_ledger_entry_created": False,
        "trial_consumed": False,
        "provider_query_performed": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "execution_approval_status": "not_granted",
        "required_tables": ["output_directory_gate.csv"],
    }
    (artifact / "pre_execution_output_ledger_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "output_directory_gate.csv").write_text(
        "field,value,status\n"
        "planned_output_dir,future-output,specified_not_created\n"
        "directory_creation_allowed,false,blocks_until_approval\n"
        "raw_payload_retention,false,required\n"
        "immutable_run_manifest_required,true,pending\n"
        "write_test_performed,false,not_performed\n",
        encoding="utf-8",
    )
    (artifact / "trial_ledger_gate.csv").write_text(
        "field,value,status\n"
        "trial_id,TRIAL-001,planned_not_created\n"
        "preregistration_id,PREREG-PA-SMALLCAP-001,planned\n"
        "trial_consumed,false,required_before_execution\n"
        "trial_budget_remaining_after_run,pending,blocked_until_execution\n"
        "ledger_entry_created,false,blocks_execution\n"
        "result_status,not_run,required\n",
        encoding="utf-8",
    )
    (artifact / "pre_execution_blockers.csv").write_text(
        "blocker,severity,current_status,required_response\n"
        "approval,critical,present,approve\n"
        "output,critical,present,create\n"
        "ledger,critical,present,create\n"
        "trial,critical,present,consume\n",
        encoding="utf-8",
    )
    (artifact / "pre_execution_output_ledger_summary.md").write_text("# Summary\n", encoding="utf-8")
    return artifact


def test_validate_pre_execution_output_ledger_passes_valid_artifact(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)

    report = validate_pre_execution_output_ledger(artifact)

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0


def test_validate_pre_execution_output_ledger_fails_if_trial_consumed(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)
    manifest_path = artifact / "pre_execution_output_ledger_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["trial_consumed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_pre_execution_output_ledger(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_provider_execution_side_effects" and check["status"] == "fail" for check in report["checks"])


def test_validate_pre_execution_output_ledger_fails_if_output_creation_allowed(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)
    (artifact / "output_directory_gate.csv").write_text(
        "field,value,status\n"
        "planned_output_dir,future-output,specified_not_created\n"
        "directory_creation_allowed,true,allowed\n"
        "raw_payload_retention,false,required\n"
        "immutable_run_manifest_required,true,pending\n"
        "write_test_performed,false,not_performed\n",
        encoding="utf-8",
    )

    report = validate_pre_execution_output_ledger(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "output_gate_directory_not_allowed" and check["status"] == "fail" for check in report["checks"])


def test_validate_pre_execution_output_ledger_fails_if_ledger_created(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)
    (artifact / "trial_ledger_gate.csv").write_text(
        "field,value,status\n"
        "trial_id,TRIAL-001,planned_not_created\n"
        "preregistration_id,PREREG-PA-SMALLCAP-001,planned\n"
        "trial_consumed,false,required_before_execution\n"
        "trial_budget_remaining_after_run,pending,blocked_until_execution\n"
        "ledger_entry_created,true,created\n"
        "result_status,not_run,required\n",
        encoding="utf-8",
    )

    report = validate_pre_execution_output_ledger(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "ledger_gate_entry_not_created" and check["status"] == "fail" for check in report["checks"])


def test_main_exits_zero_for_valid_artifact(tmp_path: Path, capsys) -> None:
    artifact = _write_valid_artifact(tmp_path)

    code = main(["--artifact-dir", str(artifact)])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert report["status"] == "pass"
