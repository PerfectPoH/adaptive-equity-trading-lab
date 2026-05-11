from __future__ import annotations

import pandas as pd

from src.backtest.small_cap_execution import SmallCapExecutionConfig
from src.backtest.small_cap_portfolio_backtester import SmallCapPortfolioBacktestConfig, run_small_cap_portfolio_backtest


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
    assert trade["position_notional"] == 20_000.0
    assert trade["pnl"] == 4_000.0
    assert result.summary["ending_cash"] == 104_000.0
    assert result.summary["total_trades"] == 1


def test_portfolio_backtester_rejects_candidate_when_cash_is_locked() -> None:
    frames = {
        "AAA": _frame([10.0, 10.0, 11.0, 12.0]),
        "BBB": _frame([10.0, 10.0, 11.0, 12.0]),
    }
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01", score=100.0), _candidate("BBB", "2024-01-01", score=90.0)])

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config(initial_cash=15_000.0))

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
    assert result.equity_curve.iloc[0]["cash"] == 80_000.0
    assert result.equity_curve.iloc[-1]["equity"] == 104_000.0


def test_portfolio_backtester_preserves_scanner_score_in_trade_log() -> None:
    frames = {"AAA": _frame([10.0, 10.0, 11.0, 12.0, 13.0])}
    candidates = pd.DataFrame([_candidate("AAA", "2024-01-01", score=87.5)])

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config())

    assert result.trade_log.iloc[0]["small_cap_scanner_score"] == 87.5


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

    result = run_small_cap_portfolio_backtest(candidates, frames, config=_config(initial_cash=15_000.0))

    assert result.trade_log.iloc[0]["small_cap_setup"] == "panic_reversal"
    assert result.rejections.iloc[0]["small_cap_setup"] == "post_gap_drift"
