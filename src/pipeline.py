from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from src.analysis.calibration import build_calibration_report
from src.analysis.error_analyzer import build_run_analysis, build_signal_diagnostics
from src.analysis.regime_analyzer import build_feature_regime_analysis
from src.analysis.threshold_analyzer import build_threshold_diagnostics
from src.analysis.trade_analyzer import build_trade_analysis, trades_to_frame
from src.backtest.execution import add_execution_columns
from src.backtest.metrics import equity_curve_to_frame
from src.backtest.runner import run_backtest
from src.data.downloader import download_universe
from src.features.feature_pipeline import build_features
from src.models.calibrator import fit_probability_calibrator
from src.models.label_builder import build_trade_labels
from src.models.predictor import add_model_probabilities
from src.models.trainer import evaluate_classifier, fit_model, temporal_split
from src.news.gdelt_doc import load_or_download_market_news
from src.scanner.stock_scanner import add_scanner_columns
from src.strategy.signal_engine import add_signal_columns


UNIVERSE = ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL", "SPY", "QQQ"]
FEATURE_START = "2018-01-01"
NEWS_START = "2020-01-01"
NEWS_END = "2024-12-31"
MAX_GAP_THRESHOLD = 0.05
DEFAULT_USE_NEWS = False
DEFAULT_MODEL_TYPE = "random_forest"
DEFAULT_CALIBRATION_METHOD = "isotonic"
DEFAULT_MIN_MODEL_PROBABILITY = 0.25
RUNS_DIR = Path("experiments/runs")
LOG_PATH = Path("experiments/log.csv")


def run_milestone_1(
    use_news: bool = DEFAULT_USE_NEWS,
    run_tag: str | None = None,
    model_type: str = DEFAULT_MODEL_TYPE,
    min_scanner_score: float = 70,
    min_model_probability: float = DEFAULT_MIN_MODEL_PROBABILITY,
    calibration_method: str | None = DEFAULT_CALIBRATION_METHOD,
    min_relative_volume: float | None = None,
    max_distance_from_20d_high: float | None = None,
    max_atr_pct: float | None = None,
) -> Path:
    base_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{base_run_id}_{run_tag}" if run_tag else base_run_id
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    raw = download_universe(UNIVERSE, start=FEATURE_START, pause_seconds=0.4)
    if "SPY" not in raw:
        raise RuntimeError("SPY data is required for the market trend filter")
    if len(raw) < 3:
        raise RuntimeError("Not enough tickers downloaded successfully")

    spy = raw["SPY"]
    market_news = load_or_download_market_news(NEWS_START, NEWS_END) if use_news else None
    prepared: dict[str, pd.DataFrame] = {}
    for symbol, frame in raw.items():
        featured = build_features(frame, spy, market_news=market_news)
        featured["symbol"] = symbol
        scanned = add_scanner_columns(featured)
        labeled = build_trade_labels(scanned, max_gap_threshold=MAX_GAP_THRESHOLD)
        prepared[symbol] = labeled

    combined = pd.concat(prepared.values()).sort_index()
    split = temporal_split(combined)
    model = fit_model(split.train, model_type=model_type)

    raw_validation_metrics = evaluate_classifier(model, split.validation)
    raw_test_metrics = evaluate_classifier(model, split.test)
    probability_model = model
    if calibration_method:
        probability_model = fit_probability_calibrator(model, split.validation, method=calibration_method)
    validation_metrics = evaluate_classifier(probability_model, split.validation)
    test_metrics = evaluate_classifier(probability_model, split.test)
    model_path = run_dir / "model.joblib"
    joblib.dump(probability_model, model_path)

    processed_frames: list[pd.DataFrame] = []
    backtest_rows: list[dict[str, object]] = []
    equity_frames: list[pd.DataFrame] = []
    trade_frames: list[pd.DataFrame] = []

    for symbol, frame in prepared.items():
        with_probs = add_model_probabilities(frame, probability_model)
        with_signals = add_signal_columns(
            with_probs,
            min_scanner_score=min_scanner_score,
            min_model_probability=min_model_probability,
            min_relative_volume=min_relative_volume,
            max_distance_from_20d_high=max_distance_from_20d_high,
            max_atr_pct=max_atr_pct,
        )
        executable = add_execution_columns(with_signals, max_gap_threshold=MAX_GAP_THRESHOLD)
        processed_frames.append(executable)

        test_frame = executable.loc["2024-01-01":"2024-12-31"].copy()
        if len(test_frame) < 50:
            continue

        try:
            stats, summary = run_backtest(test_frame)
        except Exception as exc:  # noqa: BLE001 - keep per-symbol runs independent.
            backtest_rows.append({"symbol": symbol, "error": str(exc)})
            continue

        row = {"symbol": symbol, "trades": int(stats.get("# Trades", 0)), **summary}
        backtest_rows.append(row)
        equity_curve = equity_curve_to_frame(stats, symbol)
        if not equity_curve.empty:
            equity_frames.append(equity_curve)
        trades = trades_to_frame(stats, test_frame, symbol)
        if not trades.empty:
            trade_frames.append(trades)

    signals = pd.concat(processed_frames).sort_index()
    signals.index.name = "Date"
    signals.to_csv(run_dir / "signals.csv")

    backtests = pd.DataFrame(backtest_rows)
    backtests.to_csv(run_dir / "backtests.csv", index=False)

    if equity_frames:
        equity_curves = pd.concat(equity_frames, ignore_index=True)
    else:
        equity_curves = pd.DataFrame()
    equity_curves.to_csv(run_dir / "equity_curves.csv", index=False)

    if trade_frames:
        trades = pd.concat(trade_frames, ignore_index=True)
    else:
        trades = pd.DataFrame()
    trades.to_csv(run_dir / "trades.csv", index=False)
    trade_analysis_by_symbol, trade_analysis_summary = build_trade_analysis(trades)
    trade_analysis_by_symbol.to_csv(run_dir / "trade_analysis_by_symbol.csv", index=False)
    (run_dir / "trade_analysis_summary.json").write_text(
        json.dumps(trade_analysis_summary, indent=2),
        encoding="utf-8",
    )
    regime_analysis, regime_contrasts, regime_summary = build_feature_regime_analysis(trades)
    regime_analysis.to_csv(run_dir / "feature_regime_analysis.csv", index=False)
    regime_contrasts.to_csv(run_dir / "feature_regime_contrasts.csv", index=False)
    (run_dir / "feature_regime_summary.json").write_text(
        json.dumps(regime_summary, indent=2),
        encoding="utf-8",
    )

    analysis, analysis_summary = build_run_analysis(signals, backtests)
    analysis.to_csv(run_dir / "analysis.csv", index=False)
    (run_dir / "analysis_summary.json").write_text(json.dumps(analysis_summary, indent=2), encoding="utf-8")
    signal_diagnostics, signal_diagnostics_summary = build_signal_diagnostics(
        signals,
        min_scanner_score=min_scanner_score,
        min_model_probability=min_model_probability,
    )
    signal_diagnostics.to_csv(run_dir / "signal_diagnostics.csv", index=False)
    (run_dir / "signal_diagnostics_summary.json").write_text(
        json.dumps(signal_diagnostics_summary, indent=2),
        encoding="utf-8",
    )
    threshold_diagnostics, threshold_diagnostics_summary = build_threshold_diagnostics(
        signals,
        min_scanner_score=min_scanner_score,
    )
    threshold_diagnostics.to_csv(run_dir / "threshold_diagnostics.csv", index=False)
    (run_dir / "threshold_diagnostics_summary.json").write_text(
        json.dumps(threshold_diagnostics_summary, indent=2),
        encoding="utf-8",
    )
    calibration, calibration_summary = build_calibration_report(probability_model, split)
    calibration.to_csv(run_dir / "calibration.csv", index=False)
    (run_dir / "calibration_summary.json").write_text(json.dumps(calibration_summary, indent=2), encoding="utf-8")

    aggregate = _aggregate_backtests(backtests)
    _append_experiment_log(
        run_id=run_id,
        dataset_snapshot="data/snapshots/*",
        model=model_type,
        params={
            "max_gap_threshold": MAX_GAP_THRESHOLD,
            "model_type": model_type,
            "min_scanner_score": min_scanner_score,
            "min_model_probability": min_model_probability,
            "calibration_method": calibration_method or "raw",
            "regime_filters": _regime_filter_config(
                min_relative_volume=min_relative_volume,
                max_distance_from_20d_high=max_distance_from_20d_high,
                max_atr_pct=max_atr_pct,
            ),
            "news_features": "gdelt_market_news_lagged_1d" if use_news else "disabled",
            "raw_validation_metrics": raw_validation_metrics,
            "raw_test_metrics": raw_test_metrics,
            "validation_metrics": validation_metrics,
            "test_metrics": test_metrics,
        },
        aggregate=aggregate,
    )

    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "model_path": str(model_path),
                "signal_config": {
                    "model_type": model_type,
                    "min_scanner_score": min_scanner_score,
                    "min_model_probability": min_model_probability,
                    "use_news": use_news,
                    "calibration_method": calibration_method or "raw",
                    "regime_filters": _regime_filter_config(
                        min_relative_volume=min_relative_volume,
                        max_distance_from_20d_high=max_distance_from_20d_high,
                        max_atr_pct=max_atr_pct,
                    ),
                },
                "validation_metrics": validation_metrics,
                "test_metrics": test_metrics,
                "raw_validation_metrics": raw_validation_metrics,
                "raw_test_metrics": raw_test_metrics,
                "aggregate_backtest": aggregate,
                "analysis_summary": analysis_summary,
                "signal_diagnostics_summary": signal_diagnostics_summary,
                "threshold_diagnostics_summary": threshold_diagnostics_summary,
                "calibration_summary": calibration_summary,
                "trade_analysis_summary": trade_analysis_summary,
                "feature_regime_summary": regime_summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return run_dir


def _regime_filter_config(
    min_relative_volume: float | None,
    max_distance_from_20d_high: float | None,
    max_atr_pct: float | None,
) -> dict[str, float]:
    config = {
        "min_relative_volume": min_relative_volume,
        "max_distance_from_20d_high": max_distance_from_20d_high,
        "max_atr_pct": max_atr_pct,
    }
    return {key: value for key, value in config.items() if value is not None}


def _aggregate_backtests(backtests: pd.DataFrame) -> dict[str, object]:
    numeric_cols = [
        "strategy_return",
        "buy_and_hold_return",
        "excess_return",
        "max_drawdown",
        "sharpe",
        "profit_factor",
        "win_rate",
    ]
    clean = backtests.dropna(subset=["strategy_return"], how="any") if "strategy_return" in backtests else pd.DataFrame()
    if clean.empty:
        return {
            "strategy_return": float("nan"),
            "buy_and_hold_return": float("nan"),
            "excess_return": float("nan"),
            "max_drawdown": float("nan"),
            "sharpe": float("nan"),
            "profit_factor": float("nan"),
            "win_rate": float("nan"),
            "beats_buy_and_hold": False,
            "notes": "No successful symbol backtests",
        }

    result = {col: float(clean[col].mean()) for col in numeric_cols if col in clean.columns}
    result["beats_buy_and_hold"] = bool(result.get("excess_return", 0) > 0)
    result["notes"] = "Mean of per-symbol 2024 backtests"
    return result


def _append_experiment_log(
    run_id: str,
    dataset_snapshot: str,
    model: str,
    params: dict[str, object],
    aggregate: dict[str, object],
) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "dataset_snapshot": dataset_snapshot,
        "strategy": "scanner_ml_next_open_v1",
        "model": model,
        "params": json.dumps(params, sort_keys=True),
        "train_period": "2020-2022",
        "test_period": "2024",
        "max_gap_threshold": MAX_GAP_THRESHOLD,
        "strategy_return": aggregate.get("strategy_return"),
        "buy_and_hold_return": aggregate.get("buy_and_hold_return"),
        "excess_return": aggregate.get("excess_return"),
        "max_drawdown": aggregate.get("max_drawdown"),
        "sharpe": aggregate.get("sharpe"),
        "profit_factor": aggregate.get("profit_factor"),
        "win_rate": aggregate.get("win_rate"),
        "beats_buy_and_hold": aggregate.get("beats_buy_and_hold"),
        "notes": aggregate.get("notes"),
    }
    exists = LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if not exists or LOG_PATH.stat().st_size == 0:
            writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    output = run_milestone_1()
    print(f"Milestone 1 run written to {output}")
