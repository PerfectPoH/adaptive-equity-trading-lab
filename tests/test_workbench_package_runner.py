from __future__ import annotations

import json
from pathlib import Path

from dashboard.lab_dashboard_data import (
    build_controlled_backtest_preview,
    build_workbench_manifest,
    persist_workbench_strategy_package,
    validate_workbench_manifest,
)
from src.experiments.workbench_package_runner import (
    main,
    run_package_diagnostic,
    validate_package_for_diagnostic_run,
)


def _package(tmp_path: Path) -> Path:
    manifest = build_workbench_manifest(
        name="Runner package",
        template="Custom Rule Builder",
        universe="expanded local research sandbox",
        holding_period_days=21,
        cost_bps=300,
        allow_provider_query=False,
        custom_rules={"signal": "momentum_5d", "selection": "top", "entries_per_symbol": 6},
    )
    validation = validate_workbench_manifest(manifest)
    preview = build_controlled_backtest_preview(manifest, validation)
    bundle = persist_workbench_strategy_package(manifest, validation, preview, root=tmp_path)
    return Path(bundle["package_dir"])


def test_validate_package_for_diagnostic_run_accepts_safe_package(tmp_path: Path) -> None:
    package_dir = _package(tmp_path)

    validation = validate_package_for_diagnostic_run(package_dir)

    assert validation["status"] == "PASS"
    assert validation["reasons"] == []


def test_package_diagnostic_runner_writes_final_artifacts(tmp_path: Path) -> None:
    package_dir = _package(tmp_path)

    paths = run_package_diagnostic(package_dir)

    assert Path(paths["runner_audit_path"]).exists()
    assert Path(paths["trades_path"]).exists()
    assert Path(paths["summary_path"]).exists()
    assert Path(paths["final_decision_path"]).exists()
    assert Path(paths["vault_report_path"]).exists()
    decision = json.loads(Path(paths["final_decision_path"]).read_text(encoding="utf-8"))
    assert decision["promotion_allowed"] is False
    assert decision["provider_query_performed"] is False
    assert decision["runner_mode"] == "diagnostic_local_package_runner"


def test_package_runner_cli_blocks_forbidden_flags(tmp_path: Path, capsys) -> None:
    package_dir = _package(tmp_path)

    code = main(["--package-dir", str(package_dir), "--live"])

    captured = capsys.readouterr()
    assert code == 2
    assert "forbidden_flag_present" in captured.out
