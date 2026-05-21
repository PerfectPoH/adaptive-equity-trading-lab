from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments.dollarbar_transform_preregistration_validator import (
    SPEC_DIR,
    create_dollarbar_transform_preregistration,
    validate_dollarbar_transform_preregistration,
)


def test_dollarbar_transform_preregistration_passes_real_spec() -> None:
    report = create_dollarbar_transform_preregistration()

    assert report["status"] == "pass"
    assert report["gate_decision"] == "DOLLARBAR_TRANSFORM_PREREGISTRATION_PASS"


def test_preregistration_fails_if_pnl_is_allowed(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    allowed = pd.read_csv(spec / "allowed_metrics.csv")
    allowed.loc[len(allowed)] = ["pnl", "allowed", "bad"]
    allowed.to_csv(spec / "allowed_metrics.csv", index=False)

    report = validate_dollarbar_transform_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "allowed_forbidden_disjoint" and check["status"] == "fail" for check in report["checks"])


def test_preregistration_fails_if_strategy_backtest_unblocked(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    blocked = pd.read_csv(spec / "blocked_actions.csv")
    blocked.loc[blocked["action"] == "strategy_backtest", "status"] = "allowed"
    blocked.to_csv(spec / "blocked_actions.csv", index=False)

    report = validate_dollarbar_transform_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocked_actions_all_blocked" and check["status"] == "fail" for check in report["checks"])


def test_preregistration_fails_if_transform_policy_mentions_pnl(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    transforms = pd.read_csv(spec / "transform_candidates.csv")
    transforms.loc[0, "parameter_policy"] = "optimize_for_pnl"
    transforms.to_csv(spec / "transform_candidates.csv", index=False)

    report = validate_dollarbar_transform_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "transform_parameters_not_pnl_optimized" and check["status"] == "fail" for check in report["checks"])


def test_preregistration_fails_if_manifest_records_execution(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    manifest = (spec / "transform_manifest.json").read_text(encoding="utf-8")
    (spec / "transform_manifest.json").write_text(manifest.replace('"backtest_performed": false', '"backtest_performed": true'), encoding="utf-8")

    report = validate_dollarbar_transform_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution" and check["status"] == "fail" for check in report["checks"])


def _copy_spec(tmp_path: Path) -> Path:
    create_dollarbar_transform_preregistration()
    target = tmp_path / "spec"
    target.mkdir()
    for item in SPEC_DIR.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
