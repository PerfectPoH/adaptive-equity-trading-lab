from __future__ import annotations

import json
from pathlib import Path

from src.experiments.xmom_catalyst_implementation_gate_validator import (
    main,
    validate_xmom_catalyst_implementation_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520")


def test_xmom_catalyst_implementation_gate_validator_passes_real_spec() -> None:
    report = validate_xmom_catalyst_implementation_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "IMPLEMENTATION_GATE_SPEC_PASS"
    assert report["summary"]["failed"] == 0


def test_xmom_catalyst_implementation_gate_validator_fails_if_oos_enabled(tmp_path: Path) -> None:
    spec_dir = _copy_spec(tmp_path)
    manifest_path = spec_dir / "implementation_gate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["no_oos_execution"] = False
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_catalyst_implementation_gate(spec_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_flags" and check["status"] == "fail" for check in report["checks"])


def test_xmom_catalyst_implementation_gate_validator_fails_if_threshold_executable(tmp_path: Path) -> None:
    spec_dir = _copy_spec(tmp_path)
    policy = spec_dir / "blind_threshold_policy.csv"
    policy.write_text(
        policy.read_text(encoding="utf-8").replace(
            "volume_decay_rate,not_final,ECDF_percentile_from_in_sample_features_only,blind_to_returns,not_executable",
            "volume_decay_rate,final,ECDF_percentile_from_in_sample_features_only,visible_to_returns,executable",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_catalyst_implementation_gate(spec_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "threshold_policy_candidates_not_final" and check["status"] == "fail" for check in report["checks"])
    assert any(check["name"] == "threshold_policy_candidates_blind_to_returns" and check["status"] == "fail" for check in report["checks"])
    assert any(check["name"] == "threshold_policy_candidates_not_executable" and check["status"] == "fail" for check in report["checks"])


def test_xmom_catalyst_implementation_gate_validator_fails_if_dsr_threshold_weakened(tmp_path: Path) -> None:
    spec_dir = _copy_spec(tmp_path)
    manifest_path = spec_dir / "implementation_gate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["dsr_minimum_confidence"] = 0.8
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_catalyst_implementation_gate(spec_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_dsr_threshold_at_least_095" and check["status"] == "fail" for check in report["checks"])


def test_xmom_catalyst_implementation_gate_validator_cli_exit_codes(tmp_path: Path) -> None:
    spec_dir = _copy_spec(tmp_path)
    assert main(["--spec-dir", str(spec_dir)]) == 0

    (spec_dir / "blocked_actions.csv").unlink()

    assert main(["--spec-dir", str(spec_dir)]) == 1


def _copy_spec(tmp_path: Path) -> Path:
    target = tmp_path / "implementation_gate_spec"
    target.mkdir()
    for item in SPEC_DIR.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
