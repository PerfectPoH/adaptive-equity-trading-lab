from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_005_recovery_breadth_backtest import (
    generate_recovery_breadth_trades,
    run_candidate_005_recovery_breadth_backtest,
)


def _frame(start: float, step: float, periods: int = 130) -> pd.DataFrame:
    index = pd.bdate_range("2025-01-01", periods=periods)
    close = pd.Series([start + step * i for i in range(periods)], index=index)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": 1_000_000,
            "Turnover": close * 1_000_000,
        },
        index=index,
    )


def _gate(path: Path) -> None:
    path.mkdir()
    payload = {
        "status": "APPROVED_ONE_TRIAL_LIMITED_RECOVERY_BREADTH_BACKTEST",
        "allowed_backtest_count": 1,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "anti_overfit_constraints": {
            "parameter_sweep_allowed": False,
            "top_k_change_allowed": False,
        },
        "strategy_contract": {
            "lookback_days": 20,
            "holding_days": 20,
            "top_k": 5,
            "min_candidates_per_rebalance": 5,
            "per_trade_weight": 0.05,
            "cost_bps": 100,
            "tradability_min_price": 1.0,
            "tradability_min_median_turnover": 1_000_000.0,
        },
    }
    (path / "gate_manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def test_recovery_breadth_generates_top_k_only_in_recovery() -> None:
    frames = {f"S{i}": _frame(10.0 + i, 0.02 * i) for i in range(1, 8)}
    dates = sorted({date for frame in frames.values() for date in frame.index})
    regime_map = pd.DataFrame(
        [
            {"date": dates[60].date().isoformat(), "regime_label": "RECOVERY_BOUNCE"},
            {"date": dates[80].date().isoformat(), "regime_label": "DRAWDOWN_STRESS"},
        ]
    )

    trades = generate_recovery_breadth_trades(
        sorted(frames),
        frames,
        regime_map,
        lookback_days=20,
        holding_days=20,
        top_k=5,
        min_candidates=5,
        per_trade_weight=0.05,
        cost_bps=100,
    )

    assert len(trades) == 5
    assert {trade["regime_label"] for trade in trades} == {"RECOVERY_BOUNCE"}
    assert {trade["per_trade_weight"] for trade in trades} == {0.05}


def test_candidate_005_run_is_trial_limited_and_non_promotable(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    _gate(gate_dir)
    frames = {f"S{i}": _frame(10.0 + i, 0.02 * i) for i in range(1, 8)}
    frames["SPY"] = _frame(100.0, 0.20)
    frames["IWM"] = _frame(80.0, 0.15)

    result = run_candidate_005_recovery_breadth_backtest(output_dir=tmp_path / "out", gate_dir=gate_dir, frames=frames)

    assert result["portfolio_backtest_performed"] is True
    assert result["parameter_sweep_performed"] is False
    assert result["promotion_allowed"] is False
    assert result["final_decision"]["promotion_allowed"] is False
    assert (tmp_path / "out" / "trade_log.csv").is_file()
