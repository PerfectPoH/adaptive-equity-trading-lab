from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MarketExposureConfig:
    name: str
    base_risk_fraction: float = 0.01
    strong_market_risk_fraction: float | None = None
    weak_market_risk_fraction: float | None = None
    strong_spy_ema_50_ratio: float = 0.02
    strong_spy_return_5d: float = 0.0


DEFAULT_MARKET_EXPOSURE_CONFIG = MarketExposureConfig(name="default_1pct")


def add_market_exposure_columns(
    frame: pd.DataFrame,
    config: MarketExposureConfig = DEFAULT_MARKET_EXPOSURE_CONFIG,
) -> pd.DataFrame:
    data = frame.copy()
    _validate_risk_fraction(config.base_risk_fraction, "base_risk_fraction")
    if config.strong_market_risk_fraction is not None:
        _validate_risk_fraction(config.strong_market_risk_fraction, "strong_market_risk_fraction")
    if config.weak_market_risk_fraction is not None:
        _validate_risk_fraction(config.weak_market_risk_fraction, "weak_market_risk_fraction")

    strong_market = _strong_market_mask(data, config)
    weak_market = ~strong_market
    data["market_exposure_config"] = config.name
    data["market_regime_strong"] = strong_market
    data["risk_fraction"] = float(config.base_risk_fraction)
    data["risk_fraction_reason"] = "base"

    if config.strong_market_risk_fraction is not None:
        data.loc[strong_market, "risk_fraction"] = float(config.strong_market_risk_fraction)
        data.loc[strong_market, "risk_fraction_reason"] = "strong_market"
    if config.weak_market_risk_fraction is not None:
        data.loc[weak_market, "risk_fraction"] = float(config.weak_market_risk_fraction)
        data.loc[weak_market, "risk_fraction_reason"] = "weak_market"

    return data


def _strong_market_mask(frame: pd.DataFrame, config: MarketExposureConfig) -> pd.Series:
    trend = frame.get("spy_trend_positive", False)
    if isinstance(trend, pd.Series):
        trend_pass = trend.fillna(False).astype(bool)
    else:
        trend_pass = pd.Series(bool(trend), index=frame.index)

    ema_ratio = _numeric(frame, "spy_ema_50_ratio")
    spy_return = _numeric(frame, "spy_return_5d")
    return (
        trend_pass
        & (ema_ratio >= config.strong_spy_ema_50_ratio)
        & (spy_return >= config.strong_spy_return_5d)
    )


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(float("nan"), index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce")


def _validate_risk_fraction(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    if value > 0.05:
        raise ValueError(f"{name} is too high for this research MVP: {value}")
