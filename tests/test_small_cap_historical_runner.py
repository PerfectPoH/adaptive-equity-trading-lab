from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis.small_cap_benchmarks import SmallCapBenchmarkConfig
from src.backtest.small_cap_portfolio_backtester import SmallCapPortfolioBacktestConfig
from src.experiments.small_cap_historical_runner import SmallCapHistoricalRunConfig, run_small_cap_historical_report


def _candidate_metadata() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "market_cap": 500_000_000,
                "price": 10.6,
                "avg_volume_20d": 900_000,
                "avg_dollar_volume_20d": 8_000_000,
                "is_etf": False,
            },
            {
                "symbol": "BBB",
                "market_cap": 800_000_000,
                "price": 20.0,
                "avg_volume_20d": 900_000,
                "avg_dollar_volume_20d": 8_000_000,
                "is_etf": False,
            },
        ]
    )


def _frames() -> dict[str, pd.DataFrame]:
    index = pd.bdate_range("2024-01-01", periods=5)
    base = pd.DataFrame(
        {
            "Open": [10.0, 10.1, 10.2, 10.3, 10.4],
            "High": [10.2, 10.6, 11.2, 11.4, 11.5],
            "Low": [9.8, 10.0, 10.1, 10.2, 10.3],
            "Close": [10.0, 10.5, 11.1, 11.3, 11.4],
            "Volume": [800_000, 900_000, 1_000_000, 950_000, 940_000],
            "atr": [0.5, 0.5, 0.5, 0.5, 0.5],
            "atr_pct": [0.05, 0.05, 0.05, 0.05, 0.05],
            "relative_volume_20d": [1.2, 2.0, 2.0, 2.0, 1.6],
            "distance_from_20d_high": [-0.05, 0.0, 0.0, 0.0, -0.03],
            "rolling_volatility_20d": [0.03, 0.03, 0.03, 0.03, 0.03],
            "iwm_close": [210.0, 210.0, 210.0, 210.0, 210.0],
            "iwm_ema_50": [200.0, 200.0, 200.0, 200.0, 200.0],
            "vix_close": [18.0, 18.0, 18.0, 18.0, 18.0],
        },
        index=index,
    )
    second = base.copy()
    second["Close"] = [20.0, 19.8, 19.6, 19.4, 19.2]
    return {"AAA": base, "BBB": second}


def _iwm() -> pd.DataFrame:
    return pd.DataFrame({"Close": [100.0, 101.0, 102.0, 103.0, 104.0]}, index=pd.bdate_range("2024-01-01", periods=5))


def test_small_cap_historical_runner_writes_expected_artifacts(tmp_path: Path) -> None:
    result = run_small_cap_historical_report(
        _candidate_metadata(),
        _frames(),
        output_dir=tmp_path,
        iwm_frame=_iwm(),
        config=SmallCapHistoricalRunConfig(
            start="2024-01-02",
            end="2024-01-03",
            benchmark=SmallCapBenchmarkConfig(holding_period_bars=1, random_seed=3),
            portfolio=SmallCapPortfolioBacktestConfig(holding_period_bars=1),
        ),
    )

    assert result["paths"]["candidate_export"].exists()
    assert result["paths"]["benchmark_report"].exists()
    assert result["paths"]["backtest_report"].exists()
    assert result["paths"]["portfolio_trade_log"].exists()
    assert result["paths"]["portfolio_equity_curve"].exists()
    assert result["paths"]["portfolio_rejections"].exists()
    assert result["paths"]["portfolio_summary"].exists()
    assert "portfolio_backtest" in result
    assert "portfolio_summary" in result["backtest_report"]
    assert "## Portfolio Backtest" in result["paths"]["backtest_report"].read_text(encoding="utf-8")
    assert result["candidate_export"]["as_of"].tolist() == ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"]
    assert set(result["benchmark_report"]["benchmark"]) == {
        "cash_flat",
        "iwm_proxy",
        "equal_weight_universe",
        "random_entry_baseline",
        "ticker_holding_window",
    }
    assert "verdict" in result["backtest_report"]


def test_small_cap_historical_runner_honors_explicit_as_of_dates(tmp_path: Path) -> None:
    result = run_small_cap_historical_report(
        _candidate_metadata(),
        _frames(),
        output_dir=tmp_path,
        iwm_frame=_iwm(),
        as_of_dates=["2024-01-03"],
        config=SmallCapHistoricalRunConfig(benchmark=SmallCapBenchmarkConfig(holding_period_bars=1)),
    )

    assert result["candidate_export"]["as_of"].unique().tolist() == ["2024-01-03"]
    loaded = pd.read_csv(tmp_path / "candidate_export.csv")
    assert loaded["as_of"].unique().tolist() == ["2024-01-03"]


def test_small_cap_historical_runner_includes_metadata_diagnostics_in_report(tmp_path: Path) -> None:
    metadata_diagnostics = pd.DataFrame([{"symbol": "BLDE", "status": "fail", "reason": "missing_market_cap"}])

    result = run_small_cap_historical_report(
        _candidate_metadata(),
        _frames(),
        output_dir=tmp_path,
        iwm_frame=_iwm(),
        as_of_dates=["2024-01-03"],
        metadata_diagnostics=metadata_diagnostics,
        config=SmallCapHistoricalRunConfig(benchmark=SmallCapBenchmarkConfig(holding_period_bars=1)),
    )

    content = (tmp_path / "small_cap_backtest_report.md").read_text(encoding="utf-8")
    assert result["backtest_report"]["metadata_diagnostic_reasons"] == {"missing_market_cap": 1}
    assert "missing_market_cap" in content


def test_small_cap_historical_runner_fails_when_no_dates_available(tmp_path: Path) -> None:
    try:
        run_small_cap_historical_report(
            _candidate_metadata(),
            _frames(),
            output_dir=tmp_path,
            start="2030-01-01",
            end="2030-01-31",
        )
    except ValueError as exc:
        assert "No historical as_of dates" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
