from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.analysis.nctrl_property_evaluator import NctrlPropertyEvaluationInput, evaluate_nctrl_trial_properties
from src.analysis.small_cap_portfolio_diagnostics import build_portfolio_outlier_breakdown


def _write_required_artifacts(tmp_path: Path) -> dict[str, Path]:
    paths = {
        "candidate_export": tmp_path / "candidate_export.csv",
        "run_manifest": tmp_path / "run_manifest.json",
        "portfolio_trade_log": tmp_path / "portfolio_trade_log.csv",
        "portfolio_equity_curve": tmp_path / "portfolio_equity_curve.csv",
        "portfolio_rejections": tmp_path / "portfolio_rejections.csv",
        "portfolio_summary": tmp_path / "portfolio_summary.csv",
        "backtest_report": tmp_path / "small_cap_backtest_report.md",
        "property_check_report_json": tmp_path / "property_check_report.json",
        "property_check_report_md": tmp_path / "property_check_report.md",
    }
    for path in paths.values():
        path.write_text("ok\n", encoding="utf-8")
    return paths


def _manifest() -> dict[str, object]:
    return {
        "config_hash": "abc123",
        "trial_accounting": {"trial_id": "TRIAL-NCTRL-001"},
        "universe": ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL", "SPY", "QQQ"],
        "period": {"start": "2024-01-02", "end": "2024-12-31"},
    }


def _candidate_export() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"as_of": "2024-01-02", "symbol": "AAPL", "operational_candidate": True},
            {"as_of": "2024-01-03", "symbol": "MSFT", "operational_candidate": True},
        ]
    )


def _benchmark_report() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"benchmark": "cash_flat", "return": 0.0, "observations": 2},
            {"benchmark": "iwm_proxy", "return": 0.05, "observations": 1},
            {"benchmark": "equal_weight_universe", "return": 0.08, "observations": 10},
            {"benchmark": "random_entry_baseline", "return": 0.07, "observations": 2},
            {"benchmark": "ticker_holding_window", "return": 0.09, "observations": 2},
        ]
    )


def _trade_log() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAPL", "pnl": 50.0, "return_pct": 0.05},
            {"symbol": "MSFT", "pnl": 30.0, "return_pct": 0.03},
            {"symbol": "NVDA", "pnl": 20.0, "return_pct": 0.02},
            {"symbol": "AMD", "pnl": -10.0, "return_pct": -0.01},
        ]
    )


def _input(tmp_path: Path, total_trades: int = 32) -> NctrlPropertyEvaluationInput:
    trade_log = _trade_log()
    return NctrlPropertyEvaluationInput(
        output_dir=tmp_path,
        artifact_paths=_write_required_artifacts(tmp_path),
        run_manifest=_manifest(),
        candidate_export=_candidate_export(),
        benchmark_report=_benchmark_report(),
        trade_log=trade_log,
        portfolio_summary={"total_trades": total_trades, "initial_cash": 1000.0, "total_pnl": 90.0, "return_pct": 0.09},
        portfolio_outlier_breakdown=build_portfolio_outlier_breakdown(trade_log, initial_cash=1000.0),
        bootstrap_random_baseline={
            "simulations": 1000,
            "base_seed": 700,
            "mean_return": 0.07,
            "median_return": 0.071,
            "std_return": 0.02,
            "p05_return": 0.02,
            "p95_return": 0.12,
            "observations_per_simulation_min": 2,
            "observations_per_simulation_max": 2,
        },
        random_entry_sign_flip_report={
            "simulations": 1000,
            "valid_simulations": 1000,
            "sign_flip_excluding_top_3_frequency": 0.42,
            "preserves_execution_mechanics": True,
        },
        risk_fraction=0.01,
        cash_ledger_fixture_tests_passed=True,
    )


def test_evaluate_nctrl_trial_properties_returns_eight_passes(tmp_path: Path) -> None:
    checks, overall_status = evaluate_nctrl_trial_properties(_input(tmp_path))

    assert overall_status == "pass"
    assert [check.property_id for check in checks] == ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    assert {check.status for check in checks} == {"pass"}


def test_evaluate_nctrl_trial_properties_applies_sample_size_stop_rule(tmp_path: Path) -> None:
    checks, overall_status = evaluate_nctrl_trial_properties(_input(tmp_path, total_trades=12))

    assert overall_status == "insufficient_evidence"
    assert any(check.property_id == "P1" and check.status == "pass" for check in checks)


def test_evaluate_nctrl_trial_properties_fails_manifest_identity(tmp_path: Path) -> None:
    inputs = _input(tmp_path)
    inputs.run_manifest["trial_accounting"] = {"trial_id": "WRONG"}

    checks, overall_status = evaluate_nctrl_trial_properties(inputs)

    assert overall_status == "fail"
    assert next(check for check in checks if check.property_id == "P2").status == "fail"


def test_evaluate_nctrl_trial_properties_accepts_actual_last_candidate_day_representation(tmp_path: Path) -> None:
    inputs = _input(tmp_path)
    inputs.run_manifest["period"] = {"start": "2024-01-02", "end": "2024-12-27"}
    inputs.candidate_export = pd.DataFrame(
        [
            {"as_of": "2024-01-02", "symbol": "AAPL", "operational_candidate": True},
            {"as_of": "2024-12-27", "symbol": "MSFT", "operational_candidate": True},
        ]
    )

    checks, overall_status = evaluate_nctrl_trial_properties(inputs)

    assert overall_status == "pass"
    assert next(check for check in checks if check.property_id == "P2").status == "pass"
