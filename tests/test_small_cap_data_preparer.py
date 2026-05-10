from __future__ import annotations

import pandas as pd

from src.data.small_cap_data_preparer import SmallCapPreparedData, prepare_small_cap_historical_data


def _ohlcv(start: float = 10.0) -> pd.DataFrame:
    index = pd.bdate_range("2024-01-01", periods=30)
    close = pd.Series([start + i * 0.1 for i in range(30)], index=index)
    return pd.DataFrame(
        {
            "Open": close - 0.05,
            "High": close + 0.4,
            "Low": close - 0.4,
            "Close": close,
            "Volume": [700_000 + i * 10_000 for i in range(30)],
        },
        index=index,
    )


def _iwm() -> pd.DataFrame:
    frame = _ohlcv(200.0)
    frame["Close"] = [200.0 + i for i in range(30)]
    return frame


def _vix() -> pd.DataFrame:
    return pd.DataFrame({"Close": [18.0] * 30}, index=pd.bdate_range("2024-01-01", periods=30))


def _static_metadata() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "market_cap": 500_000_000, "is_etf": False},
            {"symbol": "BBB", "market_cap": 900_000_000, "is_etf": False},
            {"symbol": "MISSING", "market_cap": 900_000_000, "is_etf": False},
        ]
    )


def test_prepare_small_cap_historical_data_builds_metadata_and_featured_frames() -> None:
    prepared = prepare_small_cap_historical_data(
        {"AAA": _ohlcv(10.0), "BBB": _ohlcv(20.0)},
        iwm_frame=_iwm(),
        vix_frame=_vix(),
        static_metadata=_static_metadata(),
    )

    assert isinstance(prepared, SmallCapPreparedData)
    assert prepared.candidate_metadata["symbol"].tolist() == ["AAA", "BBB"]
    assert set(["market_cap", "price", "avg_volume_20d", "avg_dollar_volume_20d", "is_etf"]).issubset(
        prepared.candidate_metadata.columns
    )
    assert prepared.candidate_metadata.loc[prepared.candidate_metadata["symbol"] == "AAA", "price"].iat[0] == 12.9
    assert prepared.iwm_frame.equals(_iwm())

    aaa = prepared.frames["AAA"]
    for column in (
        "atr",
        "atr_pct",
        "relative_volume_20d",
        "distance_from_20d_high",
        "rolling_volatility_20d",
        "avg_dollar_volume_20d",
        "iwm_close",
        "iwm_ema_50",
        "vix_close",
    ):
        assert column in aaa.columns
    assert aaa["avg_dollar_volume_20d"].notna().any()
    assert aaa["iwm_close"].iloc[-1] == 229.0
    assert aaa["vix_close"].iloc[-1] == 18.0


def test_prepare_small_cap_historical_data_records_missing_and_invalid_symbols() -> None:
    prepared = prepare_small_cap_historical_data(
        {"AAA": _ohlcv(10.0), "EMPTY": pd.DataFrame()},
        iwm_frame=_iwm(),
        vix_frame=None,
        static_metadata=_static_metadata(),
    )

    assert prepared.frames["AAA"]["vix_close"].isna().all()
    assert "EMPTY" not in prepared.frames
    assert "MISSING" in prepared.diagnostics["missing_frame_symbols"]
    assert "EMPTY" in prepared.diagnostics["empty_frame_symbols"]


def test_prepare_small_cap_historical_data_requires_static_metadata_columns() -> None:
    try:
        prepare_small_cap_historical_data(
            {"AAA": _ohlcv(10.0)},
            iwm_frame=_iwm(),
            static_metadata=pd.DataFrame([{"symbol": "AAA", "market_cap": 500_000_000}]),
        )
    except ValueError as exc:
        assert "static_metadata missing columns" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
