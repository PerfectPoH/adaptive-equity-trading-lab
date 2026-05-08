from __future__ import annotations

import pandas as pd

from src.data.downloader import load_latest_snapshot
from src.data.snapshot import save_snapshot


def test_load_latest_snapshot_returns_valid_fallback(tmp_path) -> None:
    idx = pd.bdate_range("2024-01-01", periods=5)
    frame = pd.DataFrame(
        {
            "Open": [100, 101, 102, 103, 104],
            "High": [101, 102, 103, 104, 105],
            "Low": [99, 100, 101, 102, 103],
            "Close": [100, 101, 102, 103, 104],
            "Volume": [1_000_000] * 5,
        },
        index=idx,
    )
    save_snapshot("TEST", frame, snapshot_dir=tmp_path)

    loaded = load_latest_snapshot("TEST", snapshot_dir=tmp_path, min_bars=5)

    assert loaded is not None
    assert list(loaded.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert loaded.index.equals(idx)


def test_load_latest_snapshot_returns_none_when_missing(tmp_path) -> None:
    assert load_latest_snapshot("MISSING", snapshot_dir=tmp_path, min_bars=1) is None
