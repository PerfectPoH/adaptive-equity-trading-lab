from __future__ import annotations

import pandas as pd

from src.data.small_cap_data_quality import SmallCapDataQualityConfig, build_small_cap_data_quality_report


def _ohlcv(close: list[float], volume: list[int], start: str = "2024-01-01") -> pd.DataFrame:
    index = pd.bdate_range(start, periods=len(close))
    return pd.DataFrame(
        {
            "Open": close,
            "High": [value * 1.01 for value in close],
            "Low": [value * 0.99 for value in close],
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def test_build_small_cap_data_quality_report_passes_clean_frames() -> None:
    frames = {"GOOD": _ohlcv([10.0, 10.2, 10.1, 10.3, 10.4], [100_000] * 5)}
    config = SmallCapDataQualityConfig(min_bars=5)

    report = build_small_cap_data_quality_report(["GOOD"], frames, config=config)

    assert report.iloc[0]["symbol"] == "GOOD"
    assert report.iloc[0]["status"] == "pass"
    assert report.iloc[0]["bars"] == 5
    assert report.iloc[0]["errors"] == ""


def test_build_small_cap_data_quality_report_flags_missing_data() -> None:
    report = build_small_cap_data_quality_report(["MISSING"], {}, config=SmallCapDataQualityConfig(min_bars=5))

    assert report.iloc[0]["symbol"] == "MISSING"
    assert report.iloc[0]["status"] == "fail"
    assert report.iloc[0]["errors"] == "missing_data"


def test_build_small_cap_data_quality_report_flags_dirty_small_cap_proxies() -> None:
    frame = _ohlcv([10.0, 10.2, 2.0, 2.1, 2.2], [100_000, 0, 0, 0, 100_000])
    config = SmallCapDataQualityConfig(
        min_bars=5,
        max_zero_volume_fraction=0.2,
        max_abs_daily_return=0.5,
    )

    report = build_small_cap_data_quality_report(["DIRTY"], {"DIRTY": frame}, config=config)

    warnings = report.iloc[0]["warnings"]
    assert report.iloc[0]["status"] == "warn"
    assert "high_zero_volume_fraction" in warnings
    assert "extreme_price_jump" in warnings


def test_build_small_cap_data_quality_report_fails_validation_errors() -> None:
    frame = pd.DataFrame(
        {
            "Open": [10.0, 10.1],
            "High": [10.2, 10.3],
            "Low": [9.8, 9.9],
            "Close": [10.0, 10.1],
        },
        index=pd.bdate_range("2024-01-01", periods=2),
    )

    report = build_small_cap_data_quality_report(["BAD"], {"BAD": frame}, config=SmallCapDataQualityConfig(min_bars=2))

    assert report.iloc[0]["status"] == "fail"
    assert "Missing columns" in report.iloc[0]["errors"]
