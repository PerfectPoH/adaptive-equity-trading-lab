from __future__ import annotations

import pandas as pd

from src.analysis.small_cap_portfolio_diagnostics import build_portfolio_outlier_breakdown, build_score_profile_report


def test_portfolio_outlier_breakdown_flags_concentrated_pnl() -> None:
    trade_log = pd.DataFrame(
        [
            {"symbol": "AAA", "pnl": 50.0, "return_pct": 0.50},
            {"symbol": "BBB", "pnl": 30.0, "return_pct": 0.30},
            {"symbol": "CCC", "pnl": 20.0, "return_pct": 0.20},
            {"symbol": "DDD", "pnl": -10.0, "return_pct": -0.10},
        ]
    )

    breakdown = build_portfolio_outlier_breakdown(trade_log, alert_top_n=3, alert_threshold=0.40)

    assert breakdown["total_pnl"] == 90.0
    assert breakdown["gross_profit"] == 100.0
    assert breakdown["gross_loss"] == -10.0
    assert breakdown["top_1_pnl_contribution_pct"] == 50.0 / 90.0
    assert breakdown["top_3_pnl_contribution_pct"] == 100.0 / 90.0
    assert breakdown["outlier_concentration_alert"] is True
    assert breakdown["best_trade_symbol"] == "AAA"
    assert breakdown["worst_trade_symbol"] == "DDD"


def test_portfolio_outlier_breakdown_handles_empty_trade_log() -> None:
    breakdown = build_portfolio_outlier_breakdown(pd.DataFrame())

    assert breakdown["total_trades"] == 0
    assert breakdown["total_pnl"] == 0.0
    assert breakdown["outlier_concentration_alert"] is False


def test_score_profile_report_groups_trades_by_score_decile() -> None:
    trade_log = pd.DataFrame(
        [
            {"symbol": "A", "small_cap_scanner_score": 10.0, "return_pct": -0.10, "pnl": -10.0},
            {"symbol": "B", "small_cap_scanner_score": 20.0, "return_pct": 0.00, "pnl": 0.0},
            {"symbol": "C", "small_cap_scanner_score": 80.0, "return_pct": 0.20, "pnl": 20.0},
            {"symbol": "D", "small_cap_scanner_score": 90.0, "return_pct": 0.30, "pnl": 30.0},
        ]
    )

    profile = build_score_profile_report(trade_log, bins=2)

    assert profile["score_bucket"].tolist() == ["Q1", "Q2"]
    assert profile["trade_count"].tolist() == [2, 2]
    assert profile["win_rate"].tolist() == [0.0, 1.0]
    assert profile["total_pnl"].tolist() == [-10.0, 50.0]
    assert profile["avg_return_pct"].tolist() == [-0.05, 0.25]


def test_score_profile_report_returns_empty_schema_when_score_missing() -> None:
    profile = build_score_profile_report(pd.DataFrame([{"symbol": "A", "pnl": 10.0}]))

    assert profile.empty
    assert profile.columns.tolist() == [
        "score_bucket",
        "min_score",
        "max_score",
        "trade_count",
        "avg_return_pct",
        "median_return_pct",
        "win_rate",
        "total_pnl",
        "avg_pnl",
        "simple_trade_sharpe",
    ]
