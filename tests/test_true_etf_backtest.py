from __future__ import annotations

import numpy as np
import pandas as pd

from src.experiments.true_etf_backtest import TrueEtfConfig, causal_signals, run_true_etf_backtest


def _panel(seed: int, periods: int = 700, drift: float = 0.0004) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-03", periods=periods)
    close = 100 * np.cumprod(1 + rng.normal(drift, 0.012, periods))
    open_ = close * (1 + rng.normal(0, 0.002, periods))
    return pd.DataFrame(
        {"Open": open_, "High": np.maximum(open_, close) * 1.005, "Low": np.minimum(open_, close) * 0.995,
         "Close": close, "Volume": rng.integers(1_000_000, 5_000_000, periods).astype(float)},
        index=dates,
    )


def test_causal_signals_have_no_lookahead() -> None:
    panel = _panel(1)
    cfg = TrueEtfConfig()
    base = causal_signals(panel, cfg)
    mutated = panel.copy()
    mutated.iloc[-50:, mutated.columns.get_loc("Close")] *= 3.0
    cut = panel.index[-51]
    pd.testing.assert_frame_equal(base.loc[:cut], causal_signals(mutated, cfg).loc[:cut])


def test_backtest_respects_cash_and_position_limits() -> None:
    panels = {f"S{i}": _panel(i) for i in range(6)}
    cfg = TrueEtfConfig(oos_start="2023-01-01", min_oos_trades=1)
    result = run_true_etf_backtest(panels, panels["S0"], cfg)
    equity = result["equity"]
    assert (equity["open_positions"] <= cfg.max_positions).all()
    assert (equity["cash"] >= -1e-6).all()  # mai cash negativo: no leva
    assert np.isfinite(equity["equity"]).all()


def test_double_costs_reduce_returns() -> None:
    panels = {f"S{i}": _panel(i + 10) for i in range(4)}
    cfg = TrueEtfConfig(min_oos_trades=1)
    base = run_true_etf_backtest(panels, panels["S10" if "S10" in panels else "S0"], cfg)
    double = run_true_etf_backtest(panels, panels["S0"], cfg, cost_multiplier=2.0)
    assert double["equity"]["equity"].iloc[-1] <= base["equity"]["equity"].iloc[-1] + 1e-6
