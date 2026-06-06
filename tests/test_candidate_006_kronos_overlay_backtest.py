from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments import candidate_006_kronos_overlay_backtest as overlay


def _gate(path: Path) -> None:
    path.mkdir()
    payload = {
        "status": "APPROVED_ONE_KRONOS_OVERLAY_BACKTEST_SIGN_FILTER_ONLY",
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "overlay_rule": {
            "feature": "kronos_forecast_return_median",
            "threshold": 0.0,
            "operator": ">",
            "weight_redistribution_allowed": False,
        },
    }
    (path / "gate_manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def test_apply_sign_filter_routes_negative_forecasts_to_cash() -> None:
    trades = pd.DataFrame(
        [
            {"symbol": "AAA", "signal_date": "2026-01-02", "exit_date": "2026-01-10", "weighted_net_return": 0.10},
            {"symbol": "BBB", "signal_date": "2026-01-02", "exit_date": "2026-01-10", "weighted_net_return": -0.20},
        ]
    )
    features = pd.DataFrame(
        [
            {"symbol": "AAA", "as_of_date": "2026-01-02", "kronos_forecast_return_median": 0.01},
            {"symbol": "BBB", "as_of_date": "2026-01-02", "kronos_forecast_return_median": -0.01},
        ]
    )

    joined = overlay.apply_kronos_sign_filter(trades, features)

    assert joined["kronos_keep_trade"].tolist() == [True, False]
    assert joined["overlay_weighted_net_return"].tolist() == [0.10, 0.0]


def test_overlay_backtest_is_diagnostic_only(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    _gate(gate_dir)
    trade_path = tmp_path / "trade_log.csv"
    pd.DataFrame(
        [
            {"symbol": "AAA", "signal_date": "2026-01-02", "exit_date": "2026-01-10", "weighted_net_return": 0.10, "net_return": 0.20},
            {"symbol": "BBB", "signal_date": "2026-01-02", "exit_date": "2026-01-10", "weighted_net_return": -0.20, "net_return": -0.40},
        ]
    ).to_csv(trade_path, index=False)
    feature_path = tmp_path / "features.csv"
    pd.DataFrame(
        [
            {"symbol": "AAA", "as_of_date": "2026-01-02", "kronos_forecast_return_median": 0.01},
            {"symbol": "BBB", "as_of_date": "2026-01-02", "kronos_forecast_return_median": -0.01},
        ]
    ).to_csv(feature_path, index=False)

    result = overlay.run_candidate_006_kronos_overlay_backtest(
        gate_dir=gate_dir,
        output_dir=tmp_path / "out",
        trade_log_path=trade_path,
        feature_rows_path=feature_path,
    )

    assert result["summary"]["overlay_trade_count"] == 1
    assert result["summary"]["overlay_weighted_net_return_sum"] == 0.10
    assert result["portfolio_backtest_performed"] is True
    assert result["promotion_allowed"] is False
    assert result["threshold_optimization_performed"] is False
    assert (tmp_path / "out" / "overlay_trade_log.csv").is_file()
