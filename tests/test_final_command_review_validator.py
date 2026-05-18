from __future__ import annotations

import json
from pathlib import Path

from src.experiments.final_command_review_validator import main, validate_final_command_review


def _write_valid_artifact(root: Path) -> Path:
    artifact = root / "artifact"
    artifact.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "FINAL_COMMAND_REVIEWED_EXECUTION_STILL_BLOCKED",
        "provider_query_performed": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "output_directory_created": False,
        "trial_consumed": False,
        "execution_approval_status": "not_granted",
    }
    (artifact / "final_command_review_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "command_review.csv").write_text(
        "field,value,status\n"
        "command_id,CMD,reviewed\nmodule,m,reviewed\nentrypoint,e,reviewed\nmode,--real-run,blocked_gate_report_only\n"
        "preregistration_id,P,reviewed\ntrial_id,T,reviewed\noutput_dir,o,reviewed_not_created\ncredential_source,env-file,reviewed_no_disclosure\napproval,not_granted,blocks_execution\n",
        encoding="utf-8",
    )
    (artifact / "command_gate_checks.csv").write_text(
        "check,status,detail\n"
        "single_preregistered_run,pass,d\nprovider_credentials_present,pass,d\nno_raw_payload_retention,pass,d\noutput_directory_not_created,pass,d\ntrial_not_consumed,pass,d\nexecution_approval_not_granted,pass,d\nprovider_query_not_performed,pass,d\n",
        encoding="utf-8",
    )
    (artifact / "forbidden_flags.csv").write_text(
        "flag,status,reason\n--all-symbols,forbidden_absent,r\n--sweep,forbidden_absent,r\n--promote,forbidden_absent,r\n--paper,forbidden_absent,r\n--live,forbidden_absent,r\n--retain-raw-response,forbidden_absent,r\n",
        encoding="utf-8",
    )
    (artifact / "remaining_execution_blockers.csv").write_text(
        "blocker,severity,current_status,required_response\napproval,critical,present,r\noutput,critical,present,r\nledger,critical,present,r\n",
        encoding="utf-8",
    )
    (artifact / "final_command_review_summary.md").write_text("# Summary\n", encoding="utf-8")
    return artifact


def test_validate_final_command_review_passes_valid_artifact(tmp_path: Path) -> None:
    report = validate_final_command_review(_write_valid_artifact(tmp_path))

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0


def test_validate_final_command_review_fails_if_provider_query_performed(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)
    manifest_path = artifact / "final_command_review_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_performed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_final_command_review(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_side_effects" and check["status"] == "fail" for check in report["checks"])


def test_validate_final_command_review_fails_if_approval_granted(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)
    manifest_path = artifact / "final_command_review_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["execution_approval_status"] = "granted"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_final_command_review(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_approval_not_granted" and check["status"] == "fail" for check in report["checks"])


def test_validate_final_command_review_fails_if_forbidden_flag_missing(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)
    (artifact / "forbidden_flags.csv").write_text(
        "flag,status,reason\n--all-symbols,forbidden_absent,r\n",
        encoding="utf-8",
    )

    report = validate_final_command_review(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "forbidden_flags_required_items" and check["status"] == "fail" for check in report["checks"])


def test_main_exits_zero_for_valid_artifact(tmp_path: Path, capsys) -> None:
    artifact = _write_valid_artifact(tmp_path)

    code = main(["--artifact-dir", str(artifact)])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert report["status"] == "pass"
