from __future__ import annotations

from src.experiments.sec_edgar_earnings_provider_probe import _extract_recent_earnings_8k_records, _summarize_record


def test_extract_recent_earnings_8k_records_filters_item_202() -> None:
    payload = {
        "filings": {
            "recent": {
                "form": ["8-K", "8-K", "10-Q"],
                "items": ["2.02,9.01", "7.01,9.01", ""],
                "accessionNumber": ["a", "b", "c"],
                "filingDate": ["2026-01-01", "2026-01-02", "2026-01-03"],
                "acceptanceDateTime": ["2026-01-01T12:00:00.000Z", "2026-01-02T12:00:00.000Z", "2026-01-03T12:00:00.000Z"],
            }
        }
    }

    records = _extract_recent_earnings_8k_records(payload)

    assert len(records) == 1
    assert records[0]["accessionNumber"] == "a"


def test_summarize_record_maps_sec_acceptance_timestamp_to_bmo() -> None:
    row = _summarize_record(
        {
            "accessionNumber": "a",
            "filingDate": "2026-01-01",
            "acceptanceDateTime": "2026-01-01T12:00:00.000Z",
            "items": "2.02,9.01",
        }
    )

    assert row["classification"] == "BMO"
    assert row["action"] == "allow_candidate"
