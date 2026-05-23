from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import src.experiments.sec8k_predrift_existing_daily_diagnostic as diag
from src.experiments.sec8k_predrift_existing_daily_diagnostic import (
    build_predrift_panel,
    run_sec8k_predrift_existing_daily_diagnostic,
    summarize_predrift_panel,
    validate_sec8k_predrift_existing_daily_diagnostic,
)


def test_build_predrift_panel_uses_only_pre_event_daily_bars() -> None:
    events = pd.DataFrame([{"symbol": "AAA", "reaction_session_date": "2026-01-10", "status": "event"}])
    prices = _prices("AAA", days=12)

    rows = build_predrift_panel(events, prices, pre_window_days=3, baseline_lookback_days=5)
    event_rows = [row for row in rows if row["is_sec8k_event"] is True]

    assert len(event_rows) == 1
    assert event_rows[0]["event_date"] == "2026-01-10"
    assert event_rows[0]["pre_window_start"] == "2026-01-07"
    assert event_rows[0]["pre_window_end"] == "2026-01-09"
    assert "post_event_return" not in event_rows[0]
    assert event_rows[0]["provider_query_performed"] is False


def test_summary_archives_when_directional_lift_is_not_positive() -> None:
    rows = [
        {"is_sec8k_event": True, "pre_window_return": -0.02, "pre_window_abs_return": 0.02, "pre_window_volume_ratio": 2.0},
        {"is_sec8k_event": False, "pre_window_return": 0.01, "pre_window_abs_return": 0.01, "pre_window_volume_ratio": 1.0},
    ]

    summary = summarize_predrift_panel(rows, min_event_count=1)

    assert summary["decision"] == "SEC8K_PREDRIFT_ARCHIVE_CURRENT_FORM"
    assert "event_signed_predrift_not_above_control" in summary["blockers"]
    assert summary["provider_query_performed"] is False


def test_existing_daily_diagnostic_run_writes_non_promotable_artifacts(tmp_path: Path, monkeypatch) -> None:
    events = tmp_path / "events.csv"
    prices = tmp_path / "prices.csv"
    pd.DataFrame([{"symbol": "AAA", "reaction_session_date": "2026-01-28", "status": "event"}]).to_csv(events, index=False)
    _prices("AAA", days=32).to_csv(prices, index=False)

    decision = run_sec8k_predrift_existing_daily_diagnostic(
        event_panel_path=events,
        price_file=prices,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
        min_event_count=1,
    )
    report = validate_sec8k_predrift_existing_daily_diagnostic(tmp_path / "out")
    summary = json.loads((tmp_path / "out" / "diagnostic_summary.json").read_text(encoding="utf-8"))

    assert report["status"] == "pass"
    assert decision["promotion_allowed"] is False
    assert summary["provider_query_performed"] is False
    assert summary["market_data_downloaded"] is False


def _prices(symbol: str, days: int) -> pd.DataFrame:
    rows = []
    for index in range(days):
        date = pd.Timestamp("2026-01-01") + pd.Timedelta(days=index)
        close = 10.0 + index * 0.1
        rows.append(
            {
                "symbol": symbol,
                "date": date.date().isoformat(),
                "open": close - 0.05,
                "high": close + 0.1,
                "low": close - 0.1,
                "close": close,
                "volume": 1000 + index * 50,
                "provider_dataset": "UNIT.TEST",
            }
        )
    return pd.DataFrame(rows)
