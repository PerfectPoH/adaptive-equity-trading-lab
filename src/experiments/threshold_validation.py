from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.pipeline import run_milestone_1


OUTPUT_JSON = Path("experiments/threshold_validation_latest.json")
OUTPUT_CSV = Path("experiments/threshold_validation_latest.csv")


def run_threshold_validation(thresholds: tuple[float, ...] = (0.45, 0.50, 0.55, 0.60)) -> dict[str, Any]:
    runs = []
    for use_news in (False, True):
        for threshold in thresholds:
            tag = f"{'news' if use_news else 'no_news'}_thr{int(threshold * 100):02d}"
            run_dir = run_milestone_1(
                use_news=use_news,
                calibration_method=None,
                min_model_probability=threshold,
                run_tag=tag,
            )
            runs.append(_load_run(run_dir, use_news, threshold))

    rows = [_flat_row(run) for run in runs]
    report = {
        "runs": runs,
        "best_by_strategy_return": max(rows, key=lambda row: row["strategy_return"]),
        "best_by_excess_return": max(rows, key=lambda row: row["excess_return"]),
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_csv(OUTPUT_CSV, index=False)
    return report


def _load_run(run_dir: Path, use_news: bool, threshold: float) -> dict[str, Any]:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    analysis = json.loads((run_dir / "analysis_summary.json").read_text(encoding="utf-8"))
    signals = json.loads((run_dir / "signal_diagnostics_summary.json").read_text(encoding="utf-8"))
    return {
        "run_dir": str(run_dir),
        "run_id": summary["run_id"],
        "use_news": use_news,
        "threshold": threshold,
        "aggregate_backtest": summary["aggregate_backtest"],
        "validation_metrics": summary["validation_metrics"],
        "test_metrics": summary["test_metrics"],
        "analysis_summary": analysis,
        "signal_diagnostics_summary": signals,
    }


def _flat_row(run: dict[str, Any]) -> dict[str, Any]:
    backtest = run["aggregate_backtest"]
    analysis = run["analysis_summary"]
    signals = run["signal_diagnostics_summary"]
    return {
        "run_id": run["run_id"],
        "use_news": run["use_news"],
        "threshold": run["threshold"],
        "strategy_return": backtest.get("strategy_return"),
        "buy_and_hold_return": backtest.get("buy_and_hold_return"),
        "excess_return": backtest.get("excess_return"),
        "max_drawdown": backtest.get("max_drawdown"),
        "win_rate": backtest.get("win_rate"),
        "validation_roc_auc": run["validation_metrics"].get("roc_auc"),
        "test_roc_auc": run["test_metrics"].get("roc_auc"),
        "total_signals": analysis.get("total_signals"),
        "executable_signals": analysis.get("total_executable_signals"),
        "symbols_with_signals": analysis.get("symbols_with_signals"),
        "symbols_with_model_pass": signals.get("symbols_with_model_pass"),
    }


if __name__ == "__main__":
    result = run_threshold_validation()
    print(json.dumps(result["best_by_strategy_return"], indent=2))
