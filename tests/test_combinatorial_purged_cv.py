from __future__ import annotations

import pytest

import pandas as pd

from src.validation.combinatorial_purged_cv import (
    CPCVConfig,
    assert_no_label_overlap,
    combinatorial_purged_cv_splits,
    expected_cpcv_split_count,
)


def test_expected_cpcv_split_count_matches_binomial_coefficient() -> None:
    assert expected_cpcv_split_count(n_groups=5, n_test_groups=2) == 10
    assert expected_cpcv_split_count(n_groups=6, n_test_groups=3) == 20


def test_combinatorial_purged_cv_generates_all_combinations() -> None:
    frame = _synthetic_label_frame(rows=20, label_horizon_days=2)
    config = CPCVConfig(n_groups=5, n_test_groups=2, embargo_days=0)

    splits = combinatorial_purged_cv_splits(frame, config)

    assert len(splits) == 10
    assert {split.test_groups for split in splits} == {
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 4),
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 3),
        (2, 4),
        (3, 4),
    }


def test_combinatorial_purged_cv_removes_label_window_overlap() -> None:
    frame = _synthetic_label_frame(rows=15, label_horizon_days=4)
    config = CPCVConfig(n_groups=3, n_test_groups=1, embargo_days=0)

    splits = combinatorial_purged_cv_splits(frame, config)
    middle_split = next(split for split in splits if split.test_groups == (1,))

    assert middle_split.purged_indices
    assert 3 in middle_split.purged_indices
    assert 4 in middle_split.purged_indices
    assert 3 not in middle_split.train_indices
    assert 4 not in middle_split.train_indices
    assert_no_label_overlap(frame, middle_split, config)


def test_combinatorial_purged_cv_applies_embargo_after_test_block() -> None:
    frame = _synthetic_label_frame(rows=15, label_horizon_days=1)
    config = CPCVConfig(n_groups=3, n_test_groups=1, embargo_days=2)

    splits = combinatorial_purged_cv_splits(frame, config)
    first_split = next(split for split in splits if split.test_groups == (0,))

    assert 5 in first_split.embargoed_indices
    assert 6 in first_split.embargoed_indices
    assert 5 not in first_split.train_indices
    assert 6 not in first_split.train_indices
    assert_no_label_overlap(frame, first_split, config)


def test_combinatorial_purged_cv_keeps_train_and_test_disjoint() -> None:
    frame = _synthetic_label_frame(rows=18, label_horizon_days=2)
    config = CPCVConfig(n_groups=6, n_test_groups=2, embargo_days=1)

    for split in combinatorial_purged_cv_splits(frame, config):
        assert set(split.train_indices).isdisjoint(split.test_indices)
        assert set(split.train_indices).isdisjoint(split.purged_indices)
        assert set(split.train_indices).isdisjoint(split.embargoed_indices)
        assert_no_label_overlap(frame, split, config)


def test_combinatorial_purged_cv_rejects_invalid_config() -> None:
    frame = _synthetic_label_frame(rows=10, label_horizon_days=1)

    with pytest.raises(ValueError, match="n_test_groups"):
        combinatorial_purged_cv_splits(frame, CPCVConfig(n_groups=4, n_test_groups=4))

    with pytest.raises(ValueError, match="embargo_days"):
        combinatorial_purged_cv_splits(frame, CPCVConfig(n_groups=4, n_test_groups=1, embargo_days=-1))


def test_combinatorial_purged_cv_rejects_missing_label_interval_columns() -> None:
    frame = pd.DataFrame({"feature": [1, 2, 3]}, index=pd.date_range("2024-01-01", periods=3))

    with pytest.raises(ValueError, match="Missing label interval"):
        combinatorial_purged_cv_splits(frame, CPCVConfig(n_groups=2, n_test_groups=1))


def _synthetic_label_frame(rows: int, label_horizon_days: int) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    return pd.DataFrame(
        {
            "symbol": "AAA",
            "feature": range(rows),
            "label_start": index,
            "label_end": index + pd.Timedelta(days=label_horizon_days),
        },
        index=index,
    )
