from __future__ import annotations

import math

import pytest

from src.validation.deflated_sharpe import (
    deflated_sharpe_ratio,
    expected_maximum_sharpe_ratio,
    probabilistic_sharpe_ratio,
    return_moments,
    sample_sharpe_ratio,
)


def test_expected_maximum_sharpe_matches_known_formula_values() -> None:
    assert expected_maximum_sharpe_ratio(trial_count=1, sharpe_std=1.0) == pytest.approx(0.0)
    assert expected_maximum_sharpe_ratio(trial_count=10, sharpe_std=1.0) == pytest.approx(1.5745983013)
    assert expected_maximum_sharpe_ratio(trial_count=100, sharpe_std=1.0) == pytest.approx(2.5306028932)
    assert expected_maximum_sharpe_ratio(trial_count=1000, sharpe_std=1.0) == pytest.approx(3.2551215137)


def test_probabilistic_sharpe_ratio_uses_pearson_kurtosis_convention() -> None:
    psr = probabilistic_sharpe_ratio(
        observed_sharpe=0.5,
        benchmark_sharpe=0.0,
        sample_size=101,
        skewness=0.0,
        kurtosis=3.0,
    )

    assert psr == pytest.approx(0.9999987858)


def test_probabilistic_sharpe_ratio_penalizes_bad_skew_and_fat_tails() -> None:
    normal_psr = probabilistic_sharpe_ratio(1.0, 0.0, sample_size=252, skewness=0.0, kurtosis=3.0)
    fat_tail_psr = probabilistic_sharpe_ratio(1.0, 0.0, sample_size=252, skewness=-2.0, kurtosis=9.0)

    assert normal_psr > fat_tail_psr
    assert fat_tail_psr > 0.95


def test_deflated_sharpe_ratio_can_fail_despite_high_raw_sharpe() -> None:
    result = deflated_sharpe_ratio(
        observed_sharpe=2.1,
        sample_size=252,
        skewness=-1.0,
        kurtosis=8.0,
        trial_count=50,
        sharpe_std=0.5,
        confidence_threshold=0.95,
    )

    assert result.expected_maximum_sharpe == pytest.approx(1.1381515467)
    assert result.dsr == pytest.approx(0.9999981996)
    assert result.passed is True

    harsher_result = deflated_sharpe_ratio(
        observed_sharpe=2.1,
        sample_size=252,
        skewness=-1.0,
        kurtosis=8.0,
        trial_count=50,
        sharpe_std=0.8,
        confidence_threshold=0.95,
    )

    assert harsher_result.expected_maximum_sharpe == pytest.approx(1.8210424747)
    assert harsher_result.dsr == pytest.approx(0.9104818821)
    assert harsher_result.passed is False


def test_return_moments_exposes_pearson_kurtosis() -> None:
    moments = return_moments([-2, -1, 0, 1, 2])

    assert moments.sample_size == 5
    assert moments.mean == pytest.approx(0.0)
    assert moments.skewness == pytest.approx(0.0)
    assert moments.kurtosis == pytest.approx(1.7)


def test_sample_sharpe_ratio_rejects_constant_returns() -> None:
    with pytest.raises(ValueError, match="standard deviation"):
        sample_sharpe_ratio([0.01, 0.01, 0.01])


def test_probabilistic_sharpe_ratio_rejects_excess_kurtosis_input() -> None:
    with pytest.raises(ValueError, match="Pearson"):
        probabilistic_sharpe_ratio(0.5, 0.0, sample_size=100, skewness=0.0, kurtosis=0.0)


def test_probabilistic_sharpe_ratio_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match="observed_sharpe"):
        probabilistic_sharpe_ratio(math.nan, 0.0, sample_size=100)
