from __future__ import annotations

import pandas as pd

from src.experiments.public_catalyst_hybrid_micro_backtest import (
    build_micro_backtest,
    summarize_micro_backtest,
)


def _frame(start: float, step: float, periods: int = 160) -> pd.DataFrame:
    index = pd.bdate_range("2025-01-01", periods=periods)
    close = [start + step * i for i in range(periods)]
    return pd.DataFrame(
        {
            "Open": close,
            "High": [value * 1.01 for value in close],
            "Low": [value * 0.99 for value in close],
            "Close": close,
            "Volume": [1_000_000] * periods,
        },
        index=index,
    )


def _events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "E1",
                "symbol": "AAA",
                "event_date": "2025-05-15",
                "pit_proof_status": "pass",
                "admissibility_label": "admissible_event",
                "outcome_status": "approved",
            },
            {
                "event_id": "E2",
                "symbol": "BBB",
                "event_date": "2025-05-15",
                "pit_proof_status": "pass",
                "admissibility_label": "admissible_event",
                "outcome_status": "CRL",
            },
        ]
    )


def test_micro_backtest_uses_only_admissible_panel_events_and_fixed_windows() -> None:
    frames = {"AAA": _frame(10.0, 0.05), "BBB": _frame(20.0, -0.03)}

    trades = build_micro_backtest(_events(), frames, windows=(30, 60, 90), cost_bps=500)

    assert {trade["window_days"] for trade in trades} == {30, 60, 90}
    assert {trade["event_id"] for trade in trades} == {"E1", "E2"}
    assert all(trade["provider_query_performed"] is False for trade in trades)
    assert all(trade["market_data_download_performed"] is False for trade in trades)
    assert all(trade["short_selling_allowed"] is False for trade in trades)


def test_micro_backtest_archives_when_price_coverage_is_below_gate() -> None:
    frames = {"AAA": _frame(10.0, 0.05)}

    trades = build_micro_backtest(_events(), frames, windows=(30, 60, 90), cost_bps=500)
    summary = summarize_micro_backtest(trades, event_count=12, minimum_price_covered_events=8)

    assert summary["decision"] == "PUBLIC_CATALYST_HYBRID_MICRO_BACKTEST_ARCHIVE_SAMPLE_STARVED"
    assert "price_covered_events_below_8" in summary["blockers"]
    assert summary["promotion_allowed"] is False
    assert summary["parameter_sweep_performed"] is False


def test_micro_backtest_excludes_events_and_exits_after_as_of_date() -> None:
    frames = {"AAA": _frame(10.0, 0.05, periods=260)}
    events = pd.DataFrame(
        [
            {
                "event_id": "MATURE",
                "symbol": "AAA",
                "event_date": "2025-05-15",
                "pit_proof_status": "pass",
                "admissibility_label": "admissible_event",
                "outcome_status": "approved",
            },
            {
                "event_id": "FUTURE",
                "symbol": "AAA",
                "event_date": "2025-10-15",
                "pit_proof_status": "pass",
                "admissibility_label": "admissible_event",
                "outcome_status": "unresolved",
            },
        ]
    )

    trades = build_micro_backtest(events, frames, windows=(30,), cost_bps=500, as_of_date="2025-06-01")

    assert {trade["event_id"] for trade in trades} == {"MATURE"}
    assert all(trade["exit_date"] <= "2025-06-01" for trade in trades)
