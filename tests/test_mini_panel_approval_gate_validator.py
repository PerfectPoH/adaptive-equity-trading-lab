from __future__ import annotations

import json
from pathlib import Path

from src.experiments.mini_panel_approval_gate_validator import main, validate_mini_panel_approval_gate


def _write_valid_artifact(root: Path) -> Path:
    artifact = root / "mini_panel"
    artifact.mkdir()
    manifest = {
        "status": "SPEC_ONLY_AWAITING_SEPARATE_APPROVAL",
        "decision": "MINI_PANEL_DEFINED_NOT_EXECUTED",
        "candidate_count": 4,
        "new_provider_query_count_proposed": 3,
        "separate_approval_required": True,
        "approval_status": "not_granted_for_mini_panel",
        "provider_query_performed": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "raw_payload_retention_allowed": False,
    }
    (artifact / "mini_panel_approval_gate_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "mini_panel_candidates.csv").write_text(
        "panel_slot,candidate_role,reference_run,symbol,signal_date,entry_date,exit_date,entry_price,exit_price,return_pct,execution_status,provider_query_allowed_without_new_approval\n"
        "1,executed_anchor,ref,CRMD,2024-04-11,2024-04-12,2024-04-19,6.5,5.28,-0.18,already_executed_single_diagnostic,no\n"
        "2,proposed_new_query,ref,IOVA,2025-07-16,2025-07-17,2025-07-24,2.28,3.28,0.44,not_executed,no\n"
        "3,proposed_new_query,ref,CABA,2022-08-10,2022-08-11,2022-08-18,1.37,1.42,0.03,not_executed,no\n"
        "4,proposed_new_query,ref,IOVA,2025-12-17,2025-12-18,2025-12-26,2.60,2.85,0.09,not_executed,no\n",
        encoding="utf-8",
    )
    (artifact / "mini_panel_query_plan.csv").write_text(
        "field,value,status\n"
        "max_new_provider_queries,3,blocked_until_separate_approval\n"
        "databento_dataset,EQUS.MINI,defined\n"
        "databento_schema,ohlcv-1d,defined\n"
        "raw_payload_retention,false,required\n"
        "sleep_seconds_between_candidates,13,required\n"
        "output_dir,path,not_created\n"
        "trial_ledger_entries,not_created,blocked_until_separate_approval\n",
        encoding="utf-8",
    )
    (artifact / "mini_panel_stop_rules.csv").write_text(
        "stop_rule,trigger,required_action\nrate_limit,error,stop_panel\nraw_payload_needed,debug,stop_do_not_enable_raw\n",
        encoding="utf-8",
    )
    (artifact / "mini_panel_approval_checklist.csv").write_text(
        "gate,status,requirement\n"
        "separate_user_approval,not_granted,approval required\n"
        "output_directory,not_created,create later\n"
        "trial_ledger_entries,not_created,create later\n"
        "credential_presence,pass,checked\n"
        "single_candidate_limit_removed,not_implemented,extend runner\n"
        "strategy_promotion,blocked,no promotion\n",
        encoding="utf-8",
    )
    (artifact / "mini_panel_approval_gate_summary.md").write_text("# Summary\n", encoding="utf-8")
    return artifact


def test_validate_mini_panel_approval_gate_passes_valid_artifact(tmp_path: Path) -> None:
    report = validate_mini_panel_approval_gate(_write_valid_artifact(tmp_path))

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0


def test_validate_mini_panel_approval_gate_fails_if_provider_query_performed(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)
    manifest_path = artifact / "mini_panel_approval_gate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_performed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_mini_panel_approval_gate(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution" and check["status"] == "fail" for check in report["checks"])


def test_validate_mini_panel_approval_gate_fails_if_too_many_candidates(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)
    manifest_path = artifact / "mini_panel_approval_gate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_count"] = 6
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_mini_panel_approval_gate(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_candidate_count_3_to_5" and check["status"] == "fail" for check in report["checks"])


def test_validate_mini_panel_approval_gate_fails_if_query_allowed_without_approval(tmp_path: Path) -> None:
    artifact = _write_valid_artifact(tmp_path)
    text = (artifact / "mini_panel_candidates.csv").read_text(encoding="utf-8")
    (artifact / "mini_panel_candidates.csv").write_text(text.replace(",not_executed,no", ",not_executed,yes", 1), encoding="utf-8")

    report = validate_mini_panel_approval_gate(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "candidates_no_query_without_new_approval" and check["status"] == "fail" for check in report["checks"])


def test_main_exits_zero_for_valid_artifact(tmp_path: Path, capsys) -> None:
    artifact = _write_valid_artifact(tmp_path)

    code = main(["--artifact-dir", str(artifact)])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert report["status"] == "pass"
