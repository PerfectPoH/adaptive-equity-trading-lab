from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.execution import add_execution_columns
from src.backtest.runner import run_backtest
from src.data.downloader import download_universe
from src.features.feature_pipeline import FEATURE_COLUMNS, build_features
from src.models.calibrator import fit_probability_calibrator
from src.models.label_builder import build_trade_labels
from src.models.predictor import add_model_probabilities
from src.models.trainer import fit_model, purge_label_boundary
from src.pipeline import FEATURE_START, MAX_GAP_THRESHOLD, UNIVERSE, _aggregate_backtests
from src.scanner.stock_scanner import add_scanner_columns
from src.strategy.signal_engine import add_signal_columns, apply_daily_signal_rank_filter


OUTPUT_JSON = Path("experiments/walk_forward_validation_latest.json")
OUTPUT_CSV = Path("experiments/walk_forward_validation_latest.csv")
THRESHOLDS = (0.45, 0.50, 0.55, 0.60, 0.65, 0.70)
CALIBRATED_THRESHOLDS = (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45)
DEFAULT_MODEL_TYPES = ("random_forest",)
DEFAULT_FEATURE_SETS = {"baseline": FEATURE_COLUMNS}


@dataclass(frozen=True)
class TargetExitConfig:
    name: str
    stop_atr_multiple: float = 1.5
    take_profit_atr_multiple: float = 3.0
    timeout_bars: int = 10


DEFAULT_TARGET_EXIT_CONFIGS = (
    TargetExitConfig(
        name="default_1_5x_stop_3x_tp_10d",
        stop_atr_multiple=1.5,
        take_profit_atr_multiple=3.0,
        timeout_bars=10,
    ),
)


@dataclass(frozen=True)
class SignalQualityConfig:
    name: str
    min_signal_quality_score: float | None = None
    max_signals_per_day: int | None = None
    rank_column: str = "signal_quality_score"


DEFAULT_SIGNAL_QUALITY_CONFIGS = (
    SignalQualityConfig(name="no_quality_rank_filter"),
)


@dataclass(frozen=True)
class WalkForwardFold:
    name: str
    train_end: str
    validation_start: str
    validation_end: str
    test_start: str
    test_end: str


FOLDS = (
    WalkForwardFold(
        name="wf_2023",
        train_end="2021-12-31",
        validation_start="2022-01-01",
        validation_end="2022-12-31",
        test_start="2023-01-01",
        test_end="2023-12-31",
    ),
    WalkForwardFold(
        name="wf_2024",
        train_end="2022-12-31",
        validation_start="2023-01-01",
        validation_end="2023-12-31",
        test_start="2024-01-01",
        test_end="2024-12-31",
    ),
)


def run_walk_forward_validation(
    thresholds: tuple[float, ...] = THRESHOLDS,
    calibrated_thresholds: tuple[float, ...] = CALIBRATED_THRESHOLDS,
    model_types: tuple[str, ...] = DEFAULT_MODEL_TYPES,
    feature_sets: dict[str, list[str]] | None = None,
    target_exit_configs: tuple[TargetExitConfig, ...] = DEFAULT_TARGET_EXIT_CONFIGS,
    signal_quality_configs: tuple[SignalQualityConfig, ...] = DEFAULT_SIGNAL_QUALITY_CONFIGS,
    min_validation_trades: int = 10,
    include_calibrated: bool = True,
    output_json: Path = OUTPUT_JSON,
    output_csv: Path = OUTPUT_CSV,
) -> dict[str, Any]:
    feature_sets = feature_sets or DEFAULT_FEATURE_SETS
    prepared_by_target = _prepare_frames(target_exit_configs)

    rows: list[dict[str, Any]] = []
    fold_summaries: list[dict[str, Any]] = []
    for fold in FOLDS:
        frames_by_variant: dict[tuple[str, str, str, str], dict[str, pd.DataFrame]] = {}
        validation_rows = []
        for target_config in target_exit_configs:
            prepared = prepared_by_target[target_config.name]
            combined = pd.concat(prepared.values()).sort_index()
            train = purge_label_boundary(
                combined.loc[: fold.train_end].copy(),
                label_horizon_bars=target_config.timeout_bars,
            )
            validation_for_calibration = purge_label_boundary(
                combined.loc[fold.validation_start : fold.validation_end].copy(),
                label_horizon_bars=target_config.timeout_bars,
            )

            for feature_set_name, feature_columns in feature_sets.items():
                for model_type in model_types:
                    model = fit_model(train, model_type=model_type, feature_columns=feature_columns)
                    probability_models = {"raw": model}
                    if include_calibrated:
                        probability_models["isotonic"] = fit_probability_calibrator(
                            model,
                            validation_for_calibration,
                            feature_columns=feature_columns,
                            method="isotonic",
                        )
                    model_frames = {
                        (target_config.name, feature_set_name, model_type, variant): {
                            symbol: add_model_probabilities(
                                frame,
                                probability_model,
                                feature_columns=feature_columns,
                            )
                            for symbol, frame in prepared.items()
                        }
                        for variant, probability_model in probability_models.items()
                    }
                    frames_by_variant.update(model_frames)

                    for (
                        candidate_target_exit_config,
                        candidate_feature_set,
                        candidate_model_type,
                        variant,
                    ), frames_with_probabilities in model_frames.items():
                        variant_thresholds = calibrated_thresholds if variant == "isotonic" else thresholds
                        validation_rows.extend(
                            _evaluate_threshold(
                                frames_with_probabilities,
                                fold=fold,
                                period="validation",
                                target_exit_config=candidate_target_exit_config,
                                timeout_bars=target_config.timeout_bars,
                                feature_set=candidate_feature_set,
                                model_type=candidate_model_type,
                                probability_variant=variant,
                                signal_quality_config=quality_config.name,
                                min_signal_quality_score=quality_config.min_signal_quality_score,
                                max_signals_per_day=quality_config.max_signals_per_day,
                                rank_column=quality_config.rank_column,
                                start=fold.validation_start,
                                end=fold.validation_end,
                                threshold=threshold,
                            )
                            for quality_config in signal_quality_configs
                            for threshold in variant_thresholds
                        )
        selected = select_threshold_from_validation(validation_rows, min_validation_trades=min_validation_trades)
        selected_target_config = _target_config_by_name(
            target_exit_configs,
            str(selected["target_exit_config"]),
        )
        selected_quality_config = _signal_quality_config_by_name(
            signal_quality_configs,
            str(selected["signal_quality_config"]),
        )
        test_row = _evaluate_threshold(
            frames_by_variant[
                (
                    str(selected["target_exit_config"]),
                    str(selected["feature_set"]),
                    str(selected["model_type"]),
                    str(selected["probability_variant"]),
                )
            ],
            fold=fold,
            period="test",
            target_exit_config=str(selected["target_exit_config"]),
            timeout_bars=selected_target_config.timeout_bars,
            feature_set=str(selected["feature_set"]),
            model_type=str(selected["model_type"]),
            probability_variant=str(selected["probability_variant"]),
            signal_quality_config=str(selected["signal_quality_config"]),
            min_signal_quality_score=selected_quality_config.min_signal_quality_score,
            max_signals_per_day=selected_quality_config.max_signals_per_day,
            rank_column=selected_quality_config.rank_column,
            start=fold.test_start,
            end=fold.test_end,
            threshold=float(selected["threshold"]),
        )
        test_row["selected_for_test"] = True

        for row in validation_rows:
            row["selected_for_test"] = (
                row["target_exit_config"] == selected["target_exit_config"]
                and row["feature_set"] == selected["feature_set"]
                and row["model_type"] == selected["model_type"]
                and row["probability_variant"] == selected["probability_variant"]
                and row["signal_quality_config"] == selected["signal_quality_config"]
                and float(row["threshold"]) == float(selected["threshold"])
            )
        rows.extend(validation_rows)
        rows.append(test_row)
        fold_summaries.append(
            {
                "fold": fold.name,
                "selected_target_exit_config": str(selected["target_exit_config"]),
                "selected_feature_set": str(selected["feature_set"]),
                "selected_model_type": str(selected["model_type"]),
                "selected_probability_variant": str(selected["probability_variant"]),
                "selected_signal_quality_config": str(selected["signal_quality_config"]),
                "selected_signal_rank_column": str(selected.get("signal_rank_column", "")),
                "selected_threshold": float(selected["threshold"]),
                "validation_strategy_return": selected["strategy_return"],
                "validation_excess_return": selected["excess_return"],
                "validation_closed_trades": selected["closed_trades"],
                "test_strategy_return": test_row["strategy_return"],
                "test_excess_return": test_row["excess_return"],
                "test_closed_trades": test_row["closed_trades"],
                "test_beats_buy_and_hold": test_row["beats_buy_and_hold"],
            }
        )

    report = {
        "thresholds": {
            "raw": list(thresholds),
            "isotonic": list(calibrated_thresholds) if include_calibrated else [],
        },
        "model_types": list(model_types),
        "feature_sets": list(feature_sets.keys()),
        "target_exit_configs": [asdict(config) for config in target_exit_configs],
        "signal_quality_configs": [asdict(config) for config in signal_quality_configs],
        "min_validation_trades": min_validation_trades,
        "folds": fold_summaries,
        "summary": summarize_walk_forward(fold_summaries),
    }
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_csv(output_csv, index=False)
    return report


def select_threshold_from_validation(
    validation_rows: list[dict[str, Any]],
    min_validation_trades: int = 10,
) -> dict[str, Any]:
    viable = [row for row in validation_rows if int(row.get("closed_trades", 0)) >= min_validation_trades]
    candidates = viable or validation_rows
    return max(
        candidates,
        key=lambda row: (
            _safe_float(row.get("excess_return")),
            _safe_float(row.get("strategy_return")),
            int(row.get("closed_trades", 0)),
        ),
    )


def summarize_walk_forward(fold_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not fold_summaries:
        return {
            "folds": 0,
            "mean_test_strategy_return": float("nan"),
            "mean_test_excess_return": float("nan"),
            "folds_beating_buy_and_hold": 0,
            "verdict": "no_folds",
        }

    strategy_returns = [_safe_float(row["test_strategy_return"]) for row in fold_summaries]
    excess_returns = [_safe_float(row["test_excess_return"]) for row in fold_summaries]
    beats = sum(bool(row["test_beats_buy_and_hold"]) for row in fold_summaries)
    mean_strategy = float(pd.Series(strategy_returns).mean())
    mean_excess = float(pd.Series(excess_returns).mean())
    if beats == len(fold_summaries) and mean_excess > 0:
        verdict = "walk_forward_passed"
    elif mean_strategy > 0:
        verdict = "positive_but_under_benchmark"
    else:
        verdict = "walk_forward_failed"

    return {
        "folds": int(len(fold_summaries)),
        "mean_test_strategy_return": mean_strategy,
        "mean_test_excess_return": mean_excess,
        "folds_beating_buy_and_hold": int(beats),
        "verdict": verdict,
    }


def _prepare_frames(target_exit_configs: tuple[TargetExitConfig, ...]) -> dict[str, dict[str, pd.DataFrame]]:
    raw = download_universe(UNIVERSE, start=FEATURE_START, pause_seconds=0.4)
    if "SPY" not in raw:
        raise RuntimeError("SPY data is required for the market trend filter")
    if len(raw) < 3:
        raise RuntimeError("Not enough tickers downloaded successfully")

    spy = raw["SPY"]
    scanned_frames: dict[str, pd.DataFrame] = {}
    for symbol, frame in raw.items():
        featured = build_features(frame, spy, market_news=None)
        featured["symbol"] = symbol
        scanned_frames[symbol] = add_scanner_columns(featured)

    prepared_by_target: dict[str, dict[str, pd.DataFrame]] = {}
    for config in target_exit_configs:
        prepared_by_target[config.name] = {
            symbol: build_trade_labels(
                scanned,
                stop_atr_multiple=config.stop_atr_multiple,
                take_profit_atr_multiple=config.take_profit_atr_multiple,
                timeout_bars=config.timeout_bars,
                max_gap_threshold=MAX_GAP_THRESHOLD,
            )
            for symbol, scanned in scanned_frames.items()
        }
    return prepared_by_target


def _evaluate_threshold(
    frames: dict[str, pd.DataFrame],
    fold: WalkForwardFold,
    period: str,
    target_exit_config: str,
    timeout_bars: int,
    feature_set: str,
    model_type: str,
    probability_variant: str,
    signal_quality_config: str,
    min_signal_quality_score: float | None,
    max_signals_per_day: int | None,
    rank_column: str,
    start: str,
    end: str,
    threshold: float,
) -> dict[str, Any]:
    backtest_rows: list[dict[str, Any]] = []
    signal_frames: list[pd.DataFrame] = []
    total_signals = 0
    total_signals_before_rank = 0
    executable_signals = 0
    closed_trades = 0
    symbols_with_signals = set()

    for symbol, frame in frames.items():
        signal_frames.append(
            add_signal_columns(
                frame,
                min_model_probability=threshold,
                min_signal_quality_score=min_signal_quality_score,
            )
        )

    ranked = apply_daily_signal_rank_filter(
        pd.concat(signal_frames).sort_index(),
        max_signals_per_day=max_signals_per_day,
        rank_column=rank_column,
    )

    for symbol, frame in ranked.groupby("symbol", sort=False):
        executable = add_execution_columns(frame.sort_index(), max_gap_threshold=MAX_GAP_THRESHOLD)
        window = executable.loc[start:end].copy()
        if len(window) < 50:
            continue

        symbol_signals_before_rank = int(window["signal_before_rank"].fillna(False).sum())
        symbol_signals = int(window["signal"].fillna(False).sum())
        symbol_executable = int((window["signal"].fillna(False) & window["execution_valid"].fillna(False)).sum())
        total_signals_before_rank += symbol_signals_before_rank
        total_signals += symbol_signals
        executable_signals += symbol_executable
        if symbol_signals > 0:
            symbols_with_signals.add(symbol)

        try:
            stats, summary = run_backtest(window, timeout_bars=timeout_bars)
        except Exception as exc:  # noqa: BLE001 - keep folds independent.
            backtest_rows.append({"symbol": symbol, "error": str(exc)})
            continue

        trades = int(stats.get("# Trades", 0))
        closed_trades += trades
        backtest_rows.append({"symbol": symbol, "trades": trades, **summary})

    aggregate = _aggregate_backtests(pd.DataFrame(backtest_rows))
    return {
        "fold": fold.name,
        "period": period,
        "target_exit_config": target_exit_config,
        "feature_set": feature_set,
        "model_type": model_type,
        "probability_variant": probability_variant,
        "signal_quality_config": signal_quality_config,
        "signal_rank_column": rank_column if max_signals_per_day is not None else "",
        "train_end": fold.train_end,
        "validation_start": fold.validation_start,
        "validation_end": fold.validation_end,
        "test_start": fold.test_start,
        "test_end": fold.test_end,
        "threshold": float(threshold),
        "selected_for_test": False,
        "strategy_return": aggregate.get("strategy_return"),
        "buy_and_hold_return": aggregate.get("buy_and_hold_return"),
        "excess_return": aggregate.get("excess_return"),
        "max_drawdown": aggregate.get("max_drawdown"),
        "sharpe": aggregate.get("sharpe"),
        "profit_factor": aggregate.get("profit_factor"),
        "win_rate": aggregate.get("win_rate"),
        "beats_buy_and_hold": aggregate.get("beats_buy_and_hold"),
        "total_signals_before_rank": total_signals_before_rank,
        "rank_filtered_signals": total_signals_before_rank - total_signals,
        "total_signals": total_signals,
        "executable_signals": executable_signals,
        "symbols_with_signals": len(symbols_with_signals),
        "closed_trades": closed_trades,
    }


def _target_config_by_name(
    target_exit_configs: tuple[TargetExitConfig, ...],
    name: str,
) -> TargetExitConfig:
    for config in target_exit_configs:
        if config.name == name:
            return config
    raise KeyError(f"Unknown target exit config: {name}")


def _signal_quality_config_by_name(
    signal_quality_configs: tuple[SignalQualityConfig, ...],
    name: str,
) -> SignalQualityConfig:
    for config in signal_quality_configs:
        if config.name == name:
            return config
    raise KeyError(f"Unknown signal quality config: {name}")


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


if __name__ == "__main__":
    result = run_walk_forward_validation()
    print(json.dumps(result["summary"], indent=2))
