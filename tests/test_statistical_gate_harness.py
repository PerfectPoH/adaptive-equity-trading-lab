from __future__ import annotations

import pytest

from src.validation.statistical_gate_harness import (
    SyntheticGateHarnessConfig,
    generate_correlated_noise_trials,
    run_synthetic_statistical_gate_harness,
)


def test_synthetic_gate_harness_rejects_best_trial_from_noise() -> None:
    result = run_synthetic_statistical_gate_harness(
        SyntheticGateHarnessConfig(
            observations=252,
            trial_count=100,
            common_factor_weight=0.35,
            random_seed=42,
            cpcv_groups=6,
            cpcv_test_groups=2,
            label_horizon_days=5,
            embargo_days=2,
        )
    )

    assert result.best_trial_sharpe > 0
    assert result.effective_trial_count > 1
    assert result.dsr < 0.95
    assert result.passed is False


def test_synthetic_gate_harness_uses_cpcv_and_removes_boundary_rows() -> None:
    result = run_synthetic_statistical_gate_harness(SyntheticGateHarnessConfig(observations=120, trial_count=40, random_seed=7))

    assert result.cpcv_split_count == 15
    assert result.cpcv_min_train_size > 0
    assert result.cpcv_min_test_size > 0
    assert result.cpcv_total_purged > 0
    assert result.cpcv_total_embargoed > 0


def test_synthetic_gate_harness_effective_count_reflects_common_factor_strength() -> None:
    weak_common = run_synthetic_statistical_gate_harness(
        SyntheticGateHarnessConfig(observations=252, trial_count=60, common_factor_weight=0.05, random_seed=11)
    )
    strong_common = run_synthetic_statistical_gate_harness(
        SyntheticGateHarnessConfig(observations=252, trial_count=60, common_factor_weight=0.9, random_seed=11)
    )

    assert weak_common.effective_trial_count > strong_common.effective_trial_count


def test_generate_correlated_noise_trials_rejects_bad_config() -> None:
    with pytest.raises(ValueError, match="observations"):
        generate_correlated_noise_trials(SyntheticGateHarnessConfig(observations=10))

    with pytest.raises(ValueError, match="trial_count"):
        generate_correlated_noise_trials(SyntheticGateHarnessConfig(trial_count=1))

    with pytest.raises(ValueError, match="common_factor_weight"):
        generate_correlated_noise_trials(SyntheticGateHarnessConfig(common_factor_weight=1.0))
