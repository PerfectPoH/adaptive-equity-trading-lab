from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis.small_cap_backtest_report import build_small_cap_backtest_report, write_small_cap_backtest_report_markdown


def _candidate_export() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of": "2024-01-01",
                "symbol": "AAA",
                "operational_candidate": True,
                "passes_universe_filter": True,
                "universe_rejection_reasons": "",
                "small_cap_setup": "breakout_continuation",
                "small_cap_scanner_reject_reason": "",
                "market_regime_trade_allowed": True,
                "market_regime_block_reason": "",
                "small_cap_execution_valid": True,
                "small_cap_execution_skip_reason": "",
                "small_cap_position_notional": 1_000.0,
            },
            {
                "as_of": "2024-01-01",
                "symbol": "BBB",
                "operational_candidate": False,
                "passes_universe_filter": False,
                "universe_rejection_reasons": "market_cap_above_max;dollar_volume_below_min",
                "small_cap_setup": "",
                "small_cap_scanner_reject_reason": "relative_volume_below_min;atr_pct_above_max",
                "market_regime_trade_allowed": False,
                "market_regime_block_reason": "vix_above_max",
                "small_cap_execution_valid": False,
                "small_cap_execution_skip_reason": "",
                "small_cap_position_notional": 2_500.0,
            },
            {
                "as_of": "2024-01-02",
                "symbol": "CCC",
                "operational_candidate": False,
                "passes_universe_filter": True,
                "universe_rejection_reasons": "",
                "small_cap_setup": "post_gap_drift",
                "small_cap_scanner_reject_reason": "gap_above_max",
                "market_regime_trade_allowed": True,
                "market_regime_block_reason": "",
                "small_cap_execution_valid": False,
                "small_cap_execution_skip_reason": "gap_above_max",
                "small_cap_position_notional": 0.0,
            },
        ]
    )


def _benchmark_report() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"benchmark": "cash_flat", "return": 0.0, "observations": 2, "description": "Cash"},
            {"benchmark": "iwm_proxy", "return": 0.03, "observations": 1, "description": "IWM"},
            {"benchmark": "equal_weight_universe", "return": 0.04, "observations": 3, "description": "Universe"},
            {"benchmark": "random_entry_baseline", "return": 0.02, "observations": 3, "description": "Random"},
            {"benchmark": "ticker_holding_window", "return": 0.08, "observations": 1, "description": "Candidates"},
        ]
    )


def test_build_small_cap_backtest_report_summarizes_candidates_and_verdict() -> None:
    report = build_small_cap_backtest_report(_candidate_export(), _benchmark_report())

    assert report["verdict"] == "beats_primary_benchmark"
    assert report["candidate_summary"] == {
        "rows": 3,
        "operational_candidates": 1,
        "unique_symbols": 3,
        "candidate_dates": 2,
        "conversion_rate": 1 / 3,
        "total_position_notional": 3_500.0,
        "operational_position_notional": 1_000.0,
    }
    assert report["primary_benchmark"] == "equal_weight_universe"
    assert report["strategy_proxy_return"] == 0.08
    assert report["primary_benchmark_return"] == 0.04
    assert report["excess_return"] == 0.04


def test_build_small_cap_backtest_report_includes_diagnostics() -> None:
    report = build_small_cap_backtest_report(_candidate_export(), _benchmark_report())

    assert report["setup_counts"] == {"breakout_continuation": 1}
    assert report["regime_block_reasons"] == {"vix_above_max": 1}
    assert report["execution_skip_reasons"] == {"gap_above_max": 1}
    assert report["universe_rejection_reasons"] == {"dollar_volume_below_min": 1, "market_cap_above_max": 1}
    assert report["scanner_reject_reasons"] == {
        "atr_pct_above_max": 1,
        "gap_above_max": 1,
        "relative_volume_below_min": 1,
    }


def test_build_small_cap_backtest_report_includes_metadata_diagnostics() -> None:
    metadata_diagnostics = pd.DataFrame([{"symbol": "BLDE", "status": "fail", "reason": "missing_market_cap"}])

    report = build_small_cap_backtest_report(_candidate_export(), _benchmark_report(), metadata_diagnostics=metadata_diagnostics)

    assert report["metadata_diagnostics"] == [{"symbol": "BLDE", "status": "fail", "reason": "missing_market_cap"}]
    assert report["metadata_diagnostic_reasons"] == {"missing_market_cap": 1}


def test_build_small_cap_backtest_report_includes_portfolio_summary() -> None:
    portfolio_summary = {
        "initial_cash": 100_000.0,
        "ending_cash": 104_000.0,
        "total_pnl": 4_000.0,
        "return_pct": 0.04,
        "total_trades": 1,
        "total_rejections": 1,
    }
    portfolio_rejection_summary = {"insufficient_funds": 1}

    report = build_small_cap_backtest_report(
        _candidate_export(),
        _benchmark_report(),
        portfolio_summary=portfolio_summary,
        portfolio_rejection_summary=portfolio_rejection_summary,
    )

    assert report["portfolio_summary"] == portfolio_summary
    assert report["portfolio_return"] == 0.04
    assert report["portfolio_rejection_summary"] == {"insufficient_funds": 1}


def test_build_small_cap_backtest_report_includes_portfolio_diagnostics() -> None:
    outlier_breakdown = {"top_3_pnl_contribution_pct": 0.75, "outlier_concentration_alert": True}
    score_profile = pd.DataFrame([{"score_bucket": "Q1", "trade_count": 2, "avg_return_pct": 0.05}])
    cash_starvation_summary = {"insufficient_funds_rejections": 3, "avg_missed_return_pct": -0.04}
    setup_summary = pd.DataFrame([{"setup_type": "panic_reversal", "trade_count": 2, "total_pnl": 50.0}])
    setup_score_profile = pd.DataFrame([{"setup_type": "panic_reversal", "score_bucket": "Q1", "trade_count": 2}])
    setup_cash_starvation_summary = pd.DataFrame([{"setup_type": "panic_reversal", "evaluable_missed_trades": 2}])

    report = build_small_cap_backtest_report(
        _candidate_export(),
        _benchmark_report(),
        portfolio_outlier_breakdown=outlier_breakdown,
        portfolio_score_profile=score_profile,
        portfolio_cash_starvation_summary=cash_starvation_summary,
        portfolio_setup_summary=setup_summary,
        portfolio_setup_score_profile=setup_score_profile,
        portfolio_setup_cash_starvation_summary=setup_cash_starvation_summary,
    )

    assert report["portfolio_outlier_breakdown"] == outlier_breakdown
    assert report["portfolio_score_profile"] == [{"score_bucket": "Q1", "trade_count": 2, "avg_return_pct": 0.05}]
    assert report["portfolio_cash_starvation_summary"] == cash_starvation_summary
    assert report["portfolio_setup_summary"] == [{"setup_type": "panic_reversal", "trade_count": 2, "total_pnl": 50.0}]
    assert report["portfolio_setup_score_profile"] == [{"setup_type": "panic_reversal", "score_bucket": "Q1", "trade_count": 2}]
    assert report["portfolio_setup_cash_starvation_summary"] == [{"setup_type": "panic_reversal", "evaluable_missed_trades": 2}]


def test_build_small_cap_backtest_report_handles_insufficient_benchmark_data() -> None:
    benchmark_report = pd.DataFrame(
        [
            {"benchmark": "ticker_holding_window", "return": float("nan"), "observations": 0, "description": "Candidates"},
            {"benchmark": "equal_weight_universe", "return": float("nan"), "observations": 0, "description": "Universe"},
        ]
    )

    report = build_small_cap_backtest_report(_candidate_export(), benchmark_report)

    assert report["verdict"] == "insufficient_data"
    assert report["decision"].startswith("Non promuovere")


def test_write_small_cap_backtest_report_markdown_includes_verdict(tmp_path: Path) -> None:
    output_path = tmp_path / "small_cap_report.md"

    metadata_diagnostics = pd.DataFrame([{"symbol": "BLDE", "status": "fail", "reason": "missing_market_cap"}])

    report = write_small_cap_backtest_report_markdown(
        _candidate_export(),
        _benchmark_report(),
        output_path,
        metadata_diagnostics=metadata_diagnostics,
        portfolio_summary={"return_pct": 0.04, "total_trades": 1, "ending_cash": 104_000.0},
        portfolio_rejection_summary={"insufficient_funds": 1},
        portfolio_outlier_breakdown={"top_3_pnl_contribution_pct": 0.75, "outlier_concentration_alert": True},
        portfolio_score_profile=pd.DataFrame([{"score_bucket": "Q1", "trade_count": 2, "avg_return_pct": 0.05}]),
        portfolio_cash_starvation_summary={"insufficient_funds_rejections": 1, "avg_missed_return_pct": -0.04},
        portfolio_setup_summary=pd.DataFrame([{"setup_type": "panic_reversal", "trade_count": 2, "total_pnl": 50.0}]),
        portfolio_setup_score_profile=pd.DataFrame([{"setup_type": "panic_reversal", "score_bucket": "Q1", "trade_count": 2}]),
        portfolio_setup_cash_starvation_summary=pd.DataFrame([{"setup_type": "panic_reversal", "evaluable_missed_trades": 2}]),
    )

    content = output_path.read_text(encoding="utf-8")
    assert report["verdict"] == "beats_primary_benchmark"
    assert "# Small-Cap Backtest Report" in content
    assert "beats_primary_benchmark" in content
    assert "equal_weight_universe" in content
    assert "gap_above_max" in content
    assert "## Universe Rejection Reasons" in content
    assert "## Scanner Reject Reasons" in content
    assert "## Metadata Diagnostics" in content
    assert "missing_market_cap" in content
    assert "## Portfolio Backtest" in content
    assert "return_pct: 0.04" in content
    assert "## Portfolio Rejection Summary" in content
    assert "insufficient_funds" in content
    assert "## Portfolio Outlier Breakdown" in content
    assert "top_3_pnl_contribution_pct: 0.75" in content
    assert "## Score Profile Report" in content
    assert "Q1" in content
    assert "## Cash Starvation Diagnostics" in content
    assert "avg_missed_return_pct: -0.04" in content
    assert "## Setup Diagnostics" in content
    assert "panic_reversal" in content
    assert "## Setup Score Profile Report" in content
    assert "## Setup Cash Starvation Diagnostics" in content
