from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments.dollarbar_transform_validator import (
    build_ema_dollar_bars,
    run_dollarbar_transform_validation,
    transform_verdict,
    validate_dollarbar_transform_validation,
    validate_transform_file,
)


def test_build_ema_dollar_bars_uses_predeclared_span() -> None:
    frame = pd.DataFrame(
        [
            {"timestamp": f"t{index}", "open": 10, "high": 11, "low": 9, "close": 10 + index * 0.01, "volume": 100 + index, "dollar_value": (10 + index * 0.01) * (100 + index)}
            for index in range(30)
        ]
    )

    bars = build_ema_dollar_bars(frame, span=20)

    assert len(bars) > 0
    assert all(bar["target_dollar"] > 0 for bar in bars)


def test_transform_verdict_requires_sample_gate() -> None:
    assert transform_verdict(stability_delta=10.0, sample_ratio=0.19) == "FAIL_SAMPLE_GATE"
    assert transform_verdict(stability_delta=10.0, sample_ratio=0.20) == "PASS_DISTRIBUTION_STABILITY_GATE"
    assert transform_verdict(stability_delta=-1.0, sample_ratio=0.50) == "FAIL_DISTRIBUTION_STABILITY_GATE"


def test_validate_transform_file_outputs_no_forbidden_performance_fields(tmp_path: Path) -> None:
    path = tmp_path / "bars.csv"
    _write_bars(path)

    row = validate_transform_file("PANEL", path)

    assert "pnl" not in row
    assert "win_rate" not in row
    assert "strategy_return" not in row
    assert row["ema_span"] == 20


def test_dollarbar_transform_validation_real_artifact_passes_validation() -> None:
    decision = run_dollarbar_transform_validation()
    report = validate_dollarbar_transform_validation()

    assert decision["backtest_performed"] is False
    assert decision["provider_query_performed"] is False
    assert report["status"] == "pass"


def test_dollarbar_transform_validation_fails_if_forbidden_column_appears(tmp_path: Path) -> None:
    run_dollarbar_transform_validation()
    target = _copy_validation(tmp_path)
    panel_path = target / "transform_validation_panel.csv"
    panel = pd.read_csv(panel_path)
    panel["pnl"] = 1.0
    panel.to_csv(panel_path, index=False)

    report = validate_dollarbar_transform_validation(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "forbidden_output_columns_absent" and check["status"] == "fail" for check in report["checks"])


def test_dollarbar_transform_validation_fails_if_manifest_records_backtest(tmp_path: Path) -> None:
    run_dollarbar_transform_validation()
    target = _copy_validation(tmp_path)
    manifest_path = target / "validation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_performed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_dollarbar_transform_validation(target)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution" and check["status"] == "fail" for check in report["checks"])


def _write_bars(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "symbol": "TEST",
                "timestamp": f"2026-05-21T14:{30 + index:02d}:00Z",
                "open": 10 + index * 0.01,
                "high": 10.2 + index * 0.01,
                "low": 9.9,
                "close": 10 + index * 0.02,
                "volume": 100 + index * 10,
            }
            for index in range(30)
        ]
    ).to_csv(path, index=False)


def _copy_validation(tmp_path: Path) -> Path:
    source = Path("experiments/provider_aware_research/dollarbar_transform_validation_20260521")
    target = tmp_path / "validation"
    target.mkdir()
    for item in source.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
