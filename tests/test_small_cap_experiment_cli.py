from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments import small_cap_experiment_cli
from src.experiments.small_cap_trial_accounting import build_nctrl_trial_001_accounting, build_rankex_trial_001_accounting
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


def test_build_rankex_trial_001_accounting_payload_matches_preregistration() -> None:
    payload = build_rankex_trial_001_accounting()

    assert payload["trial_id"] == "TRIAL-RANKEX-001"
    assert payload["research_question"] == "ranking_intra_candidate"
    assert payload["hypothesis_family"] == "ranking"
    assert payload["status"] == "implementation_ready_not_run"
    assert payload["train_or_design_window"] == "2022-01-03..2023-12-29"
    assert payload["validation_window"] == "2024-01-02..2024-12-31"
    assert payload["oos_window"] == "2025-01-02..2025-12-29"
    assert payload["candidate_run_id"] is None
    assert payload["ranking_policy"] == {
        "rank_column": "small_cap_scanner_score",
        "ascending": False,
        "tie_breakers": [
            {"column": "relative_volume_20d", "ascending": False},
            {"column": "open_to_close_return", "ascending": False},
            {"column": "symbol", "ascending": True},
        ],
    }


def test_build_nctrl_trial_001_accounting_payload_matches_preregistration() -> None:
    payload = build_nctrl_trial_001_accounting()

    assert payload["trial_id"] == "TRIAL-NCTRL-001"
    assert payload["research_question"] == "property_based_negative_control"
    assert payload["hypothesis_family"] == "negative_control"
    assert payload["status"] == "implementation_ready_not_run"
    assert payload["validation_window"] == "2024-01-02..2024-12-31"
    assert payload["universe"] == ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL", "SPY", "QQQ"]
    assert payload["sample_size_stop_rule"] == "closed_trades < 30 => insufficient_evidence"
    assert payload["bootstrap_random_baseline"]["simulations"] == 1000
    assert payload["bootstrap_random_baseline"]["base_seed"] == 700
    assert payload["random_entry_simulator"]["seed"] == 701
    assert payload["execution_gate"] == "do_not_execute_until_property_check_infrastructure_complete"
    assert payload["candidate_run_id"] is None


def test_run_small_cap_historical_experiment_forwards_trial_accounting(tmp_path: Path) -> None:
    def fake_downloader(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
        return _ohlcv(200.0 if symbol == "IWM" else 10.0)

    trial_accounting = build_rankex_trial_001_accounting()

    result = run_small_cap_historical_experiment(
        metadata_path=_metadata_path(tmp_path),
        output_dir=tmp_path / "run",
        start="2024-01-01",
        end="2024-02-15",
        vix_symbol=None,
        downloader=fake_downloader,
        trial_accounting=trial_accounting,
    )

    assert result["run_result"]["run_manifest"]["trial_accounting"]["trial_id"] == "TRIAL-RANKEX-001"
    assert result["run_result"]["run_manifest"]["trial_accounting"]["candidate_run_id"] is None


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


def test_run_small_cap_watchlist_experiment_forwards_metadata_diagnostics(tmp_path: Path) -> None:
    def metadata_provider(symbol: str) -> dict[str, object]:
        if symbol == "BAD":
            return {"market_cap": None, "is_etf": False}
        return {"market_cap": 500_000_000, "is_etf": False}

    def fake_downloader(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
        if symbol == "IWM":
            return _ohlcv(200.0)
        if symbol == "^VIX":
            frame = _ohlcv(18.0)
            frame["Close"] = 18.0
            return frame
        return _ohlcv(10.0)

    result = run_small_cap_watchlist_experiment(
        symbols=["AAA", "BAD"],
        metadata_output_path=tmp_path / "metadata.csv",
        metadata_diagnostics_path=tmp_path / "metadata_diagnostics.csv",
        output_dir=tmp_path / "run",
        start="2024-01-01",
        end="2024-02-15",
        metadata_provider=metadata_provider,
        downloader=fake_downloader,
    )

    report = result["experiment_result"]["run_result"]["backtest_report"]
    assert report["metadata_diagnostic_reasons"] == {"missing_market_cap": 1}
    assert "missing_market_cap" in (tmp_path / "run" / "small_cap_backtest_report.md").read_text(encoding="utf-8")


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


def test_small_cap_experiment_cli_main_passes_rankex_trial_accounting(tmp_path: Path, monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_run(**kwargs):
        calls.update(kwargs)
        return {}

    monkeypatch.setattr(small_cap_experiment_cli, "run_small_cap_historical_experiment", fake_run)

    exit_code = main(
        [
            "--metadata-path",
            str(tmp_path / "metadata.csv"),
            "--output-dir",
            str(tmp_path / "run"),
            "--start",
            "2024-01-01",
            "--trial-id",
            "TRIAL-RANKEX-001",
        ]
    )

    assert exit_code == 0
    assert calls["trial_accounting"]["trial_id"] == "TRIAL-RANKEX-001"
    assert calls["trial_accounting"]["candidate_run_id"] is None


def test_small_cap_experiment_cli_main_passes_nctrl_trial_accounting(tmp_path: Path, monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_run(**kwargs):
        calls.update(kwargs)
        return {}

    monkeypatch.setattr(small_cap_experiment_cli, "run_small_cap_historical_experiment", fake_run)

    exit_code = main(
        [
            "--metadata-path",
            str(tmp_path / "metadata.csv"),
            "--output-dir",
            str(tmp_path / "run"),
            "--start",
            "2024-01-01",
            "--trial-id",
            "TRIAL-NCTRL-001",
        ]
    )

    assert exit_code == 0
    assert calls["trial_accounting"]["trial_id"] == "TRIAL-NCTRL-001"
    assert calls["trial_accounting"]["candidate_run_id"] is None
