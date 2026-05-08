from __future__ import annotations

import math


def calculate_position_size(
    equity: float,
    entry_price: float,
    stop_loss: float,
    risk_fraction: float = 0.01,
) -> int:
    risk_per_share = entry_price - stop_loss
    if equity <= 0 or risk_fraction <= 0 or risk_per_share <= 0:
        return 0

    risk_amount = equity * risk_fraction
    shares = math.floor(risk_amount / risk_per_share)
    return max(0, shares)
