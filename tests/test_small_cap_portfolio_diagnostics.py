from __future__ import annotations

import math

import pandas as pd

from src.analysis.small_cap_portfolio_diagnostics import (
    build_cash_starvation_report,
    build_portfolio_outlier_breakdown,
    build_score_profile_report,
    build_setup_cash_starvation_summary,
    build_setup_score_profile_report,
    build_setup_summary_report,
    summarize_cash_starvation_report,
)


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
    for n in (1, 3, 5):
        assert breakdown[f"pnl_excluding_top_{n}"] == 0.0
        assert breakdown[f"sign_flip_excluding_top_{n}"] is False
        assert math.isnan(breakdown[f"portfolio_return_excluding_top_{n}"])


def test_portfolio_outlier_breakdown_exposes_ex_outlier_pnl_without_initial_cash() -> None:
    trade_log = pd.DataFrame(
        [
            {"symbol": "AAA", "pnl": 50.0, "return_pct": 0.50},
            {"symbol": "BBB", "pnl": 30.0, "return_pct": 0.30},
            {"symbol": "CCC", "pnl": 20.0, "return_pct": 0.20},
            {"symbol": "DDD", "pnl": -10.0, "return_pct": -0.10},
        ]
    )

    breakdown = build_portfolio_outlier_breakdown(trade_log)

    # total_pnl = 90, top winners = [50, 30, 20]
    assert breakdown["pnl_excluding_top_1"] == 40.0
    assert breakdown["pnl_excluding_top_3"] == -10.0
    assert breakdown["pnl_excluding_top_5"] == -10.0  # only 3 winners available
    assert math.isnan(breakdown["portfolio_return_excluding_top_1"])
    assert math.isnan(breakdown["portfolio_return_excluding_top_3"])


def test_portfolio_outlier_breakdown_computes_portfolio_return_when_initial_cash_provided() -> None:
    trade_log = pd.DataFrame(
        [
            {"symbol": "AAA", "pnl": 50.0, "return_pct": 0.50},
            {"symbol": "BBB", "pnl": 30.0, "return_pct": 0.30},
            {"symbol": "CCC", "pnl": 20.0, "return_pct": 0.20},
            {"symbol": "DDD", "pnl": -10.0, "return_pct": -0.10},
        ]
    )

    breakdown = build_portfolio_outlier_breakdown(trade_log, initial_cash=1000.0)

    assert breakdown["portfolio_return_excluding_top_1"] == 40.0 / 1000.0
    assert breakdown["portfolio_return_excluding_top_3"] == -10.0 / 1000.0
    assert breakdown["portfolio_return_excluding_top_5"] == -10.0 / 1000.0


def test_portfolio_outlier_breakdown_flags_sign_flip_when_top_winners_dominate() -> None:
    """Reproduces the 2026-05-10 smoke verdict: top 3 trades supplied 100.86% of net P&L,
    so stripping them turns the equity curve negative. RISK-022 in the backlog."""
    trade_log = pd.DataFrame(
        [
            {"symbol": "LUNR", "pnl": 49931.0, "return_pct": 0.17},
            {"symbol": "BBAI", "pnl": 24443.0, "return_pct": 0.16},
            {"symbol": "OUST", "pnl": 26383.0, "return_pct": 0.42},
            {"symbol": "OUST", "pnl": -9879.0, "return_pct": -0.12},
            {"symbol": "BBAI", "pnl": -8000.0, "return_pct": -0.10},
            {"symbol": "LUNR", "pnl": -7000.0, "return_pct": -0.09},
            {"symbol": "BBAI", "pnl": -1630.0, "return_pct": -0.02},
        ]
    )

    breakdown = build_portfolio_outlier_breakdown(trade_log, initial_cash=100_000.0)

    assert breakdown["total_pnl"] > 0
    assert breakdown["pnl_excluding_top_3"] < 0
    assert breakdown["sign_flip_excluding_top_3"] is True
    assert breakdown["portfolio_return_excluding_top_3"] < 0


def test_portfolio_outlier_breakdown_sign_flip_false_when_winners_diversified() -> None:
    trade_log = pd.DataFrame(
        [
            {"symbol": "AAA", "pnl": 10.0, "return_pct": 0.10},
            {"symbol": "BBB", "pnl": 10.0, "return_pct": 0.10},
            {"symbol": "CCC", "pnl": 10.0, "return_pct": 0.10},
            {"symbol": "DDD", "pnl": 10.0, "return_pct": 0.10},
            {"symbol": "EEE", "pnl": 10.0, "return_pct": 0.10},
            {"symbol": "FFF", "pnl": 10.0, "return_pct": 0.10},
            {"symbol": "GGG", "pnl": -2.0, "return_pct": -0.02},
        ]
    )

    breakdown = build_portfolio_outlier_breakdown(trade_log, initial_cash=1000.0)

    assert breakdown["pnl_excluding_top_3"] == 58.0 - 30.0
    assert breakdown["sign_flip_excluding_top_3"] is False
    assert breakdown["portfolio_return_excluding_top_3"] > 0


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


def test_score_profile_report_keeps_identical_scores_in_same_bucket() -> None:
    trade_log = pd.DataFrame(
        [
            {"symbol": "A", "small_cap_scanner_score": 80.0, "return_pct": 0.10, "pnl": 10.0},
            {"symbol": "B", "small_cap_scanner_score": 80.0, "return_pct": -0.10, "pnl": -10.0},
            {"symbol": "C", "small_cap_scanner_score": 100.0, "return_pct": 0.20, "pnl": 20.0},
            {"symbol": "D", "small_cap_scanner_score": 100.0, "return_pct": -0.20, "pnl": -20.0},
        ]
    )

    profile = build_score_profile_report(trade_log, bins=10)

    assert profile["score_bucket"].tolist() == ["Q1", "Q2"]
    assert profile["min_score"].tolist() == [80.0, 100.0]
    assert profile["max_score"].tolist() == [80.0, 100.0]
    assert profile["trade_count"].tolist() == [2, 2]


def test_cash_starvation_report_scores_insufficient_funds_rejections() -> None:
    rejections = pd.DataFrame(
        [
            {"symbol": "AAA", "as_of": "2024-01-01", "reject_reason": "insufficient_funds", "available_cash": 500.0},
            {"symbol": "BBB", "as_of": "2024-01-01", "reject_reason": "gap_above_max", "available_cash": 500.0},
            {"symbol": "CCC", "as_of": "2024-01-01", "reject_reason": "insufficient_funds", "available_cash": 200.0},
        ]
    )
    frames = {
        "AAA": pd.DataFrame(
            {"Open": [10.0, 11.0, 12.0], "Close": [10.0, 11.0, 13.0]},
            index=pd.bdate_range("2024-01-01", periods=3),
        ),
        "CCC": pd.DataFrame(
            {"Open": [20.0, 20.0, 18.0], "Close": [20.0, 20.0, 18.0]},
            index=pd.bdate_range("2024-01-01", periods=3),
        ),
    }

    report = build_cash_starvation_report(rejections, frames, holding_period_bars=1)

    assert report["symbol"].tolist() == ["AAA", "CCC"]
    assert report["missed_return_pct"].tolist() == [13.0 / 11.0 - 1.0, 18.0 / 20.0 - 1.0]
    assert report["available_cash"].tolist() == [500.0, 200.0]


def test_cash_starvation_summary_quantifies_missed_opportunity_quality() -> None:
    report = pd.DataFrame(
        [
            {"symbol": "AAA", "missed_return_pct": 0.10},
            {"symbol": "BBB", "missed_return_pct": -0.05},
            {"symbol": "CCC", "missed_return_pct": 0.20},
        ]
    )

    summary = summarize_cash_starvation_report(report, total_insufficient_funds_rejections=5)

    assert summary["insufficient_funds_rejections"] == 5
    assert summary["evaluable_missed_trades"] == 3
    assert summary["missed_win_rate"] == 2 / 3
    assert summary["avg_missed_return_pct"] == (0.10 - 0.05 + 0.20) / 3
    assert summary["best_missed_symbol"] == "CCC"
    assert summary["worst_missed_symbol"] == "BBB"


def test_setup_summary_report_groups_trade_quality_by_setup() -> None:
    trade_log = pd.DataFrame(
        [
            {"symbol": "AAA", "small_cap_setup": "panic_reversal", "pnl": 100.0, "return_pct": 0.10},
            {"symbol": "BBB", "small_cap_setup": "panic_reversal", "pnl": -50.0, "return_pct": -0.05},
            {"symbol": "CCC", "small_cap_setup": "post_gap_drift", "pnl": -20.0, "return_pct": -0.02},
        ]
    )

    summary = build_setup_summary_report(trade_log, setup_column="small_cap_setup")

    assert summary["setup_type"].tolist() == ["panic_reversal", "post_gap_drift"]
    assert summary["trade_count"].tolist() == [2, 1]
    assert summary["total_pnl"].tolist() == [50.0, -20.0]
    assert summary["win_rate"].tolist() == [0.5, 0.0]


def test_setup_score_profile_report_profiles_scores_inside_each_setup() -> None:
    trade_log = pd.DataFrame(
        [
            {"symbol": "AAA", "small_cap_setup": "panic_reversal", "small_cap_scanner_score": 70.0, "pnl": -10.0, "return_pct": -0.10},
            {"symbol": "BBB", "small_cap_setup": "panic_reversal", "small_cap_scanner_score": 90.0, "pnl": 30.0, "return_pct": 0.30},
            {"symbol": "CCC", "small_cap_setup": "post_gap_drift", "small_cap_scanner_score": 80.0, "pnl": 20.0, "return_pct": 0.20},
        ]
    )

    profile = build_setup_score_profile_report(trade_log, setup_column="small_cap_setup", bins=2)

    assert profile["setup_type"].tolist() == ["panic_reversal", "panic_reversal", "post_gap_drift"]
    assert profile["score_bucket"].tolist() == ["Q1", "Q2", "Q1"]
    assert profile["total_pnl"].tolist() == [-10.0, 30.0, 20.0]


def test_setup_cash_starvation_summary_groups_missed_opportunities_by_setup() -> None:
    cash_starvation = pd.DataFrame(
        [
            {"symbol": "AAA", "small_cap_setup": "panic_reversal", "missed_return_pct": 0.10},
            {"symbol": "BBB", "small_cap_setup": "panic_reversal", "missed_return_pct": -0.05},
            {"symbol": "CCC", "small_cap_setup": "post_gap_drift", "missed_return_pct": -0.20},
        ]
    )

    summary = build_setup_cash_starvation_summary(cash_starvation, setup_column="small_cap_setup")

    assert summary["setup_type"].tolist() == ["panic_reversal", "post_gap_drift"]
    assert summary["evaluable_missed_trades"].tolist() == [2, 1]
    assert summary["avg_missed_return_pct"].tolist() == [0.025, -0.20]
    assert summary["missed_win_rate"].tolist() == [0.5, 0.0]
