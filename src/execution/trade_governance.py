from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterable


class TradeGovernanceError(ValueError):
    """Raised when a trade-governance input is structurally invalid."""


class CoolDownException(RuntimeError):
    """Raised when a new order is attempted during a ticker cooldown window."""


class TradeQuality(str, Enum):
    GOOD_WIN = "GOOD_WIN"
    GOOD_LOSS = "GOOD_LOSS"
    BAD_WIN = "BAD_WIN"
    BAD_LOSS = "BAD_LOSS"


@dataclass(frozen=True)
class TradeGovernanceRecord:
    trade_id: str
    symbol: str
    pnl: float
    protocol_followed: bool
    quality: TradeQuality
    include_in_edge_metrics: bool
    reason: str


@dataclass(frozen=True)
class GovernedMetrics:
    total_trades: int
    included_trades: int
    excluded_bad_wins: int
    gross_pnl_all_trades: float
    governed_pnl: float
    bad_win_pnl_removed: float
    governed_win_rate: float | None


@dataclass(frozen=True)
class CooldownDecision:
    symbol: str
    allowed: bool
    now: datetime
    cooldown_until: datetime | None
    remaining_seconds: int


def classify_trade(
    *,
    trade_id: str,
    symbol: str,
    pnl: float,
    protocol_followed: bool,
    violation_reason: str | None = None,
) -> TradeGovernanceRecord:
    """Classify a trade by outcome and protocol adherence.

    A profitable trade that violates the protocol is intentionally marked BAD_WIN
    and excluded from edge metrics. It is useful as behavioral evidence, not alpha.
    """
    if not str(trade_id).strip():
        raise TradeGovernanceError("trade_id is required")
    if not str(symbol).strip():
        raise TradeGovernanceError("symbol is required")
    if not protocol_followed and not str(violation_reason or "").strip():
        raise TradeGovernanceError("violation_reason is required when protocol_followed is false")

    profitable = pnl > 0
    if protocol_followed and profitable:
        quality = TradeQuality.GOOD_WIN
        include = True
        reason = "protocol_followed_profitable"
    elif protocol_followed:
        quality = TradeQuality.GOOD_LOSS
        include = True
        reason = "protocol_followed_loss_or_flat"
    elif profitable:
        quality = TradeQuality.BAD_WIN
        include = False
        reason = f"protocol_violation_profitable:{violation_reason}"
    else:
        quality = TradeQuality.BAD_LOSS
        include = False
        reason = f"protocol_violation_loss_or_flat:{violation_reason}"

    return TradeGovernanceRecord(
        trade_id=str(trade_id),
        symbol=str(symbol).upper(),
        pnl=float(pnl),
        protocol_followed=bool(protocol_followed),
        quality=quality,
        include_in_edge_metrics=include,
        reason=reason,
    )


def governed_metrics(records: Iterable[TradeGovernanceRecord]) -> GovernedMetrics:
    rows = list(records)
    included = [row for row in rows if row.include_in_edge_metrics]
    bad_wins = [row for row in rows if row.quality == TradeQuality.BAD_WIN]
    governed_pnl = sum(row.pnl for row in included)
    all_pnl = sum(row.pnl for row in rows)
    if included:
        governed_win_rate: float | None = sum(1 for row in included if row.pnl > 0) / len(included)
    else:
        governed_win_rate = None
    return GovernedMetrics(
        total_trades=len(rows),
        included_trades=len(included),
        excluded_bad_wins=len(bad_wins),
        gross_pnl_all_trades=all_pnl,
        governed_pnl=governed_pnl,
        bad_win_pnl_removed=sum(row.pnl for row in bad_wins),
        governed_win_rate=governed_win_rate,
    )


def start_stop_loss_cooldown(exit_time: datetime, cooldown_minutes: int = 15) -> datetime:
    if cooldown_minutes <= 0:
        raise TradeGovernanceError("cooldown_minutes must be positive")
    return _aware_utc(exit_time) + timedelta(minutes=cooldown_minutes)


def check_symbol_cooldown(symbol: str, now: datetime, cooldown_until: datetime | None) -> CooldownDecision:
    if not str(symbol).strip():
        raise TradeGovernanceError("symbol is required")
    now_utc = _aware_utc(now)
    until_utc = _aware_utc(cooldown_until) if cooldown_until is not None else None
    if until_utc is None or now_utc >= until_utc:
        return CooldownDecision(
            symbol=str(symbol).upper(),
            allowed=True,
            now=now_utc,
            cooldown_until=until_utc,
            remaining_seconds=0,
        )
    remaining = int((until_utc - now_utc).total_seconds())
    return CooldownDecision(
        symbol=str(symbol).upper(),
        allowed=False,
        now=now_utc,
        cooldown_until=until_utc,
        remaining_seconds=remaining,
    )


def assert_order_allowed(symbol: str, now: datetime, cooldown_until: datetime | None) -> CooldownDecision:
    decision = check_symbol_cooldown(symbol, now, cooldown_until)
    if not decision.allowed:
        raise CoolDownException(
            f"{decision.symbol} is in cooldown for {decision.remaining_seconds} more seconds"
        )
    return decision


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise TradeGovernanceError("datetime values must be timezone-aware")
    return value.astimezone(timezone.utc)
