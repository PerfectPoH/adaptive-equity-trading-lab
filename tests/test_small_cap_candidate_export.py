from __future__ import annotations

import pandas as pd

from src.experiments.small_cap_candidate_export import build_small_cap_candidate_export, write_small_cap_candidate_export


def _candidate_metadata() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "GOOD",
                "market_cap": 500_000_000,
                "price": 10.6,
                "avg_volume_20d": 900_000,
                "avg_dollar_volume_20d": 8_000_000,
                "is_etf": False,
            },
            {
                "symbol": "BADETF",
                "market_cap": 500_000_000,
                "price": 10.6,
                "avg_volume_20d": 900_000,
                "avg_dollar_volume_20d": 8_000_000,
                "is_etf": True,
            },
        ]
    )


def _frames() -> dict[str, pd.DataFrame]:
    index = pd.bdate_range("2024-01-01", periods=4)
    good = pd.DataFrame(
        {
            "Open": [10.0, 10.1, 10.2, 10.3],
            "High": [10.2, 10.6, 11.2, 10.7],
            "Low": [9.8, 10.0, 10.1, 10.2],
            "Close": [10.0, 10.5, 11.1, 10.6],
            "Volume": [800_000, 900_000, 1_000_000, 950_000],
            "atr": [0.5, 0.5, 0.5, 0.5],
            "atr_pct": [0.05, 0.05, 0.05, 0.05],
            "relative_volume_20d": [1.2, 1.4, 2.0, 1.6],
            "distance_from_20d_high": [-0.05, -0.02, 0.0, -0.03],
            "rolling_volatility_20d": [0.03, 0.03, 0.03, 0.03],
            "iwm_close": [210.0, 210.0, 210.0, 210.0],
            "iwm_ema_50": [200.0, 200.0, 200.0, 200.0],
            "vix_close": [18.0, 18.0, 18.0, 18.0],
        },
        index=index,
    )
    bad = good.copy()
    return {"GOOD": good, "BADETF": bad}


def test_build_small_cap_candidate_export_returns_latest_operational_candidate() -> None:
    export = build_small_cap_candidate_export(_candidate_metadata(), _frames(), as_of="2024-01-03")

    assert export["symbol"].tolist() == ["GOOD"]
    assert export.iloc[0]["as_of"] == "2024-01-03"
    assert export.iloc[0]["small_cap_setup"] == "breakout_continuation"
    assert export.iloc[0]["small_cap_scanner_pass"] is True
    assert export.iloc[0]["market_regime_trade_allowed"] is True
    assert export.iloc[0]["small_cap_execution_valid"] is True
    assert export.iloc[0]["operational_candidate"] is True


def test_build_small_cap_candidate_export_can_include_diagnostics_for_rejected_symbols() -> None:
    export = build_small_cap_candidate_export(
        _candidate_metadata(),
        _frames(),
        as_of="2024-01-03",
        operational_only=False,
    )

    assert export["symbol"].tolist() == ["GOOD", "BADETF"]
    bad = export[export["symbol"] == "BADETF"].iloc[0]
    assert bad["operational_candidate"] is False
    assert bad["universe_rejection_reasons"] == "is_etf"


def test_build_small_cap_candidate_export_marks_missing_price_data() -> None:
    export = build_small_cap_candidate_export(
        pd.DataFrame(
            [
                {
                    "symbol": "MISSING",
                    "market_cap": 500_000_000,
                    "price": 10.0,
                    "avg_volume_20d": 900_000,
                    "avg_dollar_volume_20d": 8_000_000,
                    "is_etf": False,
                }
            ]
        ),
        {},
        operational_only=False,
    )

    assert export.iloc[0]["symbol"] == "MISSING"
    assert export.iloc[0]["operational_candidate"] is False
    assert export.iloc[0]["data_quality_status"] == "fail"
    assert export.iloc[0]["data_quality_errors"] == "missing_data"


def test_write_small_cap_candidate_export_writes_csv(tmp_path) -> None:
    export = build_small_cap_candidate_export(_candidate_metadata(), _frames(), as_of="2024-01-03")
    path = tmp_path / "candidates.csv"

    written = write_small_cap_candidate_export(export, path)

    loaded = pd.read_csv(written)
    assert written == path
    assert loaded["symbol"].tolist() == ["GOOD"]
