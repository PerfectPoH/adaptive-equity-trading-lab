from __future__ import annotations

import json

from src.experiments.provider_sensitivity_diagnostic_runner import build_dry_run_plan, main


def test_build_dry_run_plan_is_non_executing() -> None:
    report = build_dry_run_plan("PREREG-PA-SMALLCAP-001", "TRIAL-001", "future-output")

    assert report["status"] == "dry_run_only"
    assert report["execution_performed"] is False
    assert report["provider_query_performed"] is False
    assert report["backtest_performed"] is False
    assert report["strategy_promotion_performed"] is False
    assert report["preregistration_id"] == "PREREG-PA-SMALLCAP-001"
    assert "--all-symbols" in report["blocked_actions"]


def test_main_requires_dry_run(capsys) -> None:
    code = main([
        "--preregistration-id",
        "PREREG-PA-SMALLCAP-001",
        "--trial-id",
        "TRIAL-001",
        "--output-dir",
        "future-output",
    ])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 2
    assert report["status"] == "blocked"
    assert report["error"] == "dry_run_required"
    assert report["provider_query_performed"] is False


def test_main_blocks_execute(capsys) -> None:
    code = main([
        "--dry-run",
        "--execute",
        "--preregistration-id",
        "PREREG-PA-SMALLCAP-001",
        "--trial-id",
        "TRIAL-001",
        "--output-dir",
        "future-output",
    ])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 2
    assert report["error"] == "execute_forbidden"
    assert report["execution_performed"] is False


def test_main_blocks_forbidden_flags(capsys) -> None:
    code = main([
        "--dry-run",
        "--preregistration-id",
        "PREREG-PA-SMALLCAP-001",
        "--trial-id",
        "TRIAL-001",
        "--output-dir",
        "future-output",
        "--sweep",
    ])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 2
    assert report["error"] == "forbidden_flags_present"
    assert report["backtest_performed"] is False


def test_main_dry_run_returns_plan(capsys) -> None:
    code = main([
        "--dry-run",
        "--preregistration-id",
        "PREREG-PA-SMALLCAP-001",
        "--trial-id",
        "TRIAL-001",
        "--output-dir",
        "future-output",
    ])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert report["status"] == "dry_run_only"
    assert report["execution_performed"] is False
    assert report["planned_output_dir"] == "future-output"
