from __future__ import annotations

from pathlib import Path

from src.experiments.sec8k_direction_tape_oracle_preregistration_validator import (
    main,
    validate_sec8k_direction_tape_oracle_preregistration,
)


SPEC_DIR = Path("experiments/provider_aware_research/sec8k_direction_tape_oracle_preregistration_20260522")


def test_sec8k_direction_tape_oracle_preregistration_passes_real_spec() -> None:
    report = validate_sec8k_direction_tape_oracle_preregistration(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "SEC8K_DIRECTION_TAPE_ORACLE_PREREGISTRATION_PASS"
    assert report["summary"]["failed"] == 0


def test_sec8k_direction_tape_oracle_fails_if_promotion_allowed(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    decision = spec / "decision_rule.csv"
    decision.write_text(decision.read_text(encoding="utf-8").replace("promotion_rule,blocked", "promotion_rule,allowed"), encoding="utf-8")

    report = validate_sec8k_direction_tape_oracle_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "decision_promotion_blocked" and check["status"] == "fail" for check in report["checks"])


def test_sec8k_direction_tape_oracle_fails_if_cost_gate_weakened(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    params = spec / "parameter_freeze.csv"
    params.write_text(params.read_text(encoding="utf-8").replace("cost_model_bps,frozen,500", "cost_model_bps,frozen,50"), encoding="utf-8")

    report = validate_sec8k_direction_tape_oracle_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "parameter_cost_model_bps_locked" and check["status"] == "fail" for check in report["checks"])


def test_sec8k_direction_tape_oracle_fails_if_future_return_allowed_as_feature(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    features = spec / "allowed_features.csv"
    features.write_text(features.read_text(encoding="utf-8").replace("post_entry_return,blocked_as_feature", "post_entry_return,allowed"), encoding="utf-8")

    report = validate_sec8k_direction_tape_oracle_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "features_future_labels_blocked" and check["status"] == "fail" for check in report["checks"])


def test_sec8k_direction_tape_oracle_cli_exit_codes(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    assert main(["--spec-dir", str(spec)]) == 0

    (spec / "blocked_actions.csv").unlink()

    assert main(["--spec-dir", str(spec)]) == 1


def _copy_spec(tmp_path: Path) -> Path:
    target = tmp_path / "spec"
    target.mkdir()
    for item in SPEC_DIR.iterdir():
        target.joinpath(item.name).write_bytes(item.read_bytes())
    return target
