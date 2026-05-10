from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments import small_cap_experiment_cli
from src.experiments.small_cap_experiment_cli import main, run_small_cap_historical_experiment, run_small_cap_watchlist_experiment


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


def test_run_small_cap_watchlist_experiment_builds_metadata_then_runs(tmp_path: Path) -> None:
    downloaded: list[str] = []

    def metadata_provider(symbol: str) -> dict[str, object]:
        return {"market_cap": 500_000_000 if symbol == "AAA" else 900_000_000, "is_etf": False}

    def fake_downloader(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
        downloaded.append(symbol)
        if symbol == "IWM":
            return _ohlcv(200.0)
        if symbol == "^VIX":
            frame = _ohlcv(18.0)
            frame["Close"] = 18.0
            return frame
        return _ohlcv(10.0 if symbol == "AAA" else 20.0)

    result = run_small_cap_watchlist_experiment(
        symbols=["AAA", "BBB"],
        metadata_output_path=tmp_path / "metadata.csv",
        metadata_diagnostics_path=tmp_path / "metadata_diagnostics.csv",
        output_dir=tmp_path / "run",
        start="2024-01-01",
        end="2024-02-15",
        metadata_provider=metadata_provider,
        downloader=fake_downloader,
    )

    assert downloaded == ["AAA", "BBB", "IWM", "^VIX"]
    assert result["metadata_result"].metadata_path.exists()
    assert result["experiment_result"]["run_result"]["paths"]["backtest_report"].exists()
    assert pd.read_csv(tmp_path / "metadata.csv")["symbol"].tolist() == ["AAA", "BBB"]


def test_small_cap_experiment_cli_main_supports_one_shot_symbols(tmp_path: Path, monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_run(**kwargs):
        calls.update(kwargs)
        return {}

    monkeypatch.setattr(small_cap_experiment_cli, "run_small_cap_watchlist_experiment", fake_run)

    exit_code = main(
        [
            "--symbols",
            "AAA,BBB",
            "--metadata-output-path",
            str(tmp_path / "metadata.csv"),
            "--output-dir",
            str(tmp_path / "run"),
            "--start",
            "2024-01-01",
        ]
    )

    assert exit_code == 0
    assert calls["symbols"] == ["AAA", "BBB"]
    assert calls["metadata_output_path"] == str(tmp_path / "metadata.csv")
