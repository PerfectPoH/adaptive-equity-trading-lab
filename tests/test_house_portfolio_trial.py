from __future__ import annotations

import numpy as np
import pandas as pd

from src.experiments.house_portfolio_trial import HouseConfig, run_house_portfolio_trial


def _curves(crash: bool) -> pd.DataFrame:
    periods = pd.bdate_range("2025-01-02", periods=250)
    rng = np.random.default_rng(11)
    returns = pd.Series(rng.normal(0.0015, 0.008, 250), index=periods)
    if crash:
        returns.iloc[100:130] = -0.018
    dynamic = (1 + returns).cumprod() - 1
    static = (1 + returns * 0.3).cumprod() - 1
    return pd.DataFrame({"period": periods.strftime("%Y-%m-%d"), "dynamic": dynamic.to_numpy(), "static": static.to_numpy()})


def _regimes(defensive_window: bool) -> pd.DataFrame:
    periods = pd.bdate_range("2025-01-02", periods=250)
    labels = ["TREND_UP"] * 250
    if defensive_window:
        for i in range(98, 132):
            labels[i] = "HIGH_VOL"
    return pd.DataFrame({"date": periods, "regime": labels})


def test_defense_improves_risk_adjusted_metrics_in_crash() -> None:
    result = run_house_portfolio_trial(_curves(crash=True), _regimes(defensive_window=True), HouseConfig())
    assert result["promotion_allowed"] is False
    assert result["gates"]["H2_better_risk_adjusted_than_undefended"] is True
    assert result["house"]["max_drawdown"] > result["undefended_dynamic"]["max_drawdown"]


def test_costs_are_charged_on_exposure_changes() -> None:
    result = run_house_portfolio_trial(_curves(crash=True), _regimes(defensive_window=True), HouseConfig(cost_bps_per_turnover=100.0))
    assert result["house"]["total_cost_paid"] > 0


def test_no_defense_window_keeps_house_close_to_undefended() -> None:
    result = run_house_portfolio_trial(_curves(crash=False), _regimes(defensive_window=False), HouseConfig())
    assert abs(result["house"]["total_return"] - result["undefended_dynamic"]["total_return"]) < 0.02
