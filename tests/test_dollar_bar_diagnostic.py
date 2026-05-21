from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments.dollar_bar_diagnostic import (
    build_dollar_bars,
    diagnose_bars_file,
    distribution_stats,
    run_dollar_bar_diagnostic,
    validate_dollar_bar_diagnostic,
)


def test_build_dollar_bars_collapses_until_target_dollar_reached() -> None:
    frame = pd.DataFrame(
        [
            {"timestamp": "t1", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 10, "dollar_value": 100},
            {"timestamp": "t2", "open": 10, "high": 12, "low": 10, "close": 11, "volume": 5, "dollar_value": 55},
            {"timestamp": "t3", "open": 11, "high": 11, "low": 8, "close": 9, "volume": 20, "dollar_value": 180},
        ]
    )

    bars = build_dollar_bars(frame, target_dollar=150)

    assert len(bars) == 2
    assert bars[0]["open"] == 10
    assert bars[0]["high"] == 12
    assert bars[0]["close"] == 11
    assert bars[0]["volume"] == 15


def test_distribution_stats_uses_pearson_kurtosis_convention() -> None:
    stats = distribution_stats([-1, 0, 1])

    assert stats["pearson_kurtosis"] > 0
    assert "outlier_rate_3sigma" in stats


def test_diagnose_bars_file_outputs_diagnostic_only_verdict(tmp_path: Path) -> None:
    path = tmp_path / "bars.csv"
    _write_bars(path)

    row = diagnose_bars_file(path)

    assert row["status"] == "evaluated"
    assert row["target_dollar_bucket"] > 0
    assert "TRADE" not in row["diagnostic_verdict"]
    assert "PROMOTION" not in row["diagnostic_verdict"]


def test_dollar_bar_diagnostic_real_artifact_passes_validation() -> None:
    decision = run_dollar_bar_diagnostic()
    report = validate_dollar_bar_diagnostic()

    assert decision["decision"] == "DOLLAR_BAR_DIAGNOSTIC_COMPLETE_NO_STRATEGY"
    assert decision["backtest_performed"] is False
    assert report["status"] == "pass"


def test_dollar_bar_diagnostic_fails_if_backtest_marked_performed(tmp_path: Path) -> None:
    run_dollar_bar_diagnostic()
    target = _copy_diag(tmp_path)
    manifest_path = target / "diagnostic_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_performed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_dollar_bar_diagnostic(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution" and check["status"] == "fail" for check in report["checks"])


def test_dollar_bar_diagnostic_fails_if_bucket_selection_from_pnl_allowed(tmp_path: Path) -> None:
    run_dollar_bar_diagnostic()
    target = _copy_diag(tmp_path)
    blocked_path = target / "blocked_actions.csv"
    blocked_path.write_text(
        blocked_path.read_text(encoding="utf-8").replace("select_bucket_from_pnl,blocked", "select_bucket_from_pnl,allowed"),
        encoding="utf-8",
    )

    report = validate_dollar_bar_diagnostic(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocked_actions_all_blocked" and check["status"] == "fail" for check in report["checks"])


def _write_bars(path: Path) -> None:
    pd.DataFrame(
        [
            {"symbol": "TEST", "timestamp": f"2026-05-21T14:{30 + index:02d}:00Z", "open": 10 + index * 0.01, "high": 10.2 + index * 0.01, "low": 9.9, "close": 10 + index * 0.02, "volume": 100 + index * 10}
            for index in range(12)
        ]
    ).to_csv(path, index=False)


def _copy_diag(tmp_path: Path) -> Path:
    source = Path("experiments/provider_aware_research/dollar_bar_diagnostic_20260521")
    target = tmp_path / "diag"
    target.mkdir()
    for item in source.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
