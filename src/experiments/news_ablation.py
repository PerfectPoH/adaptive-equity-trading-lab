from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.pipeline import run_milestone_1


OUTPUT_JSON = Path("experiments/news_ablation_latest.json")
OUTPUT_CSV = Path("experiments/news_ablation_latest.csv")


def run_news_ablation() -> dict[str, Any]:
    no_news_dir = run_milestone_1(use_news=False, run_tag="no_news")
    news_dir = run_milestone_1(use_news=True, run_tag="news")

    no_news = _load_run_summary(no_news_dir)
    news = _load_run_summary(news_dir)
    comparison = _compare(no_news, news)

    report = {
        "no_news_run": str(no_news_dir),
        "news_run": str(news_dir),
        "no_news": no_news,
        "news": news,
        "comparison": comparison,
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame([_flat_row("no_news", no_news), _flat_row("news", news)]).to_csv(OUTPUT_CSV, index=False)
    return report


def _load_run_summary(run_dir: Path) -> dict[str, Any]:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    analysis = json.loads((run_dir / "analysis_summary.json").read_text(encoding="utf-8"))
    signal_diagnostics = json.loads((run_dir / "signal_diagnostics_summary.json").read_text(encoding="utf-8"))
    threshold_summary = json.loads((run_dir / "threshold_diagnostics_summary.json").read_text(encoding="utf-8"))
    return {
        "run_id": summary["run_id"],
        "aggregate_backtest": summary["aggregate_backtest"],
        "validation_metrics": summary["validation_metrics"],
        "test_metrics": summary["test_metrics"],
        "analysis_summary": analysis,
        "signal_diagnostics_summary": signal_diagnostics,
        "threshold_diagnostics_summary": threshold_summary,
    }


def _compare(no_news: dict[str, Any], news: dict[str, Any]) -> dict[str, Any]:
    no_backtest = no_news["aggregate_backtest"]
    news_backtest = news["aggregate_backtest"]
    no_validation = no_news["validation_metrics"]
    news_validation = news["validation_metrics"]
    no_test = no_news["test_metrics"]
    news_test = news["test_metrics"]
    return {
        "strategy_return_delta": _delta(news_backtest, no_backtest, "strategy_return"),
        "excess_return_delta": _delta(news_backtest, no_backtest, "excess_return"),
        "max_drawdown_delta": _delta(news_backtest, no_backtest, "max_drawdown"),
        "win_rate_delta": _delta(news_backtest, no_backtest, "win_rate"),
        "validation_roc_auc_delta": _delta(news_validation, no_validation, "roc_auc"),
        "test_roc_auc_delta": _delta(news_test, no_test, "roc_auc"),
        "verdict": _verdict(no_news, news),
    }


def _verdict(no_news: dict[str, Any], news: dict[str, Any]) -> str:
    strategy_delta = _delta(news["aggregate_backtest"], no_news["aggregate_backtest"], "strategy_return")
    validation_auc_delta = _delta(news["validation_metrics"], no_news["validation_metrics"], "roc_auc")
    test_auc_delta = _delta(news["test_metrics"], no_news["test_metrics"], "roc_auc")
    if strategy_delta > 0 and validation_auc_delta > 0 and test_auc_delta >= 0:
        return "news_helped_slightly"
    if strategy_delta < 0 and validation_auc_delta < 0:
        return "news_hurt"
    return "mixed_or_inconclusive"


def _flat_row(name: str, summary: dict[str, Any]) -> dict[str, Any]:
    backtest = summary["aggregate_backtest"]
    analysis = summary["analysis_summary"]
    signal_diag = summary["signal_diagnostics_summary"]
    return {
        "variant": name,
        "run_id": summary["run_id"],
        "strategy_return": backtest.get("strategy_return"),
        "buy_and_hold_return": backtest.get("buy_and_hold_return"),
        "excess_return": backtest.get("excess_return"),
        "max_drawdown": backtest.get("max_drawdown"),
        "win_rate": backtest.get("win_rate"),
        "validation_roc_auc": summary["validation_metrics"].get("roc_auc"),
        "test_roc_auc": summary["test_metrics"].get("roc_auc"),
        "total_signals": analysis.get("total_signals"),
        "symbols_with_signals": analysis.get("symbols_with_signals"),
        "primary_bottlenecks": json.dumps(signal_diag.get("primary_bottlenecks", {}), sort_keys=True),
        "recommended_threshold": summary["threshold_diagnostics_summary"].get("recommended_threshold"),
    }


def _delta(left: dict[str, Any], right: dict[str, Any], key: str) -> float:
    try:
        return float(left.get(key)) - float(right.get(key))
    except (TypeError, ValueError):
        return float("nan")


if __name__ == "__main__":
    result = run_news_ablation()
    print(json.dumps(result["comparison"], indent=2))
