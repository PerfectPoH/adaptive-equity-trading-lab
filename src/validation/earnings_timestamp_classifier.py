from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo


MARKET_TIMEZONE = "America/New_York"
DEFAULT_SOURCE_TIMEZONE = "UTC"
REGULAR_OPEN = time(9, 30)
REGULAR_CLOSE = time(16, 0)


@dataclass(frozen=True)
class EarningsTimestampClassification:
    raw_timestamp: str | None
    classification: str
    action: str
    local_timestamp: str | None
    reaction_session: str | None
    reason: str


def classify_earnings_timestamp(
    timestamp: str | datetime | None,
    *,
    source_timezone: str = DEFAULT_SOURCE_TIMEZONE,
    market_timezone: str = MARKET_TIMEZONE,
) -> EarningsTimestampClassification:
    """Map an earnings timestamp to BMO/AMC/DMT/UNSPECIFIED.

    This function is intentionally provider-agnostic and performs no calendar lookup.
    It only maps timestamp resolution to the first full reaction-session policy.
    """

    raw_timestamp = _raw_value(timestamp)
    parsed = _parse_timestamp(timestamp, source_timezone)
    if parsed is None:
        return _classification(raw_timestamp, "UNSPECIFIED", "purge", None, None, "missing_or_invalid_timestamp")
    if parsed.timetz().replace(tzinfo=None) == time(0, 0):
        return _classification(raw_timestamp, "UNSPECIFIED", "purge", parsed.isoformat(), None, "midnight_or_date_only_timestamp")

    local = parsed.astimezone(ZoneInfo(market_timezone))
    local_clock = local.timetz().replace(tzinfo=None)
    local_iso = local.isoformat()
    if local_clock < REGULAR_OPEN:
        return _classification(raw_timestamp, "BMO", "allow_candidate", local_iso, "same_regular_session", "before_regular_open")
    if local_clock >= REGULAR_CLOSE:
        return _classification(raw_timestamp, "AMC", "allow_candidate", local_iso, "next_regular_session", "at_or_after_regular_close")
    return _classification(raw_timestamp, "DMT", "purge", local_iso, None, "during_regular_session")


def _parse_timestamp(timestamp: str | datetime | None, source_timezone: str) -> datetime | None:
    if timestamp is None:
        return None
    if isinstance(timestamp, datetime):
        parsed = timestamp
    else:
        text = timestamp.strip()
        if not text:
            return None
        if _looks_date_only(text):
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(source_timezone))
    return parsed


def _looks_date_only(text: str) -> bool:
    return len(text) == 10 and text[4] == "-" and text[7] == "-"


def _raw_value(timestamp: str | datetime | None) -> str | None:
    if timestamp is None:
        return None
    if isinstance(timestamp, datetime):
        return timestamp.isoformat()
    return timestamp


def _classification(
    raw_timestamp: str | None,
    classification: str,
    action: str,
    local_timestamp: str | None,
    reaction_session: str | None,
    reason: str,
) -> EarningsTimestampClassification:
    return EarningsTimestampClassification(
        raw_timestamp=raw_timestamp,
        classification=classification,
        action=action,
        local_timestamp=local_timestamp,
        reaction_session=reaction_session,
        reason=reason,
    )
