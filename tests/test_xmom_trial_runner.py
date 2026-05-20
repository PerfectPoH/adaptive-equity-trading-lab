from __future__ import annotations

import pandas as pd

from src.experiments.xmom_trial_runner import XMOMExecutionConfig, _monthly_entry_dates


def test_xmom_monthly_entry_dates_selects_first_trading_day_per_month() -> None:
    prices = pd.DataFrame(
        {
            "symbol": ["AAA"] * 5,
            "date": pd.to_datetime(["2025-01-02", "2025-01-03", "2025-02-03", "2025-02-04", "2025-03-03"]),
        }
    )

    entries = _monthly_entry_dates(prices, XMOMExecutionConfig())

    assert [entry.date().isoformat() for entry in entries] == ["2025-01-02", "2025-02-03", "2025-03-03"]
