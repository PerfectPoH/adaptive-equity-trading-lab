from __future__ import annotations

import pandas as pd

from src.experiments.orb_930_cross_asset_backtest import (
    OrbConfig,
    backtest_orb_panel,
    backtest_orb_symbol_day,
    build_pre_run_gate,
    final_decision,
)


def _bar(ts: str, open_: float, high: float, low: float, close: float) -> dict[str, object]:
    return {
        "symbol": "BTC-USD",
        "timestamp": pd.Timestamp(ts, tz="America/New_York"),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000,
    }


def test_orb_gate_freezes_cross_asset_parameters() -> None:
    gate = build_pre_run_gate()

    assert gate["provider_query_allowed"] is True
    assert gate["symbols"]["GC=F"] == "Gold futures proxy"
    assert gate["parameter_freeze"]["opening_range_minutes"] == [5, 15]
    assert gate["parameter_freeze"]["reward_r_multiples"] == [1, 3, 4]
    assert gate["promotion_allowed"] is False


def test_orb_symbol_day_enters_breakout_and_takes_profit() -> None:
    bars = pd.DataFrame(
        [
            _bar("2026-05-01 09:30", 100, 101, 99, 100),
            _bar("2026-05-01 09:35", 100, 100.5, 99.5, 100),
            _bar("2026-05-01 09:40", 100, 100.4, 99.6, 100),
            _bar("2026-05-01 09:45", 100, 102, 100.5, 101.5),
            _bar("2026-05-01 09:50", 101.5, 105, 101.2, 104),
            _bar("2026-05-01 09:55", 104, 106, 103, 105),
        ]
    )

    trade = backtest_orb_symbol_day(bars, OrbConfig(range_minutes=15, reward_r=1))

    assert trade is not None
    assert trade["direction"] == "long"
    assert trade["or_high"] == 101
    assert trade["or_low"] == 99
    assert trade["exit_reason"] == "take_profit"
    assert trade["net_return"] > 0


def test_orb_symbol_day_skips_when_no_entry_before_11() -> None:
    bars = pd.DataFrame(
        [
            _bar("2026-05-01 09:30", 100, 101, 99, 100),
            _bar("2026-05-01 09:35", 100, 100.5, 99.5, 100),
            _bar("2026-05-01 09:45", 100, 100.5, 99.5, 100),
            _bar("2026-05-01 11:05", 100, 103, 100, 102),
        ]
    )

    assert backtest_orb_symbol_day(bars, OrbConfig(range_minutes=15, reward_r=1)) is None


def test_orb_panel_summarizes_parameter_grid_and_decision() -> None:
    rows = []
    for day in ["2026-05-01", "2026-05-02"]:
        rows.extend(
            [
                _bar(f"{day} 09:30", 100, 101, 99, 100),
                _bar(f"{day} 09:35", 100, 100.5, 99.5, 100),
                _bar(f"{day} 09:40", 100, 100.4, 99.6, 100),
                _bar(f"{day} 09:45", 100, 102, 100.5, 101.5),
                _bar(f"{day} 09:50", 101.5, 105, 101.2, 104),
                _bar(f"{day} 15:55", 104, 104.5, 103, 104),
            ]
        )
    panel = pd.DataFrame(rows)

    trades, summary = backtest_orb_panel(panel)
    decision = final_decision(summary, trades)

    assert not trades.empty
    assert {"range_minutes", "reward_r", "net_return_sum"}.issubset(summary.columns)
    assert decision["promotion_allowed"] is False
    assert decision["trade_count_total"] == len(trades)
