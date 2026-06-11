"""Regression tests for the NaN-aware return matrix and compound aggregator.

These tests prove that ``build_component_return_matrix`` no longer treats
missing periods as 0% returns and that the static baseline / compound
cumulative path produces portfolio-accounting-correct numbers.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from src.experiments.workbench_portfolio_engine import (
    _active_period_mean,
    _compound_cumulative_returns,
    _has_real_date_index,
    build_component_return_matrix,
)


def _component(component_id: str, returns_by_date: dict[str, float]) -> dict:
    return {
        "component_id": component_id,
        "strategy_name": f"strat-{component_id}",
        "template": "XMOM",
        "analysis_mode": "live",
        "decision": "GO",
        "trade_count": len(returns_by_date),
        "net_return_sum": sum(returns_by_date.values()),
        "source": f"{component_id}.json",
        "bias_warnings": [],
        "inline_returns": [
            {"period": period, "net_return": value}
            for period, value in returns_by_date.items()
        ],
    }


def test_return_matrix_leaves_missing_periods_as_nan() -> None:
    a = _component("A", {"2024-01-02": 0.01, "2024-01-03": 0.02})
    b = _component("B", {"2024-01-03": 0.03, "2024-01-04": -0.01})
    matrix = build_component_return_matrix([a, b])
    assert math.isnan(matrix.loc["2024-01-02", "B"])
    assert math.isnan(matrix.loc["2024-01-04", "A"])
    assert matrix.loc["2024-01-03", "A"] == pytest.approx(0.02)


def test_return_matrix_excludes_components_without_real_dates() -> None:
    real = _component("A", {"2024-01-02": 0.01})
    placeholder = _component("STEP", {"step-00001": 0.05, "step-00002": 0.01})
    matrix = build_component_return_matrix([real, placeholder])
    assert "A" in matrix.columns
    assert "STEP" not in matrix.columns


def test_return_matrix_admits_step_components_when_flag_disabled() -> None:
    real = _component("A", {"2024-01-02": 0.01})
    placeholder = _component("STEP", {"step-00001": 0.05})
    matrix = build_component_return_matrix([real, placeholder], require_real_dates=False)
    assert {"A", "STEP"} == set(matrix.columns)


def test_active_period_mean_skips_nan_in_denominator() -> None:
    a = _component("A", {"2024-01-02": 0.10, "2024-01-03": 0.00})
    b = _component("B", {"2024-01-03": 0.00})
    matrix = build_component_return_matrix([a, b])
    baseline = _active_period_mean(matrix)
    # Day 1: only A alive -> 0.10 (not 0.05 from diluting against B).
    assert baseline.loc["2024-01-02"] == pytest.approx(0.10)
    # Day 2: both alive, returns 0.0.
    assert baseline.loc["2024-01-03"] == pytest.approx(0.0)


def test_compound_cumulative_returns_match_portfolio_accounting() -> None:
    returns = pd.Series([0.10, 0.10], index=["2024-01-02", "2024-01-03"])
    compounded = _compound_cumulative_returns(returns)
    # (1.10)*(1.10) - 1 = 0.21, NOT 0.20 (which is what cumsum would give).
    assert compounded.iloc[-1] == pytest.approx(0.21)
    assert compounded.iloc[0] == pytest.approx(0.10)


def test_compound_cumulative_returns_treats_nan_as_cash() -> None:
    returns = pd.Series([0.05, float("nan"), 0.05], index=["d1", "d2", "d3"])
    compounded = _compound_cumulative_returns(returns)
    # NaN period contributes a factor of 1 (cash).
    assert compounded.iloc[-1] == pytest.approx((1.05 * 1.0 * 1.05) - 1)


def test_has_real_date_index_rejects_step_only_series() -> None:
    real = pd.Series([0.1], index=["2024-01-02"])
    fake = pd.Series([0.1, 0.2], index=["step-00001", "step-00002"])
    assert _has_real_date_index(real) is True
    assert _has_real_date_index(fake) is False


def test_static_baseline_is_not_diluted_by_unborn_components() -> None:
    # Component "old" lives day 1 only; "new" lives day 2 only.
    old = _component("old", {"2024-01-02": 0.10})
    new = _component("new", {"2024-01-03": 0.20})
    matrix = build_component_return_matrix([old, new])
    baseline = _active_period_mean(matrix).fillna(0.0)
    # Each day uses the alive component, so daily returns are 10% then 20%.
    assert baseline.loc["2024-01-02"] == pytest.approx(0.10)
    assert baseline.loc["2024-01-03"] == pytest.approx(0.20)
    cumulative = _compound_cumulative_returns(baseline)
    assert cumulative.iloc[-1] == pytest.approx(1.10 * 1.20 - 1.0)
