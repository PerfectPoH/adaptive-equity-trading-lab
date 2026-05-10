from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments.small_cap_experiment_cli import run_small_cap_historical_experiment


def _ohlcv(start: float) -> pd.DataFrame:
    index = pd.bdate_range("2024-01-01", periods=30)
    close = pd.Series([start + i * 0.1 for i in range(30)], index=index)
    return pd.DataFrame(
        {
            "Open": close - 0.05,
            "High": close + 0.4,
            "Low": close - 0.4,
            "Close": close,
            "Volume": [800_000 + i * 10_000 for i in range(30)],
        },
        index=index,
    )


def _metadata_path(tmp_path: Path) -> Path:
    path = tmp_path / "metadata.csv"
    pd.DataFrame(
        [
            {"symbol": "AAA", "market_cap": 500_000_000, "is_etf": False},
            {"symbol": "BBB", "market_cap": 900_000_000, "is_etf": False},
        ]
    ).to_csv(path, index=False)
    return path


def test_run_small_cap_historical_experiment_downloads_prepares_and_writes_reports(tmp_path: Path) -> None:
    downloaded: list[tuple[str, str, str | None]] = []

    def fake_downloader(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
        downloaded.append((symbol, start, end))
        if symbol == "IWM":
            return _ohlcv(200.0)
        if symbol == "^VIX":
            frame = _ohlcv(18.0)
            frame["Close"] = 18.0
            return frame
        return _ohlcv(10.0 if symbol == "AAA" else 20.0)

    result = run_small_cap_historical_experiment(
        metadata_path=_metadata_path(tmp_path),
        output_dir=tmp_path / "run",
        start="2024-01-01",
        end="2024-02-15",
        downloader=fake_downloader,
    )

    assert [item[0] for item in downloaded] == ["AAA", "BBB", "IWM", "^VIX"]
    assert result["prepared_data"].candidate_metadata["symbol"].tolist() == ["AAA", "BBB"]
    assert result["run_result"]["paths"]["candidate_export"].exists()
    assert result["run_result"]["paths"]["benchmark_report"].exists()
    assert result["run_result"]["paths"]["backtest_report"].exists()


def test_run_small_cap_historical_experiment_allows_symbol_subset(tmp_path: Path) -> None:
    downloaded: list[str] = []

    def fake_downloader(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
        downloaded.append(symbol)
        return _ohlcv(200.0 if symbol == "IWM" else 10.0)

    result = run_small_cap_historical_experiment(
        metadata_path=_metadata_path(tmp_path),
        output_dir=tmp_path / "run",
        start="2024-01-01",
        end="2024-02-15",
        symbols=["BBB"],
        vix_symbol=None,
        downloader=fake_downloader,
    )

    assert downloaded == ["BBB", "IWM"]
    assert result["prepared_data"].candidate_metadata["symbol"].tolist() == ["BBB"]


def test_run_small_cap_historical_experiment_requires_metadata_file(tmp_path: Path) -> None:
    try:
        run_small_cap_historical_experiment(
            metadata_path=tmp_path / "missing.csv",
            output_dir=tmp_path / "run",
            start="2024-01-01",
            downloader=lambda symbol, start, end=None: _ohlcv(10.0),
        )
    except FileNotFoundError as exc:
        assert "metadata_path not found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")
