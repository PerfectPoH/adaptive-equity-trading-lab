from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.experiments.sec8k_tape_oracle_clean_run_gate_validator import (
    validate_sec8k_tape_oracle_clean_run_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/sec8k_tape_oracle_clean_run_gate_20260523")


def test_sec8k_tape_oracle_clean_run_gate_passes_real_spec() -> None:
    report = validate_sec8k_tape_oracle_clean_run_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "SEC8K_TAPE_ORACLE_CLEAN_RUN_GATE_PASS"
    assert report["summary"]["failed"] == 0


def test_sec8k_tape_oracle_clean_run_gate_fails_if_mini_panel_001_reuse_allowed(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    manifest_path = spec / "run_authorization_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["invalidated_run_usage"] = "allowed_for_calibration"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_sec8k_tape_oracle_clean_run_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "invalidated_run_usage_blocked" and check["status"] == "fail" for check in report["checks"])


def test_sec8k_tape_oracle_clean_run_gate_fails_if_provider_scope_expands(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    manifest_path = spec / "run_authorization_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["max_provider_calls"] = 51
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_sec8k_tape_oracle_clean_run_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "max_provider_calls_bounded" and check["status"] == "fail" for check in report["checks"])


def test_sec8k_tape_oracle_clean_run_gate_fails_if_cost_model_weakened(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    manifest_path = spec / "run_authorization_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["cost_model_bps"] = 50
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_sec8k_tape_oracle_clean_run_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "cost_model_worst_case_500bps" and check["status"] == "fail" for check in report["checks"])


def _copy_spec(tmp_path: Path) -> Path:
    target = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, target)
    return target
