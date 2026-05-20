from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EffectiveTrialCountResult:
    nominal_count: int
    effective_count: float
    method: str
    mean_off_diagonal_correlation: float
    eigenvalues: tuple[float, ...]


def effective_trial_count_from_returns(
    trial_returns: pd.DataFrame | np.ndarray | Iterable[Iterable[float]],
    method: str = "participation_ratio",
) -> EffectiveTrialCountResult:
    matrix = _finite_2d_array(trial_returns)
    if matrix.shape[1] < 1:
        raise ValueError("At least one trial return series is required.")
    if matrix.shape[0] < 2:
        raise ValueError("At least two observations per trial are required.")

    corr = _correlation_matrix(matrix)
    return effective_trial_count_from_correlation(corr, method=method)


def effective_trial_count_from_correlation(
    correlation_matrix: pd.DataFrame | np.ndarray | Iterable[Iterable[float]],
    method: str = "participation_ratio",
) -> EffectiveTrialCountResult:
    corr = _finite_square_array(correlation_matrix)
    _validate_correlation_matrix(corr)
    nominal = corr.shape[0]
    eigenvalues = tuple(float(value) for value in np.linalg.eigvalsh(corr))
    mean_corr = _mean_off_diagonal_correlation(corr)

    if method == "participation_ratio":
        raw_effective = _participation_ratio(eigenvalues)
    elif method == "average_correlation":
        raw_effective = _average_correlation_effective_count(nominal, mean_corr)
    else:
        raise ValueError("method must be 'participation_ratio' or 'average_correlation'.")

    return EffectiveTrialCountResult(
        nominal_count=nominal,
        effective_count=_clip_effective_count(raw_effective, nominal),
        method=method,
        mean_off_diagonal_correlation=mean_corr,
        eigenvalues=eigenvalues,
    )


def _participation_ratio(eigenvalues: Iterable[float]) -> float:
    values = np.asarray(list(eigenvalues), dtype=float)
    positive = np.clip(values, 0.0, None)
    denominator = float(np.sum(positive**2))
    if denominator <= 0:
        raise ValueError("Eigenvalue energy must be positive.")
    return float(np.sum(positive) ** 2 / denominator)


def _average_correlation_effective_count(nominal_count: int, mean_correlation: float) -> float:
    denominator = 1 + (nominal_count - 1) * max(mean_correlation, 0.0)
    if denominator <= 0:
        return float(nominal_count)
    return float(nominal_count / denominator)


def _correlation_matrix(matrix: np.ndarray) -> np.ndarray:
    if matrix.shape[1] == 1:
        return np.ones((1, 1), dtype=float)
    standard_deviations = np.std(matrix, axis=0, ddof=1)
    if np.any(standard_deviations <= 0):
        raise ValueError("Trial return series must have positive standard deviation.")
    return np.corrcoef(matrix, rowvar=False)


def _mean_off_diagonal_correlation(corr: np.ndarray) -> float:
    if corr.shape[0] == 1:
        return 1.0
    mask = ~np.eye(corr.shape[0], dtype=bool)
    return float(np.mean(corr[mask]))


def _clip_effective_count(value: float, nominal_count: int) -> float:
    if not isfinite(value):
        raise ValueError("Effective trial count must be finite.")
    return float(min(max(value, 1.0), float(nominal_count)))


def _finite_2d_array(values: pd.DataFrame | np.ndarray | Iterable[Iterable[float]]) -> np.ndarray:
    if isinstance(values, pd.DataFrame):
        array = values.to_numpy(dtype=float)
    else:
        array = np.asarray(values, dtype=float)
    if array.ndim != 2:
        raise ValueError("Input must be a 2D matrix with rows as observations and columns as trials.")
    if not np.isfinite(array).all():
        raise ValueError("All trial return values must be finite.")
    return array


def _finite_square_array(values: pd.DataFrame | np.ndarray | Iterable[Iterable[float]]) -> np.ndarray:
    array = _finite_2d_array(values)
    if array.shape[0] != array.shape[1]:
        raise ValueError("Correlation matrix must be square.")
    return array


def _validate_correlation_matrix(corr: np.ndarray) -> None:
    if not np.allclose(corr, corr.T, atol=1e-10):
        raise ValueError("Correlation matrix must be symmetric.")
    if not np.allclose(np.diag(corr), 1.0, atol=1e-10):
        raise ValueError("Correlation matrix diagonal must be 1.")
    if np.any(corr < -1.0 - 1e-10) or np.any(corr > 1.0 + 1e-10):
        raise ValueError("Correlation matrix values must be in [-1, 1].")
