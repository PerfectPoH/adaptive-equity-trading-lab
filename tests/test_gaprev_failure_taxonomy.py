from __future__ import annotations

import pandas as pd

from src.experiments.gaprev_failure_taxonomy import classify_gaprev_failures, summarize_taxonomy


def test_classify_gaprev_failures_separates_daily_false_positive_and_cost_destroyed() -> None:
    frame = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "event_date": "2025-01-01",
                "trade_count": 0,
                "rth_gap_return": 0.01,
                "relative_opening_volume": 3.0,
                "reason": "setup_filter_not_met",
            },
            {
                "symbol": "BBB",
                "event_date": "2025-01-02",
                "trade_count": 1,
                "rth_gap_return": -0.1,
                "relative_opening_volume": 4.0,
                "gross_return": 0.03,
                "net_return": -0.02,
                "reason": "",
            },
            {
                "symbol": "CCC",
                "event_date": "2025-01-03",
                "trade_count": 1,
                "rth_gap_return": -0.1,
                "relative_opening_volume": 4.0,
                "gross_return": 0.08,
                "net_return": 0.03,
                "reason": "",
            },
        ]
    )

    classified = classify_gaprev_failures(frame)
    summary = summarize_taxonomy(classified)

    assert classified["failure_category"].tolist() == [
        "RTH_SETUP_FALSE_POSITIVE_FROM_DAILY_GAP",
        "GROSS_EDGE_COST_DESTROYED",
        "NET_WIN_UNPROMOTABLE_SINGLE_EVENT",
    ]
    assert summary["trade_count"] == 2
    assert summary["no_trade_count"] == 1
    assert summary["strategy_promotion_allowed"] is False
