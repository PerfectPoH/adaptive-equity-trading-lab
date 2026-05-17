from __future__ import annotations

import pandas as pd

from src.backtest.small_cap_execution import SmallCapExecutionConfig
from src.backtest.small_cap_portfolio_backtester import (
    SmallCapPortfolioBacktestConfig,
    filter_small_cap_portfolio_candidates,
    run_small_cap_portfolio_backtest,
)


def _frame(closes: list[float], opens: list[float] | None = None) -> pd.DataFrame:
    index = pd.bdate_range("2024-01-01", periods=len(closes))
    open_values = opens if opens is not None else closes
    return pd.DataFrame(
        {
            "Open": open_values,
            "High": [value + 0.5 for value in closes],
            "Low": [value - 0.5 for value in closes],
            "Close": closes,
            "Volume": [1_000_000] * len(closes),
            "atr": [0.5] * len(closes),
            "avg_dollar_volume_20d": [2_000_000.0] * len(closes),
        },
        index=index,
    )


def _candidate(symbol: str, as_of: str, score: float = 100.0, setup: str = "breakout_continuation") -> dict[str, object]:
    return {
        "symbol": symbol,
        "as_of": as_of,
        "operational_candidate": True,
        "small_cap_scanner_score": score,
        "small_cap_setup": setup,
        "gap_pct": 0.02,
        "relative_volume_20d": 2.5,
    }


def _config(initial_cash: float = 100_000.0, holding_period_bars: int = 2, max_concurrent_positions: int = 5) -> SmallCapPortfolioBacktestConfig:
    return SmallCapPortfolioBacktestConfig(
        initial_cash=initial_cash,
        holding_period_bars=holding_period_bars,
        max_concurrent_positions=max_concurrent_positions,
        execution=SmallCapExecutionConfig(spread_bps=0.0, slippage_bps=0.0, min_trade_notional=100.0),
    )


def test_portfolio_backtester_opens_and_closes_trade_with_cash_ledger() -> None:
    frames = {"AAA": _frame([10.0, 10.0, 11.0, 12.0, 13.0])}
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01")])

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config())

    trade = result.trade_log.iloc[0]
    assert len(result.trade_log) == 1
    assert trade["symbol"] == "AAA"
    assert trade["entry_date"] == pd.Timestamp("2024-01-02")
    assert trade["exit_date"] == pd.Timestamp("2024-01-04")
    assert trade["entry_price"] == 10.0
    assert trade["exit_price"] == 12.0
    assert trade["position_notional"] == 13_330.0
    assert trade["pnl"] == 2_666.0
    assert result.summary["ending_cash"] == 102_666.0
    assert result.summary["total_trades"] == 1


def test_portfolio_backtester_rejects_candidate_when_cash_is_locked() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01", score=100.0), _candidate("BBB", "2024-01-01", score=90.0)])
    config = SmallCapPortfolioBacktestConfig(
        initial_cash=15_000.0,
        holding_period_bars=2,
        execution=SmallCapExecutionConfig(spread_bps=0.0, slippage_bps=0.0, min_trade_notional=100.0, risk_fraction=1.0),
    )

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log["symbol"].tolist() == ["AAA"]
    assert result.rejection_summary == {"insufficient_funds": 1}
    assert result.rejections.iloc[0]["symbol"] == "BBB"


def test_portfolio_backtester_releases_cash_before_later_candidate() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 12.0, 12.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 10.0, 10.0, 11.0]),
    }
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01"), _candidate("BBB", "2024-01-03")])

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config(initial_cash=15_000.0, holding_period_bars=1))

    assert result.trade_log["symbol"].tolist() == ["AAA", "BBB"]
    assert result.rejection_summary == {}
    assert result.summary["total_trades"] == 2
    assert result.summary["ending_cash"] > 15_000.0


def test_portfolio_backtester_cash_stays_locked_until_exit_date() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0, 13.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0, 13.0]),
        "CCC": _frame([10.0, 10.0, 11.0, 12.0, 13.0]),
    }
    candidates = pd.DataFrame(
        [
            _candidate("AAA", "2024-01-01", score=100.0),
            _candidate("BBB", "2024-01-02", score=90.0),
            _candidate("CCC", "2024-01-03", score=80.0),
        ]
    )
    config = SmallCapPortfolioBacktestConfig(
        initial_cash=15_000.0,
        holding_period_bars=1,
        execution=SmallCapExecutionConfig(spread_bps=0.0, slippage_bps=0.0, min_trade_notional=100.0, risk_fraction=1.0),
    )

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log["symbol"].tolist() == ["AAA", "CCC"]
    assert result.rejections["symbol"].tolist() == ["BBB"]
    assert result.rejections.iloc[0]["reject_reason"] == "insufficient_funds"
    assert result.rejections.iloc[0]["available_cash"] == 0.0
    assert result.trade_log.iloc[0]["cash_after_exit"] == 16_500.0


def test_portfolio_backtester_releases_exit_cash_before_same_day_candidate() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0]),
        "BBB": _frame([10.0, 10.0, 10.0, 11.0, 11.0, 12.0, 13.0]),
    }
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01", score=100.0), _candidate("BBB", "2024-01-04", score=90.0)])
    config = SmallCapPortfolioBacktestConfig(
        initial_cash=15_000.0,
        holding_period_bars=2,
        execution=SmallCapExecutionConfig(spread_bps=0.0, slippage_bps=0.0, min_trade_notional=100.0, risk_fraction=1.0),
    )

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log["symbol"].tolist() == ["AAA", "BBB"]
    assert result.trade_log.iloc[0]["exit_date"] == pd.Timestamp("2024-01-04")
    assert result.trade_log.iloc[1]["entry_date"] == pd.Timestamp("2024-01-05")
    assert result.trade_log.iloc[1]["cash_after_entry"] == 4.0
    assert result.rejection_summary == {}


def test_portfolio_backtester_rejects_when_holding_window_cannot_close_position() -> None:
    frames = {"AAA": _frame([10.0, 10.0])}
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01")])

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config(holding_period_bars=1))

    assert result.trade_log.empty
    assert result.rejection_summary == {"missing_price_path": 1}
    assert result.summary["ending_cash"] == 100_000.0
    assert result.equity_curve.iloc[0]["open_positions"] == 0


def test_portfolio_backtester_gap_rejection_does_not_spend_cash() -> None:
    frames = {"AAA": _frame([10.0, 12.0, 12.0, 12.0], opens=[10.0, 12.0, 12.0, 12.0])}
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01")])
    config = SmallCapPortfolioBacktestConfig(
        initial_cash=15_000.0,
        holding_period_bars=1,
        execution=SmallCapExecutionConfig(spread_bps=0.0, slippage_bps=0.0, max_next_open_gap=0.10, min_trade_notional=100.0),
    )

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log.empty
    assert result.rejection_summary == {"gap_above_max": 1}
    assert result.rejections.iloc[0]["available_cash"] == 15_000.0
    assert result.summary["ending_cash"] == 15_000.0
    assert result.equity_curve.iloc[0]["cash"] == 15_000.0


def test_portfolio_backtester_open_position_equity_keeps_cash_locked_before_exit() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0, 13.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0, 13.0]),
    }
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01", score=100.0), _candidate("BBB", "2024-01-02", score=90.0)])
    config = SmallCapPortfolioBacktestConfig(
        initial_cash=15_000.0,
        holding_period_bars=2,
        execution=SmallCapExecutionConfig(spread_bps=0.0, slippage_bps=0.0, min_trade_notional=100.0, risk_fraction=1.0),
    )

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    first_open_row = result.equity_curve[result.equity_curve["date"].eq(pd.Timestamp("2024-01-01"))].iloc[0]
    second_open_row = result.equity_curve[result.equity_curve["date"].eq(pd.Timestamp("2024-01-02"))].iloc[0]
    final_row = result.equity_curve.iloc[-1]
    assert first_open_row["cash"] == 0.0
    assert second_open_row["cash"] == 0.0
    assert second_open_row["open_positions"] == 1
    assert second_open_row["open_position_notional"] == 15_000.0
    assert final_row["cash"] == result.summary["ending_cash"]
    assert final_row["open_positions"] == 0


def test_portfolio_backtester_respects_max_concurrent_positions() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01", score=100.0), _candidate("BBB", "2024-01-01", score=90.0)])

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config(max_concurrent_positions=1))

    assert result.trade_log["symbol"].tolist() == ["AAA"]
    assert result.rejection_summary == {"max_concurrent_positions": 1}


def test_portfolio_backtester_builds_equity_curve() -> None:
    frames = {"AAA": _frame([10.0, 10.0, 11.0, 12.0, 13.0])}
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01")])

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config())

    assert result.equity_curve["date"].tolist() == [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-04")]
    assert result.equity_curve.iloc[0]["cash"] == 86_670.0
    assert result.equity_curve.iloc[-1]["equity"] == 102_666.0


def test_portfolio_backtester_preserves_scanner_score_in_trade_log() -> None:
    frames = {"AAA": _frame([10.0, 10.0, 11.0, 12.0, 13.0])}
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01", score=87.5)])

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config())

    assert result.trade_log.iloc[0]["small_cap_scanner_score"] == 87.5


def test_portfolio_backtester_uses_preregistered_rankex_tie_breakers() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
        "CCC": _frame([10.0, 10.0, 11.0, 12.0]),
        "DDD": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame(
        [
            {**_candidate("AAA", "2024-01-01", score=100.0), "relative_volume_20d": 2.0, "open_to_close_return": 0.50},
            {**_candidate("BBB", "2024-01-01", score=100.0), "relative_volume_20d": 3.0, "open_to_close_return": 0.10},
            {**_candidate("DDD", "2024-01-01", score=100.0), "relative_volume_20d": 3.0, "open_to_close_return": 0.20},
            {**_candidate("CCC", "2024-01-01", score=100.0), "relative_volume_20d": 3.0, "open_to_close_return": 0.20},
        ]
    )

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config(max_concurrent_positions=1))

    assert result.trade_log["symbol"].tolist() == ["CCC"]
    assert result.rejections["symbol"].tolist() == ["DDD", "BBB", "AAA"]


def test_portfolio_backtester_preserves_setup_in_trade_and_rejection_logs() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame(
        [
            _candidate("AAA", "2024-01-01", score=100.0, setup="panic_reversal"),
            _candidate("BBB", "2024-01-01", score=90.0, setup="post_gap_drift"),
        ]
    )

    config = _config(initial_cash=15_000.0, max_concurrent_positions=1)

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log.iloc[0]["small_cap_setup"] == "panic_reversal"
    assert result.rejections.iloc[0]["small_cap_setup"] == "post_gap_drift"


def test_portfolio_backtester_preserves_scanner_features_in_trade_and_rejection_logs() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame(
        [
            {**_candidate("AAA", "2024-01-01", score=100.0), "gap_pct": 0.04, "relative_volume_20d": 3.0},
            {**_candidate("BBB", "2024-01-01", score=90.0), "gap_pct": -0.03, "relative_volume_20d": 1.7},
        ]
    )

    config = _config(initial_cash=15_000.0, max_concurrent_positions=1)

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log.iloc[0]["gap_pct"] == 0.04
    assert result.trade_log.iloc[0]["relative_volume_20d"] == 3.0
    assert result.rejections.iloc[0]["gap_pct"] == -0.03
    assert result.rejections.iloc[0]["relative_volume_20d"] == 1.7


def test_portfolio_backtester_preserves_regime_features_in_trade_and_rejection_logs() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame(
        [
            {
                **_candidate("AAA", "2024-01-01", score=100.0),
                "iwm_close": 210.0,
                "iwm_ema_50": 200.0,
                "iwm_ema_200": 190.0,
                "vix_close": 18.0,
            },
            {
                **_candidate("BBB", "2024-01-01", score=90.0),
                "iwm_close": 195.0,
                "iwm_ema_50": 200.0,
                "iwm_ema_200": 205.0,
                "vix_close": 28.0,
            },
        ]
    )

    config = _config(initial_cash=15_000.0, max_concurrent_positions=1)

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log.iloc[0]["iwm_close"] == 210.0
    assert result.trade_log.iloc[0]["iwm_ema_50"] == 200.0
    assert result.trade_log.iloc[0]["iwm_ema_200"] == 190.0
    assert result.trade_log.iloc[0]["vix_close"] == 18.0
    assert result.rejections.iloc[0]["iwm_close"] == 195.0
    assert result.rejections.iloc[0]["iwm_ema_50"] == 200.0
    assert result.rejections.iloc[0]["iwm_ema_200"] == 205.0
    assert result.rejections.iloc[0]["vix_close"] == 28.0


def test_portfolio_backtester_can_reject_disallowed_setups_without_spending_cash() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame(
        [
            _candidate("AAA", "2024-01-01", score=100.0, setup="post_gap_drift"),
            _candidate("BBB", "2024-01-01", score=90.0, setup="breakout_continuation"),
        ]
    )
    config = SmallCapPortfolioBacktestConfig(
        initial_cash=15_000.0,
        holding_period_bars=2,
        allowed_setups=("breakout_continuation",),
        execution=SmallCapExecutionConfig(spread_bps=0.0, slippage_bps=0.0, min_trade_notional=100.0),
    )

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log["symbol"].tolist() == ["BBB"]
    assert result.rejection_summary == {"setup_excluded": 1}
    assert result.rejections.iloc[0]["symbol"] == "AAA"
    assert result.rejections.iloc[0]["small_cap_setup"] == "post_gap_drift"


def test_portfolio_backtester_can_reject_candidates_below_feature_filter() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame(
        [
            {**_candidate("AAA", "2024-01-01", score=100.0), "open_to_close_return": 0.12},
            {**_candidate("BBB", "2024-01-01", score=90.0), "open_to_close_return": 0.04},
        ]
    )
    config = SmallCapPortfolioBacktestConfig(
        initial_cash=100_000.0,
        holding_period_bars=2,
        feature_filters=(
            {
                "setup": "breakout_continuation",
                "feature": "open_to_close_return",
                "min_value": 0.08,
            },
        ),
        execution=SmallCapExecutionConfig(spread_bps=0.0, slippage_bps=0.0, min_trade_notional=100.0),
    )

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log["symbol"].tolist() == ["AAA"]
    assert result.rejection_summary == {"feature_filtered": 1}
    rejection = result.rejections.iloc[0]
    assert rejection["symbol"] == "BBB"
    assert rejection["reject_reason"] == "feature_filtered"
    assert rejection["filter_feature"] == "open_to_close_return"
    assert rejection["filter_value"] == 0.04
    assert rejection["filter_min_value"] == 0.08


def test_portfolio_backtester_can_reject_candidates_by_regime_filter() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame(
        [
            {**_candidate("AAA", "2024-01-01", score=100.0), "iwm_close": 210.0, "iwm_ema_200": 200.0},
            {**_candidate("BBB", "2024-01-01", score=90.0), "iwm_close": 195.0, "iwm_ema_200": 200.0},
        ]
    )
    config = SmallCapPortfolioBacktestConfig(
        initial_cash=100_000.0,
        holding_period_bars=2,
        regime_filters=(
            {
                "feature": "iwm_close",
                "operator": ">",
                "threshold_feature": "iwm_ema_200",
            },
        ),
        execution=SmallCapExecutionConfig(spread_bps=0.0, slippage_bps=0.0, min_trade_notional=100.0),
    )

    result = run_small_cap_portfolio_backtest(candidates, frames, config=config)

    assert result.trade_log["symbol"].tolist() == ["AAA"]
    assert result.rejection_summary == {"regime_filtered": 1}
    rejection = result.rejections.iloc[0]
    assert rejection["symbol"] == "BBB"
    assert rejection["reject_reason"] == "regime_filtered"
    assert rejection["regime_filter_feature"] == "iwm_close"
    assert rejection["regime_filter_operator"] == ">"
    assert rejection["regime_filter_value"] == 195.0
    assert rejection["regime_filter_threshold_feature"] == "iwm_ema_200"
    assert rejection["regime_filter_threshold_value"] == 200.0


def test_filter_small_cap_portfolio_candidates_applies_setup_and_feature_filters() -> None:
    candidates = pd.DataFrame(
        [
            {**_candidate("AAA", "2024-01-01", setup="breakout_continuation"), "open_to_close_return": 0.12},
            {**_candidate("BBB", "2024-01-01", setup="breakout_continuation"), "open_to_close_return": 0.04},
            {**_candidate("CCC", "2024-01-01", setup="post_gap_drift"), "open_to_close_return": 0.20},
        ]
    )
    config = SmallCapPortfolioBacktestConfig(
        allowed_setups=("breakout_continuation",),
        feature_filters=(
            {
                "setup": "breakout_continuation",
                "feature": "open_to_close_return",
                "min_value": 0.08,
            },
        ),
    )

    filtered = filter_small_cap_portfolio_candidates(candidates, config)

    assert filtered["symbol"].tolist() == ["AAA"]
    assert "as_of_ts" not in filtered.columns


def test_filter_small_cap_portfolio_candidates_applies_regime_filters() -> None:
    candidates = pd.DataFrame(
        [
            {**_candidate("AAA", "2024-01-01"), "iwm_close": 210.0, "iwm_ema_200": 200.0},
            {**_candidate("BBB", "2024-01-01"), "iwm_close": 195.0, "iwm_ema_200": 200.0},
        ]
    )
    config = SmallCapPortfolioBacktestConfig(
        regime_filters=(
            {
                "feature": "iwm_close",
                "operator": ">",
                "threshold_feature": "iwm_ema_200",
            },
        ),
    )

    filtered = filter_small_cap_portfolio_candidates(candidates, config)

    assert filtered["symbol"].tolist() == ["AAA"]
