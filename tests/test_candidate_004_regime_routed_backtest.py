from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_004_regime_routed_backtest import (
    generate_regime_routed_trades,
    run_candidate_004_regime_routed_backtest,
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


def test_regime_router_generates_trades_only_for_allowed_sleeves() -> None:
    frames = {"AAA": _frame(10.0, 0.05), "BBB": _frame(20.0, -0.01)}
    dates = sorted({date for frame in frames.values() for date in frame.index})
    regime_map = pd.DataFrame(
        [
            {"date": dates[60].date().isoformat(), "regime_label": "RECOVERY_BOUNCE"},
            {"date": dates[80].date().isoformat(), "regime_label": "DRAWDOWN_STRESS"},
        ]
    )
    routes = {
        "RECOVERY_BOUNCE": {"Momentum": 0.25, "Mean Reversion": 0.10},
        "DRAWDOWN_STRESS": {"Momentum": 0.0, "Mean Reversion": 0.0, "Cash/No-Trade": 1.0},
    }

    trades = generate_regime_routed_trades(["AAA", "BBB"], frames, regime_map, routes, cost_bps=100)

    assert {trade["regime_label"] for trade in trades} == {"RECOVERY_BOUNCE"}
    assert {trade["sleeve"] for trade in trades} == {"Momentum", "Mean Reversion"}
    assert {trade["route_weight"] for trade in trades} == {0.25, 0.10}


def test_candidate_004_backtest_respects_gate_and_blocks_promotion(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    gate_dir.mkdir()
    gate = {
        "status": "APPROVED_ONE_TRIAL_LIMITED_REGIME_ROUTED_BACKTEST",
        "allowed_backtest_count": 1,
        "parameter_sweep_allowed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "cost_bps": 100,
        "router_contract": {
            "routes": {
                "TREND_UP_LOW_VOL": {"Momentum": 0.25, "Mean Reversion": 0.0, "Cash/No-Trade": 0.75},
                "INSUFFICIENT_HISTORY": {"Momentum": 0.0, "Mean Reversion": 0.0, "Cash/No-Trade": 1.0},
            }
        },
    }
    (gate_dir / "gate_manifest.json").write_text(json.dumps(gate), encoding="utf-8")
    frames = {
        "AAA": _frame(10.0, 0.05),
        "BBB": _frame(20.0, -0.02),
        "SPY": _frame(100.0, 0.20),
        "IWM": _frame(80.0, 0.15),
    }

    result = run_candidate_004_regime_routed_backtest(output_dir=tmp_path / "out", gate_dir=gate_dir, frames=frames)

    assert result["portfolio_backtest_performed"] is True
    assert result["parameter_sweep_performed"] is False
    assert result["promotion_allowed"] is False
    assert result["final_decision"]["promotion_allowed"] is False
    assert (tmp_path / "out" / "trade_log.csv").is_file()
