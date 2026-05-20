from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.validation.effective_trial_count import (
    effective_trial_count_from_correlation,
    effective_trial_count_from_returns,
)


def test_effective_trial_count_identity_equals_nominal_count() -> None:
    result = effective_trial_count_from_correlation(np.eye(5))

    assert result.nominal_count == 5
    assert result.effective_count == pytest.approx(5.0)
    assert result.mean_off_diagonal_correlation == pytest.approx(0.0)


def test_effective_trial_count_perfect_correlation_equals_one() -> None:
    result = effective_trial_count_from_correlation(np.ones((4, 4)))

    assert result.nominal_count == 4
    assert result.effective_count == pytest.approx(1.0)
    assert result.mean_off_diagonal_correlation == pytest.approx(1.0)


def test_effective_trial_count_stays_inside_real_boundary() -> None:
    corr = _equicorrelation_matrix(size=6, rho=0.4)

    result = effective_trial_count_from_correlation(corr)

    assert 1 <= result.effective_count <= result.nominal_count


def test_effective_trial_count_decreases_as_correlation_increases() -> None:
    independent = effective_trial_count_from_correlation(_equicorrelation_matrix(6, 0.0))
    moderate = effective_trial_count_from_correlation(_equicorrelation_matrix(6, 0.5))
    high = effective_trial_count_from_correlation(_equicorrelation_matrix(6, 0.9))

    assert independent.effective_count > moderate.effective_count > high.effective_count


def test_average_correlation_method_matches_closed_form_boundaries() -> None:
    independent = effective_trial_count_from_correlation(np.eye(4), method="average_correlation")
    perfect = effective_trial_count_from_correlation(np.ones((4, 4)), method="average_correlation")

    assert independent.effective_count == pytest.approx(4.0)
    assert perfect.effective_count == pytest.approx(1.0)


def test_effective_trial_count_from_returns_detects_correlated_trials() -> None:
    base = np.linspace(-1, 1, 50)
    frame = pd.DataFrame(
        {
            "trial_a": base,
            "trial_b": base * 2,
            "trial_c": -base,
            "trial_d": np.sin(np.linspace(0, 12, 50)),
        }
    )

    result = effective_trial_count_from_returns(frame)

    assert result.nominal_count == 4
    assert 1 <= result.effective_count < 4


def test_effective_trial_count_rejects_constant_trial_returns() -> None:
    with pytest.raises(ValueError, match="positive standard deviation"):
        effective_trial_count_from_returns([[1, 1], [1, 2], [1, 3]])


def test_effective_trial_count_rejects_bad_correlation_matrix() -> None:
    with pytest.raises(ValueError, match="symmetric"):
        effective_trial_count_from_correlation([[1, 0.2], [0.3, 1]])

    with pytest.raises(ValueError, match="diagonal"):
        effective_trial_count_from_correlation([[0.9, 0.2], [0.2, 1]])

    with pytest.raises(ValueError, match="square"):
        effective_trial_count_from_correlation([[1, 0.2, 0.3], [0.2, 1, 0.4]])


def test_effective_trial_count_rejects_unknown_method() -> None:
    with pytest.raises(ValueError, match="method"):
        effective_trial_count_from_correlation(np.eye(3), method="onc")


def _equicorrelation_matrix(size: int, rho: float) -> np.ndarray:
    matrix = np.full((size, size), rho, dtype=float)
    np.fill_diagonal(matrix, 1.0)
    return matrix
