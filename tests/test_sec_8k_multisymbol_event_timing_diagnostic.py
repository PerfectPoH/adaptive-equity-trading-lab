from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import src.experiments.sec_8k_multisymbol_event_timing_diagnostic as diag
from src.experiments.sec_8k_multisymbol_event_timing_diagnostic import (
    build_multisymbol_timing_panel,
    infer_equity_symbols,
    run_sec_8k_multisymbol_event_timing_diagnostic,
    summarize_multisymbol_timing_panel,
    validate_sec_8k_multisymbol_event_timing_diagnostic,
)


def test_infer_equity_symbols_excludes_iwm() -> None:
    prices = pd.DataFrame({"symbol": ["CRMD", "IWM", "AEHR"]})

    symbols = infer_equity_symbols(prices)

    assert symbols == ["AEHR", "CRMD"]


def test_build_multisymbol_timing_panel_marks_events_per_symbol() -> None:
    events = [
        {"status": "event", "symbol": "AAA", "reaction_session_date": "2026-02-03"},
        {"status": "event", "symbol": "BBB", "reaction_session_date": "2026-02-04"},
    ]
    prices = pd.concat([_prices("AAA"), _prices("BBB")], ignore_index=True)

    panel = build_multisymbol_timing_panel(events, prices, lookback_days=5)

    assert any(row["symbol"] == "AAA" and row["is_sec_8k_event_day"] is True for row in panel)
    assert any(row["symbol"] == "BBB" and row["is_sec_8k_event_day"] is True for row in panel)
    assert all("pnl" not in row for row in panel)


def test_summary_requires_minimum_event_count() -> None:
    rows = [
        {"is_sec_8k_event_day": True, "return_abs": 0.2, "volume_ratio_vs_20d_median": 4.0},
        {"is_sec_8k_event_day": False, "return_abs": 0.01, "volume_ratio_vs_20d_median": 1.0},
    ]

    summary = summarize_multisymbol_timing_panel(rows, symbols=["AAA"], event_count_fetched=1, lookback_days=20, min_event_count=30)

    assert summary["candidate_timing_signal_allowed"] is False
    assert "event_count_below_30" in summary["blockers"]


def test_validator_fails_if_backtest_marked_performed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diag, "ARTIFACT_DIR", tmp_path / "sec_multi")
    monkeypatch.setattr(diag, "VAULT_REPORT", tmp_path / "report.md")
    monkeypatch.setattr(diag, "VAULT_DEVLOG", tmp_path / "devlog.md")
    monkeypatch.setattr(diag, "fetch_sec_8k_item_202_events", lambda symbols: _events())
    price_path = tmp_path / "prices.csv"
    pd.concat([_prices("AAA"), _prices("BBB")], ignore_index=True).to_csv(price_path, index=False)
    run_sec_8k_multisymbol_event_timing_diagnostic(price_path, symbols=["AAA", "BBB"], min_event_count=30)
    summary_path = tmp_path / "sec_multi" / "diagnostic_summary.json"
    summary_path.write_text(
        summary_path.read_text(encoding="utf-8").replace('"backtest_performed": false', '"backtest_performed": true'),
        encoding="utf-8",
    )

    report = validate_sec_8k_multisymbol_event_timing_diagnostic(tmp_path / "sec_multi")

    assert report["status"] == "fail"
    assert any(check["name"] == "summary_no_backtest" and check["status"] == "fail" for check in report["checks"])


def _events() -> list[dict[str, object]]:
    return [
        {
            "status": "event",
            "symbol": "AAA",
            "cik": "1",
            "accessionNumber": "a",
            "filingDate": "2026-02-03",
            "acceptanceDateTime": "2026-02-03T12:00:00.000Z",
            "classification": "BMO",
            "reaction_session_date": "2026-02-03",
            "items": "2.02,9.01",
            "event_source": "SEC_EDGAR_8K_ITEM_2_02",
            "raw_payload_retained": False,
        },
        {
            "status": "event",
            "symbol": "BBB",
            "cik": "2",
            "accessionNumber": "b",
            "filingDate": "2026-02-04",
            "acceptanceDateTime": "2026-02-04T12:00:00.000Z",
            "classification": "BMO",
            "reaction_session_date": "2026-02-04",
            "items": "2.02,9.01",
            "event_source": "SEC_EDGAR_8K_ITEM_2_02",
            "raw_payload_retained": False,
        },
    ]


def _prices(symbol: str) -> pd.DataFrame:
    rows = []
    for index in range(20):
        rows.append(
            {
                "symbol": symbol,
                "date": f"2026-01-{27 + index:02d}" if index < 5 else f"2026-02-{index - 4:02d}",
                "open": 10.0,
                "high": 10.5,
                "low": 9.5,
                "close": 10.0 + index * 0.1,
                "volume": 1000 + index * 100,
                "provider_dataset": "UNIT.TEST",
            }
        )
    return pd.DataFrame(rows)
