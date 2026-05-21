from __future__ import annotations

from pathlib import Path

from src.experiments.gap_down_reversion_preregistration_validator import (
    main,
    validate_gap_down_reversion_preregistration,
)


SPEC_DIR = Path("experiments/provider_aware_research/gap_down_reversion_preregistration_spec_20260521")


def test_gap_down_reversion_preregistration_passes_real_spec() -> None:
    report = validate_gap_down_reversion_preregistration(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "GAPREV_PREREGISTRATION_SPEC_PASS"
    assert report["summary"]["failed"] == 0


def test_gap_down_reversion_preregistration_fails_if_promotion_allowed(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    decision = spec / "decision_rule.csv"
    decision.write_text(decision.read_text(encoding="utf-8").replace("promotion_rule,blocked", "promotion_rule,allowed"), encoding="utf-8")

    report = validate_gap_down_reversion_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "decision_promotion_blocked" and check["status"] == "fail" for check in report["checks"])


def test_gap_down_reversion_preregistration_fails_if_threshold_is_finalized(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    params = spec / "parameter_freeze.csv"
    params.write_text(params.read_text(encoding="utf-8").replace("gap_threshold,not_final,TBD_IN_FUTURE_SPEC", "gap_threshold,final,-0.05"), encoding="utf-8")

    report = validate_gap_down_reversion_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "parameters_operational_thresholds_not_final" and check["status"] == "fail" for check in report["checks"])


def test_gap_down_reversion_preregistration_fails_if_provider_query_unblocked(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    blocked = spec / "blocked_actions.csv"
    blocked.write_text(blocked.read_text(encoding="utf-8").replace("provider_query,blocked", "provider_query,allowed"), encoding="utf-8")

    report = validate_gap_down_reversion_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocked_actions_all_blocked" and check["status"] == "fail" for check in report["checks"])


def test_gap_down_reversion_preregistration_cli_exit_codes(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    assert main(["--spec-dir", str(spec)]) == 0

    (spec / "data_requirements.csv").unlink()

    assert main(["--spec-dir", str(spec)]) == 1


def _copy_spec(tmp_path: Path) -> Path:
    target = tmp_path / "spec"
    target.mkdir()
    for item in SPEC_DIR.iterdir():
        target.joinpath(item.name).write_bytes(item.read_bytes())
    return target
