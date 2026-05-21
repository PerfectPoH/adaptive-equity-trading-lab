from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments.gaprev_event_selection_probe_runner import select_gaprev_candidate


def test_select_gaprev_candidate_uses_blind_daily_rules_and_excludes_known_false_case(tmp_path: Path) -> None:
    source = tmp_path / "prices.csv"
    rows = []
    for i in range(20):
        rows.append(_row("CRMD", f"2025-04-{i + 1:02d}", 10.0, 10.0, 1000))
        rows.append(_row("AEHR", f"2025-04-{i + 1:02d}", 20.0, 20.0, 1000))
    rows.append(_row("CRMD", "2025-05-05", 9.0, 9.04, 1000))
    rows.append(_row("CRMD", "2025-05-06", 7.0, 8.0, 6000))
    rows.append(_row("AEHR", "2025-05-05", 35.0, 35.23, 1000))
    rows.append(_row("AEHR", "2025-05-06", 33.0, 34.0, 5000))
    pd.DataFrame(rows).to_csv(source, index=False)

    candidate = select_gaprev_candidate(source)

    assert candidate["symbol"] == "AEHR"
    assert candidate["event_date"] == "2025-05-06"
    assert candidate["daily_gap"] <= -0.05
    assert candidate["daily_relative_volume"] >= 2.0
    assert "exclude CRMD 2025-05-06" in candidate["selection_rule"]


def _row(symbol: str, day: str, open_: float, close: float, volume: int) -> dict[str, object]:
    return {
        "symbol": symbol,
        "date": day,
        "open": open_,
        "high": max(open_, close),
        "low": min(open_, close),
        "close": close,
        "volume": volume,
        "provider_dataset": "XNAS.ITCH",
    }
