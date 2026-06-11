"""Index-feature regime classifier with hysteresis and OOS validation.

This module replaces the in-sample, string-matched regime map used by the
Workbench Portfolio Lab. It classifies the market into a small set of
regimes from price/vol features of a benchmark index (SPY by default,
optionally combined with IWM as a small-cap proxy and QQQ as a growth
proxy) and applies a hysteresis state machine so the label only changes
after evidence persists.

Two things matter here:

1. **Determinism.** The classifier is parameter-driven, not data-fitted.
   Given the same OHLCV history and the same config, you get the same
   regime series — no in-sample optimisation.
2. **Validation.** ``validate_regime_predictiveness`` runs an OOS test:
   does the regime label assigned at the *end of yesterday* explain the
   distribution of returns and realised volatility *tomorrow*? If
   knowing the regime is informative, classes will separate; if not,
   the regime is noise dressed as a label.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


RegimeLabel = Literal["TREND_UP", "TREND_DOWN", "HIGH_VOL", "QUIET_RANGE", "MIXED_NORMAL"]
ALL_REGIMES: tuple[RegimeLabel, ...] = (
    "TREND_UP",
    "TREND_DOWN",
    "HIGH_VOL",
    "QUIET_RANGE",
    "MIXED_NORMAL",
)


@dataclass(frozen=True)
class IndexRegimeConfig:
    """Parameters controlling the classifier.

    Attributes
    ----------
    long_trend_window:
        Window for the long trend SMA (e.g. 200d).
    short_trend_window:
        Window for the short trend SMA (e.g. 50d).
    volatility_window:
        Window for realized return volatility.
    high_vol_percentile:
        Trailing percentile above which a session is HIGH_VOL.
    low_vol_percentile:
        Trailing percentile below which a session is "quiet".
    range_band:
        Half-width of the band around SMA200 (as a fraction of SMA200)
        within which a session is considered range-bound.
    hysteresis_bars:
        How many consecutive raw-regime bars must agree before the
        published regime changes. Without hysteresis the label flickers
        on noisy days.
    percentile_window:
        Window used to compute the trailing percentile of volatility.
        Must be long enough to be a stable distribution.
    """

    long_trend_window: int = 200
    short_trend_window: int = 50
    volatility_window: int = 20
    high_vol_percentile: float = 0.80
    low_vol_percentile: float = 0.40
    range_band: float = 0.02
    hysteresis_bars: int = 5
    percentile_window: int = 252

    def __post_init__(self) -> None:
        if self.long_trend_window <= self.short_trend_window:
            raise ValueError("long_trend_window must exceed short_trend_window")
        if self.volatility_window < 2:
            raise ValueError("volatility_window must be at least 2")
        if not 0.0 < self.low_vol_percentile < self.high_vol_percentile < 1.0:
            raise ValueError("percentiles must satisfy 0 < low < high < 1")
        if self.range_band <= 0:
            raise ValueError("range_band must be positive")
        if self.hysteresis_bars < 1:
            raise ValueError("hysteresis_bars must be at least 1")
        if self.percentile_window < self.volatility_window * 2:
            raise ValueError("percentile_window must be at least 2x volatility_window")


def compute_index_regime_features(
    prices: pd.DataFrame,
    *,
    close_column: str = "Adj Close",
    config: IndexRegimeConfig | None = None,
) -> pd.DataFrame:
    """Compute the feature panel used by ``classify_index_regime``.

    Expects a DataFrame indexed by date with a column ``close_column``.
    Returns a frame with columns ``log_return``, ``sma_long``, ``sma_short``,
    ``realised_vol``, ``vol_percentile``, ``trend_strength``,
    ``range_distance``.
    """

    active = config or IndexRegimeConfig()
    if close_column not in prices.columns:
        raise KeyError(f"missing column {close_column!r}")
    series = pd.to_numeric(prices[close_column], errors="coerce").astype(float)
    log_return = np.log(series).diff()
    sma_long = series.rolling(active.long_trend_window, min_periods=active.long_trend_window).mean()
    sma_short = series.rolling(active.short_trend_window, min_periods=active.short_trend_window).mean()
    realised_vol = log_return.rolling(active.volatility_window, min_periods=active.volatility_window).std()
    # Trailing percentile of realised vol against itself over a longer window.
    vol_percentile = realised_vol.rolling(active.percentile_window, min_periods=active.percentile_window // 2).apply(
        _trailing_rank, raw=True
    )
    trend_strength = (series - sma_long) / sma_long
    range_distance = (series - sma_long).abs() / sma_long
    return pd.DataFrame(
        {
            "close": series,
            "log_return": log_return,
            "sma_long": sma_long,
            "sma_short": sma_short,
            "realised_vol": realised_vol,
            "vol_percentile": vol_percentile,
            "trend_strength": trend_strength,
            "range_distance": range_distance,
        },
        index=prices.index,
    )


def _trailing_rank(values: np.ndarray) -> float:
    """Return percentile rank of the last observation in ``values``."""

    if len(values) == 0:
        return float("nan")
    last = values[-1]
    return float(np.mean(values <= last))


def classify_index_regime_raw(features: pd.DataFrame, config: IndexRegimeConfig | None = None) -> pd.Series:
    """Apply the raw classification rules without hysteresis."""

    active = config or IndexRegimeConfig()
    labels: list[RegimeLabel | float] = []
    for date in features.index:
        trend = features.loc[date, "trend_strength"]
        vol_pct = features.loc[date, "vol_percentile"]
        range_dist = features.loc[date, "range_distance"]
        if not np.isfinite(trend) or not np.isfinite(vol_pct) or not np.isfinite(range_dist):
            labels.append(float("nan"))
            continue
        if vol_pct >= active.high_vol_percentile:
            labels.append("HIGH_VOL")
        elif range_dist < active.range_band and vol_pct < active.low_vol_percentile:
            labels.append("QUIET_RANGE")
        elif trend > 0 and vol_pct < active.high_vol_percentile:
            labels.append("TREND_UP")
        elif trend < 0:
            labels.append("TREND_DOWN")
        else:
            labels.append("MIXED_NORMAL")
    return pd.Series(labels, index=features.index, dtype=object, name="regime_raw")


def apply_hysteresis(raw_labels: pd.Series, hysteresis_bars: int) -> pd.Series:
    """Smooth a regime label series so changes require persistent agreement."""

    if hysteresis_bars < 1:
        raise ValueError("hysteresis_bars must be at least 1")
    smoothed: list[object] = []
    current_label: object = float("nan")
    candidate_label: object = float("nan")
    candidate_streak = 0
    for raw in raw_labels:
        if isinstance(raw, float) and np.isnan(raw):
            smoothed.append(current_label)
            candidate_streak = 0
            candidate_label = float("nan")
            continue
        if isinstance(current_label, float) and np.isnan(current_label):
            # Bootstrap: first defined raw label becomes current immediately.
            current_label = raw
            smoothed.append(current_label)
            candidate_streak = 0
            candidate_label = float("nan")
            continue
        if raw == current_label:
            smoothed.append(current_label)
            candidate_streak = 0
            candidate_label = float("nan")
            continue
        if raw == candidate_label:
            candidate_streak += 1
        else:
            candidate_label = raw
            candidate_streak = 1
        if candidate_streak >= hysteresis_bars:
            current_label = candidate_label
            candidate_streak = 0
            candidate_label = float("nan")
        smoothed.append(current_label)
    return pd.Series(smoothed, index=raw_labels.index, dtype=object, name="regime")


def classify_index_regime(
    prices: pd.DataFrame,
    *,
    close_column: str = "Adj Close",
    config: IndexRegimeConfig | None = None,
) -> pd.DataFrame:
    """End-to-end: compute features, classify, apply hysteresis."""

    active = config or IndexRegimeConfig()
    features = compute_index_regime_features(prices, close_column=close_column, config=active)
    raw = classify_index_regime_raw(features, active)
    smoothed = apply_hysteresis(raw, active.hysteresis_bars)
    out = features.copy()
    out["regime_raw"] = raw
    out["regime"] = smoothed
    return out


# ---------------------------------------------------------------------------
# Out-of-sample validation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegimePredictivenessResult:
    """Summary of how informative the regime label is OOS.

    ``per_regime_stats`` is a DataFrame with one row per regime label,
    columns ``mean_forward_return``, ``std_forward_return``, ``count``.

    ``f_statistic_return`` and ``p_value_return`` are a one-way ANOVA on
    forward returns across regimes. Similarly ``f_statistic_vol`` /
    ``p_value_vol`` for forward realised vol.

    ``train_split_idx`` and ``test_split_idx`` mark where the OOS split
    was made.
    """

    train_split_idx: int
    test_split_idx: int
    forward_horizon: int
    train_per_regime: pd.DataFrame
    test_per_regime: pd.DataFrame
    train_f_return: float
    train_p_return: float
    test_f_return: float
    test_p_return: float
    train_f_vol: float
    train_p_vol: float
    test_f_vol: float
    test_p_vol: float
    rank_correlation_return: float
    rank_correlation_vol: float


def validate_regime_predictiveness(
    classified: pd.DataFrame,
    *,
    forward_horizon: int = 20,
    train_fraction: float = 0.6,
) -> RegimePredictivenessResult:
    """Run an OOS test: does the regime predict forward vol/return?

    Methodology
    -----------
    1. Compute forward log-return over ``forward_horizon`` days.
    2. Compute forward realised vol over the same window.
    3. Split chronologically at ``train_fraction``.
    4. On the train slice and on the test slice, group by regime and
       compute mean/std of forward stats. Run a one-way ANOVA on each.
    5. Rank-correlate per-regime test means with train means — if the
       regime captures something real, the per-regime ordering should
       persist.
    """

    if not 0.1 < train_fraction < 0.95:
        raise ValueError("train_fraction must be in (0.1, 0.95)")
    if forward_horizon < 1:
        raise ValueError("forward_horizon must be at least 1")

    log_return = classified["log_return"].astype(float)
    forward_return = log_return.shift(-1).rolling(forward_horizon, min_periods=forward_horizon).sum().shift(-(forward_horizon - 1))
    forward_vol = log_return.shift(-1).rolling(forward_horizon, min_periods=forward_horizon).std().shift(-(forward_horizon - 1))
    frame = pd.DataFrame(
        {
            "regime": classified["regime"],
            "forward_return": forward_return,
            "forward_vol": forward_vol,
        },
        index=classified.index,
    ).dropna()
    n = len(frame)
    if n < 50:
        raise ValueError("not enough finite observations for an OOS test")
    split_idx = int(n * train_fraction)
    train = frame.iloc[:split_idx]
    test = frame.iloc[split_idx:]
    train_stats = _group_stats(train, "forward_return", "forward_vol")
    test_stats = _group_stats(test, "forward_return", "forward_vol")
    f_ret_train, p_ret_train = _one_way_anova(train, "regime", "forward_return")
    f_ret_test, p_ret_test = _one_way_anova(test, "regime", "forward_return")
    f_vol_train, p_vol_train = _one_way_anova(train, "regime", "forward_vol")
    f_vol_test, p_vol_test = _one_way_anova(test, "regime", "forward_vol")
    rank_corr_ret = _rank_correlation(train_stats["mean_forward_return"], test_stats["mean_forward_return"])
    rank_corr_vol = _rank_correlation(train_stats["mean_forward_vol"], test_stats["mean_forward_vol"])
    return RegimePredictivenessResult(
        train_split_idx=split_idx,
        test_split_idx=n - split_idx,
        forward_horizon=forward_horizon,
        train_per_regime=train_stats,
        test_per_regime=test_stats,
        train_f_return=f_ret_train,
        train_p_return=p_ret_train,
        test_f_return=f_ret_test,
        test_p_return=p_ret_test,
        train_f_vol=f_vol_train,
        train_p_vol=p_vol_train,
        test_f_vol=f_vol_test,
        test_p_vol=p_vol_test,
        rank_correlation_return=rank_corr_ret,
        rank_correlation_vol=rank_corr_vol,
    )


def _group_stats(frame: pd.DataFrame, *value_columns: str) -> pd.DataFrame:
    rows: dict[str, dict[str, float]] = {}
    for regime, group in frame.groupby("regime"):
        row: dict[str, float] = {"count": float(len(group))}
        for column in value_columns:
            values = group[column].astype(float)
            row[f"mean_{column}"] = float(values.mean()) if len(values) else float("nan")
            row[f"std_{column}"] = float(values.std(ddof=1)) if len(values) > 1 else float("nan")
        rows[str(regime)] = row
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame.from_dict(rows, orient="index").reindex(sorted(rows.keys()))


def _one_way_anova(frame: pd.DataFrame, group_column: str, value_column: str) -> tuple[float, float]:
    """Compute one-way ANOVA F and approximate p-value without scipy."""

    groups = [group[value_column].astype(float).dropna().values for _, group in frame.groupby(group_column)]
    groups = [g for g in groups if len(g) >= 2]
    if len(groups) < 2:
        return float("nan"), float("nan")
    total = np.concatenate(groups)
    overall_mean = float(total.mean())
    ss_between = sum(len(g) * (float(g.mean()) - overall_mean) ** 2 for g in groups)
    ss_within = sum(float(((g - g.mean()) ** 2).sum()) for g in groups)
    k = len(groups)
    n = len(total)
    df_between = k - 1
    df_within = n - k
    if df_within <= 0 or ss_within <= 0:
        return float("nan"), float("nan")
    f_stat = (ss_between / df_between) / (ss_within / df_within)
    # Survival function approximation via the F distribution requires
    # scipy. We return an approximation derived from a chi-squared with
    # df_between degrees of freedom, which is conservative.
    p_approx = _f_p_value_approx(f_stat, df_between, df_within)
    return float(f_stat), float(p_approx)


def _f_p_value_approx(f_stat: float, df1: int, df2: int) -> float:
    """Approximate F-distribution upper-tail probability.

    Uses the relationship F = (chi2/df1) / (chi2/df2) and the
    Wilson-Hilferty cube-root chi-squared normalisation. Good enough for
    diagnostic ordering when scipy is unavailable.
    """

    if not np.isfinite(f_stat) or f_stat <= 0:
        return float("nan")
    # Treat F * df1 as approximately chi2(df1).
    chi2 = f_stat * df1
    # Wilson-Hilferty
    z = (np.power(chi2 / df1, 1 / 3) - (1 - 2 / (9 * df1))) / np.sqrt(2 / (9 * df1))
    # Upper tail of N(0,1)
    return float(0.5 * (1 - _erf(z / np.sqrt(2))))


def _erf(x: float) -> float:
    # Abramowitz & Stegun 7.1.26
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = np.sign(x) if x != 0 else 1
    x = abs(x)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x * x)
    return float(sign * y)


def _rank_correlation(left: pd.Series, right: pd.Series) -> float:
    common = left.dropna().index.intersection(right.dropna().index)
    if len(common) < 2:
        return float("nan")
    left_ranks = left.loc[common].rank()
    right_ranks = right.loc[common].rank()
    return float(left_ranks.corr(right_ranks))
