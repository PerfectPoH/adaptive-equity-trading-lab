from __future__ import annotations

import csv
from pathlib import Path

from src.experiments.outlier_resistant_diagnostic_harness import (
    diagnose_trade_log,
    run_outlier_resistant_diagnostic_harness,
    score_robustness,
    validate_outlier_resistant_diagnostic_harness,
    verdict_from_diagnostics,
)


def test_verdict_flags_outlier_dependence() -> None:
    verdict = verdict_from_diagnostics(
        trade_count=30,
        total_pnl=100.0,
        median_pnl=5.0,
        pnl_ex_top3=-10.0,
        sign_flip_ex_top3=True,
    )

    assert verdict == "OUTLIER_DEPENDENT_NO_PROMOTION"


def test_robust_score_rewards_positive_median_and_ex_top3() -> None:
    weak = score_robustness(
        trade_count=30,
        total_pnl=100.0,
        median_pnl=-1.0,
        pnl_ex_top3=-50.0,
        sign_flip_ex_top3=True,
        top3_contribution_pct=150.0,
    )
    strong = score_robustness(
        trade_count=30,
        total_pnl=100.0,
        median_pnl=2.0,
        pnl_ex_top3=40.0,
        sign_flip_ex_top3=False,
        top3_contribution_pct=30.0,
    )

    assert strong > weak


def test_diagnose_trade_log_detects_sign_flip(tmp_path: Path) -> None:
    path = tmp_path / "portfolio_trade_log.csv"
    _write_trade_log(path, [100.0, 80.0, 70.0, -40.0, -50.0, -60.0])

    result = diagnose_trade_log("TEST", "Synthetic", path)

    assert result["total_pnl"] == 100.0
    assert result["pnl_excluding_top3"] == -150.0
    assert result["sign_flip_excluding_top3"] is True
    assert result["diagnostic_verdict"] == "INSUFFICIENT_TRADES_DIAGNOSTIC_ONLY"


def test_outlier_resistant_harness_real_artifact_passes_validation() -> None:
    decision = run_outlier_resistant_diagnostic_harness()
    report = validate_outlier_resistant_diagnostic_harness()

    assert decision["decision"] == "OUTLIER_DIAGNOSTIC_COMPLETE_NO_EXECUTION"
    assert decision["backtest_performed"] is False
    assert report["status"] == "pass"


def test_outlier_resistant_harness_fails_if_backtest_marked_performed(tmp_path: Path) -> None:
    run_outlier_resistant_diagnostic_harness()
    target = _copy_harness(tmp_path)
    manifest_path = target / "diagnostic_manifest.json"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace('"backtest_performed": false', '"backtest_performed": true'),
        encoding="utf-8",
    )

    report = validate_outlier_resistant_diagnostic_harness(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution" and check["status"] == "fail" for check in report["checks"])


def test_outlier_resistant_harness_fails_if_panel_not_ranked(tmp_path: Path) -> None:
    run_outlier_resistant_diagnostic_harness()
    target = _copy_harness(tmp_path)
    panel_path = target / "diagnostic_panel.csv"
    rows = _read_rows(panel_path)
    rows[0]["robustness_score"], rows[-1]["robustness_score"] = rows[-1]["robustness_score"], rows[0]["robustness_score"]
    _write_rows(panel_path, rows)

    report = validate_outlier_resistant_diagnostic_harness(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "scores_ranked_descending" and check["status"] == "fail" for check in report["checks"])


def _write_trade_log(path: Path, pnls: list[float]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["symbol", "pnl", "return_pct"])
        writer.writeheader()
        for index, pnl in enumerate(pnls):
            writer.writerow({"symbol": f"S{index}", "pnl": pnl, "return_pct": pnl / 1000})


def _copy_harness(tmp_path: Path) -> Path:
    source = Path("experiments/provider_aware_research/outlier_resistant_diagnostic_20260521")
    target = tmp_path / "harness"
    target.mkdir()
    for item in source.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
