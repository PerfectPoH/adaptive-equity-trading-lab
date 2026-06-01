from __future__ import annotations

import pandas as pd

from src.experiments.norgate_portfolio_trial_backtest import (
    build_norgate_admissible_bundle_manifest,
    build_tradability_filtered_frames,
    persist_norgate_trial_outputs,
    run_trial_limited_portfolio_diagnostic,
)


def _frame(start: float, step: float, periods: int = 95) -> pd.DataFrame:
    index = pd.bdate_range("2025-01-01", periods=periods)
    close = [start + step * i for i in range(periods)]
    return pd.DataFrame(
        {
            "Open": close,
            "High": [value * 1.01 for value in close],
            "Low": [value * 0.99 for value in close],
            "Close": close,
            "Volume": [1_000_000] * periods,
            "Turnover": [value * 1_000_000 for value in close],
        },
        index=index,
    )


def test_norgate_bundle_is_trial_limited_but_survivorship_aware() -> None:
    probe = {
        "probe_id": "NORGATE-DATA-PROBE-001",
        "evidence": {
            "us_equities_database_available": True,
            "us_delisted_database_available": True,
            "us_delisted_prices_accessible": True,
            "us_delisted_listing_or_delisting_dates_available": True,
            "us_active_adjusted_daily_prices_available": True,
        },
    }

    bundle = build_norgate_admissible_bundle_manifest(
        probe,
        active_symbols=["AAA", "BBB"],
        delisted_symbols=["DEAD-202501"],
    )

    assert bundle["status"] == "NORGATE_ADMISSIBLE_DATA_BUNDLE_TRIAL_LIMITED"
    assert bundle["trial_limited"] is True
    assert bundle["survivorship_free_universe"] is True
    assert bundle["promotion_allowed"] is False
    assert "delisted_symbol_prices" in bundle["covered_fields"]
    assert bundle["symbol_counts"] == {"active": 2, "delisted": 1, "total": 3}


def test_norgate_bundle_blocks_without_delisted_symbols() -> None:
    bundle = build_norgate_admissible_bundle_manifest(
        {"probe_id": "NORGATE-DATA-PROBE-001", "evidence": {}},
        active_symbols=["AAA"],
        delisted_symbols=[],
    )

    assert bundle["status"] == "NORGATE_DATA_BUNDLE_BLOCKED"
    assert "delisted_symbol_sample_missing" in bundle["blockers"]
    assert bundle["promotion_allowed"] is False


def test_trial_limited_portfolio_diagnostic_keeps_unavailable_sleeves_disabled() -> None:
    frames = {
        "AAA": _frame(10.0, 0.05),
        "BBB": _frame(20.0, -0.04),
        "DEAD-202501": _frame(5.0, 0.02, periods=75),
    }
    bundle = build_norgate_admissible_bundle_manifest(
        {"probe_id": "NORGATE-DATA-PROBE-001", "evidence": {"us_delisted_prices_accessible": True}},
        active_symbols=["AAA", "BBB"],
        delisted_symbols=["DEAD-202501"],
    )
    gate = {"gate_id": "NORGATE-PORTFOLIO-TRIAL-BACKTEST-GATE-001", "parameter_sweep_allowed": False}

    result = run_trial_limited_portfolio_diagnostic(frames, bundle, gate)

    assert result["final_decision"]["decision"] == "NORGATE_PORTFOLIO_TRIAL_LIMITED_ARCHIVE_NO_PROMOTION"
    assert result["promotion_allowed"] is False
    assert result["parameter_sweep_performed"] is False
    assert result["disabled_sleeves"] == {
        "Catalyst": "missing_point_in_time_event_and_direction_source",
        "Dollar-Bar Microstructure": "daily_bars_cannot_reconstruct_dollar_bars",
    }
    assert result["symbol_counts"]["delisted"] == 1
    assert result["summary"]["total_trades"] > 0
    assert "ex_best_symbol_weighted_net_return" in result["robustness"]
    assert "promotion_locked_until_long_history_oos_gate" in result["final_decision"]["blockers"]


def test_trial_limited_portfolio_diagnostic_blocks_outlier_dependency() -> None:
    frames = {
        "AAA": _frame(2.0, 1.0),
        "BBB": _frame(20.0, -0.04),
        "DEAD-202501": _frame(10.0, -0.01),
    }
    bundle = build_norgate_admissible_bundle_manifest(
        {"probe_id": "NORGATE-DATA-PROBE-001", "evidence": {"us_delisted_prices_accessible": True}},
        active_symbols=["AAA", "BBB"],
        delisted_symbols=["DEAD-202501"],
    )
    gate = {"gate_id": "NORGATE-PORTFOLIO-TRIAL-BACKTEST-GATE-001", "parameter_sweep_allowed": False}

    result = run_trial_limited_portfolio_diagnostic(frames, bundle, gate)

    if result["robustness"]["ex_best_symbol_weighted_net_return"] <= 0:
        assert "outlier_dependency_ex_best_symbol_nonpositive" in result["final_decision"]["blockers"]


def test_persisted_report_surfaces_blockers(tmp_path) -> None:
    bundle = build_norgate_admissible_bundle_manifest(
        {"probe_id": "NORGATE-DATA-PROBE-001", "evidence": {"us_delisted_prices_accessible": True}},
        active_symbols=["AAA"],
        delisted_symbols=["DEAD-202501"],
    )
    result = {
        "summary": {"total_trades": 1, "weighted_net_return_sum": 0.1, "max_drawdown": -0.01},
        "robustness": {"ex_best_symbol_weighted_net_return": -0.1},
        "symbol_counts": {"active": 1, "delisted": 1},
        "tradability_filter": {"accepted_symbols": ["AAA"], "rejections": {"PENNY": "minimum_price_below_threshold"}},
        "trade_log": [],
        "equity_curve": [],
        "trial_limited": True,
        "final_decision": {
            "decision": "NORGATE_PORTFOLIO_TRIAL_LIMITED_ARCHIVE_NO_PROMOTION",
            "blockers": ["outlier_dependency_ex_best_symbol_nonpositive"],
        },
    }

    paths = persist_norgate_trial_outputs(bundle, result, output_dir=tmp_path)

    report = pd.io.common.Path(paths["report_path"]).read_text(encoding="utf-8")
    assert "outlier_dependency_ex_best_symbol_nonpositive" in report
    assert "accepted symbols after filter" in report
    assert "tradability rejections" in report


def test_trial_limited_portfolio_diagnostic_flags_sub_dollar_tradability() -> None:
    frames = {
        "AAA": _frame(0.01, 0.001),
        "BBB": _frame(20.0, -0.04),
        "DEAD-202501": _frame(10.0, -0.01),
    }
    bundle = build_norgate_admissible_bundle_manifest(
        {"probe_id": "NORGATE-DATA-PROBE-001", "evidence": {"us_delisted_prices_accessible": True}},
        active_symbols=["AAA", "BBB"],
        delisted_symbols=["DEAD-202501"],
    )
    gate = {"gate_id": "NORGATE-PORTFOLIO-TRIAL-BACKTEST-GATE-001", "parameter_sweep_allowed": False}

    result = run_trial_limited_portfolio_diagnostic(frames, bundle, gate)

    assert "sub_dollar_trade_quality_blocker" in result["final_decision"]["blockers"]


def test_tradability_filter_removes_sub_dollar_and_low_turnover_before_signals() -> None:
    frames = {
        "PENNY": _frame(0.50, 0.01),
        "THIN": _frame(5.0, 0.01),
        "OK": _frame(5.0, 0.01),
    }
    frames["THIN"]["Turnover"] = 25_000.0
    frames["OK"]["Turnover"] = 2_000_000.0

    filtered, report = build_tradability_filtered_frames(
        frames,
        min_price=1.0,
        min_median_turnover=1_000_000.0,
        min_rows=90,
    )

    assert sorted(filtered) == ["OK"]
    assert report["accepted_symbols"] == ["OK"]
    assert report["rejections"]["PENNY"] == "minimum_price_below_threshold"
    assert report["rejections"]["THIN"] == "median_turnover_below_threshold"


def test_trial_limited_portfolio_diagnostic_blocks_sample_starved_rerun() -> None:
    frames = {
        "OK": _frame(5.0, 0.01),
        "DEAD-202501": _frame(10.0, -0.01),
    }
    bundle = build_norgate_admissible_bundle_manifest(
        {"probe_id": "NORGATE-DATA-PROBE-001", "evidence": {"us_delisted_prices_accessible": True}},
        active_symbols=["OK"],
        delisted_symbols=["DEAD-202501"],
    )
    gate = {"gate_id": "NORGATE-PORTFOLIO-TRIAL-BACKTEST-GATE-001", "parameter_sweep_allowed": False}

    result = run_trial_limited_portfolio_diagnostic(frames, bundle, gate)

    assert result["summary"]["total_trades"] < 20
    assert "sample_starved_after_tradability_filter" in result["final_decision"]["blockers"]
