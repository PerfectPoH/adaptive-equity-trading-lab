from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.models.trainer import TemporalSplit, temporal_split


@dataclass(frozen=True)
class PurgedTemporalSplitConfig:
    train_end: str = "2022-12-30"
    validation_end: str = "2023-01-31"
    test_end: str = "2023-02-28"
    label_horizon_bars: int = 3
    embargo_days: int = 2
    symbols: tuple[str, ...] = ("AAA", "BBB", "CCC")


def validate_purged_temporal_split_embargo(config: PurgedTemporalSplitConfig | None = None) -> dict[str, Any]:
    active_config = config or PurgedTemporalSplitConfig()
    frame = build_synthetic_labeled_panel(active_config)
    split = temporal_split(
        frame,
        train_end=active_config.train_end,
        validation_end=active_config.validation_end,
        test_end=active_config.test_end,
        label_horizon_bars=active_config.label_horizon_bars,
        embargo_days=active_config.embargo_days,
    )
    checks: list[dict[str, str]] = []
    _validate_input_is_synthetic(frame, checks)
    _validate_non_empty_splits(split, checks)
    _validate_temporal_order(split, checks)
    _validate_no_index_overlap(split, checks)
    _validate_embargo(split, active_config, checks)
    _validate_purge_against_raw_boundaries(frame, split, active_config, checks)
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "research_id": "RESEARCH-062",
        "status": "pass" if failed == 0 else "fail",
        "decision": "PURGED_TEMPORAL_SPLIT_EMBARGO_VALIDATED" if failed == 0 else "PURGED_TEMPORAL_SPLIT_EMBARGO_BLOCKED",
        "market_data_downloaded": False,
        "provider_query_performed": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "config": {
            "train_end": active_config.train_end,
            "validation_end": active_config.validation_end,
            "test_end": active_config.test_end,
            "label_horizon_bars": active_config.label_horizon_bars,
            "embargo_days": active_config.embargo_days,
            "symbols": list(active_config.symbols),
        },
        "split_rows": {
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
        },
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
    }


def build_synthetic_labeled_panel(config: PurgedTemporalSplitConfig | None = None) -> pd.DataFrame:
    active_config = config or PurgedTemporalSplitConfig()
    index = pd.bdate_range("2022-12-01", "2023-03-15")
    rows = []
    for symbol_offset, symbol in enumerate(active_config.symbols):
        symbol_rows = pd.DataFrame(
            {
                "symbol": symbol,
                "feature": range(symbol_offset, symbol_offset + len(index)),
                "label": [int((row + symbol_offset) % 2 == 0) for row in range(len(index))],
                "label_executable": True,
                "synthetic_fixture": True,
            },
            index=index,
        )
        rows.append(symbol_rows)
    return pd.concat(rows).sort_index()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate purged temporal split and embargo invariants on synthetic data.")
    parser.add_argument("--train-end", default=PurgedTemporalSplitConfig.train_end)
    parser.add_argument("--validation-end", default=PurgedTemporalSplitConfig.validation_end)
    parser.add_argument("--test-end", default=PurgedTemporalSplitConfig.test_end)
    parser.add_argument("--label-horizon-bars", type=int, default=PurgedTemporalSplitConfig.label_horizon_bars)
    parser.add_argument("--embargo-days", type=int, default=PurgedTemporalSplitConfig.embargo_days)
    parser.add_argument("--output-json", default="")
    args = parser.parse_args(argv)
    report = validate_purged_temporal_split_embargo(
        PurgedTemporalSplitConfig(
            train_end=args.train_end,
            validation_end=args.validation_end,
            test_end=args.test_end,
            label_horizon_bars=args.label_horizon_bars,
            embargo_days=args.embargo_days,
        )
    )
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if report["status"] == "pass" else 1


def _validate_input_is_synthetic(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    synthetic = "synthetic_fixture" in frame.columns and frame["synthetic_fixture"].eq(True).all()
    _add_check(checks, "input_synthetic_only", bool(synthetic), f"rows={len(frame)}")


def _validate_non_empty_splits(split: TemporalSplit, checks: list[dict[str, str]]) -> None:
    _add_check(checks, "train_non_empty", not split.train.empty, f"rows={len(split.train)}")
    _add_check(checks, "validation_non_empty", not split.validation.empty, f"rows={len(split.validation)}")
    _add_check(checks, "test_non_empty", not split.test.empty, f"rows={len(split.test)}")


def _validate_temporal_order(split: TemporalSplit, checks: list[dict[str, str]]) -> None:
    ordered = split.train.index.max() < split.validation.index.min() < split.validation.index.max() < split.test.index.min()
    _add_check(checks, "split_temporal_order", bool(ordered), f"train_max={split.train.index.max()}; validation_min={split.validation.index.min()}; validation_max={split.validation.index.max()}; test_min={split.test.index.min()}")


def _validate_no_index_overlap(split: TemporalSplit, checks: list[dict[str, str]]) -> None:
    train_keys = _row_keys(split.train)
    validation_keys = _row_keys(split.validation)
    test_keys = _row_keys(split.test)
    no_overlap = train_keys.isdisjoint(validation_keys) and train_keys.isdisjoint(test_keys) and validation_keys.isdisjoint(test_keys)
    _add_check(checks, "split_row_keys_do_not_overlap", no_overlap, f"train={len(train_keys)}; validation={len(validation_keys)}; test={len(test_keys)}")


def _validate_embargo(split: TemporalSplit, config: PurgedTemporalSplitConfig, checks: list[dict[str, str]]) -> None:
    validation_start_floor = pd.Timestamp(config.train_end) + pd.Timedelta(days=1 + config.embargo_days)
    test_start_floor = pd.Timestamp(config.validation_end) + pd.Timedelta(days=1 + config.embargo_days)
    validation_ok = split.validation.index.min() >= validation_start_floor
    test_ok = split.test.index.min() >= test_start_floor
    _add_check(checks, "validation_embargo_respected", bool(validation_ok), f"min={split.validation.index.min()}; floor={validation_start_floor}")
    _add_check(checks, "test_embargo_respected", bool(test_ok), f"min={split.test.index.min()}; floor={test_start_floor}")


def _validate_purge_against_raw_boundaries(frame: pd.DataFrame, split: TemporalSplit, config: PurgedTemporalSplitConfig, checks: list[dict[str, str]]) -> None:
    raw_train = frame.loc[: config.train_end]
    raw_validation_start = pd.Timestamp(config.train_end) + pd.Timedelta(days=1 + config.embargo_days)
    raw_validation = frame.loc[raw_validation_start : config.validation_end]
    train_ok = _last_kept_equals_raw_minus_horizon(raw_train, split.train, config.label_horizon_bars)
    validation_ok = _last_kept_equals_raw_minus_horizon(raw_validation, split.validation, config.label_horizon_bars)
    _add_check(checks, "train_label_horizon_purged_by_symbol", train_ok, f"label_horizon_bars={config.label_horizon_bars}")
    _add_check(checks, "validation_label_horizon_purged_by_symbol", validation_ok, f"label_horizon_bars={config.label_horizon_bars}")


def _last_kept_equals_raw_minus_horizon(raw: pd.DataFrame, purged: pd.DataFrame, label_horizon_bars: int) -> bool:
    if label_horizon_bars <= 0:
        return True
    for symbol, raw_group in raw.groupby("symbol", sort=False):
        purged_group = purged[purged["symbol"] == symbol]
        if len(raw_group) <= label_horizon_bars:
            if not purged_group.empty:
                return False
            continue
        expected_last = raw_group.sort_index().index[-(label_horizon_bars + 1)]
        if purged_group.empty or purged_group.index.max() != expected_last:
            return False
    return True


def _row_keys(frame: pd.DataFrame) -> set[tuple[str, pd.Timestamp]]:
    return {(str(row.symbol), pd.Timestamp(index)) for index, row in frame.iterrows()}


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


if __name__ == "__main__":
    raise SystemExit(main())
