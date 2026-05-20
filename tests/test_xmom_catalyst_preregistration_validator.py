from __future__ import annotations

from pathlib import Path

from src.experiments.xmom_catalyst_preregistration_validator import (
    main,
    validate_xmom_catalyst_preregistration,
)


def test_xmom_catalyst_preregistration_validator_passes_real_spec() -> None:
    spec_dir = Path("experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520")

    report = validate_xmom_catalyst_preregistration(spec_dir)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "SPEC_VALIDATION_PASS"
    assert report["summary"]["failed"] == 0


def test_xmom_catalyst_preregistration_validator_fails_if_promotion_allowed(tmp_path: Path) -> None:
    spec_dir = _copy_spec(tmp_path)
    decision = spec_dir / "decision_rule.csv"
    decision.write_text(
        decision.read_text(encoding="utf-8").replace("promotion_rule,blocked", "promotion_rule,allowed"),
        encoding="utf-8",
    )

    report = validate_xmom_catalyst_preregistration(spec_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "decision_promotion_blocked" and check["status"] == "fail" for check in report["checks"])


def test_xmom_catalyst_preregistration_validator_fails_if_markov_not_blocked(tmp_path: Path) -> None:
    spec_dir = _copy_spec(tmp_path)
    blocked = spec_dir / "blocked_actions.csv"
    blocked.write_text(blocked.read_text(encoding="utf-8").replace("markov_hmm_patch,blocked", "markov_hmm_patch,allowed"), encoding="utf-8")

    report = validate_xmom_catalyst_preregistration(spec_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocked_actions_all_blocked" and check["status"] == "fail" for check in report["checks"])


def test_xmom_catalyst_preregistration_validator_cli_exit_codes(tmp_path: Path) -> None:
    spec_dir = _copy_spec(tmp_path)
    assert main(["--spec-dir", str(spec_dir)]) == 0

    (spec_dir / "source_hierarchy.csv").unlink()

    assert main(["--spec-dir", str(spec_dir)]) == 1


def _copy_spec(tmp_path: Path) -> Path:
    source = Path("experiments/provider_aware_research/xmom_catalyst_preregistration_spec_20260520")
    target = tmp_path / "spec"
    target.mkdir()
    for item in source.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
