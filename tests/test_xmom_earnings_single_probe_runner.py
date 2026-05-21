from __future__ import annotations

import json
from pathlib import Path

from src.experiments.xmom_earnings_single_probe_runner import (
    build_dry_run_plan,
    build_real_run_block_report,
    main,
)


ARTIFACT_DIR = Path("experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521")


def test_single_probe_runner_dry_run_never_executes() -> None:
    report = build_dry_run_plan(approval_dir=ARTIFACT_DIR)

    assert report["status"] == "dry_run_only"
    assert report["approval_gate_decision"] == "EARNINGS_SINGLE_PROBE_APPROVAL_SPEC_PASS"
    assert report["execution_performed"] is False
    assert report["provider_query_performed"] is False
    assert report["network_call_performed"] is False
    assert report["raw_payload_retained"] is False
    assert report["extractor_implemented"] is False


def test_single_probe_runner_real_run_blocks_current_artifact() -> None:
    report = build_real_run_block_report(approval_dir=ARTIFACT_DIR)

    assert report["status"] == "blocked"
    assert report["error"] == "single_probe_real_run_gates_unresolved"
    assert report["approval_status"] == "not_granted"
    assert "explicit_single_probe_approval_granted" in report["missing_gates"]
    assert "provider_selected" in report["missing_gates"]
    assert "symbol_selected" in report["missing_gates"]
    assert report["provider_query_performed"] is False


def test_single_probe_runner_real_run_still_blocks_if_acknowledged_without_manifest_grant() -> None:
    report = build_real_run_block_report(
        approval_dir=ARTIFACT_DIR,
        provider="intrinio",
        symbol="CRMD",
        output_dir="experiments/provider_aware_research/execution_outputs/XMOM-EARNINGS-SINGLE-PROBE-001",
        acknowledged_gates={
            "explicit_single_probe_approval_granted",
            "provider_selected",
            "symbol_selected",
            "endpoint_selected",
            "immutable_output_directory_created",
            "trial_ledger_entry_created",
            "raw_payload_retention_blocked",
        },
    )

    assert report["status"] == "blocked"
    assert report["approval_status"] == "not_granted"
    assert "explicit_single_probe_approval_granted" in report["missing_gates"]
    assert report["provider_query_performed"] is False


def test_single_probe_runner_blocks_if_raw_payload_retention_unlocked(tmp_path: Path) -> None:
    artifact = _copy_artifact(tmp_path)
    manifest_path = artifact / "single_probe_approval_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["approval_status"] = "granted"
    manifest["raw_payload_retention_allowed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = build_real_run_block_report(
        approval_dir=artifact,
        provider="intrinio",
        symbol="CRMD",
        output_dir="experiments/provider_aware_research/execution_outputs/XMOM-EARNINGS-SINGLE-PROBE-001",
        acknowledged_gates={"trial_ledger_entry_created"},
    )

    assert report["status"] == "blocked"
    assert "raw_payload_retention_blocked" in report["missing_gates"]
    assert report["raw_payload_retained"] is False


def test_single_probe_runner_cli_exit_codes() -> None:
    assert main(["--dry-run", "--approval-dir", str(ARTIFACT_DIR)]) == 0
    assert main(["--real-run", "--approval-dir", str(ARTIFACT_DIR)]) == 2
    assert main(["--dry-run", "--approval-dir", str(ARTIFACT_DIR), "--execute"]) == 2
    assert main(["--dry-run", "--approval-dir", str(ARTIFACT_DIR), "--live"]) == 2


def _copy_artifact(tmp_path: Path) -> Path:
    target = tmp_path / "single_probe_approval"
    target.mkdir()
    for item in ARTIFACT_DIR.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
