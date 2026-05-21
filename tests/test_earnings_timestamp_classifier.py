from __future__ import annotations

from datetime import UTC, datetime

from src.validation.earnings_timestamp_classifier import classify_earnings_timestamp


def test_missing_and_date_only_timestamp_are_unspecified() -> None:
    for value in [None, "", "2025-05-06"]:
        result = classify_earnings_timestamp(value)

        assert result.classification == "UNSPECIFIED"
        assert result.action == "purge"
        assert result.reaction_session is None


def test_midnight_timestamp_is_unspecified() -> None:
    result = classify_earnings_timestamp("2025-05-06T00:00:00Z")

    assert result.classification == "UNSPECIFIED"
    assert result.action == "purge"
    assert result.reason == "midnight_or_date_only_timestamp"


def test_before_market_open_maps_to_bmo_same_session_with_dst() -> None:
    result = classify_earnings_timestamp("2025-05-06T12:00:00Z")

    assert result.classification == "BMO"
    assert result.action == "allow_candidate"
    assert result.reaction_session == "same_regular_session"
    assert "08:00:00" in str(result.local_timestamp)


def test_regular_open_boundary_maps_to_dmt_and_is_purged() -> None:
    result = classify_earnings_timestamp("2025-05-06T13:30:00Z")

    assert result.classification == "DMT"
    assert result.action == "purge"
    assert result.reaction_session is None
    assert result.reason == "during_regular_session"


def test_regular_close_boundary_maps_to_amc_next_session() -> None:
    result = classify_earnings_timestamp("2025-05-06T20:00:00Z")

    assert result.classification == "AMC"
    assert result.action == "allow_candidate"
    assert result.reaction_session == "next_regular_session"
    assert result.reason == "at_or_after_regular_close"


def test_winter_timezone_conversion_uses_est() -> None:
    bmo = classify_earnings_timestamp("2025-01-10T14:29:00Z")
    dmt = classify_earnings_timestamp("2025-01-10T14:30:00Z")

    assert bmo.classification == "BMO"
    assert "09:29:00" in str(bmo.local_timestamp)
    assert dmt.classification == "DMT"
    assert "09:30:00" in str(dmt.local_timestamp)


def test_datetime_input_preserves_timezone_awareness() -> None:
    result = classify_earnings_timestamp(datetime(2025, 5, 6, 21, 5, tzinfo=UTC))

    assert result.classification == "AMC"
    assert result.reaction_session == "next_regular_session"


def test_malformed_timestamp_is_unspecified() -> None:
    result = classify_earnings_timestamp("not-a-timestamp")

    assert result.classification == "UNSPECIFIED"
    assert result.action == "purge"
    assert result.reason == "missing_or_invalid_timestamp"
