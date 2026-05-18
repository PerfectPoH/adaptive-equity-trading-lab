from __future__ import annotations

import json
from pathlib import Path

from src.experiments.provider_sensitivity_diagnostic_runner import build_dry_run_plan, build_real_run_block_report, main, run_approved_single_diagnostic


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
    assert report["error"] == "mode_required"
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


def test_build_real_run_block_report_never_executes() -> None:
    report = build_real_run_block_report(
        "PREREG-PA-SMALLCAP-001",
        "TRIAL-001",
        "future-output",
        {"explicit_user_execution_approval"},
    )

    assert report["status"] == "blocked"
    assert report["error"] == "real_run_gates_unresolved"
    assert report["execution_performed"] is False
    assert report["provider_query_performed"] is False
    assert "trial_ledger_entry_created" in report["missing_gates"]
    assert "explicit_user_execution_approval" in report["acknowledged_gates"]


def test_main_real_run_reports_blocked_gates(capsys) -> None:
    code = main([
        "--real-run",
        "--acknowledge-gate",
        "explicit_user_execution_approval",
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
    assert report["execution_performed"] is False
    assert report["provider_query_performed"] is False
    assert "immutable_output_directory_created" in report["missing_gates"]


def test_run_approved_single_diagnostic_uses_one_candidate_without_raw_retention(tmp_path: Path) -> None:
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    (spec_dir / "candidates.csv").write_text(
        "reference_run,symbol,signal_date,entry_date,exit_date,entry_price,exit_price,return_pct\n"
        "ref,ABCD,2024-01-02,2024-01-03,2024-01-04,10,11,0.1\n",
        encoding="utf-8",
    )
    env_file = tmp_path / ".env"
    env_file.write_text("DATABENTO_API_KEY=databento-secret\nPOLYGON_API_KEY=polygon-secret\n", encoding="utf-8")
    output_dir = tmp_path / "RUN-PREREG-PA-SMALLCAP-001-001"
    output_dir.mkdir()
    ledger_path = tmp_path / "ledger.csv"

    def fake_checker(candidate: dict[str, str], databento_key: str, polygon_key: str, *, skip_polygon: bool) -> dict[str, object]:
        assert databento_key == "databento-secret"
        assert polygon_key == "polygon-secret"
        return {
            "reference_run": candidate["reference_run"],
            "symbol": candidate["symbol"],
            "databento_status": "pass",
            "polygon_status": "OK",
            "sensitivity_class": "provider_stable_for_selected_fields",
            "raw_response_path": "RAW_RESPONSE_RETENTION_NOT_ENABLED",
        }

    report = run_approved_single_diagnostic(
        "PREREG-PA-SMALLCAP-001",
        "TRIAL-001",
        output_dir,
        spec_dir=spec_dir,
        candidates_file="candidates.csv",
        env_file=env_file,
        ledger_path=ledger_path,
        candidate_checker=fake_checker,
    )

    assert report["status"] == "completed"
    assert report["candidate_count"] == 1
    assert report["provider_query_performed"] is True
    assert report["backtest_performed"] is False
    assert report["strategy_promotion_performed"] is False
    assert report["raw_payload_retained"] is False
    assert (output_dir / "execution_manifest.json").exists()
    assert (output_dir / "provider_sensitivity_single_result.csv").exists()
    assert "completed" in ledger_path.read_text(encoding="utf-8")
    assert "databento-secret" not in (output_dir / "diagnostic_summary.json").read_text(encoding="utf-8")
    assert "polygon-secret" not in (output_dir / "diagnostic_summary.json").read_text(encoding="utf-8")


def test_run_approved_single_diagnostic_blocks_wrong_identity(tmp_path: Path) -> None:
    output_dir = tmp_path / "RUN-PREREG-PA-SMALLCAP-001-001"
    output_dir.mkdir()

    report = run_approved_single_diagnostic("OTHER", "TRIAL-001", output_dir)

    assert report["status"] == "blocked"
    assert report["error"] == "unexpected_run_identity"
    assert report["provider_query_performed"] is False
