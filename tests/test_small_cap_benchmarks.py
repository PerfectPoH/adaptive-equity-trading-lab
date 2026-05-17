from __future__ import annotations

import math

import pandas as pd

from src.analysis.small_cap_benchmarks import (
    SmallCapBenchmarkConfig,
    SmallCapBootstrapRandomBaselineConfig,
    build_bootstrap_random_baseline_report,
    build_small_cap_benchmark_report,
)


def _frames() -> dict[str, pd.DataFrame]:
    index = pd.bdate_range("2024-01-01", periods=4)
    return {
        "AAA": pd.DataFrame({"Close": [10.0, 11.0, 12.0, 13.0]}, index=index),
        "BBB": pd.DataFrame({"Close": [20.0, 19.0, 18.0, 17.0]}, index=index),
    }


def _candidate_export() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "as_of": "2024-01-01", "operational_candidate": True},
            {"symbol": "BBB", "as_of": "2024-01-01", "operational_candidate": False},
        ]
    )


def _iwm() -> pd.DataFrame:
    return pd.DataFrame({"Close": [100.0, 102.0, 104.0, 108.0]}, index=pd.bdate_range("2024-01-01", periods=4))


def test_small_cap_benchmark_report_includes_required_benchmarks() -> None:
    report = build_small_cap_benchmark_report(
        _candidate_export(),
        _frames(),
        iwm_frame=_iwm(),
        config=SmallCapBenchmarkConfig(holding_period_bars=2, random_seed=7),
    )

    assert report["benchmark"].tolist() == [
        "cash_flat",
        "iwm_proxy",
        "equal_weight_universe",
        "random_entry_baseline",
        "ticker_holding_window",
    ]


def test_small_cap_benchmark_report_calculates_core_returns() -> None:
    report = build_small_cap_benchmark_report(
        _candidate_export(),
        _frames(),
        iwm_frame=_iwm(),
        config=SmallCapBenchmarkConfig(holding_period_bars=2, random_seed=7),
    ).set_index("benchmark")

    assert report.loc["cash_flat", "return"] == 0.0
    assert math.isclose(report.loc["iwm_proxy", "return"], 0.04)
    assert math.isclose(report.loc["equal_weight_universe", "return"], ((12 / 10 - 1) + (18 / 20 - 1)) / 2)
    assert math.isclose(report.loc["ticker_holding_window", "return"], 12 / 10 - 1)


def test_small_cap_benchmark_report_random_baseline_is_seeded_and_uses_all_candidate_dates() -> None:
    report_a = build_small_cap_benchmark_report(
        _candidate_export(),
        _frames(),
        iwm_frame=_iwm(),
        config=SmallCapBenchmarkConfig(holding_period_bars=2, random_seed=11),
    )
    report_b = build_small_cap_benchmark_report(
        _candidate_export(),
        _frames(),
        iwm_frame=_iwm(),
        config=SmallCapBenchmarkConfig(holding_period_bars=2, random_seed=11),
    )

    random_a = report_a[report_a["benchmark"] == "random_entry_baseline"].iloc[0]
    random_b = report_b[report_b["benchmark"] == "random_entry_baseline"].iloc[0]
    assert random_a["return"] == random_b["return"]
    assert random_a["observations"] == 2


def test_small_cap_benchmark_report_handles_missing_iwm() -> None:
    report = build_small_cap_benchmark_report(
        _candidate_export(),
        _frames(),
        iwm_frame=None,
        config=SmallCapBenchmarkConfig(holding_period_bars=2),
    ).set_index("benchmark")

    assert math.isnan(report.loc["iwm_proxy", "return"])
    assert report.loc["iwm_proxy", "observations"] == 0


def test_bootstrap_random_baseline_report_is_distribution_aware_and_reproducible() -> None:
    config = SmallCapBootstrapRandomBaselineConfig(simulations=1000, base_seed=700, holding_period_bars=2)

    first = build_bootstrap_random_baseline_report(_candidate_export(), _frames(), config=config)
    second = build_bootstrap_random_baseline_report(_candidate_export(), _frames(), config=config)

    assert first == second
    assert first["simulations"] == 1000
    assert first["base_seed"] == 700
    assert first["seed_start"] == 700
    assert first["seed_end"] == 1699
    assert first["observations_per_simulation_min"] == 2
    assert first["observations_per_simulation_max"] == 2
    assert first["p05_return"] <= first["median_return"] <= first["p95_return"]
    assert math.isfinite(first["mean_return"])


def test_bootstrap_random_baseline_config_changes_are_explicit() -> None:
    default = SmallCapBootstrapRandomBaselineConfig()

    assert default.simulations == 1000
    assert default.base_seed == 700
    assert default.holding_period_bars == 5
