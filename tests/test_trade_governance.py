from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.execution.trade_governance import (
    CoolDownException,
    TradeGovernanceError,
    TradeQuality,
    assert_order_allowed,
    check_symbol_cooldown,
    classify_trade,
    governed_metrics,
    start_stop_loss_cooldown,
)


def test_classify_good_win_and_good_loss_are_included_in_edge_metrics() -> None:
    win = classify_trade(trade_id="T1", symbol="crmd", pnl=100.0, protocol_followed=True)
    loss = classify_trade(trade_id="T2", symbol="AEHR", pnl=-25.0, protocol_followed=True)

    assert win.quality == TradeQuality.GOOD_WIN
    assert win.include_in_edge_metrics is True
    assert win.symbol == "CRMD"
    assert loss.quality == TradeQuality.GOOD_LOSS
    assert loss.include_in_edge_metrics is True


def test_classify_bad_win_is_excluded_even_when_profitable() -> None:
    record = classify_trade(
        trade_id="T3",
        symbol="CRMD",
        pnl=500.0,
        protocol_followed=False,
        violation_reason="manual_exit_override",
    )

    assert record.quality == TradeQuality.BAD_WIN
    assert record.include_in_edge_metrics is False
    assert "manual_exit_override" in record.reason


def test_protocol_violation_requires_reason() -> None:
    with pytest.raises(TradeGovernanceError, match="violation_reason"):
        classify_trade(trade_id="T4", symbol="CRMD", pnl=-1.0, protocol_followed=False)


def test_governed_metrics_remove_bad_wins_from_pnl_and_win_rate() -> None:
    records = [
        classify_trade(trade_id="G1", symbol="AAA", pnl=100.0, protocol_followed=True),
        classify_trade(trade_id="G2", symbol="BBB", pnl=-40.0, protocol_followed=True),
        classify_trade(
            trade_id="B1",
            symbol="CCC",
            pnl=1_000.0,
            protocol_followed=False,
            violation_reason="revenge_entry",
        ),
        classify_trade(
            trade_id="B2",
            symbol="DDD",
            pnl=-75.0,
            protocol_followed=False,
            violation_reason="cooldown_override",
        ),
    ]

    metrics = governed_metrics(records)

    assert metrics.total_trades == 4
    assert metrics.included_trades == 2
    assert metrics.excluded_bad_wins == 1
    assert metrics.gross_pnl_all_trades == 985.0
    assert metrics.governed_pnl == 60.0
    assert metrics.bad_win_pnl_removed == 1_000.0
    assert metrics.governed_win_rate == 0.5


def test_start_stop_loss_cooldown_uses_timezone_aware_utc() -> None:
    exit_time = datetime(2026, 5, 21, 14, 30, tzinfo=timezone.utc)

    cooldown_until = start_stop_loss_cooldown(exit_time, cooldown_minutes=15)

    assert cooldown_until == datetime(2026, 5, 21, 14, 45, tzinfo=timezone.utc)


def test_cooldown_blocks_reentry_until_window_expires() -> None:
    exit_time = datetime(2026, 5, 21, 14, 30, tzinfo=timezone.utc)
    cooldown_until = start_stop_loss_cooldown(exit_time, cooldown_minutes=15)

    blocked = check_symbol_cooldown("crmd", exit_time + timedelta(minutes=5), cooldown_until)
    allowed = check_symbol_cooldown("crmd", exit_time + timedelta(minutes=15), cooldown_until)

    assert blocked.allowed is False
    assert blocked.symbol == "CRMD"
    assert blocked.remaining_seconds == 600
    assert allowed.allowed is True
    assert allowed.remaining_seconds == 0


def test_assert_order_allowed_raises_during_cooldown() -> None:
    exit_time = datetime(2026, 5, 21, 14, 30, tzinfo=timezone.utc)
    cooldown_until = start_stop_loss_cooldown(exit_time, cooldown_minutes=15)

    with pytest.raises(CoolDownException, match="CRMD"):
        assert_order_allowed("CRMD", exit_time + timedelta(minutes=1), cooldown_until)


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(TradeGovernanceError, match="timezone-aware"):
        start_stop_loss_cooldown(datetime(2026, 5, 21, 14, 30), cooldown_minutes=15)
