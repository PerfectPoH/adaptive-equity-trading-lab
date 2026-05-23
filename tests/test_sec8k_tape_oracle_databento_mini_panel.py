from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments.sec8k_tape_oracle_databento_mini_panel import (
    build_approval,
    normalize_bars,
    select_event_cases,
    validate_case_bars,
)


def test_build_approval_keeps_scope_bounded_and_non_promotable() -> None:
    approval = build_approval(max_events=30, control_sessions=5, key_present=True)

    assert approval["max_provider_calls"] == 30
    assert approval["raw_payload_retention"] is False
    assert approval["parameter_sweep_allowed"] is False
    assert approval["promotion_allowed"] is False


def test_select_event_cases_requires_control_sessions(tmp_path: Path) -> None:
    events = tmp_path / "events.csv"
    prices = tmp_path / "prices.csv"
    pd.DataFrame([{"symbol": "AAA", "reaction_session_date": "2026-01-09", "status": "event"}]).to_csv(events, index=False)
    pd.DataFrame(
        [{"symbol": "AAA", "date": date} for date in ["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08", "2026-01-09"]]
    ).to_csv(prices, index=False)

    cases = select_event_cases(events, prices, max_events=1, control_sessions=5)

    assert len(cases) == 1
    assert cases[0]["control_dates"] == "2026-01-02|2026-01-05|2026-01-06|2026-01-07|2026-01-08"
    assert cases[0]["dataset"] == "XNAS.ITCH"


def test_validate_case_bars_requires_entry_and_flat_windows() -> None:
    bars = pd.DataFrame(
        [
            _bar("2026-01-09 09:30", 10.0),
            _bar("2026-01-09 09:44", 10.1),
            _bar("2026-01-09 09:46", 10.2),
            _bar("2026-01-09 15:55", 10.3),
        ]
    )

    report = validate_case_bars(bars, "2026-01-09")

    assert report["status"] == "pass"


def test_normalize_bars_maps_databento_like_frame() -> None:
    frame = pd.DataFrame(
        {
            "ts_event": [pd.Timestamp("2026-01-09T14:30:00Z")],
            "open": [10],
            "high": [11],
            "low": [9],
            "close": [10.5],
            "volume": [100],
        }
    )

    normalized = normalize_bars(frame, "AAA")

    assert list(normalized.columns) == ["symbol", "timestamp", "open", "high", "low", "close", "volume", "provider_dataset", "schema"]
    assert normalized.iloc[0]["symbol"] == "AAA"


def _bar(local_timestamp: str, price: float) -> dict[str, object]:
    return {
        "symbol": "AAA",
        "timestamp": pd.Timestamp(local_timestamp, tz="America/New_York").tz_convert("UTC").isoformat().replace("+00:00", "Z"),
        "open": price,
        "high": price,
        "low": price,
        "close": price,
        "volume": 100,
    }
