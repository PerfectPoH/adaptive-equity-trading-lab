from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.pipeline import run_milestone_1


OUTPUT_JSON = Path("experiments/calibration_comparison_latest.json")
OUTPUT_CSV = Path("experiments/calibration_comparison_latest.csv")
RAW_THRESHOLD = 0.55
CALIBRATED_DEFAULT_THRESHOLD = 0.55
CALIBRATED_SIGNAL_THRESHOLD = 0.25


def run_calibration_comparison() -> dict[str, Any]:
    raw_dir = run_milestone_1(
        calibration_method=None,
        min_model_probability=RAW_THRESHOLD,
        run_tag="raw",
    )
    calibrated_default_dir = run_milestone_1(
        calibration_method="isotonic",
        min_model_probability=CALIBRATED_DEFAULT_THRESHOLD,
        run_tag="calibrated",
    )
    calibrated_signal_dir = run_milestone_1(
        calibration_method="isotonic",
        min_model_probability=CALIBRATED_SIGNAL_THRESHOLD,
        run_tag="calibrated_thr25",
    )

    raw = _load_run(raw_dir, "raw")
    calibrated_default = _load_run(calibrated_default_dir, "calibrated_default_threshold")
    calibrated_signal = _load_run(calibrated_signal_dir, "calibrated_signal_threshold")
    variants = [raw, calibrated_default, calibrated_signal]
    report = {
        "raw_run": str(raw_dir),
        "calibrated_default_run": str(calibrated_default_dir),
        "calibrated_signal_run": str(calibrated_signal_dir),
        "raw": raw,
        "calibrated_default_threshold": calibrated_default,
        "calibrated_signal_threshold": calibrated_signal,
        "comparison": _compare(raw, calibrated_default, calibrated_signal),
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame([_flat_row(run) for run in variants]).to_csv(OUTPUT_CSV, index=False)
    return report


def _load_run(run_dir: Path, variant: str) -> dict[str, Any]:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    calibration = json.loads((run_dir / "calibration_summary.json").read_text(encoding="utf-8"))
    analysis = json.loads((run_dir / "analysis_summary.json").read_text(encoding="utf-8"))
    return {
        "variant": variant,
        "run_id": summary["run_id"],
        "signal_config": summary.get("signal_config", {}),
        "aggregate_backtest": summary["aggregate_backtest"],
        "validation_metrics": summary["validation_metrics"],
        "test_metrics": summary["test_metrics"],
        "calibration_summary": calibration,
        "analysis_summary": analysis,
    }


def _compare(
    raw: dict[str, Any],
    calibrated_default: dict[str, Any],
    calibrated_signal: dict[str, Any],
) -> dict[str, Any]:
    return {
        "same_threshold": _pairwise_compare(raw, calibrated_default),
        "retuned_threshold": _pairwise_compare(raw, calibrated_signal),
        "verdict": _verdict(raw, calibrated_default, calibrated_signal),
    }


def _pairwise_compare(raw: dict[str, Any], calibrated: dict[str, Any]) -> dict[str, float]:
    raw_backtest = raw["aggregate_backtest"]
    calibrated_backtest = calibrated["aggregate_backtest"]
    raw_calibration = raw["calibration_summary"].get("test", {})
    calibrated_calibration = calibrated["calibration_summary"].get("test", {})
    return {
        "strategy_return_delta": _delta(calibrated_backtest, raw_backtest, "strategy_return"),
        "excess_return_delta": _delta(calibrated_backtest, raw_backtest, "excess_return"),
        "test_brier_delta": _delta(calibrated_calibration, raw_calibration, "brier_score"),
        "test_mean_abs_calibration_error_delta": _delta(
            calibrated_calibration,
            raw_calibration,
            "mean_abs_calibration_error",
        ),
    }


def _verdict(
    raw: dict[str, Any],
    calibrated_default: dict[str, Any],
    calibrated_signal: dict[str, Any],
) -> str:
    signal_strategy_delta = _delta(
        calibrated_signal["aggregate_backtest"],
        raw["aggregate_backtest"],
        "strategy_return",
    )
    brier_delta = _delta(
        calibrated_default["calibration_summary"].get("test", {}),
        raw["calibration_summary"].get("test", {}),
        "brier_score",
    )
    calibration_error_delta = _delta(
        calibrated_default["calibration_summary"].get("test", {}),
        raw["calibration_summary"].get("test", {}),
        "mean_abs_calibration_error",
    )
    if brier_delta < 0 and calibration_error_delta < 0 and signal_strategy_delta >= 0:
        return "calibration_helped"
    if brier_delta < 0 or calibration_error_delta < 0:
        return "calibration_improved_probabilities_but_not_strategy"
    return "calibration_did_not_help"


def _flat_row(run: dict[str, Any]) -> dict[str, Any]:
    backtest = run["aggregate_backtest"]
    test_calibration = run["calibration_summary"].get("test", {})
    analysis = run["analysis_summary"]
    return {
        "variant": run["variant"],
        "run_id": run["run_id"],
        "calibration_method": run["signal_config"].get("calibration_method"),
        "threshold": run["signal_config"].get("min_model_probability"),
        "strategy_return": backtest.get("strategy_return"),
        "buy_and_hold_return": backtest.get("buy_and_hold_return"),
        "excess_return": backtest.get("excess_return"),
        "max_drawdown": backtest.get("max_drawdown"),
        "win_rate": backtest.get("win_rate"),
        "test_brier_score": test_calibration.get("brier_score"),
        "test_mean_abs_calibration_error": test_calibration.get("mean_abs_calibration_error"),
        "total_signals": analysis.get("total_signals"),
        "symbols_with_signals": analysis.get("symbols_with_signals"),
    }


def _delta(left: dict[str, Any], right: dict[str, Any], key: str) -> float:
    try:
        return float(left.get(key)) - float(right.get(key))
    except (TypeError, ValueError):
        return float("nan")


if __name__ == "__main__":
    result = run_calibration_comparison()
    print(json.dumps(result["comparison"], indent=2))
