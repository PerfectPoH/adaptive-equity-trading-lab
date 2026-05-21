from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments.gaprev_mini_panel_probe_runner import select_gaprev_mini_panel_candidates


def test_select_gaprev_mini_panel_candidates_are_ranked_and_blind(tmp_path: Path) -> None:
    source = tmp_path / "prices.csv"
    rows = []
    for symbol in ["AAA", "BBB", "CCC", "CRMD"]:
        for i in range(20):
            rows.append(_row(symbol, f"2025-04-{i + 1:02d}", 10.0, 10.0, 1000))
        rows.append(_row(symbol, "2025-05-05", 10.0, 10.0, 1000))
    rows.append(_row("CRMD", "2025-05-06", 7.0, 8.0, 9000))
    rows.append(_row("AAA", "2025-05-06", 9.0, 9.5, 5000))
    rows.append(_row("BBB", "2025-05-06", 9.2, 9.5, 4000))
    rows.append(_row("CCC", "2025-05-06", 9.3, 9.5, 3000))
    pd.DataFrame(rows).to_csv(source, index=False)

    candidates = select_gaprev_mini_panel_candidates(source, panel_size=2)

    assert [candidate["symbol"] for candidate in candidates] == ["AAA", "BBB"]
    assert all(candidate["daily_gap"] <= -0.05 for candidate in candidates)
    assert all(candidate["daily_relative_volume"] >= 2.0 for candidate in candidates)


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
