from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from src.pipeline import DEFAULT_MIN_MODEL_PROBABILITY, run_milestone_1


OUTPUT_JSON = Path("experiments/regime_filter_validation_latest.json")
OUTPUT_CSV = Path("experiments/regime_filter_validation_latest.csv")

FILTER_VARIANTS: tuple[dict[str, Any], ...] = (
    {
        "variant": "baseline",
        "run_tag": "regime_baseline",
        "filters": {},
    },
    {
        "variant": "volume_floor",
        "run_tag": "regime_volume",
        "filters": {"min_relative_volume": 1.0},
    },
    {
        "variant": "pullback_depth",
        "run_tag": "regime_pullback",
        "filters": {"max_distance_from_20d_high": -0.021},
    },
    {
        "variant": "atr_guard",
        "run_tag": "regime_atr",
        "filters": {"max_atr_pct": 0.0315},
    },
    {
        "variant": "combined_filters",
        "run_tag": "regime_combined",
        "filters": {
            "min_relative_volume": 1.0,
            "max_distance_from_20d_high": -0.021,
            "max_atr_pct": 0.0315,
        },
    },
)


def run_regime_filter_validation() -> dict[str, Any]:
    runs = []
    for variant in FILTER_VARIANTS:
        run_dir = run_milestone_1(
            min_model_probability=DEFAULT_MIN_MODEL_PROBABILITY,
            run_tag=variant["run_tag"],
            **variant["filters"],
        )
        runs.append(_load_run(run_dir, variant["variant"], variant["filters"]))

    rows = [_flat_row(run) for run in runs]
    baseline = rows[0]
    compared_rows = [_with_baseline_deltas(row, baseline) for row in rows]
    report = {
        "baseline_run": runs[0]["run_dir"],
        "runs": runs,
        "rows": compared_rows,
        "best_by_strategy_return": max(compared_rows, key=lambda row: row["strategy_return"]),
        "best_by_excess_return": max(compared_rows, key=lambda row: row["excess_return"]),
        "best_by_sharpe": _max_by_metric(compared_rows, "sharpe"),
        "best_by_drawdown": _max_by_metric(compared_rows, "max_drawdown"),
        "comparison": _comparison(compared_rows),
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame(compared_rows).to_csv(OUTPUT_CSV, index=False)
    return report


def _load_run(run_dir: Path, variant: str, filters: dict[str, float]) -> dict[str, Any]:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    analysis = json.loads((run_dir / "analysis_summary.json").read_text(encoding="utf-8"))
    trade_analysis = json.loads((run_dir / "trade_analysis_summary.json").read_text(encoding="utf-8"))
    regime_summary = json.loads((run_dir / "feature_regime_summary.json").read_text(encoding="utf-8"))
    return {
        "variant": variant,
        "run_dir": str(run_dir),
        "run_id": summary["run_id"],
        "filters": filters,
        "signal_config": summary.get("signal_config", {}),
        "aggregate_backtest": summary["aggregate_backtest"],
        "analysis_summary": analysis,
        "trade_analysis_summary": trade_analysis,
        "feature_regime_summary": regime_summary,
    }


def _flat_row(run: dict[str, Any]) -> dict[str, Any]:
    backtest = run["aggregate_backtest"]
    analysis = run["analysis_summary"]
    trade_summary = run["trade_analysis_summary"]
    return {
        "variant": run["variant"],
        "run_id": run["run_id"],
        "filters": json.dumps(run["filters"], sort_keys=True),
        "strategy_return": backtest.get("strategy_return"),
        "buy_and_hold_return": backtest.get("buy_and_hold_return"),
        "excess_return": backtest.get("excess_return"),
        "max_drawdown": backtest.get("max_drawdown"),
        "sharpe": backtest.get("sharpe"),
        "profit_factor": backtest.get("profit_factor"),
        "win_rate": backtest.get("win_rate"),
        "total_signals": analysis.get("total_signals"),
        "executable_signals": analysis.get("total_executable_signals"),
        "symbols_with_signals": analysis.get("symbols_with_signals"),
        "closed_trades": trade_summary.get("total_trades"),
        "trade_win_rate": trade_summary.get("win_rate"),
        "avg_trade_return_pct": trade_summary.get("avg_return_pct"),
        "negative_symbols": trade_summary.get("negative_symbols"),
        "positive_symbols": trade_summary.get("positive_symbols"),
    }


def _with_baseline_deltas(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["strategy_return_delta_vs_baseline"] = _delta(row, baseline, "strategy_return")
    output["excess_return_delta_vs_baseline"] = _delta(row, baseline, "excess_return")
    output["signals_delta_vs_baseline"] = _delta(row, baseline, "total_signals")
    output["closed_trades_delta_vs_baseline"] = _delta(row, baseline, "closed_trades")
    return output


def _comparison(rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = rows[0]
    candidates = rows[1:]
    best = max(candidates, key=lambda row: row["strategy_return"]) if candidates else baseline
    best_sharpe = _max_by_metric(rows, "sharpe")
    best_drawdown = _max_by_metric(rows, "max_drawdown")
    improved = best["strategy_return"] > baseline["strategy_return"]
    return {
        "baseline_variant": baseline["variant"],
        "best_filter_variant": best["variant"],
        "best_filter_strategy_return": best["strategy_return"],
        "baseline_strategy_return": baseline["strategy_return"],
        "best_filter_delta": best["strategy_return_delta_vs_baseline"],
        "best_sharpe_variant": best_sharpe["variant"],
        "best_sharpe": best_sharpe["sharpe"],
        "best_drawdown_variant": best_drawdown["variant"],
        "best_drawdown": best_drawdown["max_drawdown"],
        "risk_note": _risk_note(baseline, best_sharpe, best_drawdown),
        "verdict": "filter_improved_strategy_return" if improved else "filters_did_not_help",
    }


def _risk_note(
    baseline: dict[str, Any],
    best_sharpe: dict[str, Any],
    best_drawdown: dict[str, Any],
) -> str:
    notes = []
    if best_sharpe["variant"] != baseline["variant"]:
        notes.append(f"{best_sharpe['variant']} improved Sharpe")
    if best_drawdown["variant"] != baseline["variant"]:
        notes.append(f"{best_drawdown['variant']} improved max drawdown")
    return "; ".join(notes) if notes else "No risk metric improved versus baseline"


def _max_by_metric(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return max(rows, key=lambda row: _metric_value(row, key))


def _metric_value(row: dict[str, Any], key: str) -> float:
    try:
        value = float(row.get(key))
    except (TypeError, ValueError):
        return float("-inf")
    return value if math.isfinite(value) else float("-inf")


def _delta(left: dict[str, Any], right: dict[str, Any], key: str) -> float:
    try:
        return float(left.get(key)) - float(right.get(key))
    except (TypeError, ValueError):
        return float("nan")


if __name__ == "__main__":
    result = run_regime_filter_validation()
    print(json.dumps(result["comparison"], indent=2))
