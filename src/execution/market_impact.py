from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SquareRootImpactConfig:
    coefficient_bps: float = 15.0
    participation_cap: float = 0.25


def square_root_impact_bps(
    *,
    order_notional: float,
    adv_notional: float,
    volatility: float,
    config: SquareRootImpactConfig,
) -> float:
    """
    Approximate market impact in bps for daily bars.

    impact_bps = coefficient_bps * volatility * sqrt(order_notional / adv_notional)
    """
    if order_notional <= 0 or adv_notional <= 0 or volatility <= 0:
        return 0.0
    participation = order_notional / adv_notional
    if participation >= config.participation_cap:
        return float("inf")
    return float(config.coefficient_bps * volatility * math.sqrt(participation))
