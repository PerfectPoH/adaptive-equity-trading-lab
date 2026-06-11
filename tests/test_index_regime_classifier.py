from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.risk.index_regime_classifier import (
    ALL_REGIMES,
    IndexRegimeConfig,
    apply_hysteresis,
    classify_index_regime,
    classify_index_regime_raw,
    compute_index_regime_features,
    validate_regime_predictiveness,
)


def _build_synthetic_prices(seed: int = 0, length: int = 1500) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-02", periods=length)
    # Compose three regimes: low-vol uptrend, drawdown, sideways.
    segment = length // 3
    drift = np.concatenate(
        [np.full(segment, 0.0006), np.full(segment, -0.0008), np.full(length - 2 * segment, 0.0001)]
    )
    sigma = np.concatenate(
        [np.full(segment, 0.005), np.full(segment, 0.020), np.full(length - 2 * segment, 0.008)]
    )
    log_returns = rng.normal(drift, sigma)
    price = 100.0 * np.exp(np.cumsum(log_returns))
    return pd.DataFrame({"Adj Close": price}, index=dates)


def test_features_have_expected_columns_and_lengths() -> None:
    prices = _build_synthetic_prices()
    features = compute_index_regime_features(prices)
    expected = {"close", "log_return", "sma_long", "sma_short", "realised_vol", "vol_percentile", "trend_strength", "range_distance"}
    assert expected.issubset(features.columns)
    assert len(features) == len(prices)


def test_raw_labels_only_use_known_regime_values() -> None:
    prices = _build_synthetic_prices()
    features = compute_index_regime_features(prices)
    raw = classify_index_regime_raw(features)
    defined = raw.dropna()
    assert defined.isin(ALL_REGIMES).all()


def test_hysteresis_prevents_short_lived_flips() -> None:
    raw = pd.Series(
        ["TREND_UP", "TREND_UP", "TREND_UP", "TREND_DOWN", "TREND_UP", "TREND_UP", "TREND_UP"]
    )
    smoothed = apply_hysteresis(raw, hysteresis_bars=3)
    # The single TREND_DOWN should not flip the published regime.
    assert smoothed.tolist() == ["TREND_UP"] * 7


def test_hysteresis_accepts_persistent_change() -> None:
    raw = pd.Series(
        ["TREND_UP"] * 4 + ["TREND_DOWN"] * 5 + ["TREND_UP"] * 2
    )
    smoothed = apply_hysteresis(raw, hysteresis_bars=3)
    # First 6 bars: still TREND_UP because TREND_DOWN only just reached 3 streak at index 6.
    # At index 6 (3rd consecutive TREND_DOWN), label flips.
    assert smoothed.iloc[0] == "TREND_UP"
    assert smoothed.iloc[5] == "TREND_UP"  # streak=2, still TREND_UP
    assert smoothed.iloc[6] == "TREND_DOWN"  # streak=3, flips
    assert smoothed.iloc[8] == "TREND_DOWN"


def test_classifier_end_to_end_assigns_meaningful_labels() -> None:
    prices = _build_synthetic_prices()
    classified = classify_index_regime(prices)
    labels = classified["regime"].dropna()
    counts = labels.value_counts()
    # At minimum TREND_UP and TREND_DOWN should appear.
    assert "TREND_UP" in counts.index
    assert "TREND_DOWN" in counts.index


def test_oos_validation_detects_real_regime_separation() -> None:
    prices = _build_synthetic_prices()
    classified = classify_index_regime(prices)
    result = validate_regime_predictiveness(classified, forward_horizon=10, train_fraction=0.6)
    # With three engineered regimes the ANOVA on forward vol should be very
    # significant in both train and test.
    assert result.train_f_vol > 5.0
    assert result.test_f_vol > 5.0
    assert result.forward_horizon == 10


def test_config_rejects_invalid_parameters() -> None:
    with pytest.raises(ValueError, match="long_trend_window"):
        IndexRegimeConfig(long_trend_window=50, short_trend_window=50)
    with pytest.raises(ValueError, match="percentiles"):
        IndexRegimeConfig(low_vol_percentile=0.9, high_vol_percentile=0.5)
    with pytest.raises(ValueError, match="hysteresis_bars"):
        IndexRegimeConfig(hysteresis_bars=0)
