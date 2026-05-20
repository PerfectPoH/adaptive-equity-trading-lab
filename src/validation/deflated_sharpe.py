from __future__ import annotations

from dataclasses import dataclass
from math import e, isfinite, sqrt
from statistics import NormalDist
from typing import Iterable

import numpy as np


EULER_MASCHERONI = 0.5772156649015329
STANDARD_NORMAL = NormalDist()


@dataclass(frozen=True)
class ReturnMoments:
    sample_size: int
    mean: float
    standard_deviation: float
    skewness: float
    kurtosis: float


@dataclass(frozen=True)
class DeflatedSharpeResult:
    observed_sharpe: float
    benchmark_sharpe: float
    expected_maximum_sharpe: float
    sample_size: int
    skewness: float
    kurtosis: float
    trial_count: float
    sharpe_std: float
    psr: float
    dsr: float
    passed: bool


def return_moments(returns: Iterable[float]) -> ReturnMoments:
    values = _finite_array(returns)
    if len(values) < 2:
        raise ValueError("At least two finite returns are required.")

    mean = float(values.mean())
    centered = values - mean
    variance = float(np.mean(centered**2))
    if variance <= 0:
        raise ValueError("Return standard deviation must be positive.")

    std = sqrt(variance)
    skewness = float(np.mean(centered**3) / std**3)
    # Pearson kurtosis convention: normal distribution has kurtosis 3.
    kurtosis = float(np.mean(centered**4) / variance**2)
    return ReturnMoments(sample_size=len(values), mean=mean, standard_deviation=std, skewness=skewness, kurtosis=kurtosis)


def sample_sharpe_ratio(returns: Iterable[float], risk_free_return: float = 0.0) -> float:
    values = _finite_array(returns)
    if len(values) < 2:
        raise ValueError("At least two finite returns are required.")
    excess = values - risk_free_return
    std = float(np.std(excess, ddof=1))
    if std <= 0:
        raise ValueError("Return standard deviation must be positive.")
    return float(np.mean(excess) / std)


def probabilistic_sharpe_ratio(
    observed_sharpe: float,
    benchmark_sharpe: float,
    sample_size: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    _validate_finite("observed_sharpe", observed_sharpe)
    _validate_finite("benchmark_sharpe", benchmark_sharpe)
    _validate_finite("skewness", skewness)
    _validate_finite("kurtosis", kurtosis)
    if sample_size < 2:
        raise ValueError("sample_size must be at least 2.")
    if kurtosis < 1:
        raise ValueError("kurtosis must use Pearson convention and be at least 1.")

    variance_term = 1 - skewness * observed_sharpe + ((kurtosis - 1) / 4) * observed_sharpe**2
    if variance_term <= 0:
        raise ValueError("PSR variance term must be positive.")

    z_score = (observed_sharpe - benchmark_sharpe) * sqrt(sample_size - 1) / sqrt(variance_term)
    return float(STANDARD_NORMAL.cdf(z_score))


def expected_maximum_sharpe_ratio(trial_count: float, sharpe_std: float = 1.0) -> float:
    _validate_finite("trial_count", trial_count)
    _validate_finite("sharpe_std", sharpe_std)
    if trial_count < 1:
        raise ValueError("trial_count must be at least 1.")
    if sharpe_std < 0:
        raise ValueError("sharpe_std must be non-negative.")
    if trial_count == 1 or sharpe_std == 0:
        return 0.0

    first_quantile = STANDARD_NORMAL.inv_cdf(1 - 1 / trial_count)
    second_quantile = STANDARD_NORMAL.inv_cdf(1 - 1 / (trial_count * e))
    return float(sharpe_std * ((1 - EULER_MASCHERONI) * first_quantile + EULER_MASCHERONI * second_quantile))


def deflated_sharpe_ratio(
    observed_sharpe: float,
    sample_size: int,
    skewness: float,
    kurtosis: float,
    trial_count: float,
    sharpe_std: float,
    confidence_threshold: float = 0.95,
) -> DeflatedSharpeResult:
    _validate_finite("confidence_threshold", confidence_threshold)
    if not 0 < confidence_threshold < 1:
        raise ValueError("confidence_threshold must be between 0 and 1.")

    benchmark = expected_maximum_sharpe_ratio(trial_count=trial_count, sharpe_std=sharpe_std)
    dsr = probabilistic_sharpe_ratio(
        observed_sharpe=observed_sharpe,
        benchmark_sharpe=benchmark,
        sample_size=sample_size,
        skewness=skewness,
        kurtosis=kurtosis,
    )
    return DeflatedSharpeResult(
        observed_sharpe=observed_sharpe,
        benchmark_sharpe=benchmark,
        expected_maximum_sharpe=benchmark,
        sample_size=sample_size,
        skewness=skewness,
        kurtosis=kurtosis,
        trial_count=trial_count,
        sharpe_std=sharpe_std,
        psr=dsr,
        dsr=dsr,
        passed=dsr >= confidence_threshold,
    )


def deflated_sharpe_ratio_from_returns(
    returns: Iterable[float],
    trial_count: float,
    sharpe_std: float,
    risk_free_return: float = 0.0,
    confidence_threshold: float = 0.95,
) -> DeflatedSharpeResult:
    moments = return_moments(returns)
    sharpe = sample_sharpe_ratio(returns, risk_free_return=risk_free_return)
    return deflated_sharpe_ratio(
        observed_sharpe=sharpe,
        sample_size=moments.sample_size,
        skewness=moments.skewness,
        kurtosis=moments.kurtosis,
        trial_count=trial_count,
        sharpe_std=sharpe_std,
        confidence_threshold=confidence_threshold,
    )


def _finite_array(values: Iterable[float]) -> np.ndarray:
    array = np.asarray(list(values), dtype=float)
    finite = array[np.isfinite(array)]
    if len(finite) != len(array):
        raise ValueError("All returns must be finite.")
    return finite


def _validate_finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")
