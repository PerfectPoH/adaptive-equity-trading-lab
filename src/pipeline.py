from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from src.backtest.execution import add_execution_columns
from src.backtest.runner import run_backtest
from src.data.downloader import download_universe
from src.features.feature_pipeline import build_features
from src.models.label_builder import build_trade_labels
from src.models.predictor import add_model_probabilities
from src.models.trainer import evaluate_classifier, fit_model, temporal_split
from src.scanner.stock_scanner import add_scanner_columns
from src.strategy.signal_engine import add_signal_columns


UNIVERSE = ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL", "SPY", "QQQ"]
FEATURE_START = "2018-01-01"
MAX_GAP_THRESHOLD = 0.05
RUNS_DIR = Path("experiments/runs")
LOG_PATH = Path("experiments/log.csv")


def run_milestone_1() -> Path:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    raw = download_universe(UNIVERSE, start=FEATURE_START, pause_seconds=0.4)
    if "SPY" not in raw:
        raise RuntimeError("SPY data is required for the market trend filter")
    if len(raw) < 3:
        raise RuntimeError("Not enough tickers downloaded successfully")

    spy = raw["SPY"]
    prepared: dict[str, pd.DataFrame] = {}
    for symbol, frame in raw.items():
        featured = build_features(frame, spy)
        featured["symbol"] = symbol
        scanned = add_scanner_columns(featured)
        labeled = build_trade_labels(scanned, max_gap_threshold=MAX_GAP_THRESHOLD)
        prepared[symbol] = labeled

    combined = pd.concat(prepared.values()).sort_index()
    split = temporal_split(combined)
    model = fit_model(split.train, model_type="random_forest")
    model_path = run_dir / "model.joblib"
    joblib.dump(model, model_path)

    validation_metrics = evaluate_classifier(model, split.validation)
    test_metrics = evaluate_classifier(model, split.test)

    processed_frames: list[pd.DataFrame] = []
    backtest_rows: list[dict[str, object]] = []

    for symbol, frame in prepared.items():
        with_probs = add_model_probabilities(frame, model)
        with_signals = add_signal_columns(with_probs)
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

    signals = pd.concat(processed_frames).sort_index()
    signals.index.name = "Date"
    signals.to_csv(run_dir / "signals.csv")

    backtests = pd.DataFrame(backtest_rows)
    backtests.to_csv(run_dir / "backtests.csv", index=False)

    aggregate = _aggregate_backtests(backtests)
    _append_experiment_log(
        run_id=run_id,
        dataset_snapshot="data/snapshots/*",
        model="random_forest",
        params={
            "max_gap_threshold": MAX_GAP_THRESHOLD,
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
                "validation_metrics": validation_metrics,
                "test_metrics": test_metrics,
                "aggregate_backtest": aggregate,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return run_dir


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
