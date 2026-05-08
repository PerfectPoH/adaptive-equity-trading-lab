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
from src.risk.market_exposure import DEFAULT_MARKET_EXPOSURE_CONFIG, MarketExposureConfig, add_market_exposure_columns
from src.scanner.stock_scanner import add_scanner_columns
from src.strategy.signal_engine import add_signal_columns, apply_daily_signal_rank_filter


OUTPUT_JSON = Path("experiments/walk_forward_validation_latest.json")
OUTPUT_CSV = Path("experiments/walk_forward_validation_latest.csv")
THRESHOLDS = (0.45, 0.50, 0.55, 0.60, 0.65, 0.70)
CALIBRATED_THRESHOLDS = (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45)
DEFAULT_MODEL_TYPES = ("random_forest",)
DEFAULT_FEATURE_SETS = {"baseline": FEATURE_COLUMNS}


@dataclass(frozen=True)
class ModelConfig:
    name: str
    model_type: str
    model_params: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model_type": self.model_type,
            "model_params": self.model_params or {},
        }


DEFAULT_MODEL_CONFIGS = tuple(ModelConfig(name=model_type, model_type=model_type) for model_type in DEFAULT_MODEL_TYPES)


@dataclass(frozen=True)
class ModelObjectiveConfig:
    name: str
    label_column: str = "label"


DEFAULT_MODEL_OBJECTIVE_CONFIGS = (
    ModelObjectiveConfig(name="tp_before_sl", label_column="label"),
)


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
class SymbolSelectionConfig:
    name: str
    mode: str = "all"
    top_n: int | None = None
    min_symbol_trades: int = 5
    require_positive_strategy_return: bool = False
    include_symbols: tuple[str, ...] = ()
    exclude_symbols: tuple[str, ...] = ()


DEFAULT_SYMBOL_SELECTION_CONFIGS = (
    SymbolSelectionConfig(name="all_symbols"),
)


@dataclass(frozen=True)
class WalkForwardFold:
    name: str
    train_end: str
    validation_start: str
    validation_end: str
    test_start: str
    test_end: str


def build_annual_walk_forward_folds(
    first_validation_year: int,
    last_test_year: int,
) -> tuple[WalkForwardFold, ...]:
    if last_test_year <= first_validation_year:
        raise ValueError("last_test_year must be after first_validation_year")
    return tuple(
        WalkForwardFold(
            name=f"wf_{test_year}",
            train_end=f"{validation_year - 1}-12-31",
            validation_start=f"{validation_year}-01-01",
            validation_end=f"{validation_year}-12-31",
            test_start=f"{test_year}-01-01",
            test_end=f"{test_year}-12-31",
        )
        for validation_year, test_year in (
            (year, year + 1) for year in range(first_validation_year, last_test_year)
        )
    )


FOLDS = build_annual_walk_forward_folds(first_validation_year=2022, last_test_year=2024)


def run_walk_forward_validation(
    thresholds: tuple[float, ...] = THRESHOLDS,
    calibrated_thresholds: tuple[float, ...] = CALIBRATED_THRESHOLDS,
    model_types: tuple[str, ...] = DEFAULT_MODEL_TYPES,
    model_configs: tuple[ModelConfig, ...] | None = None,
    model_objective_configs: tuple[ModelObjectiveConfig, ...] = DEFAULT_MODEL_OBJECTIVE_CONFIGS,
    feature_sets: dict[str, list[str]] | None = None,
    target_exit_configs: tuple[TargetExitConfig, ...] = DEFAULT_TARGET_EXIT_CONFIGS,
    signal_quality_configs: tuple[SignalQualityConfig, ...] = DEFAULT_SIGNAL_QUALITY_CONFIGS,
    market_exposure_configs: tuple[MarketExposureConfig, ...] = (DEFAULT_MARKET_EXPOSURE_CONFIG,),
    symbol_selection_configs: tuple[SymbolSelectionConfig, ...] = DEFAULT_SYMBOL_SELECTION_CONFIGS,
    min_validation_trades: int = 10,
    include_calibrated: bool = True,
    output_json: Path = OUTPUT_JSON,
    output_csv: Path = OUTPUT_CSV,
) -> dict[str, Any]:
    feature_sets = feature_sets or DEFAULT_FEATURE_SETS
    active_model_configs = model_configs or tuple(ModelConfig(name=model_type, model_type=model_type) for model_type in model_types)
    prepared_by_target = _prepare_frames(target_exit_configs)

    rows: list[dict[str, Any]] = []
    fold_summaries: list[dict[str, Any]] = []
    for fold in FOLDS:
        frames_by_variant: dict[tuple[str, str, str, str, str, str], dict[str, pd.DataFrame]] = {}
        validation_rows = []
        for target_config in target_exit_configs:
            prepared = prepared_by_target[target_config.name]
            combined = pd.concat(prepared.values()).sort_index()

            for objective_config in model_objective_configs:
                objective_combined = _with_objective_label(combined, objective_config.label_column)
                train = purge_label_boundary(
                    objective_combined.loc[: fold.train_end].copy(),
                    label_horizon_bars=target_config.timeout_bars,
                )
                validation_for_calibration = purge_label_boundary(
                    objective_combined.loc[fold.validation_start : fold.validation_end].copy(),
                    label_horizon_bars=target_config.timeout_bars,
                )

                for feature_set_name, feature_columns in feature_sets.items():
                    for model_config in active_model_configs:
                        try:
                            model = fit_model(
                                train,
                                model_type=model_config.model_type,
                                model_params=model_config.model_params,
                                feature_columns=feature_columns,
                            )
                        except ValueError:
                            continue
                        probability_models = {"raw": model}
                        if include_calibrated:
                            try:
                                probability_models["isotonic"] = fit_probability_calibrator(
                                    model,
                                    validation_for_calibration,
                                    feature_columns=feature_columns,
                                    method="isotonic",
                                )
                            except ValueError:
                                pass
                        model_frames = {
                            (
                                target_config.name,
                                objective_config.name,
                                feature_set_name,
                                model_config.name,
                                model_config.model_type,
                                variant,
                            ): {
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
                            candidate_model_objective,
                            candidate_feature_set,
                            candidate_model_config,
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
                                    model_objective_config=candidate_model_objective,
                                    feature_set=candidate_feature_set,
                                    model_config=candidate_model_config,
                                    model_type=candidate_model_type,
                                    probability_variant=variant,
                                    signal_quality_config=quality_config.name,
                                    min_signal_quality_score=quality_config.min_signal_quality_score,
                                    max_signals_per_day=quality_config.max_signals_per_day,
                                    rank_column=quality_config.rank_column,
                                    market_exposure_config=market_exposure_config,
                                    symbol_selection_config=symbol_selection_config,
                                    start=fold.validation_start,
                                    end=fold.validation_end,
                                    threshold=threshold,
                                )
                                for quality_config in signal_quality_configs
                                for market_exposure_config in market_exposure_configs
                                for symbol_selection_config in symbol_selection_configs
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
        selected_market_exposure_config = _market_exposure_config_by_name(
            market_exposure_configs,
            str(selected["market_exposure_config"]),
        )
        selected_symbol_selection_config = _symbol_selection_config_by_name(
            symbol_selection_configs,
            str(selected["symbol_selection_config"]),
        )
        selected_symbols = _deserialize_symbols(str(selected.get("selected_symbols", "")))
        test_row = _evaluate_threshold(
            frames_by_variant[
                (
                    str(selected["target_exit_config"]),
                    str(selected["model_objective_config"]),
                    str(selected["feature_set"]),
                    str(selected["model_config"]),
                    str(selected["model_type"]),
                    str(selected["probability_variant"]),
                )
            ],
            fold=fold,
            period="test",
            target_exit_config=str(selected["target_exit_config"]),
            timeout_bars=selected_target_config.timeout_bars,
            model_objective_config=str(selected["model_objective_config"]),
            feature_set=str(selected["feature_set"]),
            model_config=str(selected["model_config"]),
            model_type=str(selected["model_type"]),
            probability_variant=str(selected["probability_variant"]),
            signal_quality_config=str(selected["signal_quality_config"]),
            min_signal_quality_score=selected_quality_config.min_signal_quality_score,
            max_signals_per_day=selected_quality_config.max_signals_per_day,
            rank_column=selected_quality_config.rank_column,
            market_exposure_config=selected_market_exposure_config,
            symbol_selection_config=selected_symbol_selection_config,
            forced_symbols=selected_symbols,
            start=fold.test_start,
            end=fold.test_end,
            threshold=float(selected["threshold"]),
        )
        test_row["selected_for_test"] = True

        for row in validation_rows:
            row["selected_for_test"] = (
                row["target_exit_config"] == selected["target_exit_config"]
                and row["model_objective_config"] == selected["model_objective_config"]
                and row["feature_set"] == selected["feature_set"]
                and row["model_config"] == selected["model_config"]
                and row["model_type"] == selected["model_type"]
                and row["probability_variant"] == selected["probability_variant"]
                and row["signal_quality_config"] == selected["signal_quality_config"]
                and row["market_exposure_config"] == selected["market_exposure_config"]
                and row["symbol_selection_config"] == selected["symbol_selection_config"]
                and float(row["threshold"]) == float(selected["threshold"])
            )
        rows.extend(validation_rows)
        rows.append(test_row)
        fold_summaries.append(
            {
                "fold": fold.name,
                "selected_target_exit_config": str(selected["target_exit_config"]),
                "selected_model_objective_config": str(selected["model_objective_config"]),
                "selected_feature_set": str(selected["feature_set"]),
                "selected_model_config": str(selected["model_config"]),
                "selected_model_type": str(selected["model_type"]),
                "selected_probability_variant": str(selected["probability_variant"]),
                "selected_signal_quality_config": str(selected["signal_quality_config"]),
                "selected_signal_rank_column": str(selected.get("signal_rank_column", "")),
                "selected_market_exposure_config": str(selected["market_exposure_config"]),
                "selected_symbol_selection_config": str(selected["symbol_selection_config"]),
                "selected_symbols": str(selected.get("selected_symbols", "")),
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
        "model_types": list(dict.fromkeys(config.model_type for config in active_model_configs)),
        "model_configs": [config.to_dict() for config in active_model_configs],
        "model_objective_configs": [asdict(config) for config in model_objective_configs],
        "feature_sets": list(feature_sets.keys()),
        "target_exit_configs": [asdict(config) for config in target_exit_configs],
        "signal_quality_configs": [asdict(config) for config in signal_quality_configs],
        "market_exposure_configs": [asdict(config) for config in market_exposure_configs],
        "symbol_selection_configs": [asdict(config) for config in symbol_selection_configs],
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


def _with_objective_label(frame: pd.DataFrame, label_column: str) -> pd.DataFrame:
    if label_column not in frame.columns:
        raise ValueError(f"Objective label column is missing: {label_column}")
    data = frame.copy()
    data["label"] = pd.to_numeric(data[label_column], errors="coerce")
    return data


def _evaluate_threshold(
    frames: dict[str, pd.DataFrame],
    fold: WalkForwardFold,
    period: str,
    target_exit_config: str,
    timeout_bars: int,
    model_objective_config: str,
    feature_set: str,
    model_config: str,
    model_type: str,
    probability_variant: str,
    signal_quality_config: str,
    min_signal_quality_score: float | None,
    max_signals_per_day: int | None,
    rank_column: str,
    market_exposure_config: MarketExposureConfig,
    symbol_selection_config: SymbolSelectionConfig,
    start: str,
    end: str,
    threshold: float,
    forced_symbols: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    symbol_rows: list[dict[str, Any]] = []
    signal_frames: list[pd.DataFrame] = []

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
    exposure_adjusted = add_market_exposure_columns(ranked, market_exposure_config)

    for symbol, frame in exposure_adjusted.groupby("symbol", sort=False):
        executable = add_execution_columns(frame.sort_index(), max_gap_threshold=MAX_GAP_THRESHOLD)
        window = executable.loc[start:end].copy()
        if len(window) < 50:
            continue

        symbol_signals_before_rank = int(window["signal_before_rank"].fillna(False).sum())
        symbol_signals = int(window["signal"].fillna(False).sum())
        symbol_executable = int((window["signal"].fillna(False) & window["execution_valid"].fillna(False)).sum())

        try:
            stats, summary = run_backtest(window, timeout_bars=timeout_bars)
        except Exception as exc:  # noqa: BLE001 - keep folds independent.
            symbol_rows.append(
                {
                    "symbol": symbol,
                    "error": str(exc),
                    "total_signals_before_rank": symbol_signals_before_rank,
                    "total_signals": symbol_signals,
                    "executable_signals": symbol_executable,
                    "strong_market_signals": _strong_market_signal_count(window, start, end),
                }
            )
            continue

        trades = int(stats.get("# Trades", 0))
        symbol_rows.append(
            {
                "symbol": symbol,
                "trades": trades,
                "total_signals_before_rank": symbol_signals_before_rank,
                "total_signals": symbol_signals,
                "executable_signals": symbol_executable,
                "strong_market_signals": _strong_market_signal_count(window, start, end),
                **summary,
            }
        )

    selected_symbols = _select_symbols(symbol_rows, symbol_selection_config, forced_symbols=forced_symbols)
    selected_rows = [row for row in symbol_rows if str(row.get("symbol")) in selected_symbols]
    aggregate = _aggregate_backtests(pd.DataFrame(selected_rows))
    return {
        "fold": fold.name,
        "period": period,
        "target_exit_config": target_exit_config,
        "model_objective_config": model_objective_config,
        "feature_set": feature_set,
        "model_config": model_config,
        "model_type": model_type,
        "probability_variant": probability_variant,
        "signal_quality_config": signal_quality_config,
        "signal_rank_column": rank_column if max_signals_per_day is not None else "",
        "market_exposure_config": market_exposure_config.name,
        "symbol_selection_config": symbol_selection_config.name,
        "selected_symbols": ",".join(selected_symbols),
        "selected_symbol_count": len(selected_symbols),
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
        "total_signals_before_rank": _sum_selected(selected_rows, "total_signals_before_rank"),
        "rank_filtered_signals": _sum_selected(selected_rows, "total_signals_before_rank")
        - _sum_selected(selected_rows, "total_signals"),
        "total_signals": _sum_selected(selected_rows, "total_signals"),
        "executable_signals": _sum_selected(selected_rows, "executable_signals"),
        "avg_risk_fraction_on_signals": _avg_risk_fraction_on_signals(
            exposure_adjusted,
            start,
            end,
            selected_symbols,
        ),
        "strong_market_signals": _sum_selected(selected_rows, "strong_market_signals"),
        "symbols_with_signals": _symbols_with_selected_signals(selected_rows),
        "closed_trades": _sum_selected(selected_rows, "trades"),
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


def _market_exposure_config_by_name(
    market_exposure_configs: tuple[MarketExposureConfig, ...],
    name: str,
) -> MarketExposureConfig:
    for config in market_exposure_configs:
        if config.name == name:
            return config
    raise KeyError(f"Unknown market exposure config: {name}")


def _symbol_selection_config_by_name(
    symbol_selection_configs: tuple[SymbolSelectionConfig, ...],
    name: str,
) -> SymbolSelectionConfig:
    for config in symbol_selection_configs:
        if config.name == name:
            return config
    raise KeyError(f"Unknown symbol selection config: {name}")


def _select_symbols(
    symbol_rows: list[dict[str, Any]],
    config: SymbolSelectionConfig,
    forced_symbols: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    if forced_symbols is not None:
        present = {str(row.get("symbol")) for row in symbol_rows if row.get("symbol") and "error" not in row}
        forced = tuple(symbol for symbol in forced_symbols if symbol in present)
        return forced or tuple(symbol for symbol in forced_symbols if symbol)

    eligible = [row for row in symbol_rows if row.get("symbol") and "error" not in row]

    if config.include_symbols:
        include = set(config.include_symbols)
        eligible = [row for row in eligible if str(row.get("symbol")) in include]
    if config.exclude_symbols:
        exclude = set(config.exclude_symbols)
        eligible = [row for row in eligible if str(row.get("symbol")) not in exclude]

    if config.mode == "all":
        return tuple(sorted(str(row["symbol"]) for row in eligible if row.get("symbol")))

    available = [row for row in eligible if int(row.get("trades", 0)) >= config.min_symbol_trades]

    if config.require_positive_strategy_return:
        positive = [row for row in available if _safe_float(row.get("strategy_return")) > 0]
        if positive:
            available = positive

    if not available:
        fallback = [str(row.get("symbol")) for row in eligible if row.get("symbol")]
        return tuple(sorted(fallback))

    if config.mode == "top_n_strategy_return":
        selected = _top_n_symbols(available, "strategy_return", config.top_n)
    elif config.mode == "top_n_excess_return":
        selected = _top_n_symbols(available, "excess_return", config.top_n)
    elif config.mode == "top_n_sharpe":
        selected = _top_n_symbols(available, "sharpe", config.top_n)
    elif config.mode == "positive_strategy_return":
        selected = [row for row in available if _safe_float(row.get("strategy_return")) > 0] or available
    else:
        raise ValueError(f"Unsupported symbol selection mode: {config.mode}")

    return tuple(sorted(str(row["symbol"]) for row in selected if row.get("symbol")))


def _top_n_symbols(rows: list[dict[str, Any]], metric: str, top_n: int | None) -> list[dict[str, Any]]:
    if top_n is None or top_n <= 0:
        raise ValueError("top_n must be positive for top_n symbol selection modes")
    return sorted(
        rows,
        key=lambda row: (
            _sort_metric(row.get(metric)),
            _sort_metric(row.get("strategy_return")),
            int(row.get("trades", 0)),
        ),
        reverse=True,
    )[:top_n]


def _deserialize_symbols(value: str) -> tuple[str, ...]:
    return tuple(symbol for symbol in value.split(",") if symbol)


def _sum_selected(rows: list[dict[str, Any]], key: str) -> int:
    total = 0
    for row in rows:
        try:
            total += int(row.get(key, 0))
        except (TypeError, ValueError):
            continue
    return total


def _symbols_with_selected_signals(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if int(row.get("total_signals", 0)) > 0)


def _avg_risk_fraction_on_signals(
    frame: pd.DataFrame,
    start: str,
    end: str,
    selected_symbols: tuple[str, ...],
) -> float:
    window = frame.loc[start:end].copy()
    if window.empty or "risk_fraction" not in window.columns:
        return float("nan")
    if selected_symbols and "symbol" in window.columns:
        window = window[window["symbol"].astype(str).isin(selected_symbols)].copy()
    signal_mask = window.get("signal", False).fillna(False).astype(bool)
    if not signal_mask.any():
        return float("nan")
    return _safe_float(pd.to_numeric(window.loc[signal_mask, "risk_fraction"], errors="coerce").mean())


def _strong_market_signal_count(frame: pd.DataFrame, start: str, end: str) -> int:
    window = frame.loc[start:end].copy()
    if window.empty or "market_regime_strong" not in window.columns:
        return 0
    signal_mask = window.get("signal", False).fillna(False).astype(bool)
    strong_mask = window["market_regime_strong"].fillna(False).astype(bool)
    return int((signal_mask & strong_mask).sum())


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _sort_metric(value: object) -> float:
    parsed = _safe_float(value)
    if pd.isna(parsed):
        return float("-inf")
    return parsed


if __name__ == "__main__":
    result = run_walk_forward_validation()
    print(json.dumps(result["summary"], indent=2))
