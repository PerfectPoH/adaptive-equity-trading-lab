from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MarketRegimeGuardrailConfig:
    name: str = "small_cap_market_regime_v1"
    max_vix: float = 35.0
    require_iwm_above_ema_50: bool = True
    require_iwm_above_ema_200: bool = False
    min_small_cap_breadth: float | None = None


DEFAULT_MARKET_REGIME_GUARDRAIL_CONFIG = MarketRegimeGuardrailConfig()


def add_market_regime_guardrail_columns(
    frame: pd.DataFrame,
    config: MarketRegimeGuardrailConfig = DEFAULT_MARKET_REGIME_GUARDRAIL_CONFIG,
) -> pd.DataFrame:
    data = frame.copy()
    data["market_regime_guardrail_config"] = config.name
    data["market_regime_block_reason"] = data.apply(lambda row: _block_reason(row, data.columns, config), axis=1)
    data["market_regime_trade_allowed"] = data["market_regime_block_reason"].eq("").astype(object)

    if "signal" in data.columns:
        data["signal_before_market_regime_guardrail"] = data["signal"].fillna(False).astype(bool).astype(object)
        data["signal"] = (
            data["signal_before_market_regime_guardrail"].fillna(False).astype(bool)
            & data["market_regime_trade_allowed"].fillna(False).astype(bool)
        ).astype(object)
    else:
        data["signal_before_market_regime_guardrail"] = pd.Series(False, index=data.index, dtype=object)
        data["signal"] = pd.Series(False, index=data.index, dtype=object)

    return data


def _block_reason(row: pd.Series, columns: pd.Index, config: MarketRegimeGuardrailConfig) -> str:
    reasons: list[str] = []
    required_columns = _required_columns(config)
    for column in required_columns:
        if column not in columns or pd.isna(row.get(column)):
            reasons.append(f"missing_{column}")

    if reasons:
        return ";".join(reasons)

    iwm_close = float(row["iwm_close"])
    if config.require_iwm_above_ema_50 and iwm_close < float(row["iwm_ema_50"]):
        reasons.append("iwm_below_ema_50")
    if config.require_iwm_above_ema_200 and iwm_close < float(row["iwm_ema_200"]):
        reasons.append("iwm_below_ema_200")
    if float(row["vix_close"]) > config.max_vix:
        reasons.append("vix_above_max")
    if config.min_small_cap_breadth is not None and float(row["small_cap_breadth"]) < config.min_small_cap_breadth:
        reasons.append("breadth_below_min")

    return ";".join(reasons)


def _required_columns(config: MarketRegimeGuardrailConfig) -> tuple[str, ...]:
    columns = ["iwm_close", "vix_close"]
    if config.require_iwm_above_ema_50:
        columns.append("iwm_ema_50")
    if config.require_iwm_above_ema_200:
        columns.append("iwm_ema_200")
    if config.min_small_cap_breadth is not None:
        columns.append("small_cap_breadth")
    return tuple(columns)
