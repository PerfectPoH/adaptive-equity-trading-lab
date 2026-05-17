from __future__ import annotations

import json
from pathlib import Path

from src.experiments.run_artifact_validator import main, validate_run_artifacts


REQUIRED_CSVS = [
    "candidate_export.csv",
    "benchmark_report.csv",
    "portfolio_trade_log.csv",
    "portfolio_equity_curve.csv",
    "portfolio_rejections.csv",
    "portfolio_summary.csv",
]


def _valid_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    manifest = {
        "run_id": "run_test",
        "config_hash": "abc123",
        "period": {"start": "2024-01-02", "end": "2024-01-03"},
        "universe": ["AAA", "BBB"],
        "extras": {"purpose": "test"},
        "trial_accounting": {},
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    for name in REQUIRED_CSVS:
        (run_dir / name).write_text("symbol,value\nAAA,1\n", encoding="utf-8")
    (run_dir / "small_cap_backtest_report.md").write_text("# Report\n", encoding="utf-8")
    return run_dir


def test_validate_run_artifacts_passes_valid_minimal_run_dir(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)

    report = validate_run_artifacts(run_dir)

    assert report["status"] == "pass"
    assert report["run_dir"] == str(run_dir)
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "manifest_required_fields" and check["status"] == "pass" for check in report["checks"])


def test_validate_run_artifacts_fails_missing_required_file(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)
    (run_dir / "portfolio_summary.csv").unlink()

    report = validate_run_artifacts(run_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "required_file:portfolio_summary.csv" and check["status"] == "fail" for check in report["checks"])


def test_validate_run_artifacts_fails_invalid_manifest_json(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)
    (run_dir / "run_manifest.json").write_text("{bad json", encoding="utf-8")

    report = validate_run_artifacts(run_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_json" and check["status"] == "fail" for check in report["checks"])


def test_validate_run_artifacts_fails_empty_csv(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)
    (run_dir / "candidate_export.csv").write_text("", encoding="utf-8")

    report = validate_run_artifacts(run_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "csv_readable:candidate_export.csv" and check["status"] == "fail" for check in report["checks"])


def test_validate_run_artifacts_allows_empty_portfolio_rejections_csv(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)
    (run_dir / "portfolio_rejections.csv").write_text("", encoding="utf-8")

    report = validate_run_artifacts(run_dir)

    assert report["status"] == "pass"
    assert any(check["name"] == "csv_readable:portfolio_rejections.csv" and check["status"] == "pass" for check in report["checks"])


def test_validate_run_artifacts_validates_optional_property_report_json(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)
    (run_dir / "property_check_report.json").write_text(json.dumps({"trial_id": "TRIAL-NCTRL-001", "overall_status": "pass"}), encoding="utf-8")
    (run_dir / "property_check_report.md").write_text("# Property Report\n", encoding="utf-8")

    report = validate_run_artifacts(run_dir)

    assert report["status"] == "pass"
    assert any(check["name"] == "optional_json:property_check_report.json" and check["status"] == "pass" for check in report["checks"])


def test_validate_run_artifacts_fails_invalid_optional_property_report_json(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)
    (run_dir / "property_check_report.json").write_text("{bad json", encoding="utf-8")

    report = validate_run_artifacts(run_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "optional_json:property_check_report.json" and check["status"] == "fail" for check in report["checks"])


def test_run_artifact_validator_cli_exit_codes(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)

    assert main(["--run-dir", str(run_dir)]) == 0

    (run_dir / "run_manifest.json").unlink()

    assert main(["--run-dir", str(run_dir)]) == 1
