from __future__ import annotations

import numpy as np
import pandas as pd

from src.experiments.kronos_defense_trial import KronosDefenseConfig, run_kronos_defense_duel


def _setup(prescient: bool) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    periods = pd.bdate_range("2025-01-02", periods=200)
    rng = np.random.default_rng(7)
    returns = pd.Series(rng.normal(0.001, 0.01, 200), index=periods)
    returns.iloc[80:110] = -0.02  # crash window
    asof = periods[::5]
    rows = []
    for d in asof:
        in_crash = periods[80] <= d <= periods[110]
        prob_up = (0.2 if in_crash else 0.8) if prescient else 0.8
        rows.append({"as_of_date": d.strftime("%Y-%m-%d"), "kronos_probability_up": prob_up, "kronos_forecast_drawdown_proxy": -0.02})
    features = pd.DataFrame(rows)
    regimes = pd.DataFrame({"date": periods, "regime": ["TREND_UP"] * 200})
    return returns, features, regimes


def test_prescient_kronos_passes_drawdown_gates() -> None:
    returns, features, regimes = _setup(prescient=True)
    result = run_kronos_defense_duel(returns, features, regimes, KronosDefenseConfig(random_shifts=200))
    assert result["promotion_allowed"] is False
    assert result["gates"]["G2_reduces_drawdown"] is True
    assert result["kronos"]["max_drawdown"] > result["unthrottled"]["max_drawdown"]
    assert result["coverage"] >= 0.8


def test_blind_kronos_fails_duel() -> None:
    returns, features, regimes = _setup(prescient=False)
    result = run_kronos_defense_duel(returns, features, regimes, KronosDefenseConfig(random_shifts=200))
    # esposizione costante: nessuna riduzione di drawdown attribuibile al timing
    assert result["gates"]["G3_beats_random_timing"] is False or result["gates"]["G2_reduces_drawdown"] is False


def test_metrics_are_finite() -> None:
    returns, features, regimes = _setup(prescient=True)
    result = run_kronos_defense_duel(returns, features, regimes, KronosDefenseConfig(random_shifts=100))
    for block in ("unthrottled", "kronos", "classifier"):
        for value in result[block].values():
            assert np.isfinite(float(value))
