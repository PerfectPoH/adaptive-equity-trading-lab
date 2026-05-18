from __future__ import annotations

import csv
import json
from pathlib import Path

from src.experiments.mini_panel_execution_preflight_validator import main, validate_mini_panel_execution_preflight


def _write_valid_preflight(root: Path) -> tuple[Path, Path, Path, Path]:
    gate_dir = root / "gate"
    approval_dir = root / "approval"
    output_dir = root / "MINIPANEL-PREREG-PA-SMALLCAP-001-001"
    ledger_path = root / "mini_panel_trial_ledger.csv"
    gate_dir.mkdir()
    approval_dir.mkdir()
    output_dir.mkdir()
    (gate_dir / "mini_panel_approval_gate_manifest.json").write_text(json.dumps({
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
    }), encoding="utf-8")
    (gate_dir / "mini_panel_candidates.csv").write_text(
        "panel_slot,candidate_role,reference_run,symbol,signal_date,entry_date,exit_date,entry_price,exit_price,return_pct,execution_status,provider_query_allowed_without_new_approval\n"
        "1,executed_anchor,ref,CRMD,2024-04-11,2024-04-12,2024-04-19,6.5,5.28,-0.18,already_executed_single_diagnostic,no\n"
        "2,proposed_new_query,ref,IOVA,2025-07-16,2025-07-17,2025-07-24,2.28,3.28,0.44,not_executed,no\n"
        "3,proposed_new_query,ref,CABA,2022-08-10,2022-08-11,2022-08-18,1.37,1.42,0.03,not_executed,no\n"
        "4,proposed_new_query,ref,IOVA,2025-12-17,2025-12-18,2025-12-26,2.60,2.85,0.09,not_executed,no\n",
        encoding="utf-8",
    )
    (gate_dir / "mini_panel_query_plan.csv").write_text(
        "field,value,status\nmax_new_provider_queries,3,blocked_until_separate_approval\ndatabento_dataset,EQUS.MINI,defined\ndatabento_schema,ohlcv-1d,defined\nraw_payload_retention,false,required\nsleep_seconds_between_candidates,13,required\noutput_dir,path,not_created\ntrial_ledger_entries,not_created,blocked_until_separate_approval\n",
        encoding="utf-8",
    )
    (gate_dir / "mini_panel_stop_rules.csv").write_text("stop_rule,trigger,required_action\nrate_limit,error,stop_panel\n", encoding="utf-8")
    (gate_dir / "mini_panel_approval_checklist.csv").write_text(
        "gate,status,requirement\nseparate_user_approval,not_granted,approval required\noutput_directory,not_created,create later\ntrial_ledger_entries,not_created,create later\ncredential_presence,pass,checked\nsingle_candidate_limit_removed,not_implemented,extend runner\nstrategy_promotion,blocked,no promotion\n",
        encoding="utf-8",
    )
    (gate_dir / "mini_panel_approval_gate_summary.md").write_text("# Summary\n", encoding="utf-8")
    (approval_dir / "mini_panel_explicit_approval_manifest.json").write_text(json.dumps({
        "status": "APPROVAL_GRANTED_FOR_MINI_PANEL_PREPARATION",
        "panel_id": "MINIPANEL-PREREG-PA-SMALLCAP-001-001",
        "preregistration_id": "PREREG-PA-SMALLCAP-001",
        "max_new_provider_queries": 3,
        "max_total_panel_candidates": 4,
        "provider_query_performed": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "raw_payload_retention_allowed": False,
        "output_directory_created": True,
        "trial_ledger_entries_created": True,
    }), encoding="utf-8")
    (output_dir / "mini_panel_pre_execution_manifest.json").write_text(json.dumps({
        "status": "prepared_not_executed",
        "provider_query_performed": False,
        "new_provider_query_count_planned": 3,
    }), encoding="utf-8")
    with ledger_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["panel_id", "trial_id", "candidate_symbol", "candidate_role", "stage", "executed_at", "code_commit", "artifact_dir", "trial_number", "within_budget", "result_status", "decision", "notes"])
        writer.writerow(["MINIPANEL-PREREG-PA-SMALLCAP-001-001", "MINIPANEL-TRIAL-001", "CRMD", "executed_anchor", "new_signal_research", "prepared_not_executed", "sha", str(output_dir), "001", "yes", "already_executed_single_diagnostic", "pending_execution", "pre"])
        writer.writerow(["MINIPANEL-PREREG-PA-SMALLCAP-001-001", "MINIPANEL-TRIAL-002", "IOVA", "proposed_new_query", "new_signal_research", "prepared_not_executed", "sha", str(output_dir), "002", "yes", "prepared_not_executed", "pending_execution", "pre"])
        writer.writerow(["MINIPANEL-PREREG-PA-SMALLCAP-001-001", "MINIPANEL-TRIAL-003", "CABA", "proposed_new_query", "new_signal_research", "prepared_not_executed", "sha", str(output_dir), "003", "yes", "prepared_not_executed", "pending_execution", "pre"])
        writer.writerow(["MINIPANEL-PREREG-PA-SMALLCAP-001-001", "MINIPANEL-TRIAL-004", "IOVA", "proposed_new_query", "new_signal_research", "prepared_not_executed", "sha", str(output_dir), "004", "yes", "prepared_not_executed", "pending_execution", "pre"])
    return gate_dir, approval_dir, output_dir, ledger_path


def test_validate_mini_panel_execution_preflight_passes_valid_artifacts(tmp_path: Path) -> None:
    gate_dir, approval_dir, output_dir, ledger_path = _write_valid_preflight(tmp_path)

    report = validate_mini_panel_execution_preflight(gate_dir, approval_dir, output_dir, ledger_path)

    assert report["status"] == "pass"
    assert report["provider_query_performed"] is False
    assert report["summary"]["failed"] == 0


def test_validate_mini_panel_execution_preflight_blocks_existing_execution_manifest(tmp_path: Path) -> None:
    gate_dir, approval_dir, output_dir, ledger_path = _write_valid_preflight(tmp_path)
    (output_dir / "mini_panel_execution_manifest.json").write_text("{}", encoding="utf-8")

    report = validate_mini_panel_execution_preflight(gate_dir, approval_dir, output_dir, ledger_path)

    assert report["status"] == "blocked"
    assert any(check["name"] == "execution_manifest_absent" and check["status"] == "fail" for check in report["checks"])


def test_validate_mini_panel_execution_preflight_blocks_unsafe_approval(tmp_path: Path) -> None:
    gate_dir, approval_dir, output_dir, ledger_path = _write_valid_preflight(tmp_path)
    approval_path = approval_dir / "mini_panel_explicit_approval_manifest.json"
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval["provider_query_performed"] = True
    approval_path.write_text(json.dumps(approval), encoding="utf-8")

    report = validate_mini_panel_execution_preflight(gate_dir, approval_dir, output_dir, ledger_path)

    assert report["status"] == "blocked"
    assert any(check["name"] == "approval_pre_execution_safety_flags" and check["status"] == "fail" for check in report["checks"])


def test_main_exits_zero_for_valid_preflight(tmp_path: Path, capsys) -> None:
    gate_dir, approval_dir, output_dir, ledger_path = _write_valid_preflight(tmp_path)

    code = main(["--gate-dir", str(gate_dir), "--approval-dir", str(approval_dir), "--output-dir", str(output_dir), "--ledger-path", str(ledger_path)])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert report["status"] == "pass"
