from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.small_cap_metadata_builder import build_small_cap_metadata, write_small_cap_metadata_csv


def test_build_small_cap_metadata_uses_provider_and_sorts_symbols() -> None:
    calls: list[str] = []

    def provider(symbol: str) -> dict[str, object]:
        calls.append(symbol)
        return {
            "market_cap": 500_000_000 if symbol == "AAA" else 900_000_000,
            "is_etf": symbol == "ETF",
        }

    result = build_small_cap_metadata(["bbb", "AAA", "ETF"], provider=provider)

    assert calls == ["AAA", "BBB", "ETF"]
    assert result.metadata.to_dict(orient="records") == [
        {"symbol": "AAA", "market_cap": 500_000_000, "is_etf": False},
        {"symbol": "BBB", "market_cap": 900_000_000, "is_etf": False},
        {"symbol": "ETF", "market_cap": 900_000_000, "is_etf": True},
    ]
    assert result.diagnostics == []


def test_build_small_cap_metadata_records_provider_failures_and_missing_fields() -> None:
    def provider(symbol: str) -> dict[str, object]:
        if symbol == "BAD":
            raise RuntimeError("provider failed")
        return {"market_cap": None, "is_etf": False}

    result = build_small_cap_metadata(["BAD", "MISS"], provider=provider)

    assert result.metadata.empty
    assert result.diagnostics == [
        {"symbol": "BAD", "status": "fail", "reason": "provider_failed:provider failed"},
        {"symbol": "MISS", "status": "fail", "reason": "missing_market_cap"},
    ]


def test_write_small_cap_metadata_csv_writes_metadata_and_diagnostics(tmp_path: Path) -> None:
    def provider(symbol: str) -> dict[str, object]:
        if symbol == "MISS":
            return {"is_etf": False}
        return {"market_cap": 500_000_000, "is_etf": False}

    output_path = tmp_path / "metadata.csv"
    diagnostics_path = tmp_path / "metadata_diagnostics.csv"

    result = write_small_cap_metadata_csv(["AAA", "MISS"], output_path, diagnostics_path=diagnostics_path, provider=provider)

    assert result.metadata_path == output_path
    assert result.diagnostics_path == diagnostics_path
    assert pd.read_csv(output_path).to_dict(orient="records") == [
        {"symbol": "AAA", "market_cap": 500_000_000, "is_etf": False}
    ]
    assert pd.read_csv(diagnostics_path).to_dict(orient="records") == [
        {"symbol": "MISS", "status": "fail", "reason": "missing_market_cap"}
    ]
