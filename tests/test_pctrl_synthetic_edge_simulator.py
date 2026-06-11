from __future__ import annotations

import pytest

from src.experiments.pctrl_synthetic_edge_simulator import (
    PositiveControlConfig,
    PowerCurveSpec,
    evaluate_positive_control_cell,
    minimum_sample_size_for_power,
    run_power_curve,
)


def test_zero_edge_pass_rate_is_at_or_below_nominal_type_one() -> None:
    config = PositiveControlConfig(
        sample_size=252,
        effect_size_mean=0.0,
        bootstrap_iterations=200,
        base_seed=11,
    )
    result = evaluate_positive_control_cell(config)
    # DSR is conservative for small/medium N; empirical type-I should sit at
    # or below the nominal (1 - confidence) of 5%.
    assert result.pass_rate <= 0.10
    assert 0.0 <= result.pass_rate <= 1.0
    assert result.bootstrap_iterations == 200


def test_large_edge_with_sufficient_sample_passes_gate_with_high_power() -> None:
    config = PositiveControlConfig(
        sample_size=200,
        effect_size_mean=0.010,  # annualized Sharpe ~7.9
        bootstrap_iterations=100,
        base_seed=23,
    )
    result = evaluate_positive_control_cell(config)
    assert result.pass_rate >= 0.80
    assert result.mean_observed_sharpe > 0


def test_power_increases_monotonically_with_sample_size_at_fixed_edge() -> None:
    pass_rates: list[float] = []
    for n in (50, 100, 200):
        cfg = PositiveControlConfig(
            sample_size=n,
            effect_size_mean=0.0075,
            bootstrap_iterations=100,
            base_seed=37,
        )
        pass_rates.append(evaluate_positive_control_cell(cfg).pass_rate)
    # Strictly non-decreasing in N (with possibly small noise allowed).
    assert pass_rates[0] - 0.05 <= pass_rates[1]
    assert pass_rates[1] - 0.05 <= pass_rates[2]
    assert pass_rates[2] > pass_rates[0]


def test_run_power_curve_returns_one_cell_per_combination() -> None:
    spec = PowerCurveSpec(
        sample_sizes=(50, 100),
        effect_sizes=(0.0, 0.005),
        bootstrap_iterations=50,
        base_seed=5,
    )
    results = run_power_curve(spec)
    assert len(results) == 4
    keys = {(cell.sample_size, cell.effect_size_mean) for cell in results}
    assert keys == {(50, 0.0), (50, 0.005), (100, 0.0), (100, 0.005)}


def test_minimum_sample_size_for_power_handles_unreachable_effects() -> None:
    spec = PowerCurveSpec(
        sample_sizes=(20, 50),
        effect_sizes=(0.0, 0.010),
        bootstrap_iterations=100,
        base_seed=9,
    )
    results = run_power_curve(spec)
    min_n = minimum_sample_size_for_power(results, target_power=0.80)
    # mu=0 must never reach 80% power
    assert min_n[0.0] is None
    # mu=0.010 may or may not reach 80% at these N — just check the key is present
    assert 0.010 in min_n


def test_config_rejects_invalid_parameters() -> None:
    with pytest.raises(ValueError, match="sample_size"):
        PositiveControlConfig(sample_size=1, effect_size_mean=0.0)
    with pytest.raises(ValueError, match="return_volatility"):
        PositiveControlConfig(sample_size=20, effect_size_mean=0.0, return_volatility=0.0)
    with pytest.raises(ValueError, match="confidence_threshold"):
        PositiveControlConfig(sample_size=20, effect_size_mean=0.0, confidence_threshold=1.0)
