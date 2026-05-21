from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments.opening_reclaim_probe_runner import (
    OpeningReclaimParams,
    evaluate_opening_reclaim_event,
    summarize_opening_reclaim_results,
)


def test_opening_reclaim_event_executes_from_intraday_rth_without_daily_gap(tmp_path: Path) -> None:
    event_dir = tmp_path / "AAA_2025-01-02"
    event_dir.mkdir()
    _sample_bars().to_csv(event_dir / "bars.csv", index=False)

    result = evaluate_opening_reclaim_event(event_dir / "bars.csv", OpeningReclaimParams())

    assert result["status"] == "pass"
    assert result["trade_count"] == 1
    assert result["opening_shock"] <= -0.05
    assert result["relative_opening_volume"] >= 2.0


def test_opening_reclaim_summary_blocks_promotion_for_small_panel() -> None:
    results = pd.DataFrame(
        [
            {"trade_count": 1, "gross_return": 0.08, "net_return": 0.03},
            {"trade_count": 1, "gross_return": 0.01, "net_return": -0.04},
            {"trade_count": 0},
        ]
    )

    summary = summarize_opening_reclaim_results(results, OpeningReclaimParams())

    assert summary["trade_count"] == 2
    assert summary["promotion_allowed"] is False
    assert "below_30_trades" in summary["promotion_blockers"]


def _sample_bars() -> pd.DataFrame:
    rows = []
    for minute in range(30):
        rows.append(_bar("2025-01-01", minute, 100.0, 100.5, 99.5, 100.0, 100))
    rows.append(
        {
            "symbol": "AAA",
            "timestamp": "2025-01-01T20:59:00Z",
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.0,
            "volume": 100,
            "provider_dataset": "UNIT.TEST",
            "schema": "ohlcv-1m",
        }
    )
    for minute in range(150):
        close = 95.0 if minute < 5 else 96.0 + minute * 0.03
        low = 93.5 if minute == 2 else close - 0.2
        rows.append(_bar("2025-01-02", minute, 100.0 if minute == 0 else close - 0.05, close + 0.1, low, close, 500))
    return pd.DataFrame(rows)


def _bar(day: str, minute: int, open_: float, high: float, low: float, close: float, volume: int) -> dict[str, object]:
    hour = 14 + (30 + minute) // 60
    mins = (30 + minute) % 60
    return {
        "symbol": "AAA",
        "timestamp": f"{day}T{hour:02d}:{mins:02d}:00Z",
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "provider_dataset": "UNIT.TEST",
        "schema": "ohlcv-1m",
    }
