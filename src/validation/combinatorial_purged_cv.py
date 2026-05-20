from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import comb
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CPCVConfig:
    n_groups: int
    n_test_groups: int
    label_start_column: str = "label_start"
    label_end_column: str = "label_end"
    embargo_days: int = 0
    symbol_column: str = "symbol"


@dataclass(frozen=True)
class CPCVSplit:
    split_id: int
    test_groups: tuple[int, ...]
    train_indices: tuple[int, ...]
    test_indices: tuple[int, ...]
    purged_indices: tuple[int, ...]
    embargoed_indices: tuple[int, ...]


def combinatorial_purged_cv_splits(frame: pd.DataFrame, config: CPCVConfig) -> list[CPCVSplit]:
    _validate_config(config)
    data = _prepared_frame(frame, config)
    group_by_position = _group_positions_by_time(data.index, config.n_groups)
    splits: list[CPCVSplit] = []

    for split_id, test_groups in enumerate(combinations(range(config.n_groups), config.n_test_groups)):
        test_positions = sorted(position for group_id in test_groups for position in group_by_position[group_id])
        train_candidate_positions = sorted(set(range(len(data))) - set(test_positions))
        purged_positions = _purged_positions(data, train_candidate_positions, test_positions, config)
        embargoed_positions = _embargoed_positions(data, train_candidate_positions, test_positions, config)
        excluded = set(test_positions) | set(purged_positions) | set(embargoed_positions)
        train_positions = tuple(position for position in range(len(data)) if position not in excluded)

        splits.append(
            CPCVSplit(
                split_id=split_id,
                test_groups=tuple(test_groups),
                train_indices=tuple(int(data.iloc[position]["_row_id"]) for position in train_positions),
                test_indices=tuple(int(data.iloc[position]["_row_id"]) for position in test_positions),
                purged_indices=tuple(int(data.iloc[position]["_row_id"]) for position in purged_positions),
                embargoed_indices=tuple(int(data.iloc[position]["_row_id"]) for position in embargoed_positions),
            )
        )

    return splits


def expected_cpcv_split_count(n_groups: int, n_test_groups: int) -> int:
    if n_groups < 2:
        raise ValueError("n_groups must be at least 2.")
    if n_test_groups < 1 or n_test_groups >= n_groups:
        raise ValueError("n_test_groups must be in [1, n_groups).")
    return comb(n_groups, n_test_groups)


def assert_no_label_overlap(frame: pd.DataFrame, split: CPCVSplit, config: CPCVConfig) -> None:
    data = _prepared_frame(frame, config)
    train = data[data["_row_id"].isin(split.train_indices)]
    test = data[data["_row_id"].isin(split.test_indices)]
    if test.empty:
        raise ValueError("test split must not be empty.")
    overlaps = _label_overlaps(train, test, config)
    if overlaps.any():
        raise ValueError("Training label windows overlap the test window.")


def _validate_config(config: CPCVConfig) -> None:
    expected_cpcv_split_count(config.n_groups, config.n_test_groups)
    if config.embargo_days < 0:
        raise ValueError("embargo_days must be non-negative.")


def _prepared_frame(frame: pd.DataFrame, config: CPCVConfig) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("frame must not be empty.")
    missing = [column for column in [config.label_start_column, config.label_end_column] if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing label interval columns: {missing}")

    data = frame.copy()
    data["_row_id"] = np.arange(len(data))
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)
    data = data.sort_index(kind="mergesort")
    data[config.label_start_column] = pd.to_datetime(data[config.label_start_column])
    data[config.label_end_column] = pd.to_datetime(data[config.label_end_column])
    if (data[config.label_end_column] < data[config.label_start_column]).any():
        raise ValueError("label_end must be greater than or equal to label_start.")
    return data


def _group_positions_by_time(index: pd.DatetimeIndex, n_groups: int) -> list[list[int]]:
    unique_dates = pd.Index(sorted(index.unique()))
    if len(unique_dates) < n_groups:
        raise ValueError("n_groups cannot exceed the number of unique timestamps.")
    date_groups = np.array_split(unique_dates, n_groups)
    groups: list[list[int]] = []
    for date_group in date_groups:
        date_set = set(pd.Timestamp(value) for value in date_group)
        groups.append([position for position, timestamp in enumerate(index) if pd.Timestamp(timestamp) in date_set])
    return groups


def _purged_positions(data: pd.DataFrame, train_positions: Iterable[int], test_positions: list[int], config: CPCVConfig) -> list[int]:
    train_position_list = list(train_positions)
    train = data.iloc[train_position_list]
    test = data.iloc[test_positions]
    overlap_mask = _label_overlaps(train, test, config)
    return [int(train_position_list[row_position]) for row_position, overlaps in enumerate(overlap_mask) if bool(overlaps)]


def _embargoed_positions(data: pd.DataFrame, train_positions: Iterable[int], test_positions: list[int], config: CPCVConfig) -> list[int]:
    if config.embargo_days == 0:
        return []
    train_position_list = list(train_positions)
    train = data.iloc[train_position_list]
    test = data.iloc[test_positions]
    embargo_mask = pd.Series(False, index=train.index)
    for _start, end in _contiguous_time_blocks(test.index):
        embargo_start = pd.Timestamp(end)
        embargo_end = embargo_start + pd.Timedelta(days=config.embargo_days)
        embargo_mask |= (train.index > embargo_start) & (train.index <= embargo_end)
    return [int(train_position_list[row_position]) for row_position, embargoed in enumerate(embargo_mask) if bool(embargoed)]


def _label_overlaps(train: pd.DataFrame, test: pd.DataFrame, config: CPCVConfig) -> pd.Series:
    mask = pd.Series(False, index=train.index)
    for start, end in _contiguous_time_blocks(test.index):
        test_start = pd.Timestamp(start)
        test_end = pd.Timestamp(end)
        mask |= (train[config.label_start_column] <= test_end) & (train[config.label_end_column] >= test_start)
    return mask


def _contiguous_time_blocks(index: pd.DatetimeIndex) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    dates = [pd.Timestamp(value) for value in sorted(index.unique())]
    if not dates:
        return []
    blocks: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    start = dates[0]
    previous = dates[0]
    for current in dates[1:]:
        if (current - previous).days > 1:
            blocks.append((start, previous))
            start = current
        previous = current
    blocks.append((start, previous))
    return blocks
