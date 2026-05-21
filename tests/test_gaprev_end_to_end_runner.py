from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments.gaprev_end_to_end_runner import (
    GapRevParameters,
    controlled_backtest_from_frame,
    validate_intraday_bars,
)


def test_validate_intraday_bars_accepts_clean_derived_contract(tmp_path: Path) -> None:
    path = tmp_path / "bars.csv"
    _sample_frame().to_csv(path, index=False)

    report = validate_intraday_bars(path)

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0


def test_validate_intraday_bars_rejects_raw_payload_retention(tmp_path: Path) -> None:
    path = tmp_path / "bars.csv"
    _sample_frame().to_csv(path, index=False)
    (tmp_path / "raw_payload.json").write_text("{}", encoding="utf-8")

    report = validate_intraday_bars(path)

    assert report["status"] == "fail"
    assert any(check["name"] == "raw_payload_absent" and check["status"] == "fail" for check in report["checks"])


def test_controlled_backtest_blocks_if_less_than_two_sessions() -> None:
    frame = _sample_frame().query("timestamp < '2025-05-06T13:30:00Z'")

    result = controlled_backtest_from_frame(frame, GapRevParameters())

    assert result["status"] == "blocked"
    assert result["reason"] == "insufficient_sessions"


def test_controlled_backtest_executes_gaprev_when_filters_and_vwap_reclaim_match() -> None:
    result = controlled_backtest_from_frame(_sample_frame(), GapRevParameters())

    assert result["status"] == "pass"
    assert result["trade_count"] == 1
    assert result["gap_return"] <= -0.05
    assert result["relative_opening_volume"] >= 2.0
    assert result["promotion_allowed"] is False
    assert "trade_count_below_30" in result["promotion_blockers"]


def test_controlled_backtest_no_trade_if_gap_too_small() -> None:
    frame = _sample_frame()
    second_open = frame.index[frame["timestamp"].eq("2025-05-06T13:30:00Z")][0]
    frame.loc[second_open, "open"] = 99.0
    frame.loc[second_open, "high"] = 99.5
    frame.loc[second_open, "low"] = 98.8
    frame.loc[second_open, "close"] = 99.2

    result = controlled_backtest_from_frame(frame, GapRevParameters())

    assert result["status"] == "pass"
    assert result["trade_count"] == 0
    assert result["reason"] == "setup_filter_not_met"


def _sample_frame() -> pd.DataFrame:
    rows = []
    # Previous session: quiet first 30 minutes and prior close at 100.
    for minute in range(30):
        rows.append(
            {
                "symbol": "TEST",
                "timestamp": f"2025-05-05T13:{30 + minute:02d}:00Z" if minute < 30 else "2025-05-05T14:00:00Z",
                "open": 100.0,
                "high": 100.5,
                "low": 99.5,
                "close": 100.0,
                "volume": 100,
                "provider_dataset": "UNIT.TEST",
                "schema": "ohlcv-1m",
            }
        )
    rows.append(
        {
            "symbol": "TEST",
            "timestamp": "2025-05-05T19:59:00Z",
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.0,
            "volume": 100,
            "provider_dataset": "UNIT.TEST",
            "schema": "ohlcv-1m",
        }
    )
    # Reaction session: -10% gap, high opening volume, reclaim before 10:30 NY, exit after 120 minutes.
    for minute in range(121):
        hour = 13 + (30 + minute) // 60
        mins = (30 + minute) % 60
        close = 90.0 if minute < 5 else 92.0 + minute * 0.02
        rows.append(
            {
                "symbol": "TEST",
                "timestamp": f"2025-05-06T{hour:02d}:{mins:02d}:00Z",
                "open": 90.0 if minute == 0 else close - 0.05,
                "high": close + 0.1,
                "low": close - 0.2,
                "close": close,
                "volume": 500,
                "provider_dataset": "UNIT.TEST",
                "schema": "ohlcv-1m",
            }
        )
    return pd.DataFrame(rows)
