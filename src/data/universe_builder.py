from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SmallCapUniverseConfig:
    min_market_cap: float = 100_000_000
    max_market_cap: float = 5_000_000_000
    min_price: float = 2.0
    min_avg_volume_20d: float = 500_000
    min_avg_dollar_volume_20d: float = 2_000_000
    exclude_etfs: bool = True


REQUIRED_COLUMNS = (
    "symbol",
    "market_cap",
    "price",
    "avg_volume_20d",
    "avg_dollar_volume_20d",
    "is_etf",
)


def build_small_cap_universe(
    candidates: pd.DataFrame,
    config: SmallCapUniverseConfig = SmallCapUniverseConfig(),
    passed_only: bool = True,
) -> pd.DataFrame:
    diagnostics = candidates.copy()
    if diagnostics.empty:
        diagnostics["passes_universe_filter"] = pd.Series(dtype=object)
        diagnostics["rejection_reasons"] = pd.Series(dtype=object)
        return diagnostics

    diagnostics["rejection_reasons"] = diagnostics.apply(
        lambda row: _rejection_reasons(row, diagnostics.columns, config),
        axis=1,
    )
    diagnostics["passes_universe_filter"] = diagnostics["rejection_reasons"].eq("").astype(object)
    if passed_only:
        diagnostics = diagnostics[diagnostics["passes_universe_filter"]].copy()
    if "avg_dollar_volume_20d" in diagnostics.columns:
        diagnostics = diagnostics.sort_values("avg_dollar_volume_20d", ascending=False)
    return diagnostics.reset_index(drop=True)


def _rejection_reasons(row: pd.Series, columns: pd.Index, config: SmallCapUniverseConfig) -> str:
    reasons: list[str] = []
    for column in REQUIRED_COLUMNS:
        if column not in columns or pd.isna(row.get(column)):
            reasons.append(f"missing_{column}")

    if reasons:
        return ";".join(reasons)

    market_cap = float(row["market_cap"])
    price = float(row["price"])
    avg_volume = float(row["avg_volume_20d"])
    avg_dollar_volume = float(row["avg_dollar_volume_20d"])
    is_etf = bool(row["is_etf"])

    if config.exclude_etfs and is_etf:
        reasons.append("is_etf")
    if market_cap < config.min_market_cap:
        reasons.append("market_cap_below_min")
    if market_cap > config.max_market_cap:
        reasons.append("market_cap_above_max")
    if price < config.min_price:
        reasons.append("price_below_min")
    if avg_volume < config.min_avg_volume_20d:
        reasons.append("volume_below_min")
    if avg_dollar_volume < config.min_avg_dollar_volume_20d:
        reasons.append("dollar_volume_below_min")

    return ";".join(reasons)
