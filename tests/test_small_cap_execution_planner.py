from __future__ import annotations

import pandas as pd

from src.backtest.small_cap_execution import SmallCapExecutionConfig
from src.backtest.small_cap_execution_planner import SmallCapExecutionPlanner


def _candidate(**overrides: object) -> pd.Series:
    data: dict[str, object] = {
        "symbol": "GOOD",
        "as_of": "2024-01-02",
        "Close": 10.0,
        "atr": 0.5,
        "avg_dollar_volume_20d": 2_000_000.0,
    }
    data.update(overrides)
    return pd.Series(data)


def test_execution_planner_rejects_next_open_gap_above_limit() -> None:
    planner = SmallCapExecutionPlanner(SmallCapExecutionConfig(max_next_open_gap=0.08))

    decision = planner.plan_trade(_candidate(), next_open=11.0, available_cash=100_000.0)

    assert decision.accepted is False
    assert decision.reject_reason == "gap_above_max"
    assert decision.symbol == "GOOD"


def test_execution_planner_caps_notional_by_dollar_volume_capacity() -> None:
    config = SmallCapExecutionConfig(
        max_position_dollar_volume_fraction=0.01,
        min_trade_notional=100.0,
        spread_bps=0.0,
        slippage_bps=0.0,
    )
    planner = SmallCapExecutionPlanner(config)

    decision = planner.plan_trade(_candidate(avg_dollar_volume_20d=200_000.0), next_open=10.0, available_cash=100_000.0)

    assert decision.accepted is True
    assert decision.position_notional <= 2_000.0
    assert decision.max_liquidity_notional == 2_000.0
    assert decision.position_size == 200


def test_execution_planner_caps_notional_by_available_cash() -> None:
    config = SmallCapExecutionConfig(min_trade_notional=100.0, spread_bps=0.0, slippage_bps=0.0, risk_fraction=1.0)
    planner = SmallCapExecutionPlanner(config)

    decision = planner.plan_trade(_candidate(), next_open=10.0, available_cash=1_500.0)

    assert decision.accepted is True
    assert decision.position_notional <= 1_500.0
    assert decision.position_size == 150


def test_execution_planner_uses_risk_fraction_position_sizing_before_cash_or_liquidity_caps() -> None:
    config = SmallCapExecutionConfig(
        min_trade_notional=100.0,
        spread_bps=0.0,
        slippage_bps=0.0,
        risk_fraction=0.01,
        stop_atr_multiple=1.5,
        max_position_dollar_volume_fraction=0.01,
    )
    planner = SmallCapExecutionPlanner(config)

    decision = planner.plan_trade(_candidate(avg_dollar_volume_20d=2_000_000.0), next_open=10.0, available_cash=100_000.0)

    assert decision.accepted is True
    assert decision.stop_loss == 9.25
    assert decision.position_size == 1333
    assert decision.position_notional == 13_330.0
    assert decision.position_notional < decision.max_liquidity_notional
    assert decision.position_notional < decision.available_cash


def test_execution_planner_applies_entry_cost_haircut() -> None:
    config = SmallCapExecutionConfig(spread_bps=40.0, slippage_bps=60.0, min_trade_notional=100.0)
    planner = SmallCapExecutionPlanner(config)

    decision = planner.plan_trade(_candidate(), next_open=10.0, available_cash=100_000.0)

    assert decision.accepted is True
    assert decision.entry_reference_price == 10.0
    assert decision.entry_price == 10.1
    assert decision.estimated_cost_pct == 0.01


def test_execution_planner_rejects_when_cash_is_below_min_notional() -> None:
    planner = SmallCapExecutionPlanner(SmallCapExecutionConfig(min_trade_notional=1_000.0))

    decision = planner.plan_trade(_candidate(), next_open=10.0, available_cash=500.0)

    assert decision.accepted is False
    assert decision.reject_reason == "insufficient_funds"


def test_execution_planner_adds_square_root_impact_when_volatility_available() -> None:
    config = SmallCapExecutionConfig(
        spread_bps=0.0,
        slippage_bps=0.0,
        impact_coefficient_bps=50.0,
        min_trade_notional=100.0,
    )
    planner = SmallCapExecutionPlanner(config)

    decision = planner.plan_trade(
        _candidate(avg_dollar_volume_20d=200_000.0, rolling_volatility_20d=0.04),
        next_open=10.0,
        available_cash=100_000.0,
    )

    assert decision.accepted is True
    assert decision.impact_cost_pct > 0.0
    assert decision.estimated_cost_pct > 0.0
