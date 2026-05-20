from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.validation.combinatorial_purged_cv import CPCVConfig, assert_no_label_overlap, combinatorial_purged_cv_splits
from src.validation.deflated_sharpe import DeflatedSharpeResult, deflated_sharpe_ratio, return_moments, sample_sharpe_ratio
from src.validation.effective_trial_count import EffectiveTrialCountResult, effective_trial_count_from_returns


@dataclass(frozen=True)
class SyntheticGateHarnessConfig:
    observations: int = 252
    trial_count: int = 100
    common_factor_weight: float = 0.35
    random_seed: int = 42
    cpcv_groups: int = 6
    cpcv_test_groups: int = 2
    label_horizon_days: int = 5
    embargo_days: int = 2
    confidence_threshold: float = 0.95


@dataclass(frozen=True)
class SyntheticGateHarnessResult:
    nominal_trial_count: int
    effective_trial_count: float
    best_trial_index: int
    best_trial_sharpe: float
    sharpe_std_across_trials: float
    dsr: float
    passed: bool
    cpcv_split_count: int
    cpcv_min_train_size: int
    cpcv_min_test_size: int
    cpcv_total_purged: int
    cpcv_total_embargoed: int
    trial_count_result: EffectiveTrialCountResult
    dsr_result: DeflatedSharpeResult


def run_synthetic_statistical_gate_harness(config: SyntheticGateHarnessConfig | None = None) -> SyntheticGateHarnessResult:
    active = config or SyntheticGateHarnessConfig()
    returns = generate_correlated_noise_trials(active)
    split_frame = build_synthetic_label_interval_frame(active.observations, active.label_horizon_days)
    cpcv_config = CPCVConfig(
        n_groups=active.cpcv_groups,
        n_test_groups=active.cpcv_test_groups,
        embargo_days=active.embargo_days,
    )
    splits = combinatorial_purged_cv_splits(split_frame, cpcv_config)
    for split in splits:
        assert_no_label_overlap(split_frame, split, cpcv_config)

    sharpe_values = np.asarray([sample_sharpe_ratio(returns[:, trial]) for trial in range(returns.shape[1])], dtype=float)
    best_trial_index = int(np.argmax(sharpe_values))
    trial_count_result = effective_trial_count_from_returns(returns)
    sharpe_std = float(np.std(sharpe_values, ddof=1))
    best_moments = return_moments(returns[:, best_trial_index])
    dsr_result = deflated_sharpe_ratio(
        observed_sharpe=float(sharpe_values[best_trial_index]),
        sample_size=best_moments.sample_size,
        skewness=best_moments.skewness,
        kurtosis=best_moments.kurtosis,
        trial_count=trial_count_result.effective_count,
        sharpe_std=sharpe_std,
        confidence_threshold=active.confidence_threshold,
    )

    return SyntheticGateHarnessResult(
        nominal_trial_count=active.trial_count,
        effective_trial_count=trial_count_result.effective_count,
        best_trial_index=best_trial_index,
        best_trial_sharpe=float(sharpe_values[best_trial_index]),
        sharpe_std_across_trials=sharpe_std,
        dsr=dsr_result.dsr,
        passed=dsr_result.passed,
        cpcv_split_count=len(splits),
        cpcv_min_train_size=min(len(split.train_indices) for split in splits),
        cpcv_min_test_size=min(len(split.test_indices) for split in splits),
        cpcv_total_purged=sum(len(split.purged_indices) for split in splits),
        cpcv_total_embargoed=sum(len(split.embargoed_indices) for split in splits),
        trial_count_result=trial_count_result,
        dsr_result=dsr_result,
    )


def generate_correlated_noise_trials(config: SyntheticGateHarnessConfig) -> np.ndarray:
    if config.observations < 20:
        raise ValueError("observations must be at least 20.")
    if config.trial_count < 2:
        raise ValueError("trial_count must be at least 2.")
    if not 0 <= config.common_factor_weight < 1:
        raise ValueError("common_factor_weight must be in [0, 1).")

    rng = np.random.default_rng(config.random_seed)
    common = rng.normal(0.0, 1.0, size=(config.observations, 1))
    idiosyncratic = rng.normal(0.0, 1.0, size=(config.observations, config.trial_count))
    common_scale = config.common_factor_weight
    idiosyncratic_scale = float(np.sqrt(1 - common_scale**2))
    return common_scale * common + idiosyncratic_scale * idiosyncratic


def build_synthetic_label_interval_frame(observations: int, label_horizon_days: int) -> pd.DataFrame:
    if observations < 2:
        raise ValueError("observations must be at least 2.")
    if label_horizon_days < 0:
        raise ValueError("label_horizon_days must be non-negative.")

    index = pd.date_range("2024-01-01", periods=observations, freq="D")
    return pd.DataFrame(
        {
            "symbol": "SYNTH",
            "feature": np.arange(observations, dtype=float),
            "label_start": index,
            "label_end": index + pd.Timedelta(days=label_horizon_days),
        },
        index=index,
    )
