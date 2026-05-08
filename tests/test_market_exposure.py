from __future__ import annotations

import pandas as pd

from src.risk.market_exposure import MarketExposureConfig, add_market_exposure_columns


def test_add_market_exposure_columns_increases_risk_only_in_strong_market() -> None:
    frame = pd.DataFrame(
        {
            "spy_trend_positive": [True, True, False],
            "spy_ema_50_ratio": [0.03, 0.01, 0.04],
            "spy_return_5d": [0.02, 0.02, 0.02],
        }
    )
    config = MarketExposureConfig(
        name="strong_2pct",
        base_risk_fraction=0.01,
        strong_market_risk_fraction=0.02,
        strong_spy_ema_50_ratio=0.02,
    )

    result = add_market_exposure_columns(frame, config)

    assert result["market_regime_strong"].tolist() == [True, False, False]
    assert result["risk_fraction"].tolist() == [0.02, 0.01, 0.01]
    assert result["risk_fraction_reason"].tolist() == ["strong_market", "base", "base"]


def test_add_market_exposure_columns_can_reduce_weak_market_risk() -> None:
    frame = pd.DataFrame(
        {
            "spy_trend_positive": [True, False],
            "spy_ema_50_ratio": [0.03, -0.01],
            "spy_return_5d": [0.01, -0.01],
        }
    )
    config = MarketExposureConfig(
        name="weak_half",
        base_risk_fraction=0.01,
        weak_market_risk_fraction=0.005,
    )

    result = add_market_exposure_columns(frame, config)

    assert result["risk_fraction"].tolist() == [0.01, 0.005]
    assert result["risk_fraction_reason"].tolist() == ["base", "weak_market"]
