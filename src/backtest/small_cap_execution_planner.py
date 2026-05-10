from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.backtest.small_cap_execution import SmallCapExecutionConfig


@dataclass(frozen=True)
class SmallCapExecutionDecision:
    accepted: bool
    symbol: str
    as_of: object | None
    reject_reason: str
    entry_reference_price: float | None
    entry_price: float | None
    estimated_cost_pct: float
    next_open_gap_pct: float | None
    stop_loss: float | None
    take_profit: float | None
    position_size: int
    position_notional: float
    max_liquidity_notional: float | None
    available_cash: float


class SmallCapExecutionPlanner:
    def __init__(self, config: SmallCapExecutionConfig = SmallCapExecutionConfig()) -> None:
        self.config = config

    def plan_trade(
        self,
        candidate: pd.Series | dict[str, Any],
        next_open: float,
        available_cash: float,
    ) -> SmallCapExecutionDecision:
        row = pd.Series(candidate)
        symbol = str(row.get("symbol", ""))
        as_of = row.get("as_of", None)
        cost_pct = self._cost_pct()
        base = {
            "symbol": symbol,
            "as_of": as_of,
            "estimated_cost_pct": cost_pct,
            "available_cash": float(available_cash),
        }

        close = _safe_float(row.get("Close"))
        atr = _safe_float(row.get("atr"))
        avg_dollar_volume = _safe_float(row.get("avg_dollar_volume_20d"))
        next_open_value = _safe_float(next_open)
        if close is None:
            return self._reject(base, "missing_Close")
        if atr is None:
            return self._reject(base, "missing_atr")
        if avg_dollar_volume is None:
            return self._reject(base, "missing_avg_dollar_volume_20d")
        if next_open_value is None:
            return self._reject(base, "missing_next_open")
        if available_cash < self.config.min_trade_notional:
            return self._reject(base, "insufficient_funds")

        gap = abs((next_open_value / close) - 1)
        if gap > self.config.max_next_open_gap:
            return self._reject(base, "gap_above_max", entry_reference_price=next_open_value, next_open_gap_pct=gap)

        entry_price = round(next_open_value * (1 + cost_pct), 6)
        stop_loss = round(entry_price - (atr * self.config.stop_atr_multiple), 6)
        take_profit = round(entry_price + (atr * self.config.take_profit_atr_multiple), 6)
        max_liquidity_notional = float(avg_dollar_volume * self.config.max_position_dollar_volume_fraction)
        if max_liquidity_notional < self.config.min_trade_notional:
            return self._reject(
                base,
                "liquidity_cap_below_min_trade_notional",
                entry_reference_price=next_open_value,
                entry_price=entry_price,
                next_open_gap_pct=gap,
                stop_loss=stop_loss,
                take_profit=take_profit,
                max_liquidity_notional=max_liquidity_notional,
            )

        target_notional = min(float(available_cash), max_liquidity_notional)
        position_size = math.floor(target_notional / entry_price)
        position_notional = float(position_size * entry_price)
        if position_size <= 0 or position_notional < self.config.min_trade_notional:
            return self._reject(
                base,
                "position_below_min_trade_notional",
                entry_reference_price=next_open_value,
                entry_price=entry_price,
                next_open_gap_pct=gap,
                stop_loss=stop_loss,
                take_profit=take_profit,
                max_liquidity_notional=max_liquidity_notional,
            )

        return SmallCapExecutionDecision(
            accepted=True,
            reject_reason="",
            entry_reference_price=float(next_open_value),
            entry_price=entry_price,
            next_open_gap_pct=float(gap),
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=int(position_size),
            position_notional=position_notional,
            max_liquidity_notional=max_liquidity_notional,
            **base,
        )

    def _cost_pct(self) -> float:
        return float((self.config.spread_bps + self.config.slippage_bps) / 10_000)

    def _reject(
        self,
        base: dict[str, object],
        reason: str,
        entry_reference_price: float | None = None,
        entry_price: float | None = None,
        next_open_gap_pct: float | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        max_liquidity_notional: float | None = None,
    ) -> SmallCapExecutionDecision:
        return SmallCapExecutionDecision(
            accepted=False,
            reject_reason=reason,
            entry_reference_price=entry_reference_price,
            entry_price=entry_price,
            next_open_gap_pct=next_open_gap_pct,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=0,
            position_notional=0.0,
            max_liquidity_notional=max_liquidity_notional,
            **base,
        )


def _safe_float(value: object) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
