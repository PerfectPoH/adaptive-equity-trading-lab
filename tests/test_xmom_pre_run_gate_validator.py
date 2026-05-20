from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.experiments.xmom_pre_run_gate_validator import main, validate_xmom_pre_run_gate


def _write_gate(tmp_path: Path, *, prepared: bool) -> Path:
    prereg = tmp_path / "prereg"
    prereg.mkdir(parents=True)
    parameter_text = "parameter_name,status,allowed_values,change_after_execution_policy,notes\nimpact_coefficient_bps,final,500,new_preregistration_required,x\n"
    feature_text = "feature_name,status,allowed_before_execution,change_after_execution_policy,notes\nmomentum_3m,final,yes,new_preregistration_required,x\n"
    (prereg / "parameter_freeze.csv").write_text(parameter_text, encoding="utf-8")
    (prereg / "feature_freeze.csv").write_text(feature_text, encoding="utf-8")
    expected_hash = hashlib.sha256((parameter_text + "\n" + feature_text).encode("utf-8")).hexdigest()

    data_dir = tmp_path / "data_inputs"
    data_dir.mkdir()
    (data_dir / "dataset.csv").write_text("x\n1\n", encoding="utf-8")

    ledger = tmp_path / "trial_ledger.csv"
    ledger_status = "prepared_not_executed" if prepared else "completed"
    ledger.write_text(
        "trial_id,preregistration_id,stage,executed_at,code_commit,artifact_dir,trial_number,within_budget,result_status,decision,notes\n"
        f"TRIAL-XMOM-001,PREREG-XMOM-001,new_signal_research,prepared_not_executed,abc,x,1,yes,{ledger_status},pending,x\n",
        encoding="utf-8",
    )

    gate = tmp_path / "gate"
    gate.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "XMOM_PRE_RUN_GATE_DEFINED_NOT_EXECUTED",
        "scope": "x",
        "trial_id": "TRIAL-XMOM-001",
        "preregistration_id": "PREREG-XMOM-001",
        "research_stage": "new_signal_research",
        "required_checks": ["databento_data_exists", "config_hash_match", "ledger_status_is_prepared"],
        "required_artifacts": ["pre_run_gate_checklist.csv", "pre_run_gate_summary.md"],
        "fail_closed_policy": True,
        "on_failure_action": "EXIT_1_BLOCK_EXECUTION",
        "no_provider_query": True,
        "no_backtest": True,
        "no_strategy_promotion": True,
        "execution_status": "not_executed",
        "linked_preregistration_dir": str(prereg),
        "expected_trial_config_hash": expected_hash,
    }
    (gate / "pre_run_gate_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (gate / "pre_run_gate_checklist.csv").write_text(
        "check,required,current_status,pass_condition,failure_action,evidence_source\n"
        f"databento_data_exists,yes,not_run,x,EXIT_1_BLOCK_EXECUTION,{data_dir}\n"
        "config_hash_match,yes,not_run,x,EXIT_1_BLOCK_EXECUTION,run_manifest_config_hash_vs_prereg_artifact\n"
        f"ledger_status_is_prepared,yes,not_run,x,EXIT_1_BLOCK_EXECUTION,{ledger}\n",
        encoding="utf-8",
    )
    (gate / "pre_run_gate_summary.md").write_text("# summary\n", encoding="utf-8")
    return gate


def test_validate_xmom_pre_run_gate_passes_when_all_runtime_checks_pass(tmp_path: Path) -> None:
    gate = _write_gate(tmp_path, prepared=True)
    report = validate_xmom_pre_run_gate(gate)
    assert report["status"] == "pass"
    assert report["gate_decision"] == "PASS_READY_TO_EXECUTE"


def test_validate_xmom_pre_run_gate_blocks_when_ledger_not_prepared(tmp_path: Path) -> None:
    gate = _write_gate(tmp_path, prepared=False)
    report = validate_xmom_pre_run_gate(gate)
    assert report["status"] == "fail"
    assert report["gate_decision"] == "BLOCKED_EXIT_1"
    assert any(check["name"] == "runtime_ledger_status_is_prepared" and check["status"] == "fail" for check in report["checks"])


def test_xmom_pre_run_gate_validator_cli_exit_codes(tmp_path: Path) -> None:
    gate = _write_gate(tmp_path, prepared=True)
    assert main(["--gate-dir", str(gate)]) == 0
    bad_gate = _write_gate(tmp_path / "other", prepared=False)
    assert main(["--gate-dir", str(bad_gate)]) == 1
