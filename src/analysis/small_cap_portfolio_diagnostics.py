from __future__ import annotations

import math
from typing import Any

import pandas as pd


SCORE_PROFILE_COLUMNS = [
    "score_bucket",
    "min_score",
    "max_score",
    "trade_count",
    "avg_return_pct",
    "median_return_pct",
    "win_rate",
    "total_pnl",
    "avg_pnl",
    "simple_trade_sharpe",
]

SETUP_SUMMARY_COLUMNS = [
    "setup_type",
    "trade_count",
    "total_pnl",
    "avg_pnl",
    "avg_return_pct",
    "median_return_pct",
    "win_rate",
    "best_trade_symbol",
    "best_trade_return_pct",
    "worst_trade_symbol",
    "worst_trade_return_pct",
]

SETUP_SCORE_PROFILE_COLUMNS = ["setup_type", *SCORE_PROFILE_COLUMNS]

SETUP_CASH_STARVATION_COLUMNS = [
    "setup_type",
    "evaluable_missed_trades",
    "avg_missed_return_pct",
    "median_missed_return_pct",
    "missed_win_rate",
    "best_missed_symbol",
    "best_missed_return_pct",
    "worst_missed_symbol",
    "worst_missed_return_pct",
]

SETUP_FEATURE_PROFILE_COLUMNS = [
    "setup_type",
    "feature",
    "feature_bucket",
    "min_feature_value",
    "max_feature_value",
    "trade_count",
    "avg_return_pct",
    "median_return_pct",
    "win_rate",
    "total_pnl",
    "avg_pnl",
    "simple_trade_sharpe",
]

REGIME_PROFILE_COLUMNS = [
    "regime_feature",
    "regime_value",
    "trade_count",
    "avg_return_pct",
    "median_return_pct",
    "win_rate",
    "total_pnl",
    "avg_pnl",
    "simple_trade_sharpe",
]

SCANNER_FEATURE_COLUMNS = [
    "gap_pct",
    "open_to_close_return",
    "close_position_daily_range",
    "intraday_range_pct",
    "relative_volume_20d",
    "atr_pct",
    "distance_from_20d_high",
    "rolling_volatility_20d",
]

CASH_STARVATION_COLUMNS = [
    "symbol",
    "as_of",
    "entry_date",
    "exit_date",
    "available_cash",
    "small_cap_setup",
    "entry_price",
    "exit_price",
    "missed_return_pct",
]


def build_portfolio_outlier_breakdown(
    trade_log: pd.DataFrame,
    alert_top_n: int = 3,
    alert_threshold: float = 0.40,
    initial_cash: float | None = None,
) -> dict[str, Any]:
    if trade_log.empty or "pnl" not in trade_log.columns:
        return _empty_outlier_breakdown()

    data = trade_log.copy()
    data["pnl"] = pd.to_numeric(data["pnl"], errors="coerce").fillna(0.0)
    data["return_pct"] = pd.to_numeric(data.get("return_pct", pd.Series(0.0, index=data.index)), errors="coerce")
    total_pnl = float(data["pnl"].sum())
    gross_profit = float(data.loc[data["pnl"] > 0, "pnl"].sum())
    gross_loss = float(data.loc[data["pnl"] < 0, "pnl"].sum())
    winners = data[data["pnl"] > 0].sort_values("pnl", ascending=False)
    best = data.sort_values("pnl", ascending=False).iloc[0]
    worst = data.sort_values("pnl", ascending=True).iloc[0]
    top_contributions = {f"top_{n}_pnl_contribution_pct": _top_contribution(winners, n, total_pnl) for n in (1, 3, 5, 10)}
    alert_value = top_contributions.get(f"top_{alert_top_n}_pnl_contribution_pct", float("nan"))
    ex_outlier = _ex_outlier_metrics(winners, total_pnl, initial_cash)
    return {
        "total_trades": int(len(data)),
        "total_pnl": total_pnl,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        **top_contributions,
        "max_single_trade_contribution_pct": _top_contribution(winners, 1, total_pnl),
        "outlier_concentration_alert": bool(pd.notna(alert_value) and alert_value > alert_threshold),
        **ex_outlier,
        "best_trade_symbol": _symbol(best),
        "best_trade_pnl": float(best.get("pnl", 0.0)),
        "best_trade_return_pct": _safe_float(best.get("return_pct")),
        "worst_trade_symbol": _symbol(worst),
        "worst_trade_pnl": float(worst.get("pnl", 0.0)),
        "worst_trade_return_pct": _safe_float(worst.get("return_pct")),
    }


def build_score_profile_report(
    trade_log: pd.DataFrame,
    score_column: str = "small_cap_scanner_score",
    bins: int = 10,
) -> pd.DataFrame:
    if bins <= 0:
        raise ValueError("bins must be positive")
    if trade_log.empty or score_column not in trade_log.columns or "return_pct" not in trade_log.columns or "pnl" not in trade_log.columns:
        return pd.DataFrame(columns=SCORE_PROFILE_COLUMNS)

    data = trade_log.copy()
    data[score_column] = pd.to_numeric(data[score_column], errors="coerce")
    data["return_pct"] = pd.to_numeric(data["return_pct"], errors="coerce")
    data["pnl"] = pd.to_numeric(data["pnl"], errors="coerce")
    data = data.dropna(subset=[score_column, "return_pct", "pnl"]).sort_values(score_column).reset_index(drop=True)
    if data.empty:
        return pd.DataFrame(columns=SCORE_PROFILE_COLUMNS)

    unique_scores = sorted(data[score_column].unique())
    bucket_count = min(int(bins), len(unique_scores))
    score_to_bucket = {
        score: f"Q{min((i * bucket_count) // len(unique_scores) + 1, bucket_count)}" for i, score in enumerate(unique_scores)
    }
    data["score_bucket"] = data[score_column].map(score_to_bucket)
    rows: list[dict[str, Any]] = []
    for bucket, group in data.groupby("score_bucket", sort=False):
        returns = group["return_pct"]
        pnl = group["pnl"]
        rows.append(
            {
                "score_bucket": bucket,
                "min_score": float(group[score_column].min()),
                "max_score": float(group[score_column].max()),
                "trade_count": int(len(group)),
                "avg_return_pct": float(returns.mean()),
                "median_return_pct": float(returns.median()),
                "win_rate": float((returns > 0).sum() / len(group)),
                "total_pnl": float(pnl.sum()),
                "avg_pnl": float(pnl.mean()),
                "simple_trade_sharpe": _simple_sharpe(returns),
            }
        )
    return pd.DataFrame(rows, columns=SCORE_PROFILE_COLUMNS)


def build_setup_summary_report(
    trade_log: pd.DataFrame,
    setup_column: str = "small_cap_setup",
) -> pd.DataFrame:
    if trade_log.empty or setup_column not in trade_log.columns or "return_pct" not in trade_log.columns or "pnl" not in trade_log.columns:
        return pd.DataFrame(columns=SETUP_SUMMARY_COLUMNS)
    data = _with_setup_type(trade_log, setup_column)
    data["return_pct"] = pd.to_numeric(data["return_pct"], errors="coerce")
    data["pnl"] = pd.to_numeric(data["pnl"], errors="coerce")
    data = data.dropna(subset=["return_pct", "pnl"])
    if data.empty:
        return pd.DataFrame(columns=SETUP_SUMMARY_COLUMNS)

    rows: list[dict[str, Any]] = []
    for setup_type, group in data.groupby("setup_type", sort=True):
        returns = group["return_pct"]
        pnl = group["pnl"]
        best = group.sort_values("return_pct", ascending=False).iloc[0]
        worst = group.sort_values("return_pct", ascending=True).iloc[0]
        rows.append(
            {
                "setup_type": setup_type,
                "trade_count": int(len(group)),
                "total_pnl": float(pnl.sum()),
                "avg_pnl": float(pnl.mean()),
                "avg_return_pct": float(returns.mean()),
                "median_return_pct": float(returns.median()),
                "win_rate": float((returns > 0).sum() / len(group)),
                "best_trade_symbol": _symbol(best),
                "best_trade_return_pct": float(best["return_pct"]),
                "worst_trade_symbol": _symbol(worst),
                "worst_trade_return_pct": float(worst["return_pct"]),
            }
        )
    return pd.DataFrame(rows, columns=SETUP_SUMMARY_COLUMNS)


def build_setup_score_profile_report(
    trade_log: pd.DataFrame,
    setup_column: str = "small_cap_setup",
    score_column: str = "small_cap_scanner_score",
    bins: int = 10,
) -> pd.DataFrame:
    if trade_log.empty or setup_column not in trade_log.columns:
        return pd.DataFrame(columns=SETUP_SCORE_PROFILE_COLUMNS)
    rows: list[pd.DataFrame] = []
    for setup_type, group in _with_setup_type(trade_log, setup_column).groupby("setup_type", sort=True):
        profile = build_score_profile_report(group, score_column=score_column, bins=bins)
        if profile.empty:
            continue
        profile.insert(0, "setup_type", setup_type)
        rows.append(profile)
    if not rows:
        return pd.DataFrame(columns=SETUP_SCORE_PROFILE_COLUMNS)
    return pd.concat(rows, ignore_index=True)[SETUP_SCORE_PROFILE_COLUMNS]


def build_setup_feature_profile_report(
    trade_log: pd.DataFrame,
    features: list[str] | tuple[str, ...] = tuple(SCANNER_FEATURE_COLUMNS),
    setup_column: str = "small_cap_setup",
    bins: int = 4,
) -> pd.DataFrame:
    if bins <= 0:
        raise ValueError("bins must be positive")
    if trade_log.empty or setup_column not in trade_log.columns or "return_pct" not in trade_log.columns or "pnl" not in trade_log.columns:
        return pd.DataFrame(columns=SETUP_FEATURE_PROFILE_COLUMNS)
    data = _with_setup_type(trade_log, setup_column)
    data["return_pct"] = pd.to_numeric(data["return_pct"], errors="coerce")
    data["pnl"] = pd.to_numeric(data["pnl"], errors="coerce")
    data = data.dropna(subset=["return_pct", "pnl"])
    if data.empty:
        return pd.DataFrame(columns=SETUP_FEATURE_PROFILE_COLUMNS)

    rows: list[dict[str, Any]] = []
    for setup_type, setup_group in data.groupby("setup_type", sort=True):
        for feature in features:
            if feature not in setup_group.columns:
                continue
            feature_group = setup_group.copy()
            feature_group[feature] = pd.to_numeric(feature_group[feature], errors="coerce")
            feature_group = feature_group.dropna(subset=[feature])
            if feature_group.empty:
                continue
            unique_values = sorted(feature_group[feature].unique())
            bucket_count = min(int(bins), len(unique_values))
            value_to_bucket = {
                value: f"Q{min((i * bucket_count) // len(unique_values) + 1, bucket_count)}" for i, value in enumerate(unique_values)
            }
            feature_group["feature_bucket"] = feature_group[feature].map(value_to_bucket)
            for bucket, bucket_group in feature_group.groupby("feature_bucket", sort=False):
                returns = bucket_group["return_pct"]
                pnl = bucket_group["pnl"]
                rows.append(
                    {
                        "setup_type": setup_type,
                        "feature": feature,
                        "feature_bucket": bucket,
                        "min_feature_value": float(bucket_group[feature].min()),
                        "max_feature_value": float(bucket_group[feature].max()),
                        "trade_count": int(len(bucket_group)),
                        "avg_return_pct": float(returns.mean()),
                        "median_return_pct": float(returns.median()),
                        "win_rate": float((returns > 0).sum() / len(bucket_group)),
                        "total_pnl": float(pnl.sum()),
                        "avg_pnl": float(pnl.mean()),
                        "simple_trade_sharpe": _simple_sharpe(returns),
                    }
                )
    return pd.DataFrame(rows, columns=SETUP_FEATURE_PROFILE_COLUMNS)


def build_regime_profile_report(trade_log: pd.DataFrame) -> pd.DataFrame:
    if trade_log.empty or "return_pct" not in trade_log.columns or "pnl" not in trade_log.columns:
        return pd.DataFrame(columns=REGIME_PROFILE_COLUMNS)
    data = trade_log.copy()
    data["return_pct"] = pd.to_numeric(data["return_pct"], errors="coerce")
    data["pnl"] = pd.to_numeric(data["pnl"], errors="coerce")
    data = data.dropna(subset=["return_pct", "pnl"])
    if data.empty:
        return pd.DataFrame(columns=REGIME_PROFILE_COLUMNS)

    rows: list[dict[str, Any]] = []
    rows.extend(_binary_regime_rows(data, "iwm_above_ema_50", "iwm_close", "iwm_ema_50"))
    rows.extend(_binary_regime_rows(data, "iwm_above_ema_200", "iwm_close", "iwm_ema_200"))
    rows.extend(_vix_regime_rows(data))
    return pd.DataFrame(rows, columns=REGIME_PROFILE_COLUMNS)


def build_cash_starvation_report(
    rejections: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    holding_period_bars: int,
) -> pd.DataFrame:
    if holding_period_bars <= 0:
        raise ValueError("holding_period_bars must be positive")
    if rejections.empty or "reject_reason" not in rejections.columns:
        return pd.DataFrame(columns=CASH_STARVATION_COLUMNS)

    rows: list[dict[str, Any]] = []
    rejected = rejections[rejections["reject_reason"].fillna("").astype(str) == "insufficient_funds"]
    for _, rejection in rejected.iterrows():
        symbol = str(rejection.get("symbol", ""))
        entry = _entry_and_exit(frames.get(symbol), rejection.get("as_of"), holding_period_bars)
        if entry is None:
            continue
        entry_date, entry_price, exit_date, exit_price = entry
        rows.append(
            {
                "symbol": symbol,
                "as_of": pd.to_datetime(rejection.get("as_of"), errors="coerce"),
                "entry_date": entry_date,
                "exit_date": exit_date,
                "available_cash": _safe_float(rejection.get("available_cash")),
                "small_cap_setup": _setup_type(rejection.get("small_cap_setup")),
                "entry_price": entry_price,
                "exit_price": exit_price,
                "missed_return_pct": float((exit_price / entry_price) - 1) if entry_price else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=CASH_STARVATION_COLUMNS)


def summarize_cash_starvation_report(
    cash_starvation: pd.DataFrame,
    total_insufficient_funds_rejections: int,
) -> dict[str, Any]:
    if cash_starvation.empty or "missed_return_pct" not in cash_starvation.columns:
        return {
            "insufficient_funds_rejections": int(total_insufficient_funds_rejections),
            "evaluable_missed_trades": 0,
            "avg_missed_return_pct": float("nan"),
            "median_missed_return_pct": float("nan"),
            "missed_win_rate": float("nan"),
            "best_missed_symbol": None,
            "best_missed_return_pct": float("nan"),
            "worst_missed_symbol": None,
            "worst_missed_return_pct": float("nan"),
        }

    data = cash_starvation.copy()
    data["missed_return_pct"] = pd.to_numeric(data["missed_return_pct"], errors="coerce")
    data = data.dropna(subset=["missed_return_pct"])
    if data.empty:
        return summarize_cash_starvation_report(pd.DataFrame(), total_insufficient_funds_rejections)

    best = data.sort_values("missed_return_pct", ascending=False).iloc[0]
    worst = data.sort_values("missed_return_pct", ascending=True).iloc[0]
    return {
        "insufficient_funds_rejections": int(total_insufficient_funds_rejections),
        "evaluable_missed_trades": int(len(data)),
        "avg_missed_return_pct": float(data["missed_return_pct"].mean()),
        "median_missed_return_pct": float(data["missed_return_pct"].median()),
        "missed_win_rate": float((data["missed_return_pct"] > 0).sum() / len(data)),
        "best_missed_symbol": _symbol(best),
        "best_missed_return_pct": float(best["missed_return_pct"]),
        "worst_missed_symbol": _symbol(worst),
        "worst_missed_return_pct": float(worst["missed_return_pct"]),
    }


def build_setup_cash_starvation_summary(
    cash_starvation: pd.DataFrame,
    setup_column: str = "small_cap_setup",
) -> pd.DataFrame:
    if cash_starvation.empty or setup_column not in cash_starvation.columns or "missed_return_pct" not in cash_starvation.columns:
        return pd.DataFrame(columns=SETUP_CASH_STARVATION_COLUMNS)
    data = _with_setup_type(cash_starvation, setup_column)
    data["missed_return_pct"] = pd.to_numeric(data["missed_return_pct"], errors="coerce")
    data = data.dropna(subset=["missed_return_pct"])
    if data.empty:
        return pd.DataFrame(columns=SETUP_CASH_STARVATION_COLUMNS)

    rows: list[dict[str, Any]] = []
    for setup_type, group in data.groupby("setup_type", sort=True):
        returns = group["missed_return_pct"]
        best = group.sort_values("missed_return_pct", ascending=False).iloc[0]
        worst = group.sort_values("missed_return_pct", ascending=True).iloc[0]
        rows.append(
            {
                "setup_type": setup_type,
                "evaluable_missed_trades": int(len(group)),
                "avg_missed_return_pct": float(returns.mean()),
                "median_missed_return_pct": float(returns.median()),
                "missed_win_rate": float((returns > 0).sum() / len(group)),
                "best_missed_symbol": _symbol(best),
                "best_missed_return_pct": float(best["missed_return_pct"]),
                "worst_missed_symbol": _symbol(worst),
                "worst_missed_return_pct": float(worst["missed_return_pct"]),
            }
        )
    return pd.DataFrame(rows, columns=SETUP_CASH_STARVATION_COLUMNS)


def _binary_regime_rows(data: pd.DataFrame, regime_feature: str, lhs_column: str, rhs_column: str) -> list[dict[str, Any]]:
    if lhs_column not in data.columns or rhs_column not in data.columns:
        return []
    regime_data = data.copy()
    regime_data[lhs_column] = pd.to_numeric(regime_data[lhs_column], errors="coerce")
    regime_data[rhs_column] = pd.to_numeric(regime_data[rhs_column], errors="coerce")
    regime_data = regime_data.dropna(subset=[lhs_column, rhs_column])
    if regime_data.empty:
        return []
    regime_data["_regime_value"] = (regime_data[lhs_column] > regime_data[rhs_column]).astype(str)
    rows = []
    for value in sorted(regime_data["_regime_value"].unique()):
        rows.append(_regime_summary_row(regime_feature, value, regime_data[regime_data["_regime_value"] == value]))
    return rows


def _vix_regime_rows(data: pd.DataFrame) -> list[dict[str, Any]]:
    if "vix_close" not in data.columns:
        return []
    regime_data = data.copy()
    regime_data["vix_close"] = pd.to_numeric(regime_data["vix_close"], errors="coerce")
    regime_data = regime_data.dropna(subset=["vix_close"])
    if regime_data.empty:
        return []
    median_vix = float(regime_data["vix_close"].median())
    regime_data["_regime_value"] = ["low" if value <= median_vix else "high" for value in regime_data["vix_close"]]
    rows = []
    for value in ("low", "high"):
        bucket = regime_data[regime_data["_regime_value"] == value]
        if not bucket.empty:
            rows.append(_regime_summary_row("vix_bucket", value, bucket))
    return rows


def _regime_summary_row(regime_feature: str, regime_value: str, group: pd.DataFrame) -> dict[str, Any]:
    returns = group["return_pct"]
    pnl = group["pnl"]
    return {
        "regime_feature": regime_feature,
        "regime_value": regime_value,
        "trade_count": int(len(group)),
        "avg_return_pct": float(returns.mean()),
        "median_return_pct": float(returns.median()),
        "win_rate": float((returns > 0).sum() / len(group)),
        "total_pnl": float(pnl.sum()),
        "avg_pnl": float(pnl.mean()),
        "simple_trade_sharpe": _simple_sharpe(returns),
    }


def _empty_outlier_breakdown() -> dict[str, Any]:
    breakdown: dict[str, Any] = {
        "total_trades": 0,
        "total_pnl": 0.0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "top_1_pnl_contribution_pct": float("nan"),
        "top_3_pnl_contribution_pct": float("nan"),
        "top_5_pnl_contribution_pct": float("nan"),
        "top_10_pnl_contribution_pct": float("nan"),
        "max_single_trade_contribution_pct": float("nan"),
        "outlier_concentration_alert": False,
        "best_trade_symbol": None,
        "best_trade_pnl": float("nan"),
        "best_trade_return_pct": float("nan"),
        "worst_trade_symbol": None,
        "worst_trade_pnl": float("nan"),
        "worst_trade_return_pct": float("nan"),
    }
    for n in (1, 3, 5):
        breakdown[f"pnl_excluding_top_{n}"] = 0.0
        breakdown[f"sign_flip_excluding_top_{n}"] = False
        breakdown[f"portfolio_return_excluding_top_{n}"] = float("nan")
    return breakdown


def _ex_outlier_metrics(
    winners: pd.DataFrame,
    total_pnl: float,
    initial_cash: float | None,
) -> dict[str, Any]:
    """Compute P&L and portfolio return after stripping the top N winners.

    The check answers RISK-022: if removing the top N winning trades flips the
    portfolio from net positive to net non-positive, the equity curve is a
    lottery on a handful of outliers and the setup is not promotable, no matter
    how large ``return_pct`` looks.
    """
    metrics: dict[str, Any] = {}
    has_initial_cash = initial_cash is not None and float(initial_cash) > 0
    for n in (1, 3, 5):
        top_pnl = float(winners.head(n)["pnl"].sum()) if not winners.empty else 0.0
        excluded_pnl = total_pnl - top_pnl
        metrics[f"pnl_excluding_top_{n}"] = excluded_pnl
        metrics[f"sign_flip_excluding_top_{n}"] = bool(total_pnl > 0 and excluded_pnl <= 0)
        if has_initial_cash:
            metrics[f"portfolio_return_excluding_top_{n}"] = excluded_pnl / float(initial_cash)
        else:
            metrics[f"portfolio_return_excluding_top_{n}"] = float("nan")
    return metrics


def _top_contribution(winners: pd.DataFrame, n: int, total_pnl: float) -> float:
    if winners.empty or total_pnl == 0:
        return float("nan")
    return float(winners.head(n)["pnl"].sum() / total_pnl)


def _entry_and_exit(
    frame: pd.DataFrame | None,
    as_of: object,
    holding_period_bars: int,
) -> tuple[pd.Timestamp, float, pd.Timestamp, float] | None:
    if frame is None or frame.empty or "Open" not in frame.columns or "Close" not in frame.columns:
        return None
    data = frame.copy().sort_index()
    as_of_ts = pd.to_datetime(as_of, errors="coerce")
    if pd.isna(as_of_ts):
        return None
    signal_date = _nearest_index_on_or_before(data, pd.Timestamp(as_of_ts).normalize())
    if signal_date is None:
        return None
    signal_position = data.index.get_loc(signal_date)
    entry_position = signal_position + 1
    exit_position = entry_position + holding_period_bars
    if exit_position >= len(data):
        return None
    entry_date = data.index[entry_position]
    exit_date = data.index[exit_position]
    entry_price = pd.to_numeric(pd.Series([data.loc[entry_date, "Open"]]), errors="coerce").iat[0]
    exit_price = pd.to_numeric(pd.Series([data.loc[exit_date, "Close"]]), errors="coerce").iat[0]
    if pd.isna(entry_price) or pd.isna(exit_price):
        return None
    return pd.Timestamp(entry_date), float(entry_price), pd.Timestamp(exit_date), float(exit_price)


def _nearest_index_on_or_before(frame: pd.DataFrame, date: pd.Timestamp) -> pd.Timestamp | None:
    candidates = frame.index[frame.index <= date]
    if len(candidates) == 0:
        return None
    return candidates[-1]


def _simple_sharpe(returns: pd.Series) -> float:
    if len(returns) < 2:
        return float("nan")
    std = float(returns.std(ddof=1))
    if std == 0 or math.isnan(std):
        return float("nan")
    return float(returns.mean() / std)


def _safe_float(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return parsed if math.isfinite(parsed) else float("nan")


def _with_setup_type(frame: pd.DataFrame, setup_column: str) -> pd.DataFrame:
    data = frame.copy()
    data["setup_type"] = data[setup_column].map(_setup_type)
    data = data[data["setup_type"] != "unknown"].copy()
    return data


def _setup_type(value: object) -> str:
    if pd.isna(value):
        return "unknown"
    setup = str(value).strip()
    return setup if setup else "unknown"


def _symbol(row: pd.Series) -> str | None:
    value = row.get("symbol")
    if pd.isna(value):
        return None
    return str(value)
