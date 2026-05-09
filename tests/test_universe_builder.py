from __future__ import annotations

import pandas as pd

from src.data.universe_builder import SmallCapUniverseConfig, build_small_cap_universe


def test_build_small_cap_universe_applies_hard_filters() -> None:
    candidates = pd.DataFrame(
        [
            {
                "symbol": "GOOD",
                "market_cap": 500_000_000,
                "price": 6.0,
                "avg_volume_20d": 700_000,
                "avg_dollar_volume_20d": 4_200_000,
                "is_etf": False,
            },
            {
                "symbol": "ETF1",
                "market_cap": 500_000_000,
                "price": 6.0,
                "avg_volume_20d": 700_000,
                "avg_dollar_volume_20d": 4_200_000,
                "is_etf": True,
            },
            {
                "symbol": "TINY",
                "market_cap": 50_000_000,
                "price": 6.0,
                "avg_volume_20d": 700_000,
                "avg_dollar_volume_20d": 4_200_000,
                "is_etf": False,
            },
            {
                "symbol": "LOWPX",
                "market_cap": 500_000_000,
                "price": 1.5,
                "avg_volume_20d": 700_000,
                "avg_dollar_volume_20d": 4_200_000,
                "is_etf": False,
            },
            {
                "symbol": "ILLQ",
                "market_cap": 500_000_000,
                "price": 6.0,
                "avg_volume_20d": 10_000,
                "avg_dollar_volume_20d": 60_000,
                "is_etf": False,
            },
        ]
    )

    universe = build_small_cap_universe(candidates)

    assert universe["symbol"].tolist() == ["GOOD"]
    assert universe.iloc[0]["passes_universe_filter"] is True


def test_build_small_cap_universe_records_rejection_reasons() -> None:
    candidates = pd.DataFrame(
        [
            {
                "symbol": "BAD",
                "market_cap": 20_000_000,
                "price": 0.8,
                "avg_volume_20d": 5_000,
                "avg_dollar_volume_20d": 4_000,
                "is_etf": True,
            }
        ]
    )

    diagnostics = build_small_cap_universe(candidates, passed_only=False)

    reasons = diagnostics.iloc[0]["rejection_reasons"]
    assert diagnostics.iloc[0]["passes_universe_filter"] is False
    assert "is_etf" in reasons
    assert "market_cap_below_min" in reasons
    assert "price_below_min" in reasons
    assert "volume_below_min" in reasons
    assert "dollar_volume_below_min" in reasons


def test_build_small_cap_universe_rejects_missing_required_fields() -> None:
    candidates = pd.DataFrame([{"symbol": "MISSING", "market_cap": 500_000_000}])

    diagnostics = build_small_cap_universe(candidates, passed_only=False)

    reasons = diagnostics.iloc[0]["rejection_reasons"]
    assert diagnostics.iloc[0]["passes_universe_filter"] is False
    assert "missing_price" in reasons
    assert "missing_avg_volume_20d" in reasons
    assert "missing_avg_dollar_volume_20d" in reasons
    assert "missing_is_etf" in reasons


def test_small_cap_universe_config_can_be_tightened() -> None:
    candidates = pd.DataFrame(
        [
            {
                "symbol": "MID",
                "market_cap": 2_000_000_000,
                "price": 10.0,
                "avg_volume_20d": 1_000_000,
                "avg_dollar_volume_20d": 10_000_000,
                "is_etf": False,
            }
        ]
    )
    config = SmallCapUniverseConfig(max_market_cap=1_000_000_000)

    diagnostics = build_small_cap_universe(candidates, config=config, passed_only=False)

    assert diagnostics.iloc[0]["passes_universe_filter"] is False
    assert diagnostics.iloc[0]["rejection_reasons"] == "market_cap_above_max"
