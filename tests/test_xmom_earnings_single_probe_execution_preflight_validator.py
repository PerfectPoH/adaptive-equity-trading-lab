from __future__ import annotations

import csv
import json
from pathlib import Path

from src.experiments.xmom_earnings_single_probe_execution_preflight_validator import (
    main,
    validate_xmom_earnings_single_probe_execution_preflight,
)


SOURCE_APPROVAL_GATE = Path("experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521")


def test_single_probe_execution_preflight_blocks_current_post_execution_artifact() -> None:
    report = validate_xmom_earnings_single_probe_execution_preflight()

    assert report["status"] == "blocked"
    assert report["provider_query_performed"] is False
    assert report["network_call_performed"] is False
    assert report["extractor_implemented"] is False
    assert any(check["name"] == "execution_manifest_absent" and check["status"] == "fail" for check in report["checks"])


def test_single_probe_execution_preflight_passes_valid_prepared_artifacts(tmp_path: Path) -> None:
    approval_gate, explicit_approval, output_dir, ledger_path = _write_valid_preflight(tmp_path)

    report = validate_xmom_earnings_single_probe_execution_preflight(
        approval_gate_dir=approval_gate,
        explicit_approval_dir=explicit_approval,
        output_dir=output_dir,
        ledger_path=ledger_path,
    )

    assert report["status"] == "pass"
    assert report["decision"] == "XMOM_EARNINGS_SINGLE_PROBE_PREFLIGHT_PASS_READY_FOR_APPROVED_EXECUTION"
    assert report["provider_query_performed"] is False
    assert report["summary"]["failed"] == 0


def test_single_probe_execution_preflight_blocks_existing_execution_manifest(tmp_path: Path) -> None:
    approval_gate, explicit_approval, output_dir, ledger_path = _write_valid_preflight(tmp_path)
    (output_dir / "single_probe_execution_manifest.json").write_text("{}", encoding="utf-8")

    report = validate_xmom_earnings_single_probe_execution_preflight(approval_gate, explicit_approval, output_dir, ledger_path)

    assert report["status"] == "blocked"
    assert any(check["name"] == "execution_manifest_absent" and check["status"] == "fail" for check in report["checks"])


def test_single_probe_execution_preflight_blocks_raw_payload_retention(tmp_path: Path) -> None:
    approval_gate, explicit_approval, output_dir, ledger_path = _write_valid_preflight(tmp_path)
    approval_path = explicit_approval / "single_probe_explicit_approval_manifest.json"
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval["raw_payload_retention_allowed"] = True
    approval_path.write_text(json.dumps(approval), encoding="utf-8")

    report = validate_xmom_earnings_single_probe_execution_preflight(approval_gate, explicit_approval, output_dir, ledger_path)

    assert report["status"] == "blocked"
    assert any(check["name"] == "explicit_approval_pre_execution_safety_flags" and check["status"] == "fail" for check in report["checks"])


def test_single_probe_execution_preflight_blocks_ledger_mismatch(tmp_path: Path) -> None:
    approval_gate, explicit_approval, output_dir, ledger_path = _write_valid_preflight(tmp_path)
    text = ledger_path.read_text(encoding="utf-8").replace(",CRMD,", ",AEHR,")
    ledger_path.write_text(text, encoding="utf-8")

    report = validate_xmom_earnings_single_probe_execution_preflight(approval_gate, explicit_approval, output_dir, ledger_path)

    assert report["status"] == "blocked"
    assert any(check["name"] == "ledger_identity_matches_approval" and check["status"] == "fail" for check in report["checks"])


def test_single_probe_execution_preflight_cli_exit_codes(tmp_path: Path, capsys) -> None:
    approval_gate, explicit_approval, output_dir, ledger_path = _write_valid_preflight(tmp_path)

    code = main([
        "--approval-gate-dir",
        str(approval_gate),
        "--explicit-approval-dir",
        str(explicit_approval),
        "--output-dir",
        str(output_dir),
        "--ledger-path",
        str(ledger_path),
    ])
    report = json.loads(capsys.readouterr().out)

    assert code == 0
    assert report["status"] == "pass"
    assert main([]) == 1


def _write_valid_preflight(root: Path) -> tuple[Path, Path, Path, Path]:
    approval_gate = root / "approval_gate"
    explicit_approval = root / "explicit_approval"
    output_dir = root / "XMOM-EARNINGS-SINGLE-PROBE-001"
    ledger_path = root / "xmom_earnings_single_probe_trial_ledger.csv"
    approval_gate.mkdir()
    explicit_approval.mkdir()
    output_dir.mkdir()
    for item in SOURCE_APPROVAL_GATE.iterdir():
        approval_gate.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    (explicit_approval / "single_probe_explicit_approval_manifest.json").write_text(json.dumps({
        "status": "APPROVAL_GRANTED_FOR_SINGLE_PROBE_PREPARATION",
        "gate_id": "EARNINGS-SINGLE-PROBE-XMOM-CATALYST-001",
        "trial_id": "TRIAL-XMOM-CATALYST-001",
        "provider": "intrinio",
        "symbol": "CRMD",
        "endpoint": "earnings_calendar_or_equivalent",
        "output_id": "XMOM-EARNINGS-SINGLE-PROBE-001",
        "output_directory_created": True,
        "trial_ledger_entry_created": True,
        "max_provider_calls": 1,
        "max_provider_count": 1,
        "max_symbol_count": 1,
        "max_endpoint_count": 1,
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retention_allowed": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
    }), encoding="utf-8")
    (output_dir / "single_probe_pre_execution_manifest.json").write_text(json.dumps({
        "status": "prepared_not_executed",
        "gate_id": "EARNINGS-SINGLE-PROBE-XMOM-CATALYST-001",
        "trial_id": "TRIAL-XMOM-CATALYST-001",
        "provider": "intrinio",
        "symbol": "CRMD",
        "endpoint": "earnings_calendar_or_equivalent",
        "provider_query_performed": False,
        "network_call_performed": False,
        "max_provider_calls": 1,
        "raw_payload_retention_allowed": False,
    }), encoding="utf-8")
    with ledger_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gate_id", "trial_id", "provider", "symbol", "endpoint", "stage", "prepared_at", "artifact_dir", "trial_number", "within_budget", "result_status", "decision", "notes"])
        writer.writerow([
            "EARNINGS-SINGLE-PROBE-XMOM-CATALYST-001",
            "TRIAL-XMOM-CATALYST-001",
            "intrinio",
            "CRMD",
            "earnings_calendar_or_equivalent",
            "earnings_metadata_probe",
            "prepared_not_executed",
            str(output_dir),
            "1",
            "yes",
            "prepared_not_executed",
            "pending_execution",
            "pre_execution_entry",
        ])
    return approval_gate, explicit_approval, output_dir, ledger_path
