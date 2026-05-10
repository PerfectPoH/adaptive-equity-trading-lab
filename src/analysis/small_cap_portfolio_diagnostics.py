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


def build_portfolio_outlier_breakdown(
    trade_log: pd.DataFrame,
    alert_top_n: int = 3,
    alert_threshold: float = 0.40,
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
    return {
        "total_trades": int(len(data)),
        "total_pnl": total_pnl,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        **top_contributions,
        "max_single_trade_contribution_pct": _top_contribution(winners, 1, total_pnl),
        "outlier_concentration_alert": bool(pd.notna(alert_value) and alert_value > alert_threshold),
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


def _empty_outlier_breakdown() -> dict[str, Any]:
    return {
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


def _top_contribution(winners: pd.DataFrame, n: int, total_pnl: float) -> float:
    if winners.empty or total_pnl == 0:
        return float("nan")
    return float(winners.head(n)["pnl"].sum() / total_pnl)


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


def _symbol(row: pd.Series) -> str | None:
    value = row.get("symbol")
    if pd.isna(value):
        return None
    return str(value)
