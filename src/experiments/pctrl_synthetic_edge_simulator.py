"""Positive control: inject a synthetic edge and measure statistical-gate power.

This module is the counterpart of ``nctrl_random_entry_simulator``. The negative
control verifies that the gates reject pure noise; the positive control verifies
that the gates accept a known edge once sample size and effect size are
sufficient. Together they let us measure the **power** of the DSR gate, i.e.
the minimum number of trades required to detect a given per-trade edge after
correcting for the multiple trials the program ran.

The simulator stays at the statistical layer (no broker, no universe, no
yfinance dependency): we sample IID returns directly. That keeps the power
curve dependent only on the gate math, not on data quality or execution
slippage, which is exactly what we want when calibrating ``DSR + N_eff``.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

import numpy as np

from src.validation.deflated_sharpe import (
    DeflatedSharpeResult,
    deflated_sharpe_ratio,
    return_moments,
    sample_sharpe_ratio,
)


@dataclass(frozen=True)
class PositiveControlConfig:
    """Parameters describing one (sample_size, effect_size) cell.

    Attributes
    ----------
    sample_size:
        Number of per-trade returns observed for the candidate trial.
    effect_size_mean:
        True mean of the candidate trial's returns (the injected edge).
    return_volatility:
        Per-trade return standard deviation, fixed across cells so that
        Sharpe = effect_size_mean / return_volatility.
    trial_count_searched:
        Number of program-level trials the researcher has actually run.
        This drives the DSR multiplicity penalty and matters more than the
        in-cell candidate count.
    noise_trials_for_dispersion:
        Number of pure-noise trials simulated alongside the candidate to
        estimate ``sharpe_std`` for the DSR benchmark. These exist only to
        calibrate the gate; they are not "candidates".
    bootstrap_iterations:
        Number of independent simulations of the cell used to estimate the
        empirical pass rate (= power when effect>0, type-I when effect=0).
    confidence_threshold:
        DSR confidence threshold (Bailey & Lopez de Prado).
    base_seed:
        Seed seed.
    """

    sample_size: int
    effect_size_mean: float
    return_volatility: float = 0.02
    trial_count_searched: int = 30
    noise_trials_for_dispersion: int = 30
    bootstrap_iterations: int = 200
    confidence_threshold: float = 0.95
    base_seed: int = 1701

    def __post_init__(self) -> None:
        if self.sample_size < 2:
            raise ValueError("sample_size must be at least 2")
        if not isfinite(self.effect_size_mean):
            raise ValueError("effect_size_mean must be finite")
        if self.return_volatility <= 0:
            raise ValueError("return_volatility must be positive")
        if self.trial_count_searched < 1:
            raise ValueError("trial_count_searched must be at least 1")
        if self.noise_trials_for_dispersion < 2:
            raise ValueError("noise_trials_for_dispersion must be at least 2")
        if self.bootstrap_iterations < 1:
            raise ValueError("bootstrap_iterations must be at least 1")
        if not 0.0 < self.confidence_threshold < 1.0:
            raise ValueError("confidence_threshold must be in (0, 1)")


@dataclass(frozen=True)
class PositiveControlCellResult:
    sample_size: int
    effect_size_mean: float
    return_volatility: float
    annualized_edge_sharpe: float
    trial_count_searched: int
    bootstrap_iterations: int
    pass_count: int
    pass_rate: float
    mean_observed_sharpe: float
    mean_dsr: float
    mean_benchmark_sharpe: float


def evaluate_positive_control_cell(config: PositiveControlConfig) -> PositiveControlCellResult:
    """Run the DSR gate ``bootstrap_iterations`` times and report empirical power."""

    passes = 0
    observed_sharpes: list[float] = []
    dsrs: list[float] = []
    benchmarks: list[float] = []
    for iteration in range(config.bootstrap_iterations):
        seed = config.base_seed + iteration
        result = _single_evaluation(config, seed=seed)
        if result.passed:
            passes += 1
        observed_sharpes.append(result.observed_sharpe)
        dsrs.append(result.dsr)
        benchmarks.append(result.benchmark_sharpe)
    annualized = (
        config.effect_size_mean / config.return_volatility * float(np.sqrt(252))
    )
    return PositiveControlCellResult(
        sample_size=config.sample_size,
        effect_size_mean=config.effect_size_mean,
        return_volatility=config.return_volatility,
        annualized_edge_sharpe=annualized,
        trial_count_searched=config.trial_count_searched,
        bootstrap_iterations=config.bootstrap_iterations,
        pass_count=passes,
        pass_rate=passes / config.bootstrap_iterations,
        mean_observed_sharpe=float(np.mean(observed_sharpes)),
        mean_dsr=float(np.mean(dsrs)),
        mean_benchmark_sharpe=float(np.mean(benchmarks)),
    )


def _single_evaluation(config: PositiveControlConfig, seed: int) -> DeflatedSharpeResult:
    rng = np.random.default_rng(seed)
    edge_returns = rng.normal(config.effect_size_mean, config.return_volatility, size=config.sample_size)
    noise_returns = rng.normal(
        0.0,
        config.return_volatility,
        size=(config.sample_size, config.noise_trials_for_dispersion),
    )
    noise_sharpes = np.asarray(
        [sample_sharpe_ratio(noise_returns[:, k]) for k in range(noise_returns.shape[1])],
        dtype=float,
    )
    sharpe_std = float(np.std(noise_sharpes, ddof=1))
    if sharpe_std <= 0:
        sharpe_std = 1e-6
    observed_sharpe = sample_sharpe_ratio(edge_returns)
    moments = return_moments(edge_returns)
    return deflated_sharpe_ratio(
        observed_sharpe=observed_sharpe,
        sample_size=moments.sample_size,
        skewness=moments.skewness,
        kurtosis=moments.kurtosis,
        trial_count=float(config.trial_count_searched),
        sharpe_std=sharpe_std,
        confidence_threshold=config.confidence_threshold,
    )


@dataclass(frozen=True)
class PowerCurveSpec:
    sample_sizes: tuple[int, ...]
    effect_sizes: tuple[float, ...]
    return_volatility: float = 0.02
    trial_count_searched: int = 30
    noise_trials_for_dispersion: int = 30
    bootstrap_iterations: int = 200
    confidence_threshold: float = 0.95
    base_seed: int = 1701


def run_power_curve(spec: PowerCurveSpec) -> list[PositiveControlCellResult]:
    """Sweep (sample_size, effect_size) and return empirical pass rates."""

    results: list[PositiveControlCellResult] = []
    cell_index = 0
    for sample_size in spec.sample_sizes:
        for effect_size in spec.effect_sizes:
            cell_seed = spec.base_seed + cell_index * spec.bootstrap_iterations
            cell_config = PositiveControlConfig(
                sample_size=sample_size,
                effect_size_mean=effect_size,
                return_volatility=spec.return_volatility,
                trial_count_searched=spec.trial_count_searched,
                noise_trials_for_dispersion=spec.noise_trials_for_dispersion,
                bootstrap_iterations=spec.bootstrap_iterations,
                confidence_threshold=spec.confidence_threshold,
                base_seed=cell_seed,
            )
            results.append(evaluate_positive_control_cell(cell_config))
            cell_index += 1
    return results


def minimum_sample_size_for_power(
    results: Iterable[PositiveControlCellResult],
    *,
    target_power: float = 0.8,
) -> dict[float, int | None]:
    """For each effect size, return the smallest tested ``sample_size`` whose
    empirical pass rate is at least ``target_power``. ``None`` means no cell
    crossed the threshold within the swept range.
    """

    if not 0.0 < target_power <= 1.0:
        raise ValueError("target_power must be in (0, 1]")
    by_effect: dict[float, list[PositiveControlCellResult]] = {}
    for result in results:
        by_effect.setdefault(result.effect_size_mean, []).append(result)
    out: dict[float, int | None] = {}
    for effect, cells in by_effect.items():
        passing = [cell for cell in sorted(cells, key=lambda c: c.sample_size) if cell.pass_rate >= target_power]
        out[effect] = passing[0].sample_size if passing else None
    return out
