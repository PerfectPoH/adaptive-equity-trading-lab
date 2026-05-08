from __future__ import annotations

import math
from typing import Any

import pandas as pd


REGIME_FEATURES = [
    "signal_model_probability",
    "signal_scanner_score",
    "signal_signal_quality_score",
    "signal_risk_fraction",
    "signal_atr_pct",
    "signal_relative_volume_20d",
    "signal_distance_from_20d_high",
    "signal_rolling_volatility_20d",
    "signal_news_market_stress",
    "signal_news_market_avg_tone",
]


def build_feature_regime_analysis(
    trades: pd.DataFrame,
    bins: int = 3,
    min_bin_count: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if trades.empty:
        return pd.DataFrame(), pd.DataFrame(), _empty_summary()

    trade_data = trades.copy()
    trade_data["return_pct"] = pd.to_numeric(trade_data["return_pct"], errors="coerce")
    trade_data["pnl"] = pd.to_numeric(trade_data["pnl"], errors="coerce")
    trade_data = trade_data.dropna(subset=["return_pct"])
    if trade_data.empty:
        return pd.DataFrame(), pd.DataFrame(), _empty_summary()

    regime_rows = _build_regime_rows(trade_data, bins)
    contrast_rows = _build_contrast_rows(trade_data)
    summary = _summarize_regimes(regime_rows, contrast_rows, trade_data, min_bin_count)
    return regime_rows, contrast_rows, summary


def _build_regime_rows(trades: pd.DataFrame, bins: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for feature in _available_numeric_features(trades):
        feature_data = trades.dropna(subset=[feature]).copy()
        unique_values = feature_data[feature].nunique()
        if unique_values < 2:
            continue

        bucket_count = max(2, min(bins, unique_values, len(feature_data)))
        buckets = pd.qcut(feature_data[feature], q=bucket_count, duplicates="drop")
        categories = list(buckets.cat.categories)
        if len(categories) < 2:
            continue

        feature_data["_regime_bucket"] = buckets
        for bucket_index, bucket in enumerate(categories):
            bucket_rows = feature_data[feature_data["_regime_bucket"] == bucket]
            if bucket_rows.empty:
                continue
            returns = bucket_rows["return_pct"]
            rows.append(
                {
                    "feature": feature,
                    "regime": _bucket_label(bucket_index, len(categories)),
                    "lower": _safe_float(bucket.left),
                    "upper": _safe_float(bucket.right),
                    "trades": int(len(bucket_rows)),
                    "wins": int((returns > 0).sum()),
                    "losses": int((returns < 0).sum()),
                    "win_rate": _safe_float((returns > 0).mean()),
                    "loss_rate": _safe_float((returns < 0).mean()),
                    "avg_return_pct": _safe_float(returns.mean()),
                    "median_return_pct": _safe_float(returns.median()),
                    "total_pnl": _safe_float(bucket_rows["pnl"].sum()),
                    "avg_feature_value": _safe_float(bucket_rows[feature].mean()),
                }
            )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["feature", "regime"]).reset_index(drop=True)


def _build_contrast_rows(trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    winners = trades[trades["return_pct"] > 0]
    losers = trades[trades["return_pct"] < 0]
    if winners.empty or losers.empty:
        return pd.DataFrame()

    for feature in _available_numeric_features(trades):
        winner_values = pd.to_numeric(winners[feature], errors="coerce").dropna()
        loser_values = pd.to_numeric(losers[feature], errors="coerce").dropna()
        if winner_values.empty or loser_values.empty:
            continue
        if pd.concat([winner_values, loser_values]).nunique() < 2:
            continue

        loss_mean = _safe_float(loser_values.mean())
        win_mean = _safe_float(winner_values.mean())
        loss_median = _safe_float(loser_values.median())
        win_median = _safe_float(winner_values.median())
        median_delta = loss_median - win_median
        rows.append(
            {
                "feature": feature,
                "win_mean": win_mean,
                "loss_mean": loss_mean,
                "loss_mean_minus_win_mean": loss_mean - win_mean,
                "win_median": win_median,
                "loss_median": loss_median,
                "loss_median_minus_win_median": median_delta,
                "abs_median_delta": abs(median_delta),
                "direction": "losses_higher" if median_delta > 0 else "losses_lower",
                "win_count": int(len(winner_values)),
                "loss_count": int(len(loser_values)),
            }
        )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("abs_median_delta", ascending=False).reset_index(drop=True)


def _summarize_regimes(
    regimes: pd.DataFrame,
    contrasts: pd.DataFrame,
    trades: pd.DataFrame,
    min_bin_count: int,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total_trades": int(len(trades)),
        "wins": int((trades["return_pct"] > 0).sum()),
        "losses": int((trades["return_pct"] < 0).sum()),
        "min_bin_count": int(min_bin_count),
        "worst_regimes": [],
        "best_regimes": [],
        "highest_loss_rate_regimes": [],
        "strongest_feature_contrasts": [],
        "primary_findings": [],
    }

    eligible = regimes[regimes["trades"] >= min_bin_count].copy() if not regimes.empty else pd.DataFrame()
    if not eligible.empty:
        worst = eligible.sort_values(["avg_return_pct", "trades"], ascending=[True, False]).head(5)
        best = eligible.sort_values(["avg_return_pct", "trades"], ascending=[False, False]).head(5)
        high_loss = eligible.sort_values(["loss_rate", "avg_return_pct"], ascending=[False, True]).head(5)
        summary["worst_regimes"] = _records(worst)
        summary["best_regimes"] = _records(best)
        summary["highest_loss_rate_regimes"] = _records(high_loss)

    if not contrasts.empty:
        summary["strongest_feature_contrasts"] = _records(contrasts.head(5))

    summary["primary_findings"] = _primary_findings(summary)
    return summary


def _primary_findings(summary: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    worst = summary.get("worst_regimes") or []
    if worst:
        first = worst[0]
        findings.append(
            "Weakest average-return regime: "
            f"{first['feature']} {first['regime']} "
            f"with avg return {_format_pct(first['avg_return_pct'])} across {first['trades']} trades."
        )

    high_loss = summary.get("highest_loss_rate_regimes") or []
    if high_loss:
        first = high_loss[0]
        findings.append(
            "Highest loss-rate regime: "
            f"{first['feature']} {first['regime']} "
            f"with loss rate {_format_pct(first['loss_rate'])} across {first['trades']} trades."
        )

    contrasts = summary.get("strongest_feature_contrasts") or []
    if contrasts:
        first = contrasts[0]
        direction = "higher" if first["direction"] == "losses_higher" else "lower"
        findings.append(
            "Largest win/loss feature contrast: "
            f"losing trades had {direction} {first['feature']} than winning trades."
        )

    if not findings:
        findings.append("No stable feature regime pattern found yet.")
    return findings


def _available_numeric_features(trades: pd.DataFrame) -> list[str]:
    features = []
    for feature in REGIME_FEATURES:
        if feature not in trades.columns:
            continue
        numeric = pd.to_numeric(trades[feature], errors="coerce")
        if numeric.notna().sum() >= 2:
            trades[feature] = numeric
            features.append(feature)
    return features


def _bucket_label(index: int, total: int) -> str:
    if total == 3:
        return ["low", "mid", "high"][index]
    return f"bin_{index + 1}"


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.copy()
    for column in clean.columns:
        if pd.api.types.is_numeric_dtype(clean[column]):
            clean[column] = clean[column].map(_safe_float)
    return clean.to_dict(orient="records")


def _empty_summary() -> dict[str, Any]:
    return {
        "total_trades": 0,
        "wins": 0,
        "losses": 0,
        "min_bin_count": 0,
        "worst_regimes": [],
        "best_regimes": [],
        "highest_loss_rate_regimes": [],
        "strongest_feature_contrasts": [],
        "primary_findings": ["No trades available for feature-regime analysis."],
    }


def _format_pct(value: object) -> str:
    parsed = _safe_float(value)
    if math.isnan(parsed):
        return "nan"
    return f"{parsed:.2%}"


def _safe_float(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return parsed if math.isfinite(parsed) else float("nan")
