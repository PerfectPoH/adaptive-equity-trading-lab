from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.backtest.small_cap_execution import SmallCapExecutionConfig
from src.execution.market_impact import SquareRootImpactConfig, square_root_impact_bps
from src.risk.risk_manager import calculate_position_size


@dataclass(frozen=True)
class SmallCapExecutionDecision:
    accepted: bool
    symbol: str
    as_of: object | None
    reject_reason: str
    entry_reference_price: float | None
    entry_price: float | None
    estimated_cost_pct: float
    impact_cost_pct: float
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
            "available_cash": float(available_cash),
        }

        close = _safe_float(row.get("Close"))
        atr = _safe_float(row.get("atr"))
        avg_dollar_volume = _safe_float(row.get("avg_dollar_volume_20d"))
        execution_volatility = _safe_float(row.get("rolling_volatility_20d"))
        if execution_volatility is None:
            execution_volatility = _safe_float(row.get("atr_pct"))
        if execution_volatility is None:
            execution_volatility = 0.0
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

        risk_size = calculate_position_size(float(available_cash), entry_price, stop_loss, self.config.risk_fraction)
        liquidity_size = math.floor(max_liquidity_notional / entry_price)
        cash_size = math.floor(float(available_cash) / entry_price)
        position_size = min(risk_size, liquidity_size, cash_size)
        provisional_notional = float(position_size * entry_price)
        impact_bps = square_root_impact_bps(
            order_notional=provisional_notional,
            adv_notional=float(avg_dollar_volume),
            volatility=float(execution_volatility),
            config=SquareRootImpactConfig(
                coefficient_bps=self.config.impact_coefficient_bps,
                participation_cap=self.config.impact_participation_cap,
            ),
        )
        if math.isinf(impact_bps):
            return self._reject(
                base,
                "impact_participation_above_cap",
                entry_reference_price=next_open_value,
                entry_price=entry_price,
                next_open_gap_pct=gap,
                stop_loss=stop_loss,
                take_profit=take_profit,
                max_liquidity_notional=max_liquidity_notional,
                impact_cost_pct=float("inf"),
            )
        impact_cost_pct = impact_bps / 10_000.0
        total_cost_pct = cost_pct + impact_cost_pct
        entry_price = round(next_open_value * (1 + total_cost_pct), 6)
        stop_loss = round(entry_price - (atr * self.config.stop_atr_multiple), 6)
        take_profit = round(entry_price + (atr * self.config.take_profit_atr_multiple), 6)
        risk_size = calculate_position_size(float(available_cash), entry_price, stop_loss, self.config.risk_fraction)
        liquidity_size = math.floor(max_liquidity_notional / entry_price)
        cash_size = math.floor(float(available_cash) / entry_price)
        position_size = min(risk_size, liquidity_size, cash_size)
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
                impact_cost_pct=impact_cost_pct,
            )

        return SmallCapExecutionDecision(
            accepted=True,
            reject_reason="",
            entry_reference_price=float(next_open_value),
            entry_price=entry_price,
            estimated_cost_pct=total_cost_pct,
            impact_cost_pct=impact_cost_pct,
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
        impact_cost_pct: float | None = None,
    ) -> SmallCapExecutionDecision:
        return SmallCapExecutionDecision(
            accepted=False,
            reject_reason=reason,
            entry_reference_price=entry_reference_price,
            entry_price=entry_price,
            estimated_cost_pct=self._cost_pct(),
            impact_cost_pct=0.0 if impact_cost_pct is None else float(impact_cost_pct),
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
